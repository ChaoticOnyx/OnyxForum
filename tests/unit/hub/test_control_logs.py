import os
import subprocess

import pytest

from hub.services import control_logs


def test_append_update_log_creates_file_and_parent_directory(tmpdir):
    log_path = str(tmpdir.join("logs", "onyx", "update.log"))

    control_logs.append_update_log(log_path, "Update requested")
    control_logs.append_update_log(log_path, "Update queued")

    with open(log_path, "r", encoding="utf-8") as log_file:
        assert log_file.read() == "Update requested\nUpdate queued\n"


def test_update_log_uses_shared_absolute_log_root(tmpdir):
    log_root = str(tmpdir.join("logs"))

    log_path = control_logs.get_update_log_path(log_root, "onyx")

    assert os.path.isabs(log_path)
    assert log_path == os.path.join(
        log_root,
        "onyx",
        "update.log",
    )


def test_update_log_path_rejects_parent_directory(tmpdir):
    with pytest.raises(ValueError):
        control_logs.get_update_log_path(str(tmpdir), "../outside")


def test_reads_last_update_log_lines(tmpdir):
    log_root = str(tmpdir.join("logs"))
    log_path = control_logs.get_update_log_path(log_root, "onyx")
    os.makedirs(os.path.dirname(log_path))
    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write("first\nsecond\nthird\n")

    lines = control_logs.read_update_log(
        log_root,
        "onyx",
        line_limit=2,
    )

    assert lines == ["second", "third"]


def test_missing_update_log_is_empty(tmpdir):
    lines = control_logs.read_update_log(str(tmpdir), "onyx")

    assert lines == []


def test_reads_server_output_without_shell(monkeypatch):
    calls = []

    def run(arguments, **kwargs):
        calls.append((arguments, kwargs))
        return subprocess.CompletedProcess(
            arguments,
            0,
            stdout="old\nnew\n",
        )

    monkeypatch.setattr(control_logs.subprocess, "run", run)

    lines = control_logs.read_server_output("onyx.service", line_limit=2)

    assert lines == ["old", "new"]
    assert calls[0][0] == [
        "journalctl",
        "--unit=onyx.service",
        "-n",
        "2",
        "--no-pager",
    ]
    assert "shell" not in calls[0][1]


def test_server_output_falls_back_to_systemctl_status(monkeypatch):
    calls = []
    responses = iter([
        subprocess.CompletedProcess(
            [],
            0,
            stdout="-- No entries --\n",
        ),
        subprocess.CompletedProcess(
            [],
            0,
            stdout="erebus.service active (running)\nDreamDaemon\n",
        ),
    ])

    def run(arguments, **kwargs):
        calls.append((arguments, kwargs))
        return next(responses)

    monkeypatch.setattr(control_logs.subprocess, "run", run)

    lines = control_logs.read_server_output("erebus.service")

    assert lines == [
        "erebus.service active (running)",
        "DreamDaemon",
    ]
    assert calls[1][0] == [
        "systemctl",
        "status",
        "erebus.service",
        "--no-pager",
        "--full",
    ]
    assert "shell" not in calls[1][1]
