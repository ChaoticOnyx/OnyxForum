import errno
import hashlib
import os
import shlex
import shutil
import subprocess
import tempfile
import uuid

try:
    import fcntl
except ImportError:  # pragma: no cover - the production host is Linux
    fcntl = None

from .config_sync import merge_config_directories


class ServerUpdateError(RuntimeError):
    pass


class CommandRunner(object):
    def __init__(self, write_log):
        self.write_log = write_log

    def run(self, arguments, cwd=None, check=True):
        command = " ".join(shlex.quote(argument) for argument in arguments)
        self.write_log("$ " + command)
        process = subprocess.Popen(
            arguments,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
        )
        for line in iter(process.stdout.readline, ""):
            self.write_log(line.rstrip("\r\n"))
        process.stdout.close()
        return_code = process.wait()

        if check and return_code:
            raise ServerUpdateError(
                "Command failed with exit code {}: {}".format(
                    return_code,
                    command,
                )
            )
        return return_code

    def capture(self, arguments, cwd=None, check=True):
        process = subprocess.Popen(
            arguments,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        stdout, stderr = process.communicate()
        if check and process.returncode:
            raise ServerUpdateError(
                "Command failed with exit code {}: {}".format(
                    process.returncode,
                    stderr.strip(),
                )
            )
        return process.returncode, stdout.strip()


class ServerUpdateLock(object):
    def __init__(self, server_id):
        digest = hashlib.sha256(server_id.encode("utf-8")).hexdigest()
        lock_directory = os.path.join(
            tempfile.gettempdir(),
            "onyxforum-server-updates",
        )
        if not os.path.exists(lock_directory):
            try:
                os.makedirs(lock_directory)
            except OSError as exception:
                if exception.errno != errno.EEXIST:
                    raise
        self.path = os.path.join(lock_directory, digest + ".lock")
        self.lock_file = None

    def __enter__(self):
        self.lock_file = open(self.path, "a+")
        if fcntl is None:
            return self

        try:
            fcntl.flock(
                self.lock_file.fileno(),
                fcntl.LOCK_EX | fcntl.LOCK_NB,
            )
        except OSError:
            self.lock_file.close()
            self.lock_file = None
            raise ServerUpdateError(
                "An update for this server is already running"
            )
        return self

    def __exit__(self, exception_type, exception, traceback):
        if self.lock_file is None:
            return
        if fcntl is not None:
            fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
        self.lock_file.close()


class ServerUpdateService(object):
    def __init__(self, server, write_log):
        self.server = server
        self.write_log = write_log
        self.runner = CommandRunner(write_log)
        self.repository_path = os.path.abspath(server.path)

    def run(self):
        if not os.path.isdir(self.repository_path):
            raise ServerUpdateError("Server repository does not exist")

        self.write_log("Repository: {}".format(self.repository_path))
        with ServerUpdateLock(self.server.id):
            script_path = self._update_script_path()
            if script_path and not self._is_inside_repository(script_path):
                self._run_external_update_script(script_path)
            else:
                self._run_isolated_update(script_path)

    def _update_script_path(self):
        configured_path = self.server.update_script_path
        if not configured_path:
            return None
        if os.path.isabs(configured_path):
            return os.path.abspath(configured_path)
        return os.path.abspath(
            os.path.join(self.repository_path, configured_path)
        )

    def _is_inside_repository(self, path):
        try:
            common_path = os.path.commonpath(
                (self.repository_path, os.path.abspath(path))
            )
        except ValueError:
            return False
        return common_path == self.repository_path

    def _run_external_update_script(self, script_path):
        if not os.path.isfile(script_path):
            raise ServerUpdateError("Configured update script does not exist")

        self.write_log(
            "Running external update script: {}".format(script_path)
        )
        self.write_log(
            "Repository and config handling are delegated to the script"
        )
        self.runner.run(
            ["/bin/bash", script_path],
            cwd=self.repository_path,
        )

    def _run_isolated_update(self, script_path):
        old_revision = self.runner.capture(
            ["git", "-C", self.repository_path, "rev-parse", "HEAD"]
        )[1]
        self.write_log("Current revision: {}".format(old_revision))
        self.runner.run(
            [
                "git",
                "-C",
                self.repository_path,
                "fetch",
                "origin",
                self.server.branch_name,
            ]
        )
        new_revision = self.runner.capture(
            ["git", "-C", self.repository_path, "rev-parse", "FETCH_HEAD"]
        )[1]
        self.write_log("Incoming revision: {}".format(new_revision))

        server_digest = hashlib.sha256(
            self.server.id.encode("utf-8")
        ).hexdigest()[:12]
        temporary_root = tempfile.mkdtemp(
            prefix=".hub-build-{}-".format(server_digest),
            dir=os.path.dirname(self.repository_path),
        )
        worktree_path = os.path.join(temporary_root, "worktree")

        try:
            self.runner.run(
                [
                    "git",
                    "-C",
                    self.repository_path,
                    "worktree",
                    "add",
                    "--detach",
                    worktree_path,
                    new_revision,
                ]
            )
            self.write_log("Building in an isolated worktree")
            self._build(worktree_path, script_path)
            artifacts = self._prepare_artifacts(
                temporary_root,
                worktree_path,
            )
            self.write_log("Preparing server config merge")
            config_state = self._prepare_config(
                temporary_root,
                worktree_path,
                old_revision,
            )
            self.write_log("Publishing revision and build artifacts")
            self._deploy(
                old_revision,
                new_revision,
                artifacts,
                config_state,
            )
        finally:
            if os.path.exists(worktree_path):
                self.runner.run(
                    [
                        "git",
                        "-C",
                        self.repository_path,
                        "worktree",
                        "remove",
                        "--force",
                        worktree_path,
                    ],
                    check=False,
                )
            shutil.rmtree(temporary_root, ignore_errors=True)

    def _build(self, worktree_path, script_path):
        if script_path:
            relative_script_path = os.path.relpath(
                script_path,
                self.repository_path,
            )
            worktree_script_path = os.path.join(
                worktree_path,
                relative_script_path,
            )
            if not os.path.isfile(worktree_script_path):
                raise ServerUpdateError(
                    "Configured build script does not exist in the new "
                    "revision"
                )
            self.write_log(
                "Running repository build script: {}".format(
                    relative_script_path
                )
            )
            self.runner.run(
                ["/bin/bash", worktree_script_path],
                cwd=worktree_path,
            )
            return

        dme_path = self._worktree_path(
            worktree_path,
            self.server.dme_name,
        )
        if not os.path.isfile(dme_path):
            raise ServerUpdateError("Configured DME file does not exist")
        self.write_log(
            "Running DreamMaker compiler for {}".format(
                self.server.dme_name
            )
        )
        self.runner.run(
            [
                self.server.dream_maker_binary,
                "-clean",
                self.server.dme_name,
            ],
            cwd=worktree_path,
        )

    def _worktree_path(self, worktree_path, relative_path):
        candidate_path = os.path.abspath(
            os.path.join(worktree_path, relative_path)
        )
        try:
            common_path = os.path.commonpath(
                (os.path.abspath(worktree_path), candidate_path)
            )
        except ValueError:
            common_path = None
        if common_path != os.path.abspath(worktree_path):
            raise ServerUpdateError("Configured path leaves the repository")
        return candidate_path

    def _collect_artifacts(self, worktree_path):
        dme_path = self._worktree_path(worktree_path, self.server.dme_name)
        artifact_base = os.path.splitext(dme_path)[0]
        dmb_path = artifact_base + ".dmb"
        resource_path = artifact_base + ".rsc"
        required_paths = [resource_path, dmb_path]
        missing_paths = [
            path for path in required_paths if not os.path.isfile(path)
        ]
        if missing_paths:
            raise ServerUpdateError(
                "Build did not produce: {}".format(
                    ", ".join(os.path.basename(path) for path in missing_paths)
                )
            )

        dynamic_resource_path = artifact_base + ".dyn.rsc"
        if os.path.isfile(dynamic_resource_path):
            required_paths.insert(1, dynamic_resource_path)

        return [
            (
                artifact_path,
                os.path.relpath(artifact_path, worktree_path),
            )
            for artifact_path in required_paths
        ]

    def _prepare_artifacts(self, temporary_root, worktree_path):
        deploy_script_path = os.path.join(
            worktree_path,
            "tools",
            "deploy.sh",
        )
        if not os.path.isfile(deploy_script_path):
            self.write_log(
                "Repository deploy script not found; publishing DM "
                "artifacts only"
            )
            return self._collect_artifacts(worktree_path)

        deployment_path = os.path.join(temporary_root, "deployment")
        os.makedirs(deployment_path)
        self.write_log(
            "Collecting runtime artifacts with tools/deploy.sh"
        )
        self.runner.run(
            [
                "/bin/bash",
                deploy_script_path,
                deployment_path,
                worktree_path,
            ],
            cwd=worktree_path,
        )

        # A repository deployment must still contain the compiled game.
        self._collect_artifacts(deployment_path)

        config_relative_path = self._config_relative_path()
        if config_relative_path == os.curdir:
            config_relative_path = None
        elif config_relative_path is not None:
            config_relative_path = os.path.normpath(config_relative_path)

        artifacts = []
        skipped_config_files = 0
        for directory_path, directory_names, file_names in os.walk(
            deployment_path
        ):
            directory_names.sort()
            file_names.sort()
            for file_name in file_names:
                artifact_path = os.path.join(directory_path, file_name)
                relative_path = os.path.relpath(
                    artifact_path,
                    deployment_path,
                )
                normalized_path = os.path.normpath(relative_path)
                if config_relative_path and (
                    normalized_path == config_relative_path
                    or normalized_path.startswith(
                        config_relative_path + os.path.sep
                    )
                ):
                    skipped_config_files += 1
                    continue
                artifacts.append((artifact_path, relative_path))

        if skipped_config_files:
            self.write_log(
                "Skipped {} config files from deployment artifacts".format(
                    skipped_config_files
                )
            )
        self.write_log(
            "Collected {} runtime artifacts for publication".format(
                len(artifacts)
            )
        )
        return artifacts

    def _config_relative_path(self):
        config_path = os.path.abspath(self.server.configs_path)
        try:
            common_path = os.path.commonpath(
                (self.repository_path, config_path)
            )
        except ValueError:
            return None
        if common_path != self.repository_path:
            return None
        return os.path.relpath(config_path, self.repository_path)

    def _prepare_config(self, temporary_root, worktree_path, old_revision):
        relative_path = self._config_relative_path()
        if relative_path is None:
            self.write_log(
                "Config path is outside the repository; config sync skipped"
            )
            return None

        incoming_path = self._worktree_path(worktree_path, relative_path)
        if not os.path.isdir(incoming_path):
            self.write_log(
                "The new revision has no configured config directory; "
                "config sync skipped"
            )
            return None

        config_path = os.path.abspath(self.server.configs_path)
        local_path = os.path.join(temporary_root, "config-local")
        if os.path.isdir(config_path):
            shutil.copytree(config_path, local_path, symlinks=True)

        base_root = os.path.join(temporary_root, "config-base")
        os.makedirs(base_root)
        git_relative_path = relative_path.replace(os.path.sep, "/")
        object_name = "{}:{}".format(old_revision, git_relative_path)
        has_old_config = self.runner.capture(
            ["git", "-C", self.repository_path, "cat-file", "-e", object_name],
            check=False,
        )[0] == 0
        base_path = os.path.join(base_root, relative_path)
        if has_old_config:
            archive_path = os.path.join(temporary_root, "config-base.tar")
            self.runner.run(
                [
                    "git",
                    "-C",
                    self.repository_path,
                    "archive",
                    "--format=tar",
                    "--output",
                    archive_path,
                    old_revision,
                    "--",
                    git_relative_path,
                ]
            )
            self.runner.run(["tar", "-xf", archive_path, "-C", base_root])

        merged_path = os.path.join(temporary_root, "config-merged")
        merge_config_directories(
            local_path,
            base_path,
            incoming_path,
            merged_path,
        )

        link_target = None
        link_destination = None
        if os.path.islink(config_path):
            link_target = os.readlink(config_path)
            link_destination = os.path.realpath(config_path)

        return {
            "config_path": config_path,
            "local_path": local_path,
            "merged_path": merged_path,
            "link_target": link_target,
            "destination_path": link_destination or config_path,
        }

    def _deploy(self, old_revision, new_revision, artifacts, config_state):
        artifact_backups = []
        checkout_completed = False

        try:
            self.runner.run(
                [
                    "git",
                    "-C",
                    self.repository_path,
                    "checkout",
                    "-f",
                    new_revision,
                ]
            )
            checkout_completed = True
            if config_state:
                self._install_config(config_state, "merged_path")
            artifact_backups = self._publish_artifacts(artifacts)
        except Exception:
            self._restore_artifacts(artifact_backups)
            if checkout_completed:
                self.runner.run(
                    [
                        "git",
                        "-C",
                        self.repository_path,
                        "checkout",
                        "-f",
                        old_revision,
                    ],
                    check=False,
                )
                if config_state and os.path.isdir(config_state["local_path"]):
                    self._install_config(config_state, "local_path")
            raise
        else:
            self._remove_artifact_backups(artifact_backups)
            self.write_log("Update deployed successfully")

    def _install_config(self, config_state, source_key):
        destination_path = config_state["destination_path"]
        source_path = config_state[source_key]
        self._replace_directory(source_path, destination_path)

        if config_state["link_target"] is None:
            return

        config_path = config_state["config_path"]
        self._remove_path(config_path)
        os.symlink(config_state["link_target"], config_path)

    def _replace_directory(self, source_path, destination_path):
        parent_path = os.path.dirname(destination_path)
        if not os.path.exists(parent_path):
            os.makedirs(parent_path)

        staged_path = tempfile.mkdtemp(
            prefix=".hub-config-new-",
            dir=parent_path,
        )
        os.rmdir(staged_path)
        shutil.copytree(source_path, staged_path, symlinks=True)

        backup_path = None
        try:
            if os.path.lexists(destination_path):
                backup_path = destination_path + ".hub-old-" + uuid.uuid4().hex
                os.rename(destination_path, backup_path)
            os.rename(staged_path, destination_path)
        except Exception:
            self._remove_path(staged_path)
            if backup_path and not os.path.lexists(destination_path):
                os.rename(backup_path, destination_path)
            raise
        else:
            if backup_path:
                self._remove_path(backup_path)

    def _publish_artifacts(self, artifacts):
        prepared_artifacts = []
        backups = []
        token = uuid.uuid4().hex

        try:
            for source_path, relative_path in artifacts:
                destination_path = self._repository_artifact_path(
                    relative_path
                )
                destination_directory = os.path.dirname(destination_path)
                if not os.path.exists(destination_directory):
                    os.makedirs(destination_directory)
                staged_path = os.path.join(
                    destination_directory,
                    ".{}.hub-new-{}".format(
                        os.path.basename(destination_path),
                        token,
                    ),
                )
                os.replace(source_path, staged_path)
                prepared_artifacts.append((staged_path, destination_path))

            for staged_path, destination_path in prepared_artifacts:
                backup_path = None
                if os.path.lexists(destination_path):
                    backup_path = destination_path + ".hub-old-" + token
                    os.replace(destination_path, backup_path)
                backups.append((destination_path, backup_path))
                os.replace(staged_path, destination_path)
        except Exception:
            self._restore_artifacts(backups)
            for staged_path, _ in prepared_artifacts:
                if os.path.lexists(staged_path):
                    self._remove_path(staged_path)
            raise

        return backups

    def _repository_artifact_path(self, relative_path):
        destination_path = os.path.abspath(
            os.path.join(self.repository_path, relative_path)
        )
        if not self._is_inside_repository(destination_path):
            raise ServerUpdateError("Build artifact leaves the repository")
        return destination_path

    def _restore_artifacts(self, backups):
        for destination_path, backup_path in reversed(backups):
            if os.path.lexists(destination_path):
                self._remove_path(destination_path)
            if backup_path and os.path.lexists(backup_path):
                os.replace(backup_path, destination_path)

    def _remove_artifact_backups(self, backups):
        for _, backup_path in backups:
            if backup_path and os.path.lexists(backup_path):
                self._remove_path(backup_path)

    def _remove_path(self, path):
        if not os.path.lexists(path):
            return
        if os.path.isdir(path) and not os.path.islink(path):
            shutil.rmtree(path)
        else:
            os.unlink(path)
