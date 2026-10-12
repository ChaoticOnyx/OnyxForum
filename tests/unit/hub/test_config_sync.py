import json
import os

from hub.features.servers_managment.services.config_sync import (
    merge_config_directories,
)


def _write(path, content):
    path.dirpath().ensure(dir=True)
    path.write(content)


def test_merges_config_values_and_upstream_structure(tmpdir):
    local_path = tmpdir.join("local")
    base_path = tmpdir.join("base")
    incoming_path = tmpdir.join("incoming")
    destination_path = tmpdir.join("destination")

    _write(
        base_path.join("config.txt"),
        "## Server name\n"
        "## Server options\n"
        "SERVERNAME upstream\n"
        "KEEP_OPTION upstream\n"
        "OLD_OPTION upstream\n",
    )
    _write(
        local_path.join("config.txt"),
        "## Server name\n"
        "## Server options\n"
        "SERVERNAME local\n"
        "KEEP_OPTION local\n"
        "OLD_OPTION customized\n"
        "CUSTOM_OPTION enabled\n",
    )
    _write(
        incoming_path.join("config.txt"),
        "## Updated server name\n"
        "## Updated server options\n"
        "SERVERNAME new-default\n"
        "KEEP_OPTION new-default\n"
        "NEW_OPTION enabled\n",
    )
    _write(base_path.join("removed.txt"), "old upstream file\n")
    _write(local_path.join("removed.txt"), "local old file\n")
    _write(local_path.join("local.txt"), "local-only file\n")
    _write(incoming_path.join("added.txt"), "new upstream file\n")

    merge_config_directories(
        str(local_path),
        str(base_path),
        str(incoming_path),
        str(destination_path),
    )

    merged = destination_path.join("config.txt").read()
    assert "SERVERNAME local" in merged
    assert "KEEP_OPTION local" in merged
    assert "NEW_OPTION enabled" in merged
    assert "CUSTOM_OPTION enabled" in merged
    assert "OLD_OPTION" not in merged
    assert destination_path.join("added.txt").read() == "new upstream file\n"
    assert destination_path.join("local.txt").read() == "local-only file\n"
    assert not destination_path.join("removed.txt").exists()


def test_merges_json_values_and_removes_obsolete_keys(tmpdir):
    local_path = tmpdir.join("local")
    base_path = tmpdir.join("base")
    incoming_path = tmpdir.join("incoming")
    destination_path = tmpdir.join("destination")

    _write(
        base_path.join("settings.json"),
        json.dumps({"database": {"host": "old", "removed": True}}),
    )
    _write(
        local_path.join("settings.json"),
        json.dumps({
            "database": {
                "host": "localhost",
                "removed": False,
                "custom": "value",
            }
        }),
    )
    _write(
        incoming_path.join("settings.json"),
        json.dumps({"database": {"host": "new", "port": 3306}}),
    )

    merge_config_directories(
        str(local_path),
        str(base_path),
        str(incoming_path),
        str(destination_path),
    )

    merged = json.loads(destination_path.join("settings.json").read())
    assert merged == {
        "database": {
            "host": "localhost",
            "port": 3306,
            "custom": "value",
        }
    }


def test_first_sync_preserves_local_files(tmpdir):
    local_path = tmpdir.join("local")
    incoming_path = tmpdir.join("incoming")
    destination_path = tmpdir.join("destination")

    _write(local_path.join("config.txt"), "SERVERNAME local\n")
    _write(incoming_path.join("config.txt"), "SERVERNAME upstream\n")
    _write(incoming_path.join("new.txt"), "new file\n")

    merge_config_directories(
        str(local_path),
        str(tmpdir.join("missing-base")),
        str(incoming_path),
        str(destination_path),
    )

    assert destination_path.join("config.txt").read() == "SERVERNAME local\n"
    assert destination_path.join("new.txt").read() == "new file\n"


def test_merges_toml_values_and_structure(tmpdir):
    local_path = tmpdir.join("local")
    base_path = tmpdir.join("base")
    incoming_path = tmpdir.join("incoming")
    destination_path = tmpdir.join("destination")

    _write(
        base_path.join("general.toml"),
        "[general]\nname = \"default\"\nremoved = true\n",
    )
    _write(
        local_path.join("general.toml"),
        "[general]\nname = \"production\"\nremoved = false\n"
        "custom = \"kept\"\n",
    )
    _write(
        incoming_path.join("general.toml"),
        "[general]\nname = \"new default\"\nadded = 42\n",
    )

    merge_config_directories(
        str(local_path),
        str(base_path),
        str(incoming_path),
        str(destination_path),
    )

    merged = destination_path.join("general.toml").read()
    assert 'name = "production"' in merged
    assert "added = 42" in merged
    assert 'custom = "kept"' in merged
    assert "removed" not in merged
