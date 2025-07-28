#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Composant tableau de bord
"""

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta

class DashboardFrame(ttk.Frame):
    """Frame du tableau de bord avec statistiques et graphiques"""
    
    def __init__(self, parent, db_manager, current_user):
        super().__init__(parent)
        self.db = db_manager
        self.current_user = current_user
        
        self.setup_ui()
        self.refresh_data()
    
    def setup_ui(self):
        """Configure l'interface du tableau de bord"""
        # Titre
        title_frame = ttk.Frame(self)
        title_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(title_frame, text="📊 Tableau de Bord", 
                 font=('Arial', 16, 'bold')).pack(side=tk.LEFT)
        
        ttk.Button(title_frame, text="🔄 Actualiser", 
                  command=self.refresh_data).pack(side=tk.RIGHT)
        
        # Zone des cartes statistiques
        self.create_stats_cards()
        
        # Zone des graphiques
        self.create_charts_area()
        
        # Zone des alertes
        self.create_alerts_area()
    
    def create_stats_cards(self):
        """Crée les cartes de statistiques"""
        cards_frame = ttk.Frame(self)
        cards_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Configuration des cartes
        self.stats_cards = {}
        card_configs = [
            ("total_cheques", "📊 Total Chèques", "primary"),
            ("total_amount", "💰 Montant Total", "success"),
            ("pending_count", "⏳ En Attente", "warning"),
            ("overdue_count", "⚠️ En Retard", "danger")
        ]
        
        for i, (key, title, style) in enumerate(card_configs):
            card = self.create_stat_card(cards_frame, title, "0", style)
            card.grid(row=0, column=i, padx=10, pady=5, sticky="ew")
            self.stats_cards[key] = card
            cards_frame.columnconfigure(i, weight=1)
    
    def create_stat_card(self, parent, title, value, style):
        """Crée une carte de statistique"""
        card_frame = ttk.LabelFrame(parent, text=title, padding=15)
        
        # Valeur principale
        value_label = ttk.Label(card_frame, text=value, 
                               font=('Arial', 20, 'bold'))
        value_label.pack()
        
        # Stockage de la référence pour mise à jour
        card_frame.value_label = value_label
        
        return card_frame
    
    def create_charts_area(self):
        """Crée la zone des graphiques"""
        charts_frame = ttk.Frame(self)
        charts_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Graphique des statuts (gauche)
        status_frame = ttk.LabelFrame(charts_frame, text="📈 Répartition par Statut", padding=10)
        status_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.status_chart_frame = ttk.Frame(status_frame)
        self.status_chart_frame.pack(fill=tk.BOTH, expand=True)
        
        # Graphique temporel (droite)
        temporal_frame = ttk.LabelFrame(charts_frame, text="📅 Évolution Mensuelle", padding=10)
        temporal_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        self.temporal_chart_frame = ttk.Frame(temporal_frame)
        self.temporal_chart_frame.pack(fill=tk.BOTH, expand=True)
    
    def create_alerts_area(self):
        """Crée la zone des alertes"""
        alerts_frame = ttk.LabelFrame(self, text="🚨 Alertes et Notifications", padding=10)
        alerts_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Liste des alertes
        self.alerts_tree = ttk.Treeview(alerts_frame, columns=('Type', 'Message', 'Date'), 
                                       show='headings', height=6)
        
        self.alerts_tree.heading('Type', text='Type')
        self.alerts_tree.heading('Message', text='Message')
        self.alerts_tree.heading('Date', text='Date')
        
        self.alerts_tree.column('Type', width=100)
        self.alerts_tree.column('Message', width=400)
        self.alerts_tree.column('Date', width=150)
        
        self.alerts_tree.pack(fill=tk.X)
        
        # Scrollbar
        alerts_scroll = ttk.Scrollbar(alerts_frame, orient=tk.VERTICAL, 
                                     command=self.alerts_tree.yview)
        alerts_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.alerts_tree.configure(yscrollcommand=alerts_scroll.set)
    
    def refresh_data(self):
        """Actualise toutes les données du tableau de bord"""
        try:
            # Récupération des statistiques
            stats = self.db.get_dashboard_stats()
            
            # Mise à jour des cartes
            self.update_stats_cards(stats)
            
            # Mise à jour des graphiques
            self.update_status_chart(stats)
            self.update_temporal_chart()
            
            # Mise à jour des alertes
            self.update_alerts()
            
        except Exception as e:
            print(f"Erreur lors de l'actualisation du tableau de bord: {e}")
    
    def update_stats_cards(self, stats):
        """Met à jour les cartes de statistiques"""
        # Total des chèques
        self.stats_cards['total_cheques'].value_label.config(
            text=str(stats['total_cheques'])
        )
        
        # Montant total
        self.stats_cards['total_amount'].value_label.config(
            text=f"{stats['total_amount']:,.0f} DH"
        )
        
        # En attente
        pending_count = stats['by_status'].get('en_attente', {}).get('count', 0)
        self.stats_cards['pending_count'].value_label.config(
            text=str(pending_count)
        )
        
        # En retard
        self.stats_cards['overdue_count'].value_label.config(
            text=str(stats['overdue_count'])
        )
    
    def update_status_chart(self, stats):
        """Met à jour le graphique des statuts"""
        # Nettoyer le frame précédent
        for widget in self.status_chart_frame.winfo_children():
            widget.destroy()
        
        # Données pour le graphique
        status_data = stats['by_status']
        if not status_data:
            ttk.Label(self.status_chart_frame, text="Aucune donnée disponible").pack()
            return
        
        # Création du graphique en secteurs
        fig, ax = plt.subplots(figsize=(6, 4))
        
        labels = []
        sizes = []
        colors = []
        
        status_colors = {
            'en_attente': '#ffc107',
            'encaisse': '#28a745',
            'rejete': '#dc3545',
            'impaye': '#fd7e14',
            'depose': '#17a2b8',
            'annule': '#6c757d'
        }
        
        status_labels = {
            'en_attente': 'En Attente',
            'encaisse': 'Encaissé',
            'rejete': 'Rejeté',
            'impaye': 'Impayé',
            'depose': 'Déposé',
            'annule': 'Annulé'
        }
        
        for status, data in status_data.items():
            if data['count'] > 0:
                labels.append(status_labels.get(status, status))
                sizes.append(data['count'])
                colors.append(status_colors.get(status, '#6c757d'))
        
        if sizes:
            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax.set_title('Répartition par Statut')
        
        # Intégration dans Tkinter
        canvas = FigureCanvasTkAgg(fig, self.status_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        plt.close(fig)
    
    def update_temporal_chart(self):
        """Met à jour le graphique temporel"""
        # Nettoyer le frame précédent
        for widget in self.temporal_chart_frame.winfo_children():
            widget.destroy()
        
        try:
            # Récupération des données des 6 derniers mois
            import sqlite3
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        strftime('%Y-%m', due_date) as month,
                        COUNT(*) as count,
                        SUM(amount) as total
                    FROM cheques 
                    WHERE due_date >= date('now', '-6 months')
                    GROUP BY strftime('%Y-%m', due_date)
                    ORDER BY month
                """)
                
                data = cursor.fetchall()
            
            if not data:
                ttk.Label(self.temporal_chart_frame, text="Aucune donnée disponible").pack()
                return
            
            # Création du graphique linéaire
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 4), sharex=True)
            
            months = [row[0] for row in data]
            counts = [row[1] for row in data]
            amounts = [row[2] for row in data]
            
            # Graphique du nombre de chèques
            ax1.plot(months, counts, marker='o', color='#007bff')
            ax1.set_ylabel('Nombre de chèques')
            ax1.set_title('Évolution sur 6 mois')
            ax1.grid(True, alpha=0.3)
            
            # Graphique des montants
            ax2.plot(months, amounts, marker='s', color='#28a745')
            ax2.set_ylabel('Montant (DH)')
            ax2.set_xlabel('Mois')
            ax2.grid(True, alpha=0.3)
            
            # Rotation des labels
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Intégration dans Tkinter
            canvas = FigureCanvasTkAgg(fig, self.temporal_chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            plt.close(fig)
            
        except Exception as e:
            ttk.Label(self.temporal_chart_frame, 
                     text=f"Erreur lors du chargement: {e}").pack()
    
    def update_alerts(self):
        """Met à jour la liste des alertes"""
        # Nettoyer la liste
        for item in self.alerts_tree.get_children():
            self.alerts_tree.delete(item)
        
        try:
            # Chèques arrivant à échéance
            due_cheques = self.db.get_cheques_due_soon(7)  # 7 jours
            
            for cheque in due_cheques:
                self.alerts_tree.insert('', tk.END, values=(
                    '⏰ Échéance',
                    f"Chèque n°{cheque['cheque_number']} - {cheque['client_name'] or 'Client inconnu'}",
                    cheque['due_date']
                ))
            
            # Notifications non lues
            notifications = self.db.get_notifications(self.current_user['id'], unread_only=True)
            
            for notif in notifications[:5]:  # Limiter à 5
                self.alerts_tree.insert('', tk.END, values=(
                    '🔔 Notification',
                    notif['message'],
                    notif['created_at'][:10]  # Date seulement
                ))
            
            if not due_cheques and not notifications:
                self.alerts_tree.insert('', tk.END, values=(
                    '✅ Info',
                    'Aucune alerte en cours',
                    datetime.now().strftime('%Y-%m-%d')
                ))
                
        except Exception as e:
            self.alerts_tree.insert('', tk.END, values=(
                '❌ Erreur',
                f'Erreur lors du chargement des alertes: {e}',
                datetime.now().strftime('%Y-%m-%d')
            ))
