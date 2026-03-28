# ZKTeco iClock 580 Manager

Application de gestion complète pour pointeuse biométrique ZKTeco iClock 580.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## 📋 Fonctionnalités

### Gestion des utilisateurs
- ✅ Ajouter, modifier, supprimer des utilisateurs
- ✅ Gestion des privilèges (Utilisateur, Enregistreur, Gestionnaire, Super Admin)
- ✅ Assignation aux départements
- ✅ Gestion des cartes de proximité
- ✅ Synchronisation avec la pointeuse

### Gestion des empreintes digitales
- ✅ Visualisation des empreintes enregistrées
- ✅ Récupération depuis le périphérique
- ✅ Suppression d'empreintes

### Gestion des pointages
- ✅ Téléchargement des pointages depuis la pointeuse
- ✅ Filtrage par date, utilisateur, département
- ✅ Affichage des types de vérification
- ✅ Calcul automatique des heures travaillées

### Rapports et statistiques
- ✅ Rapport de présence journalière
- ✅ Rapport de présence mensuelle
- ✅ Rapport des retards et absences
- ✅ Rapport des heures travaillées
- ✅ Statistiques globales

### Export
- ✅ Export Excel (.xlsx)
- ✅ Export PDF
- ✅ Export CSV

### Configuration
- ✅ Gestion des départements
- ✅ Gestion des horaires de travail
- ✅ Gestion des jours fériés
- ✅ Paramètres de connexion
- ✅ Synchronisation automatique

## 🔧 Installation

### Prérequis
- Python 3.8 ou supérieur
- Windows 7/8/10/11

### Installation depuis les sources

```bash
# Cloner ou extraire le projet
cd zkteco-iclock-manager

# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
python main.py
```

### Création de l'exécutable (.exe)

```bash
# Exécuter le script de compilation
python build_exe.py

# Ou sous Windows:
build.bat
```

L'exécutable sera créé dans le dossier `dist/`.

## ⚙️ Configuration

### Connexion à la pointeuse

Par défaut, l'application est configurée pour :
- **IP**: 192.168.1.201
- **Port**: 4370

Pour modifier ces paramètres :
1. Aller dans **Paramètres**
2. Modifier l'adresse IP et le port
3. Cliquer sur **Enregistrer**

### Structure de la base de données

L'application utilise SQLite avec les tables suivantes :
- `users` - Utilisateurs
- `fingerprints` - Empreintes digitales
- `attendance` - Pointages
- `departments` - Départements
- `schedules` - Horaires
- `holidays` - Jours fériés
- `settings` - Paramètres
- `logs` - Journal des événements

## 📖 Guide d'utilisation

### Première utilisation

1. **Configurer la connexion**
   - Aller dans Paramètres
   - Vérifier l'adresse IP de la pointeuse
   - Cliquer sur "Connecter" dans le panneau latéral

2. **Synchroniser les utilisateurs**
   - Aller dans Utilisateurs
   - Cliquer sur "Synchroniser depuis le périphérique"

3. **Télécharger les pointages**
   - Aller dans Pointages
   - Cliquer sur "Télécharger depuis le périphérique"

### Gestion quotidienne

1. **Connecter la pointeuse** au démarrage
2. **Télécharger les pointages** du jour
3. **Consulter les rapports** pour vérifier les présences

### Export des données

1. **Exporter les pointages**
   - Aller dans Pointages
   - Définir la période
   - Cliquer sur "Exporter Excel"

2. **Générer un rapport**
   - Aller dans Rapports
   - Sélectionner le type de rapport
   - Exporter en Excel ou PDF

## 🔐 Sécurité

- Les mots de passe sont stockés de manière sécurisée
- La base de données est locale et chiffrée
- Les connexions réseau sont sécurisées

## 📁 Structure du projet

```
zkteco-iclock-manager/
├── main.py                 # Point d'entrée
├── requirements.txt        # Dépendances Python
├── build_exe.py           # Script de compilation
├── build.bat              # Script Windows
├── zkteco_manager.spec    # Configuration PyInstaller
├── database/
│   ├── __init__.py
│   └── db_manager.py      # Gestionnaire SQLite
├── zk/
│   ├── __init__.py
│   ├── zk_device.py       # Communication pointeuse
│   └── zk_protocol.py     # Protocole ZK
├── ui/
│   ├── __init__.py
│   ├── main_window.py     # Fenêtre principale
│   ├── dialogs.py         # Dialogues
│   └── styles.py          # Styles Qt
├── utils/
│   ├── __init__.py
│   ├── export.py          # Export Excel/PDF
│   └── helpers.py         # Fonctions utilitaires
└── resources/
    └── icon.ico           # Icône de l'application
```

## 🛠️ Dépannage

### La connexion échoue

1. Vérifier que la pointeuse est allumée
2. Vérifier l'adresse IP dans les paramètres
3. Vérifier que le port 4370 est ouvert
4. Essayer de pinger la pointeuse : `ping 192.168.1.201`

### Les pointages ne se téléchargent pas

1. Vérifier la connexion
2. Essayer de se reconnecter
3. Vérifier les logs dans la base de données

### L'application ne démarre pas

1. Vérifier que Python 3.8+ est installé
2. Réinstaller les dépendances : `pip install -r requirements.txt`
3. Vérifier les logs d'erreur

## 📞 Support

Pour toute question ou problème :
1. Consulter ce README
2. Vérifier les logs de l'application
3. Contacter le support technique

## 📜 Licence

Ce projet est sous licence MIT.

---

**Version**: 1.0.0
**Auteur**: ZKTeco Manager Team
**Dernière mise à jour**: 2024
