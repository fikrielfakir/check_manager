#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Automation Features for Cheque Management System
"""

import sqlite3
import requests
import smtplib
import json
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
import hashlib
import re

@dataclass
class BankAPIConfig:
    bank_name: str
    api_url: str
    api_key: str
    username: str
    password: str
    enabled: bool

@dataclass
class NotificationTemplate:
    template_id: str
    name: str
    subject: str
    body: str
    template_type: str  # 'sms' or 'email'

class SmartAutomation:
    """Smart automation engine for cheque management"""
    
    def __init__(self, db_manager, config_manager):
        self.db = db_manager
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Load bank API configurations
        self.bank_apis = self._load_bank_api_configs()
        
        # Load notification templates
        self.notification_templates = self._load_notification_templates()
    
    def _load_bank_api_configs(self) -> Dict[str, BankAPIConfig]:
        """Load bank API configurations"""
        # This would typically load from a secure configuration file
        return {
            'cih': BankAPIConfig(
                bank_name='CIH Bank',
                api_url='https://api.cih.ma/cheques',
                api_key=self.config.get('bank_apis.cih.api_key', ''),
                username=self.config.get('bank_apis.cih.username', ''),
                password=self.config.get('bank_apis.cih.password', ''),
                enabled=self.config.get('bank_apis.cih.enabled', False)
            ),
            'bmce': BankAPIConfig(
                bank_name='BMCE Bank',
                api_url='https://api.bmcebank.ma/cheques',
                api_key=self.config.get('bank_apis.bmce.api_key', ''),
                username=self.config.get('bank_apis.bmce.username', ''),
                password=self.config.get('bank_apis.bmce.password', ''),
                enabled=self.config.get('bank_apis.bmce.enabled', False)
            ),
            'awb': BankAPIConfig(
                bank_name='Attijariwafa Bank',
                api_url='https://api.attijariwafa.ma/cheques',
                api_key=self.config.get('bank_apis.awb.api_key', ''),
                username=self.config.get('bank_apis.awb.username', ''),
                password=self.config.get('bank_apis.awb.password', ''),
                enabled=self.config.get('bank_apis.awb.enabled', False)
            )
        }
    
    def _load_notification_templates(self) -> Dict[str, NotificationTemplate]:
        """Load notification templates"""
        return {
            'payment_reminder_sms': NotificationTemplate(
                template_id='payment_reminder_sms',
                name='Rappel de paiement SMS',
                subject='',
                body='Cher(e) {client_name}, votre chèque n°{cheque_number} d\'un montant de {amount} MAD arrive à échéance le {due_date}. Merci de vous assurer de la provision suffisante.',
                template_type='sms'
            ),
            'payment_reminder_email': NotificationTemplate(
                template_id='payment_reminder_email',
                name='Rappel de paiement Email',
                subject='Rappel d\'échéance - Chèque n°{cheque_number}',
                body='''
                Cher(e) {client_name},
                
                Nous vous rappelons que votre chèque n°{cheque_number} d'un montant de {amount} MAD 
                arrive à échéance le {due_date}.
                
                Merci de vous assurer que votre compte dispose de la provision suffisante.
                
                Cordialement,
                L'équipe de gestion
                ''',
                template_type='email'
            ),
            'cheque_bounced_sms': NotificationTemplate(
                template_id='cheque_bounced_sms',
                name='Chèque rejeté SMS',
                subject='',
                body='URGENT: Votre chèque n°{cheque_number} de {amount} MAD a été rejeté. Contactez-nous au plus vite.',
                template_type='sms'
            ),
            'cheque_processed_email': NotificationTemplate(
                template_id='cheque_processed_email',
                name='Chèque traité Email',
                subject='Confirmation de traitement - Chèque n°{cheque_number}',
                body='''
                Cher(e) {client_name},
                
                Nous vous confirmons que votre chèque n°{cheque_number} d'un montant de {amount} MAD 
                a été traité avec succès le {processing_date}.
                
                Statut: {status}
                
                Cordialement,
                L'équipe de gestion
                ''',
                template_type='email'
            )
        }
    
    async def update_cheque_status_from_bank_api(self, cheque_id: int) -> bool:
        """
        Update cheque status using bank API
        """
        try:
            # Get cheque details
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.cheque_number, c.amount, c.branch_id, b.bank_id, bk.code
                    FROM cheques c
                    JOIN branches b ON c.branch_id = b.id
                    JOIN banks bk ON b.bank_id = bk.id
                    WHERE c.id = ?
                """, (cheque_id,))
                
                result = cursor.fetchone()
                if not result:
                    return False
                
                cheque_number, amount, branch_id, bank_id, bank_code = result
            
            # Find appropriate bank API
            bank_api = None
            for api_key, api_config in self.bank_apis.items():
                if api_config.enabled and bank_code.lower() in api_key:
                    bank_api = api_config
                    break
            
            if not bank_api:
                self.logger.warning(f"No API configuration found for bank code: {bank_code}")
                return False
            
            # Call bank API
            headers = {
                'Authorization': f'Bearer {bank_api.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'cheque_number': cheque_number,
                'amount': amount,
                'branch_id': branch_id
            }
            
            response = requests.post(
                f"{bank_api.api_url}/status",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                api_data = response.json()
                new_status = self._map_bank_status_to_internal(api_data.get('status'))
                
                if new_status:
                    # Update cheque status
                    with sqlite3.connect(self.db.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE cheques 
                            SET status = ?, updated_at = CURRENT_TIMESTAMP 
                            WHERE id = ?
                        """, (new_status, cheque_id))
                    
                    self.logger.info(f"Updated cheque {cheque_id} status to {new_status} via API")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error updating cheque status from API: {e}")
            return False
    
    def _map_bank_status_to_internal(self, bank_status: str) -> Optional[str]:
        """Map bank API status to internal status"""
        status_mapping = {
            'cleared': 'encaisse',
            'bounced': 'rejete',
            'returned': 'rejete',
            'pending': 'en_attente',
            'processing': 'depose',
            'cancelled': 'annule'
        }
        
        return status_mapping.get(bank_status.lower())
    
    def send_automated_reminders(self) -> Dict[str, int]:
        """
        Send automated payment reminders
        """
        try:
            # Get cheques due in the next 3 days
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        c.id, c.cheque_number, c.amount, c.due_date,
                        cl.name as client_name, cl.phone, cl.email
                    FROM cheques c
                    LEFT JOIN clients cl ON c.client_id = cl.id
                    WHERE c.status IN ('en_attente', 'depose')
                    AND date(c.due_date) BETWEEN date('now') AND date('now', '+3 days')
                    AND cl.id IS NOT NULL
                """)
                
                due_cheques = cursor.fetchall()
            
            sms_sent = 0
            emails_sent = 0
            
            for cheque in due_cheques:
                cheque_id, cheque_number, amount, due_date, client_name, phone, email = cheque
                
                # Check if reminder already sent today
                if self._reminder_already_sent_today(cheque_id):
                    continue
                
                # Prepare template variables
                template_vars = {
                    'client_name': client_name or 'Client',
                    'cheque_number': cheque_number,
                    'amount': f"{amount:,.2f}",
                    'due_date': due_date
                }
                
                # Send SMS reminder
                if phone and self._is_valid_phone(phone):
                    if self._send_sms_reminder(phone, template_vars):
                        sms_sent += 1
                
                # Send email reminder
                if email and self._is_valid_email(email):
                    if self._send_email_reminder(email, template_vars):
                        emails_sent += 1
                
                # Log reminder sent
                self._log_reminder_sent(cheque_id, 'payment_reminder')
            
            return {
                'sms_sent': sms_sent,
                'emails_sent': emails_sent,
                'total_cheques': len(due_cheques)
            }
            
        except Exception as e:
            self.logger.error(f"Error sending automated reminders: {e}")
            return {'sms_sent': 0, 'emails_sent': 0, 'total_cheques': 0}
    
    def _reminder_already_sent_today(self, cheque_id: int) -> bool:
        """Check if reminder was already sent today"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM notifications 
                    WHERE cheque_id = ? 
                    AND type = 'payment_reminder'
                    AND date(created_at) = date('now')
                """, (cheque_id,))
                
                return cursor.fetchone()[0] > 0
        except:
            return False
    
    def _send_sms_reminder(self, phone: str, template_vars: Dict) -> bool:
        """Send SMS reminder"""
        try:
            template = self.notification_templates['payment_reminder_sms']
            message = template.body.format(**template_vars)
            
            # SMS Gateway integration (example with a generic SMS API)
            sms_api_url = self.config.get('sms.api_url', '')
            sms_api_key = self.config.get('sms.api_key', '')
            
            if not sms_api_url or not sms_api_key:
                self.logger.warning("SMS API not configured")
                return False
            
            payload = {
                'to': phone,
                'message': message,
                'from': self.config.get('sms.sender_id', 'ChequeManager')
            }
            
            headers = {
                'Authorization': f'Bearer {sms_api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(sms_api_url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                self.logger.info(f"SMS reminder sent to {phone}")
                return True
            else:
                self.logger.error(f"Failed to send SMS: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending SMS reminder: {e}")
            return False
    
    def _send_email_reminder(self, email: str, template_vars: Dict) -> bool:
        """Send email reminder"""
        try:
            template = self.notification_templates['payment_reminder_email']
            subject = template.subject.format(**template_vars)
            body = template.body.format(**template_vars)
            
            # Email configuration
            smtp_server = self.config.get('email.smtp_server', 'smtp.gmail.com')
            smtp_port = self.config.get('email.smtp_port', 587)
            smtp_username = self.config.get('email.username', '')
            smtp_password = self.config.get('email.password', '')
            sender_email = self.config.get('email.sender', smtp_username)
            
            if not smtp_username or not smtp_password:
                self.logger.warning("Email configuration not complete")
                return False
            
            # Create message
            msg = MimeMultipart()
            msg['From'] = sender_email
            msg['To'] = email
            msg['Subject'] = subject
            
            msg.attach(MimeText(body, 'plain', 'utf-8'))
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            self.logger.info(f"Email reminder sent to {email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending email reminder: {e}")
            return False
    
    def _is_valid_phone(self, phone: str) -> bool:
        """Validate phone number format"""
        # Moroccan phone number validation
        phone_pattern = r'^(\+212|0)[5-7]\d{8}$'
        return bool(re.match(phone_pattern, phone.replace(' ', '').replace('-', '')))
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))
    
    def _log_reminder_sent(self, cheque_id: int, reminder_type: str):
        """Log that a reminder was sent"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO notifications (type, title, message, cheque_id, created_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    reminder_type,
                    'Rappel automatique envoyé',
                    f'Rappel de paiement envoyé pour le chèque ID {cheque_id}',
                    cheque_id
                ))
        except Exception as e:
            self.logger.error(f"Error logging reminder: {e}")
    
    def calculate_ai_risk_score(self, client_id: int) -> float:
        """
        Calculate AI-powered client risk score using machine learning features
        """
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Get comprehensive client data
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_cheques,
                        SUM(amount) as total_amount,
                        AVG(amount) as avg_amount,
                        SUM(CASE WHEN status IN ('rejete', 'impaye') THEN 1 ELSE 0 END) as bounced_count,
                        AVG(julianday(updated_at) - julianday(created_at)) as avg_processing_time,
                        COUNT(DISTINCT strftime('%Y-%m', created_at)) as active_months,
                        MAX(created_at) as last_cheque_date,
                        MIN(created_at) as first_cheque_date,
                        COUNT(DISTINCT branch_id) as banks_used
                    FROM cheques 
                    WHERE client_id = ?
                """, (client_id,))
                
                data = cursor.fetchone()
                if not data or data[0] == 0:
                    return 50.0  # Default neutral score
                
                # Extract features
                total_cheques, total_amount, avg_amount, bounced_count, avg_processing_time, active_months, last_cheque_date, first_cheque_date, banks_used = data
                
                # Calculate feature scores
                bounce_rate = (bounced_count / total_cheques) if total_cheques > 0 else 0
                
                # Recency score (how recent is the last activity)
                try:
                    last_date = datetime.strptime(last_cheque_date, '%Y-%m-%d %H:%M:%S')
                    days_since_last = (datetime.now() - last_date).days
                    recency_score = max(0, 100 - days_since_last / 30 * 10)  # Decrease score over time
                except:
                    recency_score = 0
                
                # Volume consistency score
                volume_score = min(100, total_cheques * 2)  # More cheques = lower risk
                
                # Amount consistency score
                amount_variance_score = 100 - min(50, (avg_amount / 1000))  # Higher amounts = higher risk
                
                # Processing time score
                processing_score = max(0, 100 - avg_processing_time * 2) if avg_processing_time else 100
                
                # Diversification score (using multiple banks)
                diversification_score = min(100, banks_used * 20)
                
                # Weighted risk calculation
                risk_score = (
                    bounce_rate * 40 +  # 40% weight on bounce rate
                    (100 - recency_score) * 0.15 +  # 15% weight on recency
                    (100 - volume_score) * 0.15 +  # 15% weight on volume
                    amount_variance_score * 0.10 +  # 10% weight on amount variance
                    (100 - processing_score) * 0.10 +  # 10% weight on processing time
                    (100 - diversification_score) * 0.10  # 10% weight on diversification
                )
                
                return min(100, max(0, risk_score))
                
        except Exception as e:
            self.logger.error(f"Error calculating AI risk score: {e}")
            return 50.0
    
    def detect_advanced_duplicates(self, cheque_data: Dict) -> List[Dict]:
        """
        Advanced duplicate detection with fuzzy matching
        """
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Search for potential duplicates using multiple criteria
                cursor.execute("""
                    SELECT 
                        id, cheque_number, amount, client_id, created_at, branch_id
                    FROM cheques 
                    WHERE (
                        cheque_number = ? OR
                        (amount = ? AND client_id = ?) OR
                        (abs(amount - ?) < 0.01 AND client_id = ? AND 
                         abs(julianday(created_at) - julianday('now')) <= 30)
                    )
                    ORDER BY created_at DESC
                    LIMIT 10
                """, (
                    cheque_data.get('cheque_number'),
                    cheque_data.get('amount'),
                    cheque_data.get('client_id'),
                    cheque_data.get('amount'),
                    cheque_data.get('client_id')
                ))
                
                potential_matches = cursor.fetchall()
                duplicates = []
                
                for match in potential_matches:
                    similarity_score = self._calculate_cheque_similarity(cheque_data, {
                        'id': match[0],
                        'cheque_number': match[1],
                        'amount': match[2],
                        'client_id': match[3],
                        'created_at': match[4],
                        'branch_id': match[5]
                    })
                    
                    if similarity_score > 0.7:  # 70% similarity threshold
                        duplicates.append({
                            'existing_cheque_id': match[0],
                            'similarity_score': round(similarity_score * 100, 1),
                            'match_criteria': self._get_duplicate_reasons(cheque_data, match)
                        })
                
                return duplicates
                
        except Exception as e:
            self.logger.error(f"Error in advanced duplicate detection: {e}")
            return []
    
    def _calculate_cheque_similarity(self, cheque1: Dict, cheque2: Dict) -> float:
        """Calculate similarity between two cheques"""
        score = 0
        
        # Exact cheque number match (50% weight)
        if cheque1.get('cheque_number') == cheque2.get('cheque_number'):
            score += 0.5
        
        # Exact amount match (30% weight)
        if abs(float(cheque1.get('amount', 0)) - float(cheque2.get('amount', 0))) < 0.01:
            score += 0.3
        
        # Same client (15% weight)
        if cheque1.get('client_id') == cheque2.get('client_id'):
            score += 0.15
        
        # Same branch (5% weight)
        if cheque1.get('branch_id') == cheque2.get('branch_id'):
            score += 0.05
        
        return min(score, 1.0)
    
    def _get_duplicate_reasons(self, cheque1: Dict, cheque2_tuple) -> List[str]:
        """Get reasons why cheques might be duplicates"""
        reasons = []
        
        if cheque1.get('cheque_number') == cheque2_tuple[1]:
            reasons.append("Même numéro de chèque")
        
        if abs(float(cheque1.get('amount', 0)) - float(cheque2_tuple[2])) < 0.01:
            reasons.append("Même montant")
        
        if cheque1.get('client_id') == cheque2_tuple[3]:
            reasons.append("Même client")
        
        if cheque1.get('branch_id') == cheque2_tuple[5]:
            reasons.append("Même agence")
        
        return reasons
    
    def bulk_import_cheques(self, file_path: str, file_type: str = 'excel') -> Dict:
        """
        Bulk import cheques from Excel/CSV with validation
        """
        try:
            import pandas as pd
            
            # Read file based on type
            if file_type.lower() == 'excel':
                df = pd.read_excel(file_path)
            else:
                df = pd.read_csv(file_path)
            
            # Validate required columns
            required_columns = ['cheque_number', 'amount', 'due_date', 'client_name']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return {
                    'success': False,
                    'error': f'Colonnes manquantes: {", ".join(missing_columns)}',
                    'imported': 0,
                    'errors': []
                }
            
            imported_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Validate and process each row
                    validation_result = self._validate_import_row(row)
                    
                    if validation_result['valid']:
                        # Import the cheque
                        cheque_data = validation_result['data']
                        
                        # Check for duplicates
                        duplicates = self.detect_advanced_duplicates(cheque_data)
                        
                        if not duplicates:
                            cheque_id = self.db.add_cheque(cheque_data)
                            imported_count += 1
                        else:
                            errors.append(f"Ligne {index + 2}: Doublon détecté")
                    else:
                        errors.append(f"Ligne {index + 2}: {validation_result['error']}")
                        
                except Exception as e:
                    errors.append(f"Ligne {index + 2}: Erreur - {str(e)}")
            
            return {
                'success': True,
                'imported': imported_count,
                'total_rows': len(df),
                'errors': errors
            }
            
        except Exception as e:
            self.logger.error(f"Error in bulk import: {e}")
            return {
                'success': False,
                'error': str(e),
                'imported': 0,
                'errors': []
            }
    
    def _validate_import_row(self, row) -> Dict:
        """Validate a single import row"""
        try:
            # Extract and validate data
            cheque_number = str(row['cheque_number']).strip()
            if not cheque_number:
                return {'valid': False, 'error': 'Numéro de chèque manquant'}
            
            try:
                amount = float(row['amount'])
                if amount <= 0:
                    return {'valid': False, 'error': 'Montant invalide'}
            except:
                return {'valid': False, 'error': 'Montant non numérique'}
            
            # Validate date
            try:
                due_date = pd.to_datetime(row['due_date']).strftime('%Y-%m-%d')
            except:
                return {'valid': False, 'error': 'Date d\'échéance invalide'}
            
            # Find or create client
            client_name = str(row['client_name']).strip()
            if not client_name:
                return {'valid': False, 'error': 'Nom du client manquant'}
            
            # Find client ID
            client_id = self._find_or_create_client(client_name, row)
            
            # Find branch ID
            branch_name = row.get('branch_name', '').strip()
            branch_id = self._find_branch_id(branch_name) if branch_name else None
            
            if not branch_id:
                return {'valid': False, 'error': 'Agence non trouvée'}
            
            return {
                'valid': True,
                'data': {
                    'cheque_number': cheque_number,
                    'amount': amount,
                    'due_date': due_date,
                    'issue_date': due_date,  # Default to due date if not provided
                    'client_id': client_id,
                    'branch_id': branch_id,
                    'status': 'en_attente',
                    'currency': row.get('currency', 'MAD'),
                    'depositor_name': row.get('depositor_name', ''),
                    'notes': row.get('notes', ''),
                    'created_by': 1  # System import
                }
            }
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def _find_or_create_client(self, client_name: str, row) -> int:
        """Find existing client or create new one"""
        try:
            # Search for existing client
            clients = self.db.search_clients(client_name)
            
            if clients:
                return clients[0]['id']
            
            # Create new client
            client_id = self.db.add_client(
                client_type=row.get('client_type', 'personne'),
                name=client_name,
                phone=row.get('client_phone', ''),
                email=row.get('client_email', ''),
                address=row.get('client_address', '')
            )
            
            return client_id
            
        except Exception as e:
            self.logger.error(f"Error finding/creating client: {e}")
            return None
    
    def _find_branch_id(self, branch_name: str) -> Optional[int]:
        """Find branch ID by name"""
        try:
            branches = self.db.get_branches()
            
            for branch in branches:
                if branch_name.lower() in branch['name'].lower():
                    return branch['id']
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding branch: {e}")
            return None