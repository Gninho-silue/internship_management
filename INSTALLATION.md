# 📦 Guide d'Installation - Système de Gestion des Stages

Guide complet d'installation du système de gestion des stages TechPal sur Odoo 17.

---

## 📋 Table des Matières

- [Prérequis système](#prérequis-système)
- [Installation sur Windows](#installation-sur-windows)
- [Installation sur Linux](#installation-sur-linux)
- [Configuration](#configuration)
- [Installation des modules](#installation-des-modules)
- [Données de démonstration](#données-de-démonstration)
- [Dépannage](#dépannage)

---

## 💻 Prérequis système

### Configuration minimale recommandée

- **Processeur** : Intel i5 / AMD Ryzen 5 ou supérieur
- **RAM** : 8 GB minimum (16 GB recommandé)
- **Espace disque** : 10 GB libres
- **Connexion Internet** : Requise pour l'installation initiale

### Logiciels requis

| Logiciel | Version | Lien de téléchargement |
|----------|---------|----------------------|
| Python | 3.11+ | https://www.python.org/downloads/ |
| PostgreSQL | 16.x | https://www.postgresql.org/download/ |
| wkhtmltopdf | 0.12.6 | https://wkhtmltopdf.org/downloads.html |
| Git | Latest | https://git-scm.com/downloads |

---

## 🪟 Installation sur Windows

### Étape 1 : Installer Python 3.11+

```bash
# Télécharger depuis python.org
# ⚠️ IMPORTANT : Cocher "Add Python to PATH" lors de l'installation

# Vérifier l'installation
python --version
# Sortie attendue : Python 3.11.x ou supérieur
```

### Étape 2 : Installer PostgreSQL

```bash
# Télécharger PostgreSQL 16 depuis postgresql.org
# Lors de l'installation, noter le mot de passe du superuser "postgres"

# Créer un utilisateur odoo17
psql -U postgres
CREATE USER odoo17 WITH PASSWORD 'odoo17';
CREATE DATABASE internship_management_db OWNER odoo17;
ALTER USER odoo17 CREATEDB;
\q
```

### Étape 3 : Installer wkhtmltopdf

```bash
# Télécharger wkhtmltopdf 0.12.6 depuis wkhtmltopdf.org
# Installer dans C:\wkhtmltopdf\

# Ajouter au PATH système :
# Panneau de contrôle > Système > Paramètres système avancés
# Variables d'environnement > PATH > Ajouter : C:\wkhtmltopdf\bin
```

### Étape 4 : Cloner le projet

```bash
# Créer le dossier de travail
mkdir C:\Dev
cd C:\Dev

# Cloner le dépôt
git clone https://github.com/techpal-casablanca/odoo17-internship.git
cd odoo17-internship
```

### Étape 5 : Installer les dépendances Python

```bash
# Créer environnement virtuel
python -m venv odoo-venv

# Activer l'environnement
odoo-venv\Scripts\activate

# Mettre à jour pip
python -m pip install --upgrade pip

# Installer les dépendances Odoo
pip install -r odoo-source/requirements.txt
```

### Étape 6 : Configuration Odoo

Éditer le fichier `config/odoo.conf` :

```ini
[options]
admin_passwd = VOTRE_MOT_DE_PASSE_ADMIN_SECURISE
db_host = localhost
db_port = 5432
db_user = odoo17
db_password = odoo17
db_name = internship_management_db
addons_path = C:\Dev\odoo17-internship\odoo-source\addons,C:\Dev\odoo17-internship\custom-addons
data_dir = C:\Dev\odoo17-internship\filestore
logfile = C:\Dev\odoo17-internship\logs\odoo.log
report_url = http://localhost:8069
```

### Étape 7 : Premier démarrage

```bash
# Initialiser la base de données
python odoo-source/odoo-bin -c config/odoo.conf -d internship_management_db -i base --stop-after-init

# Redémarrer en mode normal
python odoo-source/odoo-bin -c config/odoo.conf
```

### Étape 8 : Accéder à l'interface

1. Ouvrir un navigateur : http://localhost:8069
2. Email : `admin`
3. Mot de passe : `admin` (⚠️ À changer après première connexion)


## 🐧 Installation sur Linux (Ubuntu/Debian)

### Étape 1 : Mettre à jour le système

```bash
sudo apt update && sudo apt upgrade -y
```

### Étape 2 : Installer les dépendances système

```bash
# Python et outils
sudo apt install -y python3.11 python3.11-venv python3-pip python3-dev

# PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# wkhtmltopdf
mkdir -p /tmp/wkhtmltopdf
cd /tmp/wkhtmltopdf
wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.focal_amd64.deb
sudo dpkg -i wkhtmltox_0.12.6-1.focal_amd64.deb || sudo apt-get install -f -y

# Autres dépendances
sudo apt install -y git build-essential libpq-dev libxml2-dev libxslt1-dev \
    libldap2-dev libsasl2-dev libjpeg-dev zlib1g-dev libffi-dev libssl-dev
```

### Étape 3 : Configurer PostgreSQL

```bash
sudo -u postgres createuser -s odoo17
sudo -u postgres psql
ALTER USER odoo17 WITH PASSWORD 'odoo17';
CREATE DATABASE internship_management_db OWNER odoo17;
\q
```

### Étape 4 : Cloner et installer

```bash
# Cloner le projet
cd /opt
sudo git clone https://github.com/techpal-casablanca/odoo17-internship.git
sudo chown -R $USER:$USER odoo17-internship
cd odoo17-internship

# Créer venv
python3.11 -m venv odoo-venv
source odoo-venv/bin/activate

# Installer dépendances
pip install -r odoo-source/requirements.txt
```

### Étape 5 : Configuration et démarrage

```bash
# Éditer config/odoo.conf
nano config/odoo.conf

# Lancer Odoo
python odoo-source/odoo-bin -c config/odoo.conf
```

---

## ⚙️ Configuration

### Fichier de configuration (config/odoo.conf)

```ini
[options]
# Sécurité
admin_passwd = VOTRE_MOT_DE_PASSE_SECURISE

# Base de données
db_host = localhost
db_port = 5432
db_user = odoo17
db_password = odoo17
db_name = internship_management_db

# Chemins (adaptez selon votre installation)
addons_path = ./odoo-source/addons,./custom-addons
data_dir = ./filestore
logfile = ./logs/odoo.log

# Performance
workers = 0  # 0 pour développement, 2+ pour production
limit_memory_hard = 2684354560
limit_memory_soft = 2147483648

# Logs
log_level = info  # debug en développement

# Rapports PDF
report_url = http://localhost:8069
```

### Variables d'environnement (optionnel)

```bash
# Ajouter dans ~/.bashrc ou ~/.profile
export PYTHONPATH="/chemin/vers/odoo17-internship/odoo-source"
export ODOO_RC="/chemin/vers/odoo17-internship/config/odoo.conf"
```

---

## 📦 Installation des modules

### Via l'interface web (recommandé)

1. **Se connecter** : http://localhost:8069
2. **Menu** : Applications (ou Apps)
3. **Mettre à jour** : Cliquer "Mettre à jour la liste des applications"
4. **Rechercher** : "Gestion des Stages TechPal"
5. **Installer** : Cliquer "Installer"
6. **Attendre** : 2-3 minutes pour l'installation
7. **Thème** : Répéter pour "Internship Management - Theme"

### Via ligne de commande

```bash
# Installer le module principal
python odoo-source/odoo-bin -c config/odoo.conf -d internship_management_db -i internship_management --stop-after-init

# Installer le module thème
python odoo-source/odoo-bin -c config/odoo.conf -d internship_management_db -i internship_theme --stop-after-init

# Redémarrer le serveur
python odoo-source/odoo-bin -c config/odoo.conf
```

### Vérification de l'installation

1. Aller sur : http://localhost:8069/web#action=base.open_menu
2. Rechercher "Stages" dans le menu
3. Vérifier que tous les sous-menus sont présents :
   - Gestion des Stages
   - Étudiants
   - Encadrants
   - Documents
   - Soutenances
   - Tâches


---

## 🎭 Données de démonstration

Le module inclut des données de démonstration automatiquement installées.

### Comptes de test

| Rôle | Email | Mot de passe |
|------|-------|-------------|
| Admin | admin@techpal.ma | admin |
| Coordinateur | coordinator@techpal.ma | demo |

### Données incluses

- ✅ Configurations de base (séquences, types d'activité)
- ✅ Utilisateurs et groupes de sécurité
- ✅ Templates d'email pour notifications
- ✅ Exemples de stages et étudiants
- ✅ Documents d'exemple

⚠️ **IMPORTANT** : Changer tous les mots de passe en production !

---

## 🔧 Dépannage

### Problème : Port 8069 déjà utilisé

```ini
# Solution 1 : Changer le port dans config/odoo.conf
http_port = 8070
```

```bash
# Solution 2 : Tuer le processus qui utilise le port

# Windows
netstat -ano | findstr :8069
taskkill /PID <PID> /F

# Linux/Mac
sudo lsof -i :8069
sudo kill -9 <PID>
```

### Problème : Erreur de connexion PostgreSQL

```bash
# Windows - Vérifier que PostgreSQL tourne
# Ouvrir services.msc et vérifier "postgresql-x64-16"

# Linux - Démarrer PostgreSQL
sudo systemctl status postgresql
sudo systemctl start postgresql

# Vérifier la connexion
psql -U postgres -h localhost -p 5432
```

### Problème : Module non trouvé dans la liste des applications

1. **Vérifier les chemins** dans `config/odoo.conf` :
   ```ini
   addons_path = ./odoo-source/addons,./custom-addons
   ```

2. **Vérifier les fichiers** du module :
   ```bash
   ls custom-addons/internship_management/
   # Doit contenir __manifest__.py
   ```

3. **Mettre à jour la liste** :
   - Interface web > Applications > "Mettre à jour la liste"

### Problème : Erreur wkhtmltopdf (rapports PDF)

```bash
# Windows : Vérifier PATH
# Ajouter C:\wkhtmltopdf\bin au PATH système

# Linux/Mac : Réinstaller
sudo apt install wkhtmltopdf
# ou
wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.focal_amd64.deb
sudo dpkg -i wkhtmltox_0.12.6-1.focal_amd64.deb
```

```ini
# Vérifier dans config/odoo.conf :
report_url = http://localhost:8069
```

### Problème : Erreur de permissions de fichiers

```bash
# Linux - Corriger les permissions
sudo chown -R $USER:$USER /opt/odoo17-internship/
chmod -R 755 /opt/odoo17-internship/custom-addons/
```

### Problème : Erreur Python/dépendances

```bash
# Vérifier l'environnement virtuel
which python
# Doit pointer vers odoo-venv

# Réinstaller les dépendances
pip install --upgrade pip
pip install -r odoo-source/requirements.txt
```

### Logs de débogage

```bash
# Activer les logs détaillés
# Dans config/odoo.conf :
log_level = debug

# Vérifier les logs
tail -f logs/odoo.log
```

---

## 📞 Support

En cas de problème persistant :

- 📧 **Email** : support@techpal.ma
- 📚 **Documentation** : [docs/](../docs/)
- 🐛 **Issues GitHub** : [Signaler un bug](../../issues)
- 💬 **Communauté** : [Discussions](../../discussions)

---

## ✅ Installation réussie !

🎉 **Félicitations !** Votre environnement est maintenant prêt.

### Prochaines étapes recommandées :

1. 📖 **Consulter le guide utilisateur** : Formation sur l'utilisation du système
2. 🎨 **Personnaliser** : Configurer les paramètres selon vos besoins
3. 👥 **Créer des utilisateurs** : Ajouter les premiers coordinateurs et encadrants
4. 📊 **Configurer les données** : Paramétrer les domaines et compétences d'études

---

**Développé avec ❤️ pour TechPal Casablanca**