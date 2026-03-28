#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests unitaires pour le module de sécurité ZKTeco Manager
"""

import pytest
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.security import (
    PasswordManager,
    InputValidator,
    SecurityConfig,
    secure_hash,
    secure_verify,
    is_safe_input
)


class TestPasswordManager:
    """Tests pour la classe PasswordManager"""
    
    def test_hash_password_basic(self):
        """Test de hachage basique"""
        password = "mon_mot_de_passe_123"
        hashed = PasswordManager.hash_password(password)
        
        assert hashed is not None
        assert hashed != password
        assert hashed.startswith('$2b$')  # Format bcrypt
    
    def test_hash_password_unique(self):
        """Vérifier que deux hashs du même mot de passe sont différents (sel différent)"""
        password = "mon_mot_de_passe_123"
        hash1 = PasswordManager.hash_password(password)
        hash2 = PasswordManager.hash_password(password)
        
        assert hash1 != hash2  # Sels différents
    
    def test_verify_password_correct(self):
        """Test de vérification avec mot de passe correct"""
        password = "mon_mot_de_passe_123"
        hashed = PasswordManager.hash_password(password)
        
        assert PasswordManager.verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test de vérification avec mot de passe incorrect"""
        password = "mon_mot_de_passe_123"
        wrong_password = "mauvais_mot_de_passe"
        hashed = PasswordManager.hash_password(password)
        
        assert PasswordManager.verify_password(wrong_password, hashed) is False
    
    def test_verify_password_empty(self):
        """Test avec mot de passe vide"""
        hashed = PasswordManager.hash_password("password")
        
        assert PasswordManager.verify_password("", hashed) is False
        assert PasswordManager.verify_password("password", "") is False
    
    def test_hash_password_empty_raises(self):
        """Test que le hachage d'un mot de passe vide lève une exception"""
        with pytest.raises(ValueError):
            PasswordManager.hash_password("")
    
    def test_needs_rehash(self):
        """Test de détection de rehachage nécessaire"""
        password = "mon_mot_de_passe_123"
        hashed = PasswordManager.hash_password(password)
        
        # Un hash fraîchement créé ne devrait pas nécessiter de rehash
        assert PasswordManager.needs_rehash(hashed) is False
    
    def test_secure_hash_function(self):
        """Test de la fonction raccourci secure_hash"""
        password = "test_password"
        hashed = secure_hash(password)
        
        assert hashed is not None
        assert hashed != password
    
    def test_secure_verify_function(self):
        """Test de la fonction raccourci secure_verify"""
        password = "test_password"
        hashed = secure_hash(password)
        
        assert secure_verify(password, hashed) is True
        assert secure_verify("wrong", hashed) is False


