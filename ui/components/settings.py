#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Composant paramètres et configuration
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import hashlib
from datetime import datetime

class SettingsFrame(ttk.Frame):
    """Frame pour les paramètres de l'application"""
    
    def __init__(self, parent, db_manager, current_user):
        super().__init__(parent)
        self.db = db_manager
        self.current_user = current_user
        
        # Vérifier les permissions
        if current_user['role'] != 'admin':
            self.show_access_denied()
            return
        
        # Interface utilisateur
        self.setup_ui()
        
        # Charger les données
        self.load_data()
    
    def show_access_denied(self):
        """Affiche un message d'accès refusé"""
        ttk.Label(self, text="🚫 Accès Refusé", 
                 font=('Arial', 16, 'bold')).pack(pady=50)
        ttk.Label(self, text="Vous n'avez pas les droits pour accéder aux paramètres.", 
                 font=('Arial', 12)).pack()
    
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        # Titre
        title_frame = ttk.Frame(self)
        title_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(title_frame, text="⚙️ Paramètres", 
                 font=('Arial', 16, 'bold')).pack(side=tk.LEFT)
        
        ttk.Button(title_frame, text="💾 Sauvegarder", 
                  command=self.save_settings).pack(side=tk.RIGHT)
        
        # Notebook pour les différentes sections
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Onglets
        self.create_banks_tab()
        self.create_users_tab()
        self.create_system_tab()
        self.create_backup_tab()
    
    def create_banks_tab(self):
        """Crée l'onglet gestion des banques"""
        banks_frame = ttk.Frame(self.notebook)
        self.notebook.add(banks_frame, text="🏦 Banques & Agences")
        
        # Section banques
        banks_section = ttk.LabelFrame(banks_frame, text="Gestion des Banques", padding=15)
        banks_section.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Contrôles banques
        banks_controls = ttk.Frame(banks_section)
        banks_controls.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(banks_controls, text="➕ Ajouter Banque", 
                  command=self.add_bank).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(banks_controls, text="✏️ Modifier", 
                  command=self.edit_bank).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(banks_controls, text="🗑️ Supprimer", 
                  command=self.delete_bank).pack(side=tk.LEFT)
        
        # Liste des banques
        banks_container = ttk.Frame(banks_section)
        banks_container.pack(fill=tk.BOTH, expand=True)
        
        columns = ('ID', 'Nom', 'Code', 'Agences', 'Statut')
        self.banks_tree = ttk.Treeview(banks_container, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.banks_tree.heading(col, text=col)
            self.banks_tree.column(col, width=100)
        
        banks_scroll = ttk.Scrollbar(banks_container, orient=tk.VERTICAL, command=self.banks_tree.yview)
        self.banks_tree.configure(yscrollcommand=banks_scroll.set)
        
        self.banks_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        banks_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Section agences
        branches_section = ttk.LabelFrame(banks_frame, text="Gestion des Agences", padding=15)
        branches_section.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Contrôles agences
        branches_controls = ttk.Frame(branches_section)
        branches_controls.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(branches_controls, text="➕ Ajouter Agence", 
                  command=self.add_branch).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(branches_controls, text="✏️ Modifier", 
                  command=self.edit_branch).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(branches_controls, text="🗑️ Supprimer", 
                  command=self.delete_branch).pack(side=tk.LEFT)
        
        # Liste des agences
        branches_container = ttk.Frame(branches_section)
        branches_container.pack(fill=tk.BOTH, expand=True)
        
        columns = ('ID', 'Banque', 'Nom', 'Adresse', 'Téléphone', 'Email')
        self.branches_tree = ttk.Treeview(branches_container, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.branches_tree.heading(col, text=col)
            self.branches_tree.column(col, width=120)
        
        branches_scroll = ttk.Scrollbar(branches_container, orient=tk.VERTICAL, command=self.branches_tree.yview)
        self.branches_tree.configure(yscrollcommand=branches_scroll.set)
        
        self.branches_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        branches_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_users_tab(self):
        """Crée l'onglet gestion des utilisateurs"""
        users_frame = ttk.Frame(self.notebook)
        self.notebook.add(users_frame, text="👥 Utilisateurs")
        
        # Contrôles
        controls_frame = ttk.Frame(users_frame)
        controls_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(controls_frame, text="➕ Nouvel Utilisateur", 
                  command=self.add_user).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(controls_frame, text="✏️ Modifier", 
                  command=self.edit_user).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(controls_frame, text="🔒 Changer Mot de Passe", 
                  command=self.change_password).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(controls_frame, text="🗑️ Supprimer", 
                  command=self.delete_user).pack(side=tk.LEFT)
        
        # Liste des utilisateurs
        users_container = ttk.Frame(users_frame)
        users_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ('ID', 'Nom d\'utilisateur', 'Nom complet', 'Rôle', 'Email', 'Statut', 'Dernière connexion')
        self.users_tree = ttk.Treeview(users_container, columns=columns, show='headings', height=12)
        
        for col in columns:
            self.users_tree.heading(col, text=col)
            self.users_tree.column(col, width=120)
        
        users_scroll = ttk.Scrollbar(users_container, orient=tk.VERTICAL, command=self.users_tree.yview)
        self.users_tree.configure(yscrollcommand=users_scroll.set)
        
        self.users_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        users_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_system_tab(self):
        """Crée l'onglet paramètres système"""
        system_frame = ttk.Frame(self.notebook)
        self.notebook.add(system_frame, text="🔧 Système")
        
        # Paramètres généraux
        general_section = ttk.LabelFrame(system_frame, text="Paramètres Généraux", padding=15)
        general_section.pack(fill=tk.X, padx=10, pady=10)
        
        # Nom de l'entreprise
        ttk.Label(general_section, text="Nom de l'entreprise:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.company_name_var = tk.StringVar()
        ttk.Entry(general_section, textvariable=self.company_name_var, width=40).grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Devise par défaut
        ttk.Label(general_section, text="Devise par défaut:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.default_currency_var = tk.StringVar()
        currency_combo = ttk.Combobox(general_section, textvariable=self.default_currency_var, 
                                     values=['MAD', 'EUR', 'USD'], state="readonly", width=10)
        currency_combo.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Paramètres de notifications
        notif_section = ttk.LabelFrame(system_frame, text="Notifications", padding=15)
        notif_section.pack(fill=tk.X, padx=10, pady=10)
        
        # Notifications activées
        self.notifications_enabled_var = tk.BooleanVar()
        ttk.Checkbutton(notif_section, text="Activer les notifications", 
                       variable=self.notifications_enabled_var).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # Jours avant échéance
        ttk.Label(notif_section, text="Jours avant échéance pour notification:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.notification_days_var = tk.StringVar()
        ttk.Entry(notif_section, textvariable=self.notification_days_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Paramètres d'export
        export_section = ttk.LabelFrame(system_frame, text="Exports", padding=15)
        export_section.pack(fill=tk.X, padx=10, pady=10)
        
        # Format par défaut
        ttk.Label(export_section, text="Format d'export par défaut:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.export_format_var = tk.StringVar()
        format_combo = ttk.Combobox(export_section, textvariable=self.export_format_var, 
                                   values=['xlsx', 'pdf', 'csv'], state="readonly", width=10)
        format_combo.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Répertoire d'export
        ttk.Label(export_section, text="Répertoire d'export:").grid(row=1, column=0, sticky=tk.W, pady=5)
        export_dir_frame = ttk.Frame(export_section)
        export_dir_frame.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        self.export_dir_var = tk.StringVar()
        ttk.Entry(export_dir_frame, textvariable=self.export_dir_var, width=30).pack(side=tk.LEFT)
        ttk.Button(export_dir_frame, text="📁", command=self.browse_export_dir).pack(side=tk.LEFT, padx=(5, 0))
    
    def create_backup_tab(self):
        """Crée l'onglet sauvegarde"""
        backup_frame = ttk.Frame(self.notebook)
        self.notebook.add(backup_frame, text="💾 Sauvegarde")
        
        # Sauvegarde manuelle
        manual_section = ttk.LabelFrame(backup_frame, text="Sauvegarde Manuelle", padding=15)
        manual_section.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(manual_section, text="Créer une sauvegarde de la base de données").pack(anchor=tk.W, pady=5)
        
        backup_controls = ttk.Frame(manual_section)
        backup_controls.pack(fill=tk.X, pady=10)
        
        ttk.Button(backup_controls, text="💾 Créer Sauvegarde", 
                  command=self.create_backup).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(backup_controls, text="📂 Restaurer", 
                  command=self.restore_backup).pack(side=tk.LEFT)
        
        # Sauvegarde automatique
        auto_section = ttk.LabelFrame(backup_frame, text="Sauvegarde Automatique", padding=15)
        auto_section.pack(fill=tk.X, padx=10, pady=10)
        
        self.auto_backup_var = tk.BooleanVar()
        ttk.Checkbutton(auto_section, text="Activer la sauvegarde automatique", 
                       variable=self.auto_backup_var).pack(anchor=tk.W, pady=5)
        
        interval_frame = ttk.Frame(auto_section)
        interval_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(interval_frame, text="Intervalle (heures):").pack(side=tk.LEFT)
        self.backup_interval_var = tk.StringVar()
        ttk.Entry(interval_frame, textvariable=self.backup_interval_var, width=10).pack(side=tk.LEFT, padx=(10, 0))
        
        # Historique des sauvegardes
        history_section = ttk.LabelFrame(backup_frame, text="Historique", padding=15)
        history_section.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ('Date', 'Fichier', 'Taille', 'Actions')
        self.backup_tree = ttk.Treeview(history_section, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.backup_tree.heading(col, text=col)
            self.backup_tree.column(col, width=150)
        
        backup_scroll = ttk.Scrollbar(history_section, orient=tk.VERTICAL, command=self.backup_tree.yview)
        self.backup_tree.configure(yscrollcommand=backup_scroll.set)
        
        self.backup_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        backup_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def load_data(self):
        """Charge les données dans les onglets"""
        self.load_banks_data()
        self.load_users_data()
        self.load_system_settings()
    
    def load_banks_data(self):
        """Charge les données des banques"""
        try:
            # Charger les banques
            banks = self.db.get_banks(active_only=False)
            
            # Vider le tree
            for item in self.banks_tree.get_children():
                self.banks_tree.delete(item)
            
            # Ajouter les banques
            for bank in banks:
                # Compter les agences
                branches = self.db.get_branches(bank['id'])
                branch_count = len(branches)
                
                status = "✅ Actif" if bank['active'] else "❌ Inactif"
                
                self.banks_tree.insert('', tk.END, values=(
                    bank['id'],
                    bank['name'],
                    bank.get('code', ''),
                    branch_count,
                    status
                ))
            
            # Charger les agences
            branches = self.db.get_branches(active_only=False)
            
            # Vider le tree
            for item in self.branches_tree.get_children():
                self.branches_tree.delete(item)
            
            # Ajouter les agences
            for branch in branches:
                self.branches_tree.insert('', tk.END, values=(
                    branch['id'],
                    branch['bank_name'],
                    branch['name'],
                    branch.get('address', ''),
                    branch.get('phone', ''),
                    branch.get('email', '')
                ))
                
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des banques: {e}")
    
    def load_users_data(self):
        """Charge les données des utilisateurs"""
        try:
            import sqlite3
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, username, full_name, role, email, active, last_login
                    FROM users ORDER BY username
                """)
                users = cursor.fetchall()
            
            # Vider le tree
            for item in self.users_tree.get_children():
                self.users_tree.delete(item)
            
            # Ajouter les utilisateurs
            for user in users:
                status = "✅ Actif" if user[5] else "❌ Inactif"
                last_login = user[6] if user[6] else "Jamais"
                
                self.users_tree.insert('', tk.END, values=(
                    user[0],  # ID
                    user[1],  # username
                    user[2] or '',  # full_name
                    user[3],  # role
                    user[4] or '',  # email
                    status,
                    last_login
                ))
                
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des utilisateurs: {e}")
    
    def load_system_settings(self):
        """Charge les paramètres système"""
        try:
            # Charger les paramètres
            self.company_name_var.set(self.db.get_setting('company_name', 'Votre Entreprise'))
            self.default_currency_var.set(self.db.get_setting('default_currency', 'MAD'))
            self.notifications_enabled_var.set(self.db.get_setting('notification_enabled', 'true') == 'true')
            self.notification_days_var.set(self.db.get_setting('notification_days', '3'))
            self.export_format_var.set(self.db.get_setting('export_format', 'xlsx'))
            self.export_dir_var.set(self.db.get_setting('export_dir', ''))
            self.auto_backup_var.set(self.db.get_setting('backup_enabled', 'true') == 'true')
            self.backup_interval_var.set(self.db.get_setting('backup_interval', '24'))
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des paramètres: {e}")
    
    def save_settings(self):
        """Sauvegarde tous les paramètres"""
        try:
            # Sauvegarder les paramètres système
            self.db.set_setting('company_name', self.company_name_var.get())
            self.db.set_setting('default_currency', self.default_currency_var.get())
            self.db.set_setting('notification_enabled', str(self.notifications_enabled_var.get()).lower())
            self.db.set_setting('notification_days', self.notification_days_var.get())
            self.db.set_setting('export_format', self.export_format_var.get())
            self.db.set_setting('export_dir', self.export_dir_var.get())
            self.db.set_setting('backup_enabled', str(self.auto_backup_var.get()).lower())
            self.db.set_setting('backup_interval', self.backup_interval_var.get())
            
            messagebox.showinfo("Succès", "Paramètres sauvegardés avec succès!")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {e}")
    
    # Méthodes pour la gestion des banques
    def add_bank(self):
        """Ajoute une nouvelle banque"""
        from ..dialogs.bank_dialog import BankDialog
        dialog = BankDialog(self, self.db)
        self.wait_window(dialog.dialog)
        
        if dialog.result:
            self.load_banks_data()
    
    def edit_bank(self):
        """Modifie la banque sélectionnée"""
        selection = self.banks_tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner une banque")
            return
        
        item = self.banks_tree.item(selection[0])
        bank_id = item['values'][0]
        
        from ..dialogs.bank_dialog import BankDialog
        dialog = BankDialog(self, self.db, bank_id)
        self.wait_window(dialog.dialog)
        
        if dialog.result:
            self.load_banks_data()
    
    def delete_bank(self):
        """Supprime la banque sélectionnée"""
        selection = self.banks_tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner une banque")
            return
        
        item = self.banks_tree.item(selection[0])
        bank_id = item['values'][0]
        bank_name = item['values'][1]
        
        if messagebox.askyesno("Confirmer", f"Supprimer la banque '{bank_name}'?"):
            try:
                self.db.delete_bank(bank_id)
                messagebox.showinfo("Succès", "Banque supprimée avec succès")
                self.load_banks_data()
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la suppression: {e}")
    
    def add_branch(self):
        """Ajoute une nouvelle agence"""
        from ..dialogs.branch_dialog import BranchDialog
        dialog = BranchDialog(self, self.db)
        self.wait_window(dialog.dialog)
        
        if dialog.result:
            self.load_banks_data()
    
    def edit_branch(self):
        """Modifie l'agence sélectionnée"""
        selection = self.branches_tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner une agence")
            return
        
        item = self.branches_tree.item(selection[0])
        branch_id = item['values'][0]
        
        from ..dialogs.branch_dialog import BranchDialog
        dialog = BranchDialog(self, self.db, branch_id)
        self.wait_window(dialog.dialog)
        
        if dialog.result:
            self.load_banks_data()
    
    def delete_branch(self):
        """Supprime l'agence sélectionnée"""
        selection = self.branches_tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner une agence")
            return
        
        item = self.branches_tree.item(selection[0])
        branch_id = item['values'][0]
        branch_name = item['values'][2]
        
        if messagebox.askyesno("Confirmer", f"Supprimer l'agence '{branch_name}'?"):
            try:
                import sqlite3
                with sqlite3.connect(self.db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE branches SET active = FALSE WHERE id = ?", (branch_id,))
                
                messagebox.showinfo("Succès", "Agence supprimée avec succès")
                self.load_banks_data()
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la suppression: {e}")
    
    # Méthodes pour la gestion des utilisateurs
    def add_user(self):
        """Ajoute un nouvel utilisateur"""
        from ..dialogs.user_dialog import UserDialog
        dialog = UserDialog(self, self.db)
        self.wait_window(dialog.dialog)
        
        if dialog.result:
            self.load_users_data()
    
    def edit_user(self):
        """Modifie l'utilisateur sélectionné"""
        selection = self.users_tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un utilisateur")
            return
        
        item = self.users_tree.item(selection[0])
        user_id = item['values'][0]
        
        from ..dialogs.user_dialog import UserDialog
        dialog = UserDialog(self, self.db, user_id)
        self.wait_window(dialog.dialog)
        
        if dialog.result:
            self.load_users_data()
    
    def change_password(self):
        """Change le mot de passe de l'utilisateur sélectionné"""
        selection = self.users_tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un utilisateur")
            return
        
        item = self.users_tree.item(selection[0])
        user_id = item['values'][0]
        username = item['values'][1]
        
        from ..dialogs.password_dialog import PasswordDialog
        dialog = PasswordDialog(self, self.db, user_id, username)
        self.wait_window(dialog.dialog)
        
        if dialog.result:
            messagebox.showinfo("Succès", "Mot de passe modifié avec succès")
    
    def delete_user(self):
        """Supprime l'utilisateur sélectionné"""
        selection = self.users_tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un utilisateur")
            return
        
        item = self.users_tree.item(selection[0])
        user_id = item['values'][0]
        username = item['values'][1]
        
        if user_id == self.current_user['id']:
            messagebox.showwarning("Attention", "Vous ne pouvez pas supprimer votre propre compte")
            return
        
        if messagebox.askyesno("Confirmer", f"Supprimer l'utilisateur '{username}'?"):
            try:
                import sqlite3
                with sqlite3.connect(self.db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET active = FALSE WHERE id = ?", (user_id,))
                
                messagebox.showinfo("Succès", "Utilisateur supprimé avec succès")
                self.load_users_data()
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la suppression: {e}")
    
    # Méthodes pour la sauvegarde
    def browse_export_dir(self):
        """Parcourt pour sélectionner le répertoire d'export"""
        directory = filedialog.askdirectory(title="Sélectionner le répertoire d'export")
        if directory:
            self.export_dir_var.set(directory)
    
    def create_backup(self):
        """Crée une sauvegarde manuelle"""
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
    
    def restore_backup(self):
        """Restaure une sauvegarde"""
        backup_path = filedialog.askopenfilename(
            title="Restaurer une sauvegarde",
            filetypes=[("Base de données", "*.db"), ("Tous les fichiers", "*.*")]
        )
        
        if backup_path:
            if messagebox.askyesno("Confirmer", 
                                  "La restauration remplacera toutes les données actuelles. Continuer?"):
                try:
                    import shutil
                    shutil.copy2(backup_path, self.db.db_path)
                    messagebox.showinfo("Succès", 
                                       "Sauvegarde restaurée avec succès!\n"
                                       "Redémarrez l'application pour voir les changements.")
                except Exception as e:
                    messagebox.showerror("Erreur", f"Erreur lors de la restauration: {e}")
