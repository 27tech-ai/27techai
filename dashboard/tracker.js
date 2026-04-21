/**
 * 27TechAI - Tracking Snippet
 * Add this script to your website's index.html before </body>
 * to enable visitor tracking and click analytics in the dashboard.
 */
(function() {
    // Change this to your dashboard URL
    const DASHBOARD_URL = 'http://localhost:5000';

    function track(event, data) {
        try {
            fetch(DASHBOARD_URL + '/api/tracking', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(Object.assign({
                    event: event,
                    page: window.location.pathname,
                    referrer: document.referrer,
                    user_agent: navigator.userAgent,
                    device: /Mobi|Android/i.test(navigator.userAgent) ? 'mobile' : 'desktop'
                }, data))
            }).catch(function() {});
        } catch(e) {}
    }

    // Track page view
    track('page_view', {});

    // Track script clicks
    document.addEventListener('click', function(e) {
        var link = e.target.closest('a');
        if (link) {
            var card = link.closest('[class*="card"]');
            if (card) {
                var titleEl = card.querySelector('h3');
                if (titleEl) {
                    track('script_click', {
                        script_title: titleEl.textContent.trim()
                    });
                }
            }
        }
    });
})();
