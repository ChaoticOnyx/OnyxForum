import datetime

from flaskbb.extensions import celery

from hub.services.control_logs import append_update_log

from ...servers_config import ServerDescriptor
from .services.server_update import ServerUpdateService


def _timestamp():
    return datetime.datetime.now().strftime("[%d.%m.%Y %H:%M:%S]\t")


@celery.task
def update_server_async(server_id, output_file_path):
    append_update_log(
        output_file_path,
        _timestamp() + "Celery worker accepted the update task",
    )

    with open(
        output_file_path,
        "a",
        encoding="utf-8",
        buffering=1,
    ) as output_file:
        def write_log(message):
            output_file.write(_timestamp() + message + "\n")
            output_file.flush()

        try:
            server = ServerDescriptor.query.get(server_id)
            if server is None:
                raise RuntimeError("Server descriptor does not exist")

            write_log("Update started")
            ServerUpdateService(server, write_log).run()
        except Exception as exception:
            write_log("Update failed: {}".format(exception))
            raise
        else:
            write_log("Update finished")
