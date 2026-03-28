#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de logging structuré pour ZKTeco iClock Manager
Logging avancé avec rotation des fichiers et sortie colorée
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional
import json

# Essayer d'importer colorlog, utiliser le logging standard si non disponible
try:
    import colorlog
    COLORLOG_AVAILABLE = True
except ImportError:
    COLORLOG_AVAILABLE = False


class StructuredFormatter(logging.Formatter):
    """
    Formateur de log structuré avec support JSON
    """
    
    def format(self, record):
        """Formater l'enregistrement de log"""
        # Informations de base
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Ajouter les informations d'exception si présentes
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Ajouter les champs supplémentaires
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'device_ip'):
            log_data['device_ip'] = record.device_ip
        if hasattr(record, 'operation'):
            log_data['operation'] = record.operation
        
        return json.dumps(log_data, ensure_ascii=False)


class ZKTecoLogger:
    """
    Gestionnaire de logging centralisé pour l'application
    """
    
    _instance: Optional['ZKTecoLogger'] = None
    _initialized: bool = False
    
    def __new__(cls, *args, **kwargs):
        """Pattern Singleton pour assurer une seule instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, 
                 log_dir: str = None,
                 log_level: int = logging.INFO,
                 max_bytes: int = 5 * 1024 * 1024,  # 5 MB
                 backup_count: int = 5):
        """
        Initialiser le logger
        
        Args:
            log_dir: Répertoire des fichiers de log
            log_level: Niveau de logging
            max_bytes: Taille maximale d'un fichier de log
            backup_count: Nombre de fichiers de sauvegarde
        """
        # Éviter la réinitialisation multiple (Singleton)
        if ZKTecoLogger._initialized:
            return
        
        self.log_dir = log_dir or os.path.expanduser('~/.zkteco_manager/logs')
        self.log_level = log_level
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        
        # Créer le répertoire de logs
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Configuration du logger racine
        self.root_logger = logging.getLogger('zkteco')
        self.root_logger.setLevel(log_level)
        
        # Supprimer les handlers existants
        self.root_logger.handlers.clear()
        
        # Ajouter les handlers
        self._setup_console_handler()
        self._setup_file_handler()
        self._setup_error_file_handler()
        
        ZKTecoLogger._initialized = True
    
    def _setup_console_handler(self):
        """Configurer le handler de console avec couleurs"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        
        if COLORLOG_AVAILABLE:
            # Utiliser colorlog pour la sortie colorée
            formatter = colorlog.ColoredFormatter(
                '%(log_color)s%(asctime)s - %(levelname)-8s%(reset)s - %(name)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                }
            )
        else:
            # Fallback sans couleurs
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)-8s - %(name)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        console_handler.setFormatter(formatter)
        self.root_logger.addHandler(console_handler)
    
    def _setup_file_handler(self):
        """Configurer le handler de fichier principal"""
        from logging.handlers import RotatingFileHandler
        
        log_file = os.path.join(self.log_dir, 'zkteco_manager.log')
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(self.log_level)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)-8s - %(name)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        self.root_logger.addHandler(file_handler)
    
    def _setup_error_file_handler(self):
        """Configurer le handler de fichier d'erreurs"""
        from logging.handlers import RotatingFileHandler
        
        error_file = os.path.join(self.log_dir, 'zkteco_errors.log')
        error_handler = RotatingFileHandler(
            error_file,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)-8s - %(name)s - %(filename)s:%(lineno)d\n%(message)s\n' + '='*80,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        error_handler.setFormatter(formatter)
        self.root_logger.addHandler(error_handler)
    
    @staticmethod
    def get_logger(name: str = None) -> logging.Logger:
        """
        Obtenir un logger
        
        Args:
            name: Nom du logger (optionnel)
            
        Returns:
            Instance de logger
        """
        if not ZKTecoLogger._initialized:
            ZKTecoLogger()
        
        if name:
            return logging.getLogger(f'zkteco.{name}')
        return logging.getLogger('zkteco')
    
    @staticmethod
    def set_level(level: int):
        """
        Changer le niveau de logging
        
        Args:
            level: Nouveau niveau (logging.DEBUG, logging.INFO, etc.)
        """
        if ZKTecoLogger._initialized:
            ZKTecoLogger._instance.root_logger.setLevel(level)
            for handler in ZKTecoLogger._instance.root_logger.handlers:
                handler.setLevel(level)


# Classes utilitaires pour le logging contextuel
class LogContext:
    """
    Contexte de logging pour ajouter des informations supplémentaires
    """
    
    def __init__(self, logger: logging.Logger, **kwargs):
        self.logger = logger
        self.context = kwargs
    
    def info(self, message: str, **kwargs):
        """Log INFO avec contexte"""
        extra = {**self.context, **kwargs}
        self.logger.info(message, extra=extra)
    
    def warning(self, message: str, **kwargs):
        """Log WARNING avec contexte"""
        extra = {**self.context, **kwargs}
        self.logger.warning(message, extra=extra)
    
    def error(self, message: str, exc_info=False, **kwargs):
        """Log ERROR avec contexte"""
        extra = {**self.context, **kwargs}
        self.logger.error(message, exc_info=exc_info, extra=extra)
    
    def debug(self, message: str, **kwargs):
        """Log DEBUG avec contexte"""
        extra = {**self.context, **kwargs}
        self.logger.debug(message, extra=extra)


# Décorateurs de logging
def log_function_call(logger: logging.Logger = None):
    """
    Décorateur pour logger les appels de fonction
    
    Args:
        logger: Logger à utiliser (optionnel)
    """
    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = ZKTecoLogger.get_logger(func.__module__)
        
        def wrapper(*args, **kwargs):
            logger.debug(f"Appel de {func.__name__}(args={len(args)}, kwargs={len(kwargs)})")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"{func.__name__} terminé avec succès")
                return result
            except Exception as e:
                logger.error(f"Erreur dans {func.__name__}: {e}", exc_info=True)
                raise
        
        return wrapper
    return decorator


def log_device_operation(operation: str):
    """
    Décorateur pour logger les opérations sur les appareils
    
    Args:
        operation: Nom de l'opération
    """
    def decorator(func):
        logger = ZKTecoLogger.get_logger('device')
        
        def wrapper(self, *args, **kwargs):
            device_info = getattr(self, 'ip', 'unknown')
            logger.info(f"[{device_info}] Début de l'opération: {operation}")
            try:
                result = func(self, *args, **kwargs)
                logger.info(f"[{device_info}] Opération {operation} terminée avec succès")
                return result
            except Exception as e:
                logger.error(f"[{device_info}] Échec de l'opération {operation}: {e}", exc_info=True)
                raise
        
        return wrapper
    return decorator


# Initialisation automatique du logger
def init_logging(log_dir: str = None, level: int = logging.INFO):
    """
    Initialiser le système de logging
    
    Args:
        log_dir: Répertoire des logs
        level: Niveau de logging
    """
    return ZKTecoLogger(log_dir=log_dir, log_level=level)


# Exports
__all__ = [
    'ZKTecoLogger',
    'LogContext',
    'StructuredFormatter',
    'log_function_call',
    'log_device_operation',
    'init_logging',
    'get_logger'
]


# Fonction raccourci
def get_logger(name: str = None) -> logging.Logger:
    """Obtenir un logger configuré"""
    return ZKTecoLogger.get_logger(name)
