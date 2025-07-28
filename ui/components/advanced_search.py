#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Search Component with Fuzzy Search and Dynamic Filters
"""

import tkinter as tk
from tkinter import ttk
import sqlite3
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
import re
from difflib import SequenceMatcher

class FuzzySearchEngine:
    """Fuzzy search engine for intelligent text matching"""
    
    def __init__(self, threshold: float = 0.6):
        self.threshold = threshold
    
    def similarity(self, a: str, b: str) -> float:
        """Calculate similarity between two strings"""
        if not a or not b:
            return 0.0
        
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    def fuzzy_match(self, query: str, text: str) -> bool:
        """Check if query fuzzy matches text"""
        if not query or not text:
            return False
        
        # Exact match
        if query.lower() in text.lower():
            return True
        
        # Fuzzy match
        return self.similarity(query, text) >= self.threshold
    
    def search_in_fields(self, query: str, fields: List[str]) -> bool:
        """Search query in multiple fields"""
        for field in fields:
            if field and self.fuzzy_match(query, str(field)):
                return True
        return False

class DynamicFilter:
    """Dynamic filter that can be added/removed at runtime"""
    
    def __init__(self, field: str, operator: str, value: Any, label: str = None):
        self.field = field
        self.operator = operator  # 'equals', 'contains', 'greater', 'less', 'between', 'in'
        self.value = value
        self.label = label or f"{field} {operator} {value}"
        self.active = True
    
    def to_sql(self) -> tuple[str, List[Any]]:
        """Convert filter to SQL WHERE clause"""
        if not self.active:
            return "", []
        
        if self.operator == 'equals':
            return f"{self.field} = ?", [self.value]
        elif self.operator == 'contains':
            return f"{self.field} LIKE ?", [f"%{self.value}%"]
        elif self.operator == 'greater':
            return f"{self.field} > ?", [self.value]
        elif self.operator == 'less':
            return f"{self.field} < ?", [self.value]
        elif self.operator == 'between':
            return f"{self.field} BETWEEN ? AND ?", self.value
        elif self.operator == 'in':
            placeholders = ','.join(['?' for _ in self.value])
            return f"{self.field} IN ({placeholders})", self.value
        else:
            return "", []

class SavedSearch:
    """Saved search configuration"""
    
    def __init__(self, name: str, query: str, filters: List[DynamicFilter], 
                 sort_field: str = None, sort_order: str = 'ASC'):
        self.name = name
        self.query = query
        self.filters = filters
        self.sort_field = sort_field
        self.sort_order = sort_order
        self.created_at = datetime.now()
        self.last_used = None

class AdvancedSearchFrame(ttk.Frame):
    """Advanced search component with fuzzy search and dynamic filters"""
    
    def __init__(self, parent, db_manager, on_results_callback=None):
        super().__init__(parent)
        self.db = db_manager
        self.on_results_callback = on_results_callback
        
        # Search components
        self.fuzzy_engine = FuzzySearchEngine()
        self.active_filters = []
        self.saved_searches = []
        
        # Search state
        self.current_results = []
        self.search_history = []
        
        # UI setup
        self.setup_ui()
        
        # Load saved searches
        self.load_saved_searches()
    
    def setup_ui(self):
        """Setup the advanced search UI"""
        # Main search bar
        self.create_search_bar()
        
        # Quick filters
        self.create_quick_filters()
        
        # Dynamic filters area
        self.create_dynamic_filters_area()
        
        # Search results info
        self.create_results_info()
        
        # Saved searches
        self.create_saved_searches_section()
    
    def create_search_bar(self):
        """Create main search bar"""
        search_frame = ttk.LabelFrame(self, text="🔍 Recherche Avancée", padding=10)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Search input
        input_frame = ttk.Frame(search_frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(input_frame, textvariable=self.search_var, 
                                     font=('Arial', 11), width=50)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Search button
        ttk.Button(input_frame, text="🔍 Rechercher", 
                  command=self.perform_search).pack(side=tk.LEFT, padx=(5, 0))
        
        # Clear button
        ttk.Button(input_frame, text="🗑️ Effacer", 
                  command=self.clear_search).pack(side=tk.LEFT, padx=(5, 0))
        
        # Search options
        options_frame = ttk.Frame(search_frame)
        options_frame.pack(fill=tk.X, pady=5)
        
        # Fuzzy search toggle
        self.fuzzy_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Recherche approximative", 
                       variable=self.fuzzy_enabled).pack(side=tk.LEFT)
        
        # Case sensitive toggle
        self.case_sensitive = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Sensible à la casse", 
                       variable=self.case_sensitive).pack(side=tk.LEFT, padx=(20, 0))
        
        # Search in fields
        ttk.Label(options_frame, text="Rechercher dans:").pack(side=tk.LEFT, padx=(20, 5))
        
        self.search_fields = {
            'cheque_number': tk.BooleanVar(value=True),
            'client_name': tk.BooleanVar(value=True),
            'depositor_name': tk.BooleanVar(value=True),
            'notes': tk.BooleanVar(value=False)
        }
        
        for field, var in self.search_fields.items():
            field_labels = {
                'cheque_number': 'N° Chèque',
                'client_name': 'Client',
                'depositor_name': 'Déposant',
                'notes': 'Notes'
            }
            ttk.Checkbutton(options_frame, text=field_labels[field], 
                           variable=var).pack(side=tk.LEFT, padx=(5, 0))
        
        # Bind Enter key
        self.search_entry.bind('<Return>', lambda e: self.perform_search())
        self.search_entry.bind('<KeyRelease>', self.on_search_change)
    
    def create_quick_filters(self):
        """Create quick filter buttons"""
        quick_frame = ttk.LabelFrame(self, text="⚡ Filtres Rapides", padding=10)
        quick_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Status filters
        status_frame = ttk.Frame(quick_frame)
        status_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(status_frame, text="Statut:").pack(side=tk.LEFT)
        
        status_filters = [
            ("Tous", None),
            ("En Attente", "en_attente"),
            ("Encaissé", "encaisse"),
            ("Rejeté", "rejete"),
            ("En Retard", "overdue")
        ]
        
        for label, status in status_filters:
            btn = ttk.Button(status_frame, text=label, width=12,
                           command=lambda s=status: self.add_status_filter(s))
            btn.pack(side=tk.LEFT, padx=2)
        
        # Date filters
        date_frame = ttk.Frame(quick_frame)
        date_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(date_frame, text="Période:").pack(side=tk.LEFT)
        
        date_filters = [
            ("Aujourd'hui", 0),
            ("Cette semaine", 7),
            ("Ce mois", 30),
            ("3 mois", 90),
            ("Cette année", 365)
        ]
        
        for label, days in date_filters:
            btn = ttk.Button(date_frame, text=label, width=12,
                           command=lambda d=days: self.add_date_filter(d))
            btn.pack(side=tk.LEFT, padx=2)
        
        # Amount filters
        amount_frame = ttk.Frame(quick_frame)
        amount_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(amount_frame, text="Montant:").pack(side=tk.LEFT)
        
        amount_filters = [
            ("< 1000", (0, 1000)),
            ("1K - 5K", (1000, 5000)),
            ("5K - 10K", (5000, 10000)),
            ("10K - 50K", (10000, 50000)),
            ("> 50K", (50000, float('inf')))
        ]
        
        for label, (min_amt, max_amt) in amount_filters:
            btn = ttk.Button(amount_frame, text=label, width=12,
                           command=lambda mn=min_amt, mx=max_amt: self.add_amount_filter(mn, mx))
            btn.pack(side=tk.LEFT, padx=2)
    
    def create_dynamic_filters_area(self):
        """Create dynamic filters management area"""
        filters_frame = ttk.LabelFrame(self, text="🎛️ Filtres Actifs", padding=10)
        filters_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Filters container
        self.filters_container = ttk.Frame(filters_frame)
        self.filters_container.pack(fill=tk.X, pady=5)
        
        # Add filter controls
        add_filter_frame = ttk.Frame(filters_frame)
        add_filter_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(add_filter_frame, text="➕ Ajouter Filtre", 
                  command=self.show_add_filter_dialog).pack(side=tk.LEFT)
        
        ttk.Button(add_filter_frame, text="🗑️ Effacer Tous", 
                  command=self.clear_all_filters).pack(side=tk.LEFT, padx=(10, 0))
        
        # Filter summary
        self.filter_summary_var = tk.StringVar(value="Aucun filtre actif")
        ttk.Label(add_filter_frame, textvariable=self.filter_summary_var, 
                 font=('Arial', 9, 'italic')).pack(side=tk.RIGHT)
    
    def create_results_info(self):
        """Create search results information area"""
        results_frame = ttk.Frame(self)
        results_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Results count and info
        self.results_info_var = tk.StringVar(value="Prêt à rechercher")
        ttk.Label(results_frame, textvariable=self.results_info_var, 
                 font=('Arial', 10)).pack(side=tk.LEFT)
        
        # Search time
        self.search_time_var = tk.StringVar()
        ttk.Label(results_frame, textvariable=self.search_time_var, 
                 font=('Arial', 9, 'italic')).pack(side=tk.RIGHT)
    
    def create_saved_searches_section(self):
        """Create saved searches section"""
        saved_frame = ttk.LabelFrame(self, text="💾 Recherches Sauvegardées", padding=10)
        saved_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Saved searches list
        list_frame = ttk.Frame(saved_frame)
        list_frame.pack(fill=tk.X, pady=5)
        
        self.saved_searches_combo = ttk.Combobox(list_frame, state="readonly", width=30)
        self.saved_searches_combo.pack(side=tk.LEFT)
        self.saved_searches_combo.bind('<<ComboboxSelected>>', self.load_saved_search)
        
        # Controls
        ttk.Button(list_frame, text="📂 Charger", 
                  command=self.load_selected_search).pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Button(list_frame, text="💾 Sauvegarder", 
                  command=self.save_current_search).pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Button(list_frame, text="🗑️ Supprimer", 
                  command=self.delete_saved_search).pack(side=tk.LEFT, padx=(5, 0))
    
    def on_search_change(self, event=None):
        """Handle search input changes for live search"""
        query = self.search_var.get()
        
        # Perform live search if query is long enough
        if len(query) >= 3:
            self.after(500, self.perform_search)  # Debounce
    
    def perform_search(self):
        """Perform the search with current criteria"""
        start_time = datetime.now()
        
        try:
            query = self.search_var.get().strip()
            
            # Build SQL query
            sql_query, params = self.build_search_query(query)
            
            # Execute search
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(sql_query, params)
                
                # Get column names
                columns = [desc[0] for desc in cursor.description]
                
                # Fetch results
                rows = cursor.fetchall()
                
                # Convert to dictionaries
                self.current_results = [dict(zip(columns, row)) for row in rows]
            
            # Apply fuzzy search if enabled
            if self.fuzzy_enabled.get() and query:
                self.current_results = self.apply_fuzzy_filter(query, self.current_results)
            
            # Update UI
            search_time = (datetime.now() - start_time).total_seconds()
            self.update_results_info(len(self.current_results), search_time)
            
            # Add to search history
            self.add_to_search_history(query)
            
            # Callback with results
            if self.on_results_callback:
                self.on_results_callback(self.current_results)
                
        except Exception as e:
            self.results_info_var.set(f"Erreur: {e}")
    
    def build_search_query(self, query: str) -> tuple[str, List[Any]]:
        """Build SQL query from search criteria"""
        base_query = """
            SELECT c.*, 
                   cl.name as client_name, cl.type as client_type,
                   b.name as branch_name, bk.name as bank_name
            FROM cheques c
            LEFT JOIN clients cl ON c.client_id = cl.id
            LEFT JOIN branches b ON c.branch_id = b.id
            LEFT JOIN banks bk ON b.bank_id = bk.id
        """
        
        where_clauses = []
        params = []
        
        # Text search
        if query:
            search_conditions = []
            
            for field, enabled in self.search_fields.items():
                if enabled.get():
                    if field == 'cheque_number':
                        search_conditions.append("c.cheque_number LIKE ?")
                    elif field == 'client_name':
                        search_conditions.append("cl.name LIKE ?")
                    elif field == 'depositor_name':
                        search_conditions.append("c.depositor_name LIKE ?")
                    elif field == 'notes':
                        search_conditions.append("c.notes LIKE ?")
                    
                    params.append(f"%{query}%")
            
            if search_conditions:
                where_clauses.append(f"({' OR '.join(search_conditions)})")
        
        # Apply dynamic filters
        for filter_obj in self.active_filters:
            if filter_obj.active:
                filter_sql, filter_params = filter_obj.to_sql()
                if filter_sql:
                    where_clauses.append(filter_sql)
                    params.extend(filter_params)
        
        # Combine query
        if where_clauses:
            base_query += " WHERE " + " AND ".join(where_clauses)
        
        base_query += " ORDER BY c.created_at DESC"
        
        return base_query, params
    
    def apply_fuzzy_filter(self, query: str, results: List[Dict]) -> List[Dict]:
        """Apply fuzzy search filtering to results"""
        if not query:
            return results
        
        fuzzy_results = []
        
        for result in results:
            # Check fuzzy match in enabled fields
            search_fields = []
            
            if self.search_fields['cheque_number'].get():
                search_fields.append(result.get('cheque_number', ''))
            if self.search_fields['client_name'].get():
                search_fields.append(result.get('client_name', ''))
            if self.search_fields['depositor_name'].get():
                search_fields.append(result.get('depositor_name', ''))
            if self.search_fields['notes'].get():
                search_fields.append(result.get('notes', ''))
            
            if self.fuzzy_engine.search_in_fields(query, search_fields):
                fuzzy_results.append(result)
        
        return fuzzy_results
    
    def add_status_filter(self, status: str):
        """Add status filter"""
        # Remove existing status filters
        self.active_filters = [f for f in self.active_filters if f.field != 'c.status']
        
        if status == "overdue":
            # Special case for overdue cheques
            filter_obj = DynamicFilter(
                field="c.due_date",
                operator="less",
                value=date.today().isoformat(),
                label="En retard"
            )
            filter_obj.to_sql = lambda: ("c.due_date < date('now') AND c.status IN ('en_attente', 'depose')", [])
        elif status:
            filter_obj = DynamicFilter(
                field="c.status",
                operator="equals",
                value=status,
                label=f"Statut: {status}"
            )
        else:
            return  # "Tous" - no filter
        
        self.active_filters.append(filter_obj)
        self.update_filters_display()
        self.perform_search()
    
    def add_date_filter(self, days: int):
        """Add date range filter"""
        # Remove existing date filters
        self.active_filters = [f for f in self.active_filters 
                              if not f.field.startswith('c.') or 'date' not in f.field]
        
        if days == 0:
            # Today
            filter_obj = DynamicFilter(
                field="date(c.created_at)",
                operator="equals",
                value=date.today().isoformat(),
                label="Aujourd'hui"
            )
        else:
            # Last N days
            start_date = (date.today() - timedelta(days=days)).isoformat()
            filter_obj = DynamicFilter(
                field="c.created_at",
                operator="greater",
                value=start_date,
                label=f"Derniers {days} jours"
            )
        
        self.active_filters.append(filter_obj)
        self.update_filters_display()
        self.perform_search()
    
    def add_amount_filter(self, min_amount: float, max_amount: float):
        """Add amount range filter"""
        # Remove existing amount filters
        self.active_filters = [f for f in self.active_filters if f.field != 'c.amount']
        
        if max_amount == float('inf'):
            filter_obj = DynamicFilter(
                field="c.amount",
                operator="greater",
                value=min_amount,
                label=f"Montant > {min_amount:,.0f}"
            )
        else:
            filter_obj = DynamicFilter(
                field="c.amount",
                operator="between",
                value=[min_amount, max_amount],
                label=f"Montant: {min_amount:,.0f} - {max_amount:,.0f}"
            )
        
        self.active_filters.append(filter_obj)
        self.update_filters_display()
        self.perform_search()
    
    def show_add_filter_dialog(self):
        """Show dialog to add custom filter"""
        dialog = AddFilterDialog(self, self.add_custom_filter)
    
    def add_custom_filter(self, filter_obj: DynamicFilter):
        """Add custom filter"""
        self.active_filters.append(filter_obj)
        self.update_filters_display()
        self.perform_search()
    
    def update_filters_display(self):
        """Update the display of active filters"""
        # Clear existing filter widgets
        for widget in self.filters_container.winfo_children():
            widget.destroy()
        
        if not self.active_filters:
            self.filter_summary_var.set("Aucun filtre actif")
            return
        
        # Create filter chips
        for i, filter_obj in enumerate(self.active_filters):
            filter_frame = ttk.Frame(self.filters_container)
            filter_frame.pack(side=tk.LEFT, padx=2, pady=2)
            
            # Filter label
            label = ttk.Label(filter_frame, text=filter_obj.label, 
                             background="#e3f2fd", padding=5)
            label.pack(side=tk.LEFT)
            
            # Remove button
            remove_btn = ttk.Button(filter_frame, text="✕", width=3,
                                   command=lambda idx=i: self.remove_filter(idx))
            remove_btn.pack(side=tk.LEFT)
        
        # Update summary
        active_count = len([f for f in self.active_filters if f.active])
        self.filter_summary_var.set(f"{active_count} filtre(s) actif(s)")
    
    def remove_filter(self, index: int):
        """Remove filter by index"""
        if 0 <= index < len(self.active_filters):
            del self.active_filters[index]
            self.update_filters_display()
            self.perform_search()
    
    def clear_all_filters(self):
        """Clear all active filters"""
        self.active_filters.clear()
        self.update_filters_display()
        self.perform_search()
    
    def clear_search(self):
        """Clear search and filters"""
        self.search_var.set("")
        self.clear_all_filters()
        self.current_results.clear()
        self.results_info_var.set("Recherche effacée")
        
        if self.on_results_callback:
            self.on_results_callback([])
    
    def update_results_info(self, count: int, search_time: float):
        """Update results information display"""
        self.results_info_var.set(f"📊 {count} résultat(s) trouvé(s)")
        self.search_time_var.set(f"⏱️ {search_time:.2f}s")
    
    def add_to_search_history(self, query: str):
        """Add query to search history"""
        if query and query not in self.search_history:
            self.search_history.insert(0, query)
            # Keep only last 20 searches
            self.search_history = self.search_history[:20]
    
    def save_current_search(self):
        """Save current search configuration"""
        dialog = SaveSearchDialog(self, self.search_var.get(), 
                                 self.active_filters.copy(), self.save_search)
    
    def save_search(self, saved_search: SavedSearch):
        """Save search configuration"""
        self.saved_searches.append(saved_search)
        self.update_saved_searches_combo()
        self.persist_saved_searches()
    
    def load_saved_search(self, event=None):
        """Load selected saved search"""
        self.load_selected_search()
    
    def load_selected_search(self):
        """Load the selected saved search"""
        selection = self.saved_searches_combo.get()
        if not selection:
            return
        
        # Find saved search
        saved_search = None
        for search in self.saved_searches:
            if search.name == selection:
                saved_search = search
                break
        
        if saved_search:
            # Load search criteria
            self.search_var.set(saved_search.query)
            self.active_filters = saved_search.filters.copy()
            
            # Update display
            self.update_filters_display()
            
            # Perform search
            self.perform_search()
            
            # Update last used
            saved_search.last_used = datetime.now()
    
    def delete_saved_search(self):
        """Delete selected saved search"""
        selection = self.saved_searches_combo.get()
        if not selection:
            return
        
        # Remove from list
        self.saved_searches = [s for s in self.saved_searches if s.name != selection]
        
        # Update combo
        self.update_saved_searches_combo()
        
        # Persist changes
        self.persist_saved_searches()
    
    def update_saved_searches_combo(self):
        """Update saved searches combobox"""
        search_names = [search.name for search in self.saved_searches]
        self.saved_searches_combo['values'] = search_names
    
    def load_saved_searches(self):
        """Load saved searches from database"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Create table if not exists
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS saved_searches (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        query TEXT,
                        filters TEXT,
                        sort_field TEXT,
                        sort_order TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_used TIMESTAMP
                    )
                ''')
                
                # Load searches
                cursor.execute('SELECT * FROM saved_searches ORDER BY last_used DESC')
                
                for row in cursor.fetchall():
                    try:
                        filters_data = json.loads(row[3]) if row[3] else []
                        filters = []
                        
                        for filter_data in filters_data:
                            filter_obj = DynamicFilter(
                                field=filter_data['field'],
                                operator=filter_data['operator'],
                                value=filter_data['value'],
                                label=filter_data['label']
                            )
                            filters.append(filter_obj)
                        
                        saved_search = SavedSearch(
                            name=row[1],
                            query=row[2] or '',
                            filters=filters,
                            sort_field=row[4],
                            sort_order=row[5] or 'ASC'
                        )
                        
                        if row[6]:
                            saved_search.created_at = datetime.fromisoformat(row[6])
                        if row[7]:
                            saved_search.last_used = datetime.fromisoformat(row[7])
                        
                        self.saved_searches.append(saved_search)
                        
                    except Exception as e:
                        print(f"Error loading saved search: {e}")
                
                self.update_saved_searches_combo()
                
        except Exception as e:
            print(f"Error loading saved searches: {e}")
    
    def persist_saved_searches(self):
        """Persist saved searches to database"""
        try:
            import json
            
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Clear existing searches
                cursor.execute('DELETE FROM saved_searches')
                
                # Insert current searches
                for search in self.saved_searches:
                    filters_data = []
                    for filter_obj in search.filters:
                        filters_data.append({
                            'field': filter_obj.field,
                            'operator': filter_obj.operator,
                            'value': filter_obj.value,
                            'label': filter_obj.label
                        })
                    
                    cursor.execute('''
                        INSERT INTO saved_searches 
                        (name, query, filters, sort_field, sort_order, created_at, last_used)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        search.name,
                        search.query,
                        json.dumps(filters_data),
                        search.sort_field,
                        search.sort_order,
                        search.created_at.isoformat(),
                        search.last_used.isoformat() if search.last_used else None
                    ))
                
        except Exception as e:
            print(f"Error persisting saved searches: {e}")

