# SR PITSYNC Frontend

Plain HTML, CSS and JavaScript. No build step.

## Run it
1. Start the backend first (`uvicorn main:app --reload` in the backend folder).
2. In THIS folder run: `python -m http.server 5500`
3. Open http://localhost:5500 and log in (for example taha@example.com / ChangeMe123!).

Do not double-click index.html: browsers block API calls from file:// pages.

## Go live
- Change `API_BASE` at the top of `js/api.js` to your backend address (use https).
- Add your website address to `CORS_ORIGINS` in the backend `.env`.
- Host this folder on Netlify, Vercel or GitHub Pages.

## Files
| File | Job |
|---|---|
| js/api.js | The only file that talks to the backend |
| js/dateTime.js | Clock synced to the server |
| js/ui.js | Shared state and helpers |
| js/car3d.js | Interactive 3D car and subsystem pop-ups |
| js/auth.js | Login and logout |
| js/app.js | Page shell, tabs, start-up |
| js/workshop.js | Who's In, dashboard, timing |
| js/attendance.js | My attendance |
| js/tasks.js | Assign and update tasks |
| js/profile.js | Profile, photo, password |
| js/members.js | Coordinators add, edit, remove members |
| js/notifications.js | Email outbox |
