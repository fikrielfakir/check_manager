#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire de Chèques Professionnel
Version 3.0 - Architecture Modulaire

Système complet de gestion de chèques avec :
- Gestion des banques et agences
- Gestion des clients (personnes/entreprises)
- Suivi des chèques avec statuts
- Exports et rapports
- Notifications automatiques
- Authentification et rôles
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
from pathlib import Path

# Ajouter le répertoire des modules au path
sys.path.append(str(Path(__file__).parent))

from database.db_manager import DatabaseManager
from ui.main_window import MainWindow
from utils.config import Config
from utils.logger import setup_logger

def main():
    """Point d'entrée principal de l'application"""
    try:
        # Configuration du logging
        logger = setup_logger()
        logger.info("🚀 Démarrage du Gestionnaire de Chèques Pro v3.0")
        
        # Initialisation de la configuration
        config = Config()
        
        # Initialisation de la base de données
        db_manager = DatabaseManager(config.get_db_path())
        
        # Création de la fenêtre principale
        root = tk.Tk()
        app = MainWindow(root, db_manager, config)
        
        # Démarrage de l'application
        logger.info("✅ Application initialisée avec succès")
        root.mainloop()
        
    except Exception as e:
        error_msg = f"Erreur fatale lors du démarrage: {str(e)}"
        print(error_msg)
        if 'root' in locals():
            messagebox.showerror("Erreur Fatale", error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()
