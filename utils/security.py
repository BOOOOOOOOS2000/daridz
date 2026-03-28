#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de sécurité pour ZKTeco iClock Manager
Gestion des mots de passe, validation des entrées et protection contre les injections
"""

import re
import bcrypt
from typing import Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)


class PasswordManager:
    """
    Gestionnaire de mots de passe sécurisés avec bcrypt
    Utilise 12 rounds pour un bon équilibre entre sécurité et performance
    """
    
    ROUNDS = 12  # Nombre de rounds pour bcrypt
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hacher un mot de passe avec bcrypt
        
        Args:
            password: Mot de passe en clair
            
        Returns:
            Mot de passe haché (string)
        """
        if not password:
            raise ValueError("Le mot de passe ne peut pas être vide")
        
        # Générer le sel et hacher
        salt = bcrypt.gensalt(rounds=PasswordManager.ROUNDS)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """
        Vérifier un mot de passe contre un hash
        
        Args:
            password: Mot de passe en clair à vérifier
            hashed: Mot de passe haché stocké
            
        Returns:
            True si le mot de passe correspond, False sinon
        """
        if not password or not hashed:
            return False
        
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du mot de passe: {e}")
            return False
    
    @staticmethod
    def needs_rehash(hashed: str) -> bool:
        """
        Vérifier si un hash doit être régénéré (mise à jour des rounds)
        
        Args:
            hashed: Mot de passe haché
            
        Returns:
            True si le hash doit être régénéré
        """
        try:
            # Extraire les rounds du hash
            parts = hashed.split('$')
            if len(parts) >= 3:
                current_rounds = int(parts[2])
                return current_rounds < PasswordManager.ROUNDS
        except Exception:
            pass
        return False


class InputValidator:
    """
    Validateur d'entrées pour prévenir les injections et garantir l'intégrité des données
    """
    
    # Patterns de validation
    IP_PATTERN = re.compile(
        r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
        r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    )
    
    NAME_PATTERN = re.compile(r'^[\w\s\-\'àâäéèêëïîôùûüçÀÂÄÉÈÊËÏÎÔÙÛÜÇ]{2,100}$')
    
    # Patterns suspects pour la détection d'injections SQL
    SQL_INJECTION_PATTERNS = [
        r"('|\")(;|--|\)|union|select|insert|delete|update|drop|exec)",
        r"(union\s+select)",
        r"(;\s*drop\s+)",
        r"(;\s*delete\s+)",
        r"(;\s*update\s+)",
        r"(--\s*$)",
        r"(/\*.*\*/)",
        r"(xp_cmdshell)",
        r"(script\s*>)",
        r"(javascript:)",
        r"(on\w+\s*=)",  # Event handlers like onclick=
    ]
    
    @staticmethod
    def validate_ip(ip: str) -> Tuple[bool, Optional[str]]:
        """
        Valider une adresse IP
        
        Args:
            ip: Adresse IP à valider
            
        Returns:
            Tuple (is_valid, error_message)
        """
        if not ip:
            return False, "L'adresse IP ne peut pas être vide"
        
        ip = ip.strip()
        
        if not InputValidator.IP_PATTERN.match(ip):
            return False, f"Format d'adresse IP invalide: {ip}"
        
        return True, None
    
    @staticmethod
    def validate_port(port: int) -> Tuple[bool, Optional[str]]:
        """
        Valider un numéro de port
        
        Args:
            port: Numéro de port
            
        Returns:
            Tuple (is_valid, error_message)
        """
        if not isinstance(port, int):
            try:
                port = int(port)
            except (ValueError, TypeError):
                return False, "Le port doit être un nombre entier"
        
        if port < 1 or port > 65535:
            return False, f"Port invalide: {port}. Doit être entre 1 et 65535"
        
        return True, None
    
    @staticmethod
    def validate_name(name: str, field_name: str = "Nom") -> Tuple[bool, Optional[str]]:
        """
        Valider un nom (utilisateur, département, etc.)
        
        Args:
            name: Nom à valider
            field_name: Nom du champ pour les messages d'erreur
            
        Returns:
            Tuple (is_valid, error_message)
        """
        if not name:
            return False, f"{field_name} ne peut pas être vide"
        
        name = name.strip()
        
        if len(name) < 2:
            return False, f"{field_name} doit contenir au moins 2 caractères"
        
        if len(name) > 100:
            return False, f"{field_name} ne peut pas dépasser 100 caractères"
        
        if not InputValidator.NAME_PATTERN.match(name):
            return False, f"{field_name} contient des caractères non autorisés"
        
        return True, None
    
    @staticmethod
    def validate_user_id(user_id: int) -> Tuple[bool, Optional[str]]:
        """
        Valider un ID utilisateur
        
        Args:
            user_id: ID utilisateur
            
        Returns:
            Tuple (is_valid, error_message)
        """
        if not isinstance(user_id, int):
            try:
                user_id = int(user_id)
            except (ValueError, TypeError):
                return False, "L'ID utilisateur doit être un nombre entier"
        
        if user_id < 1 or user_id > 999999:
            return False, f"ID utilisateur invalide: {user_id}"
        
        return True, None
    
    @staticmethod
    def detect_sql_injection(value: str) -> Tuple[bool, Optional[str]]:
        """
        Détecter les tentatives d'injection SQL potentielles
        
        Args:
            value: Valeur à analyser
            
        Returns:
            Tuple (is_safe, detected_pattern)
        """
        if not value:
            return True, None
        
        value_lower = value.lower()
        
        for pattern in InputValidator.SQL_INJECTION_PATTERNS:
            match = re.search(pattern, value_lower, re.IGNORECASE)
            if match:
                logger.warning(f"Tentative d'injection SQL détectée: {match.group()}")
                return False, match.group()
        
        return True, None
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 255) -> str:
        """
        Nettoyer une chaîne de caractères
        
        Args:
            value: Chaîne à nettoyer
            max_length: Longueur maximale autorisée
            
        Returns:
            Chaîne nettoyée
        """
        if not value:
            return ""
        
        # Supprimer les espaces en début et fin
        value = value.strip()
        
        # Limiter la longueur
        if len(value) > max_length:
            value = value[:max_length]
        
        # Échapper les caractères potentiellement dangereux pour SQL
        # Note: Les requêtes paramétrées restent la meilleure protection
        dangerous_chars = {
            "'": "''",
            "\\": "\\\\",
            "\x00": "",
            "\n": " ",
            "\r": " ",
        }
        
        for char, replacement in dangerous_chars.items():
            value = value.replace(char, replacement)
        
        return value


