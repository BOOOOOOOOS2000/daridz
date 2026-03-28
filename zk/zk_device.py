#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Classe ZKDevice pour communication avec pointeuses ZKTeco
Implémente toutes les opérations de base et avancées
"""

import socket
import struct
import time
import threading
from datetime import datetime, date
from typing import Tuple, Optional, List, Dict, Any, Callable
from .zk_protocol import ZKProtocol, ZKCommands, ZKMachineConstants, VERIFY_TYPE_NAMES, STATUS_NAMES


class ZKDevice:
    """
    Classe principale pour communiquer avec les terminaux ZKTeco.
    
    Cette classe implémente toutes les opérations nécessaires pour
    interagir avec les pointeuses ZKTeco via TCP/IP.
    
    Exemple d'utilisation:
        device = ZKDevice('192.168.1.201', 4370)
        if device.connect():
            users = device.get_users()
            attendance = device.get_attendance()
            device.disconnect()
    """
    
    def __init__(self, ip: str, port: int = 4370, timeout: int = 30):
        """
        Initialiser la connexion au périphérique ZK.
        
        Args:
            ip: Adresse IP du périphérique
            port: Port TCP (défaut: 4370)
            timeout: Timeout en secondes (défaut: 30)
        """
        self.ip = ip
        self.port = port
        self.timeout = timeout
        
        # Socket de connexion
        self.__socket: Optional[socket.socket] = None
        self.__connected = False
        self.__locked = False
        
        # Paramètres de session
        self.__session_id = 0
        self.__reply_id = 0
        
        # Informations du périphérique
        self.firmware_version = None
        self.device_name = None
        self.serial_number = None
        self.platform = None
        self.mac_address = None
        
        # Capacités
        self.user_capacity = 0
        self.finger_capacity = 0
        self.record_capacity = 0
        self.face_capacity = 0
        
        # Cache
        self.__users_cache = None
        self.__attendance_cache = None
        
        # Verrou pour thread-safety
        self.__lock = threading.Lock()
        
        # Callback pour progression
        self.__progress_callback: Optional[Callable[[int, int, str], None]] = None
    
    def set_progress_callback(self, callback: Callable[[int, int, str], None]):
        """Définir un callback pour la progression des opérations longues"""
        self.__progress_callback = callback
    
    def __send_packet(self, command: int, data: bytes = b'') -> bool:
        """
        Envoyer un paquet au périphérique.
        
        Args:
            command: Code de commande
            data: Données à envoyer
        
        Returns:
            bool: True si envoyé avec succès
        """
        if not self.__socket:
            return False
        
        # Calculer le checksum
        checksum = ZKProtocol.create_checksum(
            command, self.__session_id, self.__reply_id, data
        )
        
        # Créer l'en-tête
        header = ZKProtocol.create_header(
            command, checksum, self.__session_id, self.__reply_id, len(data)
        )
        
        # Envoyer le paquet complet
        packet = header + data
        
        try:
            self.__socket.send(packet)
            return True
        except socket.error:
            return False
    
    def __recv_packet(self, timeout: int = None) -> Tuple[int, int, bytes]:
        """
        Recevoir un paquet du périphérique.
        
        Returns:
            Tuple[int, int, bytes]: (command, response_code, data)
        """
        if not self.__socket:
            return (0, 0, b'')
        
        old_timeout = self.__socket.gettimeout()
        if timeout:
            self.__socket.settimeout(timeout)
        
        try:
            # Recevoir l'en-tête (16 bytes)
            header = self.__recv_all(16)
            
            if len(header) < 16:
                return (0, 0, b'')
            
            # Parser l'en-tête
            _, size, command, checksum, session_id, reply_id = struct.unpack(
                '<HHHHHH', header
            )
            
            # Mettre à jour la session
            self.__session_id = session_id
            self.__reply_id = reply_id
            
            # Recevoir les données
            data_size = size - 8
            data = b''
            
            if data_size > 0:
                data = self.__recv_all(data_size)
            
            # Le command reçu est en fait le code de réponse
            response_code = command
            
            return (command, response_code, data)
            
        except socket.timeout:
            return (0, 0, b'')
        except socket.error:
            return (0, 0, b'')
        finally:
            if timeout:
                self.__socket.settimeout(old_timeout)
    
    def __recv_all(self, size: int) -> bytes:
        """Recevoir exactement 'size' octets"""
        data = b''
        while len(data) < size:
            chunk = self.__socket.recv(size - len(data))
            if not chunk:
                break
            data += chunk
        return data
    
    def __send_command(self, command: int, data: bytes = b'',
                       timeout: int = None) -> Tuple[int, bytes]:
        """
        Envoyer une commande et recevoir la réponse.
        
        Args:
            command: Code de commande
            data: Données à envoyer
            timeout: Timeout spécifique
        
        Returns:
            Tuple[int, bytes]: (code_réponse, données_reçues)
        """
        with self.__lock:
            # Envoyer la commande
            if not self.__send_packet(command, data):
                return (ZKCommands.CMD_ACK_ERROR, b'')
            
            # Recevoir la réponse
            _, response_code, response_data = self.__recv_packet(timeout)
            
            return (response_code, response_data)
    
    # ==================== CONNEXION ====================
    
    def connect(self) -> bool:
        """
        Établir la connexion avec le périphérique.
        
        Returns:
            bool: True si connecté avec succès
        """
        try:
            # Créer le socket
            self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.__socket.settimeout(self.timeout)
            
            # Connecter
            self.__socket.connect((self.ip, self.port))
            
            # Envoyer la commande de connexion
            response, data = self.__send_command(ZKCommands.CMD_CONNECT)
            
            if response == ZKCommands.CMD_ACK_OK:
                self.__connected = True
                self.__reply_id = 0
                
                # Récupérer les infos du périphérique
                self.__get_device_info()
                
                return True
            
            return False
            
        except socket.error as e:
            self.__connected = False
            self.__socket = None
            raise ConnectionError(f"Erreur de connexion: {str(e)}")
    
    def disconnect(self) -> bool:
        """
        Fermer la connexion avec le périphérique.
        
        Returns:
            bool: True si déconnecté avec succès
        """
        if not self.__connected:
            return True
        
        try:
            # Déverrouiller le périphérique si nécessaire
            if self.__locked:
                self.enable_device()
            
            # Envoyer la commande de déconnexion
            self.__send_command(ZKCommands.CMD_EXIT)
            
        except Exception:
            pass
        finally:
            try:
                if self.__socket:
                    self.__socket.close()
            except Exception:
                pass
            
            self.__socket = None
            self.__connected = False
            self.__locked = False
        
        return True
    
    def is_connected(self) -> bool:
        """Vérifier si le périphérique est connecté"""
        return self.__connected
    
    def __get_device_info(self):
        """Récupérer les informations du périphérique"""
        try:
            # Version firmware
            response, data = self.__send_command(ZKCommands.CMD_VERSION)
            if response == ZKCommands.CMD_ACK_DATA:
                self.firmware_version = data.rstrip(b'\x00').decode('utf-8', errors='ignore')
        except Exception:
            pass
        
        try:
            # Nom du périphérique
            response, data = self.__send_command(ZKCommands.CMD_DEVICE)
            if response == ZKCommands.CMD_ACK_DATA:
                info = data.rstrip(b'\x00').decode('utf-8', errors='ignore')
                parts = info.split(',')
                if len(parts) >= 2:
                    self.device_name = parts[0].strip()
                    self.serial_number = parts[1].strip()
        except Exception:
            pass
        
        try:
            # Capacités
            response, data = self.__send_command(ZKCommands.CMD_GET_FREE_SIZES)
            if response == ZKCommands.CMD_ACK_DATA and len(data) >= 16:
                # Parser les capacités (format variable selon modèle)
                pass
        except Exception:
            pass
    
    def get_device_time(self) -> Optional[datetime]:
        """
        Récupérer l'heure du périphérique.
        
        Returns:
            datetime: Heure du périphérique ou None
        """
        response, data = self.__send_command(ZKCommands.CMD_GET_TIME)
        
        if response == ZKCommands.CMD_ACK_DATA and len(data) >= 4:
            return ZKProtocol.decode_time(data[:4])
        
        return None
    
    def set_device_time(self, dt: datetime = None) -> bool:
        """
        Définir l'heure du périphérique.
        
        Args:
            dt: Date/heure à définir (défaut: heure actuelle)
        
        Returns:
            bool: True si succès
        """
        if dt is None:
            dt = datetime.now()
        
        data = ZKProtocol.encode_time(dt)
        response, _ = self.__send_command(ZKCommands.CMD_SET_TIME, data)
        
        return response == ZKCommands.CMD_ACK_OK
    
    def enable_device(self) -> bool:
        """Réactiver le périphérique (après maintenance)"""
        response, _ = self.__send_command(ZKCommands.CMD_ENABLEDEVICE)
        
        if response == ZKCommands.CMD_ACK_OK:
            self.__locked = False
        
        return response == ZKCommands.CMD_ACK_OK
    
    def disable_device(self) -> bool:
        """Désactiver le périphérique (pour maintenance)"""
        response, _ = self.__send_command(ZKCommands.CMD_DISABLEDEVICE)
        
        if response == ZKCommands.CMD_ACK_OK:
            self.__locked = True
        
        return response == ZKCommands.CMD_ACK_OK
    
    def restart(self) -> bool:
        """Redémarrer le périphérique"""
        response, _ = self.__send_command(ZKCommands.CMD_RESTART)
        self.__connected = False
        self.__socket = None
        return True
    
    # ==================== UTILISATEURS ====================
    
    def get_users(self, use_cache: bool = False) -> List[Dict]:
        """
        Récupérer tous les utilisateurs du périphérique.
        
        Args:
            use_cache: Utiliser le cache si disponible
        
        Returns:
            List[Dict]: Liste des utilisateurs
        """
        if use_cache and self.__users_cache:
            return self.__users_cache
        
        users = []
        
        # Désactiver le périphérique
        self.disable_device()
        
        try:
            # Envoyer la commande de récupération
            response, data = self.__send_command(
                ZKCommands.CMD_USER_WRQ,
                struct.pack('<I', 1)  # Flag pour nouvelle version
            )
            
            if response == ZKCommands.CMD_PREPARE_DATA:
                # Récupérer la taille des données
                size = struct.unpack('<I', data)[0] if len(data) >= 4 else 0
                
                # Recevoir les données
                all_data = self.__recv_data(size)
                
                # Parser les utilisateurs (taille fixe de 72 bytes par utilisateur)
                offset = 0
                while offset + 72 <= len(all_data):
                    user_data = all_data[offset:offset + 72]
                    user = ZKProtocol.parse_user(user_data)
                    
                    if user and user['user_id'] > 0:
                        user['uid'] = len(users) + 1
                        users.append(user)
                    
                    offset += 72
                
                # Libérer les données
                self.__send_command(ZKCommands.CMD_FREE_DATA)
            
        finally:
            self.enable_device()
        
        self.__users_cache = users
        return users
    
    def __recv_data(self, size: int) -> bytes:
        """Recevoir des données de grande taille"""
        data = b''
        received = 0
        
        while received < size:
            response, chunk = self.__send_command(ZKCommands.CMD_DATA)
            
            if response == ZKCommands.CMD_DATA:
                data += chunk
                received += len(chunk)
                
                # Callback de progression
                if self.__progress_callback:
                    self.__progress_callback(received, size, "Réception données...")
            
            elif response == ZKCommands.CMD_ACK_OK:
                break
            
            else:
                break
        
        return data
    
    def set_user(self, user_id: int, name: str, privilege: int = 0,
                 password: str = '', card: str = '', group_id: int = 0) -> bool:
        """
        Ajouter ou mettre à jour un utilisateur.
        
        Args:
            user_id: ID utilisateur (numéro employé)
            name: Nom de l'utilisateur
            privilege: Niveau de privilège (0=user, 3=admin, 6=super admin)
            password: Mot de passe (optionnel)
            card: Numéro de carte (optionnel)
            group_id: ID de groupe (optionnel)
        
        Returns:
            bool: True si succès
        """
        # Créer l'enregistrement utilisateur
        user_data = ZKProtocol.create_user(
            user_id, name, privilege, password, card, group_id
        )
        
        # Envoyer la commande
        response, _ = self.__send_command(
            ZKCommands.CMD_USERTEMP_WRQ,
            struct.pack('<I', user_id) + user_data
        )
        
        # Invalider le cache
        self.__users_cache = None
        
        return response == ZKCommands.CMD_ACK_OK
    
    def delete_user(self, user_id: int) -> bool:
        """
        Supprimer un utilisateur.
        
        Args:
            user_id: ID utilisateur à supprimer
        
        Returns:
            bool: True si succès
        """
        # Commande de suppression
        data = struct.pack('<I', user_id)
        response, _ = self.__send_command(ZKCommands.CMD_DEL_USER, data)
        
        # Invalider le cache
        self.__users_cache = None
        
        return response == ZKCommands.CMD_ACK_OK
    
    def delete_user_fingerprints(self, user_id: int, finger_index: int = -1) -> bool:
        """
        Supprimer les empreintes d'un utilisateur.
        
        Args:
            user_id: ID utilisateur
            finger_index: Index du doigt (-1 pour tous)
        
        Returns:
            bool: True si succès
        """
        data = struct.pack('<IB', user_id, finger_index if finger_index >= 0 else 255)
        response, _ = self.__send_command(ZKCommands.CMD_DEL_USER_TEMP, data)
        
        return response == ZKCommands.CMD_ACK_OK
    
    # ==================== EMPREINTES ====================
    
    def get_user_fingerprints(self, user_id: int) -> List[Dict]:
        """
        Récupérer les empreintes d'un utilisateur.
        
        Args:
            user_id: ID utilisateur
        
        Returns:
            List[Dict]: Liste des empreintes
        """
        fingerprints = []
        
        self.disable_device()
        
        try:
            # Demander les templates
            data = struct.pack('<I', user_id)
            response, resp_data = self.__send_command(
                ZKCommands.CMD_USERTEMP_RRQ, data
            )
            
            if response == ZKCommands.CMD_PREPARE_DATA:
                size = struct.unpack('<I', resp_data)[0] if len(resp_data) >= 4 else 0
                
                # Recevoir les données
                all_data = self.__recv_data(size)
                
                # Parser les empreintes
                fingerprints = ZKProtocol.decode_fingerprint(all_data)
                
                # Libérer les données
                self.__send_command(ZKCommands.CMD_FREE_DATA)
        
        finally:
            self.enable_device()
        
        return fingerprints
    
    def get_all_fingerprints(self) -> List[Dict]:
        """
        Récupérer toutes les empreintes du périphérique.
        
        Returns:
            List[Dict]: Liste de toutes les empreintes
        """
        all_fingerprints = []
        
        # Récupérer d'abord les utilisateurs
        users = self.get_users()
        
        if self.__progress_callback:
            self.__progress_callback(0, len(users), "Récupération empreintes...")
        
        for i, user in enumerate(users):
            fps = self.get_user_fingerprints(user['user_id'])
            all_fingerprints.extend(fps)
            
            if self.__progress_callback:
                self.__progress_callback(i + 1, len(users), f"Utilisateur {user['name']}")
        
        return all_fingerprints
    
    # ==================== POINTAGES ====================
    
    def get_attendance(self, use_cache: bool = False) -> List[Dict]:
        """
        Récupérer tous les enregistrements de pointage.
        
        Args:
            use_cache: Utiliser le cache si disponible
        
        Returns:
            List[Dict]: Liste des pointages
        """
        if use_cache and self.__attendance_cache:
            return self.__attendance_cache
        
        attendance = []
        
        self.disable_device()
        
        try:
            # Demander les pointages
            response, data = self.__send_command(ZKCommands.CMD_ATTLOG_RRQ)
            
            if response == ZKCommands.CMD_PREPARE_DATA:
                size = struct.unpack('<I', data)[0] if len(data) >= 4 else 0
                
                # Recevoir les données
                all_data = self.__recv_data(size)
                
                # Parser les pointages (taille variable, généralement 10-40 bytes)
                offset = 0
                while offset + 10 <= len(all_data):
                    record = ZKProtocol.parse_attendance(all_data[offset:offset + 40])
                    
                    if record:
                        attendance.append(record)
                        
                        # Taille de l'enregistrement (variable selon modèle)
                        # Pour iClock, généralement 10 ou 12 bytes minimum
                        offset += 40  # Aligner sur 40 bytes pour compatibilité
                    else:
                        break
                
                # Libérer les données
                self.__send_command(ZKCommands.CMD_FREE_DATA)
        
        finally:
            self.enable_device()
        
        self.__attendance_cache = attendance
        return attendance
    
    def get_attendance_count(self) -> int:
        """
        Récupérer le nombre d'enregistrements de pointage.
        
        Returns:
            int: Nombre d'enregistrements
        """
        # Cette information peut être obtenue via d'autres commandes
        # Pour l'instant, on fait une estimation
        attendance = self.get_attendance()
        return len(attendance)
    
    def clear_attendance(self) -> bool:
        """
        Effacer tous les enregistrements de pointage.
        
        Returns:
            bool: True si succès
        """
        response, _ = self.__send_command(ZKCommands.CMD_CLEAR_ATTLOG)
        
        # Invalider le cache
        self.__attendance_cache = None
        
        return response == ZKCommands.CMD_ACK_OK
    
    def clear_all_data(self) -> bool:
        """
        Effacer toutes les données du périphérique.
        
        Attention: Cette opération est irréversible!
        
        Returns:
            bool: True si succès
        """
        response, _ = self.__send_command(ZKCommands.CMD_CLEAR_DATA)
        
        # Invalider les caches
        self.__users_cache = None
        self.__attendance_cache = None
        
        return response == ZKCommands.CMD_ACK_OK
    
    # ==================== SYNCHRONISATION ====================
    
    def sync_users_to_device(self, users: List[Dict],
                            on_progress: Callable[[int, int], None] = None) -> Tuple[int, int]:
        """
        Synchroniser les utilisateurs vers le périphérique.
        
        Args:
            users: Liste des utilisateurs à synchroniser
            on_progress: Callback de progression
        
        Returns:
            Tuple[int, int]: (succès, échecs)
        """
        success = 0
        failed = 0
        
        total = len(users)
        
        for i, user in enumerate(users):
            if self.set_user(
                user.get('id'),
                user.get('name', ''),
                user.get('privilege', 0),
                user.get('password', ''),
                user.get('card', '')
            ):
                success += 1
            else:
                failed += 1
            
            if on_progress:
                on_progress(i + 1, total)
        
        return (success, failed)
    
    def sync_users_from_device(self, db_manager) -> int:
        """
        Synchroniser les utilisateurs du périphérique vers la base de données.
        
        Args:
            db_manager: Gestionnaire de base de données
        
        Returns:
            int: Nombre d'utilisateurs synchronisés
        """
        users = self.get_users()
        count = 0
        
        for user in users:
            try:
                db_manager.add_user(
                    user_id=user['user_id'],
                    uid=user.get('uid', user['user_id']),
                    name=user['name'],
                    privilege=user.get('privilege', 0),
                    password=user.get('password'),
                    card=user.get('card')
                )
                count += 1
            except Exception:
                pass
        
        return count
    
    def sync_attendance_from_device(self, db_manager) -> int:
        """
        Synchroniser les pointages du périphérique vers la base de données.
        
        Args:
            db_manager: Gestionnaire de base de données
        
        Returns:
            int: Nombre de pointages synchronisés
        """
        attendance = self.get_attendance()
        count = 0
        
        records = []
        for record in attendance:
            records.append({
                'user_id': record['user_id'],
                'uid': record['user_id'],
                'timestamp': record['timestamp'],
                'status': record.get('status', 0),
                'verify_type': record.get('verify_type', 1),
                'work_code': record.get('work_code', 0),
                'terminal_id': self.serial_number
            })
            count += 1
        
        # Insertion en masse
        db_manager.bulk_add_attendance(records)
        
        return count
    
    # ==================== INFORMATIONS ====================
    
    def get_device_info(self) -> Dict[str, Any]:
        """
        Récupérer les informations complètes du périphérique.
        
        Returns:
            Dict: Informations du périphérique
        """
        return {
            'ip': self.ip,
            'port': self.port,
            'connected': self.__connected,
            'firmware_version': self.firmware_version,
            'device_name': self.device_name,
            'serial_number': self.serial_number,
            'platform': self.platform,
            'mac_address': self.mac_address,
            'device_time': self.get_device_time(),
            'user_capacity': self.user_capacity,
            'finger_capacity': self.finger_capacity,
            'record_capacity': self.record_capacity,
            'users_count': len(self.get_users(use_cache=True)),
            'attendance_count': self.get_attendance_count()
        }
    
    def test_voice(self, voice_id: int = 0) -> bool:
        """
        Tester la voix du périphérique.
        
        Args:
            voice_id: ID du son à jouer
        
        Returns:
            bool: True si succès
        """
        data = struct.pack('<I', voice_id)
        response, _ = self.__send_command(ZKCommands.CMD_TESTVOICE, data)
        return response == ZKCommands.CMD_ACK_OK
    
    # ==================== CONTEXT MANAGER ====================
    
    def __enter__(self):
        """Support du context manager"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Nettoyage du context manager"""
        self.disconnect()
        return False


# Fonction utilitaire pour tester la connexion
def test_connection(ip: str, port: int = 4370, timeout: int = 5) -> Tuple[bool, str]:
    """
    Tester la connexion à un périphérique ZKTeco.
    
    Args:
        ip: Adresse IP
        port: Port TCP
        timeout: Timeout en secondes
    
    Returns:
        Tuple[bool, str]: (succès, message)
    """
    try:
        device = ZKDevice(ip, port, timeout)
        if device.connect():
            info = device.get_device_info()
            device.disconnect()
            return (True, f"Connecté! Firmware: {info.get('firmware_version', 'N/A')}")
        else:
            return (False, "Échec de l'authentification")
    except socket.timeout:
        return (False, "Timeout de connexion")
    except ConnectionRefusedError:
        return (False, "Connexion refusée")
    except Exception as e:
        return (False, f"Erreur: {str(e)}")
