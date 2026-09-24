/* profile.js: complete profile, photo, email, password */

function profV() {
  const m = S.me;

  const sel = (list, v) =>
    list.map(y => `<option ${v === y ? 'selected' : ''}>${y}</option>`).join('');

  return `
    <h2>My profile</h2>

    ${m.must_change_password
      ? '<div class="card" style="border-color:var(--y)">First login: please set a new password below.</div>'
      : ''
    }

    ${m.profile_complete
      ? ''
      : '<div class="card" style="border-color:var(--y);margin-top:8px">Complete your profile so the team can reach you.</div>'
    }

    <div class="card row" style="margin-top:8px">
      ${av(m)}
      <div>
        <b>${esc(m.name)}</b>
        <div class="mu">${esc(m.role_text)}</div>
      </div>
    </div>

    <!-- PROFILE -->
    <div class="card" style="margin-top:8px">

      <label for="ph">Photo (JPG, PNG or WEBP, max 2 MB)</label>
      <input type="file" id="ph" accept="image/jpeg,image/png,image/webp">

      <label for="pp">Phone (digits only)</label>
      <input id="pp" value="${esc(m.phone)}" inputmode="tel">

      <label for="pb">Branch</label>
      <input id="pb" value="${esc(m.branch)}">

      <label for="py">Year</label>
      <select id="py">
        ${sel(['', 'FE', 'SE', 'TE', 'BE'], m.year)}
      </select>

      <label for="pg">Blood group</label>
      <select id="pg">
        ${sel(
          ['', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'],
          m.blood_group
        )}
      </select>

      <p>
        <button class="pri" id="ps">Save profile</button>
      </p>
    </div>


    <!-- CHANGE EMAIL -->
    <h2>Change email</h2>

    <div class="card">

      <label>Current email</label>
      <input
        value="${esc(m.email)}"
        disabled
      >

      <label for="ce">New email</label>
      <input
        id="ce"
        type="email"
        autocomplete="email"
        placeholder="Enter new email"
      >

      <label for="cep">Current password</label>
      <input
        id="cep"
        type="password"
        autocomplete="current-password"
        placeholder="Enter your current password"
      >

      <p>
        <button id="cebtn">Change email</button>
      </p>

    </div>


    <!-- CHANGE PASSWORD -->
    <h2>Change password</h2>

    <div class="card">

      <label for="op">Current password</label>
      <input
        id="op"
        type="password"
        autocomplete="current-password"
      >

      <label for="np">New password (8+ characters)</label>
      <input
        id="np"
        type="password"
        autocomplete="new-password"
      >

      <p>
        <button id="pc">Change password</button>
      </p>

    </div>
  `;
}


function profB() {

  // SAVE PROFILE
  $('#ps').onclick = () =>
    run(async () => {

      const body = {};

      [
        ['phone', 'pp'],
        ['branch', 'pb'],
        ['year', 'py'],
        ['blood_group', 'pg']
      ].forEach(([k, i]) => {

        const v = $('#' + i).value.trim();

        if (v) {
          body[k] = v;
        }

      });

      S.me = await api('/members/me', {
        method: 'PATCH',
        body
      });

      toast('Profile saved');
      view(true);
    });


  // PHOTO
  $('#ph').onchange = e =>
    run(async () => {

      const f = e.target.files[0];

      if (!f) return;

      const fd = new FormData();

      fd.append('file', f);

      S.me = await api('/members/me/photo', {
        method: 'POST',
        form: fd
      });

      toast('Photo updated');

      await loadWho();

      view(true);
    });


  // CHANGE EMAIL
  $('#cebtn').onclick = () =>
    run(async () => {

      const newEmail = $('#ce').value.trim();
      const currentPassword = $('#cep').value;

      if (!newEmail) {
        toast('Please enter your new email');
        return;
      }

      if (!currentPassword) {
        toast('Please enter your current password');
        return;
      }

      S.me = await api('/auth/change-email', {
        method: 'POST',
        body: {
          current_password: currentPassword,
          new_email: newEmail
        }
      });

      toast('Email changed successfully');

      await loadWho();

      view(true);
    });


  // CHANGE PASSWORD
  $('#pc').onclick = () =>
    run(async () => {

      await api('/auth/change-password', {
        method: 'POST',
        body: {
          old_password: $('#op').value,
          new_password: $('#np').value
        }
      });

      S.me.must_change_password = false;

      toast('Password changed');

      view(true);
    });
}


VIEWS.prof = {
  html: profV,
  bind: profB,
  load: async () => {
    S.me = await api('/members/me');
  }
};