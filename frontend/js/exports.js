/* exports.js: coordinator data export */

function exportSettingsHtml() {
    return `
        <section class="card">
            <h2>Data Export</h2>

            <p class="mu">
                Download SR PITSYNC data as CSV files.
            </p>

            <div style="display:grid;gap:12px;margin-top:18px">

                <button class="pri" id="downloadMembers">
                    ↓ Download Members CSV
                </button>

                <button class="pri" id="downloadAttendance">
                    ↓ Download Attendance CSV
                </button>

                <button class="pri" id="downloadTasks">
                    ↓ Download Tasks CSV
                </button>

            </div>

            <p class="mu" style="margin-top:16px;font-size:.85rem">
                CSV exports are available only to coordinators.
            </p>
        </section>
    `;
}


async function downloadCSV(endpoint, filename) {

    try {

        const response = await fetch(
            `http://127.0.0.1:8000${endpoint}`,
            {
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${getToken()}`
                }
            }
        );

        if (!response.ok) {

            if (response.status === 401) {
                throw new Error("Your session has expired. Please log in again.");
            }

            if (response.status === 403) {
                throw new Error("Only coordinators can download this file.");
            }

            const text = await response.text();
            throw new Error(text || "Download failed.");
        }

        const blob = await response.blob();

        const url = window.URL.createObjectURL(blob);

        const link = document.createElement("a");
        link.href = url;
        link.download = filename;

        document.body.appendChild(link);
        link.click();
        link.remove();

        window.URL.revokeObjectURL(url);

        toast(`${filename} downloaded successfully`);

    } catch (error) {

        toast(error.message || "Could not download CSV", true);

    }
}


function setupExportButtons() {

    const membersButton = document.querySelector("#downloadMembers");
    const attendanceButton = document.querySelector("#downloadAttendance");
    const tasksButton = document.querySelector("#downloadTasks");

    if (membersButton) {
        membersButton.onclick = () =>
            downloadCSV(
                "/export/members.csv",
                "pitsync_members.csv"
            );
    }

    if (attendanceButton) {
        attendanceButton.onclick = () =>
            downloadCSV(
                "/export/attendance.csv",
                "pitsync_attendance.csv"
            );
    }

    if (tasksButton) {
        tasksButton.onclick = () =>
            downloadCSV(
                "/export/tasks.csv",
                "pitsync_tasks.csv"
            );
    }
}


/*
 * Add the Settings page to the existing VIEWS object.
 */
VIEWS.settings = {
    html: exportSettingsHtml,
    bind: setupExportButtons
};