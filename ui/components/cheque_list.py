#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Composant liste des chèques avec filtres avancés
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta
import sqlite3

class ChequeListFrame(ttk.Frame):
    """Frame pour la liste et gestion des chèques"""
    
    def __init__(self, parent, db_manager, current_user):
        super().__init__(parent)
        self.db = db_manager
        self.current_user = current_user
        
        # Variables de filtrage
        self.init_filter_variables()
        
        # Interface utilisateur
        self.setup_ui()
        
        # Charger les données
        self.load_data()
    
    def init_filter_variables(self):
        """Initialise les variables de filtrage"""
        self.search_var = tk.StringVar()
        self.status_filter_var = tk.StringVar(value="Tous")
        self.bank_filter_var = tk.StringVar(value="Toutes")
        self.date_from_var = tk.StringVar()
        self.date_to_var = tk.StringVar()
        self.amount_min_var = tk.StringVar()
        self.amount_max_var = tk.StringVar()
        
        # Données de référence
        self.cheques_data = []
        self.filtered_data = []
    
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        # Titre et contrôles principaux
        self.create_header()
        
        # Zone de filtres
        self.create_filters_section()
        
        # Liste des chèques
        self.create_cheques_table()
        
        # Barre d'actions
        self.create_actions_bar()
    
    def create_header(self):
        """Crée l'en-tête avec titre et contrôles"""
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Titre
        ttk.Label(header_frame, text="📋 Liste des Chèques", 
                 font=('Arial', 16, 'bold')).pack(side=tk.LEFT)
        
        # Contrôles à droite
        controls_frame = ttk.Frame(header_frame)
        controls_frame.pack(side=tk.RIGHT)
        
        ttk.Button(controls_frame, text="🔄 Actualiser", 
                  command=self.refresh_data).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls_frame, text="📤 Exporter", 
                  command=self.export_selection).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls_frame, text="➕ Nouveau", 
                  command=self.new_cheque).pack(side=tk.LEFT, padx=2)
    
    def create_filters_section(self):
        """Crée la section des filtres"""
        filters_frame = ttk.LabelFrame(self, text="🔍 Filtres de Recherche", padding=15)
        filters_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Ligne 1: Recherche textuelle et statut
        row1 = ttk.Frame(filters_frame)
        row1.pack(fill=tk.X, pady=5)
        
        ttk.Label(row1, text="Recherche:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        search_entry = ttk.Entry(row1, textvariable=self.search_var, width=25)
        search_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 30))
        search_entry.bind('<KeyRelease>', self.on_search_change)
        
        ttk.Label(row1, text="Statut:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        status_combo = ttk.Combobox(row1, textvariable=self.status_filter_var, width=15, state="readonly")
        status_combo['values'] = ['Tous', 'en_attente', 'encaisse', 'rejete', 'impaye', 'depose', 'annule']
        status_combo.grid(row=0, column=3, sticky=tk.W, padx=(0, 30))
        status_combo.bind('<<ComboboxSelected>>', self.apply_filters)
        
        ttk.Label(row1, text="Banque:").grid(row=0, column=4, sticky=tk.W, padx=(0, 10))
        self.bank_combo = ttk.Combobox(row1, textvariable=self.bank_filter_var, width=20, state="readonly")
        self.bank_combo.grid(row=0, column=5, sticky=tk.W)
        self.bank_combo.bind('<<ComboboxSelected>>', self.apply_filters)
        
        # Ligne 2: Filtres de dates et montants
        row2 = ttk.Frame(filters_frame)
        row2.pack(fill=tk.X, pady=5)
        
        ttk.Label(row2, text="Du:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        from tkcalendar import DateEntry
        self.date_from = DateEntry(row2, width=12, background='darkblue',
                                  foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
        self.date_from.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        self.date_from.bind('<<DateEntrySelected>>', self.apply_filters)
        
        ttk.Label(row2, text="Au:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.date_to = DateEntry(row2, width=12, background='darkblue',
                                foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
        self.date_to.grid(row=0, column=3, sticky=tk.W, padx=(0, 30))
        self.date_to.bind('<<DateEntrySelected>>', self.apply_filters)
        
        ttk.Label(row2, text="Montant min:").grid(row=0, column=4, sticky=tk.W, padx=(0, 10))
        min_entry = ttk.Entry(row2, textvariable=self.amount_min_var, width=12)
        min_entry.grid(row=0, column=5, sticky=tk.W, padx=(0, 20))
        min_entry.bind('<KeyRelease>', self.on_amount_change)
        
        ttk.Label(row2, text="Montant max:").grid(row=0, column=6, sticky=tk.W, padx=(0, 10))
        max_entry = ttk.Entry(row2, textvariable=self.amount_max_var, width=12)
        max_entry.grid(row=0, column=7, sticky=tk.W)
        max_entry.bind('<KeyRelease>', self.on_amount_change)
        
        # Boutons de contrôle des filtres
        controls_frame = ttk.Frame(filters_frame)
        controls_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(controls_frame, text="🔍 Appliquer", 
                  command=self.apply_filters).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(controls_frame, text="🗑️ Effacer", 
                  command=self.clear_filters).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(controls_frame, text="⚙️ Filtres Avancés", 
                  command=self.show_advanced_filters).pack(side=tk.LEFT)
        
        # Informations sur les résultats
        self.results_info_var = tk.StringVar(value="Chargement...")
        ttk.Label(controls_frame, textvariable=self.results_info_var, 
                 font=('Arial', 10, 'italic')).pack(side=tk.RIGHT)
    
    def create_cheques_table(self):
        """Crée le tableau des chèques"""
        table_frame = ttk.LabelFrame(self, text="📊 Résultats", padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Conteneur avec scrollbars
        container = ttk.Frame(table_frame)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Treeview
        columns = ('ID', 'N° Chèque', 'Client', 'Banque', 'Montant', 'Échéance', 'Statut', 'Déposant')
        self.tree = ttk.Treeview(container, columns=columns, show='headings', height=15)
        
        # Configuration des colonnes
        self.tree.heading('ID', text='ID')
        self.tree.heading('N° Chèque', text='N° Chèque')
        self.tree.heading('Client', text='Client')
        self.tree.heading('Banque', text='Banque')
        self.tree.heading('Montant', text='Montant')
        self.tree.heading('Échéance', text='Échéance')
        self.tree.heading('Statut', text='Statut')
        self.tree.heading('Déposant', text='Déposant')
        
        # Largeurs des colonnes
        self.tree.column('ID', width=50)
        self.tree.column('N° Chèque', width=120)
        self.tree.column('Client', width=200)
        self.tree.column('Banque', width=150)
        self.tree.column('Montant', width=100)
        self.tree.column('Échéance', width=100)
        self.tree.column('Statut', width=100)
        self.tree.column('Déposant', width=150)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(container, orient=tk.HORIZONTAL, command=self.tree.xview)
        
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Placement
        self.tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        # Événements
        self.tree.bind('<Double-1>', self.on_double_click)
        self.tree.bind('<Button-3>', self.show_context_menu)
        self.tree.bind('<<TreeviewSelect>>', self.on_selection_change)
    
    def create_actions_bar(self):
        """Crée la barre d'actions"""
        actions_frame = ttk.Frame(self)
        actions_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Actions sur la sélection
        ttk.Label(actions_frame, text="Actions sur la sélection:", 
                 font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        
        ttk.Button(actions_frame, text="✏️ Modifier", 
                  command=self.edit_selected).pack(side=tk.LEFT, padx=(10, 5))
        ttk.Button(actions_frame, text="🗑️ Supprimer", 
                  command=self.delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="📋 Dupliquer", 
                  command=self.duplicate_selected).pack(side=tk.LEFT, padx=5)
        
        # Changement de statut
        ttk.Label(actions_frame, text="Changer statut:", 
                 font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=(20, 5))
        
        status_buttons = [
            ("✅ Encaissé", "encaisse", "#28a745"),
            ("❌ Rejeté", "rejete", "#dc3545"),
            ("⚠️ Impayé", "impaye", "#fd7e14"),
            ("📤 Déposé", "depose", "#17a2b8")
        ]
        
        for text, status, color in status_buttons:
            btn = ttk.Button(actions_frame, text=text, 
                           command=lambda s=status: self.change_status(s))
            btn.pack(side=tk.LEFT, padx=2)
    
    def load_data(self):
        """Charge les données initiales"""
        try:
            # Charger tous les chèques
            self.cheques_data = self.db.get_cheques()
            
            # Charger les banques pour le filtre
            banks = self.db.get_banks()
            bank_names = ['Toutes'] + [bank['name'] for bank in banks]
            self.bank_combo['values'] = bank_names
            
            # Appliquer les filtres initiaux
            self.apply_filters()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement: {e}")
    
    def apply_filters(self, event=None):
        """Applique les filtres aux données"""
        try:
            # Construire les filtres
            filters = {}
            
            # Filtre par statut
            if self.status_filter_var.get() != "Tous":
                filters['status'] = self.status_filter_var.get()
            
            # Filtre par banque
            if self.bank_filter_var.get() != "Toutes":
                # Trouver l'ID de la banque
                banks = self.db.get_banks()
                for bank in banks:
                    if bank['name'] == self.bank_filter_var.get():
                        filters['bank_id'] = bank['id']
                        break
            
            # Filtres de dates
            try:
                if self.date_from.get():
                    filters['date_from'] = self.date_from.get_date().strftime('%Y-%m-%d')
                if self.date_to.get():
                    filters['date_to'] = self.date_to.get_date().strftime('%Y-%m-%d')
            except:
                pass
            
            # Filtres de montants
            try:
                if self.amount_min_var.get():
                    filters['amount_min'] = float(self.amount_min_var.get().replace(',', '.'))
                if self.amount_max_var.get():
                    filters['amount_max'] = float(self.amount_max_var.get().replace(',', '.'))
            except ValueError:
                pass
            
            # Récupérer les données filtrées
            self.filtered_data = self.db.get_cheques(filters)
            
            # Appliquer le filtre de recherche textuelle
            if self.search_var.get():
                search_term = self.search_var.get().lower()
                self.filtered_data = [
                    cheque for cheque in self.filtered_data
                    if (search_term in (cheque.get('cheque_number', '') or '').lower() or
                        search_term in (cheque.get('client_name', '') or '').lower() or
                        search_term in (cheque.get('depositor_name', '') or '').lower() or
                        search_term in (cheque.get('bank_name', '') or '').lower())
                ]
            
            # Mettre à jour l'affichage
            self.update_table()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du filtrage: {e}")
    
    def update_table(self):
        """Met à jour l'affichage du tableau"""
        # Vider le tableau
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Ajouter les données filtrées
        total_amount = 0
        for cheque in self.filtered_data:
            # Formatage des données
            amount_str = f"{cheque['amount']:,.2f} {cheque['currency']}"
            total_amount += cheque['amount']
            
            # Badge de statut
            status_badges = {
                'en_attente': '⏳ En Attente',
                'encaisse': '✅ Encaissé',
                'rejete': '❌ Rejeté',
                'impaye': '⚠️ Impayé',
                'depose': '📤 Déposé',
                'annule': '🚫 Annulé'
            }
            status_display = status_badges.get(cheque['status'], cheque['status'])
            
            # Insérer la ligne
            item = self.tree.insert('', tk.END, values=(
                cheque['id'],
                cheque['cheque_number'],
                cheque.get('client_name', 'N/A'),
                cheque.get('bank_name', 'N/A'),
                amount_str,
                cheque['due_date'],
                status_display,
                cheque.get('depositor_name', '')
            ))
            
            # Coloration selon le statut
            if cheque['status'] == 'rejete':
                self.tree.set(item, 'Statut', '❌ Rejeté')
            elif cheque['status'] == 'encaisse':
                self.tree.set(item, 'Statut', '✅ Encaissé')
            elif cheque['status'] == 'impaye':
                self.tree.set(item, 'Statut', '⚠️ Impayé')
        
        # Mettre à jour les informations
        count = len(self.filtered_data)
        self.results_info_var.set(
            f"📊 {count} chèque(s) | Total: {total_amount:,.2f} MAD"
        )
    
    def on_search_change(self, event=None):
        """Gère les changements de recherche avec délai"""
        if hasattr(self, '_search_timer'):
            self.after_cancel(self._search_timer)
        self._search_timer = self.after(500, self.apply_filters)
    
    def on_amount_change(self, event=None):
        """Gère les changements de montant avec délai"""
        if hasattr(self, '_amount_timer'):
            self.after_cancel(self._amount_timer)
        self._amount_timer = self.after(1000, self.apply_filters)
    
    def clear_filters(self):
        """Efface tous les filtres"""
        self.search_var.set("")
        self.status_filter_var.set("Tous")
        self.bank_filter_var.set("Toutes")
        self.amount_min_var.set("")
        self.amount_max_var.set("")
        
        # Réinitialiser les dates
        self.date_from.set_date(None)
        self.date_to.set_date(None)
        
        # Réappliquer les filtres
        self.apply_filters()
    
    def focus_search(self):
        """Met le focus sur la recherche"""
        # Cette méthode est appelée depuis main_window
        pass
    
    def show_advanced_filters(self):
        """Affiche les filtres avancés"""
        messagebox.showinfo("Filtres Avancés", "Fonctionnalité à implémenter")
    
    def refresh_data(self):
        """Actualise les données"""
        self.load_data()
    
    def new_cheque(self):
        """Ouvre le formulaire de nouveau chèque"""
        # Notifier la fenêtre parent
        self.event_generate('<<NewCheque>>')
    
    def on_double_click(self, event):
        """Gère le double-clic sur une ligne"""
        self.edit_selected()
    
    def on_selection_change(self, event):
        """Gère le changement de sélection"""
        selection = self.tree.selection()
        # Activer/désactiver les boutons selon la sélection
    
    def show_context_menu(self, event):
        """Affiche le menu contextuel"""
        item = self.tree.identify_row(event.y)
        if not item:
            return
        
        self.tree.selection_set(item)
        
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="✏️ Modifier", command=self.edit_selected)
        menu.add_command(label="📋 Dupliquer", command=self.duplicate_selected)
        menu.add_separator()
        menu.add_command(label="✅ Marquer encaissé", command=lambda: self.change_status('encaisse'))
        menu.add_command(label="❌ Marquer rejeté", command=lambda: self.change_status('rejete'))
        menu.add_command(label="⚠️ Marquer impayé", command=lambda: self.change_status('impaye'))
        menu.add_separator()
        menu.add_command(label="🗑️ Supprimer", command=self.delete_selected)
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def get_selected_cheque(self):
        """Récupère le chèque sélectionné"""
        selection = self.tree.selection()
        if not selection:
            return None
        
        item = self.tree.item(selection[0])
        cheque_id = item['values'][0]
        
        # Trouver le chèque dans les données
        for cheque in self.filtered_data:
            if cheque['id'] == cheque_id:
                return cheque
        
        return None
    
    def edit_selected(self):
        """Modifie le chèque sélectionné"""
        cheque = self.get_selected_cheque()
        if not cheque:
            messagebox.showwarning("Attention", "Veuillez sélectionner un chèque")
            return
        
        from ..dialogs.cheque_edit_dialog import ChequeEditDialog
        dialog = ChequeEditDialog(self, self.db, cheque, self.current_user)
        self.wait_window(dialog.dialog)
        
        if dialog.result:
            self.refresh_data()
    
    def duplicate_selected(self):
        """Duplique le chèque sélectionné"""
        cheque = self.get_selected_cheque()
        if not cheque:
            messagebox.showwarning("Attention", "Veuillez sélectionner un chèque")
            return
        
        if messagebox.askyesno("Confirmer", "Dupliquer ce chèque?"):
            try:
                # Créer une copie avec un nouveau numéro
                new_cheque = cheque.copy()
                new_cheque.pop('id', None)
                new_cheque['cheque_number'] = f"{cheque['cheque_number']}_COPY"
                new_cheque['status'] = 'en_attente'
                new_cheque['created_by'] = self.current_user['id']
                
                self.db.add_cheque(new_cheque)
                messagebox.showinfo("Succès", "Chèque dupliqué avec succès")
                self.refresh_data()
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la duplication: {e}")
    
    def delete_selected(self):
        """Supprime le chèque sélectionné"""
        cheque = self.get_selected_cheque()
        if not cheque:
            messagebox.showwarning("Attention", "Veuillez sélectionner un chèque")
            return
        
        if messagebox.askyesno("Confirmer", 
                              f"Supprimer définitivement le chèque n°{cheque['cheque_number']}?"):
            try:
                # Supprimer de la base de données
                with sqlite3.connect(self.db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM cheques WHERE id = ?", (cheque['id'],))
                
                messagebox.showinfo("Succès", "Chèque supprimé avec succès")
                self.refresh_data()
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la suppression: {e}")
    
    def change_status(self, new_status):
        """Change le statut du chèque sélectionné"""
        cheque = self.get_selected_cheque()
        if not cheque:
            messagebox.showwarning("Attention", "Veuillez sélectionner un chèque")
            return
        
        status_names = {
            'en_attente': 'En Attente',
            'encaisse': 'Encaissé',
            'rejete': 'Rejeté',
            'impaye': 'Impayé',
            'depose': 'Déposé',
            'annule': 'Annulé'
        }
        
        if messagebox.askyesno("Confirmer", 
                              f"Changer le statut du chèque n°{cheque['cheque_number']} "
                              f"vers '{status_names.get(new_status, new_status)}'?"):
            try:
                self.db.update_cheque_status(cheque['id'], new_status, self.current_user['id'])
                messagebox.showinfo("Succès", "Statut mis à jour avec succès")
                self.refresh_data()
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la mise à jour: {e}")
    
    def export_selection(self):
        """Exporte la sélection ou tous les résultats"""
        if not self.filtered_data:
            messagebox.showwarning("Attention", "Aucune donnée à exporter")
            return
        
        from ..dialogs.export_dialog import ExportDialog
        dialog = ExportDialog(self, self.filtered_data)
        self.wait_window(dialog.dialog)
