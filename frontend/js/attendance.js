/* attendance.js: my attendance. The server refuses any day except today. */

const mine = () =>
    rowOf(S.me.id) || {
        status: 'not_updated',
        eta: '',
        time_in: '',
        time_out: ''
    };

function attV() {
    const a = mine();
    const s = a.status;
    const p = todayStr().split('-').map(Number);

    const strip = [-3, -2, -1, 0, 1, 2, 3]
        .map(o => {
            const x = new Date(
                p[0],
                p[1] - 1,
                p[2] + o
            );

            return `
                <button ${o ? 'data-lock="1"' : 'class="on"'}>
                    ${x.toLocaleDateString('en-IN', { weekday: 'short' })}<br>
                    ${x.getDate()}${o ? ' 🔒' : ''}
                </button>
            `;
        })
        .join('');

    return `
        <h2>My attendance</h2>

        <div class="dates">
            ${strip}
        </div>

        <p class="mu">
            Only today can be edited. Past and future days are locked for everyone.
        </p>

        <div class="card">
            <p>
                Status:
                <span class="pill" style="--c:${colors[s]}">
                    ${label[s]}
                </span>
            </p>

            <div class="row">
                <button class="${s === 'present' ? 'on' : ''}" data-a="present">
                    I'm here
                </button>

                <button class="${s === 'coming' ? 'on' : ''}" data-a="coming">
                    Coming
                </button>

                <button class="dng" data-a="absent">
                    Absent
                </button>
            </div>

            <label for="eta">ETA (if coming)</label>

            <input
                type="time"
                id="eta"
                value="${a.eta || ''}"
            >

            <div class="row" style="margin-top:12px">
                <button data-a="in">
                    Time in: ${a.time_in || '--:--'}
                </button>

                <button data-a="out">
                    Time out: ${a.time_out || '--:--'}
                </button>
            </div>
        </div>
    `;
}

async function setAtt(k) {
    const eta = $('#eta').value;

    if (k === 'in') {
        await api('/attendance/today/time-in', {
            method: 'POST'
        });
    } else if (k === 'out') {
        await api('/attendance/today/time-out', {
            method: 'POST'
        });
    } else {
        await api('/attendance/today', {
            method: 'PUT',
            body: {
                status: k,
                ...(k === 'coming' && eta ? { eta } : {})
            }
        });
    }

    if (k === 'absent') {
        toast('Marked absent. Coordinators were emailed.');
    }

    /*
     * loadWho() is called dynamically here.
     * This prevents the browser from trying to resolve
     * loadWho before the file defining it has loaded.
     */
    if (typeof loadWho === 'function') {
        await loadWho();
    }

    view(true);
}

function attB() {
    document.querySelectorAll('[data-lock]').forEach(b => {
        b.onclick = () =>
            toast('Locked. Only today can be edited.', true);
    });

    document.querySelectorAll('[data-a]').forEach(b => {
        b.onclick = () =>
            run(() => setAtt(b.dataset.a));
    });

    $('#eta').onchange = () =>
        run(async () => {
            if (
                mine().status === 'coming' &&
                $('#eta').value
            ) {
                await api('/attendance/today', {
                    method: 'PUT',
                    body: {
                        eta: $('#eta').value
                    }
                });

                if (typeof loadWho === 'function') {
                    await loadWho();
                }

                view(true);
            }
        });
}

/*
 * Do NOT write:
 * VIEWS.att={html:attV,bind:attB,load:loadWho};
 *
 * because that tries to access loadWho immediately.
 */
VIEWS.att = {
    html: attV,
    bind: attB,
    load: async () => {
        if (typeof loadWho === 'function') {
            await loadWho();
        }
    }
};