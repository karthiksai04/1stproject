/**
 * CartCompass-BI - Common Shared JavaScript
 * Provides universal currency formatting, API client with automatic
 * GitHub Pages demo fallback, dark theme Chart.js configuration, and sidebar navigation.
 */

// Shared State
const AppState = {
    currency: localStorage.getItem('cartcompass_currency') || 'INR',
    currencySymbol: (localStorage.getItem('cartcompass_currency') === 'USD') ? '$' : '₹',
    usdRate: 0.012, // 1 INR ~ 0.012 USD
    isLiveMode: false,
    activeFilters: {
        period: 'all',
        status_mode: 'delivered'
    }
};

// Embedded Seeded Synthetic Data (Guarantees 100% functionality on GitHub Pages / Static Hosting)
const DEMO_DATA = {
    kpis: {
        gross_sales: 5324865.0,
        discount_amount: 207400.1,
        return_amount: 174972.37,
        net_sales: 4942492.53,
        total_orders: 551,
        total_items_sold: 1483,
        average_order_value: 8970.04,
        growth: {
            revenue_growth_pct: 110.51,
            order_growth_pct: 113.57,
            previous_net_sales: 2347890.0,
            previous_orders: 258
        }
    },
    monthly: [
        { year_month: "2025-01", gross_sales: 437532.0, discount_amount: 19142.44, return_amount: 7749.9, net_sales: 410639.66, total_orders: 41, aov: 10015.6 },
        { year_month: "2025-02", gross_sales: 298955.0, discount_amount: 6907.32, return_amount: 6748.5, net_sales: 285299.18, total_orders: 36, aov: 7924.98 },
        { year_month: "2025-03", gross_sales: 288036.0, discount_amount: 15540.02, return_amount: 19948.95, net_sales: 252547.03, total_orders: 46, aov: 5490.15 },
        { year_month: "2025-04", gross_sales: 469523.0, discount_amount: 8319.83, return_amount: 2387.61, net_sales: 458815.56, total_orders: 28, aov: 16386.27 },
        { year_month: "2025-05", gross_sales: 292866.0, discount_amount: 13425.89, return_amount: 20203.99, net_sales: 259236.12, total_orders: 38, aov: 6822.0 },
        { year_month: "2025-06", gross_sales: 282026.0, discount_amount: 15546.5, return_amount: 1924.3, net_sales: 264555.2, total_orders: 29, aov: 9122.59 },
        { year_month: "2025-07", gross_sales: 450297.0, discount_amount: 25434.81, return_amount: 8064.93, net_sales: 416797.26, total_orders: 40, aov: 10419.93 },
        { year_month: "2025-08", gross_sales: 416676.0, discount_amount: 13131.85, return_amount: 4329.61, net_sales: 399214.54, total_orders: 31, aov: 12877.89 },
        { year_month: "2025-09", gross_sales: 547020.0, discount_amount: 24434.55, return_amount: 9932.15, net_sales: 512653.3, total_orders: 45, aov: 11392.3 },
        { year_month: "2025-10", gross_sales: 424178.0, discount_amount: 15968.49, return_amount: 33560.82, net_sales: 374648.69, total_orders: 44, aov: 8514.74 },
        { year_month: "2025-11", gross_sales: 378521.0, discount_amount: 17425.1, return_amount: 3858.6, net_sales: 357237.3, total_orders: 49, aov: 7290.56 },
        { year_month: "2025-12", gross_sales: 512757.0, discount_amount: 11655.41, return_amount: 8641.65, net_sales: 492459.94, total_orders: 54, aov: 9119.63 },
        { year_month: "2026-01", gross_sales: 260061.0, discount_amount: 14999.96, return_amount: 44041.63, net_sales: 201019.41, total_orders: 36, aov: 5583.87 },
        { year_month: "2026-02", gross_sales: 266417.0, discount_amount: 5467.93, return_amount: 3579.73, net_sales: 257369.34, total_orders: 34, aov: 7569.69 }
    ],
    categories: [
        { category: "Electronics", gross_sales: 2198807.0, discount_amount: 86468.33, return_amount: 31484.15, net_sales: 2080854.52, total_items: 293, distinct_orders: 169, revenue_share_pct: 42.10, growth_pct: 19.6 },
        { category: "Home & Kitchen", gross_sales: 1542388.0, discount_amount: 59384.20, return_amount: 68340.50, net_sales: 1414663.30, total_items: 412, distinct_orders: 178, revenue_share_pct: 28.62, growth_pct: 21.1 },
        { category: "Fashion & Apparel", gross_sales: 798440.0, discount_amount: 32410.15, return_amount: 42390.10, net_sales: 723639.75, total_items: 395, distinct_orders: 182, revenue_share_pct: 14.64, growth_pct: 5.6 },
        { category: "Sports & Fitness", gross_sales: 472110.0, discount_amount: 18450.00, return_amount: 19800.00, net_sales: 433860.00, total_items: 218, distinct_orders: 114, revenue_share_pct: 8.78, growth_pct: -3.5 },
        { category: "Beauty & Personal Care", gross_sales: 313120.0, discount_amount: 10687.42, return_amount: 12957.62, net_sales: 289474.96, total_items: 165, distinct_orders: 98, revenue_share_pct: 5.86, growth_pct: 11.4 }
    ],
    regions: [
        { region: "North", gross_sales: 1160992.0, discount_amount: 38865.40, return_amount: 26756.72, net_sales: 1095369.88, total_orders: 120, total_items: 319, average_order_value: 9128.08, revenue_share_pct: 22.16, target_pct: 94 },
        { region: "South", gross_sales: 1124500.0, discount_amount: 44210.10, return_amount: 38120.00, net_sales: 1042169.90, total_orders: 115, total_items: 308, average_order_value: 9062.34, revenue_share_pct: 21.08, target_pct: 91 },
        { region: "West", gross_sales: 1092300.0, discount_amount: 41320.00, return_amount: 36400.00, net_sales: 1014580.00, total_orders: 112, total_items: 295, average_order_value: 9058.75, revenue_share_pct: 20.53, target_pct: 88 },
        { region: "Central", gross_sales: 994200.0, discount_amount: 42100.00, return_amount: 37200.00, net_sales: 914900.00, total_orders: 106, total_items: 286, average_order_value: 8631.13, revenue_share_pct: 18.51, target_pct: 85 },
        { region: "East", gross_sales: 952873.0, discount_amount: 40904.60, return_amount: 36495.65, net_sales: 875472.75, total_orders: 98, total_items: 275, average_order_value: 8933.39, revenue_share_pct: 17.72, target_pct: 82 }
    ],
    status_distribution: [
        { status: "delivered", order_count: 551, percentage: 73.47 },
        { status: "shipped", order_count: 80, percentage: 10.67 },
        { status: "cancelled", order_count: 61, percentage: 8.13 },
        { status: "pending", order_count: 58, percentage: 7.73 }
    ]
};

