#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Formulaire de saisie de chèques
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
from datetime import datetime, date
import os

class ChequeFormFrame(ttk.Frame):
    """Frame pour le formulaire de saisie de chèques"""
    
    def __init__(self, parent, db_manager, current_user):
        super().__init__(parent)
        self.db = db_manager
        self.current_user = current_user
        
        # Variables du formulaire
        self.init_variables()
        
        # Interface utilisateur
        self.setup_ui()
        
        # Chargement des données
        self.load_form_data()
    
    def init_variables(self):
        """Initialise les variables du formulaire"""
        self.amount_var = tk.StringVar()
        self.currency_var = tk.StringVar(value="MAD")
        self.cheque_number_var = tk.StringVar()
        self.depositor_name_var = tk.StringVar()
        self.invoice_number_var = tk.StringVar()
        self.notes_var = tk.StringVar()
        self.client_var = tk.StringVar()
        self.branch_var = tk.StringVar()
        self.status_var = tk.StringVar(value="en_attente")
        
        # Variables pour les clients
        self.client_type_var = tk.StringVar(value="personne")
        self.client_name_var = tk.StringVar()
        self.client_id_number_var = tk.StringVar()
        self.client_vat_number_var = tk.StringVar()
        self.client_address_var = tk.StringVar()
        self.client_phone_var = tk.StringVar()
        self.client_email_var = tk.StringVar()
        
        # Données de référence
        self.clients_data = []
        self.branches_data = []
        self.banks_data = []
    
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        # Conteneur principal avec scrollbar
        main_canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Titre
        title_frame = ttk.Frame(scrollable_frame)
        title_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(title_frame, text="➕ Nouveau Chèque", 
                 font=('Arial', 16, 'bold')).pack(side=tk.LEFT)
        
        ttk.Button(title_frame, text="🗑️ Effacer", 
                  command=self.clear_form).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(title_frame, text="💾 Enregistrer", 
                  command=self.save_cheque).pack(side=tk.RIGHT)
        
        # Section informations du chèque
        self.create_cheque_section(scrollable_frame)
        
        # Section client
        self.create_client_section(scrollable_frame)
        
        # Section banque et agence
        self.create_bank_section(scrollable_frame)
        
        # Section complémentaire
        self.create_additional_section(scrollable_frame)
        
        # Section scan
        self.create_scan_section(scrollable_frame)
    
    def create_cheque_section(self, parent):
        """Crée la section des informations du chèque"""
        section = ttk.LabelFrame(parent, text="📋 Informations du Chèque", padding=15)
        section.pack(fill=tk.X, padx=20, pady=10)
        
        # Ligne 1: Numéro et Montant
        row1 = ttk.Frame(section)
        row1.pack(fill=tk.X, pady=5)
        
        ttk.Label(row1, text="N° Chèque *:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        cheque_entry = ttk.Entry(row1, textvariable=self.cheque_number_var, width=20)
        cheque_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 30))
        cheque_entry.bind('<FocusOut>', self.check_duplicate)
        
        ttk.Label(row1, text="Montant *:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        amount_frame = ttk.Frame(row1)
        amount_frame.grid(row=0, column=3, sticky=tk.W)
        
        ttk.Entry(amount_frame, textvariable=self.amount_var, width=15).pack(side=tk.LEFT)
        ttk.Combobox(amount_frame, textvariable=self.currency_var, 
                    values=["MAD", "EUR", "USD"], width=8, state="readonly").pack(side=tk.LEFT, padx=(5, 0))
        
        # Ligne 2: Dates
        row2 = ttk.Frame(section)
        row2.pack(fill=tk.X, pady=5)
        
        ttk.Label(row2, text="Date d'émission *:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.issue_date = DateEntry(row2, width=12, background='darkblue',
                                   foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
        self.issue_date.grid(row=0, column=1, sticky=tk.W, padx=(0, 30))
        
        ttk.Label(row2, text="Date d'échéance *:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.due_date = DateEntry(row2, width=12, background='darkblue',
                                 foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
        self.due_date.grid(row=0, column=3, sticky=tk.W)
        
        # Ligne 3: Déposant et Statut
        row3 = ttk.Frame(section)
        row3.pack(fill=tk.X, pady=5)
        
        ttk.Label(row3, text="Nom du Déposant:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Entry(row3, textvariable=self.depositor_name_var, width=25).grid(row=0, column=1, sticky=tk.W, padx=(0, 30))
        
        ttk.Label(row3, text="Statut:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        status_combo = ttk.Combobox(row3, textvariable=self.status_var, width=15, state="readonly")
        status_combo['values'] = ['en_attente', 'encaisse', 'rejete', 'impaye', 'depose', 'annule']
        status_combo.grid(row=0, column=3, sticky=tk.W)
        
        # Indicateur de doublon
        self.duplicate_label = ttk.Label(section, text="", foreground="red")
        self.duplicate_label.pack(anchor=tk.W, pady=5)
    
    def create_client_section(self, parent):
        """Crée la section client avec toggle personne/entreprise"""
        section = ttk.LabelFrame(parent, text="👤 Informations Client", padding=15)
        section.pack(fill=tk.X, padx=20, pady=10)
        
        # Toggle type de client
        type_frame = ttk.Frame(section)
        type_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(type_frame, text="Type de client:").pack(side=tk.LEFT)
        ttk.Radiobutton(type_frame, text="🔘 Personne", variable=self.client_type_var, 
                       value="personne", command=self.toggle_client_fields).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Radiobutton(type_frame, text="🔘 Entreprise", variable=self.client_type_var, 
                       value="entreprise", command=self.toggle_client_fields).pack(side=tk.LEFT, padx=(10, 0))
        
        # Recherche client existant
        search_frame = ttk.Frame(section)
        search_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(search_frame, text="Rechercher client:").pack(side=tk.LEFT)
        self.client_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.client_search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(10, 0))
        search_entry.bind('<KeyRelease>', self.search_clients)
        
        # Liste des suggestions
        self.client_listbox = tk.Listbox(section, height=3)
        self.client_listbox.pack(fill=tk.X, pady=5)
        self.client_listbox.bind('<Double-Button-1>', self.select_client)
        
        # Champs client
        self.client_fields_frame = ttk.Frame(section)
        self.client_fields_frame.pack(fill=tk.X, pady=10)
        
        # Nom/Raison sociale
        name_frame = ttk.Frame(self.client_fields_frame)
        name_frame.pack(fill=tk.X, pady=2)
        
        self.client_name_label = ttk.Label(name_frame, text="Nom et prénom:")
        self.client_name_label.pack(side=tk.LEFT)
        ttk.Entry(name_frame, textvariable=self.client_name_var, width=40).pack(side=tk.LEFT, padx=(10, 0))
        
        # ID Number (CIN/RC)
        id_frame = ttk.Frame(self.client_fields_frame)
        id_frame.pack(fill=tk.X, pady=2)
        
        self.client_id_label = ttk.Label(id_frame, text="CIN:")
        self.client_id_label.pack(side=tk.LEFT)
        ttk.Entry(id_frame, textvariable=self.client_id_number_var, width=20).pack(side=tk.LEFT, padx=(10, 0))
        
        # VAT Number (IF/ICE)
        vat_frame = ttk.Frame(self.client_fields_frame)
        vat_frame.pack(fill=tk.X, pady=2)
        
        self.client_vat_label = ttk.Label(vat_frame, text="IF:")
        self.client_vat_label.pack(side=tk.LEFT)
        ttk.Entry(vat_frame, textvariable=self.client_vat_number_var, width=20).pack(side=tk.LEFT, padx=(10, 0))
        
        # Adresse
        address_frame = ttk.Frame(self.client_fields_frame)
        address_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(address_frame, text="Adresse:").pack(side=tk.LEFT)
        ttk.Entry(address_frame, textvariable=self.client_address_var, width=50).pack(side=tk.LEFT, padx=(10, 0))
        
        # Contact
        contact_frame = ttk.Frame(self.client_fields_frame)
        contact_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(contact_frame, text="Téléphone:").pack(side=tk.LEFT)
        ttk.Entry(contact_frame, textvariable=self.client_phone_var, width=15).pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Label(contact_frame, text="Email:").pack(side=tk.LEFT, padx=(20, 0))
        ttk.Entry(contact_frame, textvariable=self.client_email_var, width=25).pack(side=tk.LEFT, padx=(10, 0))
        
        # Bouton ajouter client
        ttk.Button(section, text="➕ Ajouter comme nouveau client", 
                  command=self.add_new_client).pack(pady=10)
        
        # Initialiser l'affichage
        self.toggle_client_fields()
    
    def create_bank_section(self, parent):
        """Crée la section banque et agence"""
        section = ttk.LabelFrame(parent, text="🏦 Banque et Agence", padding=15)
        section.pack(fill=tk.X, padx=20, pady=10)
        
        # Sélection de l'agence (format: Nom Banque - Agence)
        branch_frame = ttk.Frame(section)
        branch_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(branch_frame, text="Agence de dépôt *:").pack(side=tk.LEFT)
        self.branch_combo = ttk.Combobox(branch_frame, textvariable=self.branch_var, 
                                        width=50, state="readonly")
        self.branch_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Bouton gestion des banques/agences
        ttk.Button(branch_frame, text="⚙️ Gérer", 
                  command=self.manage_banks).pack(side=tk.RIGHT)
    
    def create_additional_section(self, parent):
        """Crée la section des informations complémentaires"""
        section = ttk.LabelFrame(parent, text="📄 Informations Complémentaires", padding=15)
        section.pack(fill=tk.X, padx=20, pady=10)
        
        # Ligne 1: Facture
        row1 = ttk.Frame(section)
        row1.pack(fill=tk.X, pady=5)
        
        ttk.Label(row1, text="N° Facture:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Entry(row1, textvariable=self.invoice_number_var, width=20).grid(row=0, column=1, sticky=tk.W, padx=(0, 30))
        
        ttk.Label(row1, text="Date Facture:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.invoice_date = DateEntry(row1, width=12, background='darkblue',
                                     foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
        self.invoice_date.grid(row=0, column=3, sticky=tk.W)
        
        # Ligne 2: Notes
        row2 = ttk.Frame(section)
        row2.pack(fill=tk.X, pady=5)
        
        ttk.Label(row2, text="Notes:").pack(anchor=tk.W)
        notes_text = tk.Text(row2, height=3, width=60)
        notes_text.pack(fill=tk.X, pady=5)
        
        # Lier le Text widget à la variable
        def update_notes(*args):
            self.notes_var.set(notes_text.get(1.0, tk.END).strip())
        
        notes_text.bind('<KeyRelease>', update_notes)
        self.notes_text = notes_text
    
    def create_scan_section(self, parent):
        """Crée la section pour le scan du chèque"""
        section = ttk.LabelFrame(parent, text="📷 Scan du Chèque", padding=15)
        section.pack(fill=tk.X, padx=20, pady=10)
        
        scan_frame = ttk.Frame(section)
        scan_frame.pack(fill=tk.X)
        
        self.scan_path_var = tk.StringVar()
        ttk.Entry(scan_frame, textvariable=self.scan_path_var, width=50, state="readonly").pack(side=tk.LEFT)
        
        ttk.Button(scan_frame, text="📁 Parcourir", 
                  command=self.browse_scan_file).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(scan_frame, text="👁️ Aperçu", 
                  command=self.preview_scan).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(scan_frame, text="🗑️ Supprimer", 
                  command=self.remove_scan).pack(side=tk.LEFT, padx=(5, 0))
    
    def load_form_data(self):
        """Charge les données nécessaires au formulaire"""
        try:
            # Charger les clients
            self.clients_data = self.db.get_clients()
            
            # Charger les agences avec leurs banques
            self.branches_data = self.db.get_branches()
            
            # Mettre à jour la combobox des agences
            branch_options = []
            for branch in self.branches_data:
                option = f"{branch['bank_name']} - {branch['name']}"
                branch_options.append(option)
            
            self.branch_combo['values'] = branch_options
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des données: {e}")
    
    def toggle_client_fields(self):
        """Bascule l'affichage des champs selon le type de client"""
        client_type = self.client_type_var.get()
        
        if client_type == "personne":
            self.client_name_label.config(text="Nom et prénom:")
            self.client_id_label.config(text="CIN:")
            self.client_vat_label.config(text="IF:")
        else:  # entreprise
            self.client_name_label.config(text="Raison sociale:")
            self.client_id_label.config(text="RC:")
            self.client_vat_label.config(text="ICE:")
    
    def search_clients(self, event=None):
        """Recherche des clients en temps réel"""
        search_term = self.client_search_var.get()
        
        if len(search_term) < 2:
            self.client_listbox.delete(0, tk.END)
            return
        
        try:
            clients = self.db.search_clients(search_term)
            
            self.client_listbox.delete(0, tk.END)
            for client in clients:
                display_text = f"{client['name']} ({client['type']})"
                if client['id_number']:
                    display_text += f" - {client['id_number']}"
                self.client_listbox.insert(tk.END, display_text)
                
        except Exception as e:
            print(f"Erreur lors de la recherche: {e}")
    
    def select_client(self, event=None):
        """Sélectionne un client depuis la liste"""
        selection = self.client_listbox.curselection()
        if not selection:
            return
        
        try:
            # Récupérer le client sélectionné
            selected_text = self.client_listbox.get(selection[0])
            client_name = selected_text.split(' (')[0]
            
            # Trouver le client dans les données
            selected_client = None
            for client in self.clients_data:
                if client['name'] == client_name:
                    selected_client = client
                    break
            
            if selected_client:
                # Remplir les champs
                self.client_type_var.set(selected_client['type'])
                self.client_name_var.set(selected_client['name'])
                self.client_id_number_var.set(selected_client['id_number'] or '')
                self.client_vat_number_var.set(selected_client['vat_number'] or '')
                self.client_address_var.set(selected_client['address'] or '')
                self.client_phone_var.set(selected_client['phone'] or '')
                self.client_email_var.set(selected_client['email'] or '')
                
                # Mettre à jour l'affichage
                self.toggle_client_fields()
                
                # Vider la recherche
                self.client_search_var.set('')
                self.client_listbox.delete(0, tk.END)
                
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sélection: {e}")
    
    def add_new_client(self):
        """Ajoute un nouveau client à la base de données"""
        if not self.client_name_var.get().strip():
            messagebox.showwarning("Attention", "Veuillez saisir le nom du client")
            return
        
        try:
            client_id = self.db.add_client(
                client_type=self.client_type_var.get(),
                name=self.client_name_var.get().strip(),
                id_number=self.client_id_number_var.get().strip() or None,
                vat_number=self.client_vat_number_var.get().strip() or None,
                address=self.client_address_var.get().strip() or None,
                phone=self.client_phone_var.get().strip() or None,
                email=self.client_email_var.get().strip() or None
            )
            
            messagebox.showinfo("Succès", "Client ajouté avec succès!")
            
            # Recharger les données
            self.load_form_data()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'ajout du client: {e}")
    
    def check_duplicate(self, event=None):
        """Vérifie les doublons de numéro de chèque"""
        cheque_number = self.cheque_number_var.get().strip()
        branch_selection = self.branch_var.get()
        
        if not cheque_number or not branch_selection:
            self.duplicate_label.config(text="")
            return
        
        try:
            # Trouver l'ID de l'agence
            branch_id = None
            for branch in self.branches_data:
                if f"{branch['bank_name']} - {branch['name']}" == branch_selection:
                    branch_id = branch['id']
                    break
            
            if branch_id and self.db.check_duplicate_cheque(cheque_number, branch_id):
                self.duplicate_label.config(text="⚠️ Ce numéro de chèque existe déjà pour cette agence!")
            else:
                self.duplicate_label.config(text="")
                
        except Exception as e:
            print(f"Erreur lors de la vérification: {e}")
    
    def browse_scan_file(self):
        """Parcourt pour sélectionner un fichier de scan"""
        file_path = filedialog.askopenfilename(
            title="Sélectionner le scan du chèque",
            filetypes=[
                ("Images", "*.jpg *.jpeg *.png *.bmp *.gif"),
                ("PDF", "*.pdf"),
                ("Tous les fichiers", "*.*")
            ]
        )
        
        if file_path:
            self.scan_path_var.set(file_path)
    
    def preview_scan(self):
        """Affiche un aperçu du scan"""
        scan_path = self.scan_path_var.get()
        if not scan_path or not os.path.exists(scan_path):
            messagebox.showwarning("Attention", "Aucun fichier de scan sélectionné")
            return
        
        try:
            # Ouvrir le fichier avec l'application par défaut
            if os.name == 'nt':  # Windows
                os.startfile(scan_path)
            elif os.name == 'posix':  # macOS et Linux
                os.system(f'open "{scan_path}"')
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le fichier: {e}")
    
    def remove_scan(self):
        """Supprime le scan sélectionné"""
        self.scan_path_var.set("")
    
    def manage_banks(self):
        """Ouvre la gestion des banques et agences"""
        from ..dialogs.bank_management_dialog import BankManagementDialog
        dialog = BankManagementDialog(self, self.db)
        self.wait_window(dialog.dialog)
        
        # Recharger les données après modification
        self.load_form_data()
    
    def validate_form(self):
        """Valide le formulaire avant sauvegarde"""
        errors = []
        
        # Champs obligatoires
        if not self.cheque_number_var.get().strip():
            errors.append("• Numéro de chèque requis")
        
        if not self.amount_var.get().strip():
            errors.append("• Montant requis")
        else:
            try:
                amount = float(self.amount_var.get().replace(',', '.'))
                if amount <= 0:
                    errors.append("• Le montant doit être positif")
            except ValueError:
                errors.append("• Montant invalide")
        
        if not self.branch_var.get():
            errors.append("• Agence de dépôt requise")
        
        # Dates
        try:
            issue_date = self.issue_date.get_date()
            due_date = self.due_date.get_date()
            
            if due_date < issue_date:
                errors.append("• La date d'échéance ne peut pas être antérieure à la date d'émission")
        except:
            errors.append("• Dates invalides")
        
        return errors
    
    def save_cheque(self):
        """Sauvegarde le chèque"""
        # Validation
        errors = self.validate_form()
        if errors:
            messagebox.showerror("Erreurs de validation", "\n".join(errors))
            return
        
        try:
            # Trouver l'ID de l'agence
            branch_id = None
            branch_selection = self.branch_var.get()
            for branch in self.branches_data:
                if f"{branch['bank_name']} - {branch['name']}" == branch_selection:
                    branch_id = branch['id']
                    break
            
            # Ajouter le client s'il n'existe pas
            client_id = None
            if self.client_name_var.get().strip():
                client_id = self.db.add_client(
                    client_type=self.client_type_var.get(),
                    name=self.client_name_var.get().strip(),
                    id_number=self.client_id_number_var.get().strip() or None,
                    vat_number=self.client_vat_number_var.get().strip() or None,
                    address=self.client_address_var.get().strip() or None,
                    phone=self.client_phone_var.get().strip() or None,
                    email=self.client_email_var.get().strip() or None
                )
            
            # Préparer les données du chèque
            cheque_data = {
                'amount': float(self.amount_var.get().replace(',', '.')),
                'currency': self.currency_var.get(),
                'issue_date': self.issue_date.get_date().strftime('%Y-%m-%d'),
                'due_date': self.due_date.get_date().strftime('%Y-%m-%d'),
                'client_id': client_id,
                'branch_id': branch_id,
                'status': self.status_var.get(),
                'cheque_number': self.cheque_number_var.get().strip(),
                'depositor_name': self.depositor_name_var.get().strip() or None,
                'invoice_number': self.invoice_number_var.get().strip() or None,
                'invoice_date': self.invoice_date.get_date().strftime('%Y-%m-%d') if self.invoice_date.get() else None,
                'notes': self.notes_var.get().strip() or None,
                'scan_path': self.scan_path_var.get() or None,
                'created_by': self.current_user['id']
            }
            
            # Sauvegarder
            cheque_id = self.db.add_cheque(cheque_data)
            
            messagebox.showinfo("Succès", f"Chèque enregistré avec succès!\nID: {cheque_id}")
            
            # Effacer le formulaire
            self.clear_form()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {e}")
    
    def clear_form(self):
        """Efface tous les champs du formulaire"""
        # Variables principales
        self.amount_var.set("")
        self.currency_var.set("MAD")
        self.cheque_number_var.set("")
        self.depositor_name_var.set("")
        self.invoice_number_var.set("")
        self.notes_var.set("")
        self.client_var.set("")
        self.branch_var.set("")
        self.status_var.set("en_attente")
        self.scan_path_var.set("")
        
        # Variables client
        self.client_type_var.set("personne")
        self.client_name_var.set("")
        self.client_id_number_var.set("")
        self.client_vat_number_var.set("")
        self.client_address_var.set("")
        self.client_phone_var.set("")
        self.client_email_var.set("")
        self.client_search_var.set("")
        
        # Dates à aujourd'hui
        today = date.today()
        self.issue_date.set_date(today)
        self.due_date.set_date(today)
        self.invoice_date.set_date(today)
        
        # Nettoyer les widgets
        self.notes_text.delete(1.0, tk.END)
        self.client_listbox.delete(0, tk.END)
        self.duplicate_label.config(text="")
        
        # Réinitialiser l'affichage client
        self.toggle_client_fields()
