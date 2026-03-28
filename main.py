#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZKTeco iClock 580 Manager
Application de gestion complète pour pointeuse ZKTeco
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt, QTranslator, QLocale
from PyQt5.QtGui import QIcon, QFont

# Ajouter le répertoire courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow
from database.db_manager import DatabaseManager


def check_dependencies():
    """Vérifier que toutes les dépendances sont installées"""
    missing = []
    
    try:
        import PyQt5
    except ImportError:
        missing.append("PyQt5")
    
    try:
        import pandas
    except ImportError:
        missing.append("pandas")
    
    try:
        import openpyxl
    except ImportError:
        missing.append("openpyxl")
    
    try:
        from reportlab.lib import colors
    except ImportError:
        missing.append("reportlab")
    
    if missing:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Dépendances manquantes")
        msg.setText(f"Les packages suivants sont manquants:\n\n{chr(10).join(missing)}\n\nInstallez-les avec:\npip install {' '.join(missing)}")
        msg.exec_()
        return False
    
    return True


def main():
    """Fonction principale de l'application"""
    # Vérifier les dépendances
    if not check_dependencies():
        sys.exit(1)
    
    # Activer le support haute résolution
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Créer l'application
    app = QApplication(sys.argv)
    app.setApplicationName("ZKTeco iClock Manager")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("ZKTeco Manager")
    
    # Définir le style
    app.setStyle('Fusion')
    
    # Définir la police par défaut
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    # Initialiser la base de données
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "zkteco.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    db_manager = DatabaseManager(db_path)
    
    # Créer et afficher la fenêtre principale
    window = MainWindow(db_manager)
    window.show()
    
    # Exécuter l'application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
