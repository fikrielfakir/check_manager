#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire de base de données pour le système de gestion de chèques
"""

import sqlite3
import logging
from datetime import datetime, date
from typing import List, Dict, Optional, Any
from pathlib import Path

class DatabaseManager:
    """Gestionnaire principal de la base de données"""
    
    def __init__(self, db_path: str = "cheques.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.init_database()
    
    def init_database(self):
        """Initialise la base de données avec toutes les tables nécessaires"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Table des banques
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS banks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        code TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        active BOOLEAN DEFAULT TRUE
                    )
                ''')
                
                # Table des agences
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS branches (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        bank_id INTEGER NOT NULL REFERENCES banks(id) ON DELETE CASCADE,
                        name TEXT NOT NULL,
                        address TEXT,
                        postal_code TEXT,
                        phone TEXT,
                        email TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        active BOOLEAN DEFAULT TRUE
                    )
                ''')
                
                # Table des clients
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS clients (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        type TEXT CHECK(type IN ('personne', 'entreprise')) NOT NULL,
                        name TEXT NOT NULL,
                        id_number TEXT,  -- CIN ou RC
                        vat_number TEXT, -- IF ou ICE
                        address TEXT,
                        phone TEXT,
                        email TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        active BOOLEAN DEFAULT TRUE
                    )
                ''')
                
                # Table des chèques
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cheques (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        amount DECIMAL(10,2) NOT NULL,
                        currency TEXT DEFAULT 'MAD',
                        issue_date DATE NOT NULL,
                        due_date DATE NOT NULL,
                        client_id INTEGER REFERENCES clients(id),
                        branch_id INTEGER REFERENCES branches(id),
                        status TEXT CHECK(status IN ('en_attente', 'encaisse', 'rejete', 'impaye', 'depose', 'annule')) DEFAULT 'en_attente',
                        cheque_number TEXT NOT NULL,
                        scan_path TEXT,
                        depositor_name TEXT,
                        invoice_number TEXT,
                        invoice_date DATE,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_by INTEGER,
                        UNIQUE(cheque_number, branch_id)
                    )
                ''')
                
                # Table des utilisateurs
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        role TEXT CHECK(role IN ('admin', 'comptable', 'agent', 'readonly')) NOT NULL,
                        full_name TEXT,
                        email TEXT,
                        active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP
                    )
                ''')
                
                # Table des notifications
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS notifications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        message TEXT NOT NULL,
                        cheque_id INTEGER REFERENCES cheques(id),
                        user_id INTEGER REFERENCES users(id),
                        read BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Table de l'historique des exports
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS export_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        filename TEXT NOT NULL,
                        export_type TEXT NOT NULL,
                        filters TEXT,
                        record_count INTEGER,
                        file_size INTEGER,
                        created_by INTEGER REFERENCES users(id),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Table des paramètres système
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        key TEXT UNIQUE NOT NULL,
                        value TEXT NOT NULL,
                        description TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Création des index pour optimiser les performances
                self._create_indexes(cursor)
                
                # Insertion des données par défaut
                self._insert_default_data(cursor)
                
                conn.commit()
                self.logger.info("✅ Base de données initialisée avec succès")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de l'initialisation de la base de données: {e}")
            raise
    
    def _create_indexes(self, cursor):
        """Crée les index pour optimiser les performances"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_cheques_status ON cheques(status)",
            "CREATE INDEX IF NOT EXISTS idx_cheques_due_date ON cheques(due_date)",
            "CREATE INDEX IF NOT EXISTS idx_cheques_client ON cheques(client_id)",
            "CREATE INDEX IF NOT EXISTS idx_cheques_branch ON cheques(branch_id)",
            "CREATE INDEX IF NOT EXISTS idx_cheques_number ON cheques(cheque_number)",
            "CREATE INDEX IF NOT EXISTS idx_branches_bank ON branches(bank_id)",
            "CREATE INDEX IF NOT EXISTS idx_clients_type ON clients(type)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
    
    def _insert_default_data(self, cursor):
        """Insert les données par défaut"""
        # Banques par défaut
        default_banks = [
            ("Crédit Agricole du Maroc", "CAM"),
            ("Attijariwafa Bank", "AWB"),
            ("Banque Populaire", "BP"),
            ("Crédit Immobilier et Hôtelier", "CIH"),
            ("BMCE Bank", "BMCE"),
            ("Société Générale Maroc", "SGMB"),
            ("Crédit du Maroc", "CDM"),
            ("Al Barid Bank", "ABB"),
            ("BMCI", "BMCI")
        ]
        
        for bank_name, bank_code in default_banks:
            cursor.execute(
                "INSERT OR IGNORE INTO banks (name, code) VALUES (?, ?)",
                (bank_name, bank_code)
            )
        
        # Utilisateur admin par défaut
        import hashlib
        admin_password = hashlib.sha256("admin123".encode()).hexdigest()
        cursor.execute(
            "INSERT OR IGNORE INTO users (username, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
            ("admin", admin_password, "admin", "Administrateur")
        )
        
        # Paramètres par défaut
        default_settings = [
            ("company_name", "Votre Entreprise", "Nom de l'entreprise"),
            ("notification_days", "3", "Nombre de jours avant échéance pour notification"),
            ("default_currency", "MAD", "Devise par défaut"),
            ("backup_enabled", "true", "Sauvegarde automatique activée"),
            ("export_format", "xlsx", "Format d'export par défaut")
        ]
        
        for key, value, description in default_settings:
            cursor.execute(
                "INSERT OR IGNORE INTO settings (key, value, description) VALUES (?, ?, ?)",
                (key, value, description)
            )
    
    # === MÉTHODES POUR LES BANQUES ===
    
    def get_banks(self, active_only: bool = True) -> List[Dict]:
        """Récupère la liste des banques"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM banks"
            if active_only:
                query += " WHERE active = TRUE"
            query += " ORDER BY name"
            
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def add_bank(self, name: str, code: str = None) -> int:
        """Ajoute une nouvelle banque"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO banks (name, code) VALUES (?, ?)",
                (name, code)
            )
            return cursor.lastrowid
    
    def update_bank(self, bank_id: int, name: str, code: str = None) -> bool:
        """Met à jour une banque"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE banks SET name = ?, code = ? WHERE id = ?",
                (name, code, bank_id)
            )
            return cursor.rowcount > 0
    
    def delete_bank(self, bank_id: int) -> bool:
        """Supprime une banque (soft delete)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE banks SET active = FALSE WHERE id = ?",
                (bank_id,)
            )
            return cursor.rowcount > 0
    
    # === MÉTHODES POUR LES AGENCES ===
    
    def get_branches(self, bank_id: int = None, active_only: bool = True) -> List[Dict]:
        """Récupère la liste des agences"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            query = """
                SELECT b.*, bk.name as bank_name 
                FROM branches b 
                JOIN banks bk ON b.bank_id = bk.id
            """
            params = []
            
            conditions = []
            if active_only:
                conditions.append("b.active = TRUE")
            if bank_id:
                conditions.append("b.bank_id = ?")
                params.append(bank_id)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY bk.name, b.name"
            
            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def add_branch(self, bank_id: int, name: str, address: str = None, 
                   postal_code: str = None, phone: str = None, email: str = None) -> int:
        """Ajoute une nouvelle agence"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO branches (bank_id, name, address, postal_code, phone, email) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (bank_id, name, address, postal_code, phone, email)
            )
            return cursor.lastrowid
    
    # === MÉTHODES POUR LES CLIENTS ===
    
    def get_clients(self, client_type: str = None, active_only: bool = True) -> List[Dict]:
        """Récupère la liste des clients"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM clients"
            params = []
            
            conditions = []
            if active_only:
                conditions.append("active = TRUE")
            if client_type:
                conditions.append("type = ?")
                params.append(client_type)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY name"
            
            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def add_client(self, client_type: str, name: str, id_number: str = None,
                   vat_number: str = None, address: str = None, 
                   phone: str = None, email: str = None) -> int:
        """Ajoute un nouveau client"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO clients (type, name, id_number, vat_number, address, phone, email) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (client_type, name, id_number, vat_number, address, phone, email)
            )
            return cursor.lastrowid
    
    def search_clients(self, search_term: str) -> List[Dict]:
        """Recherche des clients par nom"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM clients 
                   WHERE active = TRUE AND (name LIKE ? OR id_number LIKE ?) 
                   ORDER BY name LIMIT 10""",
                (f"%{search_term}%", f"%{search_term}%")
            )
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    # === MÉTHODES POUR LES CHÈQUES ===
    
    def add_cheque(self, cheque_data: Dict) -> int:
        """Ajoute un nouveau chèque"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO cheques (
                    amount, currency, issue_date, due_date, client_id, branch_id,
                    status, cheque_number, depositor_name, invoice_number, 
                    invoice_date, notes, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    cheque_data['amount'],
                    cheque_data.get('currency', 'MAD'),
                    cheque_data['issue_date'],
                    cheque_data['due_date'],
                    cheque_data.get('client_id'),
                    cheque_data['branch_id'],
                    cheque_data.get('status', 'en_attente'),
                    cheque_data['cheque_number'],
                    cheque_data.get('depositor_name'),
                    cheque_data.get('invoice_number'),
                    cheque_data.get('invoice_date'),
                    cheque_data.get('notes'),
                    cheque_data.get('created_by')
                )
            )
            return cursor.lastrowid
    
    def get_cheques(self, filters: Dict = None) -> List[Dict]:
        """Récupère les chèques avec filtres optionnels"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT c.*, 
                       cl.name as client_name, cl.type as client_type,
                       b.name as branch_name, bk.name as bank_name
                FROM cheques c
                LEFT JOIN clients cl ON c.client_id = cl.id
                LEFT JOIN branches b ON c.branch_id = b.id
                LEFT JOIN banks bk ON b.bank_id = bk.id
            """
            
            params = []
            conditions = []
            
            if filters:
                if 'status' in filters:
                    conditions.append("c.status = ?")
                    params.append(filters['status'])
                
                if 'bank_id' in filters:
                    conditions.append("bk.id = ?")
                    params.append(filters['bank_id'])
                
                if 'branch_id' in filters:
                    conditions.append("c.branch_id = ?")
                    params.append(filters['branch_id'])
                
                if 'client_id' in filters:
                    conditions.append("c.client_id = ?")
                    params.append(filters['client_id'])
                
                if 'date_from' in filters:
                    conditions.append("c.due_date >= ?")
                    params.append(filters['date_from'])
                
                if 'date_to' in filters:
                    conditions.append("c.due_date <= ?")
                    params.append(filters['date_to'])
                
                if 'amount_min' in filters:
                    conditions.append("c.amount >= ?")
                    params.append(filters['amount_min'])
                
                if 'amount_max' in filters:
                    conditions.append("c.amount <= ?")
                    params.append(filters['amount_max'])
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY c.due_date DESC, c.created_at DESC"
            
            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def update_cheque_status(self, cheque_id: int, new_status: str, user_id: int = None) -> bool:
        """Met à jour le statut d'un chèque"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE cheques SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (new_status, cheque_id)
            )
            
            # Créer une notification si nécessaire
            if cursor.rowcount > 0 and user_id:
                self._create_status_notification(cursor, cheque_id, new_status, user_id)
            
            return cursor.rowcount > 0
    
    def check_duplicate_cheque(self, cheque_number: str, branch_id: int) -> bool:
        """Vérifie si un chèque existe déjà"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM cheques WHERE cheque_number = ? AND branch_id = ?",
                (cheque_number, branch_id)
            )
            return cursor.fetchone()[0] > 0
    
    def get_cheques_due_soon(self, days: int = 3) -> List[Dict]:
        """Récupère les chèques arrivant à échéance bientôt"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT c.*, cl.name as client_name, b.name as branch_name, bk.name as bank_name
                   FROM cheques c
                   LEFT JOIN clients cl ON c.client_id = cl.id
                   LEFT JOIN branches b ON c.branch_id = b.id
                   LEFT JOIN banks bk ON b.bank_id = bk.id
                   WHERE c.status IN ('en_attente', 'depose') 
                   AND date(c.due_date) BETWEEN date('now') AND date('now', '+{} days')
                   ORDER BY c.due_date""".format(days)
            )
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    # === MÉTHODES POUR LES STATISTIQUES ===
    
    def get_dashboard_stats(self) -> Dict:
        """Récupère les statistiques pour le tableau de bord"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Total des chèques
            cursor.execute("SELECT COUNT(*) FROM cheques")
            stats['total_cheques'] = cursor.fetchone()[0]
            
            # Montant total
            cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM cheques")
            stats['total_amount'] = cursor.fetchone()[0]
            
            # Statistiques par statut
            cursor.execute("""
                SELECT status, COUNT(*), COALESCE(SUM(amount), 0)
                FROM cheques 
                GROUP BY status
            """)
            
            status_stats = {}
            for status, count, amount in cursor.fetchall():
                status_stats[status] = {'count': count, 'amount': amount}
            
            stats['by_status'] = status_stats
            
            # Chèques en retard
            cursor.execute("""
                SELECT COUNT(*) FROM cheques 
                WHERE status IN ('en_attente', 'depose') 
                AND date(due_date) < date('now')
            """)
            stats['overdue_count'] = cursor.fetchone()[0]
            
            # Top 5 banques
            cursor.execute("""
                SELECT bk.name, COUNT(*), COALESCE(SUM(c.amount), 0)
                FROM cheques c
                JOIN branches b ON c.branch_id = b.id
                JOIN banks bk ON b.bank_id = bk.id
                GROUP BY bk.id, bk.name
                ORDER BY SUM(c.amount) DESC
                LIMIT 5
            """)
            stats['top_banks'] = cursor.fetchall()
            
            return stats
    
    # === MÉTHODES POUR LES NOTIFICATIONS ===
    
    def _create_status_notification(self, cursor, cheque_id: int, new_status: str, user_id: int):
        """Crée une notification de changement de statut"""
        status_messages = {
            'encaisse': 'Chèque encaissé avec succès',
            'rejete': 'Chèque rejeté par la banque',
            'impaye': 'Chèque marqué comme impayé',
            'annule': 'Chèque annulé'
        }
        
        if new_status in status_messages:
            cursor.execute(
                """INSERT INTO notifications (type, title, message, cheque_id, user_id)
                   VALUES (?, ?, ?, ?, ?)""",
                ('status_change', 'Changement de statut', 
                 status_messages[new_status], cheque_id, user_id)
            )
    
    def create_due_notifications(self):
        """Crée des notifications pour les chèques arrivant à échéance"""
        cheques_due = self.get_cheques_due_soon()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for cheque in cheques_due:
                # Vérifier si une notification existe déjà
                cursor.execute(
                    """SELECT COUNT(*) FROM notifications 
                       WHERE type = 'due_soon' AND cheque_id = ? 
                       AND date(created_at) = date('now')""",
                    (cheque['id'],)
                )
                
                if cursor.fetchone()[0] == 0:
                    cursor.execute(
                        """INSERT INTO notifications (type, title, message, cheque_id)
                           VALUES (?, ?, ?, ?)""",
                        ('due_soon', 'Chèque arrivant à échéance',
                         f"Le chèque n°{cheque['cheque_number']} arrive à échéance le {cheque['due_date']}",
                         cheque['id'])
                    )
            
            conn.commit()
    
    def get_notifications(self, user_id: int = None, unread_only: bool = False) -> List[Dict]:
        """Récupère les notifications"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM notifications"
            params = []
            conditions = []
            
            if user_id:
                conditions.append("(user_id = ? OR user_id IS NULL)")
                params.append(user_id)
            
            if unread_only:
                conditions.append("read = FALSE")
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY created_at DESC LIMIT 50"
            
            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    # === MÉTHODES UTILITAIRES ===
    
    def get_setting(self, key: str, default_value: str = None) -> str:
        """Récupère une valeur de paramètre"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            result = cursor.fetchone()
            return result[0] if result else default_value
    
    def set_setting(self, key: str, value: str):
        """Définit une valeur de paramètre"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT OR REPLACE INTO settings (key, value, updated_at) 
                   VALUES (?, ?, CURRENT_TIMESTAMP)""",
                (key, value)
            )
    
    def backup_database(self, backup_path: str) -> bool:
        """Crée une sauvegarde de la base de données"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            self.logger.info(f"✅ Sauvegarde créée: {backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de la sauvegarde: {e}")
            return False
