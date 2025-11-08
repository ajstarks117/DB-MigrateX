function applyMigrations() {
    const confirmRun = confirm("Are you sure you want to apply all pending migrations?");
    
    if (!confirmRun) return;

    // Redirect to /apply route
    window.location.href = "/apply";
}


function rollbackThis(migrationId) {
    const ok = confirm(`Rollback migration ${migrationId}? This will run the down SQL for that migration.`);
    if (!ok) return;

    fetch(`/rollback/${encodeURIComponent(migrationId)}`, {
        method: 'POST',
        headers: {
            'Accept': 'text/plain'
        }
    }).then(async (resp) => {
        const text = await resp.text();
        if (!resp.ok) {
            showToast(text || 'Rollback failed', true);
            return;
        }
        showToast(text || 'Rolled back successfully', false);
        setTimeout(() => { window.location.href = '/'; }, 900);
    }).catch((err) => {
        showToast('Network error: ' + err, true);
    });
}

function rollbackTo(migrationId) {
    const ok = confirm(`Rollback to ${migrationId}? This will remove any migrations applied after this one.`);
    if (!ok) return;

    fetch(`/rollback_to/${encodeURIComponent(migrationId)}`, {
        method: 'POST',
        headers: {
            'Accept': 'text/plain'
        }
    }).then(async (resp) => {
        const text = await resp.text();
        if (!resp.ok) {
            showToast(text || 'Rollback failed', true);
            return;
        }
        showToast(text || 'Rolled back successfully', false);
        setTimeout(() => { window.location.href = '/'; }, 900);
    }).catch((err) => {
        showToast('Network error: ' + err, true);
    });
}


function showToast(message, isError) {
    const el = document.getElementById('toast');
    if (!el) {
        alert(message);
        return;
    }
    el.textContent = message;
    el.className = 'toast show ' + (isError ? 'error' : 'success');
    el.style.display = 'block';
    // hide after 3s
    setTimeout(() => {
        el.className = 'toast';
        setTimeout(() => { el.style.display = 'none'; }, 250);
    }, 3000);
}