// Global Chart.js Dark Theme Configuration
if (typeof Chart !== 'undefined') {
    Chart.defaults.color = '#94A3B8';
    Chart.defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, sans-serif";
    Chart.defaults.font.size = 11;
    Chart.defaults.plugins.tooltip.backgroundColor = '#0D1322';
    Chart.defaults.plugins.tooltip.titleColor = '#FFFFFF';
    Chart.defaults.plugins.tooltip.bodyColor = '#E2E8F0';
    Chart.defaults.plugins.tooltip.borderColor = '#1D2844';
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.cornerRadius = 6;
}

// Formatting Utilities
function formatCurrency(val) {
    if (val === null || val === undefined || isNaN(val)) return '--';
    let num = Number(val);
    if (AppState.currency === 'USD') {
        num = num * AppState.usdRate;
        return '$' + num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
    return '₹' + num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatCompactCurrency(val) {
    if (val === null || val === undefined || isNaN(val)) return '--';
    let num = Number(val);
    if (AppState.currency === 'USD') {
        num = num * AppState.usdRate;
        if (num >= 1000000) return `$${(num / 1000000).toFixed(1)}M`;
        if (num >= 1000) return `$${(num / 1000).toFixed(1)}K`;
        return `$${num.toFixed(0)}`;
    }
    // Indian formatting (Lakhs & Crores)
    if (num >= 10000000) return `₹${(num / 10000000).toFixed(2)} Cr`;
    if (num >= 100000) return `₹${(num / 100000).toFixed(1)} Lakh`;
    if (num >= 1000) return `₹${(num / 1000).toFixed(0)}k`;
    return `₹${num.toFixed(0)}`;
}

function formatNumber(val) {
    if (val === null || val === undefined || isNaN(val)) return '--';
    return Number(val).toLocaleString();
}

function formatPercent(val) {
    if (val === null || val === undefined || val === '' || isNaN(Number(val))) return 'N/A';
    const num = Number(val);
    const sign = num > 0 ? '+' : '';
    return `${sign}${num.toFixed(1)}%`;
}

// Check Backend Connectivity & Toggle Demo/Live Status
async function initBackendHealth() {
    try {
        const res = await fetch('/api/health');
        if (res.ok) {
            AppState.isLiveMode = true;
            return true;
        }
    } catch (e) {
        // Fallback to static demo data (GitHub Pages mode)
    }
    AppState.isLiveMode = false;
    return false;
}

// Universal Data Fetcher
async function getKpisData(params = {}) {
    if (AppState.isLiveMode) {
        try {
            const qs = new URLSearchParams(params).toString();
            const res = await fetch(`/api/kpis?${qs}`);
            if (res.ok) {
                const json = await res.json();
                return json.data;
            }
        } catch (e) {
            console.warn('API fetch failed, falling back to demo dataset:', e);
        }
    }
    return DEMO_DATA.kpis;
}

async function getMonthlyData(params = {}) {
    if (AppState.isLiveMode) {
        try {
            const qs = new URLSearchParams(params).toString();
            const res = await fetch(`/api/revenue/monthly?${qs}`);
            if (res.ok) {
                const json = await res.json();
                return json.data;
            }
        } catch (e) {
            console.warn('API monthly fetch failed, falling back to demo data');
        }
    }
    return DEMO_DATA.monthly;
}

async function getCategoriesData(params = {}) {
    if (AppState.isLiveMode) {
        try {
            const qs = new URLSearchParams(params).toString();
            const res = await fetch(`/api/categories?${qs}`);
            if (res.ok) {
                const json = await res.json();
                return json.data;
            }
        } catch (e) {
            console.warn('API categories fetch failed, falling back to demo data');
        }
    }
    return DEMO_DATA.categories;
}

async function getRegionsData(params = {}) {
    if (AppState.isLiveMode) {
        try {
            const qs = new URLSearchParams(params).toString();
            const res = await fetch(`/api/regions?${qs}`);
            if (res.ok) {
                const json = await res.json();
                return json.data;
            }
        } catch (e) {
            console.warn('API regions fetch failed, falling back to demo data');
        }
    }
    return DEMO_DATA.regions;
}

async function getStatusDistributionData(params = {}) {
    if (AppState.isLiveMode) {
        try {
            const qs = new URLSearchParams(params).toString();
            const res = await fetch(`/api/status-distribution?${qs}`);
            if (res.ok) {
                const json = await res.json();
                return json.data;
            }
        } catch (e) {
            console.warn('API status fetch failed, falling back to demo data');
        }
    }
    return { distribution: DEMO_DATA.status_distribution, total_orders: 750 };
}

async function refreshSidebarMetrics() {
    const orderCount = document.getElementById('sidebar-order-count');
    if (!orderCount) return;

    try {
        const response = await fetch('/api/dashboard-summary', { cache: 'no-store' });
        const result = await response.json();
        if (!response.ok || result.status !== 'success') {
            throw new Error(result.message || 'Unable to load current dataset counts.');
        }

        const summary = result.data;
        const totalOrders = Number(summary.total_orders);
        const deliveredOrders = Number(summary.delivered_orders);
        const totalItems = Number(summary.total_items);
        const deliveryRate = totalOrders > 0
            ? Math.min(100, (deliveredOrders / totalOrders) * 100)
            : 0;

        orderCount.textContent = `${formatNumber(totalOrders)} Orders`;
        document.getElementById('sidebar-item-count').textContent =
            `Items: ${formatNumber(totalItems)}`;
        document.getElementById('sidebar-delivery-progress').style.width =
            `${deliveryRate.toFixed(1)}%`;
        document.getElementById('sidebar-dataset-status').textContent =
            totalOrders === 0
                ? 'No Orders'
                : deliveredOrders === totalOrders
                    ? 'On Track'
                    : 'In Progress';
    } catch (error) {
        console.error('Failed to refresh sidebar dataset counts:', error);
        orderCount.textContent = 'Unavailable';
        document.getElementById('sidebar-item-count').textContent = 'Items: --';
        document.getElementById('sidebar-dataset-status').textContent = 'Unavailable';
    }
}

// Setup Shared Page Controls (Currency toggle, Mobile nav, Export PDF)
function setupSharedControls(onCurrencyChangeCallback) {
    refreshSidebarMetrics();

    // Currency Switcher
    const inrBtn = document.getElementById('curr-inr');
    const usdBtn = document.getElementById('curr-usd');

    function syncCurrencyUI() {
        if (inrBtn && usdBtn) {
            inrBtn.classList.toggle('active', AppState.currency === 'INR');
            usdBtn.classList.toggle('active', AppState.currency === 'USD');
        }
    }

    syncCurrencyUI();

    if (inrBtn) {
        inrBtn.addEventListener('click', () => {
            AppState.currency = 'INR';
            AppState.currencySymbol = '₹';
            localStorage.setItem('cartcompass_currency', 'INR');
            syncCurrencyUI();
            if (onCurrencyChangeCallback) onCurrencyChangeCallback();
        });
    }

    if (usdBtn) {
        usdBtn.addEventListener('click', () => {
            AppState.currency = 'USD';
            AppState.currencySymbol = '$';
            localStorage.setItem('cartcompass_currency', 'USD');
            syncCurrencyUI();
            if (onCurrencyChangeCallback) onCurrencyChangeCallback();
        });
    }

    // Mobile Sidebar Toggle
    const mobileToggle = document.getElementById('mobile-sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    if (mobileToggle && sidebar) {
        mobileToggle.addEventListener('click', () => {
            sidebar.classList.toggle('mobile-open');
        });
    }

    // Print / Export PDF button
    const printBtn = document.getElementById('btn-print-report');
    if (printBtn) {
        printBtn.addEventListener('click', () => {
            window.print();
        });
    }
}
