# Restaurant App - Guide d'Installation et de Build

## 📋 Prérequis

- Node.js >= 16
- npm ou yarn
- Android SDK (API 34)
- JDK 17+
- Gradle 8.0+

## 🚀 Installation

### 1. Installer les dépendances

```bash
cd RestaurantAppRN
npm install --legacy-peer-deps
```

### 2. Configurer Android SDK

Assurez-vous que les variables d'environnement suivantes sont définies :

```bash
export ANDROID_HOME=/root/Android
export PATH=$PATH:$ANDROID_HOME/platform-tools
export PATH=$PATH:$ANDROID_HOME/build-tools/34.0.0
```

### 3. Construire l'APK

```bash
# Méthode 1: Utiliser le script de build
./build.sh

# Méthode 2: Manuellement
cd android
./gradlew clean
./gradlew assembleDebug
```

L'APK sera généré à : `android/app/build/outputs/apk/debug/app-debug.apk`

### 4. Installer sur un appareil/émulateur

```bash
# Sur un émulateur ou appareil connecté
npm run android

# Ou manuellement
adb install android/app/build/outputs/apk/debug/app-debug.apk
```

## 🗄️ Base de données

L'application utilise SQLite avec les données suivantes pré-remplies :

- **27 tables** (toutes libres au démarrage)
- **7 catégories** de menu
- **42 articles** (6 par catégorie)
- **4 plats du jour** par défaut

### Mot de passe administrateur
`admin123`

## 📱 Fonctionnalités

1. **Écran Tables** : Grille des 27 tables avec codes couleurs
   - Vert : Libre
   - Orange : Occupée
   - Bleu : Commande envoyée

2. **Écran Menu** : Prise de commande
   - 7 catégories
   - Quantités modifiables
   - Notes personnalisées
   - Panier avec total

3. **Écran Commandes** : Suivi des commandes actives
   - Statuts : En attente → En préparation → Prête → Servie
   - Détail des articles par commande

4. **Écran Admin** : Gestion des plats du jour
   - Ajout/suppression de plats
   - Protégé par mot de passe

## 🔧 Dépannage

### Erreur de build
```bash
cd android
./gradlew clean
cd ..
npm install --legacy-peer-deps
```

### Erreur Metro Bundler
```bash
npm start -- --reset-cache
```

### Problème avec aapt2 (ARM64)
Si vous rencontrez des erreurs aapt2 sur ARM64, utilisez le script `build-android.sh` à la racine qui gère la compatibilité avec box64.

## 📄 Licence

MIT