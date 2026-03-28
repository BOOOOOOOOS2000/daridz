#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fonctions utilitaires pour ZKTeco Manager
"""

import os
import sys
from datetime import datetime, date, time, timedelta
from typing import Optional, List, Dict, Any


def get_resource_path(relative_path: str) -> str:
    """
    Obtenir le chemin absolu d'une ressource.
    Fonctionne en mode développement et en mode empaqueté (PyInstaller).
    
    Args:
        relative_path: Chemin relatif vers la ressource
    
    Returns:
        str: Chemin absolu
    """
    if hasattr(sys, '_MEIPASS'):
        # Mode PyInstaller
        return os.path.join(sys._MEIPASS, relative_path)
    
    # Mode développement
    return os.path.join(os.path.dirname(__file__), '..', relative_path)


def format_datetime(dt: datetime, fmt: str = '%d/%m/%Y %H:%M:%S') -> str:
    """
    Formater une date/heure.
    
    Args:
        dt: Objet datetime
        fmt: Format de sortie
    
    Returns:
        str: Date formatée
    """
    if dt is None:
        return ''
    
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except ValueError:
            return dt
    
    return dt.strftime(fmt)


def format_time_delta(td: timedelta) -> str:
    """
    Formater une durée.
    
    Args:
        td: Objet timedelta
    
    Returns:
        str: Durée formatée (ex: "2h 30min")
    """
    if td is None:
        return ''
    
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    
    if hours > 0:
        return f"{hours}h {minutes}min"
    else:
        return f"{minutes}min"


def parse_time(time_str: str) -> Optional[time]:
    """
    Parser une chaîne de temps.
    
    Args:
        time_str: Chaîne de temps (HH:MM ou HH:MM:SS)
    
    Returns:
        time: Objet time ou None
    """
    if not time_str:
        return None
    
    formats = ['%H:%M:%S', '%H:%M']
    
    for fmt in formats:
        try:
            return datetime.strptime(time_str, fmt).time()
        except ValueError:
            continue
    
    return None


def calculate_work_hours(check_in: datetime, check_out: datetime,
                        break_duration: timedelta = None) -> float:
    """
    Calculer les heures travaillées.
    
    Args:
        check_in: Heure d'entrée
        check_out: Heure de sortie
        break_duration: Durée de la pause
    
    Returns:
        float: Nombre d'heures travaillées
    """
    if not check_in or not check_out:
        return 0.0
    
    if check_out < check_in:
        # La sortie est le lendemain
        check_out += timedelta(days=1)
    
    duration = check_out - check_in
    
    if break_duration:
        duration -= break_duration
    
    return duration.total_seconds() / 3600


def is_late(check_in: datetime, schedule_start: time,
           grace_period: int = 15) -> bool:
    """
    Vérifier si un employé est en retard.
    
    Args:
        check_in: Heure de pointage d'entrée
        schedule_start: Heure de début prévue
        grace_period: Période de grâce en minutes
    
    Returns:
        bool: True si en retard
    """
    if not check_in or not schedule_start:
        return False
    
    check_in_time = check_in.time()
    grace_time = time(
        schedule_start.hour,
        schedule_start.minute + grace_period
    )
    
    return check_in_time > grace_time


def get_week_bounds(target_date: date = None) -> tuple:
    """
    Obtenir les limites de la semaine contenant la date.
    
    Args:
        target_date: Date cible (défaut: aujourd'hui)
    
    Returns:
        tuple: (lundi, dimanche)
    """
    if target_date is None:
        target_date = date.today()
    
    # Trouver le lundi
    monday = target_date - timedelta(days=target_date.weekday())
    sunday = monday + timedelta(days=6)
    
    return (monday, sunday)


def get_month_bounds(year: int = None, month: int = None) -> tuple:
    """
    Obtenir les limites du mois.
    
    Args:
        year: Année (défaut: année actuelle)
        month: Mois (défaut: mois actuel)
    
    Returns:
        tuple: (premier_jour, dernier_jour)
    """
    if year is None or month is None:
        today = date.today()
        year = year or today.year
        month = month or today.month
    
    first_day = date(year, month, 1)
    
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)
    
    return (first_day, last_day)


def get_working_days(start_date: date, end_date: date,
                    holidays: List[date] = None) -> int:
    """
    Calculer le nombre de jours ouvrés dans une période.
    
    Args:
        start_date: Date de début
        end_date: Date de fin
        holidays: Liste des jours fériés
    
    Returns:
        int: Nombre de jours ouvrés
    """
    if holidays is None:
        holidays = []
    
    working_days = 0
    current = start_date
    
    while current <= end_date:
        # Lundi = 0, Vendredi = 4
        if current.weekday() < 5 and current not in holidays:
            working_days += 1
        current += timedelta(days=1)
    
    return working_days


def validate_ip_address(ip: str) -> bool:
    """
    Valider une adresse IP.
    
    Args:
        ip: Adresse IP à valider
    
    Returns:
        bool: True si valide
    """
    if not ip:
        return False
    
    parts = ip.split('.')
    
    if len(parts) != 4:
        return False
    
    try:
        return all(0 <= int(part) <= 255 for part in parts)
    except ValueError:
        return False


def format_file_size(size_bytes: int) -> str:
    """
    Formater une taille de fichier.
    
    Args:
        size_bytes: Taille en octets
    
    Returns:
        str: Taille formatée
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    
    return f"{size_bytes:.1f} TB"


def sanitize_filename(filename: str) -> str:
    """
    Nettoyer un nom de fichier.
    
    Args:
        filename: Nom de fichier à nettoyer
    
    Returns:
        str: Nom de fichier nettoyé
    """
    # Caractères interdits
    forbidden = '<>:"/\\|?*'
    
    for char in forbidden:
        filename = filename.replace(char, '_')
    
    return filename.strip()


def ensure_directory(path: str) -> bool:
    """
    S'assurer qu'un répertoire existe.
    
    Args:
        path: Chemin du répertoire
    
    Returns:
        bool: True si le répertoire existe
    """
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception:
        return False


def get_application_path() -> str:
    """
    Obtenir le chemin de l'application.
    
    Returns:
        str: Chemin de l'application
    """
    if getattr(sys, 'frozen', False):
        # Mode exe
        return os.path.dirname(sys.executable)
    else:
        # Mode script
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_data_path() -> str:
    """
    Obtenir le chemin des données.
    
    Returns:
        str: Chemin du dossier data
    """
    app_path = get_application_path()
    data_path = os.path.join(app_path, 'data')
    ensure_directory(data_path)
    return data_path


def get_export_path() -> str:
    """
    Obtenir le chemin d'export par défaut.
    
    Returns:
        str: Chemin du dossier export
    """
    export_path = os.path.expanduser('~/Documents/ZKTeco')
    ensure_directory(export_path)
    return export_path


# Dictionnaires de traduction
STATUS_NAMES = {
    0: "Entrée",
    1: "Sortie",
    2: "Sortie Pause",
    3: "Retour Pause",
    4: "Entrée H.Sup",
    5: "Sortie H.Sup"
}

VERIFY_TYPE_NAMES = {
    0: "Mot de passe",
    1: "Empreinte",
    2: "Carte",
    3: "Visage",
    4: "Empreinte + PW",
    5: "Visage + PW",
    6: "Empreinte + Carte",
    7: "Visage + Carte"
}

PRIVILEGE_NAMES = {
    0: "Utilisateur",
    2: "Enregistreur",
    3: "Gestionnaire",
    6: "Super Admin"
}

DAY_NAMES = {
    0: "Lundi",
    1: "Mardi",
    2: "Mercredi",
    3: "Jeudi",
    4: "Vendredi",
    5: "Samedi",
    6: "Dimanche"
}

MONTH_NAMES = {
    1: "Janvier",
    2: "Février",
    3: "Mars",
    4: "Avril",
    5: "Mai",
    6: "Juin",
    7: "Juillet",
    8: "Août",
    9: "Septembre",
    10: "Octobre",
    11: "Novembre",
    12: "Décembre"
}
