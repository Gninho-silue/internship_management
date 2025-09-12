/**
 * Role-Based Dashboard JavaScript Implementation
 * ============================================
 * 
 */

/** @odoo-module **/

import { AbstractAction } from "@web/webclient/actions/abstract_action";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";

export class InternshipRoleDashboard extends AbstractAction {
    setup() {
        super.setup();
        this.rpc = useService("rpc");
        this.notification = useService("notification");
        this.action = useService("action");
        
        this.state = useState({
            dashboardData: {},
            isLoading: true,
            userRole: 'default',
            charts: {},
        });
        
        onMounted(() => {
            this.loadDashboard();
        });
        
        onWillUnmount(() => {
            this.destroyCharts();
        });
    }

    /**
     * Load dashboard data based on user role
     */
    async loadDashboard() {
        try {
            this.state.isLoading = true;
            
            // Get dashboard data from backend
            const dashboardData = await this.rpc("/web/dataset/call_kw", {
                model: "internship.analytics",
                method: "get_dashboard_data",
                args: [],
                kwargs: {}
            });
            
            this.state.dashboardData = dashboardData;
            this.state.userRole = dashboardData.user_role || 'default';
            this.state.isLoading = false;
            
            // Render charts after data is loaded
            this.renderCharts();
            
        } catch (error) {
            console.error("Dashboard loading error:", error);
            this.notification.add("Failed to load dashboard data", {
                type: "danger"
            });
            this.state.isLoading = false;
        }
    }

    /**
     * Render charts based on loaded data
     */
    renderCharts() {
        if (typeof Chart === 'undefined') {
            console.warn('Chart.js not available, skipping chart rendering');
            return;
        }

        // Clear existing charts
        this.destroyCharts();

        try {
            const data = this.state.dashboardData;
            
            // KPI Progress Chart
            if (data.kpi_cards && data.kpi_cards.length > 0) {
                this.renderKpiChart(data.kpi_cards);
            }
            
            // Status Distribution Chart
            if (data.charts && data.charts.status_distribution) {
                this.renderStatusChart(data.charts.status_distribution);
            }
            
            // Timeline Chart
            if (data.charts && data.charts.timeline_data) {
                this.renderTimelineChart(data.charts.timeline_data);
            }
            
        } catch (error) {
            console.error("Chart rendering error:", error);
        }
    }

    /**
     * Render KPI chart
     */
    renderKpiChart(kpiData) {
        const canvas = this.el.querySelector('#kpiChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        this.state.charts.kpi = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: kpiData.map(kpi => kpi.title),
                datasets: [{
                    data: kpiData.map(kpi => kpi.value),
                    backgroundColor: [
                        '#17a2b8', '#28a745', '#ffc107', '#dc3545', '#6f42c1'
                    ],
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
    }

    /**
     * Render status distribution chart
     */
    renderStatusChart(statusData) {
        const canvas = this.el.querySelector('#statusChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        this.state.charts.status = new Chart(ctx, {
            type: 'bar',
            data: statusData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    /**
     * Render timeline chart
     */
    renderTimelineChart(timelineData) {
        const canvas = this.el.querySelector('#timelineChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        this.state.charts.timeline = new Chart(ctx, {
            type: 'line',
            data: timelineData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'month'
                        }
                    },
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    /**
     * Destroy all charts to prevent memory leaks
     */
    destroyCharts() {
        Object.values(this.state.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        this.state.charts = {};
    }

    /**
     * Refresh dashboard data
     */
    async refreshDashboard() {
        await this.loadDashboard();
        this.notification.add("Dashboard refreshed successfully", {
            type: "success"
        });
    }

    /**
     * Navigate to internships view
     */
    viewMyInternships() {
        this.action.doAction({
            name: "My Internships",
            type: "ir.actions.act_window",
            res_model: "internship.stage",
            view_mode: "kanban,tree,form",
            domain: [["student_id.user_id", "=", this.user.userId]],
            target: "current"
        });
    }

    /**
     * Navigate to students view (for supervisors)
     */
    viewMyStudents() {
        this.action.doAction({
            name: "My Students",
            type: "ir.actions.act_window",
            res_model: "internship.stage",
            view_mode: "tree,form,kanban",
            domain: [["supervisor_id.user_id", "=", this.user.userId]],
            target: "current"
        });
    }

    /**
     * Navigate to all internships (for admins)
     */
    viewAllInternships() {
        this.action.doAction({
            name: "All Internships",
            type: "ir.actions.act_window",
            res_model: "internship.stage",
            view_mode: "kanban,tree,form",
            target: "current"
        });
    }
}

// Template for the dashboard
InternshipRoleDashboard.template = "internship_management.RoleDashboardTemplate";

// Register the component with the action registry
registry.category("actions").add("internship_role_dashboard", InternshipRoleDashboard);