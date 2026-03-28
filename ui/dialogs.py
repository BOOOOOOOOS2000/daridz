#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dialogues pour l'édition des données
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QSpinBox, QCheckBox, QDialogButtonBox,
    QDateEdit, QTimeEdit, QTextEdit, QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt, QDate, QTime


class UserDialog(QDialog):
    """Dialogue pour ajouter/modifier un utilisateur"""
    
    def __init__(self, db_manager, user_id=None, parent=None):
        super().__init__(parent)
        
        self.db = db_manager
        self.user_id = user_id
        
        self.setup_ui()
        
        if user_id:
            self.load_user()
    
    def setup_ui(self):
        """Configurer l'interface"""
        self.setWindowTitle("Utilisateur")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Formulaire
        form_group = QGroupBox("Informations utilisateur")
        form_layout = QFormLayout(form_group)
        
        # ID utilisateur
        self.id_spin = QSpinBox()
        self.id_spin.setRange(1, 999999)
        if not self.user_id:
            self.id_spin.setValue(self.db.get_next_uid())
        form_layout.addRow("ID employé:", self.id_spin)
        
        # Nom
        self.name_edit = QLineEdit()
        form_layout.addRow("Nom complet:", self.name_edit)
        
        # Privilège
        self.privilege_combo = QComboBox()
        self.privilege_combo.addItem("Utilisateur", 0)
        self.privilege_combo.addItem("Enregistreur", 2)
        self.privilege_combo.addItem("Gestionnaire", 3)
        self.privilege_combo.addItem("Super Admin", 6)
        form_layout.addRow("Privilège:", self.privilege_combo)
        
        # Mot de passe
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Mot de passe:", self.password_edit)
        
        # Carte
        self.card_edit = QLineEdit()
        form_layout.addRow("Numéro de carte:", self.card_edit)
        
        # Département
        self.dept_combo = QComboBox()
        departments = self.db.get_all_departments()
        for dept in departments:
            self.dept_combo.addItem(dept['name'], dept['id'])
        form_layout.addRow("Département:", self.dept_combo)
        
        # Actif
        self.active_check = QCheckBox()
        self.active_check.setChecked(True)
        form_layout.addRow("Actif:", self.active_check)
        
        layout.addWidget(form_group)
        
        # Boutons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.save)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
    
    def load_user(self):
        """Charger les données de l'utilisateur"""
        user = self.db.get_user(self.user_id)
        
        if user:
            self.id_spin.setValue(user['id'])
            self.name_edit.setText(user['name'])
            
            # Privilège
            index = self.privilege_combo.findData(user.get('privilege', 0))
            if index >= 0:
                self.privilege_combo.setCurrentIndex(index)
            
            self.password_edit.setText(user.get('password') or '')
            self.card_edit.setText(user.get('card') or '')
            
            # Département
            index = self.dept_combo.findData(user.get('department_id', 1))
            if index >= 0:
                self.dept_combo.setCurrentIndex(index)
            
            self.active_check.setChecked(user.get('is_active', 1) == 1)
    
    def save(self):
        """Sauvegarder l'utilisateur"""
        name = self.name_edit.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Erreur", "Le nom est obligatoire.")
            return
        
        try:
            if self.user_id:
                # Mise à jour
                self.db.update_user(
                    self.user_id,
                    name=name,
                    privilege=self.privilege_combo.currentData(),
                    password=self.password_edit.text() or None,
                    card=self.card_edit.text() or None,
                    department_id=self.dept_combo.currentData(),
                    is_active=1 if self.active_check.isChecked() else 0
                )
            else:
                # Création
                self.db.add_user(
                    user_id=self.id_spin.value(),
                    uid=self.id_spin.value(),
                    name=name,
                    privilege=self.privilege_combo.currentData(),
                    password=self.password_edit.text() or None,
                    card=self.card_edit.text() or None,
                    department_id=self.dept_combo.currentData()
                )
            
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde:\n{str(e)}")


class DepartmentDialog(QDialog):
    """Dialogue pour ajouter/modifier un département"""
    
    def __init__(self, db_manager, dept_id=None, parent=None):
        super().__init__(parent)
        
        self.db = db_manager
        self.dept_id = dept_id
        
        self.setup_ui()
        
        if dept_id:
            self.load_department()
    
    def setup_ui(self):
        """Configurer l'interface"""
        self.setWindowTitle("Département")
        self.setMinimumWidth(350)
        
        layout = QVBoxLayout(self)
        
        # Formulaire
        form_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        form_layout.addRow("Nom:", self.name_edit)
        
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(80)
        form_layout.addRow("Description:", self.desc_edit)
        
        layout.addLayout(form_layout)
        
        # Boutons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.save)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
    
    def load_department(self):
        """Charger les données du département"""
        dept = self.db.get_department(self.dept_id)
        
        if dept:
            self.name_edit.setText(dept['name'])
            self.desc_edit.setText(dept.get('description') or '')
    
    def save(self):
        """Sauvegarder le département"""
        name = self.name_edit.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Erreur", "Le nom est obligatoire.")
            return
        
        try:
            if self.dept_id:
                self.db.update_department(self.dept_id, name, self.desc_edit.toPlainText() or None)
            else:
                self.db.add_department(name, self.desc_edit.toPlainText() or None)
            
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde:\n{str(e)}")


class ScheduleDialog(QDialog):
    """Dialogue pour ajouter/modifier un horaire"""
    
    def __init__(self, db_manager, schedule_id=None, parent=None):
        super().__init__(parent)
        
        self.db = db_manager
        self.schedule_id = schedule_id
        
        self.setup_ui()
        
        if schedule_id:
            self.load_schedule()
    
    def setup_ui(self):
        """Configurer l'interface"""
        self.setWindowTitle("Horaire")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Formulaire
        form_group = QGroupBox("Configuration de l'horaire")
        form_layout = QFormLayout(form_group)
        
        # Nom
        self.name_edit = QLineEdit()
        form_layout.addRow("Nom:", self.name_edit)
        
        # Heures de début et fin
        time_layout = QHBoxLayout()
        
        self.start_time = QTimeEdit()
        self.start_time.setTime(QTime(8, 0))
        time_layout.addWidget(QLabel("Début:"))
        time_layout.addWidget(self.start_time)
        
        self.end_time = QTimeEdit()
        self.end_time.setTime(QTime(17, 0))
        time_layout.addWidget(QLabel("Fin:"))
        time_layout.addWidget(self.end_time)
        
        form_layout.addRow("Horaires:", time_layout)
        
        # Période de grâce
        self.grace_spin = QSpinBox()
        self.grace_spin.setRange(0, 60)
        self.grace_spin.setValue(15)
        form_layout.addRow("Période de grâce (min):", self.grace_spin)
        
        # Plages de pointage
        checkin_group = QGroupBox("Plages de pointage")
        checkin_layout = QFormLayout(checkin_group)
        
        # Entrée
        entry_layout = QHBoxLayout()
        self.entry_start = QTimeEdit()
        self.entry_start.setTime(QTime(7, 0))
        self.entry_end = QTimeEdit()
        self.entry_end.setTime(QTime(9, 0))
        entry_layout.addWidget(self.entry_start)
        entry_layout.addWidget(QLabel("à"))
        entry_layout.addWidget(self.entry_end)
        checkin_layout.addRow("Entrée:", entry_layout)
        
        # Sortie
        exit_layout = QHBoxLayout()
        self.exit_start = QTimeEdit()
        self.exit_start.setTime(QTime(16, 0))
        self.exit_end = QTimeEdit()
        self.exit_end.setTime(QTime(18, 0))
        exit_layout.addWidget(self.exit_start)
        exit_layout.addWidget(QLabel("à"))
        exit_layout.addWidget(self.exit_end)
        checkin_layout.addRow("Sortie:", exit_layout)
        
        layout.addWidget(form_group)
        layout.addWidget(checkin_group)
        
        # Défaut
        self.default_check = QCheckBox("Définir comme horaire par défaut")
        layout.addWidget(self.default_check)
        
        # Boutons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.save)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
    
    def load_schedule(self):
        """Charger les données de l'horaire"""
        schedule = self.db.get_schedule(self.schedule_id)
        
        if schedule:
            self.name_edit.setText(schedule['name'])
            
            # Parser les temps
            start = schedule.get('start_time')
            if start:
                self.start_time.setTime(QTime.fromString(str(start), 'HH:mm:ss'))
            
            end = schedule.get('end_time')
            if end:
                self.end_time.setTime(QTime.fromString(str(end), 'HH:mm:ss'))
            
            self.grace_spin.setValue(schedule.get('grace_period', 15))
            self.default_check.setChecked(schedule.get('is_default', False))
    
    def save(self):
        """Sauvegarder l'horaire"""
        name = self.name_edit.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Erreur", "Le nom est obligatoire.")
            return
        
        try:
            start = self.start_time.time().toString('HH:mm:ss')
            end = self.end_time.time().toString('HH:mm:ss')
            entry_start = self.entry_start.time().toString('HH:mm:ss')
            entry_end = self.entry_end.time().toString('HH:mm:ss')
            exit_start = self.exit_start.time().toString('HH:mm:ss')
            exit_end = self.exit_end.time().toString('HH:mm:ss')
            
            if self.schedule_id:
                self.db.update_schedule(
                    self.schedule_id,
                    name=name,
                    start_time=start,
                    end_time=end,
                    grace_period=self.grace_spin.value(),
                    check_in_start=entry_start,
                    check_in_end=entry_end,
                    check_out_start=exit_start,
                    check_out_end=exit_end,
                    is_default=self.default_check.isChecked()
                )
            else:
                self.db.add_schedule(
                    name=name,
                    start_time=start,
                    end_time=end,
                    grace_period=self.grace_spin.value(),
                    check_in_start=entry_start,
                    check_in_end=entry_end,
                    check_out_start=exit_start,
                    check_out_end=exit_end,
                    is_default=self.default_check.isChecked()
                )
            
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde:\n{str(e)}")


class HolidayDialog(QDialog):
    """Dialogue pour ajouter/modifier un jour férié"""
    
    def __init__(self, db_manager, holiday_id=None, parent=None):
        super().__init__(parent)
        
        self.db = db_manager
        self.holiday_id = holiday_id
        
        self.setup_ui()
        
        if holiday_id:
            self.load_holiday()
    
    def setup_ui(self):
        """Configurer l'interface"""
        self.setWindowTitle("Jour férié")
        self.setMinimumWidth(300)
        
        layout = QVBoxLayout(self)
        
        # Formulaire
        form_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        form_layout.addRow("Nom:", self.name_edit)
        
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        form_layout.addRow("Date:", self.date_edit)
        
        self.recurring_check = QCheckBox("Récurrent (chaque année)")
        form_layout.addRow("", self.recurring_check)
        
        layout.addLayout(form_layout)
        
        # Boutons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.save)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
    
    def load_holiday(self):
        """Charger les données du jour férié"""
        # TODO: Implémenter le chargement
        pass
    
    def save(self):
        """Sauvegarder le jour férié"""
        name = self.name_edit.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Erreur", "Le nom est obligatoire.")
            return
        
        try:
            self.db.add_holiday(
                name=name,
                date_val=self.date_edit.date().toPyDate(),
                is_recurring=self.recurring_check.isChecked()
            )
            
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde:\n{str(e)}")


class ConnectionDialog(QDialog):
    """Dialogue pour configurer la connexion"""
    
    def __init__(self, parent=None, ip='192.168.1.201', port=4370):
        super().__init__(parent)
        
        self.ip = ip
        self.port = port
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configurer l'interface"""
        self.setWindowTitle("Configuration de connexion")
        self.setMinimumWidth(300)
        
        layout = QVBoxLayout(self)
        
        # Formulaire
        form_layout = QFormLayout()
        
        self.ip_edit = QLineEdit(self.ip)
        form_layout.addRow("Adresse IP:", self.ip_edit)
        
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(self.port)
        form_layout.addRow("Port:", self.port_spin)
        
        layout.addLayout(form_layout)
        
        # Boutons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
    
    def get_values(self):
        """Obtenir les valeurs saisies"""
        return (self.ip_edit.text(), self.port_spin.value())
