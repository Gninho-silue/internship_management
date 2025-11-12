/** @odoo-module **/

import {Component, onWillStart, useState} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

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

            todayTasks: 0,
            pendingTasks: 0,

            // Messages Chatter
            totalMessages: 0,
            unreadMessages: 0,

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
            let messageDomain = [];

            if (isAdmin || isCoordinator) {
                stageDomain = [];
                studentDomain = [];
                supervisorDomain = [];
                documentDomain = [];
                presentationDomain = [];
                todoDomain = [];
                meetingDomain = [];
                messageDomain = [];
            } else if (isSupervisor) {
                const supervisorId = await this.orm.call("internship.supervisor", "search", [
                    [["user_id", "=", this.env.services.user.userId]]
                ]);

                if (supervisorId.length > 0) {
                    stageDomain = [["supervisor_id", "=", supervisorId[0]]];

                    // CORRIGÉ: Récupérer étudiants via stages (Many2many)
                    const stages = await this.orm.call("internship.stage", "search_read", [
                        [["supervisor_id", "=", supervisorId[0]]],
                        ["student_ids"]
                    ]);

                    // Extraire tous les IDs d'étudiants de tous les stages
                    const studentIds = [];
                    stages.forEach(stage => {
                        if (stage.student_ids && stage.student_ids.length > 0) {
                            studentIds.push(...stage.student_ids);
                        }
                    });
                    // Supprimer les doublons
                    const uniqueStudentIds = [...new Set(studentIds)];

                    studentDomain = uniqueStudentIds.length > 0 ? [["id", "in", uniqueStudentIds]] : [["id", "=", 0]];

                    documentDomain = [["supervisor_id", "=", supervisorId[0]]];
                    presentationDomain = [["supervisor_id", "=", supervisorId[0]]];
                    todoDomain = [["stage_id.supervisor_id", "=", supervisorId[0]]];
                    // Supervisor voit : réunions organisées OU réunions où il participe
                    const supervisorPartnerId = await this.orm.call("res.users", "read", [
                        [this.env.services.user.userId],
                        ["partner_id"]
                    ]);
                    const partnerId = supervisorPartnerId[0].partner_id[0];

                    meetingDomain = [
                        "|",
                        ["organizer_id", "=", this.env.services.user.userId],
                        ["partner_ids", "in", [partnerId]]
                    ];

                    // Messages Chatter - utilisateur mentionné ou abonné
                    messageDomain = [["author_id", "!=", this.env.services.user.userId]];
                    supervisorDomain = [["id", "=", supervisorId[0]]];
                }
            } else if (isStudent) {
                // Tâches: basé sur l'utilisateur assigné via assigned_to_ids (Many2many)
                todoDomain = [["assigned_to_ids.user_id", "=", this.env.services.user.userId]];

                // Meetings: basé sur le partner de l'utilisateur (même domaine que dans openMeetings)
                const studentPartnerId = await this.orm.call("res.users", "read", [
                    [this.env.services.user.userId],
                    ["partner_id"]
                ]);
                const partnerId = studentPartnerId[0].partner_id[0];
                meetingDomain = [["partner_ids", "in", [partnerId]]];

                // Documents: basé sur student_id.user_id (un document = un étudiant)
                documentDomain = [["student_id.user_id", "=", this.env.services.user.userId]];

                // Présentations: basé sur student_id.user_id (une présentation = un étudiant)
                presentationDomain = [["student_id.user_id", "=", this.env.services.user.userId]];

                // Stages: basé sur student_ids.user_id (Many2many)
                stageDomain = [["student_ids.user_id", "=", this.env.services.user.userId]];

                // Autres domaines pour cohérence
                messageDomain = [["author_id", "!=", this.env.services.user.userId]];

                // Récupérer la fiche student si elle existe pour les domaines spécifiques
                const studentId = await this.orm.call("internship.student", "search", [[
                    ["user_id", "=", this.env.services.user.userId]
                ]]);
                if (studentId.length > 0) {
                    studentDomain = [["id", "=", studentId[0]]];
                    // Pour les superviseurs: filtrer via les stages (supervisor n'a pas de student_ids direct)
                    // On compte les superviseurs qui encadrent des stages avec cet étudiant
                    const stagesWithSupervisor = await this.orm.call("internship.stage", "search_read", [
                        [["student_ids", "in", [studentId[0]]]],
                        ["supervisor_id"]
                    ]);
                    const supervisorIds = stagesWithSupervisor
                        .map(stage => stage.supervisor_id ? stage.supervisor_id[0] : null)
                        .filter(id => id !== null);
                    if (supervisorIds.length > 0) {
                        supervisorDomain = [["id", "in", supervisorIds]];
                    } else {
                        supervisorDomain = [["id", "=", 0]];
                    }
                } else {
                    studentDomain = [["id", "=", 0]];
                    supervisorDomain = [["id", "=", 0]];
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

            // Tâches terminées
            this.state.completedTasks = await this.orm.call(
                "internship.todo", "search_count",
                [todoDomain.concat([["state", "=", "done"]])]
            );

            // Tâches en retard : deadline < maintenant et state in ['todo', 'in_progress']
            const now = new Date().toISOString();
            this.state.overdueTasks = await this.orm.call(
                "internship.todo", "search_count",
                [todoDomain.concat([
                    ["deadline", "<", now],
                    ["state", "in", ["todo", "in_progress"]]
                ])]
            );

            // Tâches en attente (à faire)
            this.state.pendingTasks = await this.orm.call(
                "internship.todo", "search_count",
                [todoDomain.concat([["state", "=", "todo"]])]
            );

            // Tâches d'aujourd'hui : deadline entre début et fin de la journée d'aujourd'hui
            const todayStart = new Date().toISOString().split('T')[0] + " 00:00:00";
            const todayEnd = new Date().toISOString().split('T')[0] + " 23:59:59";
            this.state.todayTasks = await this.orm.call(
                "internship.todo", "search_count",
                [todoDomain.concat([
                    ["deadline", ">=", todayStart],
                    ["deadline", "<=", todayEnd],
                    ["state", "in", ["todo", "in_progress"]]
                ])]
            );

            this.state.totalMeetings = await this.orm.call(
                "internship.meeting", "search_count", [meetingDomain]
            );

            // Réunions à venir : date > maintenant et état approprié
            // Note: Odoo compare les dates Datetime en UTC, donc toISOString() est correct
            const now_meet = new Date().toISOString();
            // Créer le domaine pour les réunions à venir
            const upcomingMeetingDomain = meetingDomain.concat([
                ["date", ">", now_meet],
                ["state", "!=", "completed"],
                ["state", "!=", "cancelled"]
            ]);
            this.state.upcomingMeetings = await this.orm.call(
                "internship.meeting", "search_count", [upcomingMeetingDomain]
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
            domain = [["student_ids.user_id", "=", this.env.services.user.userId]];
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
                    ["student_ids"]
                ]);

                // Extraire tous les IDs d'étudiants de tous les stages
                const studentIds = [];
                stages.forEach(stage => {
                    if (stage.student_ids && stage.student_ids.length > 0) {
                        studentIds.push(...stage.student_ids);
                    }
                });
                // Supprimer les doublons
                const uniqueStudentIds = [...new Set(studentIds)];

                if (uniqueStudentIds.length > 0) {
                    domain = [["id", "in", uniqueStudentIds]];
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

    openTasks() {
        // Ouvrir les tâches selon le rôle de l'utilisateur
        let domain = [];
        if (this.state.isStudent) {
            domain = [["assigned_to_ids.user_id", "=", this.env.services.user.userId]];
        } else if (this.state.isSupervisor) {
            domain = [["stage_id.supervisor_id.user_id", "=", this.env.services.user.userId]];
        }

        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "internship.todo",
            views: [[false, "list"], [false, "form"]],
            domain: domain,
            context: {},
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


    async openMeetings() {
        let domain = [];

        // Récupérer le partner_id de l'utilisateur
        const userData = await this.orm.call("res.users", "read", [
            [this.env.services.user.userId],
            ["partner_id"]
        ]);
        const partnerId = userData[0].partner_id[0];

        if (this.state.isStudent) {
            // Étudiant voit où il participe
            domain = [["partner_ids", "in", [partnerId]]];
        } else if (this.state.isSupervisor) {
            // Superviseur voit où il organise OU participe
            domain = [
                "|",
                ["organizer_id", "=", this.env.services.user.userId],
                ["partner_ids", "in", [partnerId]]
            ];
        }

        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "internship.meeting",
            views: [[false, "calendar"], [false, "list"], [false, "form"]],
            domain: domain,
            target: "current",
        });
    }

}

InternshipDashboard.template = "internship_management.Dashboard";

registry.category("actions").add("internship_dashboard", InternshipDashboard);