/* app.js: page shell, theme toggle, tab switching, live clock and start-up */

let vseq = 0;


/* =========================================================
   BRIGHT / DARK MODE
   ========================================================= */

function applyBrightness() {
    const bright = localStorage.getItem('pitsync-bright') === 'true';

    document.body.classList.toggle('bright-mode', bright);

    const btn = $('#themeToggle');

    if (btn) {
        btn.textContent = bright ? '🌙' : '☀️';
        btn.title = bright
            ? 'Switch to dark mode'
            : 'Switch to bright mode';
        btn.setAttribute(
            'aria-label',
            bright
                ? 'Switch to dark mode'
                : 'Switch to bright mode'
        );
    }
}


function toggleBrightness() {
    const bright =
        localStorage.getItem('pitsync-bright') === 'true';

    localStorage.setItem(
        'pitsync-bright',
        String(!bright)
    );

    applyBrightness();
}


/* =========================================================
   APPLICATION SHELL
   ========================================================= */

function shell() {

    const co = S.me.is_coordinator;

    const tabs = co
        ? [
            ['pit', "Who's In"],
            ['dash', 'Dashboard'],
            ['tasks', 'Tasks'],
            ['team', 'Team'],
            ['time', 'Timing'],
            ['mail', 'Outbox'],
            ['prof', 'Profile'],
            ['settings', 'Settings']
        ]
        : [
            ['pit', "Who's In"],
            ['att', 'My Attendance'],
            ['tasks', 'My Tasks'],
            ['prof', 'Profile']
        ];


    $('#app').innerHTML = `
        <div class="wrap">

            <header>

                <img
                    src="assets/images/logo.png"
                    alt="STES Racing"
                >

                <div class="clock">

                    <div class="clock-actions">

                        <button
                            id="themeToggle"
                            class="theme-toggle"
                            type="button"
                            title="Switch to bright mode"
                            aria-label="Switch to bright mode"
                        >
                            ☀️
                        </button>

                        <button
                            id="out"
                            type="button"
                            style="padding:2px 8px;margin-top:3px;font-size:.75rem"
                        >
                            Log out
                        </button>

                    </div>

                    <span id="clk"></span>

                    <small id="dt"></small>

                </div>

            </header>


            <div id="hero">

                <div class="sw">
                    ${THEMES.map(t => `
                        <button
                            aria-label="${t[0]} theme"
                            data-th="${t[0]}"
                            style="--c:${t[1]}"
                        ></button>
                    `).join('')}
                </div>

                <div class="tag" id="tg">
                    SR PITSYNC ·
                    ${co ? 'Coordinator' : 'Member'}:
                    ${esc(S.me.name)}
                </div>

            </div>


            <div class="row chips" id="chips"></div>


            <nav>
                ${tabs.map(t => `
                    <button data-t="${t[0]}">
                        ${t[1]}
                    </button>
                `).join('')}
            </nav>


            <main id="main"></main>

        </div>
    `;


    /* Logout */
    $('#out').onclick = () => logout();


    /* Bright / Dark toggle */
    $('#themeToggle').onclick = () => {
        toggleBrightness();
    };


    /* Existing color themes */
    document
        .querySelectorAll('[data-th]')
        .forEach(b => {
            b.onclick = () => setTheme(b.dataset.th);
        });


    /* Navigation */
    document
        .querySelectorAll('nav button')
        .forEach(b => {
            b.onclick = () => go(b.dataset.t);
        });


    /* 3D hero */
    init3D();


    /* Restore selected brightness mode */
    applyBrightness();


    /* Open current tab */
    go(S.tab);


    /* Start clock */
    tick();
}


/* =========================================================
   NAVIGATION
   ========================================================= */

function go(t) {

    S.tab = t;

    document
        .querySelectorAll('nav button')
        .forEach(b => {
            b.classList.toggle(
                'on',
                b.dataset.t === t
            );
        });

    view();
}


/* =========================================================
   VIEW LOADING
   ========================================================= */

async function view(quiet) {

    const id = ++vseq;

    const v = VIEWS[S.tab];

    if (!v || !$('#main')) return;


    if (!quiet) {

        $('#main').innerHTML = `
            <div
                class="load"
                style="height:25vh"
            >
                <div class="spin"></div>
            </div>
        `;
    }


    try {

        if (v.load) {
            await v.load();
        }

    } catch (e) {

        toast(e.message, true);

    }


    if (id !== vseq || !$('#main')) {
        return;
    }


    try {

        $('#main').innerHTML = v.html();

        if (v.bind) {
            v.bind();
        }

        chips();

    } catch (e) {

        $('#main').innerHTML = `
            <p class="err">
                Could not show this page.
            </p>
        `;
    }
}


/* =========================================================
   CLOCK
   ========================================================= */

function tick() {

    const c = $('#clk');

    if (c) {

        const d = srv();

        c.textContent =
            d.toLocaleTimeString(
                'en-GB',
                {
                    timeZone: TZ
                }
            );

        $('#dt').textContent =
            d.toLocaleDateString(
                'en-IN',
                {
                    timeZone: TZ,
                    weekday: 'long',
                    day: 'numeric',
                    month: 'short',
                    year: 'numeric'
                }
            );
    }


    const cd = $('#cd');

    if (cd) {
        cd.innerHTML = cdText();
    }


    /* Automatically refresh when date changes */

    if (
        S.me &&
        S.day &&
        todayStr() !== S.day
    ) {

        S.day = todayStr();

        view();
    }
}


/* =========================================================
   AUTO REFRESH
   ========================================================= */

setInterval(
    async () => {

        if (
            !S.me ||
            document.hidden ||
            !['pit', 'dash'].includes(S.tab) ||
            document.querySelector('.modal') ||
            document.activeElement.id === 'sq'
        ) {
            return;
        }


        try {

            await Promise.all([
                loadWho(),
                loadTasks()
            ]);

            view(true);

        } catch (e) {}

    },
    30000
);


/* =========================================================
   ENTER APPLICATION
   ========================================================= */

async function enter() {

    await loadW();

    await Promise.all([
        loadWho(),
        loadTasks()
    ]);

    S.day = todayStr();

    S.tab =
        S.me.must_change_password
            ? 'prof'
            : 'pit';

    shell();


    if (S.me.must_change_password) {

        toast(
            'Please set a new password'
        );
    }
}


/* =========================================================
   START APPLICATION
   ========================================================= */

async function start() {

    try {

        setTheme(
            localStorage.getItem(
                'pitsync-theme'
            ) || 'volt'
        );

    } catch (e) {}


    if (!getToken()) {

        return loginView();
    }


    try {

        S.me = await api('/members/me');

        await enter();

    } catch (e) {

        loginView();

    }
}


/* =========================================================
   START
   ========================================================= */

start();

setInterval(tick, 1000);