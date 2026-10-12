import filecmp
import json
import os
import re
import shutil
import subprocess


OPTION_RE = re.compile(
    r"^(?P<indent>\s*)(?P<comment>#\s*)?(?P<lock>@)?"
    r"(?P<key>[A-Z][A-Z0-9_]*)\b"
)
TOML_SECTION_RE = re.compile(r"^\s*\[+(?P<section>[^]]+)\]+\s*$")
TOML_OPTION_RE = re.compile(
    r"^\s*(?P<comment>#\s*)?"
    r"(?P<key>[A-Za-z0-9_.-]+|\"[^\"]+\"|'[^']+')\s*="
)


def _files_equal(first_path, second_path):
    return filecmp.cmp(first_path, second_path, shallow=False)


def _copy_file(source_path, destination_path):
    parent_path = os.path.dirname(destination_path)
    if not os.path.exists(parent_path):
        os.makedirs(parent_path)
    shutil.copy2(source_path, destination_path)


def _read_lines(path):
    with open(path, "r", encoding="utf-8") as config_file:
        return config_file.readlines()


def _option_occurrences(lines):
    occurrences = {}
    descriptions = 0

    for index, line in enumerate(lines):
        if line.lstrip().startswith("##"):
            descriptions += 1
            continue

        match = OPTION_RE.match(line)
        if not match:
            continue

        key = match.group("key")
        occurrences.setdefault(key, []).append(
            (index, match.group("comment") is None)
        )

    return occurrences, descriptions


def _preferred_occurrence(occurrences):
    active = [occurrence for occurrence in occurrences if occurrence[1]]
    return active[-1] if active else occurrences[-1]


def _merge_option_file(local_path, base_path, incoming_path):
    local_lines = _read_lines(local_path)
    base_lines = _read_lines(base_path)
    incoming_lines = _read_lines(incoming_path)

    local_options, local_descriptions = _option_occurrences(local_lines)
    base_options, base_descriptions = _option_occurrences(base_lines)
    incoming_options, incoming_descriptions = _option_occurrences(
        incoming_lines
    )

    description_count = max(
        local_descriptions,
        base_descriptions,
        incoming_descriptions,
    )
    if len(incoming_options) < 2 or description_count < 2:
        return None

    merged_lines = list(incoming_lines)
    for key in set(local_options).intersection(incoming_options):
        local_index, _ = _preferred_occurrence(local_options[key])
        incoming_index, _ = _preferred_occurrence(incoming_options[key])
        merged_lines[incoming_index] = local_lines[local_index]

    custom_keys = set(local_options) - set(base_options) - set(incoming_options)
    if custom_keys:
        if merged_lines and not merged_lines[-1].endswith(("\n", "\r")):
            merged_lines[-1] += "\n"
        merged_lines.append("\n# Local options\n")
        for key in sorted(custom_keys):
            local_index, _ = _preferred_occurrence(local_options[key])
            merged_lines.append(local_lines[local_index])

    return "".join(merged_lines).encode("utf-8")


def _merge_json_values(local_value, base_value, incoming_value):
    if not isinstance(incoming_value, dict):
        return local_value

    local_dict = local_value if isinstance(local_value, dict) else {}
    base_dict = base_value if isinstance(base_value, dict) else {}
    merged = {}

    for key, incoming_item in incoming_value.items():
        if key not in local_dict:
            merged[key] = incoming_item
            continue

        merged[key] = _merge_json_values(
            local_dict[key],
            base_dict.get(key),
            incoming_item,
        )

    for key, local_item in local_dict.items():
        if key not in base_dict and key not in incoming_value:
            merged[key] = local_item

    return merged


def _merge_json_file(local_path, base_path, incoming_path):
    try:
        with open(local_path, "r", encoding="utf-8") as local_file:
            local_value = json.load(local_file)
        with open(base_path, "r", encoding="utf-8") as base_file:
            base_value = json.load(base_file)
        with open(incoming_path, "r", encoding="utf-8") as incoming_file:
            incoming_value = json.load(incoming_file)
    except (UnicodeDecodeError, ValueError):
        return None

    merged = _merge_json_values(local_value, base_value, incoming_value)
    content = json.dumps(
        merged,
        ensure_ascii=False,
        indent=2,
        sort_keys=False,
    )
    return (content + "\n").encode("utf-8")


def _toml_structure(lines):
    section = ""
    sections = {section}
    options = {}

    for index, line in enumerate(lines):
        section_match = TOML_SECTION_RE.match(line)
        if section_match:
            section = section_match.group("section")
            sections.add(section)
            continue

        option_match = TOML_OPTION_RE.match(line)
        if not option_match:
            continue

        identity = (section, option_match.group("key"))
        options.setdefault(identity, []).append(
            (index, option_match.group("comment") is None)
        )

    return sections, options


def _append_custom_toml_options(result, section, custom_options,
                                local_options, local_lines):
    section_options = sorted(
        identity for identity in custom_options if identity[0] == section
    )
    if not section_options:
        return

    if result and result[-1].strip():
        result.append("\n")
    result.append("# Local options\n")
    for identity in section_options:
        local_index, _ = _preferred_occurrence(local_options[identity])
        result.append(local_lines[local_index])


