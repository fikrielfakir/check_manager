#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire de configuration
"""

import os
import json
from pathlib import Path

class Config:
    """Gestionnaire de configuration de l'application"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".cheque_manager"
        self.config_file = self.config_dir / "config.json"
        self.data_dir = self.config_dir / "data"
        
        # Créer les répertoires si nécessaire
        self.config_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
        
        # Charger la configuration
        self.config = self.load_config()
    
    def load_config(self):
        """Charge la configuration depuis le fichier"""
        default_config = {
            "database": {
                "path": str(self.data_dir / "cheques.db"),
                "backup_enabled": True,
                "backup_interval": 24  # heures
            },
            "ui": {
                "theme": "default",
                "language": "fr",
                "window_size": "1400x900"
            },
            "notifications": {
                "enabled": True,
                "due_days": 3,
                "email_enabled": False
            },
            "exports": {
                "default_format": "xlsx",
                "output_dir": str(self.data_dir / "exports")
            }
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Fusionner avec la config par défaut
                    default_config.update(loaded_config)
            except Exception as e:
                print(f"Erreur lors du chargement de la configuration: {e}")
        
        return default_config
    
    def save_config(self):
        """Sauvegarde la configuration"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la configuration: {e}")
    
    def get(self, key, default=None):
        """Récupère une valeur de configuration"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key, value):
        """Définit une valeur de configuration"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.save_config()
    
    def get_db_path(self):
        """Retourne le chemin de la base de données"""
        return self.get("database.path")
    
    def get_exports_dir(self):
        """Retourne le répertoire d'exports"""
        exports_dir = Path(self.get("exports.output_dir"))
        exports_dir.mkdir(exist_ok=True)
        return str(exports_dir)
