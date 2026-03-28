#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de compilation pour ZKTeco iClock Manager
Génère un fichier exécutable (.exe) pour Windows
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def clean_build():
    """Nettoyer les dossiers de build"""
    folders = ['build', 'dist', '__pycache__']
    
    for folder in folders:
        if os.path.exists(folder):
            print(f"Suppression de {folder}...")
            shutil.rmtree(folder, ignore_errors=True)
    
    # Supprimer les fichiers .spec
    for spec_file in Path('.').glob('*.spec'):
        print(f"Suppression de {spec_file}...")
        spec_file.unlink()


def install_dependencies():
    """Installer les dépendances"""
    print("\nInstallation des dépendances...")
    
    subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], check=True)
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)


def build_exe():
    """Compiler l'exécutable"""
    print("\nCompilation de l'application...")
    
    # Options PyInstaller
    options = [
        '--name=ZKTecoManager',
        '--onefile',  # Un seul fichier
        '--windowed',  # Pas de console
        '--clean',
        '--noconfirm',
        
        # Modules cachés
        '--hidden-import=PyQt5',
        '--hidden-import=PyQt5.QtCore',
        '--hidden-import=PyQt5.QtGui',
        '--hidden-import=PyQt5.QtWidgets',
        '--hidden-import=sqlite3',
        '--hidden-import=pandas',
        '--hidden-import=openpyxl',
        '--hidden-import=openpyxl.styles',
        '--hidden-import=reportlab',
        '--hidden-import=reportlab.lib',
        '--hidden-import=reportlab.platypus',
        
        # Exclusions
        '--exclude-module=tkinter',
        '--exclude-module=matplotlib',
        '--exclude-module=IPython',
        '--exclude-module=jupyter',
        
        # Fichier principal
        'main.py'
    ]
    
    # Icône si disponible
    if os.path.exists('resources/icon.ico'):
        options.append('--icon=resources/icon.ico')
    
    # Exécuter PyInstaller
    cmd = [sys.executable, '-m', 'PyInstaller'] + options
    subprocess.run(cmd, check=True)


def create_distribution():
    """Créer la distribution"""
    print("\nCréation de la distribution...")
    
    dist_dir = Path('dist')
    
    if not dist_dir.exists():
        print("ERREUR: Le dossier dist n'existe pas")
        return False
    
    # Créer les sous-dossiers
    (dist_dir / 'data').mkdir(exist_ok=True)
    (dist_dir / 'exports').mkdir(exist_ok=True)
    
    # Créer un fichier README
    readme_content = """# ZKTeco iClock Manager

Application de gestion pour pointeuse biométrique ZKTeco iClock 580.

## Installation

1. Double-cliquez sur ZKTecoManager.exe pour lancer l'application
2. Configurez l'adresse IP de votre pointeuse dans Paramètres
3. Connectez-vous à la pointeuse

## Configuration par défaut

- IP: 192.168.1.201
- Port: 4370

## Support

Pour toute question, consultez la documentation ou contactez le support.

Version: 1.0.0
"""
    
    with open(dist_dir / 'README.txt', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"\nDistribution créée dans: {dist_dir.absolute()}")
    
    return True


def main():
    """Fonction principale"""
    print("=" * 60)
    print("  ZKTeco iClock Manager - Script de compilation")
    print("=" * 60)
    
    # Vérifier que nous sommes dans le bon dossier
    if not os.path.exists('main.py'):
        print("ERREUR: main.py non trouvé. Exécutez ce script depuis le dossier du projet.")
        return 1
    
    # Nettoyer
    clean_build()
    
    # Installer les dépendances
    try:
        install_dependencies()
    except subprocess.CalledProcessError as e:
        print(f"ERREUR lors de l'installation des dépendances: {e}")
        return 1
    
    # Compiler
    try:
        build_exe()
    except subprocess.CalledProcessError as e:
        print(f"ERREUR lors de la compilation: {e}")
        return 1
    
    # Créer la distribution
    if not create_distribution():
        return 1
    
    print("\n" + "=" * 60)
    print("  COMPILATION TERMINÉE AVEC SUCCÈS!")
    print("  L'exécutable se trouve dans le dossier 'dist'")
    print("=" * 60)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
