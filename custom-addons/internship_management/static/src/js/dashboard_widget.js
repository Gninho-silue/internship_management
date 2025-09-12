// /** @odoo-module **/
//
// import { Component, useState, onWillStart, onMounted } from "@odoo/owl";
// import { registry } from "@web/core/registry";
// import { useService } from "@web/core/utils/hooks";
//
// export class InternshipDashboard extends Component {
//     setup() {
//         this.rpc = useService("rpc");
//         this.notification = useService("notification");
//         this.state = useState({
//             data: null,
//             loading: true,
//             lastUpdate: null,
//             filters: {
//                 date_from: null,
//                 date_to: null,
//                 supervisor_id: null,
//                 area_id: null
//             }
//         });
//
//         onWillStart(async () => {
//             await this.loadDashboardData();
//         });
//
//         onMounted(() => {
//             this.initializeCharts();
//             this.startAutoRefresh();
//         });
//     }
//
//     async loadDashboardData() {
//         try {
//             this.state.loading = true;
//             const data = await this.rpc("/web/dataset/call_kw", {
//                 model: "internship.dashboard",
//                 method: "get_dashboard_data",
//                 args: [],
//                 kwargs: {}
//             });
//
//             this.state.data = data;
//             this.state.lastUpdate = new Date().toLocaleTimeString();
//             this.state.loading = false;
//
//             this.notification.add("Dashboard refreshed successfully", {
//                 type: "success",
//                 sticky: false
//             });
//
//         } catch (error) {
//             console.error("Error loading dashboard data:", error);
//             this.state.loading = false;
//             this.notification.add("Error loading dashboard data", {
//                 type: "danger"
//             });
//         }
//     }
//
//     initializeCharts() {
//         if (!this.state.data) return;
//
//         // Initialize Chart.js charts
//         setTimeout(() => {
//             this.renderStatusChart();
//             this.renderTypeChart();
//             this.renderTimelineChart();
//             this.renderGradeChart();
//         }, 100);
//     }
//
//     renderStatusChart() {
//         const ctx = document.getElementById('statusChart');
//         if (!ctx || !this.state.data.charts.internship_by_status) return;
//
//         const chartData = this.state.data.charts.internship_by_status;
//
//         new Chart(ctx, {
//             type: 'doughnut',
//             data: {
//                 labels: chartData.labels,
//                 datasets: [{
//                     data: chartData.data,
//                     backgroundColor: chartData.colors,
//                     borderWidth: 2,
//                     borderColor: '#fff'
//                 }]
//             },
//             options: {
//                 responsive: true,
//                 maintainAspectRatio: false,
//                 plugins: {
//                     legend: {
//                         position: 'bottom'
//                     },
//                     title: {
//                         display: true,
//                         text: 'Internships by Status'
//                     }
//                 }
//             }
//         });
//     }
//
//     renderTypeChart() {
//         const ctx = document.getElementById('typeChart');
//         if (!ctx || !this.state.data.charts.internship_by_type) return;
//
//         const chartData = this.state.data.charts.internship_by_type;
//
//         new Chart(ctx, {
//             type: 'pie',
//             data: {
//                 labels: chartData.labels,
//                 datasets: [{
//                     data: chartData.data,
//                     backgroundColor: chartData.colors,
//                     borderWidth: 2,
//                     borderColor: '#fff'
//                 }]
//             },
//             options: {
//                 responsive: true,
//                 maintainAspectRatio: false,
//                 plugins: {
//                     legend: {
//                         position: 'right'
//                     },
//                     title: {
//                         display: true,
//                         text: 'Internships by Type'
//                     }
//                 }
//             }
//         });
//     }
//
//     renderTimelineChart() {
//         const ctx = document.getElementById('timelineChart');
//         if (!ctx || !this.state.data.charts.progress_timeline) return;
//
//         const chartData = this.state.data.charts.progress_timeline;
//
//         new Chart(ctx, {
//             type: 'line',
//             data: {
//                 labels: chartData.labels,
//                 datasets: chartData.datasets
//             },
//             options: {
//                 responsive: true,
//                 maintainAspectRatio: false,
//                 scales: {
//                     y: {
//                         beginAtZero: true,
//                         title: {
//                             display: true,
//                             text: 'Number of Internships'
//                         }
//                     }
//                 },
//                 plugins: {
//                     title: {
//                         display: true,
//                         text: 'Internship Progress Timeline'
//                     },
//                     legend: {
//                         position: 'top'
//                     }
//                 }
//             }
//         });
//     }
//
//     renderGradeChart() {
//         const ctx = document.getElementById('gradeChart');
//         if (!ctx || !this.state.data.charts.grade_distribution) return;
//
//         const chartData = this.state.data.charts.grade_distribution;
//
//         new Chart(ctx, {
//             type: 'bar',
//             data: {
//                 labels: chartData.labels,
//                 datasets: [{
//                     label: 'Number of Students',
//                     data: chartData.data,
//                     backgroundColor: chartData.colors,
//                     borderWidth: 1
//                 }]
//             },
//             options: {
//                 responsive: true,
//                 maintainAspectRatio: false,
//                 scales: {
//                     y: {
//                         beginAtZero: true,
//                         title: {
//                             display: true,
//                             text: 'Number of Students'
//                         }
//                     }
//                 },
//                 plugins: {
//                     title: {
//                         display: true,
//                         text: 'Grade Distribution'
//                     },
//                     legend: {
//                         display: false
//                     }
//                 }
//             }
//         });
//     }
//
//     startAutoRefresh() {
//         // Refresh dashboard every 5 minutes
//         setInterval(() => {
//             this.loadDashboardData();
//         }, 300000);
//     }
//
//     async onRefreshClick() {
//         await this.loadDashboardData();
//         this.initializeCharts();
//     }
//
//     getKpiTrend(value) {
//         // Simple trend calculation (you can make this more sophisticated)
//         return value >= 70 ? 'up' : value >= 50 ? 'stable' : 'down';
//     }
//
//     getAlertClass(alert) {
//         return {
//             'warning': 'alert-warning',
//             'info': 'alert-info',
//             'danger': 'alert-danger',
//             'success': 'alert-success'
//         }[alert.type] || 'alert-info';
//     }
//
//     formatNumber(num) {
//         return new Intl.NumberFormat().format(num);
//     }
//
//     formatPercentage(num) {
//         return `${num}%`;
//     }
// }
//
// InternshipDashboard.template = "internship_management.DashboardTemplate";
//
// // Register the component
// registry.category("actions").add("internship_dashboard", InternshipDashboard);