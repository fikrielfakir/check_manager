#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Security Manager for Cheque Management System
Handles encryption, audit logging, access control, and compliance
"""

import hashlib
import secrets
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
from enum import Enum
from dataclasses import dataclass

class UserRole(Enum):
    ADMIN = "admin"
    MANAGER = "manager" 
    EMPLOYEE = "employee"
    READONLY = "readonly"

class AuditAction(Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    IMPORT = "import"
    BACKUP = "backup"
    RESTORE = "restore"
    CONFIG_CHANGE = "config_change"

@dataclass
class AuditLogEntry:
    timestamp: datetime
    user_id: int
    username: str
    action: AuditAction
    resource_type: str
    resource_id: Optional[str]
    details: Dict[str, Any]
    ip_address: Optional[str]
    user_agent: Optional[str]
    success: bool
    error_message: Optional[str] = None

class SecurityManager:
    """Comprehensive security manager"""
    
    def __init__(self, db_manager, config_manager):
        self.db = db_manager
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Initialize encryption
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
        # Role permissions
        self.role_permissions = self._load_role_permissions()
        
        # Initialize audit logging
        self._init_audit_logging()
        
        # Security settings
        self.password_policy = self._load_password_policy()
        self.session_timeout = self.config.get('security.session_timeout', 3600)  # 1 hour
        self.max_login_attempts = self.config.get('security.max_login_attempts', 5)
        self.lockout_duration = self.config.get('security.lockout_duration', 900)  # 15 minutes
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key"""
        key_file = self.config.get('security.key_file', 'encryption.key')
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            
            # Set restrictive permissions
            os.chmod(key_file, 0o600)
            return key
    
    def _load_role_permissions(self) -> Dict[UserRole, List[str]]:
        """Load role-based permissions"""
        return {
            UserRole.ADMIN: [
                'cheque.create', 'cheque.read', 'cheque.update', 'cheque.delete',
                'client.create', 'client.read', 'client.update', 'client.delete',
                'bank.create', 'bank.read', 'bank.update', 'bank.delete',
                'user.create', 'user.read', 'user.update', 'user.delete',
                'report.generate', 'report.export',
                'system.backup', 'system.restore', 'system.configure',
                'audit.read'
            ],
            UserRole.MANAGER: [
                'cheque.create', 'cheque.read', 'cheque.update',
                'client.create', 'client.read', 'client.update',
                'bank.read',
                'report.generate', 'report.export',
                'system.backup'
            ],
            UserRole.EMPLOYEE: [
                'cheque.create', 'cheque.read', 'cheque.update',
                'client.read', 'client.update',
                'bank.read',
                'report.generate'
            ],
            UserRole.READONLY: [
                'cheque.read',
                'client.read',
                'bank.read',
                'report.generate'
            ]
        }
    
    def _init_audit_logging(self):
        """Initialize audit logging table"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS audit_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        user_id INTEGER,
                        username TEXT NOT NULL,
                        action TEXT NOT NULL,
                        resource_type TEXT,
                        resource_id TEXT,
                        details TEXT,
                        ip_address TEXT,
                        user_agent TEXT,
                        success BOOLEAN NOT NULL,
                        error_message TEXT,
                        session_id TEXT
                    )
                ''')
                
                # Create index for performance
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_audit_timestamp 
                    ON audit_log(timestamp)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_audit_user 
                    ON audit_log(user_id)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_audit_action 
                    ON audit_log(action)
                ''')
                
        except Exception as e:
            self.logger.error(f"Error initializing audit logging: {e}")
    
    def _load_password_policy(self) -> Dict:
        """Load password policy settings"""
        return {
            'min_length': self.config.get('security.password.min_length', 8),
            'require_uppercase': self.config.get('security.password.require_uppercase', True),
            'require_lowercase': self.config.get('security.password.require_lowercase', True),
            'require_numbers': self.config.get('security.password.require_numbers', True),
            'require_special': self.config.get('security.password.require_special', True),
            'max_age_days': self.config.get('security.password.max_age_days', 90),
            'history_count': self.config.get('security.password.history_count', 5)
        }
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        try:
            encrypted_data = self.cipher_suite.encrypt(data.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            self.logger.error(f"Encryption error: {e}")
            raise
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            decrypted_data = self.cipher_suite.decrypt(encrypted_bytes)
            return decrypted_data.decode()
        except Exception as e:
            self.logger.error(f"Decryption error: {e}")
            raise
    
    def hash_password(self, password: str, salt: bytes = None) -> tuple[str, str]:
        """Hash password with salt"""
        if salt is None:
            salt = secrets.token_bytes(32)
        
        # Use PBKDF2 with SHA-256
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = kdf.derive(password.encode())
        
        # Return base64 encoded hash and salt
        return (
            base64.b64encode(key).decode(),
            base64.b64encode(salt).decode()
        )
    
    def verify_password(self, password: str, stored_hash: str, stored_salt: str) -> bool:
        """Verify password against stored hash"""
        try:
            salt = base64.b64decode(stored_salt.encode())
            hash_to_check, _ = self.hash_password(password, salt)
            return secrets.compare_digest(hash_to_check, stored_hash)
        except Exception as e:
            self.logger.error(f"Password verification error: {e}")
            return False
    
    def validate_password_policy(self, password: str) -> tuple[bool, List[str]]:
        """Validate password against policy"""
        errors = []
        
        # Length check
        if len(password) < self.password_policy['min_length']:
            errors.append(f"Le mot de passe doit contenir au moins {self.password_policy['min_length']} caractères")
        
        # Character requirements
        if self.password_policy['require_uppercase'] and not any(c.isupper() for c in password):
            errors.append("Le mot de passe doit contenir au moins une majuscule")
        
        if self.password_policy['require_lowercase'] and not any(c.islower() for c in password):
            errors.append("Le mot de passe doit contenir au moins une minuscule")
        
        if self.password_policy['require_numbers'] and not any(c.isdigit() for c in password):
            errors.append("Le mot de passe doit contenir au moins un chiffre")
        
        if self.password_policy['require_special']:
            special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            if not any(c in special_chars for c in password):
                errors.append("Le mot de passe doit contenir au moins un caractère spécial")
        
        return len(errors) == 0, errors
    
    def check_user_permissions(self, user_role: str, required_permission: str) -> bool:
        """Check if user has required permission"""
        try:
            role_enum = UserRole(user_role)
            permissions = self.role_permissions.get(role_enum, [])
            return required_permission in permissions
        except ValueError:
            return False
    
    def log_audit_event(self, user_id: int, username: str, action: AuditAction,
                       resource_type: str = None, resource_id: str = None,
                       details: Dict = None, ip_address: str = None,
                       user_agent: str = None, success: bool = True,
                       error_message: str = None, session_id: str = None):
        """Log audit event"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO audit_log (
                        user_id, username, action, resource_type, resource_id,
                        details, ip_address, user_agent, success, error_message, session_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id, username, action.value, resource_type, resource_id,
                    json.dumps(details) if details else None,
                    ip_address, user_agent, success, error_message, session_id
                ))
                
        except Exception as e:
            self.logger.error(f"Error logging audit event: {e}")
    
    def get_audit_log(self, start_date: datetime = None, end_date: datetime = None,
                     user_id: int = None, action: AuditAction = None,
                     limit: int = 1000) -> List[AuditLogEntry]:
        """Retrieve audit log entries"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM audit_log WHERE 1=1"
                params = []
                
                if start_date:
                    query += " AND timestamp >= ?"
                    params.append(start_date.isoformat())
                
                if end_date:
                    query += " AND timestamp <= ?"
                    params.append(end_date.isoformat())
                
                if user_id:
                    query += " AND user_id = ?"
                    params.append(user_id)
                
                if action:
                    query += " AND action = ?"
                    params.append(action.value)
                
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                # Convert to AuditLogEntry objects
                entries = []
                for row in rows:
                    entries.append(AuditLogEntry(
                        timestamp=datetime.fromisoformat(row[1]),
                        user_id=row[2],
                        username=row[3],
                        action=AuditAction(row[4]),
                        resource_type=row[5],
                        resource_id=row[6],
                        details=json.loads(row[7]) if row[7] else {},
                        ip_address=row[8],
                        user_agent=row[9],
                        success=bool(row[10]),
                        error_message=row[11]
                    ))
                
                return entries
                
        except Exception as e:
            self.logger.error(f"Error retrieving audit log: {e}")
            return []
    
    def check_login_attempts(self, username: str) -> tuple[bool, int]:
        """Check if user is locked out due to failed login attempts"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Count failed login attempts in the last lockout period
                lockout_start = datetime.now() - timedelta(seconds=self.lockout_duration)
                
                cursor.execute('''
                    SELECT COUNT(*) FROM audit_log
                    WHERE username = ? AND action = 'login' AND success = FALSE
                    AND timestamp > ?
                ''', (username, lockout_start.isoformat()))
                
                failed_attempts = cursor.fetchone()[0]
                
                is_locked = failed_attempts >= self.max_login_attempts
                remaining_attempts = max(0, self.max_login_attempts - failed_attempts)
                
                return is_locked, remaining_attempts
                
        except Exception as e:
            self.logger.error(f"Error checking login attempts: {e}")
            return False, self.max_login_attempts
    
    def generate_session_token(self) -> str:
        """Generate secure session token"""
        return secrets.token_urlsafe(32)
    
    def create_user_session(self, user_id: int, session_token: str) -> bool:
        """Create user session"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Create sessions table if not exists
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        session_token TEXT UNIQUE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP NOT NULL,
                        is_active BOOLEAN DEFAULT TRUE,
                        ip_address TEXT,
                        user_agent TEXT
                    )
                ''')
                
                # Calculate expiration time
                expires_at = datetime.now() + timedelta(seconds=self.session_timeout)
                
                # Insert session
                cursor.execute('''
                    INSERT INTO user_sessions (user_id, session_token, expires_at)
                    VALUES (?, ?, ?)
                ''', (user_id, session_token, expires_at.isoformat()))
                
                return True
                
        except Exception as e:
            self.logger.error(f"Error creating user session: {e}")
            return False
    
    def validate_session(self, session_token: str) -> Optional[Dict]:
        """Validate user session"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT s.user_id, s.expires_at, u.username, u.role
                    FROM user_sessions s
                    JOIN users u ON s.user_id = u.id
                    WHERE s.session_token = ? AND s.is_active = TRUE
                ''', (session_token,))
                
                result = cursor.fetchone()
                if not result:
                    return None
                
                user_id, expires_at_str, username, role = result
                expires_at = datetime.fromisoformat(expires_at_str)
                
                # Check if session is expired
                if datetime.now() > expires_at:
                    # Deactivate expired session
                    cursor.execute('''
                        UPDATE user_sessions SET is_active = FALSE
                        WHERE session_token = ?
                    ''', (session_token,))
                    return None
                
                return {
                    'user_id': user_id,
                    'username': username,
                    'role': role,
                    'expires_at': expires_at
                }
                
        except Exception as e:
            self.logger.error(f"Error validating session: {e}")
            return None
    
    def invalidate_session(self, session_token: str) -> bool:
        """Invalidate user session"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE user_sessions SET is_active = FALSE
                    WHERE session_token = ?
                ''', (session_token,))
                
                return cursor.rowcount > 0
                
        except Exception as e:
            self.logger.error(f"Error invalidating session: {e}")
            return False
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE user_sessions SET is_active = FALSE
                    WHERE expires_at < ? AND is_active = TRUE
                ''', (datetime.now().isoformat(),))
                
                cleaned_count = cursor.rowcount
                self.logger.info(f"Cleaned up {cleaned_count} expired sessions")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up sessions: {e}")
    
    def get_security_report(self) -> Dict:
        """Generate security report"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Failed login attempts in last 24 hours
                yesterday = datetime.now() - timedelta(days=1)
                cursor.execute('''
                    SELECT COUNT(*) FROM audit_log
                    WHERE action = 'login' AND success = FALSE
                    AND timestamp > ?
                ''', (yesterday.isoformat(),))
                failed_logins_24h = cursor.fetchone()[0]
                
                # Active sessions
                cursor.execute('''
                    SELECT COUNT(*) FROM user_sessions
                    WHERE is_active = TRUE AND expires_at > ?
                ''', (datetime.now().isoformat(),))
                active_sessions = cursor.fetchone()[0]
                
                # Most active users (last 7 days)
                week_ago = datetime.now() - timedelta(days=7)
                cursor.execute('''
                    SELECT username, COUNT(*) as activity_count
                    FROM audit_log
                    WHERE timestamp > ?
                    GROUP BY username
                    ORDER BY activity_count DESC
                    LIMIT 10
                ''', (week_ago.isoformat(),))
                top_users = cursor.fetchall()
                
                # Security events by type
                cursor.execute('''
                    SELECT action, COUNT(*) as count
                    FROM audit_log
                    WHERE timestamp > ?
                    GROUP BY action
                    ORDER BY count DESC
                ''', (week_ago.isoformat(),))
                events_by_type = cursor.fetchall()
                
                return {
                    'failed_logins_24h': failed_logins_24h,
                    'active_sessions': active_sessions,
                    'top_users': top_users,
                    'events_by_type': events_by_type,
                    'generated_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error generating security report: {e}")
            return {}
    
    def backup_audit_log(self, backup_path: str) -> bool:
        """Backup audit log to external file"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM audit_log ORDER BY timestamp')
                
                audit_data = []
                for row in cursor.fetchall():
                    audit_data.append({
                        'id': row[0],
                        'timestamp': row[1],
                        'user_id': row[2],
                        'username': row[3],
                        'action': row[4],
                        'resource_type': row[5],
                        'resource_id': row[6],
                        'details': row[7],
                        'ip_address': row[8],
                        'user_agent': row[9],
                        'success': row[10],
                        'error_message': row[11],
                        'session_id': row[12]
                    })
                
                # Encrypt and save
                encrypted_data = self.encrypt_sensitive_data(json.dumps(audit_data, indent=2))
                
                with open(backup_path, 'w') as f:
                    f.write(encrypted_data)
                
                self.logger.info(f"Audit log backed up to {backup_path}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error backing up audit log: {e}")
            return False
    
    def check_gdpr_compliance(self) -> Dict:
        """Check GDPR compliance status"""
        compliance_status = {
            'data_encryption': True,  # We encrypt sensitive data
            'audit_logging': True,    # We log all activities
            'user_consent': False,    # Would need to implement consent tracking
            'data_retention': False,  # Would need to implement retention policies
            'right_to_erasure': False,  # Would need to implement data deletion
            'data_portability': True,  # We have export functionality
            'breach_notification': False,  # Would need to implement breach detection
            'privacy_by_design': True,  # Security is built-in
            'recommendations': []
        }
        
        # Add recommendations for non-compliant items
        if not compliance_status['user_consent']:
            compliance_status['recommendations'].append(
                "Implémenter un système de consentement utilisateur"
            )
        
        if not compliance_status['data_retention']:
            compliance_status['recommendations'].append(
                "Définir et implémenter des politiques de rétention des données"
            )
        
        if not compliance_status['right_to_erasure']:
            compliance_status['recommendations'].append(
                "Implémenter le droit à l'effacement des données"
            )
        
        if not compliance_status['breach_notification']:
            compliance_status['recommendations'].append(
                "Implémenter un système de détection et notification des violations"
            )
        
        return compliance_status
    
    def sanitize_input(self, input_data: str) -> str:
        """Sanitize user input to prevent injection attacks"""
        if not input_data:
            return ""
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '|', '`']
        sanitized = input_data
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        # Limit length
        max_length = 1000
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    def validate_file_upload(self, file_path: str, allowed_extensions: List[str]) -> tuple[bool, str]:
        """Validate file upload for security"""
        try:
            # Check file extension
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in allowed_extensions:
                return False, f"Extension de fichier non autorisée: {file_ext}"
            
            # Check file size (max 10MB)
            max_size = 10 * 1024 * 1024  # 10MB
            if os.path.getsize(file_path) > max_size:
                return False, "Fichier trop volumineux (max 10MB)"
            
            # Basic content validation
            try:
                with open(file_path, 'rb') as f:
                    header = f.read(512)
                    
                # Check for executable signatures
                executable_signatures = [
                    b'\x4d\x5a',  # PE executable
                    b'\x7f\x45\x4c\x46',  # ELF executable
                    b'\xfe\xed\xfa',  # Mach-O executable
                ]
                
                for sig in executable_signatures:
                    if header.startswith(sig):
                        return False, "Fichier exécutable détecté"
                
            except Exception:
                return False, "Impossible de lire le fichier"
            
            return True, "Fichier valide"
            
        except Exception as e:
            return False, f"Erreur de validation: {e}"