#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dialogue de connexion
"""

import tkinter as tk
from tkinter import ttk, messagebox
import hashlib
import sqlite3

class LoginDialog:
    """Dialogue de connexion utilisateur"""
    
    def __init__(self, parent, db_manager):
        self.parent = parent
        self.db = db_manager
        self.user = None
        
        # Créer la fenêtre de dialogue
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("🔐 Connexion")
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        
        # Centrer la fenêtre
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Variables
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        
        # Interface utilisateur
        self.setup_ui()
        
        # Focus sur le champ username
        self.username_entry.focus()
        
        # Gérer la fermeture
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)
        
        # Raccourcis clavier
        self.dialog.bind('<Return>', lambda e: self.login())
        self.dialog.bind('<Escape>', lambda e: self.cancel())
    
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        # Frame principal
        main_frame = ttk.Frame(self.dialog, padding=30)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Logo/Titre
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 30))
        
        ttk.Label(title_frame, text="💳", font=('Arial', 32)).pack()
        ttk.Label(title_frame, text="Gestionnaire de Chèques Pro", 
                 font=('Arial', 14, 'bold')).pack(pady=(10, 0))
        ttk.Label(title_frame, text="Connexion requise", 
                 font=('Arial', 10)).pack(pady=(5, 0))
        
        # Formulaire de connexion
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Nom d'utilisateur
        ttk.Label(form_frame, text="Nom d'utilisateur:").pack(anchor=tk.W, pady=(0, 5))
        self.username_entry = ttk.Entry(form_frame, textvariable=self.username_var, 
                                       font=('Arial', 11), width=25)
        self.username_entry.pack(fill=tk.X, pady=(0, 15))
        
        # Mot de passe
        ttk.Label(form_frame, text="Mot de passe:").pack(anchor=tk.W, pady=(0, 5))
        self.password_entry = ttk.Entry(form_frame, textvariable=self.password_var, 
                                       show="*", font=('Arial', 11), width=25)
        self.password_entry.pack(fill=tk.X, pady=(0, 20))
        
        # Boutons
        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.pack(fill=tk.X)
        
        ttk.Button(buttons_frame, text="🔐 Se connecter", 
                  command=self.login).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(buttons_frame, text="❌ Annuler", 
                  command=self.cancel).pack(side=tk.LEFT)
        
        # Informations par défaut
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Label(info_frame, text="Compte par défaut:", 
                 font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        ttk.Label(info_frame, text="Utilisateur: admin", 
                 font=('Arial', 9)).pack(anchor=tk.W)
        ttk.Label(info_frame, text="Mot de passe: admin123", 
                 font=('Arial', 9)).pack(anchor=tk.W)
        
        # Pré-remplir avec les valeurs par défaut
        self.username_var.set("admin")
        self.password_var.set("admin123")
    
    def login(self):
        """Tente la connexion"""
        username = self.username_var.get().strip()
        password = self.password_var.get()
        
        if not username or not password:
            messagebox.showerror("Erreur", "Veuillez saisir le nom d'utilisateur et le mot de passe")
            return
        
        try:
            # Hacher le mot de passe
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Vérifier les identifiants
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, username, full_name, role, email, active
                    FROM users 
                    WHERE username = ? AND password_hash = ? AND active = TRUE
                """, (username, password_hash))
                
                user_data = cursor.fetchone()
                
                if user_data:
                    # Connexion réussie
                    self.user = {
                        'id': user_data[0],
                        'username': user_data[1],
                        'full_name': user_data[2],
                        'role': user_data[3],
                        'email': user_data[4],
                        'active': user_data[5]
                    }
                    
                    # Mettre à jour la dernière connexion
                    cursor.execute(
                        "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                        (self.user['id'],)
                    )
                    
                    self.dialog.destroy()
                else:
                    messagebox.showerror("Erreur", "Nom d'utilisateur ou mot de passe incorrect")
                    self.password_var.set("")
                    self.password_entry.focus()
                    
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la connexion: {e}")
    
    def cancel(self):
        """Annule la connexion"""
        self.user = None
        self.dialog.destroy()
