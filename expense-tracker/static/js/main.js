(function () {
    var KEY = 'spendly-theme';
    var html = document.documentElement;
    var btn = document.getElementById('themeToggle');

    function applyTheme(theme) {
        if (theme === 'dark') {
            html.setAttribute('data-theme', 'dark');
        } else {
            html.removeAttribute('data-theme');
        }
        if (btn) {
            btn.setAttribute('aria-label',
                theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode');
        }
    }

    function stored() {
        try { return localStorage.getItem(KEY); } catch (e) { return null; }
    }

    function save(theme) {
        try {
            if (theme === 'dark') { localStorage.setItem(KEY, 'dark'); }
            else { localStorage.removeItem(KEY); }
        } catch (e) {}
    }

    applyTheme(stored() || 'light');

    if (btn) {
        btn.addEventListener('click', function () {
            var next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            applyTheme(next);
            save(next);
        });
    }
}());