class TestInputValidator:
    """Tests pour la classe InputValidator"""
    
    # ==================== Tests IP ====================
    
    def test_validate_ip_correct(self):
        """Test de validation d'IP correctes"""
        valid_ips = [
            "192.168.1.1",
            "10.0.0.1",
            "172.16.0.1",
            "255.255.255.255",
            "0.0.0.0"
        ]
        
        for ip in valid_ips:
            is_valid, error = InputValidator.validate_ip(ip)
            assert is_valid is True, f"IP {ip} devrait être valide: {error}"
    
    def test_validate_ip_incorrect(self):
        """Test de validation d'IP incorrectes"""
        invalid_ips = [
            "256.1.1.1",
            "192.168.1",
            "192.168.1.1.1",
            "abc.def.ghi.jkl",
            "192.168.1.-1",
            ""
        ]
        
        for ip in invalid_ips:
            is_valid, error = InputValidator.validate_ip(ip)
            assert is_valid is False, f"IP {ip} devrait être invalide"
    
    # ==================== Tests Port ====================
    
    def test_validate_port_correct(self):
        """Test de validation de ports corrects"""
        valid_ports = [1, 80, 443, 4370, 8080, 65535]
        
        for port in valid_ports:
            is_valid, error = InputValidator.validate_port(port)
            assert is_valid is True, f"Port {port} devrait être valide: {error}"
    
    def test_validate_port_incorrect(self):
        """Test de validation de ports incorrects"""
        invalid_ports = [0, -1, 65536, 100000]
        
        for port in invalid_ports:
            is_valid, error = InputValidator.validate_port(port)
            assert is_valid is False, f"Port {port} devrait être invalide"
    
    def test_validate_port_string(self):
        """Test de validation de port en string"""
        is_valid, _ = InputValidator.validate_port("4370")
        assert is_valid is True
    
    # ==================== Tests Nom ====================
    
    def test_validate_name_correct(self):
        """Test de validation de noms corrects"""
        valid_names = [
            "Jean Dupont",
            "Marie",
            "O'Brien",
            "François",
            "Aéïôù",
            "Test-User"
        ]
        
        for name in valid_names:
            is_valid, error = InputValidator.validate_name(name)
            assert is_valid is True, f"Nom '{name}' devrait être valide: {error}"
    
    def test_validate_name_incorrect(self):
        """Test de validation de noms incorrects"""
        invalid_names = [
            "",
            "A",  # Trop court
            "A" * 101,  # Trop long
            "Name<script>",  # Caractères dangereux
            "Name;DROP TABLE"
        ]
        
        for name in invalid_names:
            is_valid, error = InputValidator.validate_name(name)
            assert is_valid is False, f"Nom '{name}' devrait être invalide"
    
    # ==================== Tests User ID ====================
    
    def test_validate_user_id_correct(self):
        """Test de validation d'IDs utilisateur corrects"""
        valid_ids = [1, 100, 999999, 50000]
        
        for user_id in valid_ids:
            is_valid, error = InputValidator.validate_user_id(user_id)
            assert is_valid is True, f"ID {user_id} devrait être valide: {error}"
    
    def test_validate_user_id_incorrect(self):
        """Test de validation d'IDs utilisateur incorrects"""
        invalid_ids = [0, -1, 1000000]
        
        for user_id in invalid_ids:
            is_valid, error = InputValidator.validate_user_id(user_id)
            assert is_valid is False, f"ID {user_id} devrait être invalide"
    
    # ==================== Tests Injection SQL ====================
    
    def test_detect_sql_injection_safe(self):
        """Test avec des entrées sûres"""
        safe_inputs = [
            "Jean Dupont",
            "user@example.com",
            "192.168.1.1",
            "Normal text with numbers 123"
        ]
        
        for input_val in safe_inputs:
            is_safe, pattern = InputValidator.detect_sql_injection(input_val)
            assert is_safe is True, f"'{input_val}' devrait être sûr"
    
    def test_detect_sql_injection_unsafe(self):
        """Test avec des tentatives d'injection"""
        unsafe_inputs = [
            "'; DROP TABLE users; --",
            "admin'--",
            "1' UNION SELECT * FROM users--",
            "1; DELETE FROM attendance",
            "<script>alert('xss')</script>",
            "javascript:alert(1)",
            "onclick=alert(1)"
        ]
        
        for input_val in unsafe_inputs:
            is_safe, pattern = InputValidator.detect_sql_injection(input_val)
            assert is_safe is False, f"'{input_val}' devrait être détecté comme dangereux"
    
    # ==================== Tests Sanitization ====================
    
    def test_sanitize_string_basic(self):
        """Test de nettoyage basique"""
        assert InputValidator.sanitize_string("  test  ") == "test"
        assert InputValidator.sanitize_string("") == ""
        assert InputValidator.sanitize_string(None) == ""
    
    def test_sanitize_string_max_length(self):
        """Test de limitation de longueur"""
        long_string = "a" * 300
        result = InputValidator.sanitize_string(long_string, max_length=100)
        assert len(result) == 100
    
    def test_sanitize_string_special_chars(self):
        """Test d'échappement des caractères spéciaux"""
        result = InputValidator.sanitize_string("test'quote")
        assert "''" in result  # Quote échappée


class TestSecurityConfig:
    """Tests pour la configuration de sécurité"""
    
    def test_validate_password_strength_valid(self):
        """Test avec mots de passe valides"""
        valid_passwords = [
            "Password123",
            "MySecurePass1",
            "Abcdef12345"
        ]
        
        for password in valid_passwords:
            is_valid, errors = SecurityConfig.validate_password_strength(password)
            assert is_valid is True, f"'{password}' devrait être valide: {errors}"
    
    def test_validate_password_strength_too_short(self):
        """Test avec mot de passe trop court"""
        is_valid, errors = SecurityConfig.validate_password_strength("Ab12")
        assert is_valid is False
        assert any("6" in e for e in errors)  # Message mentionne 6 caractères
    
    def test_validate_password_strength_missing_uppercase(self):
        """Test sans majuscule"""
        is_valid, errors = SecurityConfig.validate_password_strength("password123")
        assert is_valid is False
        assert any("majuscule" in e.lower() for e in errors)
    
    def test_validate_password_strength_missing_lowercase(self):
        """Test sans minuscule"""
        is_valid, errors = SecurityConfig.validate_password_strength("PASSWORD123")
        assert is_valid is False
        assert any("minuscule" in e.lower() for e in errors)
    
    def test_validate_password_strength_missing_digit(self):
        """Test sans chiffre"""
        is_valid, errors = SecurityConfig.validate_password_strength("PasswordOnly")
        assert is_valid is False
        assert any("chiffre" in e.lower() for e in errors)


class TestGlobalFunctions:
    """Tests pour les fonctions globales"""
    
    def test_is_safe_input(self):
        """Test de la fonction is_safe_input"""
        assert is_safe_input("Normal text") is True
        assert is_safe_input("'; DROP TABLE users; --") is False
        assert is_safe_input("") is True


# Configuration pour pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
