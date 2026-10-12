import os
import shutil
from types import SimpleNamespace

import pytest

from hub.features.servers_managment.services.server_update import (
    ServerUpdateService,
)


def _server(repository_path):
    return SimpleNamespace(
        id="test",
        path=str(repository_path),
        branch_name="main",
        dream_maker_binary="DreamMaker",
        dme_name="game.dme",
        configs_path=os.path.join(str(repository_path), "config"),
        update_script_path=None,
    )


def test_collects_required_and_dynamic_artifacts(tmpdir):
    repository_path = tmpdir.mkdir("repository")
    worktree_path = tmpdir.mkdir("worktree")
    worktree_path.join("game.dme").write("")
    worktree_path.join("game.dmb").write("new dmb")
    worktree_path.join("game.rsc").write("new rsc")
    worktree_path.join("game.dyn.rsc").write("new dynamic rsc")
    service = ServerUpdateService(_server(repository_path), lambda _: None)

    artifacts = service._collect_artifacts(str(worktree_path))

    assert [relative_path for _, relative_path in artifacts] == [
        "game.rsc",
        "game.dyn.rsc",
        "game.dmb",
    ]


def test_prepares_all_artifacts_from_repository_deploy_script(tmpdir):
    repository_path = tmpdir.mkdir("repository")
    temporary_root = tmpdir.mkdir("temporary")
    worktree_path = temporary_root.mkdir("worktree")
    tools_path = worktree_path.mkdir("tools")
    tools_path.join("deploy.sh").write("#!/bin/bash\n")
    tgui_path = worktree_path.mkdir("tgui").mkdir("public")
    tgui_path.join("tgui.bundle.js").write(
        "./Purity.tsx ./Rosewall.tsx ./Brassface.tsx"
    )
    worktree_path.join("game.dmb").write("new dmb")
    worktree_path.join("game.rsc").write("new rsc")
    worktree_path.mkdir("config").join("server.txt").write(
        "incoming config"
    )
    service = ServerUpdateService(_server(repository_path), lambda _: None)

    def run_deploy(arguments, cwd=None, check=True):
        deployment_path = arguments[2]
        os.makedirs(os.path.join(deployment_path, "tgui", "public"))
        os.makedirs(os.path.join(deployment_path, "config"))
        shutil.copy2(
            os.path.join(str(worktree_path), "game.dmb"),
            deployment_path,
        )
        shutil.copy2(
            os.path.join(str(worktree_path), "game.rsc"),
            deployment_path,
        )
        shutil.copy2(
            os.path.join(
                str(worktree_path),
                "tgui",
                "public",
                "tgui.bundle.js",
            ),
            os.path.join(deployment_path, "tgui", "public"),
        )
        shutil.copy2(
            os.path.join(str(worktree_path), "config", "server.txt"),
            os.path.join(deployment_path, "config"),
        )

    service.runner.run = run_deploy

    artifacts = service._prepare_artifacts(
        str(temporary_root),
        str(worktree_path),
    )

    relative_paths = [relative_path for _, relative_path in artifacts]
    assert relative_paths == [
        "game.dmb",
        "game.rsc",
        os.path.join("tgui", "public", "tgui.bundle.js"),
    ]
    assert os.path.join("config", "server.txt") not in relative_paths

    backups = service._publish_artifacts(artifacts)

    published_bundle = repository_path.join(
        "tgui",
        "public",
        "tgui.bundle.js",
    )
    assert published_bundle.read() == (
        "./Purity.tsx ./Rosewall.tsx ./Brassface.tsx"
    )
    service._remove_artifact_backups(backups)


def test_publishes_artifacts_and_keeps_backups_until_commit(tmpdir):
    repository_path = tmpdir.mkdir("repository")
    build_path = tmpdir.mkdir("build")
    old_dmb = repository_path.join("game.dmb")
    new_dmb = build_path.join("game.dmb")
    old_dmb.write("old dmb")
    new_dmb.write("new dmb")
    service = ServerUpdateService(_server(repository_path), lambda _: None)

    backups = service._publish_artifacts([
        (str(new_dmb), "game.dmb"),
    ])

    assert old_dmb.read() == "new dmb"
    assert not new_dmb.exists()
    assert len(backups) == 1
    assert os.path.isfile(backups[0][1])
    service._remove_artifact_backups(backups)
    assert not os.path.exists(backups[0][1])


@pytest.mark.skipif(
    os.name == "nt",
    reason="Windows does not allow replacing an open file",
)
def test_publishes_artifacts_without_overwriting_open_file(tmpdir):
    repository_path = tmpdir.mkdir("repository")
    build_path = tmpdir.mkdir("build")
    old_dmb = repository_path.join("game.dmb")
    old_rsc = repository_path.join("game.rsc")
    new_dmb = build_path.join("game.dmb")
    new_rsc = build_path.join("game.rsc")
    old_dmb.write("old dmb")
    old_rsc.write("old rsc")
    new_dmb.write("new dmb")
    new_rsc.write("new rsc")
    service = ServerUpdateService(_server(repository_path), lambda _: None)

    with open(str(old_dmb), "r") as running_server_file:
        backups = service._publish_artifacts([
            (str(new_dmb), "game.dmb"),
            (str(new_rsc), "game.rsc"),
        ])
        assert running_server_file.read() == "old dmb"

    assert old_dmb.read() == "new dmb"
    assert old_rsc.read() == "new rsc"
    service._remove_artifact_backups(backups)
    assert not list(repository_path.visit("*.hub-old-*"))


def test_resolves_relative_build_script_inside_repository(tmpdir):
    repository_path = tmpdir.mkdir("repository")
    server = _server(repository_path)
    server.update_script_path = os.path.join("tools", "build.sh")
    service = ServerUpdateService(server, lambda _: None)

    script_path = service._update_script_path()

    assert script_path == os.path.join(
        str(repository_path),
        "tools",
        "build.sh",
    )
    assert service._is_inside_repository(script_path)
