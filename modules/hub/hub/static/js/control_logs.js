(function () {
    "use strict";

    var output = document.getElementById("server-live-log");
    if (!output) {
        return;
    }

    var requestInProgress = false;
    var source = output.getAttribute("data-source");

    function refreshLogs() {
        if (requestInProgress || document.hidden) {
            return;
        }

        requestInProgress = true;
        var followOutput = output.scrollHeight - output.scrollTop
            - output.clientHeight < 40;

        window.fetch(source, {
            credentials: "same-origin",
            headers: {"X-Requested-With": "XMLHttpRequest"},
            cache: "no-store"
        })
            .then(function (response) {
                if (!response.ok) {
                    throw new Error("Log request failed: " + response.status);
                }
                return response.json();
            })
            .then(function (data) {
                output.textContent = data.lines.join("\n");
                if (followOutput) {
                    output.scrollTop = output.scrollHeight;
                }
            })
            .catch(function (error) {
                window.console.error(error);
            })
            .then(function () {
                requestInProgress = false;
            });
    }

    output.scrollTop = output.scrollHeight;
    refreshLogs();
    var refreshTimer = window.setInterval(refreshLogs, 2000);
    window.addEventListener("pagehide", function () {
        window.clearInterval(refreshTimer);
    });
}());
