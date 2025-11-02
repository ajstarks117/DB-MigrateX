function applyMigrations() {
    const confirmRun = confirm("Are you sure you want to apply all pending migrations?");
    
    if (!confirmRun) return;

    // Redirect to /apply route
    window.location.href = "/apply";
}
