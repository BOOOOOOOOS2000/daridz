#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fenêtre principale de ZKTeco iClock Manager
Interface graphique complète avec toutes les fonctionnalités
"""

import sys
import os
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QTableWidget, QTableWidgetItem,
    QComboBox, QTabWidget, QGroupBox, QSplitter, QFrame, QStatusBar,
    QToolBar, QAction, QMenuBar, QMenu, QMessageBox, QProgressBar,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QAbstractItemView,
    QDateEdit, QTimeEdit, QCheckBox, QSpinBox, QDialog, QDialogButtonBox,
    QFormLayout, QTextEdit, QFileDialog, QApplication, QStyle
)
from PyQt5.QtCore import (
    Qt, QTimer, QDate, QTime, QDateTime, QThread, pyqtSignal, QSize
)
from PyQt5.QtGui import QIcon, QFont, QColor, QBrush, QPalette, QPixmap

from .styles import MAIN_STYLE, COLORS
from ..zk.zk_device import ZKDevice, test_connection
from ..zk.zk_protocol import VERIFY_TYPE_NAMES, STATUS_NAMES, PRIVILEGE_NAMES


class ConnectionThread(QThread):
    """Thread pour la connexion au périphérique"""
    finished = pyqtSignal(bool, str)
    
    def __init__(self, device: ZKDevice):
        super().__init__()
        self.device = device
    
    def run(self):
        try:
            if self.device.connect():
                self.finished.emit(True, "Connecté avec succès")
            else:
                self.finished.emit(False, "Échec de la connexion")
        except Exception as e:
            self.finished.emit(False, str(e))


class SyncThread(QThread):
    """Thread pour la synchronisation des données"""
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(bool, str, int)
    
    def __init__(self, device: ZKDevice, db_manager, sync_type: str):
        super().__init__()
        self.device = device
        self.db_manager = db_manager
        self.sync_type = sync_type
    
    def run(self):
        try:
            if self.sync_type == 'attendance':
                self.progress.emit(0, 100, "Récupération des pointages...")
                count = self.device.sync_attendance_from_device(self.db_manager)
                self.finished.emit(True, f"{count} pointages synchronisés", count)
            elif self.sync_type == 'users':
                self.progress.emit(0, 100, "Récupération des utilisateurs...")
                count = self.device.sync_users_from_device(self.db_manager)
                self.finished.emit(True, f"{count} utilisateurs synchronisés", count)
        except Exception as e:
            self.finished.emit(False, str(e), 0)


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application"""
    
    def __init__(self, db_manager):
        super().__init__()
        
        self.db = db_manager
        self.device: Optional[ZKDevice] = None
        self.connected = False
        
        # Configuration initiale
        self.load_settings()
        
        # Configuration de la fenêtre
        self.setup_ui()
        self.setup_menus()
        self.setup_toolbar()
        self.setup_statusbar()
        
        # Timer pour l'auto-sync
        self.auto_sync_timer = QTimer()
        self.auto_sync_timer.timeout.connect(self.auto_sync)
        
        # Charger les données initiales
        self.refresh_dashboard()
        
        # Appliquer le style
        self.setStyleSheet(MAIN_STYLE)
    
    def load_settings(self):
        """Charger les paramètres depuis la base de données"""
        self.settings = self.db.get_all_settings()
        self.device_ip = self.settings.get('device_ip', '192.168.1.201')
        self.device_port = int(self.settings.get('device_port', 4370))
    
    def setup_ui(self):
        """Configurer l'interface utilisateur"""
        # Configuration de la fenêtre
        self.setWindowTitle(f"ZKTeco iClock Manager - {self.settings.get('company_name', 'Ma Société')}")
        self.setMinimumSize(1200, 800)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Panneau latéral
        self.setup_sidebar(main_layout)
        
        # Zone principale avec onglets
        self.setup_main_area(main_layout)
    
    def setup_sidebar(self, parent_layout):
        """Configurer le panneau latéral"""
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border: none;
            }
            QPushButton {
                background-color: transparent;
                color: white;
                text-align: left;
                padding: 15px 20px;
                border: none;
                border-radius: 0px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton:checked {
                background-color: #1abc9c;
                border-left: 4px solid #16a085;
            }
            QLabel {
                color: white;
                padding: 15px 20px 10px 20px;
                font-size: 11pt;
                font-weight: bold;
            }
        """)
        
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # Titre
        title_label = QLabel("🖥️ ZKTeco Manager")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 14pt; padding: 20px;")
        sidebar_layout.addWidget(title_label)
        
        # Séparateur
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #34495e; max-height: 1px;")
        sidebar_layout.addWidget(separator)
        
        # Boutons de navigation
        self.nav_buttons = []
        
        nav_items = [
            ("📊 Tableau de bord", self.show_dashboard),
            ("👥 Utilisateurs", self.show_users),
            ("👆 Empreintes", self.show_fingerprints),
            ("📋 Pointages", self.show_attendance),
            ("📈 Rapports", self.show_reports),
            ("🏢 Départements", self.show_departments),
            ("⏰ Horaires", self.show_schedules),
            ("📅 Jours fériés", self.show_holidays),
            ("⚙️ Paramètres", self.show_settings),
        ]
        
        for text, callback in nav_items:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.clicked.connect(callback)
            btn.clicked.connect(lambda checked, b=btn: self.set_active_nav(b))
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)
        
        # Sélectionner le premier par défaut
        self.nav_buttons[0].setChecked(True)
        
        # Espaceur
        sidebar_layout.addStretch()
        
        # Section de connexion
        self.setup_connection_section(sidebar_layout)
        
        parent_layout.addWidget(sidebar)
    
    def setup_connection_section(self, sidebar_layout):
        """Configurer la section de connexion"""
        conn_frame = QFrame()
        conn_frame.setStyleSheet("""
            QFrame {
                background-color: #34495e;
                border-radius: 8px;
                margin: 10px;
                padding: 10px;
            }
            QLabel { padding: 5px; }
        """)
        
        conn_layout = QVBoxLayout(conn_frame)
        
        # Titre
        conn_title = QLabel("📡 Connexion")
        conn_title.setStyleSheet("font-weight: bold;")
        conn_layout.addWidget(conn_title)
        
        # IP
        ip_label = QLabel(f"IP: {self.device_ip}")
        ip_label.setObjectName("conn_ip_label")
        conn_layout.addWidget(ip_label)
        
        # Status
        self.conn_status = QLabel("● Déconnecté")
        self.conn_status.setStyleSheet("color: #e74c3c;")
        conn_layout.addWidget(self.conn_status)
        
        # Bouton de connexion
        self.conn_button = QPushButton("🔗 Connecter")
        self.conn_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                padding: 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.conn_button.clicked.connect(self.toggle_connection)
        conn_layout.addWidget(self.conn_button)
        
        sidebar_layout.addWidget(conn_frame)
    
    def setup_main_area(self, parent_layout):
        """Configurer la zone principale"""
        # Container principal
        main_container = QFrame()
        main_container.setStyleSheet("background-color: #f5f5f5;")
        
        layout = QVBoxLayout(main_container)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Stack de pages
        self.pages = {}
        
        # Créer les pages
        self.create_dashboard_page()
        self.create_users_page()
        self.create_fingerprints_page()
        self.create_attendance_page()
        self.create_reports_page()
        self.create_departments_page()
        self.create_schedules_page()
        self.create_holidays_page()
        self.create_settings_page()
        
        # Stack widget
        self.stack = QFrame()
        self.stack_layout = QVBoxLayout(self.stack)
        self.stack_layout.setContentsMargins(0, 0, 0, 0)
        
        for name, page in self.pages.items():
            page.setParent(self.stack)
            self.stack_layout.addWidget(page)
            page.hide()
        
        layout.addWidget(self.stack)
        
        # Afficher le dashboard par défaut
        self.show_dashboard()
        
        parent_layout.addWidget(main_container)
    
    def create_dashboard_page(self):
        """Créer la page du tableau de bord"""
        page = QFrame()
        layout = QVBoxLayout(page)
        
        # Titre
        title = QLabel("📊 Tableau de bord")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #2c3e50; padding: 10px 0;")
        layout.addWidget(title)
        
        # Cartes de statistiques
        stats_layout = QHBoxLayout()
        
        # Carte utilisateurs
        self.card_users = self.create_stat_card("👥 Utilisateurs", "0", "Utilisateurs enregistrés")
        stats_layout.addWidget(self.card_users)
        
        # Carte pointages aujourd'hui
        self.card_today = self.create_stat_card("📋 Pointages aujourd'hui", "0", "Entrées/sorties")
        stats_layout.addWidget(self.card_today)
        
        # Carte départements
        self.card_depts = self.create_stat_card("🏢 Départements", "0", "Départements actifs")
        stats_layout.addWidget(self.card_depts)
        
        # Carte synchronisation
        self.card_sync = self.create_stat_card("🔄 Dernière sync", "Jamais", "Dernière synchronisation")
        stats_layout.addWidget(self.card_sync)
        
        layout.addLayout(stats_layout)
        
        # Section des actions rapides
        actions_group = QGroupBox("Actions rapides")
        actions_layout = QHBoxLayout(actions_group)
        
        # Boutons d'action
        btn_sync_users = QPushButton("📥 Synchroniser utilisateurs")
        btn_sync_users.setStyleSheet("background-color: #27ae60;")
        btn_sync_users.clicked.connect(lambda: self.sync_data('users'))
        actions_layout.addWidget(btn_sync_users)
        
        btn_sync_attendance = QPushButton("📥 Synchroniser pointages")
        btn_sync_attendance.setStyleSheet("background-color: #3498db;")
        btn_sync_attendance.clicked.connect(lambda: self.sync_data('attendance'))
        actions_layout.addWidget(btn_sync_attendance)
        
        btn_export = QPushButton("📤 Exporter données")
        btn_export.setStyleSheet("background-color: #9b59b6;")
        btn_export.clicked.connect(self.export_data)
        actions_layout.addWidget(btn_export)
        
        btn_test = QPushButton("🔔 Tester connexion")
        btn_test.setStyleSheet("background-color: #f39c12;")
        btn_test.clicked.connect(self.test_device_connection)
        actions_layout.addWidget(btn_test)
        
        layout.addWidget(actions_group)
        
        # Tableaux récents
        tables_layout = QHBoxLayout()
        
        # Derniers pointages
        recent_group = QGroupBox("Derniers pointages")
        recent_layout = QVBoxLayout(recent_group)
        
        self.recent_table = QTableWidget()
        self.recent_table.setColumnCount(4)
        self.recent_table.setHorizontalHeaderLabels(["Employé", "Date/Heure", "Type", "Status"])
        self.recent_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.recent_table.setMaximumHeight(200)
        recent_layout.addWidget(self.recent_table)
        
        tables_layout.addWidget(recent_group)
        
        # Alertes
        alerts_group = QGroupBox("Alertes & Notifications")
        alerts_layout = QVBoxLayout(alerts_group)
        
        self.alerts_list = QTextEdit()
        self.alerts_list.setReadOnly(True)
        self.alerts_list.setMaximumHeight(200)
        self.alerts_list.setStyleSheet("background-color: white;")
        alerts_layout.addWidget(self.alerts_list)
        
        tables_layout.addWidget(alerts_group)
        
        layout.addLayout(tables_layout)
        
        layout.addStretch()
        
        self.pages['dashboard'] = page
    
    def create_stat_card(self, title: str, value: str, subtitle: str) -> QFrame:
        """Créer une carte de statistique"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(card)
        
        # Titre
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 10pt; color: #7f8c8d;")
        layout.addWidget(title_label)
        
        # Valeur
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 24pt; font-weight: bold; color: #2c3e50;")
        value_label.setObjectName("stat_value")
        layout.addWidget(value_label)
        
        # Sous-titre
        sub_label = QLabel(subtitle)
        sub_label.setStyleSheet("font-size: 9pt; color: #bdc3c7;")
        layout.addWidget(sub_label)
        
        return card
    
    def create_users_page(self):
        """Créer la page de gestion des utilisateurs"""
        page = QFrame()
        layout = QVBoxLayout(page)
        
        # Titre et barre d'outils
        header_layout = QHBoxLayout()
        
        title = QLabel("👥 Gestion des utilisateurs")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Recherche
        search_label = QLabel("Rechercher:")
        header_layout.addWidget(search_label)
        
        self.users_search = QLineEdit()
        self.users_search.setPlaceholderText("Nom, ID ou carte...")
        self.users_search.setMaximumWidth(200)
        self.users_search.textChanged.connect(self.filter_users)
        header_layout.addWidget(self.users_search)
        
        # Filtre département
        dept_label = QLabel("Département:")
        header_layout.addWidget(dept_label)
        
        self.users_dept_filter = QComboBox()
        self.users_dept_filter.addItem("Tous", None)
        self.users_dept_filter.setMaximumWidth(150)
        self.users_dept_filter.currentIndexChanged.connect(self.filter_users)
        header_layout.addWidget(self.users_dept_filter)
        
        layout.addLayout(header_layout)
        
        # Table des utilisateurs
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(8)
        self.users_table.setHorizontalHeaderLabels([
            "ID", "UID", "Nom", "Privilège", "Département", "Carte", "Empreintes", "Actif"
        ])
        self.users_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.users_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.users_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.users_table.doubleClicked.connect(self.edit_user)
        
        layout.addWidget(self.users_table)
        
        # Boutons d'action
        buttons_layout = QHBoxLayout()
        
        btn_add = QPushButton("➕ Ajouter")
        btn_add.setStyleSheet("background-color: #27ae60;")
        btn_add.clicked.connect(self.add_user)
        buttons_layout.addWidget(btn_add)
        
        btn_edit = QPushButton("✏️ Modifier")
        btn_edit.setStyleSheet("background-color: #3498db;")
        btn_edit.clicked.connect(self.edit_user)
        buttons_layout.addWidget(btn_edit)
        
        btn_delete = QPushButton("🗑️ Supprimer")
        btn_delete.setStyleSheet("background-color: #e74c3c;")
        btn_delete.clicked.connect(self.delete_user)
        buttons_layout.addWidget(btn_delete)
        
        btn_sync_device = QPushButton("📤 Envoyer au périphérique")
        btn_sync_device.setStyleSheet("background-color: #9b59b6;")
        btn_sync_device.clicked.connect(self.send_user_to_device)
        buttons_layout.addWidget(btn_sync_device)
        
        btn_refresh = QPushButton("🔄 Actualiser")
        btn_refresh.clicked.connect(self.refresh_users)
        buttons_layout.addWidget(btn_refresh)
        
        buttons_layout.addStretch()
        
        # Info
        self.users_count_label = QLabel("0 utilisateur(s)")
        buttons_layout.addWidget(self.users_count_label)
        
        layout.addLayout(buttons_layout)
        
        self.pages['users'] = page
    
    def create_fingerprints_page(self):
        """Créer la page de gestion des empreintes"""
        page = QFrame()
        layout = QVBoxLayout(page)
        
        # Titre
        title = QLabel("👆 Gestion des empreintes digitales")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        
        # Sélection utilisateur
        select_layout = QHBoxLayout()
        
        select_label = QLabel("Utilisateur:")
        select_layout.addWidget(select_label)
        
        self.fp_user_combo = QComboBox()
        self.fp_user_combo.currentIndexChanged.connect(self.load_user_fingerprints)
        select_layout.addWidget(self.fp_user_combo)
        
        select_layout.addStretch()
        
        layout.addLayout(select_layout)
        
        # Visualisation des doigts
        fingers_group = QGroupBox("Empreintes enregistrées")
        fingers_layout = QGridLayout(fingers_group)
        
        finger_names = [
            "Pouce G", "Index G", "Majeur G", "Annulaire G", "Auriculaire G",
            "Pouce D", "Index D", "Majeur D", "Annulaire D", "Auriculaire D"
        ]
        
        self.finger_buttons = []
        for i, name in enumerate(finger_names):
            btn = QPushButton(f"{name}\n○")
            btn.setCheckable(True)
            btn.setEnabled(False)
            btn.setStyleSheet("""
                QPushButton {
                    min-width: 100px;
                    min-height: 80px;
                    font-size: 10pt;
                }
                QPushButton:checked {
                    background-color: #27ae60;
                }
            """)
            row = i // 5
            col = i % 5
            fingers_layout.addWidget(btn, row, col)
            self.finger_buttons.append(btn)
        
        layout.addWidget(fingers_group)
        
        # Actions
        buttons_layout = QHBoxLayout()
        
        btn_refresh = QPushButton("🔄 Actualiser depuis le périphérique")
        btn_refresh.clicked.connect(self.refresh_fingerprints_from_device)
        buttons_layout.addWidget(btn_refresh)
        
        btn_enroll = QPushButton("👆 Enregistrer nouvelle empreinte")
        btn_enroll.setStyleSheet("background-color: #27ae60;")
        btn_enroll.clicked.connect(self.enroll_fingerprint)
        buttons_layout.addWidget(btn_enroll)
        
        btn_delete = QPushButton("🗑️ Supprimer empreinte sélectionnée")
        btn_delete.setStyleSheet("background-color: #e74c3c;")
        btn_delete.clicked.connect(self.delete_fingerprint)
        buttons_layout.addWidget(btn_delete)
        
        layout.addLayout(buttons_layout)
        
        layout.addStretch()
        
        self.pages['fingerprints'] = page
    
    def create_attendance_page(self):
        """Créer la page de gestion des pointages"""
        page = QFrame()
        layout = QVBoxLayout(page)
        
        # Titre
        header_layout = QHBoxLayout()
        
        title = QLabel("📋 Gestion des pointages")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Filtres
        filters_layout = QHBoxLayout()
        
        # Période
        filters_layout.addWidget(QLabel("Du:"))
        self.att_start_date = QDateEdit()
        self.att_start_date.setCalendarPopup(True)
        self.att_start_date.setDate(QDate.currentDate().addMonths(-1))
        filters_layout.addWidget(self.att_start_date)
        
        filters_layout.addWidget(QLabel("Au:"))
        self.att_end_date = QDateEdit()
        self.att_end_date.setCalendarPopup(True)
        self.att_end_date.setDate(QDate.currentDate())
        filters_layout.addWidget(self.att_end_date)
        
        # Utilisateur
        filters_layout.addWidget(QLabel("Utilisateur:"))
        self.att_user_filter = QComboBox()
        self.att_user_filter.addItem("Tous", None)
        filters_layout.addWidget(self.att_user_filter)
        
        # Département
        filters_layout.addWidget(QLabel("Département:"))
        self.att_dept_filter = QComboBox()
        self.att_dept_filter.addItem("Tous", None)
        filters_layout.addWidget(self.att_dept_filter)
        
        # Bouton filtrer
        btn_filter = QPushButton("🔍 Filtrer")
        btn_filter.clicked.connect(self.filter_attendance)
        filters_layout.addWidget(btn_filter)
        
        layout.addLayout(filters_layout)
        
        # Table des pointages
        self.attendance_table = QTableWidget()
        self.attendance_table.setColumnCount(7)
        self.attendance_table.setHorizontalHeaderLabels([
            "ID", "Employé", "Date", "Heure", "Type", "Vérification", "Terminal"
        ])
        self.attendance_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.attendance_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.attendance_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.attendance_table)
        
        # Boutons d'action
        buttons_layout = QHBoxLayout()
        
        btn_sync = QPushButton("📥 Télécharger depuis le périphérique")
        btn_sync.setStyleSheet("background-color: #3498db;")
        btn_sync.clicked.connect(lambda: self.sync_data('attendance'))
        buttons_layout.addWidget(btn_sync)
        
        btn_export = QPushButton("📤 Exporter Excel")
        btn_export.setStyleSheet("background-color: #27ae60;")
        btn_export.clicked.connect(self.export_attendance)
        buttons_layout.addWidget(btn_export)
        
        btn_clear = QPushButton("🗑️ Effacer sélection")
        btn_clear.setStyleSheet("background-color: #e74c3c;")
        btn_clear.clicked.connect(self.clear_attendance)
        buttons_layout.addWidget(btn_clear)
        
        btn_refresh = QPushButton("🔄 Actualiser")
        btn_refresh.clicked.connect(self.refresh_attendance)
        buttons_layout.addWidget(btn_refresh)
        
        buttons_layout.addStretch()
        
        self.attendance_count_label = QLabel("0 enregistrement(s)")
        buttons_layout.addWidget(self.attendance_count_label)
        
        layout.addLayout(buttons_layout)
        
        self.pages['attendance'] = page
    
    def create_reports_page(self):
        """Créer la page des rapports"""
        page = QFrame()
        layout = QVBoxLayout(page)
        
        # Titre
        title = QLabel("📈 Rapports et statistiques")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        
        # Types de rapports
        reports_group = QGroupBox("Types de rapports")
        reports_layout = QGridLayout(reports_group)
        
        report_buttons = [
            ("📊 Présence journalière", self.report_daily_presence),
            ("📅 Présence mensuelle", self.report_monthly_presence),
            ("⏰ Retards et absences", self.report_late_absent),
            ("🕐 Heures travaillées", self.report_work_hours),
            ("📈 Statistiques globales", self.report_global_stats),
            ("👤 Rapport individuel", self.report_individual),
        ]
        
        for i, (text, callback) in enumerate(report_buttons):
            btn = QPushButton(text)
            btn.setMinimumHeight(60)
            btn.clicked.connect(callback)
            row, col = i // 3, i % 3
            reports_layout.addWidget(btn, row, col)
        
        layout.addWidget(reports_group)
        
        # Période
        period_group = QGroupBox("Période du rapport")
        period_layout = QHBoxLayout(period_group)
        
        period_layout.addWidget(QLabel("Du:"))
        self.report_start_date = QDateEdit()
        self.report_start_date.setCalendarPopup(True)
        self.report_start_date.setDate(QDate.currentDate().addMonths(-1))
        period_layout.addWidget(self.report_start_date)
        
        period_layout.addWidget(QLabel("Au:"))
        self.report_end_date = QDateEdit()
        self.report_end_date.setCalendarPopup(True)
        self.report_end_date.setDate(QDate.currentDate())
        period_layout.addWidget(self.report_end_date)
        
        period_layout.addWidget(QLabel("Département:"))
        self.report_dept_filter = QComboBox()
        self.report_dept_filter.addItem("Tous", None)
        period_layout.addWidget(self.report_dept_filter)
        
        layout.addWidget(period_group)
        
        # Zone de prévisualisation
        preview_group = QGroupBox("Prévisualisation")
        preview_layout = QVBoxLayout(preview_group)
        
        self.report_preview = QTableWidget()
        self.report_preview.setEditTriggers(QAbstractItemView.NoEditTriggers)
        preview_layout.addWidget(self.report_preview)
        
        layout.addWidget(preview_group)
        
        # Boutons d'export
        export_layout = QHBoxLayout()
        
        btn_export_excel = QPushButton("📊 Exporter Excel")
        btn_export_excel.setStyleSheet("background-color: #27ae60;")
        btn_export_excel.clicked.connect(self.export_report_excel)
        export_layout.addWidget(btn_export_excel)
        
        btn_export_pdf = QPushButton("📄 Exporter PDF")
        btn_export_pdf.setStyleSheet("background-color: #e74c3c;")
        btn_export_pdf.clicked.connect(self.export_report_pdf)
        export_layout.addWidget(btn_export_pdf)
        
        btn_print = QPushButton("🖨️ Imprimer")
        btn_print.clicked.connect(self.print_report)
        export_layout.addWidget(btn_print)
        
        export_layout.addStretch()
        
        layout.addLayout(export_layout)
        
        self.pages['reports'] = page
    
    def create_departments_page(self):
        """Créer la page de gestion des départements"""
        page = QFrame()
        layout = QVBoxLayout(page)
        
        # Titre
        title = QLabel("🏢 Gestion des départements")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        
        # Table des départements
        self.depts_table = QTableWidget()
        self.depts_table.setColumnCount(4)
        self.depts_table.setHorizontalHeaderLabels(["ID", "Nom", "Description", "Employés"])
        self.depts_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.depts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.depts_table)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        
        btn_add = QPushButton("➕ Ajouter")
        btn_add.setStyleSheet("background-color: #27ae60;")
        btn_add.clicked.connect(self.add_department)
        buttons_layout.addWidget(btn_add)
        
        btn_edit = QPushButton("✏️ Modifier")
        btn_edit.clicked.connect(self.edit_department)
        buttons_layout.addWidget(btn_edit)
        
        btn_delete = QPushButton("🗑️ Supprimer")
        btn_delete.setStyleSheet("background-color: #e74c3c;")
        btn_delete.clicked.connect(self.delete_department)
        buttons_layout.addWidget(btn_delete)
        
        btn_refresh = QPushButton("🔄 Actualiser")
        btn_refresh.clicked.connect(self.refresh_departments)
        buttons_layout.addWidget(btn_refresh)
        
        layout.addLayout(buttons_layout)
        
        self.pages['departments'] = page
    
    def create_schedules_page(self):
        """Créer la page de gestion des horaires"""
        page = QFrame()
        layout = QVBoxLayout(page)
        
        # Titre
        title = QLabel("⏰ Gestion des horaires")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        
        # Table des horaires
        self.schedules_table = QTableWidget()
        self.schedules_table.setColumnCount(6)
        self.schedules_table.setHorizontalHeaderLabels([
            "Nom", "Début", "Fin", "Grâce (min)", "Entrée", "Sortie"
        ])
        self.schedules_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.schedules_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.schedules_table)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        
        btn_add = QPushButton("➕ Ajouter")
        btn_add.setStyleSheet("background-color: #27ae60;")
        btn_add.clicked.connect(self.add_schedule)
        buttons_layout.addWidget(btn_add)
        
        btn_edit = QPushButton("✏️ Modifier")
        btn_edit.clicked.connect(self.edit_schedule)
        buttons_layout.addWidget(btn_edit)
        
        btn_delete = QPushButton("🗑️ Supprimer")
        btn_delete.setStyleSheet("background-color: #e74c3c;")
        btn_delete.clicked.connect(self.delete_schedule)
        buttons_layout.addWidget(btn_delete)
        
        btn_refresh = QPushButton("🔄 Actualiser")
        btn_refresh.clicked.connect(self.refresh_schedules)
        buttons_layout.addWidget(btn_refresh)
        
        layout.addLayout(buttons_layout)
        
        self.pages['schedules'] = page
    
    def create_holidays_page(self):
        """Créer la page de gestion des jours fériés"""
        page = QFrame()
        layout = QVBoxLayout(page)
        
        # Titre
        title = QLabel("📅 Gestion des jours fériés")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        
        # Table des jours fériés
        self.holidays_table = QTableWidget()
        self.holidays_table.setColumnCount(4)
        self.holidays_table.setHorizontalHeaderLabels([
            "ID", "Nom", "Date", "Récurrent"
        ])
        self.holidays_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.holidays_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.holidays_table)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        
        btn_add = QPushButton("➕ Ajouter")
        btn_add.setStyleSheet("background-color: #27ae60;")
        btn_add.clicked.connect(self.add_holiday)
        buttons_layout.addWidget(btn_add)
        
        btn_edit = QPushButton("✏️ Modifier")
        btn_edit.clicked.connect(self.edit_holiday)
        buttons_layout.addWidget(btn_edit)
        
        btn_delete = QPushButton("🗑️ Supprimer")
        btn_delete.setStyleSheet("background-color: #e74c3c;")
        btn_delete.clicked.connect(self.delete_holiday)
        buttons_layout.addWidget(btn_delete)
        
        btn_refresh = QPushButton("🔄 Actualiser")
        btn_refresh.clicked.connect(self.refresh_holidays)
        buttons_layout.addWidget(btn_refresh)
        
        layout.addLayout(buttons_layout)
        
        self.pages['holidays'] = page
    
    def create_settings_page(self):
        """Créer la page des paramètres"""
        page = QFrame()
        layout = QVBoxLayout(page)
        
        # Titre
        title = QLabel("⚙️ Paramètres")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        
        # Paramètres du périphérique
        device_group = QGroupBox("Configuration du périphérique")
        device_layout = QFormLayout(device_group)
        
        self.settings_ip = QLineEdit(self.device_ip)
        device_layout.addRow("Adresse IP:", self.settings_ip)
        
        self.settings_port = QSpinBox()
        self.settings_port.setRange(1, 65535)
        self.settings_port.setValue(self.device_port)
        device_layout.addRow("Port:", self.settings_port)
        
        self.settings_timeout = QSpinBox()
        self.settings_timeout.setRange(5, 120)
        self.settings_timeout.setValue(int(self.settings.get('device_timeout', 30)))
        device_layout.addRow("Timeout (sec):", self.settings_timeout)
        
        layout.addWidget(device_group)
        
        # Paramètres de synchronisation
        sync_group = QGroupBox("Synchronisation automatique")
        sync_layout = QFormLayout(sync_group)
        
        self.settings_auto_sync = QCheckBox()
        self.settings_auto_sync.setChecked(self.settings.get('auto_sync') == '1')
        sync_layout.addRow("Activer:", self.settings_auto_sync)
        
        self.settings_sync_interval = QSpinBox()
        self.settings_sync_interval.setRange(1, 1440)
        self.settings_sync_interval.setValue(int(self.settings.get('sync_interval', 30)))
        sync_layout.addRow("Intervalle (min):", self.settings_sync_interval)
        
        layout.addWidget(sync_group)
        
        # Paramètres généraux
        general_group = QGroupBox("Paramètres généraux")
        general_layout = QFormLayout(general_group)
        
        self.settings_company = QLineEdit(self.settings.get('company_name', ''))
        general_layout.addRow("Nom de l'entreprise:", self.settings_company)
        
        self.settings_export_path = QLineEdit(self.settings.get('export_path', ''))
        btn_browse = QPushButton("Parcourir...")
        btn_browse.clicked.connect(self.browse_export_path)
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.settings_export_path)
        path_layout.addWidget(btn_browse)
        general_layout.addRow("Dossier d'export:", path_layout)
        
        layout.addWidget(general_group)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        
        btn_save = QPushButton("💾 Enregistrer")
        btn_save.setStyleSheet("background-color: #27ae60;")
        btn_save.clicked.connect(self.save_settings)
        buttons_layout.addWidget(btn_save)
        
        btn_reset = QPushButton("🔄 Réinitialiser")
        btn_reset.clicked.connect(self.reset_settings)
        buttons_layout.addWidget(btn_reset)
        
        layout.addLayout(buttons_layout)
        
        layout.addStretch()
        
        self.pages['settings'] = page
    
    def setup_menus(self):
        """Configurer les menus"""
        menubar = self.menuBar()
        
        # Menu Fichier
        file_menu = menubar.addMenu("Fichier")
        
        export_action = QAction("Exporter données...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        
        backup_action = QAction("Sauvegarder base de données...", self)
        backup_action.triggered.connect(self.backup_database)
        file_menu.addAction(backup_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Quitter", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menu Périphérique
        device_menu = menubar.addMenu("Périphérique")
        
        connect_action = QAction("Connecter", self)
        connect_action.triggered.connect(self.toggle_connection)
        device_menu.addAction(connect_action)
        
        sync_users_action = QAction("Synchroniser utilisateurs", self)
        sync_users_action.triggered.connect(lambda: self.sync_data('users'))
        device_menu.addAction(sync_users_action)
        
        sync_att_action = QAction("Synchroniser pointages", self)
        sync_att_action.triggered.connect(lambda: self.sync_data('attendance'))
        device_menu.addAction(sync_att_action)
        
        device_menu.addSeparator()
        
        time_sync_action = QAction("Synchroniser l'heure", self)
        time_sync_action.triggered.connect(self.sync_device_time)
        device_menu.addAction(time_sync_action)
        
        restart_action = QAction("Redémarrer le périphérique", self)
        restart_action.triggered.connect(self.restart_device)
        device_menu.addAction(restart_action)
        
        # Menu Rapports
        reports_menu = menubar.addMenu("Rapports")
        
        daily_action = QAction("Présence journalière", self)
        daily_action.triggered.connect(self.report_daily_presence)
        reports_menu.addAction(daily_action)
        
        monthly_action = QAction("Présence mensuelle", self)
        monthly_action.triggered.connect(self.report_monthly_presence)
        reports_menu.addAction(monthly_action)
        
        # Menu Aide
        help_menu = menubar.addMenu("Aide")
        
        about_action = QAction("À propos", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_toolbar(self):
        """Configurer la barre d'outils"""
        toolbar = QToolBar("Barre d'outils principale")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Actions
        toolbar.addAction("🏠 Accueil", self.show_dashboard)
        toolbar.addAction("👥 Utilisateurs", self.show_users)
        toolbar.addAction("📋 Pointages", self.show_attendance)
        toolbar.addAction("📈 Rapports", self.show_reports)
        
        toolbar.addSeparator()
        
        toolbar.addAction("📥 Sync pointages", lambda: self.sync_data('attendance'))
        toolbar.addAction("📤 Export", self.export_data)
    
    def setup_statusbar(self):
        """Configurer la barre de statut"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        # Label de statut
        self.status_label = QLabel("Prêt")
        self.statusbar.addWidget(self.status_label, 1)
        
        # Progress bar (cachée par défaut)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        self.statusbar.addPermanentWidget(self.progress_bar)
        
        # Heure
        self.time_label = QLabel()
        self.statusbar.addPermanentWidget(self.time_label)
        
        # Timer pour l'heure
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)
    
    # ==================== NAVIGATION ====================
    
    def set_active_nav(self, active_btn):
        """Définir le bouton de navigation actif"""
        for btn in self.nav_buttons:
            btn.setChecked(btn == active_btn)
    
    def show_page(self, page_name: str):
        """Afficher une page"""
        for name, page in self.pages.items():
            page.setVisible(name == page_name)
    
    def show_dashboard(self):
        """Afficher le tableau de bord"""
        self.show_page('dashboard')
        self.refresh_dashboard()
    
    def show_users(self):
        """Afficher la page utilisateurs"""
        self.show_page('users')
        self.refresh_users()
    
    def show_fingerprints(self):
        """Afficher la page empreintes"""
        self.show_page('fingerprints')
        self.refresh_fingerprints()
    
    def show_attendance(self):
        """Afficher la page pointages"""
        self.show_page('attendance')
        self.refresh_attendance()
    
    def show_reports(self):
        """Afficher la page rapports"""
        self.show_page('reports')
        self.refresh_reports()
    
    def show_departments(self):
        """Afficher la page départements"""
        self.show_page('departments')
        self.refresh_departments()
    
    def show_schedules(self):
        """Afficher la page horaires"""
        self.show_page('schedules')
        self.refresh_schedules()
    
    def show_holidays(self):
        """Afficher la page jours fériés"""
        self.show_page('holidays')
        self.refresh_holidays()
    
    def show_settings(self):
        """Afficher la page paramètres"""
        self.show_page('settings')
    
    # ==================== CONNEXION ====================
    
    def toggle_connection(self):
        """Connecter/Déconnecter le périphérique"""
        if self.connected:
            self.disconnect_device()
        else:
            self.connect_device()
    
    def connect_device(self):
        """Connecter au périphérique"""
        self.status_label.setText("Connexion en cours...")
        self.conn_button.setEnabled(False)
        
        # Créer le périphérique
        self.device = ZKDevice(
            self.device_ip,
            self.device_port,
            int(self.settings.get('device_timeout', 30))
        )
        
        # Lancer la connexion dans un thread
        self.conn_thread = ConnectionThread(self.device)
        self.conn_thread.finished.connect(self.on_connection_finished)
        self.conn_thread.start()
    
    def disconnect_device(self):
        """Déconnecter le périphérique"""
        if self.device:
            self.device.disconnect()
            self.device = None
        
        self.connected = False
        self.conn_status.setText("● Déconnecté")
        self.conn_status.setStyleSheet("color: #e74c3c;")
        self.conn_button.setText("🔗 Connecter")
        self.conn_button.setEnabled(True)
        self.status_label.setText("Déconnecté")
    
    def on_connection_finished(self, success: bool, message: str):
        """Callback de fin de connexion"""
        self.conn_button.setEnabled(True)
        
        if success:
            self.connected = True
            self.conn_status.setText("● Connecté")
            self.conn_status.setStyleSheet("color: #27ae60;")
            self.conn_button.setText("🔌 Déconnecter")
            self.status_label.setText(f"Connecté à {self.device_ip}")
            
            # Ajouter un log
            self.db.add_log('INFO', f'Connexion réussie à {self.device_ip}')
        else:
            self.conn_status.setText(f"● Erreur")
            self.conn_status.setStyleSheet("color: #e74c3c;")
            self.conn_button.setText("🔗 Connecter")
            self.status_label.setText(f"Erreur: {message}")
            
            QMessageBox.warning(self, "Erreur de connexion", message)
            self.db.add_log('ERROR', f'Échec de connexion: {message}')
    
    def test_device_connection(self):
        """Tester la connexion au périphérique"""
        success, message = test_connection(self.device_ip, self.device_port)
        
        if success:
            QMessageBox.information(self, "Test de connexion", message)
        else:
            QMessageBox.warning(self, "Test de connexion", message)
    
    # ==================== SYNCHRONISATION ====================
    
    def sync_data(self, sync_type: str):
        """Synchroniser les données"""
        if not self.connected:
            QMessageBox.warning(self, "Non connecté", 
                              "Veuillez vous connecter au périphérique d'abord.")
            return
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Mode indéterminé
        self.status_label.setText(f"Synchronisation {sync_type} en cours...")
        
        self.sync_thread = SyncThread(self.device, self.db, sync_type)
        self.sync_thread.progress.connect(self.on_sync_progress)
        self.sync_thread.finished.connect(self.on_sync_finished)
        self.sync_thread.start()
    
    def on_sync_progress(self, current: int, total: int, message: str):
        """Callback de progression de synchronisation"""
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(current)
        self.status_label.setText(message)
    
    def on_sync_finished(self, success: bool, message: str, count: int):
        """Callback de fin de synchronisation"""
        self.progress_bar.setVisible(False)
        
        if success:
            self.status_label.setText(message)
            QMessageBox.information(self, "Synchronisation terminée", message)
            
            # Rafraîchir les données
            if 'utilisateurs' in message:
                self.refresh_users()
            else:
                self.refresh_attendance()
                self.refresh_dashboard()
            
            # Mettre à jour la carte de synchronisation
            self.update_sync_card()
        else:
            QMessageBox.warning(self, "Erreur de synchronisation", message)
        
        self.status_label.setText("Prêt")
    
    def auto_sync(self):
        """Synchronisation automatique"""
        if self.connected:
            self.sync_data('attendance')
    
    # ==================== RAFRAÎCHISSEMENT DES DONNÉES ====================
    
    def refresh_dashboard(self):
        """Rafraîchir le tableau de bord"""
        # Utilisateurs
        users_count = self.db.get_users_count()
        self.card_users.findChild(QLabel, "stat_value").setText(str(users_count))
        
        # Pointages aujourd'hui
        today = date.today()
        today_attendance = self.db.get_attendance_by_date(today)
        self.card_today.findChild(QLabel, "stat_value").setText(str(len(today_attendance)))
        
        # Départements
        depts = self.db.get_all_departments()
        self.card_depts.findChild(QLabel, "stat_value").setText(str(len(depts)))
        
        # Derniers pointages
        self.recent_table.setRowCount(0)
        recent = self.db.get_attendance_range(
            date.today() - timedelta(days=7), date.today()
        )[:10]
        
        for record in recent:
            row = self.recent_table.rowCount()
            self.recent_table.insertRow(row)
            
            self.recent_table.setItem(row, 0, QTableWidgetItem(str(record.get('user_name', ''))))
            self.recent_table.setItem(row, 1, QTableWidgetItem(str(record.get('timestamp', ''))))
            self.recent_table.setItem(row, 2, QTableWidgetItem(STATUS_NAMES.get(record.get('status', 0), 'N/A')))
            self.recent_table.setItem(row, 3, QTableWidgetItem(VERIFY_TYPE_NAMES.get(record.get('verify_type', 0), 'N/A')))
        
        # Alertes
        self.refresh_alerts()
    
    def refresh_alerts(self):
        """Rafraîchir les alertes"""
        alerts = []
        
        # Vérifier la connexion
        if not self.connected:
            alerts.append("⚠️ Non connecté au périphérique")
        
        # Vérifier les logs d'erreur récents
        error_logs = self.db.get_logs(5, 'ERROR')
        if error_logs:
            alerts.append(f"⚠️ {len(error_logs)} erreur(s) récente(s)")
        
        # Mettre à jour
        self.alerts_list.setText("\n".join(alerts) if alerts else "✅ Aucune alerte")
    
    def update_sync_card(self):
        """Mettre à jour la carte de synchronisation"""
        now = datetime.now().strftime("%H:%M:%S")
        self.card_sync.findChild(QLabel, "stat_value").setText(now)
    
    def refresh_users(self):
        """Rafraîchir la liste des utilisateurs"""
        users = self.db.get_all_users(include_inactive=True)
        departments = self.db.get_all_departments()
        
        # Mettre à jour le filtre des départements
        self.users_dept_filter.clear()
        self.users_dept_filter.addItem("Tous", None)
        for dept in departments:
            self.users_dept_filter.addItem(dept['name'], dept['id'])
        
        # Peupler la table
        self.users_table.setRowCount(0)
        
        for user in users:
            row = self.users_table.rowCount()
            self.users_table.insertRow(row)
            
            self.users_table.setItem(row, 0, QTableWidgetItem(str(user['id'])))
            self.users_table.setItem(row, 1, QTableWidgetItem(str(user.get('uid', ''))))
            self.users_table.setItem(row, 2, QTableWidgetItem(user['name']))
            self.users_table.setItem(row, 3, QTableWidgetItem(PRIVILEGE_NAMES.get(user.get('privilege', 0), 'Utilisateur')))
            self.users_table.setItem(row, 4, QTableWidgetItem(user.get('department_name', '')))
            self.users_table.setItem(row, 5, QTableWidgetItem(user.get('card', '') or ''))
            self.users_table.setItem(row, 6, QTableWidgetItem(str(self.db.count_user_fingerprints(user['id']))))
            
            active_item = QTableWidgetItem("✓" if user.get('is_active', 1) else "✗")
            active_item.setTextAlignment(Qt.AlignCenter)
            self.users_table.setItem(row, 7, active_item)
        
        self.users_count_label.setText(f"{len(users)} utilisateur(s)")
    
    def filter_users(self):
        """Filtrer les utilisateurs"""
        query = self.users_search.text()
        dept_id = self.users_dept_filter.currentData()
        
        if query:
            users = self.db.search_users(query)
        else:
            users = self.db.get_all_users(include_inactive=True)
        
        if dept_id:
            users = [u for u in users if u.get('department_id') == dept_id]
        
        # Mettre à jour la table
        self.users_table.setRowCount(0)
        
        for user in users:
            row = self.users_table.rowCount()
            self.users_table.insertRow(row)
            
            self.users_table.setItem(row, 0, QTableWidgetItem(str(user['id'])))
            self.users_table.setItem(row, 1, QTableWidgetItem(str(user.get('uid', ''))))
            self.users_table.setItem(row, 2, QTableWidgetItem(user['name']))
            self.users_table.setItem(row, 3, QTableWidgetItem(PRIVILEGE_NAMES.get(user.get('privilege', 0), 'Utilisateur')))
            self.users_table.setItem(row, 4, QTableWidgetItem(user.get('department_name', '')))
            self.users_table.setItem(row, 5, QTableWidgetItem(user.get('card', '') or ''))
            self.users_table.setItem(row, 6, QTableWidgetItem(str(self.db.count_user_fingerprints(user['id']))))
            
            active_item = QTableWidgetItem("✓" if user.get('is_active', 1) else "✗")
            active_item.setTextAlignment(Qt.AlignCenter)
            self.users_table.setItem(row, 7, active_item)
        
        self.users_count_label.setText(f"{len(users)} utilisateur(s)")
    
    def refresh_fingerprints(self):
        """Rafraîchir les empreintes"""
        # Charger les utilisateurs dans le combo
        self.fp_user_combo.clear()
        users = self.db.get_all_users()
        
        for user in users:
            self.fp_user_combo.addItem(user['name'], user['id'])
    
    def load_user_fingerprints(self):
        """Charger les empreintes d'un utilisateur"""
        user_id = self.fp_user_combo.currentData()
        
        if not user_id:
            return
        
        # Récupérer les empreintes
        fingerprints = self.db.get_user_fingerprints(user_id)
        fp_indexes = [fp['finger_index'] for fp in fingerprints]
        
        # Mettre à jour les boutons
        for i, btn in enumerate(self.finger_buttons):
            if i in fp_indexes:
                btn.setChecked(True)
                btn.setText(btn.text().split('\n')[0] + '\n●')
            else:
                btn.setChecked(False)
                btn.setText(btn.text().split('\n')[0] + '\n○')
    
    def refresh_attendance(self):
        """Rafraîchir les pointages"""
        start_date = self.att_start_date.date().toPyDate()
        end_date = self.att_end_date.date().toPyDate()
        
        attendance = self.db.get_attendance_range(start_date, end_date)
        
        # Mettre à jour le filtre des utilisateurs
        self.att_user_filter.clear()
        self.att_user_filter.addItem("Tous", None)
        users = self.db.get_all_users()
        for user in users:
            self.att_user_filter.addItem(user['name'], user['id'])
        
        # Mettre à jour le filtre des départements
        self.att_dept_filter.clear()
        self.att_dept_filter.addItem("Tous", None)
        depts = self.db.get_all_departments()
        for dept in depts:
            self.att_dept_filter.addItem(dept['name'], dept['id'])
        
        # Peupler la table
        self.attendance_table.setRowCount(0)
        
        for record in attendance:
            row = self.attendance_table.rowCount()
            self.attendance_table.insertRow(row)
            
            ts = record.get('timestamp')
            if isinstance(ts, datetime):
                date_str = ts.strftime('%d/%m/%Y')
                time_str = ts.strftime('%H:%M:%S')
            else:
                date_str = str(ts)
                time_str = ''
            
            self.attendance_table.setItem(row, 0, QTableWidgetItem(str(record['id'])))
            self.attendance_table.setItem(row, 1, QTableWidgetItem(str(record.get('user_name', ''))))
            self.attendance_table.setItem(row, 2, QTableWidgetItem(date_str))
            self.attendance_table.setItem(row, 3, QTableWidgetItem(time_str))
            self.attendance_table.setItem(row, 4, QTableWidgetItem(STATUS_NAMES.get(record.get('status', 0), 'N/A')))
            self.attendance_table.setItem(row, 5, QTableWidgetItem(VERIFY_TYPE_NAMES.get(record.get('verify_type', 0), 'N/A')))
            self.attendance_table.setItem(row, 6, QTableWidgetItem(str(record.get('terminal_id', ''))))
        
        self.attendance_count_label.setText(f"{len(attendance)} enregistrement(s)")
    
    def filter_attendance(self):
        """Filtrer les pointages"""
        self.refresh_attendance()
    
    def refresh_reports(self):
        """Rafraîchir les rapports"""
        # Charger les filtres
        self.report_dept_filter.clear()
        self.report_dept_filter.addItem("Tous", None)
        depts = self.db.get_all_departments()
        for dept in depts:
            self.report_dept_filter.addItem(dept['name'], dept['id'])
    
    def refresh_departments(self):
        """Rafraîchir les départements"""
        departments = self.db.get_all_departments()
        
        self.depts_table.setRowCount(0)
        
        for dept in departments:
            row = self.depts_table.rowCount()
            self.depts_table.insertRow(row)
            
            self.depts_table.setItem(row, 0, QTableWidgetItem(str(dept['id'])))
            self.depts_table.setItem(row, 1, QTableWidgetItem(dept['name']))
            self.depts_table.setItem(row, 2, QTableWidgetItem(dept.get('description', '') or ''))
            self.depts_table.setItem(row, 3, QTableWidgetItem(str(self.db.get_department_users_count(dept['id']))))
    
    def refresh_schedules(self):
        """Rafraîchir les horaires"""
        schedules = self.db.get_all_schedules()
        
        self.schedules_table.setRowCount(0)
        
        for schedule in schedules:
            row = self.schedules_table.rowCount()
            self.schedules_table.insertRow(row)
            
            self.schedules_table.setItem(row, 0, QTableWidgetItem(schedule['name']))
            self.schedules_table.setItem(row, 1, QTableWidgetItem(str(schedule['start_time'])))
            self.schedules_table.setItem(row, 2, QTableWidgetItem(str(schedule['end_time'])))
            self.schedules_table.setItem(row, 3, QTableWidgetItem(str(schedule.get('grace_period', 0))))
            self.schedules_table.setItem(row, 4, QTableWidgetItem(f"{schedule.get('check_in_start', '')} - {schedule.get('check_in_end', '')}"))
            self.schedules_table.setItem(row, 5, QTableWidgetItem(f"{schedule.get('check_out_start', '')} - {schedule.get('check_out_end', '')}"))
    
    def refresh_holidays(self):
        """Rafraîchir les jours fériés"""
        holidays = self.db.get_all_holidays()
        
        self.holidays_table.setRowCount(0)
        
        for holiday in holidays:
            row = self.holidays_table.rowCount()
            self.holidays_table.insertRow(row)
            
            self.holidays_table.setItem(row, 0, QTableWidgetItem(str(holiday['id'])))
            self.holidays_table.setItem(row, 1, QTableWidgetItem(holiday['name']))
            self.holidays_table.setItem(row, 2, QTableWidgetItem(str(holiday['date'])))
            self.holidays_table.setItem(row, 3, QTableWidgetItem("Oui" if holiday.get('is_recurring') else "Non"))
    
    # ==================== ACTIONS CRUD ====================
    
    def add_user(self):
        """Ajouter un utilisateur"""
        from .dialogs import UserDialog
        
        dialog = UserDialog(self.db, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_users()
    
    def edit_user(self):
        """Modifier un utilisateur"""
        selected = self.users_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner un utilisateur.")
            return
        
        user_id = int(self.users_table.item(selected[0].row(), 0).text())
        
        from .dialogs import UserDialog
        
        dialog = UserDialog(self.db, user_id, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_users()
    
    def delete_user(self):
        """Supprimer un utilisateur"""
        selected = self.users_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner un utilisateur.")
            return
        
        user_id = int(self.users_table.item(selected[0].row(), 0).text())
        user_name = self.users_table.item(selected[0].row(), 2).text()
        
        reply = QMessageBox.question(
            self, "Confirmation",
            f"Voulez-vous vraiment supprimer l'utilisateur '{user_name}' ?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.db.delete_user(user_id)
            self.refresh_users()
    
    def send_user_to_device(self):
        """Envoyer l'utilisateur au périphérique"""
        if not self.connected:
            QMessageBox.warning(self, "Non connecté", "Veuillez vous connecter au périphérique.")
            return
        
        selected = self.users_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner un utilisateur.")
            return
        
        user_id = int(self.users_table.item(selected[0].row(), 0).text())
        user = self.db.get_user(user_id)
        
        if self.device.set_user(
            user['id'],
            user['name'],
            user.get('privilege', 0),
            user.get('password', ''),
            user.get('card', '')
        ):
            QMessageBox.information(self, "Succès", "Utilisateur envoyé au périphérique.")
        else:
            QMessageBox.warning(self, "Erreur", "Échec de l'envoi au périphérique.")
    
    def enroll_fingerprint(self):
        """Enregistrer une empreinte"""
        QMessageBox.information(self, "Information", 
            "L'enregistrement d'empreinte doit se faire directement sur le périphérique.\n"
            "Après l'enregistrement, utilisez 'Actualiser depuis le périphérique'.")
    
    def refresh_fingerprints_from_device(self):
        """Rafraîchir les empreintes depuis le périphérique"""
        if not self.connected:
            QMessageBox.warning(self, "Non connecté", "Veuillez vous connecter au périphérique.")
            return
        
        user_id = self.fp_user_combo.currentData()
        if not user_id:
            return
        
        try:
            fingerprints = self.device.get_user_fingerprints(user_id)
            
            # Sauvegarder dans la base
            for fp in fingerprints:
                self.db.save_fingerprint(
                    user_id,
                    fp['finger_index'],
                    fp['template'],
                    fp['template_size'],
                    fp.get('validity', 1)
                )
            
            self.load_user_fingerprints()
            QMessageBox.information(self, "Succès", f"{len(fingerprints)} empreinte(s) récupérée(s).")
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur: {str(e)}")
    
    def delete_fingerprint(self):
        """Supprimer une empreinte"""
        user_id = self.fp_user_combo.currentData()
        
        # Trouver le doigt sélectionné
        selected_index = None
        for i, btn in enumerate(self.finger_buttons):
            if btn.isChecked():
                selected_index = i
                break
        
        if selected_index is None:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner une empreinte.")
            return
        
        reply = QMessageBox.question(
            self, "Confirmation",
            "Voulez-vous vraiment supprimer cette empreinte ?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Supprimer de la base
            self.db.delete_fingerprint(user_id, selected_index)
            
            # Supprimer du périphérique si connecté
            if self.connected:
                self.device.delete_user_fingerprints(user_id, selected_index)
            
            self.load_user_fingerprints()
    
    def clear_attendance(self):
        """Effacer les pointages sélectionnés"""
        # TODO: Implémenter la suppression
        pass
    
    def add_department(self):
        """Ajouter un département"""
        from .dialogs import DepartmentDialog
        
        dialog = DepartmentDialog(self.db, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_departments()
    
    def edit_department(self):
        """Modifier un département"""
        selected = self.depts_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner un département.")
            return
        
        dept_id = int(self.depts_table.item(selected[0].row(), 0).text())
        
        from .dialogs import DepartmentDialog
        
        dialog = DepartmentDialog(self.db, dept_id, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_departments()
    
    def delete_department(self):
        """Supprimer un département"""
        selected = self.depts_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner un département.")
            return
        
        dept_id = int(self.depts_table.item(selected[0].row(), 0).text())
        dept_name = self.depts_table.item(selected[0].row(), 1).text()
        
        if dept_id == 1:
            QMessageBox.warning(self, "Erreur", "Impossible de supprimer le département par défaut.")
            return
        
        reply = QMessageBox.question(
            self, "Confirmation",
            f"Voulez-vous vraiment supprimer le département '{dept_name}' ?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.db.delete_department(dept_id)
            self.refresh_departments()
    
    def add_schedule(self):
        """Ajouter un horaire"""
        from .dialogs import ScheduleDialog
        
        dialog = ScheduleDialog(self.db, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_schedules()
    
    def edit_schedule(self):
        """Modifier un horaire"""
        selected = self.schedules_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner un horaire.")
            return
        
        # TODO: Récupérer l'ID et ouvrir le dialogue
    
    def delete_schedule(self):
        """Supprimer un horaire"""
        # TODO: Implémenter
        pass
    
    def add_holiday(self):
        """Ajouter un jour férié"""
        from .dialogs import HolidayDialog
        
        dialog = HolidayDialog(self.db, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_holidays()
    
    def edit_holiday(self):
        """Modifier un jour férié"""
        # TODO: Implémenter
        pass
    
    def delete_holiday(self):
        """Supprimer un jour férié"""
        selected = self.holidays_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner un jour férié.")
            return
        
        holiday_id = int(self.holidays_table.item(selected[0].row(), 0).text())
        
        reply = QMessageBox.question(
            self, "Confirmation",
            "Voulez-vous vraiment supprimer ce jour férié ?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.db.delete_holiday(holiday_id)
            self.refresh_holidays()
    
    # ==================== RAPPORTS ====================
    
    def report_daily_presence(self):
        """Rapport de présence journalière"""
        target_date = self.report_start_date.date().toPyDate()
        attendance = self.db.get_attendance_by_date(target_date)
        users = self.db.get_all_users()
        
        # Préparer les données
        self.report_preview.setRowCount(0)
        self.report_preview.setColumnCount(5)
        self.report_preview.setHorizontalHeaderLabels([
            "Employé", "Première entrée", "Dernière sortie", "Total heures", "Status"
        ])
        
        # Grouper par utilisateur
        user_attendance = {}
        for record in attendance:
            uid = record['user_id']
            if uid not in user_attendance:
                user_attendance[uid] = []
            user_attendance[uid].append(record)
        
        for user in users:
            row = self.report_preview.rowCount()
            self.report_preview.insertRow(row)
            
            self.report_preview.setItem(row, 0, QTableWidgetItem(user['name']))
            
            records = user_attendance.get(user['id'], [])
            if records:
                times = [r['timestamp'] for r in records]
                first = min(times)
                last = max(times)
                
                self.report_preview.setItem(row, 1, QTableWidgetItem(first.strftime('%H:%M:%S')))
                self.report_preview.setItem(row, 2, QTableWidgetItem(last.strftime('%H:%M:%S')))
                
                # Calculer les heures
                if first != last:
                    hours = (last - first).total_seconds() / 3600
                    self.report_preview.setItem(row, 3, QTableWidgetItem(f"{hours:.1f}h"))
                else:
                    self.report_preview.setItem(row, 3, QTableWidgetItem("N/A"))
                
                self.report_preview.setItem(row, 4, QTableWidgetItem("Présent"))
            else:
                self.report_preview.setItem(row, 1, QTableWidgetItem("-"))
                self.report_preview.setItem(row, 2, QTableWidgetItem("-"))
                self.report_preview.setItem(row, 3, QTableWidgetItem("-"))
                self.report_preview.setItem(row, 4, QTableWidgetItem("Absent"))
    
    def report_monthly_presence(self):
        """Rapport de présence mensuelle"""
        QMessageBox.information(self, "Info", "Rapport mensuel en cours de développement.")
    
    def report_late_absent(self):
        """Rapport des retards et absences"""
        QMessageBox.information(self, "Info", "Rapport retards/absences en cours de développement.")
    
    def report_work_hours(self):
        """Rapport des heures travaillées"""
        QMessageBox.information(self, "Info", "Rapport heures travaillées en cours de développement.")
    
    def report_global_stats(self):
        """Statistiques globales"""
        QMessageBox.information(self, "Info", "Statistiques globales en cours de développement.")
    
    def report_individual(self):
        """Rapport individuel"""
        QMessageBox.information(self, "Info", "Rapport individuel en cours de développement.")
    
    # ==================== EXPORT ====================
    
    def export_data(self):
        """Exporter les données"""
        # TODO: Ouvrir un dialogue d'export
        pass
    
    def export_attendance(self):
        """Exporter les pointages"""
        from ..utils.export import export_attendance_to_excel
        
        start_date = self.att_start_date.date().toPyDate()
        end_date = self.att_end_date.date().toPyDate()
        attendance = self.db.get_attendance_range(start_date, end_date)
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Exporter les pointages",
            f"pointages_{start_date}_{end_date}.xlsx",
            "Excel (*.xlsx)"
        )
        
        if filename:
            export_attendance_to_excel(attendance, filename)
            QMessageBox.information(self, "Succès", f"Données exportées vers:\n{filename}")
    
    def export_report_excel(self):
        """Exporter le rapport en Excel"""
        QMessageBox.information(self, "Info", "Export Excel en cours de développement.")
    
    def export_report_pdf(self):
        """Exporter le rapport en PDF"""
        QMessageBox.information(self, "Info", "Export PDF en cours de développement.")
    
    def print_report(self):
        """Imprimer le rapport"""
        QMessageBox.information(self, "Info", "Impression en cours de développement.")
    
    # ==================== PARAMÈTRES ====================
    
    def save_settings(self):
        """Sauvegarder les paramètres"""
        self.db.set_setting('device_ip', self.settings_ip.text())
        self.db.set_setting('device_port', str(self.settings_port.value()))
        self.db.set_setting('device_timeout', str(self.settings_timeout.value()))
        self.db.set_setting('auto_sync', '1' if self.settings_auto_sync.isChecked() else '0')
        self.db.set_setting('sync_interval', str(self.settings_sync_interval.value()))
        self.db.set_setting('company_name', self.settings_company.text())
        self.db.set_setting('export_path', self.settings_export_path.text())
        
        # Mettre à jour les variables locales
        self.device_ip = self.settings_ip.text()
        self.device_port = self.settings_port.value()
        
        # Auto-sync
        if self.settings_auto_sync.isChecked():
            self.auto_sync_timer.start(self.settings_sync_interval.value() * 60000)
        else:
            self.auto_sync_timer.stop()
        
        QMessageBox.information(self, "Succès", "Paramètres enregistrés.")
    
    def reset_settings(self):
        """Réinitialiser les paramètres"""
        self.settings_ip.setText('192.168.1.201')
        self.settings_port.setValue(4370)
        self.settings_timeout.setValue(30)
        self.settings_auto_sync.setChecked(False)
        self.settings_sync_interval.setValue(30)
    
    def browse_export_path(self):
        """Parcourir pour le dossier d'export"""
        folder = QFileDialog.getExistingDirectory(self, "Dossier d'export")
        if folder:
            self.settings_export_path.setText(folder)
    
    # ==================== UTILITAIRES ====================
    
    def backup_database(self):
        """Sauvegarder la base de données"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Sauvegarder la base de données",
            f"zkteco_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
            "Database (*.db)"
        )
        
        if filename:
            self.db.backup_database(filename)
            QMessageBox.information(self, "Succès", f"Base de données sauvegardée:\n{filename}")
    
    def sync_device_time(self):
        """Synchroniser l'heure du périphérique"""
        if not self.connected:
            QMessageBox.warning(self, "Non connecté", "Veuillez vous connecter au périphérique.")
            return
        
        if self.device.set_device_time():
            QMessageBox.information(self, "Succès", "Heure synchronisée avec succès.")
        else:
            QMessageBox.warning(self, "Erreur", "Échec de la synchronisation de l'heure.")
    
    def restart_device(self):
        """Redémarrer le périphérique"""
        if not self.connected:
            QMessageBox.warning(self, "Non connecté", "Veuillez vous connecter au périphérique.")
            return
        
        reply = QMessageBox.question(
            self, "Confirmation",
            "Voulez-vous vraiment redémarrer le périphérique ?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.device.restart()
            self.disconnect_device()
            QMessageBox.information(self, "Info", "Le périphérique redémarre...")
    
    def update_time(self):
        """Mettre à jour l'heure dans la barre de statut"""
        self.time_label.setText(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    
    def show_about(self):
        """Afficher la boîte À propos"""
        QMessageBox.about(self, "À propos",
            """<h2>ZKTeco iClock Manager</h2>
            <p>Version 1.0.0</p>
            <p>Application de gestion pour pointeuse biométrique ZKTeco iClock 580.</p>
            <p>Fonctionnalités:</p>
            <ul>
            <li>Gestion des utilisateurs</li>
            <li>Gestion des empreintes digitales</li>
            <li>Synchronisation des pointages</li>
            <li>Rapports et statistiques</li>
            <li>Export Excel/PDF</li>
            </ul>
            """)
    
    def closeEvent(self, event):
        """Gérer la fermeture de l'application"""
        # Se déconnecter du périphérique
        if self.connected and self.device:
            self.device.disconnect()
        
        # Fermer la base de données
        self.db.close()
        
        event.accept()
