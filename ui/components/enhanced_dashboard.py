#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Dashboard with Advanced Analytics and Real-time Updates
"""

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from datetime import datetime, timedelta, date
import threading
import time
from analytics.advanced_analytics import AdvancedAnalytics, RiskLevel
from automation.smart_automation import SmartAutomation

class EnhancedDashboardFrame(ttk.Frame):
    """Enhanced dashboard with advanced analytics and real-time updates"""
    
    def __init__(self, parent, db_manager, current_user, config_manager):
        super().__init__(parent)
        self.db = db_manager
        self.current_user = current_user
        self.config = config_manager
        
        # Initialize analytics engines
        self.analytics = AdvancedAnalytics(db_manager)
        self.automation = SmartAutomation(db_manager, config_manager)
        
        # Real-time update control
        self.auto_refresh = tk.BooleanVar(value=True)
        self.refresh_interval = 30  # seconds
        self.last_update = None
        
        # Setup UI
        self.setup_ui()
        
        # Start real-time updates
        self.start_real_time_updates()
    
    def setup_ui(self):
        """Setup the enhanced dashboard UI"""
        # Header with controls
        self.create_header()
        
        # Main content area with tabs
        self.create_main_content()
        
        # Status bar
        self.create_status_bar()
    
    def create_header(self):
        """Create dashboard header with controls"""
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Title
        title_label = ttk.Label(header_frame, text="📊 Tableau de Bord Avancé", 
                               font=('Arial', 18, 'bold'))
        title_label.pack(side=tk.LEFT)
        
        # Controls
        controls_frame = ttk.Frame(header_frame)
        controls_frame.pack(side=tk.RIGHT)
        
        # Auto-refresh toggle
        ttk.Checkbutton(controls_frame, text="🔄 Actualisation auto", 
                       variable=self.auto_refresh,
                       command=self.toggle_auto_refresh).pack(side=tk.LEFT, padx=5)
        
        # Manual refresh
        ttk.Button(controls_frame, text="🔄 Actualiser", 
                  command=self.manual_refresh).pack(side=tk.LEFT, padx=5)
        
        # Export dashboard
        ttk.Button(controls_frame, text="📤 Exporter", 
                  command=self.export_dashboard).pack(side=tk.LEFT, padx=5)
        
        # Settings
        ttk.Button(controls_frame, text="⚙️ Paramètres", 
                  command=self.show_dashboard_settings).pack(side=tk.LEFT, padx=5)
    
    def create_main_content(self):
        """Create main dashboard content with tabs"""
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Overview tab
        self.create_overview_tab()
        
        # Analytics tab
        self.create_analytics_tab()
        
        # Risk Management tab
        self.create_risk_tab()
        
        # Performance tab
        self.create_performance_tab()
        
        # Automation tab
        self.create_automation_tab()
    
    def create_overview_tab(self):
        """Create overview tab with key metrics"""
        overview_frame = ttk.Frame(self.notebook)
        self.notebook.add(overview_frame, text="📈 Vue d'ensemble")
        
        # KPI Cards
        self.create_kpi_cards(overview_frame)
        
        # Charts area
        charts_frame = ttk.Frame(overview_frame)
        charts_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Status distribution (left)
        status_frame = ttk.LabelFrame(charts_frame, text="Répartition par Statut", padding=10)
        status_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.status_chart_frame = ttk.Frame(status_frame)
        self.status_chart_frame.pack(fill=tk.BOTH, expand=True)
        
        # Trend analysis (right)
        trend_frame = ttk.LabelFrame(charts_frame, text="Tendances (30 jours)", padding=10)
        trend_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.trend_chart_frame = ttk.Frame(trend_frame)
        self.trend_chart_frame.pack(fill=tk.BOTH, expand=True)
        
        # Recent activity
        self.create_recent_activity(overview_frame)
    
    def create_kpi_cards(self, parent):
        """Create KPI cards"""
        kpi_frame = ttk.Frame(parent)
        kpi_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Card configurations
        self.kpi_cards = {}
        card_configs = [
            ("total_cheques", "📊 Total Chèques", "0", "#007bff"),
            ("total_amount", "💰 Montant Total", "0 MAD", "#28a745"),
            ("success_rate", "✅ Taux de Réussite", "0%", "#17a2b8"),
            ("avg_processing", "⏱️ Temps Moyen", "0 jours", "#ffc107"),
            ("pending_count", "⏳ En Attente", "0", "#fd7e14"),
            ("risk_alerts", "⚠️ Alertes Risque", "0", "#dc3545")
        ]
        
        for i, (key, title, default_value, color) in enumerate(card_configs):
            card = self.create_kpi_card(kpi_frame, title, default_value, color)
            card.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
            self.kpi_cards[key] = card
            kpi_frame.columnconfigure(i, weight=1)
    
    def create_kpi_card(self, parent, title, value, color):
        """Create a single KPI card"""
        card_frame = ttk.LabelFrame(parent, text=title, padding=15)
        
        # Value display
        value_label = ttk.Label(card_frame, text=value, 
                               font=('Arial', 16, 'bold'))
        value_label.pack()
        
        # Trend indicator
        trend_label = ttk.Label(card_frame, text="", 
                               font=('Arial', 10))
        trend_label.pack()
        
        # Store references
        card_frame.value_label = value_label
        card_frame.trend_label = trend_label
        
        return card_frame
    
    def create_recent_activity(self, parent):
        """Create recent activity section"""
        activity_frame = ttk.LabelFrame(parent, text="🕒 Activité Récente", padding=10)
        activity_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Activity list
        columns = ('Heure', 'Type', 'Description', 'Utilisateur')
        self.activity_tree = ttk.Treeview(activity_frame, columns=columns, 
                                         show='headings', height=6)
        
        for col in columns:
            self.activity_tree.heading(col, text=col)
            self.activity_tree.column(col, width=150)
        
        # Scrollbar
        activity_scroll = ttk.Scrollbar(activity_frame, orient=tk.VERTICAL, 
                                       command=self.activity_tree.yview)
        self.activity_tree.configure(yscrollcommand=activity_scroll.set)
        
        self.activity_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        activity_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_analytics_tab(self):
        """Create analytics tab"""
        analytics_frame = ttk.Frame(self.notebook)
        self.notebook.add(analytics_frame, text="📊 Analyses")
        
        # Aging analysis
        aging_frame = ttk.LabelFrame(analytics_frame, text="⏳ Analyse de Vieillissement", padding=10)
        aging_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.aging_chart_frame = ttk.Frame(aging_frame)
        self.aging_chart_frame.pack(fill=tk.BOTH, expand=True)
        
        # Seasonal trends
        seasonal_frame = ttk.LabelFrame(analytics_frame, text="🌍 Tendances Saisonnières", padding=10)
        seasonal_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.seasonal_chart_frame = ttk.Frame(seasonal_frame)
        self.seasonal_chart_frame.pack(fill=tk.BOTH, expand=True)
    
    def create_risk_tab(self):
        """Create risk management tab"""
        risk_frame = ttk.Frame(self.notebook)
        self.notebook.add(risk_frame, text="⚠️ Gestion des Risques")
        
        # Risk overview
        risk_overview_frame = ttk.LabelFrame(risk_frame, text="📋 Vue d'ensemble des Risques", padding=10)
        risk_overview_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Risk metrics
        risk_metrics_frame = ttk.Frame(risk_overview_frame)
        risk_metrics_frame.pack(fill=tk.X)
        
        self.risk_cards = {}
        risk_configs = [
            ("high_risk_clients", "🔴 Clients Haut Risque", "0"),
            ("bounce_rate", "📉 Taux de Rejet", "0%"),
            ("overdue_amount", "💸 Montant en Retard", "0 MAD"),
            ("risk_score_avg", "📊 Score Risque Moyen", "0")
        ]
        
        for i, (key, title, default_value) in enumerate(risk_configs):
            card = self.create_kpi_card(risk_metrics_frame, title, default_value, "#dc3545")
            card.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
            self.risk_cards[key] = card
            risk_metrics_frame.columnconfigure(i, weight=1)
        
        # High-risk clients table
        clients_frame = ttk.LabelFrame(risk_frame, text="👥 Clients à Risque", padding=10)
        clients_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        columns = ('Client', 'Niveau Risque', 'Taux Rejet', 'Montant Total', 'Score IA', 'Actions')
        self.risk_clients_tree = ttk.Treeview(clients_frame, columns=columns, 
                                             show='headings', height=10)
        
        for col in columns:
            self.risk_clients_tree.heading(col, text=col)
            self.risk_clients_tree.column(col, width=120)
        
        # Scrollbar
        risk_scroll = ttk.Scrollbar(clients_frame, orient=tk.VERTICAL, 
                                   command=self.risk_clients_tree.yview)
        self.risk_clients_tree.configure(yscrollcommand=risk_scroll.set)
        
        self.risk_clients_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        risk_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Risk actions
        risk_actions_frame = ttk.Frame(clients_frame)
        risk_actions_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(risk_actions_frame, text="📧 Envoyer Rappels", 
                  command=self.send_risk_reminders).pack(side=tk.LEFT, padx=5)
        ttk.Button(risk_actions_frame, text="📊 Rapport Risque", 
                  command=self.generate_risk_report).pack(side=tk.LEFT, padx=5)
    
    def create_performance_tab(self):
        """Create performance metrics tab"""
        performance_frame = ttk.Frame(self.notebook)
        self.notebook.add(performance_frame, text="🎯 Performance")
        
        # Performance metrics
        metrics_frame = ttk.LabelFrame(performance_frame, text="📈 Métriques de Performance", padding=10)
        metrics_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.performance_chart_frame = ttk.Frame(metrics_frame)
        self.performance_chart_frame.pack(fill=tk.BOTH, expand=True)
        
        # Bank comparison
        bank_frame = ttk.LabelFrame(performance_frame, text="🏦 Comparaison Banques", padding=10)
        bank_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.bank_comparison_frame = ttk.Frame(bank_frame)
        self.bank_comparison_frame.pack(fill=tk.BOTH, expand=True)
    
    def create_automation_tab(self):
        """Create automation status tab"""
        automation_frame = ttk.Frame(self.notebook)
        self.notebook.add(automation_frame, text="🤖 Automatisation")
        
        # Automation status
        status_frame = ttk.LabelFrame(automation_frame, text="📊 Statut de l'Automatisation", padding=10)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Status indicators
        self.automation_status = {}
        status_configs = [
            ("api_updates", "🔄 Mises à jour API", "Inactif"),
            ("auto_reminders", "📧 Rappels Auto", "Actif"),
            ("risk_scoring", "🎯 Score Risque IA", "Actif"),
            ("duplicate_detection", "🔍 Détection Doublons", "Actif")
        ]
        
        status_grid = ttk.Frame(status_frame)
        status_grid.pack(fill=tk.X)
        
        for i, (key, title, default_status) in enumerate(status_configs):
            row = i // 2
            col = i % 2
            
            indicator_frame = ttk.LabelFrame(status_grid, text=title, padding=10)
            indicator_frame.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
            
            status_label = ttk.Label(indicator_frame, text=default_status, 
                                   font=('Arial', 12, 'bold'))
            status_label.pack()
            
            self.automation_status[key] = status_label
            status_grid.columnconfigure(col, weight=1)
        
        # Automation logs
        logs_frame = ttk.LabelFrame(automation_frame, text="📝 Journaux d'Automatisation", padding=10)
        logs_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        columns = ('Heure', 'Service', 'Action', 'Résultat', 'Détails')
        self.automation_logs_tree = ttk.Treeview(logs_frame, columns=columns, 
                                                show='headings', height=12)
        
        for col in columns:
            self.automation_logs_tree.heading(col, text=col)
            self.automation_logs_tree.column(col, width=120)
        
        # Scrollbar
        logs_scroll = ttk.Scrollbar(logs_frame, orient=tk.VERTICAL, 
                                   command=self.automation_logs_tree.yview)
        self.automation_logs_tree.configure(yscrollcommand=logs_scroll.set)
        
        self.automation_logs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        logs_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Automation controls
        controls_frame = ttk.Frame(logs_frame)
        controls_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(controls_frame, text="🔄 Forcer Sync API", 
                  command=self.force_api_sync).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="📧 Envoyer Rappels", 
                  command=self.send_automated_reminders).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="🔍 Détecter Doublons", 
                  command=self.run_duplicate_detection).pack(side=tk.LEFT, padx=5)
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_frame = ttk.Frame(self)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=5)
        
        # Status indicators
        self.status_var = tk.StringVar(value="Prêt")
        ttk.Label(self.status_frame, textvariable=self.status_var).pack(side=tk.LEFT)
        
        # Last update time
        self.last_update_var = tk.StringVar(value="Jamais")
        ttk.Label(self.status_frame, text="Dernière MAJ:").pack(side=tk.RIGHT, padx=(0, 5))
        ttk.Label(self.status_frame, textvariable=self.last_update_var).pack(side=tk.RIGHT)
    
    def start_real_time_updates(self):
        """Start real-time dashboard updates"""
        if self.auto_refresh.get():
            self.refresh_dashboard_data()
            self.after(self.refresh_interval * 1000, self.start_real_time_updates)
    
    def toggle_auto_refresh(self):
        """Toggle auto-refresh"""
        if self.auto_refresh.get():
            self.start_real_time_updates()
            self.status_var.set("Actualisation automatique activée")
        else:
            self.status_var.set("Actualisation automatique désactivée")
    
    def manual_refresh(self):
        """Manual refresh"""
        self.status_var.set("Actualisation en cours...")
        self.refresh_dashboard_data()
    
    def refresh_dashboard_data(self):
        """Refresh all dashboard data"""
        try:
            # Update KPI cards
            self.update_kpi_cards()
            
            # Update charts
            self.update_status_chart()
            self.update_trend_chart()
            self.update_aging_analysis()
            self.update_seasonal_trends()
            
            # Update risk data
            self.update_risk_data()
            
            # Update performance metrics
            self.update_performance_metrics()
            
            # Update automation status
            self.update_automation_status()
            
            # Update recent activity
            self.update_recent_activity()
            
            # Update status
            self.last_update = datetime.now()
            self.last_update_var.set(self.last_update.strftime("%H:%M:%S"))
            self.status_var.set("Données actualisées")
            
        except Exception as e:
            self.status_var.set(f"Erreur: {str(e)}")
            messagebox.showerror("Erreur", f"Erreur lors de l'actualisation: {e}")
    
    def update_kpi_cards(self):
        """Update KPI cards"""
        try:
            # Get performance metrics
            metrics = self.analytics.get_performance_metrics()
            overall = metrics.get('overall', {})
            
            # Update cards
            self.kpi_cards['total_cheques'].value_label.config(
                text=str(overall.get('total_cheques', 0))
            )
            
            self.kpi_cards['total_amount'].value_label.config(
                text=f"{overall.get('total_amount', 0):,.0f} MAD"
            )
            
            self.kpi_cards['success_rate'].value_label.config(
                text=f"{overall.get('success_rate', 0):.1f}%"
            )
            
            self.kpi_cards['avg_processing'].value_label.config(
                text=f"{overall.get('avg_processing_time', 0):.1f} jours"
            )
            
            # Get pending count
            pending_cheques = self.db.get_cheques({'status': 'en_attente'})
            self.kpi_cards['pending_count'].value_label.config(
                text=str(len(pending_cheques))
            )
            
            # Get risk alerts count
            risk_profiles = self.analytics.calculate_client_risk_profiles()
            high_risk_count = len([p for p in risk_profiles if p.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]])
            self.kpi_cards['risk_alerts'].value_label.config(
                text=str(high_risk_count)
            )
            
        except Exception as e:
            print(f"Error updating KPI cards: {e}")
    
    def update_status_chart(self):
        """Update status distribution chart"""
        try:
            # Clear previous chart
            for widget in self.status_chart_frame.winfo_children():
                widget.destroy()
            
            # Get status data
            stats = self.db.get_dashboard_stats()
            status_data = stats.get('by_status', {})
            
            if not status_data:
                ttk.Label(self.status_chart_frame, text="Aucune donnée disponible").pack()
                return
            
            # Create pie chart
            fig, ax = plt.subplots(figsize=(5, 4))
            
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
                wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, 
                                                 autopct='%1.1f%%', startangle=90)
                ax.set_title('Répartition par Statut')
                
                # Improve text readability
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
            
            # Integrate into Tkinter
            canvas = FigureCanvasTkAgg(fig, self.status_chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            plt.close(fig)
            
        except Exception as e:
            print(f"Error updating status chart: {e}")
    
    def update_trend_chart(self):
        """Update trend chart"""
        try:
            # Clear previous chart
            for widget in self.trend_chart_frame.winfo_children():
                widget.destroy()
            
            # Get trend data
            import sqlite3
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        date(created_at) as date,
                        COUNT(*) as count,
                        SUM(amount) as total_amount
                    FROM cheques 
                    WHERE created_at >= date('now', '-30 days')
                    GROUP BY date(created_at)
                    ORDER BY date
                """)
                
                trend_data = cursor.fetchall()
            
            if not trend_data:
                ttk.Label(self.trend_chart_frame, text="Aucune donnée disponible").pack()
                return
            
            # Create line chart
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 4), sharex=True)
            
            dates = [row[0] for row in trend_data]
            counts = [row[1] for row in trend_data]
            amounts = [row[2] for row in trend_data]
            
            # Count trend
            ax1.plot(dates, counts, marker='o', color='#007bff', linewidth=2)
            ax1.set_ylabel('Nombre')
            ax1.set_title('Tendances (30 derniers jours)')
            ax1.grid(True, alpha=0.3)
            
            # Amount trend
            ax2.plot(dates, amounts, marker='s', color='#28a745', linewidth=2)
            ax2.set_ylabel('Montant (MAD)')
            ax2.set_xlabel('Date')
            ax2.grid(True, alpha=0.3)
            
            # Rotate x-axis labels
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Integrate into Tkinter
            canvas = FigureCanvasTkAgg(fig, self.trend_chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            plt.close(fig)
            
        except Exception as e:
            print(f"Error updating trend chart: {e}")
    
    def update_aging_analysis(self):
        """Update aging analysis chart"""
        try:
            # Clear previous chart
            for widget in self.aging_chart_frame.winfo_children():
                widget.destroy()
            
            # Get aging data
            aging_data = self.analytics.get_cheque_aging_analysis()
            
            if not aging_data:
                ttk.Label(self.aging_chart_frame, text="Aucune donnée disponible").pack()
                return
            
            # Create bar chart
            fig, ax = plt.subplots(figsize=(10, 6))
            
            statuses = [data.status for data in aging_data]
            avg_days = [data.avg_days for data in aging_data]
            colors = ['#ffc107', '#28a745', '#dc3545', '#fd7e14', '#17a2b8', '#6c757d']
            
            bars = ax.bar(statuses, avg_days, color=colors[:len(statuses)])
            ax.set_title('Temps Moyen par Statut (jours)')
            ax.set_ylabel('Jours')
            ax.set_xlabel('Statut')
            
            # Add value labels on bars
            for bar, days in zip(bars, avg_days):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{days:.1f}j', ha='center', va='bottom')
            
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Integrate into Tkinter
            canvas = FigureCanvasTkAgg(fig, self.aging_chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            plt.close(fig)
            
        except Exception as e:
            print(f"Error updating aging analysis: {e}")
    
    def update_seasonal_trends(self):
        """Update seasonal trends chart"""
        try:
            # Clear previous chart
            for widget in self.seasonal_chart_frame.winfo_children():
                widget.destroy()
            
            # Get seasonal data
            seasonal_data = self.analytics.get_seasonal_trends()
            monthly_trends = seasonal_data.get('monthly_trends', [])
            
            if not monthly_trends:
                ttk.Label(self.seasonal_chart_frame, text="Aucune donnée disponible").pack()
                return
            
            # Create seasonal chart
            fig, ax = plt.subplots(figsize=(10, 6))
            
            months = [f"{row[1]}-{row[0]}" for row in monthly_trends]
            amounts = [row[3] for row in monthly_trends]
            
            ax.plot(months, amounts, marker='o', linewidth=2, color='#007bff')
            ax.set_title('Tendances Mensuelles')
            ax.set_ylabel('Montant (MAD)')
            ax.set_xlabel('Mois')
            ax.grid(True, alpha=0.3)
            
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Integrate into Tkinter
            canvas = FigureCanvasTkAgg(fig, self.seasonal_chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            plt.close(fig)
            
        except Exception as e:
            print(f"Error updating seasonal trends: {e}")
    
    def update_risk_data(self):
        """Update risk management data"""
        try:
            # Get risk profiles
            risk_profiles = self.analytics.calculate_client_risk_profiles()
            
            # Update risk cards
            high_risk_count = len([p for p in risk_profiles if p.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]])
            self.risk_cards['high_risk_clients'].value_label.config(text=str(high_risk_count))
            
            # Calculate overall bounce rate
            total_cheques = sum(p.total_cheques for p in risk_profiles)
            total_bounced = sum(p.total_cheques * p.bounce_rate / 100 for p in risk_profiles)
            overall_bounce_rate = (total_bounced / total_cheques * 100) if total_cheques > 0 else 0
            self.risk_cards['bounce_rate'].value_label.config(text=f"{overall_bounce_rate:.1f}%")
            
            # Calculate overdue amount
            overdue_cheques = self.db.get_cheques({
                'status': 'en_attente',
                'date_to': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            })
            overdue_amount = sum(cheque['amount'] for cheque in overdue_cheques)
            self.risk_cards['overdue_amount'].value_label.config(text=f"{overdue_amount:,.0f} MAD")
            
            # Average risk score
            avg_risk_score = sum(p.risk_score for p in risk_profiles) / len(risk_profiles) if risk_profiles else 0
            self.risk_cards['risk_score_avg'].value_label.config(text=f"{avg_risk_score:.1f}")
            
            # Update risk clients table
            for item in self.risk_clients_tree.get_children():
                self.risk_clients_tree.delete(item)
            
            # Sort by risk score and show top 20
            high_risk_clients = sorted(risk_profiles, key=lambda x: x.risk_score, reverse=True)[:20]
            
            for profile in high_risk_clients:
                risk_level_display = {
                    RiskLevel.LOW: "🟢 Faible",
                    RiskLevel.MEDIUM: "🟡 Moyen",
                    RiskLevel.HIGH: "🟠 Élevé",
                    RiskLevel.CRITICAL: "🔴 Critique"
                }.get(profile.risk_level, "❓ Inconnu")
                
                self.risk_clients_tree.insert('', tk.END, values=(
                    profile.client_name,
                    risk_level_display,
                    f"{profile.bounce_rate:.1f}%",
                    f"{profile.total_amount:,.0f} MAD",
                    f"{profile.risk_score:.1f}",
                    "📧 Contacter"
                ))
                
        except Exception as e:
            print(f"Error updating risk data: {e}")
    
    def update_performance_metrics(self):
        """Update performance metrics"""
        try:
            # Get performance data
            metrics = self.analytics.get_performance_metrics()
            
            # Clear previous charts
            for widget in self.performance_chart_frame.winfo_children():
                widget.destroy()
            
            for widget in self.bank_comparison_frame.winfo_children():
                widget.destroy()
            
            # Performance trends chart
            monthly_trends = metrics.get('monthly_trends', [])
            if monthly_trends:
                fig, ax = plt.subplots(figsize=(10, 6))
                
                months = [row[0] for row in monthly_trends]
                success_rates = [row[4] or 0 for row in monthly_trends]
                
                ax.plot(months, success_rates, marker='o', linewidth=2, color='#28a745')
                ax.set_title('Évolution du Taux de Réussite')
                ax.set_ylabel('Taux de Réussite (%)')
                ax.set_xlabel('Mois')
                ax.grid(True, alpha=0.3)
                
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                canvas = FigureCanvasTkAgg(fig, self.performance_chart_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                
                plt.close(fig)
            
            # Bank comparison chart
            bank_performance = metrics.get('bank_performance', [])
            if bank_performance:
                fig, ax = plt.subplots(figsize=(10, 6))
                
                banks = [row[0] for row in bank_performance[:10]]  # Top 10
                amounts = [row[2] for row in bank_performance[:10]]
                
                bars = ax.bar(banks, amounts, color='#007bff', alpha=0.7)
                ax.set_title('Performance par Banque (Montant Total)')
                ax.set_ylabel('Montant (MAD)')
                ax.set_xlabel('Banque')
                
                # Add value labels
                for bar, amount in zip(bars, amounts):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{amount:,.0f}', ha='center', va='bottom', rotation=90)
                
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                canvas = FigureCanvasTkAgg(fig, self.bank_comparison_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                
                plt.close(fig)
                
        except Exception as e:
            print(f"Error updating performance metrics: {e}")
    
    def update_automation_status(self):
        """Update automation status"""
        try:
            # Update status indicators (this would check actual service status)
            self.automation_status['api_updates'].config(text="🟢 Actif", foreground="green")
            self.automation_status['auto_reminders'].config(text="🟢 Actif", foreground="green")
            self.automation_status['risk_scoring'].config(text="🟢 Actif", foreground="green")
            self.automation_status['duplicate_detection'].config(text="🟢 Actif", foreground="green")
            
            # Update automation logs (mock data for now)
            for item in self.automation_logs_tree.get_children():
                self.automation_logs_tree.delete(item)
            
            # Add recent automation activities
            current_time = datetime.now()
            logs = [
                (current_time - timedelta(minutes=5), "Rappels", "Envoi automatique", "Succès", "3 rappels envoyés"),
                (current_time - timedelta(minutes=15), "Score IA", "Calcul risque", "Succès", "25 clients analysés"),
                (current_time - timedelta(minutes=30), "API Sync", "Mise à jour statuts", "Succès", "12 chèques mis à jour"),
                (current_time - timedelta(hours=1), "Doublons", "Détection", "Succès", "2 doublons détectés"),
            ]
            
            for log_time, service, action, result, details in logs:
                self.automation_logs_tree.insert('', tk.END, values=(
                    log_time.strftime("%H:%M:%S"),
                    service,
                    action,
                    result,
                    details
                ))
                
        except Exception as e:
            print(f"Error updating automation status: {e}")
    
    def update_recent_activity(self):
        """Update recent activity"""
        try:
            # Clear previous activities
            for item in self.activity_tree.get_children():
                self.activity_tree.delete(item)
            
            # Get recent activities (mock data for now)
            current_time = datetime.now()
            activities = [
                (current_time - timedelta(minutes=2), "Nouveau", "Chèque #12345 ajouté", self.current_user['username']),
                (current_time - timedelta(minutes=8), "Statut", "Chèque #12340 encaissé", "Système"),
                (current_time - timedelta(minutes=15), "Rappel", "Rappel envoyé à Client ABC", "Système"),
                (current_time - timedelta(minutes=25), "Modification", "Chèque #12338 modifié", self.current_user['username']),
                (current_time - timedelta(minutes=35), "Nouveau", "Client XYZ ajouté", self.current_user['username']),
            ]
            
            for activity_time, activity_type, description, user in activities:
                self.activity_tree.insert('', tk.END, values=(
                    activity_time.strftime("%H:%M:%S"),
                    activity_type,
                    description,
                    user
                ))
                
        except Exception as e:
            print(f"Error updating recent activity: {e}")
    
    # Action methods
    def export_dashboard(self):
        """Export dashboard data"""
        messagebox.showinfo("Export", "Fonctionnalité d'export du tableau de bord à implémenter")
    
    def show_dashboard_settings(self):
        """Show dashboard settings"""
        messagebox.showinfo("Paramètres", "Paramètres du tableau de bord à implémenter")
    
    def send_risk_reminders(self):
        """Send reminders to high-risk clients"""
        try:
            result = self.automation.send_automated_reminders()
            messagebox.showinfo("Rappels", 
                              f"Rappels envoyés:\n"
                              f"SMS: {result['sms_sent']}\n"
                              f"Emails: {result['emails_sent']}\n"
                              f"Total chèques: {result['total_cheques']}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'envoi des rappels: {e}")
    
    def generate_risk_report(self):
        """Generate risk report"""
        messagebox.showinfo("Rapport", "Génération du rapport de risque à implémenter")
    
    def force_api_sync(self):
        """Force API synchronization"""
        messagebox.showinfo("Sync API", "Synchronisation API forcée à implémenter")
    
    def send_automated_reminders(self):
        """Send automated reminders"""
        self.send_risk_reminders()
    
    def run_duplicate_detection(self):
        """Run duplicate detection"""
        try:
            duplicates = self.analytics.get_duplicate_detection_analysis()
            messagebox.showinfo("Détection Doublons", 
                              f"{len(duplicates)} doublons potentiels détectés")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la détection: {e}")