def _merge_toml_file(local_path, base_path, incoming_path):
    try:
        local_lines = _read_lines(local_path)
        base_lines = _read_lines(base_path)
        incoming_lines = _read_lines(incoming_path)
    except UnicodeDecodeError:
        return None

    local_sections, local_options = _toml_structure(local_lines)
    _, base_options = _toml_structure(base_lines)
    incoming_sections, incoming_options = _toml_structure(incoming_lines)
    if not incoming_options:
        return None

    custom_options = (
        set(local_options) - set(base_options) - set(incoming_options)
    )
    result = []
    current_section = ""
    inserted_sections = set()

    for line in incoming_lines:
        section_match = TOML_SECTION_RE.match(line)
        if section_match:
            _append_custom_toml_options(
                result,
                current_section,
                custom_options,
                local_options,
                local_lines,
            )
            inserted_sections.add(current_section)
            current_section = section_match.group("section")
            result.append(line)
            continue

        option_match = TOML_OPTION_RE.match(line)
        identity = None
        if option_match:
            identity = (current_section, option_match.group("key"))
        if identity in local_options:
            incoming_index, _ = _preferred_occurrence(
                incoming_options[identity]
            )
            if incoming_lines[incoming_index] == line:
                local_index, _ = _preferred_occurrence(
                    local_options[identity]
                )
                result.append(local_lines[local_index])
                continue
        result.append(line)

    _append_custom_toml_options(
        result,
        current_section,
        custom_options,
        local_options,
        local_lines,
    )
    inserted_sections.add(current_section)

    for section in sorted(local_sections - incoming_sections):
        if section in inserted_sections:
            continue
        section_custom_options = {
            identity for identity in custom_options if identity[0] == section
        }
        if not section_custom_options:
            continue
        if result and result[-1].strip():
            result.append("\n")
        result.append("[{}]\n".format(section))
        _append_custom_toml_options(
            result,
            section,
            section_custom_options,
            local_options,
            local_lines,
        )

    return "".join(result).encode("utf-8")


def _merge_text_file(local_path, base_path, incoming_path):
    if incoming_path.lower().endswith(".json"):
        json_content = _merge_json_file(
            local_path,
            base_path,
            incoming_path,
        )
        if json_content is not None:
            return json_content

    if incoming_path.lower().endswith(".toml"):
        toml_content = _merge_toml_file(
            local_path,
            base_path,
            incoming_path,
        )
        if toml_content is not None:
            return toml_content

    try:
        option_content = _merge_option_file(
            local_path,
            base_path,
            incoming_path,
        )
    except UnicodeDecodeError:
        option_content = None

    if option_content is not None:
        return option_content

    process = subprocess.Popen(
        [
            "git",
            "merge-file",
            "--stdout",
            "--ours",
            local_path,
            base_path,
            incoming_path,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, _ = process.communicate()
    if process.returncode in (0, 1):
        return stdout
    return None


def _merge_file(local_path, base_path, incoming_path, destination_path):
    if _files_equal(local_path, base_path):
        return

    if _files_equal(incoming_path, base_path):
        _copy_file(local_path, destination_path)
        return

    content = _merge_text_file(local_path, base_path, incoming_path)
    if content is None:
        _copy_file(local_path, destination_path)
        return

    with open(destination_path, "wb") as destination_file:
        destination_file.write(content)


def _copy_local_config(local_path, destination_path):
    for root_path, _, file_names in os.walk(local_path):
        relative_root = os.path.relpath(root_path, local_path)
        if relative_root == ".":
            relative_root = ""

        for file_name in file_names:
            relative_path = os.path.join(relative_root, file_name)
            local_file = os.path.join(local_path, relative_path)
            destination_file = os.path.join(destination_path, relative_path)
            _copy_file(local_file, destination_file)


def _merge_existing_entries(local_path, base_path, incoming_path,
                            destination_path):
    for root_path, directory_names, file_names in os.walk(local_path):
        relative_root = os.path.relpath(root_path, local_path)
        if relative_root == ".":
            relative_root = ""

        for directory_name in list(directory_names):
            local_directory = os.path.join(root_path, directory_name)
            if not os.path.islink(local_directory):
                continue

            directory_names.remove(directory_name)
            relative_path = os.path.join(relative_root, directory_name)
            base_entry = os.path.join(base_path, relative_path)
            incoming_entry = os.path.join(incoming_path, relative_path)
            destination_entry = os.path.join(destination_path, relative_path)
            if not os.path.lexists(base_entry):
                if os.path.lexists(destination_entry):
                    os.unlink(destination_entry)
                _copy_file(local_directory, destination_entry)
            elif os.path.lexists(incoming_entry):
                _copy_file(local_directory, destination_entry)

        for file_name in file_names:
            relative_path = os.path.join(relative_root, file_name)
            local_file = os.path.join(local_path, relative_path)
            base_file = os.path.join(base_path, relative_path)
            incoming_file = os.path.join(incoming_path, relative_path)
            destination_file = os.path.join(destination_path, relative_path)

            if not os.path.isfile(incoming_file):
                if not os.path.lexists(base_file):
                    _copy_file(local_file, destination_file)
                continue

            if not os.path.isfile(base_file):
                _copy_file(local_file, destination_file)
                continue

            if not os.path.isfile(local_file):
                continue

            _merge_file(
                local_file,
                base_file,
                incoming_file,
                destination_file,
            )


def merge_config_directories(local_path, base_path, incoming_path,
                             destination_path):
    """Merge a local config with old and new repository config trees.

    The incoming tree defines the current upstream structure. Local values
    win for settings that still exist, new upstream entries are added, and
    entries removed upstream are removed locally. Files that never existed
    upstream are treated as local files and retained.
    """
    if not os.path.isdir(incoming_path):
        raise ValueError("Incoming config directory does not exist")

    shutil.copytree(incoming_path, destination_path, symlinks=True)

    if not os.path.isdir(local_path):
        return

    if not os.path.isdir(base_path):
        _copy_local_config(
            local_path,
            destination_path,
        )
        return

    _merge_existing_entries(
        local_path,
        base_path,
        incoming_path,
        destination_path,
    )
