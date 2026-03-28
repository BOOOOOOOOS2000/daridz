#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Styles de l'interface ZKTeco Manager
Thème moderne et professionnel
"""

# Style principal de l'application
MAIN_STYLE = """
/* Variables de couleur */
QWidget {
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 9pt;
}

/* QMainWindow */
QMainWindow {
    background-color: #f5f5f5;
}

/* QMenuBar */
QMenuBar {
    background-color: #2c3e50;
    color: white;
    padding: 4px;
    spacing: 4px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 6px 12px;
    border-radius: 4px;
}

QMenuBar::item:selected {
    background-color: #34495e;
}

QMenuBar::item:pressed {
    background-color: #1abc9c;
}

/* QMenu */
QMenu {
    background-color: white;
    border: 1px solid #ddd;
    padding: 4px;
}

QMenu::item {
    padding: 6px 30px 6px 20px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #3498db;
    color: white;
}

QMenu::separator {
    height: 1px;
    background-color: #ddd;
    margin: 4px 10px;
}

/* QToolBar */
QToolBar {
    background-color: #34495e;
    border: none;
    spacing: 6px;
    padding: 4px;
}

QToolBar::separator {
    width: 1px;
    background-color: #4a6278;
    margin: 4px 8px;
}

/* QToolButton (boutons de la barre d'outils) */
QToolButton {
    background-color: transparent;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 12px;
    min-width: 60px;
}

QToolButton:hover {
    background-color: #4a6278;
}

QToolButton:pressed {
    background-color: #1abc9c;
}

QToolButton::menu-indicator {
    image: none;
}

/* QPushButton */
QPushButton {
    background-color: #3498db;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    min-width: 80px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #2980b9;
}

QPushButton:pressed {
    background-color: #21618c;
}

QPushButton:disabled {
    background-color: #bdc3c7;
}

/* Bouton de succès */
QPushButton[buttonType="success"] {
    background-color: #27ae60;
}

QPushButton[buttonType="success"]:hover {
    background-color: #219a52;
}

/* Bouton de danger */
QPushButton[buttonType="danger"] {
    background-color: #e74c3c;
}

QPushButton[buttonType="danger"]:hover {
    background-color: #c0392b;
}

/* Bouton d'avertissement */
QPushButton[buttonType="warning"] {
    background-color: #f39c12;
}

QPushButton[buttonType="warning"]:hover {
    background-color: #d68910;
}

/* QLineEdit */
QLineEdit {
    background-color: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 6px 10px;
    min-height: 20px;
}

QLineEdit:focus {
    border-color: #3498db;
}

QLineEdit:disabled {
    background-color: #f5f5f5;
}

/* QTextEdit */
QTextEdit {
    background-color: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 6px;
}

QTextEdit:focus {
    border-color: #3498db;
}

/* QComboBox */
QComboBox {
    background-color: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 6px 10px;
    min-height: 20px;
}

QComboBox:focus {
    border-color: #3498db;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #666;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: white;
    border: 1px solid #ddd;
    selection-background-color: #3498db;
    selection-color: white;
}

/* QSpinBox */
QSpinBox {
    background-color: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 6px 10px;
}

QSpinBox:focus {
    border-color: #3498db;
}

/* QCheckBox */
QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #ddd;
    border-radius: 3px;
}

QCheckBox::indicator:checked {
    background-color: #3498db;
    border-color: #3498db;
    image: none;
}

QCheckBox::indicator:checked:after {
    content: "✓";
}

/* QRadioButton */
QRadioButton {
    spacing: 8px;
}

QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #ddd;
    border-radius: 9px;
}

QRadioButton::indicator:checked {
    background-color: #3498db;
    border-color: #3498db;
}

/* QTableWidget */
QTableWidget {
    background-color: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    gridline-color: #eee;
    selection-background-color: #3498db;
    selection-color: white;
}

QTableWidget::item {
    padding: 6px;
}

QTableWidget::item:selected {
    background-color: #3498db;
    color: white;
}

QHeaderView::section {
    background-color: #34495e;
    color: white;
    padding: 8px;
    border: none;
    font-weight: bold;
}

QHeaderView::section:hover {
    background-color: #4a6278;
}

/* QTreeWidget */
QTreeWidget {
    background-color: white;
    border: 1px solid #ddd;
    border-radius: 4px;
}

QTreeWidget::item {
    padding: 4px;
}

QTreeWidget::item:selected {
    background-color: #3498db;
    color: white;
}

/* QTabWidget */
QTabWidget::pane {
    border: 1px solid #ddd;
    border-radius: 4px;
    background-color: white;
}

