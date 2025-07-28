#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dialogue des notifications
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

class NotificationsDialog:
    """Dialogue d'affichage des notifications"""
    
    def __init__(self, parent, db_manager, current_user):
        self.parent = parent
        self.db = db_manager
        self.current_user = current_user
        
        # Créer la fenêtre de dialogue
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("🔔 Notifications")
        self.dialog.geometry("700x500")
        
        # Centrer la fenêtre
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Interface utilisateur
        self.setup_ui()
        
        # Charger les notifications
        self.load_notifications()
    
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        # En-tête
        header_frame = ttk.Frame(self.dialog, padding=10)
        header_frame.pack(fill=tk.X)
        
        ttk.Label(header_frame, text="🔔 Centre de Notifications", 
                 font=('Arial', 14, 'bold')).pack(side=tk.LEFT)
        
        # Boutons de contrôle
        controls_frame = ttk.Frame(header_frame)
        controls_frame.pack(side=tk.RIGHT)
        
        ttk.Button(controls_frame, text="🔄 Actualiser", 
                  command=self.load_notifications).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(controls_frame, text="✅ Marquer tout lu", 
                  command=self.mark_all_read).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(controls_frame, text="🗑️ Effacer tout", 
                  command=self.clear_all).pack(side=tk.LEFT)
        
        # Filtres
        filters_frame = ttk.Frame(self.dialog, padding=10)
        filters_frame.pack(fill=tk.X)
        
        ttk.Label(filters_frame, text="Afficher:").pack(side=tk.LEFT)
        
        self.filter_var = tk.StringVar(value="all")
        ttk.Radiobutton(filters_frame, text="Toutes", variable=self.filter_var, 
                       value="all", command=self.apply_filter).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Radiobutton(filters_frame, text="Non lues", variable=self.filter_var, 
                       value="unread", command=self.apply_filter).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Radiobutton(filters_frame, text="Échéances", variable=self.filter_var, 
                       value="due_soon", command=self.apply_filter).pack(side=tk.LEFT, padx=(10, 0))
        
        # Liste des notifications
        list_frame = ttk.Frame(self.dialog, padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview
        columns = ('Type', 'Titre', 'Message', 'Date', 'Lu')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        # Configuration des colonnes
        self.tree.heading('Type', text='Type')
        self.tree.heading('Titre', text='Titre')
        self.tree.heading('Message', text='Message')
        self.tree.heading('Date', text='Date')
        self.tree.heading('Lu', text='Lu')
        
        self.tree.column('Type', width=80)
        self.tree.column('Titre', width=120)
        self.tree.column('Message', width=300)
        self.tree.column('Date', width=120)
        self.tree.column('Lu', width=50)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Événements
        self.tree.bind('<Double-1>', self.on_double_click)
        self.tree.bind('<Button-3>', self.show_context_menu)
        
        # Boutons de fermeture
        buttons_frame = ttk.Frame(self.dialog, padding=10)
        buttons_frame.pack(fill=tk.X)
        
        ttk.Button(buttons_frame, text="Fermer", 
                  command=self.dialog.destroy).pack(side=tk.RIGHT)
    
    def load_notifications(self):
        """Charge les notifications"""
        try:
            # Récupérer les notifications
            self.notifications = self.db.get_notifications(self.current_user['id'])
            
            # Appliquer le filtre actuel
            self.apply_filter()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement: {e}")
    
    def apply_filter(self):
        """Applique le filtre sélectionné"""
        # Vider le tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        filter_type = self.filter_var.get()
        
        # Filtrer les notifications
        filtered_notifications = []
        for notif in self.notifications:
            if filter_type == "all":
                filtered_notifications.append(notif)
            elif filter_type == "unread" and not notif['read']:
                filtered_notifications.append(notif)
            elif filter_type == "due_soon" and notif['type'] == 'due_soon':
                filtered_notifications.append(notif)
        
        # Ajouter au tree
        for notif in filtered_notifications:
            # Icônes par type
            type_icons = {
                'due_soon': '⏰',
                'status_change': '🔄',
                'system': '⚙️',
                'warning': '⚠️',
                'info': 'ℹ️'
            }
            
            type_display = f"{type_icons.get(notif['type'], '📢')} {notif['type']}"
            
            # Formatage de la date
            try:
                date_obj = datetime.strptime(notif['created_at'], '%Y-%m-%d %H:%M:%S')
                date_display = date_obj.strftime('%d/%m/%Y %H:%M')
            except:
                date_display = notif['created_at']
            
            # Statut de lecture
            read_display = "✅" if notif['read'] else "❌"
            
            # Insérer dans le tree
            item = self.tree.insert('', tk.END, values=(
                type_display,
                notif['title'],
                notif['message'][:50] + "..." if len(notif['message']) > 50 else notif['message'],
                date_display,
                read_display
            ))
            
            # Coloration pour les non lues
            if not notif['read']:
                self.tree.set(item, 'Titre', f"🔴 {notif['title']}")
    
    def on_double_click(self, event):
        """Gère le double-clic sur une notification"""
        selection = self.tree.selection()
        if not selection:
            return
        
        # Trouver la notification correspondante
        item_index = self.tree.index(selection[0])
        if item_index < len(self.notifications):
            notif = self.notifications[item_index]
            
            # Marquer comme lue
            self.mark_notification_read(notif['id'])
            
            # Afficher les détails
            self.show_notification_details(notif)
    
    def show_notification_details(self, notification):
        """Affiche les détails d'une notification"""
        details_window = tk.Toplevel(self.dialog)
        details_window.title("Détails de la Notification")
        details_window.geometry("500x400")
        details_window.transient(self.dialog)
        
        # Contenu
        main_frame = ttk.Frame(details_window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titre
        ttk.Label(main_frame, text=notification['title'], 
                 font=('Arial', 14, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        # Type et date
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(info_frame, text=f"Type: {notification['type']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Date: {notification['created_at']}").pack(anchor=tk.W)
        
        # Message
        ttk.Label(main_frame, text="Message:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(10, 5))
        
        message_text = tk.Text(main_frame, height=10, wrap=tk.WORD)
        message_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        message_text.insert(1.0, notification['message'])
        message_text.config(state=tk.DISABLED)
        
        # Bouton fermer
        ttk.Button(main_frame, text="Fermer", 
                  command=details_window.destroy).pack(side=tk.RIGHT)
    
    def show_context_menu(self, event):
        """Affiche le menu contextuel"""
        item = self.tree.identify_row(event.y)
        if not item:
            return
        
        self.tree.selection_set(item)
        
        menu = tk.Menu(self.dialog, tearoff=0)
        menu.add_command(label="👁️ Voir détails", command=lambda: self.on_double_click(None))
        menu.add_command(label="✅ Marquer comme lu", command=self.mark_selected_read)
        menu.add_command(label="🗑️ Supprimer", command=self.delete_selected)
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def mark_notification_read(self, notification_id):
        """Marque une notification comme lue"""
        try:
            import sqlite3
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE notifications SET read = TRUE WHERE id = ?",
                    (notification_id,)
                )
            
            # Recharger les notifications
            self.load_notifications()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la mise à jour: {e}")
    
    def mark_selected_read(self):
        """Marque la notification sélectionnée comme lue"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item_index = self.tree.index(selection[0])
        if item_index < len(self.notifications):
            notif = self.notifications[item_index]
            self.mark_notification_read(notif['id'])
    
    def mark_all_read(self):
        """Marque toutes les notifications comme lues"""
        if messagebox.askyesno("Confirmer", "Marquer toutes les notifications comme lues?"):
            try:
                import sqlite3
                with sqlite3.connect(self.db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE notifications SET read = TRUE WHERE user_id = ? OR user_id IS NULL",
                        (self.current_user['id'],)
                    )
                
                messagebox.showinfo("Succès", "Toutes les notifications ont été marquées comme lues")
                self.load_notifications()
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la mise à jour: {e}")
    
    def delete_selected(self):
        """Supprime la notification sélectionnée"""
        selection = self.tree.selection()
        if not selection:
            return
        
        if messagebox.askyesno("Confirmer", "Supprimer cette notification?"):
            try:
                item_index = self.tree.index(selection[0])
                if item_index < len(self.notifications):
                    notif = self.notifications[item_index]
                    
                    import sqlite3
                    with sqlite3.connect(self.db.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM notifications WHERE id = ?", (notif['id'],))
                    
                    self.load_notifications()
                    
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la suppression: {e}")
    
    def clear_all(self):
        """Efface toutes les notifications"""
        if messagebox.askyesno("Confirmer", "Supprimer toutes les notifications?"):
            try:
                import sqlite3
                with sqlite3.connect(self.db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "DELETE FROM notifications WHERE user_id = ? OR user_id IS NULL",
                        (self.current_user['id'],)
                    )
                
                messagebox.showinfo("Succès", "Toutes les notifications ont été supprimées")
                self.load_notifications()
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la suppression: {e}")
