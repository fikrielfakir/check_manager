#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automation Control Panel Dialog
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import threading

class AutomationDialog:
    """Dialog for automation control and monitoring"""
    
    def __init__(self, parent, automation_manager, current_user):
        self.parent = parent
        self.automation = automation_manager
        self.current_user = current_user
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("🤖 Panneau d'Automatisation")
        self.dialog.geometry("800x600")
        self.dialog.transient(parent)
        
        # Setup UI
        self.setup_ui()
        
        # Load initial data
        self.refresh_status()
    
    def setup_ui(self):
        """Setup the automation dialog UI"""
        # Main notebook
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Status tab
        self.create_status_tab(notebook)
        
        # Reminders tab
        self.create_reminders_tab(notebook)
        
        # API Integration tab
        self.create_api_tab(notebook)
        
        # Risk Analysis tab
        self.create_risk_tab(notebook)
        
        # Bulk Operations tab
        self.create_bulk_tab(notebook)
    
    def create_status_tab(self):
        """Create automation status tab"""
        status_frame = ttk.Frame(notebook)
        notebook.add(status_frame, text="📊 Statut")
        
        # Service status
        services_frame = ttk.LabelFrame(status_frame, text="Services d'Automatisation", padding=15)
        services_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Status indicators
        self.status_indicators = {}
        services = [
            ("reminders", "📧 Rappels Automatiques", "Actif"),
            ("api_sync", "🔄 Synchronisation API", "Inactif"),
            ("risk_analysis", "⚠️ Analyse de Risque", "Actif"),
            ("duplicate_detection", "🔍 Détection Doublons", "Actif"),
            ("bulk_import", "📥 Import en Masse", "Disponible")
        ]
        
        for i, (key, name, status) in enumerate(services):
            row = i // 2
            col = i % 2
            
            service_frame = ttk.Frame(services_frame)
            service_frame.grid(row=row, column=col, padx=10, pady=5, sticky="ew")
            
            ttk.Label(service_frame, text=name, font=('Arial', 10, 'bold')).pack(anchor="w")
            
            status_label = ttk.Label(service_frame, text=f"Statut: {status}")
            status_label.pack(anchor="w")
            
            self.status_indicators[key] = status_label
            
            services_frame.columnconfigure(col, weight=1)
        
        # Activity log
        log_frame = ttk.LabelFrame(status_frame, text="Journal d'Activité", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Log treeview
        columns = ('Heure', 'Service', 'Action', 'Résultat')
        self.log_tree = ttk.Treeview(log_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.log_tree.heading(col, text=col)
            self.log_tree.column(col, width=150)
        
        # Scrollbar
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_tree.yview)
        self.log_tree.configure(yscrollcommand=log_scroll.set)
        
        self.log_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_reminders_tab(self, notebook):
        """Create reminders management tab"""
        reminders_frame = ttk.Frame(notebook)
        notebook.add(reminders_frame, text="📧 Rappels")
        
        # Manual reminder sending
        manual_frame = ttk.LabelFrame(reminders_frame, text="Envoi Manuel", padding=15)
        manual_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(manual_frame, text="Envoyer des rappels pour les chèques arrivant à échéance").pack(anchor="w", pady=5)
        
        controls_frame = ttk.Frame(manual_frame)
        controls_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(controls_frame, text="📧 Envoyer Rappels Email", 
                  command=self.send_email_reminders).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="📱 Envoyer Rappels SMS", 
                  command=self.send_sms_reminders).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="📧📱 Envoyer Tous", 
                  command=self.send_all_reminders).pack(side=tk.LEFT, padx=5)
        
        # Reminder settings
        settings_frame = ttk.LabelFrame(reminders_frame, text="Paramètres", padding=15)
        settings_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Days before due date
        days_frame = ttk.Frame(settings_frame)
        days_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(days_frame, text="Jours avant échéance:").pack(side=tk.LEFT)
        self.reminder_days_var = tk.StringVar(value="3")
        ttk.Entry(days_frame, textvariable=self.reminder_days_var, width=5).pack(side=tk.LEFT, padx=(10, 0))
        
        # Auto-reminder toggle
        self.auto_reminders_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="Rappels automatiques activés", 
                       variable=self.auto_reminders_var).pack(anchor="w", pady=5)
        
        # Reminder history
        history_frame = ttk.LabelFrame(reminders_frame, text="Historique des Rappels", padding=10)
        history_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # History treeview
        columns = ('Date', 'Type', 'Destinataire', 'Chèque', 'Statut')
        self.reminder_tree = ttk.Treeview(history_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.reminder_tree.heading(col, text=col)
            self.reminder_tree.column(col, width=120)
        
        reminder_scroll = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.reminder_tree.yview)
        self.reminder_tree.configure(yscrollcommand=reminder_scroll.set)
        
        self.reminder_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        reminder_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_api_tab(self, notebook):
        """Create API integration tab"""
        api_frame = ttk.Frame(notebook)
        notebook.add(api_frame, text="🔄 API Banques")
        
        # API Status
        status_frame = ttk.LabelFrame(api_frame, text="Statut des APIs", padding=15)
        status_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Bank API status
        self.api_status = {}
        banks = [
            ("CIH Bank", "cih", "🔴 Inactif"),
            ("BMCE Bank", "bmce", "🔴 Inactif"),
            ("Attijariwafa Bank", "awb", "🔴 Inactif")
        ]
        
        for i, (bank_name, bank_code, status) in enumerate(banks):
            bank_frame = ttk.Frame(status_frame)
            bank_frame.grid(row=i, column=0, sticky="ew", pady=2)
            
            ttk.Label(bank_frame, text=bank_name, width=20).pack(side=tk.LEFT)
            
            status_label = ttk.Label(bank_frame, text=status)
            status_label.pack(side=tk.LEFT, padx=(10, 0))
            
            ttk.Button(bank_frame, text="⚙️ Configurer", 
                      command=lambda code=bank_code: self.configure_api(code)).pack(side=tk.RIGHT)
            
            self.api_status[bank_code] = status_label
            status_frame.columnconfigure(0, weight=1)
        
        # Manual sync
        sync_frame = ttk.LabelFrame(api_frame, text="Synchronisation Manuelle", padding=15)
        sync_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(sync_frame, text="Forcer la synchronisation avec les APIs bancaires").pack(anchor="w", pady=5)
        
        ttk.Button(sync_frame, text="🔄 Synchroniser Tout", 
                  command=self.force_sync_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(sync_frame, text="🔍 Tester Connexions", 
                  command=self.test_api_connections).pack(side=tk.LEFT, padx=5)
        
        # Sync log
        sync_log_frame = ttk.LabelFrame(api_frame, text="Journal de Synchronisation", padding=10)
        sync_log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ('Heure', 'Banque', 'Action', 'Résultat', 'Détails')
        self.sync_tree = ttk.Treeview(sync_log_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.sync_tree.heading(col, text=col)
            self.sync_tree.column(col, width=120)
        
        sync_scroll = ttk.Scrollbar(sync_log_frame, orient=tk.VERTICAL, command=self.sync_tree.yview)
        self.sync_tree.configure(yscrollcommand=sync_scroll.set)
        
        self.sync_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sync_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_risk_tab(self, notebook):
        """Create risk analysis tab"""
        risk_frame = ttk.Frame(notebook)
        notebook.add(risk_frame, text="⚠️ Analyse Risque")
        
        # Risk calculation
        calc_frame = ttk.LabelFrame(risk_frame, text="Calcul des Scores de Risque", padding=15)
        calc_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(calc_frame, text="Recalculer les scores de risque IA pour tous les clients").pack(anchor="w", pady=5)
        
        calc_controls = ttk.Frame(calc_frame)
        calc_controls.pack(fill=tk.X, pady=10)
        
        ttk.Button(calc_controls, text="🧠 Recalculer Tout", 
                  command=self.recalculate_risk_scores).pack(side=tk.LEFT, padx=5)
        ttk.Button(calc_controls, text="📊 Rapport Risque", 
                  command=self.generate_risk_report).pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        self.risk_progress = ttk.Progressbar(calc_frame, mode='determinate')
        self.risk_progress.pack(fill=tk.X, pady=5)
        
        # High-risk clients
        high_risk_frame = ttk.LabelFrame(risk_frame, text="Clients à Haut Risque", padding=10)
        high_risk_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ('Client', 'Score Risque', 'Taux Rejet', 'Dernière Activité', 'Actions')
        self.risk_tree = ttk.Treeview(high_risk_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.risk_tree.heading(col, text=col)
            self.risk_tree.column(col, width=120)
        
        risk_scroll = ttk.Scrollbar(high_risk_frame, orient=tk.VERTICAL, command=self.risk_tree.yview)
        self.risk_tree.configure(yscrollcommand=risk_scroll.set)
        
        self.risk_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        risk_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_bulk_tab(self, notebook):
        """Create bulk operations tab"""
        bulk_frame = ttk.Frame(notebook)
        notebook.add(bulk_frame, text="📥 Opérations en Masse")
        
        # Import section
        import_frame = ttk.LabelFrame(bulk_frame, text="Import de Chèques", padding=15)
        import_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # File selection
        file_frame = ttk.Frame(import_frame)
        file_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(file_frame, text="Fichier:").pack(side=tk.LEFT)
        
        self.import_file_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.import_file_var, width=50).pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Button(file_frame, text="📁 Parcourir", 
                  command=self.browse_import_file).pack(side=tk.LEFT, padx=(5, 0))
        
        # Import options
        options_frame = ttk.Frame(import_frame)
        options_frame.pack(fill=tk.X, pady=10)
        
        self.skip_duplicates_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Ignorer les doublons", 
                       variable=self.skip_duplicates_var).pack(side=tk.LEFT)
        
        self.validate_data_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Valider les données", 
                       variable=self.validate_data_var).pack(side=tk.LEFT, padx=(20, 0))
        
        # Import button
        ttk.Button(import_frame, text="📥 Importer", 
                  command=self.start_bulk_import).pack(pady=10)
        
        # Progress
        self.import_progress = ttk.Progressbar(import_frame, mode='determinate')
        self.import_progress.pack(fill=tk.X, pady=5)
        
        self.import_status_var = tk.StringVar(value="Prêt à importer")
        ttk.Label(import_frame, textvariable=self.import_status_var).pack(pady=5)
        
        # Duplicate detection
        duplicate_frame = ttk.LabelFrame(bulk_frame, text="Détection de Doublons", padding=15)
        duplicate_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(duplicate_frame, text="Rechercher et gérer les doublons dans la base de données").pack(anchor="w", pady=5)
        
        ttk.Button(duplicate_frame, text="🔍 Détecter Doublons", 
                  command=self.detect_duplicates).pack(side=tk.LEFT, padx=5)
        ttk.Button(duplicate_frame, text="📋 Rapport Doublons", 
                  command=self.show_duplicates_report).pack(side=tk.LEFT, padx=5)
    
    def refresh_status(self):
        """Refresh automation status"""
        # Update service status indicators
        current_time = datetime.now().strftime("%H:%M:%S")
        
        # Add sample log entries
        log_entries = [
            (current_time, "Rappels", "Vérification", "3 rappels envoyés"),
            ((datetime.now().replace(minute=datetime.now().minute-5)).strftime("%H:%M:%S"), 
             "Risque IA", "Calcul", "25 clients analysés"),
            ((datetime.now().replace(minute=datetime.now().minute-10)).strftime("%H:%M:%S"), 
             "Doublons", "Détection", "2 doublons trouvés")
        ]
        
        # Clear and populate log
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)
        
        for entry in log_entries:
            self.log_tree.insert('', tk.END, values=entry)
    
    # Action methods
    def send_email_reminders(self):
        """Send email reminders"""
        self.run_async_task(self._send_email_reminders, "Envoi des rappels email...")
    
    def send_sms_reminders(self):
        """Send SMS reminders"""
        self.run_async_task(self._send_sms_reminders, "Envoi des rappels SMS...")
    
    def send_all_reminders(self):
        """Send all reminders"""
        self.run_async_task(self._send_all_reminders, "Envoi de tous les rappels...")
    
    def _send_email_reminders(self):
        """Internal method to send email reminders"""
        try:
            result = self.automation.send_automated_reminders()
            return f"Emails envoyés: {result['emails_sent']}"
        except Exception as e:
            return f"Erreur: {e}"
    
    def _send_sms_reminders(self):
        """Internal method to send SMS reminders"""
        try:
            result = self.automation.send_automated_reminders()
            return f"SMS envoyés: {result['sms_sent']}"
        except Exception as e:
            return f"Erreur: {e}"
    
    def _send_all_reminders(self):
        """Internal method to send all reminders"""
        try:
            result = self.automation.send_automated_reminders()
            return f"Total: {result['emails_sent']} emails, {result['sms_sent']} SMS"
        except Exception as e:
            return f"Erreur: {e}"
    
    def configure_api(self, bank_code):
        """Configure bank API"""
        messagebox.showinfo("Configuration API", f"Configuration API pour {bank_code} à implémenter")
    
    def force_sync_all(self):
        """Force sync all APIs"""
        self.run_async_task(self._force_sync_all, "Synchronisation en cours...")
    
    def _force_sync_all(self):
        """Internal method to force sync"""
        # Simulate API sync
        import time
        time.sleep(2)
        return "Synchronisation terminée"
    
    def test_api_connections(self):
        """Test API connections"""
        messagebox.showinfo("Test API", "Test des connexions API à implémenter")
    
    def recalculate_risk_scores(self):
        """Recalculate risk scores"""
        self.run_async_task(self._recalculate_risk_scores, "Recalcul des scores de risque...")
    
    def _recalculate_risk_scores(self):
        """Internal method to recalculate risk scores"""
        try:
            # Get all clients and recalculate their risk scores
            clients = self.automation.db.get_clients()
            
            for i, client in enumerate(clients):
                # Update progress
                progress = (i + 1) / len(clients) * 100
                self.risk_progress['value'] = progress
                self.dialog.update()
                
                # Calculate risk score
                risk_score = self.automation.calculate_ai_risk_score(client['id'])
                
                # Small delay to show progress
                import time
                time.sleep(0.1)
            
            return f"Scores recalculés pour {len(clients)} clients"
            
        except Exception as e:
            return f"Erreur: {e}"
    
    def generate_risk_report(self):
        """Generate risk report"""
        messagebox.showinfo("Rapport Risque", "Génération du rapport de risque à implémenter")
    
    def browse_import_file(self):
        """Browse for import file"""
        from tkinter import filedialog
        
        file_path = filedialog.askopenfilename(
            title="Sélectionner le fichier à importer",
            filetypes=[
                ("Excel files", "*.xlsx *.xls"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.import_file_var.set(file_path)
    
    def start_bulk_import(self):
        """Start bulk import"""
        file_path = self.import_file_var.get()
        
        if not file_path:
            messagebox.showwarning("Attention", "Veuillez sélectionner un fichier")
            return
        
        self.run_async_task(lambda: self._bulk_import(file_path), "Import en cours...")
    
    def _bulk_import(self, file_path):
        """Internal method for bulk import"""
        try:
            # Determine file type
            file_type = 'excel' if file_path.endswith(('.xlsx', '.xls')) else 'csv'
            
            # Perform import
            result = self.automation.bulk_import_cheques(file_path, file_type)
            
            if result['success']:
                return f"Import réussi: {result['imported']} chèques importés"
            else:
                return f"Erreur d'import: {result['error']}"
                
        except Exception as e:
            return f"Erreur: {e}"
    
    def detect_duplicates(self):
        """Detect duplicates"""
        self.run_async_task(self._detect_duplicates, "Détection des doublons...")
    
    def _detect_duplicates(self):
        """Internal method to detect duplicates"""
        try:
            from analytics.advanced_analytics import AdvancedAnalytics
            analytics = AdvancedAnalytics(self.automation.db)
            
            duplicates = analytics.get_duplicate_detection_analysis()
            return f"Détection terminée: {len(duplicates)} doublons potentiels trouvés"
            
        except Exception as e:
            return f"Erreur: {e}"
    
    def show_duplicates_report(self):
        """Show duplicates report"""
        messagebox.showinfo("Rapport Doublons", "Rapport des doublons à implémenter")
    
    def run_async_task(self, task_func, status_message):
        """Run task asynchronously with status update"""
        def run_task():
            try:
                # Update status
                if hasattr(self, 'import_status_var'):
                    self.import_status_var.set(status_message)
                
                # Run task
                result = task_func()
                
                # Show result
                messagebox.showinfo("Résultat", result)
                
                # Reset status
                if hasattr(self, 'import_status_var'):
                    self.import_status_var.set("Terminé")
                
                # Refresh status
                self.refresh_status()
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'exécution: {e}")
                if hasattr(self, 'import_status_var'):
                    self.import_status_var.set("Erreur")
        
        # Run in separate thread
        thread = threading.Thread(target=run_task)
        thread.daemon = True
        thread.start()