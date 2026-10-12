import os
import subprocess
from collections import deque


LOG_LINE_LIMIT = 500


def append_update_log(log_path, content):
    log_directory = os.path.dirname(log_path)
    if log_directory:
        os.makedirs(log_directory, exist_ok=True)

    if not content.endswith("\n"):
        content += "\n"
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(content)
        log_file.flush()


def get_update_log_path(log_root, server_id):
    server_logs_root = os.path.abspath(log_root)
    server_log_directory = os.path.abspath(
        os.path.join(server_logs_root, str(server_id))
    )
    common_path = os.path.commonpath(
        (server_logs_root, server_log_directory)
    )
    if common_path != server_logs_root:
        raise ValueError("Server id leaves the log directory")
    return os.path.join(server_log_directory, "update.log")


def read_update_log(log_root, server_id, line_limit=LOG_LINE_LIMIT):
    log_path = get_update_log_path(log_root, server_id)
    if not os.path.isfile(log_path):
        return []

    with open(log_path, "r", encoding="utf-8", errors="replace") as log_file:
        lines = deque(log_file, maxlen=line_limit)
    return [line.rstrip("\r\n") for line in lines]


def read_server_output(service_name, line_limit=LOG_LINE_LIMIT):
    process = subprocess.run(
        [
            "journalctl",
            "--unit={}".format(service_name),
            "-n",
            str(line_limit),
            "--no-pager",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    lines = process.stdout.splitlines()
    if not lines or lines == ["-- No entries --"]:
        status_process = subprocess.run(
            [
                "systemctl",
                "status",
                service_name,
                "--no-pager",
                "--full",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )
        status_lines = status_process.stdout.splitlines()
        if status_lines:
            lines = status_lines
    if process.returncode and not lines:
        lines = [
            "journalctl exited with code {}".format(process.returncode)
        ]
    return lines[-line_limit:]
