document.addEventListener('DOMContentLoaded', () => {
    if (typeof BitcoinLabsApp !== 'undefined') {
        BitcoinLabsApp.init({
            isApp: true,
            appName: 'OSS App Stats',
            appHomeUrl: 'index.html'
        });

        document.body.classList.add('has-nav');
    }
});
