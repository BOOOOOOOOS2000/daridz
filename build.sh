#!/bin/bash
# Script de build pour Restaurant App React Native

set -e

echo "========================================="
echo "Restaurant App - Build Script"
echo "========================================="

# Nettoyer le build précédent
cd android
./gradlew clean

# Construire l'APK debug
./gradlew assembleDebug

echo ""
echo "========================================="
if [ -f "app/build/outputs/apk/debug/app-debug.apk" ]; then
    echo "✅ BUILD SUCCESSFUL!"
    echo "APK generated at: android/app/build/outputs/apk/debug/app-debug.apk"
else
    echo "❌ BUILD FAILED"
    echo "Check the error messages above"
fi
echo "========================================="