class SecurityConfig:
    """
    Configuration de sécurité pour l'application
    """
    
    # Longueurs minimales et maximales
    MIN_PASSWORD_LENGTH = 6
    MAX_PASSWORD_LENGTH = 128
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 30
    
    # Validation des mots de passe
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_DIGIT = True
    PASSWORD_REQUIRE_SPECIAL = False
    
    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
        """
        Valider la force d'un mot de passe
        
        Args:
            password: Mot de passe à valider
            
        Returns:
            Tuple (is_valid, list_of_errors)
        """
        errors = []
        
        if len(password) < SecurityConfig.MIN_PASSWORD_LENGTH:
            errors.append(f"Le mot de passe doit contenir au moins {SecurityConfig.MIN_PASSWORD_LENGTH} caractères")
        
        if len(password) > SecurityConfig.MAX_PASSWORD_LENGTH:
            errors.append(f"Le mot de passe ne peut pas dépasser {SecurityConfig.MAX_PASSWORD_LENGTH} caractères")
        
        if SecurityConfig.PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("Le mot de passe doit contenir au moins une majuscule")
        
        if SecurityConfig.PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append("Le mot de passe doit contenir au moins une minuscule")
        
        if SecurityConfig.PASSWORD_REQUIRE_DIGIT and not re.search(r'\d', password):
            errors.append("Le mot de passe doit contenir au moins un chiffre")
        
        if SecurityConfig.PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Le mot de passe doit contenir au moins un caractère spécial")
        
        return len(errors) == 0, errors


# Fonctions utilitaires globales
def secure_hash(password: str) -> str:
    """Raccourci pour hacher un mot de passe"""
    return PasswordManager.hash_password(password)


def secure_verify(password: str, hashed: str) -> bool:
    """Raccourci pour vérifier un mot de passe"""
    return PasswordManager.verify_password(password, hashed)


def is_safe_input(value: str) -> bool:
    """Vérifier si une entrée est sûre (pas d'injection SQL)"""
    is_safe, _ = InputValidator.detect_sql_injection(value)
    return is_safe
