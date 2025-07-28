#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration du système de logging
"""

import logging
import logging.handlers
from pathlib import Path
import sys

def setup_logger(name="cheque_manager", level=logging.INFO):
    """Configure le système de logging"""
    
    # Créer le répertoire de logs
    log_dir = Path.home() / ".cheque_manager" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configuration du logger principal
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Éviter la duplication des handlers
    if logger.handlers:
        return logger
    
    # Format des messages
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler pour fichier avec rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "cheque_manager.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Handler pour console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)  # Moins verbeux en console
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger
