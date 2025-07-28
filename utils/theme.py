#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire de thèmes pour l'interface
"""

import tkinter as tk
from tkinter import ttk

class ThemeManager:
    """Gestionnaire de thèmes pour l'application"""
    
    def __init__(self):
        self.current_theme = "default"
        self.themes = {
            "default": {
                "bg": "#f0f0f0",
                "fg": "#000000",
                "select_bg": "#0078d4",
                "select_fg": "#ffffff",
                "button_bg": "#e1e1e1",
                "entry_bg": "#ffffff"
            },
            "dark": {
                "bg": "#2d2d2d",
                "fg": "#ffffff",
                "select_bg": "#404040",
                "select_fg": "#ffffff",
                "button_bg": "#404040",
                "entry_bg": "#3d3d3d"
            },
            "blue": {
                "bg": "#f0f8ff",
                "fg": "#000080",
                "select_bg": "#4169e1",
                "select_fg": "#ffffff",
                "button_bg": "#e6f3ff",
                "entry_bg": "#ffffff"
            }
        }
    
    def apply_theme(self, root, theme_name="default"):
        """Applique un thème à l'application"""
        if theme_name not in self.themes:
            theme_name = "default"
        
        self.current_theme = theme_name
        theme = self.themes[theme_name]
        
        # Configuration du style ttk
        style = ttk.Style()
        
        # Thème de base
        if theme_name == "dark":
            style.theme_use('clam')
        else:
            style.theme_use('default')
        
        # Configuration des couleurs
        style.configure('TLabel', background=theme['bg'], foreground=theme['fg'])
        style.configure('TFrame', background=theme['bg'])
        style.configure('TLabelFrame', background=theme['bg'], foreground=theme['fg'])
        style.configure('TButton', background=theme['button_bg'], foreground=theme['fg'])
        style.configure('TEntry', fieldbackground=theme['entry_bg'], foreground=theme['fg'])
        style.configure('TCombobox', fieldbackground=theme['entry_bg'], foreground=theme['fg'])
        
        # Configuration de la fenêtre principale
        root.configure(bg=theme['bg'])
        
        # Styles personnalisés
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), 
                       background=theme['bg'], foreground=theme['fg'])
        style.configure('Subtitle.TLabel', font=('Arial', 12), 
                       background=theme['bg'], foreground=theme['fg'])
        
        # Styles pour les boutons d'action
        style.configure('Success.TButton', background='#28a745', foreground='white')
        style.configure('Danger.TButton', background='#dc3545', foreground='white')
        style.configure('Warning.TButton', background='#ffc107', foreground='black')
        style.configure('Info.TButton', background='#17a2b8', foreground='white')
    
    def get_color(self, color_key):
        """Récupère une couleur du thème actuel"""
        return self.themes[self.current_theme].get(color_key, "#000000")
    
    def get_status_color(self, status):
        """Retourne la couleur associée à un statut"""
        status_colors = {
            'en_attente': '#ffc107',    # Jaune
            'encaisse': '#28a745',      # Vert
            'rejete': '#dc3545',        # Rouge
            'impaye': '#fd7e14',        # Orange
            'depose': '#17a2b8',        # Bleu
            'annule': '#6c757d'         # Gris
        }
        return status_colors.get(status, '#6c757d')
    
    def get_status_badge(self, status):
        """Retourne un badge coloré pour un statut"""
        badges = {
            'en_attente': '⏳ En Attente',
            'encaisse': '✅ Encaissé',
            'rejete': '❌ Rejeté',
            'impaye': '⚠️ Impayé',
            'depose': '📤 Déposé',
            'annule': '🚫 Annulé'
        }
        return badges.get(status, status)
