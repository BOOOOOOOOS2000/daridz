#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Protocole ZK pour communication avec pointeuses ZKTeco
Basé sur le protocole de communication ZKTeco

Ce module implémente le protocole de communication utilisé par les
terminaux biométriques ZKTeco. Il utilise une communication TCP/IP
sur le port 4370 par défaut avec un format de paquet spécifique.
"""

import struct
import socket
import time
import hashlib
from typing import Tuple, Optional, List, Dict, Any
from enum import IntEnum


class ZKCommands(IntEnum):
    """Commandes ZK"""
    # Commandes de base
    CMD_CONNECT = 1000
    CMD_EXIT = 1001
    CMD_ENABLEDEVICE = 1002
    CMD_DISABLEDEVICE = 1003
    CMD_RESTART = 1004
    
    # Commandes utilisateur
    CMD_USER_WRQ = 8
    CMD_USERTEMP_RRQ = 9
    CMD_USERTEMP_WRQ = 10
    CMD_DEL_USER = 18
    CMD_DEL_USER_TEMP = 19
    
    # Commandes de données
    CMD_ATTLOG_RRQ = 7
    CMD_ATTLOG_WRQ = 8
    CMD_CLEAR_ATTLOG = 13
    CMD_CLEAR_DATA = 14
    
    # Commandes d'informations
    CMD_GET_TIME = 201
    CMD_SET_TIME = 202
    CMD_VERSION = 1100
    CMD_DEVICE = 11
    CMD_GET_FREE_SIZES = 50
    
    # Commandes optionnelles
    CMD_OPTIONS_RRQ = 11
    CMD_OPTIONS_WRQ = 12
    CMD_DATA_WRRQ = 18
    CMD_DATA_RD = 19
    
    # Commandes avancées
    CMD_REFRESHDATA = 1013
    CMD_REFRESHOPTION = 1014
    CMD_TESTVOICE = 1017
    CMD_GET_PIN_WIDTH = 1018
    CMD_GET_POSTAL = 1022
    CMD_CHK_BIO = 30
    CMD_SET_SMS = 36
    CMD_GET_SMS = 37
    CMD_DEL_SMS = 38
    CMD_WRITE_LCD = 66
    CMD_CLEAR_LCD = 67
    CMD_GET_CAMERA = 82
    CMD_GET_FACE = 84
    CMD_SET_USER_SMS = 88
    CMD_DEL_USER_SMS = 89
    CMD_DOOR_STATE = 23
    
    # Commandes de verification
    CMD_VERIFY = 16
    CMD_VERIFY_PIN = 20
    
    # Commandes AC (Access Control)
    CMD_AC_OPTIONS = 1020
    CMD_AC_UNLOCK = 1021
    
    # Commandes de status
    CMD_REG_EVENT = 500
    CMD_ACK_OK = 2000
    CMD_ACK_ERROR = 2001
    CMD_ACK_DATA = 2002
    CMD_ACK_RETRY = 2003
    CMD_ACK_REPEAT = 2004
    CMD_ACK_UNAUTH = 2005
    CMD_ACK_UNKNOWN = 0xffff
    
    # Commandes spécifiques ZKTeco
    CMD_PREPARE_DATA = 1500
    CMD_DATA = 1501
    CMD_FREE_DATA = 1502
    CMD_CAPTURE = 23
    CMD_WRITE_MIFARE = 24
    CMD_EMPTY_MIFARE = 25
    CMD_WRITE_MIFARE_DATA = 26
    CMD_READ_MIFARE_DATA = 27
    CMD_CHECK_MIFARE = 28
    CMD_TEST_CALLBACK = 29
    CMD_WRITE_MIFARE_DATAEX = 57
    CMD_READ_MIFARE_DATAEX = 58
    
    # Commandes pour enregistrement temps réel
    CMD_REG_MONITOR = 50
    CMD_UNREG_MONITOR = 51


class ZKMachineConstants:
    """Constantes de machine ZKTeco"""
    
    # Tailles de paquet
    USHRT_MAX = 65535
    
    # Tailles de données
    MAX_PACKET_SIZE = 1024
    MAX_USER_SIZE = 72
    MAX_ATT_SIZE = 40
    
    # Timeouts
    DEFAULT_TIMEOUT = 30
    CONNECT_TIMEOUT = 5
    RECEIVE_TIMEOUT = 60
    
    # Types de vérification
    VERIFY_TYPE_PASSWORD = 0
    VERIFY_TYPE_FINGER = 1
    VERIFY_TYPE_CARD = 2
    VERIFY_TYPE_FACE = 3
    VERIFY_TYPE_FINGER_PW = 4
    VERIFY_TYPE_FACE_PW = 5
    VERIFY_TYPE_FINGER_CARD = 6
    VERIFY_TYPE_FACE_CARD = 7
    VERIFY_TYPE_FP_PW_CARD = 8
    VERIFY_TYPE_FACE_PW_CARD = 9
    
    # Types de status
    STATUS_IN = 0  # Entrée
    STATUS_OUT = 1  # Sortie
    STATUS_BREAK_OUT = 2  # Sortie pause
    STATUS_BREAK_IN = 3  # Retour pause
    STATUS_OVERTIME_IN = 4  # Entrée heures sup
    STATUS_OVERTIME_OUT = 5  # Sortie heures sup
    
    # Privilèges utilisateur
    PRIVILEGE_USER = 0
    PRIVILEGE_ENROLLER = 2
    PRIVILEGE_MANAGER = 3
    PRIVILEGE_SUPERADMIN = 6
    
    # Finger indexes
    FINGER_COUNT = 10


class ZKProtocol:
    """
    Classe implémentant le protocole de communication ZKTeco.
    
    Cette classe gère l'encodage et le décodage des paquets selon
    le protocole propriétaire ZKTeco.
    """
    
    def __init__(self):
        """Initialiser le protocole"""
        self.session_id = 0
        self.reply_id = 0
        self.__data = 0  # utilisé pour encoding
    
    @staticmethod
    def create_checksum(command: int, session_id: int, reply_id: int, data: bytes = b'') -> int:
        """
        Calculer le checksum pour un paquet ZK.
        
        Le checksum est calculé en additionnant tous les octets de l'en-tête
        et des données, puis en prenant le complément à deux.
        
        Args:
            command: Code de commande
            session_id: ID de session
            reply_id: ID de réponse
            data: Données du paquet
        
        Returns:
            int: Checksum calculé
        """
        # Créer le buffer pour le calcul
        buffer = struct.pack('<HHH', command, session_id, reply_id) + data
        
        # Calculer la somme
        checksum = sum(buffer) % 65536
        
        # Complément à deux
        checksum = (~checksum + 1) % 65536
        
        return checksum
    
    @staticmethod
    def create_header(command: int, checksum: int, session_id: int, 
                      reply_id: int, data_size: int = 0) -> bytes:
        """
        Créer l'en-tête d'un paquet ZK.
        
        Format de l'en-tête:
        - 2 bytes: Start marker (0x5050)
        - 2 bytes: Taille du paquet
        - 2 bytes: Commande
        - 2 bytes: Checksum
        - 2 bytes: ID de session
        - 2 bytes: ID de réponse
        
        Args:
            command: Code de commande
            checksum: Checksum calculé
            session_id: ID de session
            reply_id: ID de réponse
            data_size: Taille des données
        
        Returns:
            bytes: En-tête du paquet
        """
        # Taille totale = taille en-tête (8 bytes) + taille données
        size = data_size + 8
        
        return struct.pack('<HHHHHH',
            0x5050,     # Start marker (constant)
            size,       # Packet size
            command,    # Command code
            checksum,   # Checksum
            session_id, # Session ID
            reply_id    # Reply ID
        )
    
    @staticmethod
    def create_user(user_id: int, name: str, privilege: int = 0,
                   password: str = '', card: str = '', group_id: int = 0,
                   timezones: str = '') -> bytes:
        """
        Créer un enregistrement utilisateur au format ZK.
        
        Format utilisateur:
        - 2 bytes: UID (user ID interne)
        - 4 bytes: User ID (numéro employé)
        - 16 bytes: Mot de passe (padding avec 0x00)
        - 24 bytes: Nom (padding avec 0x00)
        - 1 byte: Privilège
        - 1 byte: Enable (toujours 1)
        - 10 bytes: Carte/proximité
        - 8 bytes: Group/TZ
        
        Args:
            user_id: ID utilisateur (numéro employé)
            name: Nom de l'utilisateur
            privilege: Niveau de privilège
            password: Mot de passe (max 16 chars)
            card: Numéro de carte
            group_id: ID de groupe
            timezones: Timezones
        
        Returns:
            bytes: Données utilisateur encodées
        """
        # Encoder le nom en ASCII (ou UTF-8 pour les versions récentes)
        name_bytes = name.encode('utf-8', errors='replace')[:24].ljust(24, b'\x00')
        
        # Encoder le mot de passe
        pw_bytes = password.encode('ascii', errors='replace')[:16].ljust(16, b'\x00')
        
        # Encoder la carte
        card_bytes = card.encode('ascii', errors='replace')[:10].ljust(10, b'\x00')
        
        # Timezones
        tz_bytes = timezones.encode('ascii', errors='replace')[:8].ljust(8, b'\x00')
        
        # Construire l'enregistrement
        record = struct.pack('<I', user_id)      # User ID (4 bytes)
        record += pw_bytes                        # Password (16 bytes)
        record += name_bytes                      # Name (24 bytes)
        record += struct.pack('<B', privilege)   # Privilege (1 byte)
        record += struct.pack('<B', 1)           # Enable (1 byte)
        record += card_bytes                      # Card (10 bytes)
        record += tz_bytes                        # Group/TZ (8 bytes)
        
        return record
    
    @staticmethod
    def parse_user(data: bytes) -> Dict[str, Any]:
        """
        Parser un enregistrement utilisateur.
        
        Args:
            data: Données utilisateur brutes
        
        Returns:
            Dict: Informations utilisateur parsées
        """
        if len(data) < 72:
            return None
        
        try:
            # Parser selon le format ZK
            user_id = struct.unpack('<I', data[0:4])[0]
            password = data[4:20].rstrip(b'\x00').decode('ascii', errors='replace')
            name = data[20:44].rstrip(b'\x00').decode('utf-8', errors='replace')
            privilege = struct.unpack('<B', data[44:45])[0]
            # enable = struct.unpack('<B', data[45:46])[0]
            card = data[46:56].rstrip(b'\x00').decode('ascii', errors='replace')
            
            return {
                'user_id': user_id,
                'name': name,
                'privilege': privilege,
                'password': password if password else None,
                'card': card if card else None
            }
        except Exception:
            return None
    
    @staticmethod
    def create_attendance_record(user_id: int, timestamp: int,
                                 status: int = 0, verify_type: int = 1,
                                 work_code: int = 0, reserved: int = 0) -> bytes:
        """
        Créer un enregistrement de pointage.
        
        Format pointage:
        - 4 bytes: User ID
        - 4 bytes: Timestamp (epoch)
        - 1 byte: Status (entrée/sortie)
        - 1 byte: Verify type
        - 1 byte: Work code
        - 1 byte: Reserved
        
        Args:
            user_id: ID utilisateur
            timestamp: Timestamp Unix
            status: Status (0=entrée, 1=sortie, etc.)
            verify_type: Type de vérification
            work_code: Code de travail
            reserved: Réservé
        
        Returns:
            bytes: Enregistrement de pointage
        """
        return struct.pack('<IBBBBB',
            user_id,
            timestamp,
            status,
            verify_type,
            work_code,
            reserved
        )
    
    @staticmethod
    def parse_attendance(data: bytes) -> Dict[str, Any]:
        """
        Parser un enregistrement de pointage.
        
        Args:
            data: Données de pointage brutes
        
        Returns:
            Dict: Informations de pointage parsées
        """
        if len(data) < 10:
            return None
        
        try:
            user_id = struct.unpack('<I', data[0:4])[0]
            timestamp = struct.unpack('<I', data[4:8])[0]
            status = struct.unpack('<B', data[8:9])[0]
            verify_type = struct.unpack('<B', data[9:10])[0]
            
            # Work code peut ne pas être présent
            work_code = 0
            if len(data) >= 11:
                work_code = struct.unpack('<B', data[10:11])[0]
            
            from datetime import datetime
            
            return {
                'user_id': user_id,
                'timestamp': datetime.fromtimestamp(timestamp),
                'status': status,
                'verify_type': verify_type,
                'work_code': work_code
            }
        except Exception:
            return None
    
    @staticmethod
    def encode_time(dt) -> bytes:
        """
        Encoder une date/heure au format ZK.
        
        Le format ZK encode la date en secondes depuis une époque spéciale.
        
        Args:
            dt: Objet datetime
        
        Returns:
            bytes: Date encodée sur 4 bytes
        """
        import time as t
        timestamp = int(t.mktime(dt.timetuple()))
        return struct.pack('<I', timestamp)
    
    @staticmethod
    def decode_time(data: bytes) -> 'datetime':
        """
        Décoder une date/heure du format ZK.
        
        Args:
            data: Données encodées (4 bytes)
        
        Returns:
            datetime: Objet datetime
        """
        from datetime import datetime
        timestamp = struct.unpack('<I', data)[0]
        return datetime.fromtimestamp(timestamp)
    
    @staticmethod
    def decode_fingerprint(data: bytes) -> List[Dict]:
        """
        Décoder les données d'empreintes digitales.
        
        Args:
            data: Données brutes d'empreintes
        
        Returns:
            List[Dict]: Liste des empreintes
        """
        fingerprints = []
        
        if not data:
            return fingerprints
        
        pos = 0
        while pos < len(data):
            if pos + 6 > len(data):
                break
            
            try:
                # Taille de l'en-tête empreinte
                size = struct.unpack('<H', data[pos:pos+2])[0]
                uid = struct.unpack('<I', data[pos+2:pos+6])[0]
                
                # Finger index et validité
                fid = struct.unpack('<B', data[pos+6:pos+7])[0]
                valid = struct.unpack('<B', data[pos+7:pos+8])[0]
                
                # Template
                template_size = size - 8
                if template_size > 0 and pos + 8 + template_size <= len(data):
                    template = data[pos+8:pos+8+template_size]
                    
                    fingerprints.append({
                        'uid': uid,
                        'finger_index': fid,
                        'validity': valid,
                        'template': template,
                        'template_size': template_size
                    })
                
                pos += size
            except Exception:
                break
        
        return fingerprints


# Mapping des types de vérification
VERIFY_TYPE_NAMES = {
    0: "Mot de passe",
    1: "Empreinte",
    2: "Carte",
    3: "Visage",
    4: "Empreinte + PW",
    5: "Visage + PW",
    6: "Empreinte + Carte",
    7: "Visage + Carte",
    8: "FP + PW + Carte",
    9: "Visage + PW + Carte",
    10: "Reconnaissance",
    11: "Veine",
    12: "Palm",
    13: "Iris"
}

# Mapping des status
STATUS_NAMES = {
    0: "Entrée",
    1: "Sortie",
    2: "Sortie Pause",
    3: "Retour Pause",
    4: "Entrée H.Sup",
    5: "Sortie H.Sup"
}

# Mapping des privilèges
PRIVILEGE_NAMES = {
    0: "Utilisateur",
    2: "Enregistreur",
    3: "Gestionnaire",
    6: "Super Admin"
}
