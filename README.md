# Restaurant App - React Native

Application de prise de commandes pour restaurants, développée en React Native.

## 🍽️ Fonctionnalités

- **Gestion des tables** : 27 tables avec statuts (libre, occupée, commande envoyée)
- **Menu complet** : 7 catégories (Viande, Pizza, Burger, Entrées chaudes, Entrées froides, Plats enfants, Plats du jour)
- **Prise de commande** : Sélection d'articles, quantités, notes personnalisées
- **Panier** : Modification avant validation
- **Suivi des commandes** : Statuts en temps réel
- **Administration** : Gestion des plats du jour (protégé par mot de passe)
- **Mode hors ligne** : Base de données SQLite locale

## 🏗️ Architecture

```
src/
├── components/       # Composants réutilisables
├── context/          # Context API pour le state management
├── database/         # Configuration SQLite
├── navigation/       # Navigation entre écrans
├── screens/          # Écrans principaux
└── utils/            # Utilitaires
```

## 🚀 Installation

```bash
# Installer les dépendances
npm install

# Lancer le serveur Metro
npm start

# Construire et lancer sur Android
npm run android
```

## 🔧 Configuration

### Mot de passe administrateur
Le mot de passe par défaut est : `admin123`

### Base de données
L'application utilise SQLite pour stocker :
- Tables du restaurant
- Catégories et articles du menu
- Commandes en cours
- Plats du jour

## 📱 Écrans

1. **Tables** - Grille des 27 tables avec codes couleurs
2. **Menu** - Catégories et articles
3. **Commandes** - Liste des commandes actives
4. **Admin** - Gestion des plats du jour

## 🛠️ Technologies

- React Native 0.72
- SQLite (react-native-sqlite-storage)
- React Navigation 6
- Context API

## 📄 Licence

MIT