QTabBar::tab {
    background-color: #ecf0f1;
    padding: 8px 16px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: white;
    border-bottom: 2px solid #3498db;
}

QTabBar::tab:hover:!selected {
    background-color: #d5dbdb;
}

/* QGroupBox */
QGroupBox {
    font-weight: bold;
    border: 1px solid #ddd;
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 12px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 5px;
    background-color: #f5f5f5;
}

/* QProgressBar */
QProgressBar {
    background-color: #ecf0f1;
    border: none;
    border-radius: 4px;
    text-align: center;
    min-height: 20px;
}

QProgressBar::chunk {
    background-color: #3498db;
    border-radius: 4px;
}

/* QScrollBar */
QScrollBar:vertical {
    background-color: #f5f5f5;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #bdc3c7;
    border-radius: 6px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #95a5a6;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* QSplitter */
QSplitter::handle {
    background-color: #ddd;
}

/* QStatusBar */
QStatusBar {
    background-color: #2c3e50;
    color: white;
}

QStatusBar::item {
    border: none;
}

/* QDockWidget */
QDockWidget {
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}

QDockWidget::title {
    background-color: #34495e;
    color: white;
    padding: 8px;
}

/* QLabel spécial */
QLabel[labelType="title"] {
    font-size: 14pt;
    font-weight: bold;
    color: #2c3e50;
}

QLabel[labelType="subtitle"] {
    font-size: 11pt;
    color: #7f8c8d;
}

QLabel[labelType="status"] {
    padding: 4px 8px;
    border-radius: 4px;
}

QLabel[statusType="success"] {
    background-color: #d4edda;
    color: #155724;
}

QLabel[statusType="danger"] {
    background-color: #f8d7da;
    color: #721c24;
}

QLabel[statusType="warning"] {
    background-color: #fff3cd;
    color: #856404;
}

QLabel[statusType="info"] {
    background-color: #d1ecf1;
    color: #0c5460;
}

/* QFrame pour séparation */
QFrame[frameType="separator"] {
    background-color: #ddd;
}

/* QListWidget */
QListWidget {
    background-color: white;
    border: 1px solid #ddd;
    border-radius: 4px;
}

QListWidget::item {
    padding: 6px;
}

QListWidget::item:selected {
    background-color: #3498db;
    color: white;
}

/* QDateEdit */
QDateEdit {
    background-color: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 6px 10px;
}

QDateEdit:focus {
    border-color: #3498db;
}

/* QTimeEdit */
QTimeEdit {
    background-color: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 6px 10px;
}

/* QMessageBox */
QMessageBox {
    background-color: white;
}

QMessageBox QLabel {
    font-size: 10pt;
}

/* QFileDialog */
QFileDialog {
    background-color: white;
}

/* QTooltip */
QToolTip {
    background-color: #2c3e50;
    color: white;
    border: none;
    padding: 6px;
    border-radius: 4px;
}
"""

# Style pour le widget de statut de connexion
CONNECTION_STATUS_STYLE = """
QFrame {
    background-color: white;
    border-radius: 8px;
    padding: 10px;
}

QLabel {
    font-size: 10pt;
}

QPushButton {
    min-width: 100px;
}
"""

# Style pour les cartes d'information
CARD_STYLE = """
QFrame {
    background-color: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 15px;
}

QLabel[labelType="cardTitle"] {
    font-size: 12pt;
    font-weight: bold;
    color: #2c3e50;
}

QLabel[labelType="cardValue"] {
    font-size: 24pt;
    font-weight: bold;
    color: #3498db;
}

QLabel[labelType="cardSubtitle"] {
    font-size: 9pt;
    color: #7f8c8d;
}
"""

# Style pour le panneau latéral
SIDEBAR_STYLE = """
QFrame {
    background-color: #2c3e50;
    border: none;
}

QPushButton {
    background-color: transparent;
    color: white;
    text-align: left;
    padding: 12px 16px;
    border: none;
    border-radius: 0px;
}

QPushButton:hover {
    background-color: #34495e;
}

QPushButton:checked {
    background-color: #1abc9c;
    border-left: 3px solid #16a085;
}
"""

# Couleurs utilitaires
COLORS = {
    'primary': '#3498db',
    'primary_dark': '#2980b9',
    'success': '#27ae60',
    'success_dark': '#219a52',
    'danger': '#e74c3c',
    'danger_dark': '#c0392b',
    'warning': '#f39c12',
    'warning_dark': '#d68910',
    'info': '#17a2b8',
    'info_dark': '#138496',
    'dark': '#2c3e50',
    'dark_light': '#34495e',
    'light': '#ecf0f1',
    'white': '#ffffff',
    'gray': '#95a5a6',
    'gray_light': '#bdc3c7',
}
