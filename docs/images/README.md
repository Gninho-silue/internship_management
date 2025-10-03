# 📸 Images pour le Guide Utilisateur

Ce dossier contient les images nécessaires pour illustrer le guide utilisateur du système de gestion des stages TechPal.

## 📋 Liste des Images Requises

### 1. **login_page.png**
- **Description** : Capture d'écran de la page de connexion personnalisée TechPal
- **Dimensions recommandées** : 1200x800 px
- **Contenu** : Page de login avec le thème personnalisé du module `internship_theme`
- **Utilisation** : Section 2.1 - Première connexion

### 2. **dashboard_admin.png**
- **Description** : Capture d'écran du tableau de bord administrateur
- **Dimensions recommandées** : 1400x900 px
- **Contenu** : Dashboard avec statistiques globales, alertes, et activité récente
- **Utilisation** : Section 4.1.1 - Tableau de bord administrateur

### 3. **dashboard_supervisor.png**
- **Description** : Capture d'écran du tableau de bord encadrant
- **Dimensions recommandées** : 1400x900 px
- **Contenu** : Dashboard avec stages en cours, documents à réviser, réunions
- **Utilisation** : Section 4.3.1 - Tableau de bord encadrant

### 4. **dashboard_student.png**
- **Description** : Capture d'écran du tableau de bord stagiaire
- **Dimensions recommandées** : 1400x900 px
- **Contenu** : Dashboard avec stage en cours, tâches, documents, réunions
- **Utilisation** : Section 4.4.1 - Tableau de bord stagiaire

### 5. **stages_kanban.png**
- **Description** : Capture d'écran de la vue Kanban des stages
- **Dimensions recommandées** : 1400x800 px
- **Contenu** : Vue Kanban avec colonnes (Brouillon, Soumis, En cours, Terminé)
- **Utilisation** : Section 4.3.3 - Vue Kanban

## 📝 Instructions de Capture

### Pour capturer les images :

1. **Démarrez votre serveur Odoo** :
   ```bash
   cd C:\Dev\odoo17-internship
   .\odoo-venv\Scripts\activate
   python .\odoo-source\odoo-bin -c .\config\odoo.conf
   ```

2. **Connectez-vous avec différents utilisateurs** :
   - **Admin** : Pour `dashboard_admin.png`
   - **Encadrant** : Pour `dashboard_supervisor.png`
   - **Stagiaire** : Pour `dashboard_student.png`

3. **Naviguez vers les bonnes pages** :
   - Dashboard : `Gestion des Stages > Tableau de Bord`
   - Kanban : `Gestion des Stages > Stages Encadrés`
   - Login : Page d'accueil non connecté

4. **Captures d'écran** :
   - Utilisez **Windows + Shift + S** pour une capture partielle
   - Ou utilisez **Windows + Print Screen** pour une capture complète
   - Sauvegardez avec les noms exacts indiqués ci-dessus

## 🎨 Conseils pour les Captures

- **Résolution** : Utilisez une résolution d'écran élevée (1920x1080 minimum)
- **Navigateur** : Chrome recommandé pour la meilleure qualité
- **Zoom** : Évitez le zoom du navigateur (100%)
- **Données** : Utilisez des données de démo pour avoir un contenu réaliste
- **Privé** : Masquez les informations sensibles si nécessaire

## ✅ Validation

Après avoir ajouté les images, vérifiez que :
- [ ] Toutes les images s'affichent correctement dans le guide
- [ ] Les dimensions sont appropriées (pas trop grandes/petites)
- [ ] Le contenu des images correspond aux descriptions
- [ ] Les images sont nettes et lisibles

## 🔄 Mise à Jour

Si le système évolue, pensez à mettre à jour ces images pour maintenir la cohérence avec l'interface réelle.
