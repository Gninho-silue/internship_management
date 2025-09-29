/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class InternshipDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            // Statistiques stages
            totalInternships: 0,
            activeInternships: 0,
            completedInternships: 0,
            pendingInternships: 0,

            // Statistiques étudiants
            totalStudents: 0,
            activeStudents: 0,

            // Statistiques superviseurs
            totalSupervisors: 0,
            activeSupervisors: 0,

            // Documents et présentations
            totalDocuments: 0,
            pendingReviews: 0,
            totalPresentations: 0,
            pendingPresentations: 0,

            // Tâches
            totalTasks: 0,
            overdueTasks: 0,
            completedTasks: 0,

            // Réunions
            totalMeetings: 0,
            upcomingMeetings: 0,

            // Alertes
            totalAlerts: 0,
            activeAlerts: 0,
            highPriorityAlerts: 0,

            // Communications
            totalCommunications: 0,
            unreadCommunications: 0,

            // Rôles utilisateur
            isAdmin: false,
            isCoordinator: false,
            isSupervisor: false,
            isStudent: false,

            loading: true,
        });

        onWillStart(async () => {
            await this.loadDashboardData();
        });
    }

    async loadDashboardData() {
        try {
            const isAdmin = await this.orm.call("res.users", "has_group", [
                "internship_management.group_internship_admin"
            ]);

            const isCoordinator = await this.orm.call("res.users", "has_group", [
                "internship_management.group_internship_coordinator"
            ]);

            const isSupervisor = await this.orm.call("res.users", "has_group", [
                "internship_management.group_internship_supervisor"
            ]);

            const isStudent = await this.orm.call("res.users", "has_group", [
                "internship_management.group_internship_student"
            ]);

            this.state.isAdmin = isAdmin;
            this.state.isCoordinator = isCoordinator;
            this.state.isSupervisor = isSupervisor;
            this.state.isStudent = isStudent;

            let stageDomain = [];
            let studentDomain = [];
            let supervisorDomain = [];
            let documentDomain = [];
            let presentationDomain = [];
            let todoDomain = [];
            let meetingDomain = [];
            let alertDomain = [];
            let communicationDomain = [];

            if (isAdmin || isCoordinator) {
                stageDomain = [];
                studentDomain = [];
                supervisorDomain = [];
                documentDomain = [];
                presentationDomain = [];
                todoDomain = [];
                meetingDomain = [];
                alertDomain = [];
                communicationDomain = [];
            } else if (isSupervisor) {
                const supervisorId = await this.orm.call("internship.supervisor", "search", [
                    [["user_id", "=", this.env.services.user.userId]]
                ]);

                if (supervisorId.length > 0) {
                    stageDomain = [["supervisor_id", "=", supervisorId[0]]];

                    // CORRIGÉ: Récupérer étudiants via stages
                    const stages = await this.orm.call("internship.stage", "search_read", [
                        [["supervisor_id", "=", supervisorId[0]]],
                        ["student_id"]
                    ]);

                    const studentIds = stages
                        .map(stage => stage.student_id ? stage.student_id[0] : null)
                        .filter(id => id !== null);

                    studentDomain = studentIds.length > 0 ? [["id", "in", studentIds]] : [["id", "=", 0]];

                    documentDomain = [["supervisor_id", "=", supervisorId[0]]];
                    presentationDomain = [["supervisor_id", "=", supervisorId[0]]];
                    todoDomain = [["stage_id.supervisor_id", "=", supervisorId[0]]];
                    meetingDomain = [["organizer_id", "=", this.env.services.user.userId]];

                    // CORRIGÉ: Alertes via stages
                    const stageIds = await this.orm.call("internship.stage", "search", [
                        [["supervisor_id", "=", supervisorId[0]]]
                    ]);
                    alertDomain = stageIds.length > 0 ? [["stage_id", "in", stageIds]] : [["id", "=", 0]];

                    communicationDomain = [["recipient_ids", "in", [this.env.services.user.userId]]];
                    supervisorDomain = [["id", "=", supervisorId[0]]];
                }
            } else if (isStudent) {
                const studentId = await this.orm.call("internship.student", "search", [
                    [["user_id", "=", this.env.services.user.userId]]
                ]);

                if (studentId.length > 0) {
                    stageDomain = [["student_id", "=", studentId[0]]];
                    documentDomain = [["student_id", "=", studentId[0]]];
                    presentationDomain = [["student_id", "=", studentId[0]]];
                    todoDomain = [["stage_id.student_id", "=", studentId[0]]];
                    meetingDomain = [["participant_ids", "in", [this.env.services.user.userId]]];
                    alertDomain = [["student_id", "=", studentId[0]]];
                    communicationDomain = [["recipient_ids", "in", [this.env.services.user.userId]]];

                    studentDomain = [["id", "=", studentId[0]]];
                    supervisorDomain = [["student_ids", "in", [studentId[0]]]];
                }
            }

            // Charger toutes les statistiques
            this.state.totalInternships = await this.orm.call(
                "internship.stage", "search_count", [stageDomain]
            );

            this.state.activeInternships = await this.orm.call(
                "internship.stage", "search_count",
                [stageDomain.concat([["state", "=", "in_progress"]])]
            );

            this.state.completedInternships = await this.orm.call(
                "internship.stage", "search_count",
                [stageDomain.concat([["state", "=", "completed"]])]
            );

            this.state.pendingInternships = await this.orm.call(
                "internship.stage", "search_count",
                [stageDomain.concat([["state", "in", ["draft", "submitted", "approved"]]])]
            );

            this.state.totalStudents = await this.orm.call(
                "internship.student", "search_count", [studentDomain]
            );

            this.state.totalSupervisors = await this.orm.call(
                "internship.supervisor", "search_count", [supervisorDomain]
            );

            this.state.totalDocuments = await this.orm.call(
                "internship.document", "search_count", [documentDomain]
            );

            this.state.pendingReviews = await this.orm.call(
                "internship.document", "search_count",
                [documentDomain.concat([["state", "=", "submitted"]])]
            );

            this.state.totalPresentations = await this.orm.call(
                "internship.presentation", "search_count", [presentationDomain]
            );

            this.state.pendingPresentations = await this.orm.call(
                "internship.presentation", "search_count",
                [presentationDomain.concat([["status", "=", "submitted"]])]
            );

            this.state.totalTasks = await this.orm.call(
                "internship.todo", "search_count", [todoDomain]
            );

            this.state.completedTasks = await this.orm.call(
                "internship.todo", "search_count",
                [todoDomain.concat([["state", "=", "completed"]])]
            );

            this.state.totalMeetings = await this.orm.call(
                "internship.meeting", "search_count", [meetingDomain]
            );

            this.state.totalAlerts = await this.orm.call(
                "internship.alert", "search_count", [alertDomain]
            );

            this.state.activeAlerts = await this.orm.call(
                "internship.alert", "search_count",
                [alertDomain.concat([["state", "=", "active"]])]
            );

            this.state.highPriorityAlerts = await this.orm.call(
                "internship.alert", "search_count",
                [alertDomain.concat([["priority", "=", "1"]])]
            );

            this.state.totalCommunications = await this.orm.call(
                "internship.communication", "search_count", [communicationDomain]
            );

            this.state.loading = false;
        } catch (error) {
            console.error("Erreur chargement dashboard:", error);
            this.state.loading = false;
        }
    }

    openInternships() {
        let domain = [];
        if (this.state.isStudent) {
            domain = [["student_id.user_id", "=", this.env.services.user.userId]];
        } else if (this.state.isSupervisor) {
            domain = [["supervisor_id.user_id", "=", this.env.services.user.userId]];
        }

        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "internship.stage",
            views: [[false, "kanban"], [false, "list"], [false, "form"]],
            domain: domain,
            target: "current",
        });
    }

    async openStudents() {
        let domain = [];

        if (this.state.isSupervisor) {
            const supervisorId = await this.orm.call("internship.supervisor", "search", [
                [["user_id", "=", this.env.services.user.userId]]
            ]);

            if (supervisorId.length > 0) {
                const stages = await this.orm.call("internship.stage", "search_read", [
                    [["supervisor_id", "=", supervisorId[0]]],
                    ["student_id"]
                ]);

                const studentIds = stages
                    .map(stage => stage.student_id ? stage.student_id[0] : null)
                    .filter(id => id !== null);

                if (studentIds.length > 0) {
                    domain = [["id", "in", studentIds]];
                } else {
                    domain = [["id", "=", 0]];
                }
            }
        }

        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "internship.student",
            views: [[false, "list"], [false, "form"]],
            domain: domain,
            target: "current",
        });
    }

    openPendingPresentations() {
        let domain = [["status", "=", "submitted"]];
        if (this.state.isStudent) {
            domain.push(["student_id.user_id", "=", this.env.services.user.userId]);
        } else if (this.state.isSupervisor) {
            domain.push(["supervisor_id.user_id", "=", this.env.services.user.userId]);
        }

        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "internship.presentation",
            views: [[false, "list"], [false, "form"]],
            domain: domain,
            target: "current",
        });
    }

    async openAlerts() {
        let domain = [["state", "=", "active"]];

        if (this.state.isStudent) {
            const studentId = await this.orm.call("internship.student", "search", [
                [["user_id", "=", this.env.services.user.userId]]
            ]);

            if (studentId.length > 0) {
                domain.push(["student_id", "=", studentId[0]]);
            }
        } else if (this.state.isSupervisor) {
            const supervisorId = await this.orm.call("internship.supervisor", "search", [
                [["user_id", "=", this.env.services.user.userId]]
            ]);

            if (supervisorId.length > 0) {
                const stages = await this.orm.call("internship.stage", "search", [
                    [["supervisor_id", "=", supervisorId[0]]]
                ]);

                if (stages.length > 0) {
                    domain.push(["stage_id", "in", stages]);
                } else {
                    domain = [["id", "=", 0]];
                }
            }
        }

        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "internship.alert",
            views: [[false, "list"], [false, "form"]],
            domain: domain,
            target: "current",
        });
    }

    async openDocuments() {
        let domain = [];
        if (this.state.isStudent) {
            domain = [["student_id.user_id", "=", this.env.services.user.userId]];
        } else if (this.state.isSupervisor) {
            domain = [["supervisor_id.user_id", "=", this.env.services.user.userId]];
        }

        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "internship.document",
            views: [[false, "list"], [false, "form"]],
            domain: domain,
            target: "current",
        });
    }

    async openTasks() {
        let domain = [];
        if (this.state.isStudent) {
            domain = [["stage_id.student_id.user_id", "=", this.env.services.user.userId]];
        } else if (this.state.isSupervisor) {
            domain = [["stage_id.supervisor_id.user_id", "=", this.env.services.user.userId]];
        }

        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "internship.todo",
            views: [[false, "list"], [false, "form"]],
            domain: domain,
            target: "current",
        });
    }

    async openMeetings() {
        let domain = [];
        if (this.state.isStudent) {
            domain = [["participant_ids", "in", [this.env.services.user.userId]]];
        } else if (this.state.isSupervisor) {
            domain = [["organizer_id", "=", this.env.services.user.userId]];
        }

        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "internship.meeting",
            views: [[false, "list"], [false, "form"]],
            domain: domain,
            target: "current",
        });
    }
}

InternshipDashboard.template = "internship_management.Dashboard";

registry.category("actions").add("internship_dashboard", InternshipDashboard);