class AddFilterDialog:
    """Dialog for adding custom filters"""
    
    def __init__(self, parent, callback):
        self.parent = parent
        self.callback = callback
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Ajouter un Filtre")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI"""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Field selection
        ttk.Label(main_frame, text="Champ:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.field_var = tk.StringVar()
        field_combo = ttk.Combobox(main_frame, textvariable=self.field_var, state="readonly")
        field_combo['values'] = [
            'c.cheque_number', 'c.amount', 'c.status', 'c.due_date', 'c.created_at',
            'cl.name', 'cl.type', 'b.name', 'bk.name'
        ]
        field_combo.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        
        # Operator selection
        ttk.Label(main_frame, text="Opérateur:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.operator_var = tk.StringVar()
        operator_combo = ttk.Combobox(main_frame, textvariable=self.operator_var, state="readonly")
        operator_combo['values'] = ['equals', 'contains', 'greater', 'less', 'between']
        operator_combo.grid(row=1, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        
        # Value input
        ttk.Label(main_frame, text="Valeur:").grid(row=2, column=0, sticky=tk.W, pady=5)
        
        self.value_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.value_var).grid(row=2, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Ajouter", command=self.add_filter).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Annuler", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
    
    def add_filter(self):
        """Add the configured filter"""
        field = self.field_var.get()
        operator = self.operator_var.get()
        value = self.value_var.get()
        
        if not all([field, operator, value]):
            tk.messagebox.showwarning("Attention", "Veuillez remplir tous les champs")
            return
        
        # Create filter
        filter_obj = DynamicFilter(
            field=field,
            operator=operator,
            value=value,
            label=f"{field} {operator} {value}"
        )
        
        # Callback
        self.callback(filter_obj)
        
        # Close dialog
        self.dialog.destroy()

class SaveSearchDialog:
    """Dialog for saving search configurations"""
    
    def __init__(self, parent, query: str, filters: List[DynamicFilter], callback):
        self.parent = parent
        self.query = query
        self.filters = filters
        self.callback = callback
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Sauvegarder la Recherche")
        self.dialog.geometry("350x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI"""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Name input
        ttk.Label(main_frame, text="Nom de la recherche:").pack(anchor=tk.W, pady=5)
        
        self.name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.name_var, width=40).pack(fill=tk.X, pady=5)
        
        # Summary
        ttk.Label(main_frame, text="Résumé:").pack(anchor=tk.W, pady=(15, 5))
        
        summary_text = f"Requête: '{self.query}'\n"
        summary_text += f"Filtres: {len(self.filters)} actif(s)"
        
        summary_label = ttk.Label(main_frame, text=summary_text, 
                                 background="#f5f5f5", padding=10)
        summary_label.pack(fill=tk.X, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Sauvegarder", 
                  command=self.save_search).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Annuler", 
                  command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def save_search(self):
        """Save the search configuration"""
        name = self.name_var.get().strip()
        
        if not name:
            tk.messagebox.showwarning("Attention", "Veuillez saisir un nom")
            return
        
        # Create saved search
        saved_search = SavedSearch(
            name=name,
            query=self.query,
            filters=self.filters
        )
        
        # Callback
        self.callback(saved_search)
        
        # Close dialog
        self.dialog.destroy()