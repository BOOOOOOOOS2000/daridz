#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire de base de données SQLite pour ZKTeco iClock Manager
Gère les utilisateurs, pointages, départements et configurations
"""

import sqlite3
import os
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Optional, Tuple, Any
import json
import threading


class DatabaseManager:
    """Gestionnaire de base de données thread-safe"""
    
    def __init__(self, db_path: str):
        """Initialiser le gestionnaire de base de données"""
        self.db_path = db_path
        self._local = threading.local()
        self._init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Obtenir une connexion thread-safe"""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            self._local.connection.row_factory = sqlite3.Row
            # Activer les clés étrangères
            self._local.connection.execute("PRAGMA foreign_keys = ON")
        return self._local.connection
    
    @property
    def conn(self) -> sqlite3.Connection:
        """Propriété pour accéder à la connexion"""
        return self._get_connection()
    
    def _init_database(self):
        """Initialiser la structure de la base de données"""
        cursor = self.conn.cursor()
        
        # Table des départements
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table des utilisateurs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                uid INTEGER UNIQUE,
                name TEXT NOT NULL,
                privilege INTEGER DEFAULT 0,
                password TEXT,
                card TEXT,
                group_id INTEGER,
                department_id INTEGER,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (department_id) REFERENCES departments(id)
            )
        ''')
        
        # Table des empreintes digitales
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fingerprints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                finger_index INTEGER NOT NULL,
                template BLOB,
                template_size INTEGER,
                validity INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, finger_index)
            )
        ''')
        
        # Table des pointages
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                uid INTEGER,
                timestamp TIMESTAMP NOT NULL,
                status INTEGER DEFAULT 0,
                verify_type INTEGER DEFAULT 0,
                work_code INTEGER DEFAULT 0,
                terminal_id TEXT,
                sync_status INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Index pour les pointages
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_attendance_user_id 
            ON attendance(user_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_attendance_timestamp 
            ON attendance(timestamp)
        ''')
        
        # Table des horaires
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
                grace_period INTEGER DEFAULT 15,
                check_in_start TIME,
                check_in_end TIME,
                check_out_start TIME,
                check_out_end TIME,
                is_default INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table d'affectation des horaires aux utilisateurs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                schedule_id INTEGER NOT NULL,
                day_of_week INTEGER DEFAULT -1,
                effective_date DATE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (schedule_id) REFERENCES schedules(id) ON DELETE CASCADE
            )
        ''')
        
        # Table des jours fériés
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS holidays (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                date DATE NOT NULL UNIQUE,
                is_recurring INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table de configuration
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table de logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT DEFAULT 'INFO',
                message TEXT,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insérer les configurations par défaut
        default_settings = {
            'device_ip': '192.168.1.201',
            'device_port': '4370',
            'device_timeout': '30',
            'auto_sync': '0',
            'sync_interval': '30',
            'language': 'fr',
            'theme': 'default',
            'company_name': 'Ma Société',
            'export_path': os.path.expanduser('~/Documents/ZKTeco'),
            'date_format': 'DD/MM/YYYY',
            'time_format': 'HH:MM'
        }
        
        for key, value in default_settings.items():
            cursor.execute('''
                INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)
            ''', (key, value))
        
        # Insérer un département par défaut
        cursor.execute('''
            INSERT OR IGNORE INTO departments (id, name, description)
            VALUES (1, 'Général', 'Département par défaut')
        ''')
        
        # Insérer des horaires par défaut
        default_schedules = [
            ('Standard', '08:00', '17:00', 15, '07:00', '09:00', '16:00', '18:00', 1),
            ('Matin', '06:00', '14:00', 15, '05:00', '07:00', '13:00', '15:00', 0),
            ('Après-midi', '14:00', '22:00', 15, '13:00', '15:00', '21:00', '23:00', 0),
            ('Nuit', '22:00', '06:00', 15, '21:00', '23:00', '05:00', '07:00', 0),
        ]
        
        for schedule in default_schedules:
            cursor.execute('''
                INSERT OR IGNORE INTO schedules (name, start_time, end_time, grace_period,
                    check_in_start, check_in_end, check_out_start, check_out_end, is_default)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', schedule)
        
        self.conn.commit()
    
    # ==================== GESTION DES PARAMÈTRES ====================
    
    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Récupérer un paramètre"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row['value'] if row else default
    
    def set_setting(self, key: str, value: str):
        """Définir un paramètre"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, value))
        self.conn.commit()
    
    def get_all_settings(self) -> Dict[str, str]:
        """Récupérer tous les paramètres"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        return {row['key']: row['value'] for row in cursor.fetchall()}
    
    # ==================== GESTION DES DÉPARTEMENTS ====================
    
    def add_department(self, name: str, description: str = None) -> int:
        """Ajouter un département"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO departments (name, description)
            VALUES (?, ?)
        ''', (name, description))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_department(self, dept_id: int, name: str, description: str = None):
        """Mettre à jour un département"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE departments 
            SET name = ?, description = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (name, description, dept_id))
        self.conn.commit()
    
    def delete_department(self, dept_id: int):
        """Supprimer un département"""
        cursor = self.conn.cursor()
        # Déplacer les utilisateurs vers le département par défaut
        cursor.execute('''
            UPDATE users SET department_id = 1 WHERE department_id = ?
        ''', (dept_id,))
        cursor.execute("DELETE FROM departments WHERE id = ? AND id != 1", (dept_id,))
        self.conn.commit()
    
    def get_department(self, dept_id: int) -> Optional[Dict]:
        """Récupérer un département"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM departments WHERE id = ?", (dept_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_departments(self) -> List[Dict]:
        """Récupérer tous les départements"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM departments ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_department_users_count(self, dept_id: int) -> int:
        """Compter les utilisateurs d'un département"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE department_id = ?", (dept_id,))
        return cursor.fetchone()['count']
    
    # ==================== GESTION DES UTILISATEURS ====================
    
    def add_user(self, user_id: int, uid: int, name: str, privilege: int = 0,
                 password: str = None, card: str = None, group_id: int = None,
                 department_id: int = 1) -> bool:
        """Ajouter un utilisateur"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO users (id, uid, name, privilege, password, card, group_id, department_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, uid, name, privilege, password, card, group_id, department_id))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def update_user(self, user_id: int, name: str = None, privilege: int = None,
                    password: str = None, card: str = None, group_id: int = None,
                    department_id: int = None, is_active: int = None):
        """Mettre à jour un utilisateur"""
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if privilege is not None:
            updates.append("privilege = ?")
            params.append(privilege)
        if password is not None:
            updates.append("password = ?")
            params.append(password)
        if card is not None:
            updates.append("card = ?")
            params.append(card)
        if group_id is not None:
            updates.append("group_id = ?")
            params.append(group_id)
        if department_id is not None:
            updates.append("department_id = ?")
            params.append(department_id)
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(is_active)
        
        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(user_id)
            cursor = self.conn.cursor()
            cursor.execute(f'''
                UPDATE users SET {', '.join(updates)} WHERE id = ?
            ''', params)
            self.conn.commit()
    
    def delete_user(self, user_id: int):
        """Supprimer un utilisateur"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        self.conn.commit()
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Récupérer un utilisateur"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT u.*, d.name as department_name
            FROM users u
            LEFT JOIN departments d ON u.department_id = d.id
            WHERE u.id = ?
        ''', (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_user_by_uid(self, uid: int) -> Optional[Dict]:
        """Récupérer un utilisateur par son UID"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT u.*, d.name as department_name
            FROM users u
            LEFT JOIN departments d ON u.department_id = d.id
            WHERE u.uid = ?
        ''', (uid,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_users(self, include_inactive: bool = False) -> List[Dict]:
        """Récupérer tous les utilisateurs"""
        cursor = self.conn.cursor()
        if include_inactive:
            cursor.execute('''
                SELECT u.*, d.name as department_name
                FROM users u
                LEFT JOIN departments d ON u.department_id = d.id
                ORDER BY u.name
            ''')
        else:
            cursor.execute('''
                SELECT u.*, d.name as department_name
                FROM users u
                LEFT JOIN departments d ON u.department_id = d.id
                WHERE u.is_active = 1
                ORDER BY u.name
            ''')
        return [dict(row) for row in cursor.fetchall()]
    
    def get_users_by_department(self, dept_id: int) -> List[Dict]:
        """Récupérer les utilisateurs d'un département"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM users WHERE department_id = ? ORDER BY name
        ''', (dept_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_next_uid(self) -> int:
        """Obtenir le prochain UID disponible"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX(uid) as max_uid FROM users")
        row = cursor.fetchone()
        return (row['max_uid'] or 0) + 1
    
    def search_users(self, query: str) -> List[Dict]:
        """Rechercher des utilisateurs"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT u.*, d.name as department_name
            FROM users u
            LEFT JOIN departments d ON u.department_id = d.id
            WHERE u.name LIKE ? OR CAST(u.id AS TEXT) LIKE ? OR u.card LIKE ?
            ORDER BY u.name
        ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_users_count(self, active_only: bool = True) -> int:
        """Compter les utilisateurs"""
        cursor = self.conn.cursor()
        if active_only:
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE is_active = 1")
        else:
            cursor.execute("SELECT COUNT(*) as count FROM users")
        return cursor.fetchone()['count']
    
    # ==================== GESTION DES EMPREINTES ====================
    
    def save_fingerprint(self, user_id: int, finger_index: int, template: bytes,
                        template_size: int, validity: int = 1):
        """Sauvegarder une empreinte digitale"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO fingerprints 
            (user_id, finger_index, template, template_size, validity)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, finger_index, template, template_size, validity))
        self.conn.commit()
    
    def get_fingerprint(self, user_id: int, finger_index: int) -> Optional[Dict]:
        """Récupérer une empreinte"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM fingerprints WHERE user_id = ? AND finger_index = ?
        ''', (user_id, finger_index))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_user_fingerprints(self, user_id: int) -> List[Dict]:
        """Récupérer toutes les empreintes d'un utilisateur"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM fingerprints WHERE user_id = ? ORDER BY finger_index
        ''', (user_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def delete_fingerprint(self, user_id: int, finger_index: int):
        """Supprimer une empreinte"""
        cursor = self.conn.cursor()
        cursor.execute('''
            DELETE FROM fingerprints WHERE user_id = ? AND finger_index = ?
        ''', (user_id, finger_index))
        self.conn.commit()
    
    def delete_user_fingerprints(self, user_id: int):
        """Supprimer toutes les empreintes d'un utilisateur"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM fingerprints WHERE user_id = ?", (user_id,))
        self.conn.commit()
    
    def count_user_fingerprints(self, user_id: int) -> int:
        """Compter les empreintes d'un utilisateur"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as count FROM fingerprints WHERE user_id = ?
        ''', (user_id,))
        return cursor.fetchone()['count']
    
    # ==================== GESTION DES POINTAGES ====================
    
    def add_attendance(self, user_id: int, uid: int, timestamp: datetime,
                      status: int = 0, verify_type: int = 0, work_code: int = 0,
                      terminal_id: str = None) -> int:
        """Ajouter un pointage"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO attendance 
            (user_id, uid, timestamp, status, verify_type, work_code, terminal_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, uid, timestamp, status, verify_type, work_code, terminal_id))
        self.conn.commit()
        return cursor.lastrowid
    
    def bulk_add_attendance(self, records: List[Dict]):
        """Ajouter plusieurs pointages"""
        cursor = self.conn.cursor()
        for record in records:
            cursor.execute('''
                INSERT OR IGNORE INTO attendance 
                (user_id, uid, timestamp, status, verify_type, work_code, terminal_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                record.get('user_id'),
                record.get('uid'),
                record.get('timestamp'),
                record.get('status', 0),
                record.get('verify_type', 0),
                record.get('work_code', 0),
                record.get('terminal_id')
            ))
        self.conn.commit()
    
    def get_attendance(self, attendance_id: int) -> Optional[Dict]:
        """Récupérer un pointage"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT a.*, u.name as user_name
            FROM attendance a
            LEFT JOIN users u ON a.user_id = u.id
            WHERE a.id = ?
        ''', (attendance_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_user_attendance(self, user_id: int, start_date: date = None,
                           end_date: date = None) -> List[Dict]:
        """Récupérer les pointages d'un utilisateur"""
        cursor = self.conn.cursor()
        
        query = '''
            SELECT a.*, u.name as user_name
            FROM attendance a
            LEFT JOIN users u ON a.user_id = u.id
            WHERE a.user_id = ?
        '''
        params = [user_id]
        
        if start_date:
            query += " AND DATE(a.timestamp) >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND DATE(a.timestamp) <= ?"
            params.append(end_date)
        
        query += " ORDER BY a.timestamp"
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_attendance_by_date(self, target_date: date) -> List[Dict]:
        """Récupérer les pointages d'une date"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT a.*, u.name as user_name, d.name as department_name
            FROM attendance a
            LEFT JOIN users u ON a.user_id = u.id
            LEFT JOIN departments d ON u.department_id = d.id
            WHERE DATE(a.timestamp) = ?
            ORDER BY u.name, a.timestamp
        ''', (target_date,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_attendance_range(self, start_date: date, end_date: date,
                            department_id: int = None) -> List[Dict]:
        """Récupérer les pointages d'une période"""
        cursor = self.conn.cursor()
        
        if department_id:
            cursor.execute('''
                SELECT a.*, u.name as user_name, d.name as department_name
                FROM attendance a
                LEFT JOIN users u ON a.user_id = u.id
                LEFT JOIN departments d ON u.department_id = d.id
                WHERE DATE(a.timestamp) >= ? AND DATE(a.timestamp) <= ?
                AND u.department_id = ?
                ORDER BY a.timestamp
            ''', (start_date, end_date, department_id))
        else:
            cursor.execute('''
                SELECT a.*, u.name as user_name, d.name as department_name
                FROM attendance a
                LEFT JOIN users u ON a.user_id = u.id
                LEFT JOIN departments d ON u.department_id = d.id
                WHERE DATE(a.timestamp) >= ? AND DATE(a.timestamp) <= ?
                ORDER BY a.timestamp
            ''', (start_date, end_date))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_last_attendance_timestamp(self) -> Optional[datetime]:
        """Récupérer le dernier timestamp de pointage"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX(timestamp) as max_time FROM attendance")
        row = cursor.fetchone()
        return datetime.fromisoformat(row['max_time']) if row['max_time'] else None
    
    def delete_attendance(self, attendance_id: int):
        """Supprimer un pointage"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM attendance WHERE id = ?", (attendance_id,))
        self.conn.commit()
    
    def clear_attendance(self, before_date: date = None):
        """Effacer les pointages"""
        cursor = self.conn.cursor()
        if before_date:
            cursor.execute("DELETE FROM attendance WHERE DATE(timestamp) < ?", (before_date,))
        else:
            cursor.execute("DELETE FROM attendance")
        self.conn.commit()
    
    def get_attendance_count(self, user_id: int = None) -> int:
        """Compter les pointages"""
        cursor = self.conn.cursor()
        if user_id:
            cursor.execute("SELECT COUNT(*) as count FROM attendance WHERE user_id = ?", (user_id,))
        else:
            cursor.execute("SELECT COUNT(*) as count FROM attendance")
        return cursor.fetchone()['count']
    
    # ==================== GESTION DES HORAIRES ====================
    
    def add_schedule(self, name: str, start_time: str, end_time: str,
                    grace_period: int = 15, check_in_start: str = None,
                    check_in_end: str = None, check_out_start: str = None,
                    check_out_end: str = None, is_default: bool = False) -> int:
        """Ajouter un horaire"""
        cursor = self.conn.cursor()
        
        if is_default:
            cursor.execute("UPDATE schedules SET is_default = 0")
        
        cursor.execute('''
            INSERT INTO schedules 
            (name, start_time, end_time, grace_period, check_in_start, check_in_end,
             check_out_start, check_out_end, is_default)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, start_time, end_time, grace_period, check_in_start,
              check_in_end, check_out_start, check_out_end, 1 if is_default else 0))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_schedule(self, schedule_id: int, **kwargs):
        """Mettre à jour un horaire"""
        allowed = ['name', 'start_time', 'end_time', 'grace_period',
                   'check_in_start', 'check_in_end', 'check_out_start', 'check_out_end', 'is_default']
        
        updates = []
        params = []
        
        for key, value in kwargs.items():
            if key in allowed:
                if key == 'is_default':
                    value = 1 if value else 0
                updates.append(f"{key} = ?")
                params.append(value)
        
        if updates:
            params.append(schedule_id)
            cursor = self.conn.cursor()
            cursor.execute(f'''
                UPDATE schedules SET {', '.join(updates)} WHERE id = ?
            ''', params)
            self.conn.commit()
    
    def delete_schedule(self, schedule_id: int):
        """Supprimer un horaire"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM user_schedules WHERE schedule_id = ?", (schedule_id,))
        cursor.execute("DELETE FROM schedules WHERE id = ? AND is_default = 0", (schedule_id,))
        self.conn.commit()
    
    def get_schedule(self, schedule_id: int) -> Optional[Dict]:
        """Récupérer un horaire"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM schedules WHERE id = ?", (schedule_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_schedules(self) -> List[Dict]:
        """Récupérer tous les horaires"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM schedules ORDER BY is_default DESC, name")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_default_schedule(self) -> Optional[Dict]:
        """Récupérer l'horaire par défaut"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM schedules WHERE is_default = 1")
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def assign_user_schedule(self, user_id: int, schedule_id: int,
                            day_of_week: int = -1, effective_date: date = None):
        """Assigner un horaire à un utilisateur"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO user_schedules
            (user_id, schedule_id, day_of_week, effective_date)
            VALUES (?, ?, ?, ?)
        ''', (user_id, schedule_id, day_of_week, effective_date))
        self.conn.commit()
    
    def get_user_schedule(self, user_id: int, day_of_week: int = None) -> Optional[Dict]:
        """Récupérer l'horaire d'un utilisateur"""
        cursor = self.conn.cursor()
        
        if day_of_week is not None:
            cursor.execute('''
                SELECT s.* FROM schedules s
                JOIN user_schedules us ON s.id = us.schedule_id
                WHERE us.user_id = ? AND (us.day_of_week = ? OR us.day_of_week = -1)
                ORDER BY us.day_of_week DESC
                LIMIT 1
            ''', (user_id, day_of_week))
        else:
            cursor.execute('''
                SELECT s.* FROM schedules s
                JOIN user_schedules us ON s.id = us.schedule_id
                WHERE us.user_id = ?
                LIMIT 1
            ''', (user_id,))
        
        row = cursor.fetchone()
        if row:
            return dict(row)
        
        return self.get_default_schedule()
    
    # ==================== GESTION DES JOURS FÉRIÉS ====================
    
    def add_holiday(self, name: str, date_val: date, is_recurring: bool = False) -> int:
        """Ajouter un jour férié"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO holidays (name, date, is_recurring)
            VALUES (?, ?, ?)
        ''', (name, date_val, 1 if is_recurring else 0))
        self.conn.commit()
        return cursor.lastrowid
    
    def delete_holiday(self, holiday_id: int):
        """Supprimer un jour férié"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM holidays WHERE id = ?", (holiday_id,))
        self.conn.commit()
    
    def get_all_holidays(self, year: int = None) -> List[Dict]:
        """Récupérer tous les jours fériés"""
        cursor = self.conn.cursor()
        
        if year:
            cursor.execute('''
                SELECT * FROM holidays
                WHERE strftime('%Y', date) = ? OR is_recurring = 1
                ORDER BY date
            ''', (str(year),))
        else:
            cursor.execute("SELECT * FROM holidays ORDER BY date")
        
        return [dict(row) for row in cursor.fetchall()]
    
    def is_holiday(self, date_val: date) -> Tuple[bool, Optional[str]]:
        """Vérifier si une date est un jour férié"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT name FROM holidays
            WHERE date = ? OR (is_recurring = 1 AND strftime('%m-%d', date) = ?)
        ''', (date_val, date_val.strftime('%m-%d')))
        row = cursor.fetchone()
        return (True, row['name']) if row else (False, None)
    
    # ==================== LOGS ====================
    
    def add_log(self, level: str, message: str, details: str = None):
        """Ajouter une entrée de log"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO logs (level, message, details)
            VALUES (?, ?, ?)
        ''', (level, message, details))
        self.conn.commit()
    
    def get_logs(self, limit: int = 100, level: str = None) -> List[Dict]:
        """Récupérer les logs"""
        cursor = self.conn.cursor()
        
        if level:
            cursor.execute('''
                SELECT * FROM logs WHERE level = ?
                ORDER BY created_at DESC LIMIT ?
            ''', (level, limit))
        else:
            cursor.execute('''
                SELECT * FROM logs ORDER BY created_at DESC LIMIT ?
            ''', (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def clear_logs(self):
        """Effacer tous les logs"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM logs")
        self.conn.commit()
    
    # ==================== STATISTIQUES ====================
    
    def get_daily_stats(self, target_date: date) -> Dict:
        """Obtenir les statistiques d'un jour"""
        cursor = self.conn.cursor()
        
        stats = {}
        
        # Total des utilisateurs actifs
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE is_active = 1")
        stats['total_users'] = cursor.fetchone()['count']
        
        # Pointages du jour
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) as count
            FROM attendance
            WHERE DATE(timestamp) = ?
        ''', (target_date,))
        stats['present'] = cursor.fetchone()['count']
        
        # Absents
        stats['absent'] = stats['total_users'] - stats['present']
        
        # Retards (après l'heure de début + période de grâce)
        cursor.execute('''
            SELECT COUNT(*) as count FROM (
                SELECT user_id, MIN(TIME(timestamp)) as first_check
                FROM attendance
                WHERE DATE(timestamp) = ?
                GROUP BY user_id
            )
        ''', (target_date,))
        stats['on_time'] = cursor.fetchone()['count']
        
        return stats
    
    def get_monthly_stats(self, year: int, month: int, user_id: int = None) -> Dict:
        """Obtenir les statistiques mensuelles"""
        cursor = self.conn.cursor()
        
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        stats = {
            'year': year,
            'month': month,
            'start_date': start_date,
            'end_date': end_date,
            'total_days': (end_date - start_date).days + 1,
            'working_days': 0,
            'total_pointages': 0,
            'avg_check_in': None,
            'avg_check_out': None
        }
        
        # Calculer les jours ouvrés
        current = start_date
        while current <= end_date:
            if current.weekday() < 5:  # Lundi à vendredi
                is_hol, _ = self.is_holiday(current)
                if not is_hol:
                    stats['working_days'] += 1
            current += timedelta(days=1)
        
        # Total des pointages
        if user_id:
            cursor.execute('''
                SELECT COUNT(*) as count FROM attendance
                WHERE user_id = ? AND DATE(timestamp) >= ? AND DATE(timestamp) <= ?
            ''', (user_id, start_date, end_date))
        else:
            cursor.execute('''
                SELECT COUNT(*) as count FROM attendance
                WHERE DATE(timestamp) >= ? AND DATE(timestamp) <= ?
            ''', (start_date, end_date))
        
        stats['total_pointages'] = cursor.fetchone()['count']
        
        return stats
    
    # ==================== UTILITAIRES ====================
    
    def backup_database(self, backup_path: str):
        """Sauvegarder la base de données"""
        import shutil
        self.conn.commit()
        shutil.copy2(self.db_path, backup_path)
    
    def vacuum_database(self):
        """Optimiser la base de données"""
        cursor = self.conn.cursor()
        cursor.execute("VACUUM")
        self.conn.commit()
    
    def close(self):
        """Fermer la connexion"""
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
            del self._local.connection
