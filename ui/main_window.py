#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fenêtre principale de l'application
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from datetime import datetime

from .components.dashboard import DashboardFrame
from .components.cheque_form import ChequeFormFrame
from .components.cheque_list import ChequeListFrame
from .components.settings import SettingsFrame
from .components.reports import ReportsFrame
from .components.enhanced_dashboard import EnhancedDashboardFrame
from .components.mobile_responsive import MobileDashboard, DarkModeManager, KeyboardShortcutManager
from .components.advanced_search import AdvancedSearchFrame
from .dialogs.login_dialog import LoginDialog
from utils.theme import ThemeManager
from security.security_manager import SecurityManager
from analytics.advanced_analytics import AdvancedAnalytics
from automation.smart_automation import SmartAutomation

class MainWindow:
    """Fenêtre principale de l'application"""
    
    def __init__(self, root, db_manager, config):
        self.root = root
        self.db = db_manager
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.current_user = None
        
        # Initialize advanced components
        self.security_manager = SecurityManager(db_manager, config)
        self.analytics = AdvancedAnalytics(db_manager)
        self.automation = SmartAutomation(db_manager, config)
        
        # Gestionnaire de thème
        self.theme_manager = ThemeManager()
        self.dark_mode_manager = DarkModeManager()
        
        # Keyboard shortcuts
        self.keyboard_manager = None
        
        # Configuration de la fenêtre
        self.setup_window()
        
        # Authentification
        if not self.authenticate():
            self.root.quit()
            return
        
        # Interface utilisateur
        self.setup_ui()
        
        # Initialize keyboard shortcuts
        self.keyboard_manager = KeyboardShortcutManager(self.root)
        
        # Démarrage des tâches périodiques
        self.start_periodic_tasks()
    
    def setup_window(self):
        """Configure la fenêtre principale"""
        self.root.title("💳 Gestionnaire de Chèques Pro v3.0")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # Centrer la fenêtre
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1400 // 2)
        y = (self.root.winfo_screenheight() // 2) - (900 // 2)
        self.root.geometry(f"1400x900+{x}+{y}")
        
        # Appliquer le thème
        self.theme_manager.apply_theme(self.root)
        
        # Icône de l'application
        try:
            self.root.iconbitmap('assets/icon.ico')
        except:
            pass
    
    def authenticate(self) -> bool:
        """Gère l'authentification utilisateur"""
        login_dialog = LoginDialog(self.root, self.db)
        self.root.wait_window(login_dialog.dialog)
        
        if login_dialog.user:
            self.current_user = login_dialog.user
            self.logger.info(f"✅ Utilisateur connecté: {self.current_user['username']}")
            return True
        else:
            self.logger.info("❌ Authentification annulée")
            return False
    
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        # Barre de menu
        self.create_menu_bar()
        
        # Barre d'outils
        self.create_toolbar()
        
        # Zone principale avec onglets
        self.create_main_area()
        
        # Barre de statut
        self.create_status_bar()
    
    def create_menu_bar(self):
        """Crée la barre de menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menu Fichier
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="Nouveau chèque", command=self.new_cheque, accelerator="Ctrl+N")
        file_menu.add_separator()
        file_menu.add_command(label="Importer", command=self.import_data)
        file_menu.add_command(label="Exporter", command=self.export_data, accelerator="Ctrl+E")
        file_menu.add_separator()
        file_menu.add_command(label="Sauvegarde", command=self.backup_database)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.quit_application, accelerator="Ctrl+Q")
        
        # Menu Édition
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Édition", menu=edit_menu)
        edit_menu.add_command(label="Rechercher", command=self.search_cheques, accelerator="Ctrl+F")
        edit_menu.add_command(label="Filtres avancés", command=self.advanced_filters)
        
        # Menu Outils
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Outils", menu=tools_menu)
        tools_menu.add_command(label="🔍 Recherche Avancée", command=self.show_advanced_search)
        tools_menu.add_command(label="🤖 Automatisation", command=self.show_automation_panel)
        tools_menu.add_separator()
        tools_menu.add_command(label="Paramètres", command=self.open_settings)
        tools_menu.add_command(label="Notifications", command=self.show_notifications)
        tools_menu.add_separator()
        tools_menu.add_command(label="Vérifier les échéances", command=self.check_due_dates)
        
        # Menu Affichage
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Affichage", menu=view_menu)
        view_menu.add_command(label="🌙 Basculer Mode Sombre", command=self.toggle_dark_mode)
        view_menu.add_command(label="📱 Vue Mobile", command=self.toggle_mobile_view)
        view_menu.add_separator()
        view_menu.add_command(label="⌨️ Raccourcis Clavier", command=self.show_keyboard_shortcuts)
        
        # Menu Rapports
        reports_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Rapports", menu=reports_menu)
        reports_menu.add_command(label="Tableau de bord", command=self.show_dashboard)
        reports_menu.add_command(label="Rapport mensuel", command=self.monthly_report)
        reports_menu.add_command(label="Analyse par banque", command=self.bank_analysis)
        
        # Menu Aide
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Aide", menu=help_menu)
        help_menu.add_command(label="Guide utilisateur", command=self.show_help)
        help_menu.add_command(label="À propos", command=self.show_about)
        
        # Raccourcis clavier
        self.root.bind('<Control-n>', lambda e: self.new_cheque())
        self.root.bind('<Control-e>', lambda e: self.export_data())
        self.root.bind('<Control-f>', lambda e: self.search_cheques())
        self.root.bind('<Control-q>', lambda e: self.quit_application())
    
    def create_toolbar(self):
        """Crée la barre d'outils"""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=2)
        
        # Boutons principaux
        ttk.Button(toolbar, text="➕ Nouveau", command=self.new_cheque).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔍 Rechercher", command=self.search_cheques).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📊 Tableau de bord", command=self.show_dashboard).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        ttk.Button(toolbar, text="🔍 Recherche+", command=self.show_advanced_search).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📤 Exporter", command=self.export_data).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📋 Rapports", command=self.show_reports).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        ttk.Button(toolbar, text="🤖 Auto", command=self.show_automation_panel).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="⚙️ Paramètres", command=self.open_settings).pack(side=tk.LEFT, padx=2)
        
        # Informations utilisateur (à droite)
        user_frame = ttk.Frame(toolbar)
        user_frame.pack(side=tk.RIGHT)
        
        ttk.Label(user_frame, text=f"👤 {self.current_user['full_name'] or self.current_user['username']}").pack(side=tk.RIGHT, padx=5)
        ttk.Button(user_frame, text="🚪 Déconnexion", command=self.logout).pack(side=tk.RIGHT, padx=2)
    
    def create_main_area(self):
        """Crée la zone principale avec onglets"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Onglet Tableau de bord avancé
        self.dashboard_frame = EnhancedDashboardFrame(self.notebook, self.db, self.current_user, self.config)
        self.notebook.add(self.dashboard_frame, text="📊 Tableau de bord")
        
        # Onglet Nouveau chèque
        self.cheque_form_frame = ChequeFormFrame(self.notebook, self.db, self.current_user)
        self.notebook.add(self.cheque_form_frame, text="➕ Nouveau chèque")
        
        # Onglet Liste des chèques
        self.cheque_list_frame = ChequeListFrame(self.notebook, self.db, self.current_user)
        self.notebook.add(self.cheque_list_frame, text="📋 Liste des chèques")
        
        # Onglet Recherche avancée
        self.advanced_search_frame = AdvancedSearchFrame(
            self.notebook, self.db, self.on_search_results
        )
        self.notebook.add(self.advanced_search_frame, text="🔍 Recherche+")
        
        # Mobile dashboard (hidden by default)
        self.mobile_dashboard = None
        
        # Onglet Rapports
        self.reports_frame = ReportsFrame(self.notebook, self.db, self.current_user)
        self.notebook.add(self.reports_frame, text="📈 Rapports")
        
        # Onglet Paramètres (admin seulement)
        if self.current_user['role'] in ['admin']:
            self.settings_frame = SettingsFrame(self.notebook, self.db, self.current_user)
            self.notebook.add(self.settings_frame, text="⚙️ Paramètres")
    
    def create_status_bar(self):
        """Crée la barre de statut"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Statut principal
        self.status_var = tk.StringVar(value="Prêt")
        ttk.Label(self.status_bar, textvariable=self.status_var).pack(side=tk.LEFT, padx=5)
        
        # Séparateur
        ttk.Separator(self.status_bar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Notifications
        self.notifications_var = tk.StringVar(value="🔔 0")
        ttk.Label(self.status_bar, textvariable=self.notifications_var).pack(side=tk.LEFT, padx=5)
        
        # Heure
        self.time_var = tk.StringVar()
        ttk.Label(self.status_bar, textvariable=self.time_var).pack(side=tk.RIGHT, padx=5)
        
        # Mettre à jour l'heure
        self.update_time()
    
    def start_periodic_tasks(self):
        """Démarre les tâches périodiques"""
        # Vérifier les notifications toutes les 5 minutes
        self.check_notifications()
        self.root.after(300000, self.start_periodic_tasks)  # 5 minutes
    
    def check_notifications(self):
        """Vérifie et met à jour les notifications"""
        try:
            # Créer les notifications d'échéance
            self.db.create_due_notifications()
            
            # Run automation tasks
            self.run_automation_tasks()
            
            # Compter les notifications non lues
            notifications = self.db.get_notifications(self.current_user['id'], unread_only=True)
            count = len(notifications)
            
            self.notifications_var.set(f"🔔 {count}")
            
            if count > 0:
                self.status_var.set(f"{count} notification(s) non lue(s)")
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification des notifications: {e}")
    
    def run_automation_tasks(self):
        """Run periodic automation tasks"""
        try:
            # Send automated reminders
            reminder_result = self.automation.send_automated_reminders()
            
            # Log automation activity
            if reminder_result['sms_sent'] > 0 or reminder_result['emails_sent'] > 0:
                self.logger.info(f"Automation: {reminder_result['sms_sent']} SMS, {reminder_result['emails_sent']} emails sent")
                
        except Exception as e:
            self.logger.error(f"Error in automation tasks: {e}")
    
    def update_time(self):
        """Met à jour l'affichage de l'heure"""
        current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.time_var.set(current_time)
        self.root.after(1000, self.update_time)
    
    # === MÉTHODES D'ACTION ===
    
    def new_cheque(self):
        """Ouvre le formulaire de nouveau chèque"""
        self.notebook.select(1)  # Onglet formulaire
        self.cheque_form_frame.clear_form()
    
    def search_cheques(self):
        """Ouvre la recherche de chèques"""
        self.notebook.select(2)  # Onglet liste
        self.cheque_list_frame.focus_search()
    
    def show_dashboard(self):
        """Affiche le tableau de bord"""
        self.notebook.select(0)  # Onglet dashboard
        self.dashboard_frame.refresh_data()
    
    def show_reports(self):
        """Affiche les rapports"""
        self.notebook.select(3)  # Onglet rapports
    
    def show_advanced_search(self):
        """Show advanced search"""
        self.notebook.select(3)  # Advanced search tab
    
    def on_search_results(self, results):
        """Handle search results from advanced search"""
        # Switch to list view and update with results
        self.notebook.select(2)  # List tab
        # Update list with filtered results (would need to implement this method)
    
    def show_automation_panel(self):
        """Show automation control panel"""
        from .dialogs.automation_dialog import AutomationDialog
        AutomationDialog(self.root, self.automation, self.current_user)
    
    def toggle_dark_mode(self):
        """Toggle dark mode"""
        self.dark_mode_manager.toggle_dark_mode(self.root)
        self.status_var.set("Mode sombre basculé")
    
    def toggle_mobile_view(self):
        """Toggle mobile view"""
        if self.mobile_dashboard is None:
            # Create mobile dashboard
            mobile_window = tk.Toplevel(self.root)
            mobile_window.title("📱 Vue Mobile")
            mobile_window.geometry("400x800")
            
            self.mobile_dashboard = MobileDashboard(mobile_window, self.db, self.current_user)
            self.mobile_dashboard.pack(fill=tk.BOTH, expand=True)
        else:
            # Focus existing mobile window
            self.mobile_dashboard.master.lift()
    
    def show_keyboard_shortcuts(self):
        """Show keyboard shortcuts help"""
        if self.keyboard_manager:
            self.keyboard_manager.show_shortcuts_help()
    
    def open_settings(self):
        """Ouvre les paramètres"""
        if hasattr(self, 'settings_frame'):
            self.notebook.select(4)  # Onglet paramètres
        else:
            messagebox.showwarning("Accès refusé", "Vous n'avez pas les droits pour accéder aux paramètres.")
    
    def export_data(self):
        """Exporte les données"""
        self.reports_frame.show_export_dialog()
    
    def import_data(self):
        """Importe des données"""
        messagebox.showinfo("Import", "Fonctionnalité d'import à implémenter")
    
    def backup_database(self):
        """Crée une sauvegarde"""
        from tkinter import filedialog
        
        backup_path = filedialog.asksaveasfilename(
            title="Sauvegarder la base de données",
            defaultextension=".db",
            filetypes=[("Base de données", "*.db"), ("Tous les fichiers", "*.*")]
        )
        
        if backup_path:
            if self.db.backup_database(backup_path):
                messagebox.showinfo("Succès", "Sauvegarde créée avec succès!")
            else:
                messagebox.showerror("Erreur", "Erreur lors de la création de la sauvegarde")
    
    def advanced_filters(self):
        """Ouvre les filtres avancés"""
        self.cheque_list_frame.show_advanced_filters()
    
    def show_notifications(self):
        """Affiche les notifications"""
        from .dialogs.notifications_dialog import NotificationsDialog
        NotificationsDialog(self.root, self.db, self.current_user)
    
    def check_due_dates(self):
        """Vérifie manuellement les échéances"""
        self.check_notifications()
        messagebox.showinfo("Vérification", "Vérification des échéances terminée")
    
    def monthly_report(self):
        """Génère un rapport mensuel"""
        self.reports_frame.generate_monthly_report()
    
    def bank_analysis(self):
        """Affiche l'analyse par banque"""
        self.reports_frame.show_bank_analysis()
    
    def show_help(self):
        """Affiche l'aide"""
        help_text = """
        🏦 GESTIONNAIRE DE CHÈQUES PRO v3.0
        
        📋 FONCTIONNALITÉS PRINCIPALES:
        • Gestion complète des chèques
        • Suivi des statuts et échéances
        • Gestion des banques et agences
        • Gestion des clients
        • Rapports et exports
        • Notifications automatiques
        
        🔧 RACCOURCIS CLAVIER:
        • Ctrl+N : Nouveau chèque
        • Ctrl+F : Rechercher
        • Ctrl+E : Exporter
        • Ctrl+Q : Quitter
        
        📞 SUPPORT:
        Pour toute assistance, contactez l'administrateur système.
        """
        
        messagebox.showinfo("Guide utilisateur", help_text)
    
    def show_about(self):
        """Affiche les informations sur l'application"""
        about_text = """
        💳 Gestionnaire de Chèques Pro
        Version 3.0
        
        Développé avec Python et Tkinter
        
        © 2024 - Tous droits réservés
        
        Système complet de gestion de chèques
        avec fonctionnalités avancées.
        """
        
        messagebox.showinfo("À propos", about_text)
    
    def logout(self):
        """Déconnecte l'utilisateur"""
        if messagebox.askyesno("Déconnexion", "Voulez-vous vraiment vous déconnecter?"):
            self.root.quit()
    
    def quit_application(self):
        """Quitte l'application"""
        if messagebox.askyesno("Quitter", "Voulez-vous vraiment quitter l'application?"):
            self.logger.info("🔚 Fermeture de l'application")
            self.root.quit()
