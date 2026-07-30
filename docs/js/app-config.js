document.addEventListener('DOMContentLoaded', () => {
    if (typeof BitcoinLabsApp !== 'undefined') {
        BitcoinLabsApp.init({
            isApp: true,
            appName: 'OSS App Stats',
            appHomeUrl: 'index.html',

            suiteLinks: [
                { name: 'orange-dev-tracker', url: 'https://tracker.bitcoindatalabs.org', icon: 'fas fa-chart-line' },
                { name: 'orange-dev-network', url: 'https://network.bitcoindatalabs.org', icon: 'fas fa-project-diagram' },
                { name: 'This Week in Bitcoin', url: 'https://twib.bitcoindatalabs.org', icon: 'fas fa-newspaper' }
            ]
        });

        document.body.classList.add('has-nav');
    }
});
