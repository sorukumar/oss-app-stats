/**
 * OSS App Stats — Main Application Logic
 * Reads pre-built JSON data and renders the analytics dashboard.
 */

// ─── Configuration ──────────────────────────────────────────────────────────
const DATA_BASE = (() => {
    const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    return isLocal ? 'data/' : 'data/';
})();

const PLATFORM_COLORS = {
    'Windows': '#0078D4',
    'macOS': '#E8916B',
    'Linux': '#FFB000',
    'Source': '#8293AB',
    'Signatures': '#D4A298',
    'Other': '#5F6C7E',
};

// ─── Utilities ──────────────────────────────────────────────────────────────
function formatNumber(n) {
    if (n === null || n === undefined) return '—';
    if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
    if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K';
    return n.toLocaleString();
}

function formatDate(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatDateShort(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' });
}

function daysSinceText(days) {
    if (days === null || days === undefined) return '—';
    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    return `${days}d ago`;
}

function freshnessBadge(days) {
    if (days === null || days === undefined) return '';
    if (days <= 7) return '<span class="freshness-badge freshness-hot">🔥 Active</span>';
    if (days <= 30) return '<span class="freshness-badge freshness-warm">Recent</span>';
    if (days <= 90) return '<span class="freshness-badge freshness-cool">Stable</span>';
    return '<span class="freshness-badge freshness-stale">Stale</span>';
}

function formatBytes(bytes) {
    if (!bytes) return '—';
    if (bytes >= 1_073_741_824) return (bytes / 1_073_741_824).toFixed(1) + ' GB';
    if (bytes >= 1_048_576) return (bytes / 1_048_576).toFixed(1) + ' MB';
    if (bytes >= 1_024) return (bytes / 1_024).toFixed(1) + ' KB';
    return bytes + ' B';
}

// ─── Data Loading ───────────────────────────────────────────────────────────
async function loadIndex() {
    const resp = await fetch(DATA_BASE + 'index.json');
    if (!resp.ok) throw new Error(`Failed to load index: ${resp.status}`);
    return resp.json();
}

async function loadProjectData(file) {
    const resp = await fetch(DATA_BASE + file);
    if (!resp.ok) throw new Error(`Failed to load ${file}: ${resp.status}`);
    return resp.json();
}

// ─── Rendering ──────────────────────────────────────────────────────────────

function renderLeaderboard(index) {
    // Only show projects with releases
    const projects = index.projects.filter(p => p.total_releases > 0);
    // Default sort by downloads
    const sorted = [...projects].sort((a, b) => b.total_downloads - a.total_downloads);

    let rows = sorted.map((p, i) => `
        <tr data-file="${p.file}" onclick="scrollToCard('${p.full_name}')" 
            data-downloads="${p.total_downloads}"
            data-category="${p.category}"
            data-releases="${p.total_releases}"
            data-stars="${p.stars}">
            <td class="rank-cell">${i + 1}</td>
            <td>
                <div class="project-name-cell">
                    <span class="project-name">${p.name}</span>
                    <span class="project-repo">${p.full_name}</span>
                </div>
            </td>
            <td class="number-cell">${p.total_downloads > 0 ? formatNumber(p.total_downloads) : '—'}</td>
            <td><span class="category-badge">${p.category}</span></td>
            <td class="number-cell hide-mobile">${p.total_releases}</td>
            <td class="tag-cell hide-mobile">${p.latest_version || '—'}</td>
            <td class="date-cell">${freshnessBadge(p.days_since_latest)} ${daysSinceText(p.days_since_latest)}</td>
            <td class="stars-cell hide-mobile"><i class="fas fa-star"></i>${formatNumber(p.stars)}</td>
        </tr>
    `).join('');

    return `
        <h2 class="section-header">
            <i class="fas fa-trophy"></i> Adoption Leaderboard
        </h2>
        <table class="leaderboard-table" id="leaderboard">
            <thead>
                <tr>
                    <th>#</th>
                    <th>Project</th>
                    <th class="sort-active" data-sort="downloads" style="cursor:pointer">Downloads <span class="sort-icon">▼</span></th>
                    <th data-sort="category" style="cursor:pointer">Category <span class="sort-icon">▼</span></th>
                    <th class="hide-mobile" data-sort="releases" style="cursor:pointer">Releases <span class="sort-icon">▼</span></th>
                    <th class="hide-mobile">Latest</th>
                    <th>Freshness</th>
                    <th class="hide-mobile" data-sort="stars" style="cursor:pointer">Stars <span class="sort-icon">▼</span></th>
                </tr>
            </thead>
            <tbody>${rows}</tbody>
        </table>
    `;
}

function renderPlatformBar(breakdown) {
    if (!breakdown || Object.keys(breakdown).length === 0) return '';

    const total = Object.values(breakdown).reduce((s, v) => s + v, 0);
    if (total === 0) return '';

    // Filter out Signatures from the bar display
    const displayPlatforms = Object.entries(breakdown)
        .filter(([k]) => k !== 'Signatures')
        .sort((a, b) => b[1] - a[1]);

    const barSegments = displayPlatforms.map(([platform, count]) => {
        const pct = (count / total) * 100;
        const colorClass = 'platform-' + platform.toLowerCase();
        const color = PLATFORM_COLORS[platform] || '#5F6C7E';
        return `<div class="platform-segment" style="width:${pct}%; background:${color};" title="${platform}: ${formatNumber(count)} (${pct.toFixed(1)}%)"></div>`;
    }).join('');

    const legendItems = displayPlatforms.map(([platform, count]) => {
        const color = PLATFORM_COLORS[platform] || '#5F6C7E';
        const pct = ((count / total) * 100).toFixed(0);
        return `<span class="platform-legend-item">
            <span class="platform-dot" style="background:${color};"></span>
            ${platform} <span class="platform-legend-value">${pct}%</span>
        </span>`;
    }).join('');

    return `
        <div class="platform-bar">${barSegments}</div>
        <div class="platform-legend">${legendItems}</div>
    `;
}

function renderProjectCard(data) {
    const p = data.project;
    const s = data.summary;

    // Get top 5 releases for the mini-table
    const topReleases = data.releases
        .filter(r => !r.is_draft)
        .slice(0, 5);

    const releasesTable = topReleases.length > 0 ? `
        <table class="releases-table">
            <thead>
                <tr>
                    <th>Version</th>
                    <th>Date</th>
                    <th style="text-align:right">Downloads</th>
                    <th style="text-align:right">Assets</th>
                </tr>
            </thead>
            <tbody>
                ${topReleases.map(r => `
                    <tr>
                        <td>
                            <a href="${r.html_url}" target="_blank" class="tag-link">${r.tag}</a>
                            ${r.is_prerelease ? '<span class="prerelease-badge">pre</span>' : ''}
                        </td>
                        <td class="date-cell">${formatDateShort(r.published_at)}</td>
                        <td class="number-cell">${formatNumber(r.total_downloads)}</td>
                        <td class="number-cell">${r.asset_count}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
        ${data.releases.length > 5 ? `<button class="releases-toggle" onclick="toggleAllReleases(this, '${p.full_name}')">Show all ${data.releases.filter(r => !r.is_draft).length} releases ▼</button>` : ''}
        <div class="all-releases-container" id="all-releases-${p.owner}-${p.repo}" style="display:none;"></div>
    ` : '<p style="color:var(--oss-text-secondary); font-size:0.85rem;">No release assets found on GitHub.</p>';

    const activeLabel = (p.category === 'Libraries & Tools' || p.category === 'Core Infrastructure') 
        ? 'Latest Ver. Downloads' 
        : 'Active Installs (Proxy)';

    return `
        <div class="project-card" id="card-${p.full_name.replace('/', '-')}">
            <div class="project-card-header">
                <div>
                    <h3 class="project-card-title">${p.name}</h3>
                    <div class="project-card-repo">
                        <a href="${p.html_url}" target="_blank">${p.full_name}</a>
                        ${p.language ? ` · ${p.language}` : ''}
                        ${p.license ? ` · ${p.license}` : ''}
                    </div>
                </div>
                <div class="project-card-stars">
                    <i class="fas fa-star"></i> ${formatNumber(p.stars)}
                </div>
            </div>
            ${p.description ? `<div class="project-card-description">${p.description}</div>` : ''}
            <div class="project-card-stats">
                <div class="mini-stat">
                    <div class="mini-stat-value">${formatNumber(s.total_downloads)}</div>
                    <div class="mini-stat-label">Total Downloads</div>
                </div>
                <div class="mini-stat">
                    <div class="mini-stat-value highlight">${data.releases && data.releases.length > 0 ? formatNumber(data.releases[0].total_downloads) : '—'}</div>
                    <div class="mini-stat-label">${activeLabel}</div>
                </div>
                <div class="mini-stat">
                    <div class="mini-stat-value">${s.total_releases}</div>
                    <div class="mini-stat-label">Releases</div>
                </div>
                <div class="mini-stat">
                    <div class="mini-stat-value">${s.avg_cadence_days ? s.avg_cadence_days + 'd' : '—'}</div>
                    <div class="mini-stat-label">Avg Cadence</div>
                </div>
                <div class="mini-stat">
                    <div class="mini-stat-value">${daysSinceText(s.days_since_latest)}</div>
                    <div class="mini-stat-label">Last Release</div>
                </div>
            </div>
            ${renderPlatformBar(s.platform_breakdown)}
            <div class="sparkline-container" style="height: 40px; margin-top: 15px; margin-bottom: 10px;">
                <canvas id="sparkline-${p.full_name.replace('/', '-')}"></canvas>
            </div>
            ${releasesTable}
        </div>
    `;
}

function renderInsightCards(allData) {
    // Find most downloaded project
    const withDownloads = allData.filter(d => d.summary.total_downloads > 0);
    if (withDownloads.length === 0) return '';

    const mostDownloaded = withDownloads.reduce((max, d) =>
        d.summary.total_downloads > max.summary.total_downloads ? d : max
    );

    // Fastest cadence (lowest avg_cadence_days, excluding null)
    const withCadence = allData.filter(d => d.summary.avg_cadence_days && d.summary.avg_cadence_days > 0);
    const fastestShipper = withCadence.length > 0
        ? withCadence.reduce((min, d) => d.summary.avg_cadence_days < min.summary.avg_cadence_days ? d : min)
        : null;

    // Newest project (most recent first release)
    const withReleases = allData.filter(d => d.releases.length > 0);
    let newestProject = null;
    if (withReleases.length > 0) {
        newestProject = withReleases.reduce((newest, d) => {
            const firstRelease = d.releases[d.releases.length - 1];
            const newestFirst = newest.releases[newest.releases.length - 1];
            return new Date(firstRelease.published_at) > new Date(newestFirst.published_at) ? d : newest;
        });
    }

    // Most platforms
    const mostPlatforms = withDownloads.reduce((max, d) => {
        const platforms = Object.keys(d.summary.platform_breakdown || {}).filter(k => k !== 'Signatures' && k !== 'Other').length;
        const maxPlatforms = Object.keys(max.summary.platform_breakdown || {}).filter(k => k !== 'Signatures' && k !== 'Other').length;
        return platforms > maxPlatforms ? d : max;
    });

    return `
        <div class="insight-cards">
            <div class="insight-card">
                <div class="insight-card-label">Most Downloaded</div>
                <div class="insight-card-value">${formatNumber(mostDownloaded.summary.total_downloads)}</div>
                <div class="insight-card-detail">${mostDownloaded.project.name} across ${mostDownloaded.summary.total_releases} releases</div>
            </div>
            ${fastestShipper ? `
            <div class="insight-card">
                <div class="insight-card-label">Fastest Shipper</div>
                <div class="insight-card-value">${fastestShipper.summary.avg_cadence_days}d</div>
                <div class="insight-card-detail">${fastestShipper.project.name} avg release cadence</div>
            </div>
            ` : ''}
            ${newestProject ? `
            <div class="insight-card">
                <div class="insight-card-label">Newest Entrant</div>
                <div class="insight-card-value">${newestProject.project.name}</div>
                <div class="insight-card-detail">First release: ${formatDate(newestProject.releases[newestProject.releases.length - 1].published_at)}</div>
            </div>
            ` : ''}
            <div class="insight-card">
                <div class="insight-card-label">Broadest Reach</div>
                <div class="insight-card-value">${mostPlatforms.project.name}</div>
                <div class="insight-card-detail">${Object.keys(mostPlatforms.summary.platform_breakdown || {}).filter(k => k !== 'Signatures').join(', ')}</div>
            </div>
        </div>
    `;
}

function renderDownloadsChart(allData) {
    const withDownloads = allData
        .filter(d => d.summary.total_downloads > 0)
        .sort((a, b) => b.summary.total_downloads - a.summary.total_downloads);

    if (withDownloads.length === 0) return '';

    return `
        <h2 class="section-header">
            <i class="fas fa-chart-bar"></i> Who's Getting Downloaded?
        </h2>
        <div class="comparison-chart-container">
            <canvas id="downloads-comparison-chart"></canvas>
        </div>
    `;
}

function renderReleaseTimeline(allData) {
    const withReleases = allData.filter(d => d.releases.length > 0);
    if (withReleases.length === 0) return '';

    return `
        <h2 class="section-header">
            <i class="fas fa-timeline"></i> Shipping Velocity (Last 90 Days)
        </h2>
        <div class="comparison-chart-container" style="height:300px;">
            <canvas id="release-timeline-chart"></canvas>
        </div>
    `;
}

// ─── Chart Rendering ────────────────────────────────────────────────────────
function initDownloadsChart(allData) {
    const withDownloads = allData
        .filter(d => d.summary.total_downloads > 0)
        .sort((a, b) => b.summary.total_downloads - a.summary.total_downloads);

    if (withDownloads.length === 0) return;

    const ctx = document.getElementById('downloads-comparison-chart');
    if (!ctx) return;

    const labels = withDownloads.map(d => d.project.name);

    // Stack by platform
    const platforms = ['Windows', 'macOS', 'Linux', 'Other'];
    const datasets = platforms.map(platform => ({
        label: platform,
        data: withDownloads.map(d => (d.summary.platform_breakdown || {})[platform] || 0),
        backgroundColor: PLATFORM_COLORS[platform],
        borderRadius: 2,
    }));

    new Chart(ctx, {
        type: 'bar',
        data: { labels, datasets },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        pointStyle: 'rect',
                        padding: 15,
                        font: { family: "'Inter', sans-serif", size: 11 },
                        color: getComputedStyle(document.body).getPropertyValue('--oss-text-secondary').trim() || '#5F6C7E',
                    }
                },
                tooltip: {
                    callbacks: {
                        label: (ctx) => `${ctx.dataset.label}: ${ctx.raw.toLocaleString()}`
                    }
                }
            },
            scales: {
                x: {
                    stacked: true,
                    ticks: {
                        callback: (v) => formatNumber(v),
                        font: { family: "'Inter', sans-serif", size: 11 },
                        color: getComputedStyle(document.body).getPropertyValue('--oss-text-secondary').trim() || '#5F6C7E',
                    },
                    grid: { display: false },
                },
                y: {
                    stacked: true,
                    ticks: {
                        font: { family: "'Inter', sans-serif", size: 12, weight: 600 },
                        color: getComputedStyle(document.body).getPropertyValue('--oss-text').trim() || '#2A3342',
                    },
                    grid: { display: false },
                }
            }
        }
    });
}

function initReleaseTimelineChart(allData) {
    const ctx = document.getElementById('release-timeline-chart');
    if (!ctx) return;

    const now = new Date();
    const ninetyDaysAgo = new Date(now - 90 * 24 * 60 * 60 * 1000);

    const withReleases = allData.filter(d => d.releases.length > 0);
    const projectColors = [
        '#E8916B', '#0078D4', '#FFB000', '#8293AB', '#D4A298',
        '#16a34a', '#dc2626', '#7c3aed', '#0891b2', '#c2410c',
        '#4338ca', '#0f766e', '#a16207',
    ];

    const datasets = withReleases.map((d, idx) => {
        const recentReleases = d.releases
            .filter(r => new Date(r.published_at) >= ninetyDaysAgo)
            .map(r => ({
                x: new Date(r.published_at),
                y: d.project.name,
                r: Math.max(4, Math.min(14, Math.log10(r.total_downloads + 1) * 3)),
                tag: r.tag,
                downloads: r.total_downloads,
            }));

        return {
            label: d.project.name,
            data: recentReleases,
            backgroundColor: projectColors[idx % projectColors.length] + 'AA',
            borderColor: projectColors[idx % projectColors.length],
            borderWidth: 1,
        };
    }).filter(ds => ds.data.length > 0);

    if (datasets.length === 0) return;

    const allLabels = [...new Set(datasets.flatMap(ds => ds.data.map(d => d.y)))];

    new Chart(ctx, {
        type: 'bubble',
        data: { datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false,
                },
                tooltip: {
                    callbacks: {
                        label: (ctx) => {
                            const d = ctx.raw;
                            return `${ctx.dataset.label} ${d.tag}: ${d.downloads.toLocaleString()} downloads`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'week',
                        displayFormats: { week: 'MMM d' },
                    },
                    min: ninetyDaysAgo,
                    max: now,
                    ticks: {
                        font: { family: "'Inter', sans-serif", size: 11 },
                        color: getComputedStyle(document.body).getPropertyValue('--oss-text-secondary').trim() || '#5F6C7E',
                    },
                    grid: { color: 'rgba(128,128,128,0.08)' },
                },
                y: {
                    type: 'category',
                    labels: allLabels,
                    ticks: {
                        font: { family: "'Inter', sans-serif", size: 11, weight: 600 },
                        color: getComputedStyle(document.body).getPropertyValue('--oss-text').trim() || '#2A3342',
                    },
                    grid: { color: 'rgba(128,128,128,0.06)' },
                }
            }
        }
    });
}

// ─── Interaction ────────────────────────────────────────────────────────────
function scrollToCard(fullName) {
    const cardId = 'card-' + fullName.replace('/', '-');
    const card = document.getElementById(cardId);
    if (card) {
        card.scrollIntoView({ behavior: 'smooth', block: 'center' });
        card.style.borderColor = 'var(--oss-accent)';
        card.style.boxShadow = '0 0 0 2px rgba(232, 145, 107, 0.2)';
        setTimeout(() => {
            card.style.borderColor = '';
            card.style.boxShadow = '';
        }, 2000);
    }
}

// Global reference for full release data
const PROJECT_DATA_CACHE = {};

function toggleAllReleases(btn, fullName) {
    const [owner, repo] = fullName.split('/');
    const container = document.getElementById(`all-releases-${owner}-${repo}`);
    if (!container) return;

    if (container.style.display === 'none') {
        const data = PROJECT_DATA_CACHE[fullName];
        if (!data) return;

        const allReleases = data.releases.filter(r => !r.is_draft);
        container.innerHTML = `
            <table class="releases-table">
                <thead>
                    <tr>
                        <th>Version</th>
                        <th>Date</th>
                        <th style="text-align:right">Downloads</th>
                        <th style="text-align:right">Assets</th>
                    </tr>
                </thead>
                <tbody>
                    ${allReleases.map(r => `
                        <tr>
                            <td>
                                <a href="${r.html_url}" target="_blank" class="tag-link">${r.tag}</a>
                                ${r.is_prerelease ? '<span class="prerelease-badge">pre</span>' : ''}
                            </td>
                            <td class="date-cell">${formatDateShort(r.published_at)}</td>
                            <td class="number-cell">${formatNumber(r.total_downloads)}</td>
                            <td class="number-cell">${r.asset_count}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        container.style.display = 'block';
        btn.textContent = 'Show less ▲';
    } else {
        container.style.display = 'none';
        btn.textContent = `Show all releases ▼`;
    }
}

// ─── Main Init ──────────────────────────────────────────────────────────────
async function init() {
    const content = document.getElementById('main-content');
    if (!content) return;

    try {
        const index = await loadIndex();

        // Load all project detail files
        const detailPromises = index.projects
            .filter(p => p.total_releases > 0)
            .map(async p => {
                try {
                    const data = await loadProjectData(p.file);
                    PROJECT_DATA_CACHE[p.full_name] = data;
                    return data;
                } catch {
                    return null;
                }
            });

        const allData = (await Promise.all(detailPromises)).filter(Boolean);

        // Group by category
        const categories = {};
        for (const data of allData) {
            const cat = data.category || 'Other';
            if (!categories[cat]) categories[cat] = [];
            categories[cat].push(data);
        }

        // Sort each category by downloads
        for (const cat of Object.keys(categories)) {
            categories[cat].sort((a, b) => b.summary.total_downloads - a.summary.total_downloads);
        }

        // Category display order
        const categoryOrder = ['Lightning', 'Wallets', 'Core Infrastructure', 'Exchanges', 'Block Open Source', 'Libraries & Tools'];

        let html = '';

        // Insight cards
        html += renderInsightCards(allData);

        // Leaderboard
        html += renderLeaderboard(index);

        // Downloads comparison chart
        html += renderDownloadsChart(allData);

        // Release timeline
        html += renderReleaseTimeline(allData);

        // Project detail cards by category
        html += `<h2 class="section-header"><i class="fas fa-box-open"></i> Ecosystem Deep Dives</h2>`;

        for (const cat of categoryOrder) {
            if (!categories[cat] || categories[cat].length === 0) continue;
            html += `<div class="category-label"><i class="fas fa-tag"></i> ${cat}</div>`;
            html += '<div class="project-cards-grid">';
            for (const data of categories[cat]) {
                html += renderProjectCard(data);
            }
            html += '</div>';
        }

        // Data freshness note
        html += `
            <div class="data-note">
                Data sourced from the <a href="https://docs.github.com/en/rest/releases" target="_blank">GitHub Releases API</a>.
                Last updated: ${formatDate(index.generated_at)}.
                Some projects (e.g., Bitcoin Core, Electrum) distribute binaries outside GitHub Releases and may show 0 downloads here.
            </div>
        `;

        content.innerHTML = html;

        // Initialize charts and sorting after DOM is ready
        setTimeout(() => {
            initDownloadsChart(allData);
            initReleaseTimelineChart(allData);
            setupLeaderboardSorting();

            
            // Initialize sparklines
            for (const data of allData) {
                const canvasId = `sparkline-${data.project.full_name.replace('/', '-')}`;
                const canvas = document.getElementById(canvasId);
                if (canvas && data.releases && data.releases.length > 0) {
                    renderSparkline(canvas, data.releases);
                }
            }
        }, 100);

    } catch (error) {
        content.innerHTML = `
            <div class="error-state">
                <p><strong>Failed to load data.</strong></p>
                <p>${error.message}</p>
                <p style="font-size:0.8rem; margin-top:1rem;">Try running: <code>python3 src/fetch_releases.py</code> to generate data files.</p>
            </div>
        `;
    }
}

document.addEventListener('DOMContentLoaded', init);

function setupLeaderboardSorting() {
    const table = document.getElementById('leaderboard');
    if (!table) return;
    const headers = table.querySelectorAll('th[data-sort]');
    
    headers.forEach(header => {
        header.addEventListener('click', () => {
            const sortKey = header.getAttribute('data-sort');
            const isDesc = !header.classList.contains('sort-asc'); // Toggle direction if already active
            
            headers.forEach(h => {
                h.classList.remove('sort-active', 'sort-asc', 'sort-desc');
                const icon = h.querySelector('.sort-icon');
                if (icon) icon.textContent = '▼';
            });
            
            header.classList.add('sort-active', isDesc ? 'sort-desc' : 'sort-asc');
            header.querySelector('.sort-icon').textContent = isDesc ? '▼' : '▲';

            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            rows.sort((a, b) => {
                let aVal = a.getAttribute(`data-${sortKey}`);
                let bVal = b.getAttribute(`data-${sortKey}`);
                
                if (sortKey === 'category') {
                    return isDesc ? bVal.localeCompare(aVal) : aVal.localeCompare(bVal);
                } else {
                    return isDesc ? Number(bVal) - Number(aVal) : Number(aVal) - Number(bVal);
                }
            });
            
            rows.forEach((row, idx) => {
                row.querySelector('.rank-cell').textContent = idx + 1;
                tbody.appendChild(row);
            });
        });
    });
}

function renderSparkline(canvas, releases) {
    const recentReleases = [...releases].filter(r => !r.is_draft && !r.is_prerelease).slice(0, 10).reverse();
    if (recentReleases.length < 2) return;
    
    const data = recentReleases.map(r => r.total_downloads);
    const labels = recentReleases.map(r => r.tag);

    new Chart(canvas, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                borderColor: '#E8916B',
                borderWidth: 2,
                pointRadius: 0,
                pointHoverRadius: 4,
                tension: 0.4,
                fill: true,
                backgroundColor: 'rgba(232, 145, 107, 0.1)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    enabled: true,
                    backgroundColor: 'rgba(13, 15, 20, 0.9)',
                    titleFont: { family: 'Inter', size: 12 },
                    bodyFont: { family: 'Inter', size: 11 },
                    padding: 8,
                    borderColor: 'rgba(253, 246, 227, 0.1)',
                    borderWidth: 1,
                    callbacks: {
                        label: (ctx) => formatNumber(ctx.raw) + ' DLs'
                    }
                }
            },
            scales: {
                x: { display: false },
                y: { display: false, beginAtZero: true }
            },
            layout: { padding: 0 }
        }
    });
}
