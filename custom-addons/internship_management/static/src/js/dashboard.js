/**
 * Step 3: Dashboard JavaScript Implementation
 * ==========================================
 * File: static/src/js/dashboard.js
 */

odoo.define('internship_management.dashboard', function (require) {
    "use strict";

    const AbstractAction = require('web.AbstractAction');
    const core = require('web.core');
    const rpc = require('web.rpc');
    const QWeb = core.qweb;
    const _t = core._t;

    /**
     * Main Dashboard Widget
     */
    const InternshipDashboard = AbstractAction.extend({
        template: 'internship_dashboard_template',

        events: {
            'click #refreshDashboard': '_onRefreshClicked',
            'click #exportDashboard': '_onExportClicked',
            'change #trendsTimeRange': '_onTimeRangeChanged',
        },

        /**
         * Initialize the dashboard
         */
        init: function (parent, context) {
            this._super(parent, context);
            this.charts = {};
            this.dashboardData = {};
            this.isLoading = false;
        },

        /**
         * Load initial data before rendering
         */
        willStart: function () {
            return this._super().then(() => {
                return this._loadDashboardData();
            });
        },

        /**
         * Start the dashboard after DOM is ready
         */
        start: function () {
            return this._super().then(() => {
                this._setupEventHandlers();
                this._renderDashboard();
                this._startAutoRefresh();
                this._setupResponsiveness();
            });
        },

        // ===============================
        // DATA LOADING METHODS
        // ===============================

        /**
         * Load dashboard data from server
         */
        _loadDashboardData: function () {
            return rpc.query({
                model: 'internship.analytics',
                method: 'get_dashboard_data',
                args: [],
            }).then((data) => {
                this.dashboardData = data;
                console.log('Dashboard data loaded:', data);
                return data;
            }).catch((error) => {
                console.error('Error loading dashboard data:', error);
                this._showNotification('Error loading dashboard data', 'danger');
                return {};
            });
        },

        // ===============================
        // RENDERING METHODS
        // ===============================

        /**
         * Render complete dashboard
         */
        _renderDashboard: function () {
            if (this.dashboardData.error) {
                this._showError(this.dashboardData.message);
                return;
            }

            this._renderKPICards();
            this._renderCharts();
            this._renderActivities();
            this._renderAlerts();
            this._updateLastUpdated();
        },

        /**
         * Render KPI cards with animation
         */
        _renderKPICards: function () {
            const kpiData = this.dashboardData.kpi_cards || {};

            Object.keys(kpiData).forEach(key => {
                const card = kpiData[key];
                this._animateCounter(`#${key}`, card.value);
                this.$(`#${key.replace(/([A-Z])/g, '$1').toLowerCase()}Trend`).text(card.trend);
            });
        },

        /**
         * Render all charts
         */
        _renderCharts: function () {
            if (!this.dashboardData.charts) return;

            this._renderStatusChart();
            this._renderTrendsChart();
            this._renderGradeChart();
            this._renderWorkloadChart();
            this._renderPerformanceChart();
        },

        /**
         * Render status distribution pie chart
         */
        _renderStatusChart: function () {
            const ctx = this.$('#statusChart')[0];
            if (!ctx) return;

            const data = this.dashboardData.charts.status_distribution || [];

            // Destroy existing chart if exists
            if (this.charts.statusChart) {
                this.charts.statusChart.destroy();
            }

            this.charts.statusChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: data.map(item => item.label),
                    datasets: [{
                        data: data.map(item => item.value),
                        backgroundColor: data.map(item => item.color),
                        borderWidth: 2,
                        borderColor: '#fff',
                        hoverBorderWidth: 3,
                        hoverBackgroundColor: data.map(item => this._lightenColor(item.color, 20))
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                usePointStyle: true,
                                padding: 20,
                                font: {
                                    size: 12
                                }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.parsed || 0;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return `${label}: ${value} (${percentage}%)`;
                                }
                            }
                        }
                    },
                    animation: {
                        animateRotate: true,
                        duration: 1000
                    }
                }
            });
        },

        /**
         * Render monthly trends line chart
         */
        _renderTrendsChart: function () {
            const ctx = this.$('#trendsChart')[0];
            if (!ctx) return;

            const data = this.dashboardData.charts.monthly_trends || [];

            if (this.charts.trendsChart) {
                this.charts.trendsChart.destroy();
            }

            this.charts.trendsChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.map(item => item.month),
                    datasets: [
                        {
                            label: 'Created',
                            data: data.map(item => item.created),
                            borderColor: '#007bff',
                            backgroundColor: 'rgba(0, 123, 255, 0.1)',
                            borderWidth: 3,
                            fill: true,
                            tension: 0.4,
                            pointBackgroundColor: '#007bff',
                            pointBorderColor: '#fff',
                            pointBorderWidth: 2,
                            pointRadius: 6,
                            pointHoverRadius: 8
                        },
                        {
                            label: 'Completed',
                            data: data.map(item => item.completed),
                            borderColor: '#28a745',
                            backgroundColor: 'rgba(40, 167, 69, 0.1)',
                            borderWidth: 3,
                            fill: true,
                            tension: 0.4,
                            pointBackgroundColor: '#28a745',
                            pointBorderColor: '#fff',
                            pointBorderWidth: 2,
                            pointRadius: 6,
                            pointHoverRadius: 8
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: {
                                usePointStyle: true,
                                padding: 20
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(0,0,0,0.1)'
                            },
                            ticks: {
                                precision: 0
                            }
                        },
                        x: {
                            grid: {
                                display: false
                            }
                        }
                    },
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    },
                    animation: {
                        duration: 1000,
                        easing: 'easeInOutQuart'
                    }
                }
            });
        },

        /**
         * Render grade distribution bar chart
         */
        _renderGradeChart: function () {
            const ctx = this.$('#gradeChart')[0];
            if (!ctx) return;

            const data = this.dashboardData.charts.grade_distribution || [];

            if (this.charts.gradeChart) {
                this.charts.gradeChart.destroy();
            }

            this.charts.gradeChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.map(item => item.label),
                    datasets: [{
                        label: 'Students',
                        data: data.map(item => item.value),
                        backgroundColor: data.map(item => item.color),
                        borderColor: data.map(item => this._darkenColor(item.color, 20)),
                        borderWidth: 1,
                        borderRadius: 4,
                        borderSkipped: false
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const value = context.parsed.y;
                                    const dataIndex = context.dataIndex;
                                    const percentage = data[dataIndex]?.percentage || 0;
                                    return `Students: ${value} (${percentage}%)`;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                precision: 0
                            }
                        },
                        x: {
                            grid: {
                                display: false
                            }
                        }
                    },
                    animation: {
                        duration: 800,
                        easing: 'easeOutBounce'
                    }
                }
            });
        },

        /**
         * Render supervisor workload horizontal bar chart
         */
        _renderWorkloadChart: function () {
            const ctx = this.$('#workloadChart')[0];
            if (!ctx) return;

            const data = this.dashboardData.charts.supervisor_workload || [];

            if (this.charts.workloadChart) {
                this.charts.workloadChart.destroy();
            }

            // Take only top 5 supervisors for better visualization
            const topData = data.slice(0, 5);

            this.charts.workloadChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: topData.map(item => item.name),
                    datasets: [{
                        label: 'Utilization %',
                        data: topData.map(item => item.utilization),
                        backgroundColor: topData.map(item => item.color),
                        borderColor: topData.map(item => this._darkenColor(item.color, 20)),
                        borderWidth: 1,
                        borderRadius: 4
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const dataIndex = context.dataIndex;
                                    const supervisor = topData[dataIndex];
                                    return `${supervisor.active_count}/${supervisor.max_capacity} students (${supervisor.utilization}%)`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            beginAtZero: true,
                            max: 120,
                            ticks: {
                                callback: function(value) {
                                    return value + '%';
                                }
                            }
                        },
                        y: {
                            grid: {
                                display: false
                            }
                        }
                    },
                    animation: {
                        duration: 1000,
                        easing: 'easeInOutElastic'
                    }
                }
            });
        },

        /**
         * Render area performance radar chart
         */
        _renderPerformanceChart: function () {
            const ctx = this.$('#performanceChart')[0];
            if (!ctx) return;

            const data = this.dashboardData.charts.area_performance || [];

            if (this.charts.performanceChart) {
                this.charts.performanceChart.destroy();
            }

            // Take top 5 areas for better visualization
            const topAreas = data.slice(0, 5);

            this.charts.performanceChart = new Chart(ctx, {
                type: 'radar',
                data: {
                    labels: topAreas.map(item => item.name),
                    datasets: [{
                        label: 'Average Grade',
                        data: topAreas.map(item => item.avg_grade),
                        borderColor: '#dc3545',
                        backgroundColor: 'rgba(220, 53, 69, 0.2)',
                        borderWidth: 2,
                        pointBackgroundColor: '#dc3545',
                        pointBorderColor: '#fff',
                        pointRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        r: {
                            beginAtZero: true,
                            max: 20,
                            ticks: {
                                stepSize: 5
                            }
                        }
                    },
                    animation: {
                        duration: 1200,
                        easing: 'easeInOutSine'
                    }
                }
            });
        },

        /**
         * Render recent activities list
         */
        _renderActivities: function () {
            const activities = this.dashboardData.recent_activities || [];
            const $list = this.$('#activitiesList');

            if (activities.length === 0) {
                $list.html('<div class="text-center text-muted py-4">No recent activities</div>');
                return;
            }

            const activitiesHtml = activities.map(activity => `
                <div class="activity-item">
                    <div class="activity-icon">
                        <i class="fa fa-circle text-${this._getStateColor(activity.state)}"></i>
                    </div>
                    <div class="activity-content">
                        <div class="activity-title">${activity.title}</div>
                        <div class="activity-details">
                            <span class="activity-student">${activity.student}</span>
                            <span class="activity-action">${activity.action}</span>
                        </div>
                        <small class="activity-date text-muted">${activity.date}</small>
                    </div>
                </div>
            `).join('');

            $list.html(activitiesHtml);
        },

        /**
         * Render system alerts
         */
        _renderAlerts: function () {
            const alerts = this.dashboardData.alerts || [];
            const $list = this.$('#alertsList');

            if (alerts.length === 0) {
                $list.html('<div class="text-center text-muted py-4">No alerts</div>');
                return;
            }

            const alertsHtml = alerts.map(alert => `
                <div class="alert alert-${alert.type} alert-dismissible fade show" role="alert">
                    <i class="${alert.icon} me-2"></i>
                    <strong>${alert.title}</strong><br/>
                    <small>${alert.message}</small>
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `).join('');

            $list.html(alertsHtml);
        },

        // ===============================
        // EVENT HANDLERS
        // ===============================

        /**
         * Setup additional event handlers
         */
        _setupEventHandlers: function () {
            // Mobile refresh button
            this.$('#mobileRefresh').on('click', this._onRefreshClicked.bind(this));

            // Keyboard shortcuts
            $(document).on('keydown', this._onKeyDown.bind(this));
        },

        /**
         * Handle refresh button click
         */
        _onRefreshClicked: function (ev) {
            ev.preventDefault();
            this._refreshDashboard();
        },

        /**
         * Handle export button click
         */
        _onExportClicked: function (ev) {
            ev.preventDefault();
            this._exportDashboard();
        },

        /**
         * Handle time range change
         */
        _onTimeRangeChanged: function (ev) {
            const range = $(ev.target).val();
            console.log('Time range changed to:', range);
            // Reload trends chart with new range
            this._renderTrendsChart();
        },

        /**
         * Handle keyboard shortcuts
         */
        _onKeyDown: function (ev) {
            if (ev.ctrlKey && ev.key === 'r') {
                ev.preventDefault();
                this._refreshDashboard();
            }
        },

        // ===============================
        // UTILITY METHODS
        // ===============================

        /**
         * Refresh dashboard data
         */
        _refreshDashboard: function () {
            if (this.isLoading) return;

            this.isLoading = true;
            const $refreshBtn = this.$('#refreshDashboard, #mobileRefresh');
            $refreshBtn.find('i').addClass('fa-spin');

            this._loadDashboardData().then(() => {
                this._renderDashboard();
                this._showNotification('Dashboard refreshed successfully', 'success');
            }).catch((error) => {
                this._showNotification('Error refreshing dashboard', 'danger');
                console.error('Refresh error:', error);
            }).finally(() => {
                this.isLoading = false;
                $refreshBtn.find('i').removeClass('fa-spin');
            });
        },

        /**
         * Export dashboard (placeholder)
         */
        _exportDashboard: function () {
            this._showNotification('Export feature coming soon', 'info');
        },

        /**
         * Animate counter with easing
         */
        _animateCounter: function (selector, targetValue) {
            const $element = this.$(selector);
            const currentValue = parseInt($element.text()) || 0;

            if (typeof targetValue === 'string') {
                $element.text(targetValue);
                return;
            }

            const increment = (targetValue - currentValue) / 30;
            let current = currentValue;

            const animation = setInterval(() => {
                current += increment;
                if ((increment > 0 && current >= targetValue) ||
                    (increment < 0 && current <= targetValue)) {
                    current = targetValue;
                    clearInterval(animation);
                }
                $element.text(Math.round(current));
            }, 50);
        },

        /**
         * Update last updated timestamp
         */
        _updateLastUpdated: function () {
            const timestamp = this.dashboardData.last_updated || new Date().toISOString();
            this.$('#lastUpdated').text(new Date(timestamp).toLocaleString());
        },

        /**
         * Setup responsive behavior
         */
        _setupResponsiveness: function () {
            // Handle window resize
            $(window).on('resize', this._debounce(() => {
                Object.values(this.charts).forEach(chart => {
                    if (chart && chart.resize) {
                        chart.resize();
                    }
                });
            }, 250));
        },

        /**
         * Start auto-refresh timer
         */
        _startAutoRefresh: function () {
            // Auto-refresh every 5 minutes
            setInterval(() => {
                if (!this.isLoading) {
                    this._loadDashboardData().then(() => {
                        this._renderKPICards();
                        this._renderActivities();
                        this._renderAlerts();
                        this._updateLastUpdated();
                    });
                }
            }, 300000); // 5 minutes
        },

        /**
         * Show notification
         */
        _showNotification: function (message, type) {
            this.displayNotification({
                title: _t('Dashboard'),
                message: message,
                type: type || 'info',
                sticky: false,
            });
        },

        /**
         * Show error message
         */
        _showError: function (message) {
            this.$el.html(`
                <div class="alert alert-danger text-center" role="alert">
                    <i class="fa fa-exclamation-triangle fa-2x mb-3"></i>
                    <h4>Dashboard Error</h4>
                    <p>${message}</p>
                    <button class="btn btn-primary" onclick="window.location.reload()">
                        <i class="fa fa-refresh"></i> Reload Page
                    </button>
                </div>
            `);
        },

        /**
         * Get color for state
         */
        _getStateColor: function (state) {
            const colors = {
                'draft': 'secondary',
                'submitted': 'primary',
                'approved': 'success',
                'in_progress': 'warning',
                'completed': 'info',
                'evaluated': 'success',
                'cancelled': 'danger'
            };
            return colors[state] || 'secondary';
        },

        /**
         * Lighten color utility
         */
        _lightenColor: function (color, percent) {
            const num = parseInt(color.replace("#", ""), 16);
            const amt = Math.round(2.55 * percent);
            const R = (num >> 16) + amt;
            const B = (num >> 8 & 0x00FF) + amt;
            const G = (num & 0x0000FF) + amt;
            return "#" + (0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 +
                         (B < 255 ? B < 1 ? 0 : B : 255) * 0x100 +
                         (G < 255 ? G < 1 ? 0 : G : 255)).toString(16).slice(1);
        },

        /**
         * Darken color utility
         */
        _darkenColor: function (color, percent) {
            const num = parseInt(color.replace("#", ""), 16);
            const amt = Math.round(2.55 * percent);
            const R = (num >> 16) - amt;
            const B = (num >> 8 & 0x00FF) - amt;
            const G = (num & 0x0000FF) - amt;
            return "#" + (0x1000000 + (R > 255 ? 255 : R < 0 ? 0 : R) * 0x10000 +
                         (B > 255 ? 255 : B < 0 ? 0 : B) * 0x100 +
                         (G > 255 ? 255 : G < 0 ? 0 : G)).toString(16).slice(1);
        },

        /**
         * Debounce utility
         */
        _debounce: function (func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        /**
         * Cleanup when destroying widget
         */
        destroy: function () {
            // Cleanup charts
            Object.values(this.charts).forEach(chart => {
                if (chart && typeof chart.destroy === 'function') {
                    chart.destroy();
                }
            });

            // Remove event listeners
            $(window).off('resize');
            $(document).off('keydown');

            this._super();
        }
    });

    // Register the dashboard action
    core.action_registry.add('internship_dashboard', InternshipDashboard);

    return InternshipDashboard;
});