/**
 * Role-Based Dashboard JavaScript Implementation
 * ============================================
 * File: static/src/js/role_dashboard.js
 * 
 * This file handles role-specific dashboard functionality
 * following Odoo 17 best practices.
 */

odoo.define('internship_management.role_dashboard', [
    'web.AbstractAction',
    'web.core',
    'web.rpc'
], function (AbstractAction, core, rpc) {
    "use strict";

    const QWeb = core.qweb;
    const _t = core._t;

    /**
     * Base Role Dashboard Widget
     */
    const RoleDashboard = AbstractAction.extend({
        template: 'internship_dashboard_template', // Default template
        charts: {},
        dashboardData: {},
        isLoading: false,
        userRole: 'default',

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
                // Check Chart.js availability
                if (typeof Chart === 'undefined') {
                    console.warn('Chart.js is not available. Charts will not be rendered.');
                    this._showNotification('Chart.js is not loaded. Please refresh the page.', 'warning');
                }
                
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
                this.userRole = data.role || 'default';
                console.log(`Dashboard data loaded for role: ${this.userRole}`, data);
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
         * Render complete dashboard based on role
         */
        _renderDashboard: function () {
            if (this.dashboardData.error) {
                this._showError(this.dashboardData.message);
                return;
            }

            // Set the appropriate template based on role
            this._setRoleTemplate();
            
            // Render role-specific content
            this._renderRoleSpecificContent();
            
            // Render common elements
            this._renderKPICards();
            this._renderCharts();
            this._renderActivities();
            this._renderAlerts();
            this._updateLastUpdated();
        },

        /**
         * Set the appropriate template based on user role
         */
        _setRoleTemplate: function () {
            const templateMap = {
                'student': 'internship_student_dashboard_template',
                'supervisor': 'internship_supervisor_dashboard_template',
                'company': 'internship_company_dashboard_template',
                'admin': 'internship_admin_dashboard_template',
                'default': 'internship_dashboard_template'
            };

            const templateName = templateMap[this.userRole] || 'internship_dashboard_template';
            
            // Update template if different from current
            if (this.template !== templateName) {
                this.template = templateName;
                this.$el.html(QWeb.render(templateName, {}));
            }
        },

        /**
         * Render role-specific content
         */
        _renderRoleSpecificContent: function () {
            switch (this.userRole) {
                case 'student':
                    this._renderStudentContent();
                    break;
                case 'supervisor':
                    this._renderSupervisorContent();
                    break;
                case 'company':
                    this._renderCompanyContent();
                    break;
                case 'admin':
                    this._renderAdminContent();
                    break;
                default:
                    this._renderDefaultContent();
            }
        },

        /**
         * Render student-specific content
         */
        _renderStudentContent: function () {
            // Update student info
            if (this.dashboardData.user_info) {
                const info = this.dashboardData.user_info;
                this.$('#studentInfo').text(`Welcome back, ${info.name}!`);
            }

            // Render deadlines
            this._renderDeadlines();
        },

        /**
         * Render supervisor-specific content
         */
        _renderSupervisorContent: function () {
            // Update supervisor info
            if (this.dashboardData.user_info) {
                const info = this.dashboardData.user_info;
                this.$('#supervisorInfo').text(`${info.name} - ${info.department}`);
            }

            // Render workload analysis
            this._renderWorkloadAnalysis();
        },

        /**
         * Render company-specific content
         */
        _renderCompanyContent: function () {
            // Update company info
            if (this.dashboardData.user_info) {
                const info = this.dashboardData.user_info;
                this.$('#companyInfo').text(`${info.name} - ${info.industry}`);
            }

            // Render opportunities
            this._renderOpportunities();
        },

        /**
         * Render admin-specific content
         */
        _renderAdminContent: function () {
            // Update admin info
            if (this.dashboardData.user_info) {
                const info = this.dashboardData.user_info;
                this.$('.dashboard-title').text(`Admin Dashboard - ${info.name}`);
            }

            // Render system health
            this._renderSystemHealth();
        },

        /**
         * Render default content
         */
        _renderDefaultContent: function () {
            // Standard dashboard content
        },

        /**
         * Render KPI cards with role-specific data
         */
        _renderKPICards: function () {
            const kpiData = this.dashboardData.kpi_cards || {};

            Object.keys(kpiData).forEach(key => {
                const card = kpiData[key];
                this._animateCounter(`#${key}`, card.value);
            });
        },

        /**
         * Render charts based on role
         */
        _renderCharts: function () {
            if (!this.dashboardData.charts) return;

            switch (this.userRole) {
                case 'student':
                    this._renderStudentCharts();
                    break;
                case 'supervisor':
                    this._renderSupervisorCharts();
                    break;
                case 'company':
                    this._renderCompanyCharts();
                    break;
                case 'admin':
                    this._renderAdminCharts();
                    break;
                default:
                    this._renderDefaultCharts();
            }
        },

        /**
         * Render student-specific charts
         */
        _renderStudentCharts: function () {
            const charts = this.dashboardData.charts || {};
            
            if (charts.progress_timeline) {
                this._renderProgressChart(charts.progress_timeline);
            }
            
            if (charts.grade_evolution) {
                this._renderGradeEvolutionChart(charts.grade_evolution);
            }
        },

        /**
         * Render supervisor-specific charts
         */
        _renderSupervisorCharts: function () {
            const charts = this.dashboardData.charts || {};
            
            if (charts.student_progress) {
                this._renderStudentProgressChart(charts.student_progress);
            }
            
            if (charts.grade_distribution) {
                this._renderGradeDistributionChart(charts.grade_distribution);
            }
        },

        /**
         * Render company-specific charts
         */
        _renderCompanyCharts: function () {
            const charts = this.dashboardData.charts || {};
            
            if (charts.internship_distribution) {
                this._renderInternshipDistributionChart(charts.internship_distribution);
            }
            
            if (charts.timeline_analysis) {
                this._renderTimelineChart(charts.timeline_analysis);
            }
        },

        /**
         * Render admin-specific charts
         */
        _renderAdminCharts: function () {
            const charts = this.dashboardData.charts || {};
            
            if (charts.status_distribution) {
                this._renderStatusChart(charts.status_distribution);
            }
            
            if (charts.monthly_trends) {
                this._renderTrendsChart(charts.monthly_trends);
            }
            
            if (charts.grade_distribution) {
                this._renderGradeChart(charts.grade_distribution);
            }
            
            if (charts.supervisor_workload) {
                this._renderWorkloadChart(charts.supervisor_workload);
            }
            
            if (charts.area_performance) {
                this._renderPerformanceChart(charts.area_performance);
            }
        },

        /**
         * Render default charts
         */
        _renderDefaultCharts: function () {
            this._renderAdminCharts(); // Use admin charts as default
        },

        /**
         * Render recent activities
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
                            ${activity.student ? `<span class="activity-student">${activity.student}</span>` : ''}
                            ${activity.supervisor ? `<span class="activity-supervisor">${activity.supervisor}</span>` : ''}
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
        // ROLE-SPECIFIC RENDERING METHODS
        // ===============================

        /**
         * Render deadlines for student
         */
        _renderDeadlines: function () {
            const deadlines = this.dashboardData.upcoming_deadlines || [];
            const $list = this.$('#deadlinesList');

            if (deadlines.length === 0) {
                $list.html('<div class="text-center text-muted py-4">No upcoming deadlines</div>');
                return;
            }

            const deadlinesHtml = deadlines.map(deadline => `
                <div class="deadline-item">
                    <div class="deadline-title">${deadline.title}</div>
                    <div class="deadline-stage">${deadline.stage}</div>
                    <div class="deadline-date text-muted">${deadline.deadline}</div>
                </div>
            `).join('');

            $list.html(deadlinesHtml);
        },

        /**
         * Render workload analysis for supervisor
         */
        _renderWorkloadAnalysis: function () {
            const workload = this.dashboardData.workload_analysis || {};
            
            // This would render a detailed workload widget
            console.log('Workload analysis:', workload);
        },

        /**
         * Render opportunities for company
         */
        _renderOpportunities: function () {
            const opportunities = this.dashboardData.internship_opportunities || {};
            
            // This would render opportunities widget
            console.log('Opportunities:', opportunities);
        },

        /**
         * Render system health for admin
         */
        _renderSystemHealth: function () {
            const health = this.dashboardData.system_health || {};
            
            // This would render system health widget
            console.log('System health:', health);
        },

        // ===============================
        // CHART RENDERING METHODS
        // ===============================

        /**
         * Check if Chart.js is available and show error if not
         */
        _checkChartAvailability: function () {
            if (typeof Chart === 'undefined') {
                console.error('Chart.js is not available. Please ensure Chart.js is loaded.');
                this._showNotification('Charts are not available. Please refresh the page.', 'warning');
                return false;
            }
            return true;
        },

        /**
         * Render progress chart for student
         */
        _renderProgressChart: function (data) {
            const ctx = this.$('#progressChart')[0];
            if (!ctx) return;

            if (this.charts.progressChart) {
                this.charts.progressChart.destroy();
            }

            // Check if Chart.js is available
            if (!this._checkChartAvailability()) {
                return;
            }

            this.charts.progressChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels || [],
                    datasets: [{
                        label: 'Progress %',
                        data: data.data || [],
                        borderColor: '#28a745',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });
        },

        /**
         * Render grade evolution chart for student
         */
        _renderGradeEvolutionChart: function (data) {
            const ctx = this.$('#gradeChart')[0];
            if (!ctx) return;

            if (this.charts.gradeChart) {
                this.charts.gradeChart.destroy();
            }

            // Check if Chart.js is available
            if (!this._checkChartAvailability()) {
                return;
            }

            this.charts.gradeChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels || [],
                    datasets: [{
                        label: 'Grade',
                        data: data.data || [],
                        borderColor: '#ffc107',
                        backgroundColor: 'rgba(255, 193, 7, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 20
                        }
                    }
                }
            });
        },

        /**
         * Render student progress chart for supervisor
         */
        _renderStudentProgressChart: function (data) {
            const ctx = this.$('#studentProgressChart')[0];
            if (!ctx) return;

            if (this.charts.studentProgressChart) {
                this.charts.studentProgressChart.destroy();
            }

            // Check if Chart.js is available
            if (!this._checkChartAvailability()) {
                return;
            }

            this.charts.studentProgressChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.labels || [],
                    datasets: [{
                        label: 'Progress %',
                        data: data.data || [],
                        backgroundColor: '#007bff',
                        borderColor: '#0056b3',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });
        },

        /**
         * Render grade distribution chart for supervisor
         */
        _renderGradeDistributionChart: function (data) {
            const ctx = this.$('#gradeDistributionChart')[0];
            if (!ctx) return;

            if (this.charts.gradeDistributionChart) {
                this.charts.gradeDistributionChart.destroy();
            }

            // Check if Chart.js is available
            if (!this._checkChartAvailability()) {
                return;
            }

            this.charts.gradeDistributionChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: data.labels || [],
                    datasets: [{
                        data: data.data || [],
                        backgroundColor: ['#28a745', '#ffc107', '#dc3545', '#17a2b8'],
                        borderWidth: 2,
                        borderColor: '#fff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        },

        /**
         * Render internship distribution chart for company
         */
        _renderInternshipDistributionChart: function (data) {
            const ctx = this.$('#internshipDistributionChart')[0];
            if (!ctx) return;

            if (this.charts.internshipDistributionChart) {
                this.charts.internshipDistributionChart.destroy();
            }

            // Check if Chart.js is available
            if (!this._checkChartAvailability()) {
                return;
            }

            this.charts.internshipDistributionChart = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: data.labels || [],
                    datasets: [{
                        data: data.data || [],
                        backgroundColor: ['#17a2b8', '#28a745', '#ffc107', '#dc3545'],
                        borderWidth: 2,
                        borderColor: '#fff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        },

        /**
         * Render timeline chart for company
         */
        _renderTimelineChart: function (data) {
            const ctx = this.$('#timelineChart')[0];
            if (!ctx) return;

            if (this.charts.timelineChart) {
                this.charts.timelineChart.destroy();
            }

            // Check if Chart.js is available
            if (!this._checkChartAvailability()) {
                return;
            }

            this.charts.timelineChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels || [],
                    datasets: [{
                        label: 'Internships',
                        data: data.data || [],
                        borderColor: '#17a2b8',
                        backgroundColor: 'rgba(23, 162, 184, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        },

        // ===============================
        // ADMIN CHART METHODS (reuse existing)
        // ===============================

        _renderStatusChart: function (data) {
            // Reuse existing status chart logic
            const ctx = this.$('#statusChart')[0];
            if (!ctx) return;

            if (this.charts.statusChart) {
                this.charts.statusChart.destroy();
            }

            // Check if Chart.js is available
            if (!this._checkChartAvailability()) {
                return;
            }

            this.charts.statusChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: data.map(item => item.label),
                    datasets: [{
                        data: data.map(item => item.value),
                        backgroundColor: data.map(item => item.color),
                        borderWidth: 2,
                        borderColor: '#fff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        },

        _renderTrendsChart: function (data) {
            // Reuse existing trends chart logic
            const ctx = this.$('#trendsChart')[0];
            if (!ctx) return;

            if (this.charts.trendsChart) {
                this.charts.trendsChart.destroy();
            }

            // Check if Chart.js is available
            if (!this._checkChartAvailability()) {
                return;
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
                            tension: 0.4
                        },
                        {
                            label: 'Completed',
                            data: data.map(item => item.completed),
                            borderColor: '#28a745',
                            backgroundColor: 'rgba(40, 167, 69, 0.1)',
                            borderWidth: 3,
                            fill: true,
                            tension: 0.4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        },

        _renderGradeChart: function (data) {
            // Reuse existing grade chart logic
            const ctx = this.$('#gradeChart')[0];
            if (!ctx) return;

            if (this.charts.gradeChart) {
                this.charts.gradeChart.destroy();
            }

            // Check if Chart.js is available
            if (!this._checkChartAvailability()) {
                return;
            }

            this.charts.gradeChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.map(item => item.label),
                    datasets: [{
                        label: 'Students',
                        data: data.map(item => item.value),
                        backgroundColor: data.map(item => item.color),
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        },

        _renderWorkloadChart: function (data) {
            // Reuse existing workload chart logic
            const ctx = this.$('#workloadChart')[0];
            if (!ctx) return;

            if (this.charts.workloadChart) {
                this.charts.workloadChart.destroy();
            }

            // Check if Chart.js is available
            if (!this._checkChartAvailability()) {
                return;
            }

            const topData = data.slice(0, 5);

            this.charts.workloadChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: topData.map(item => item.name),
                    datasets: [{
                        label: 'Utilization %',
                        data: topData.map(item => item.utilization),
                        backgroundColor: topData.map(item => item.color),
                        borderWidth: 1
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            beginAtZero: true,
                            max: 120
                        }
                    }
                }
            });
        },

        _renderPerformanceChart: function (data) {
            // Reuse existing performance chart logic
            const ctx = this.$('#performanceChart')[0];
            if (!ctx) return;

            if (this.charts.performanceChart) {
                this.charts.performanceChart.destroy();
            }

            // Check if Chart.js is available
            if (!this._checkChartAvailability()) {
                return;
            }

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
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        r: {
                            beginAtZero: true,
                            max: 20
                        }
                    }
                }
            });
        },

        // ===============================
        // EVENT HANDLERS
        // ===============================

        _setupEventHandlers: function () {
            // Refresh button
            this.$('#refreshDashboard').on('click', this._onRefreshClicked.bind(this));
            
            // Role-specific buttons
            this.$('#viewMyInternships').on('click', this._onViewMyInternships.bind(this));
            this.$('#viewMyStudents').on('click', this._onViewMyStudents.bind(this));
            this.$('#viewCompanyInternships').on('click', this._onViewCompanyInternships.bind(this));
            this.$('#exportDashboard').on('click', this._onExportClicked.bind(this));

            // Keyboard shortcuts
            $(document).on('keydown', this._onKeyDown.bind(this));
        },

        _onRefreshClicked: function (ev) {
            ev.preventDefault();
            this._refreshDashboard();
        },

        _onViewMyInternships: function (ev) {
            ev.preventDefault();
            this._navigateToInternships();
        },

        _onViewMyStudents: function (ev) {
            ev.preventDefault();
            this._navigateToStudents();
        },

        _onViewCompanyInternships: function (ev) {
            ev.preventDefault();
            this._navigateToCompanyInternships();
        },

        _onExportClicked: function (ev) {
            ev.preventDefault();
            this._exportDashboard();
        },

        _onKeyDown: function (ev) {
            if (ev.ctrlKey && ev.key === 'r') {
                ev.preventDefault();
                this._refreshDashboard();
            }
        },

        // ===============================
        // NAVIGATION METHODS
        // ===============================

        _navigateToInternships: function () {
            this.do_action({
                name: 'My Internships',
                type: 'ir.actions.act_window',
                res_model: 'internship.stage',
                view_mode: 'tree,form,kanban',
                domain: [('student_id.user_id', '=', this.env.user.id)],
                target: 'current',
            });
        },

        _navigateToStudents: function () {
            this.do_action({
                name: 'My Students',
                type: 'ir.actions.act_window',
                res_model: 'internship.stage',
                view_mode: 'tree,form,kanban',
                domain: [('supervisor_id.user_id', '=', this.env.user.id)],
                target: 'current',
            });
        },

        _navigateToCompanyInternships: function () {
            this.do_action({
                name: 'Company Internships',
                type: 'ir.actions.act_window',
                res_model: 'internship.stage',
                view_mode: 'tree,form,kanban',
                domain: [('company_id', '=', this.env.company.id)],
                target: 'current',
            });
        },

        // ===============================
        // UTILITY METHODS
        // ===============================

        _refreshDashboard: function () {
            if (this.isLoading) return;

            this.isLoading = true;
            const $refreshBtn = this.$('#refreshDashboard');
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

        _exportDashboard: function () {
            this._showNotification('Export feature coming soon', 'info');
        },

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

        _updateLastUpdated: function () {
            const timestamp = this.dashboardData.last_updated || new Date().toISOString();
            this.$('#lastUpdated').text(new Date(timestamp).toLocaleString());
        },

        _setupResponsiveness: function () {
            $(window).on('resize', this._debounce(() => {
                Object.values(this.charts).forEach(chart => {
                    if (chart && chart.resize) {
                        chart.resize();
                    }
                });
            }, 250));
        },

        _startAutoRefresh: function () {
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

        _showNotification: function (message, type) {
            this.displayNotification({
                title: _t('Dashboard'),
                message: message,
                type: type || 'info',
                sticky: false,
            });
        },

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

        destroy: function () {
            Object.values(this.charts).forEach(chart => {
                if (chart && typeof chart.destroy === 'function') {
                    chart.destroy();
                }
            });

            $(window).off('resize');
            $(document).off('keydown');

            this._super();
        }
    });

    // Register the role-based dashboard action
    core.action_registry.add('internship_role_dashboard', RoleDashboard);

    return RoleDashboard;
});
