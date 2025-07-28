#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mobile-responsive UI components with adaptive layouts
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Callable, Optional

class ResponsiveFrame(ttk.Frame):
    """Base responsive frame that adapts to window size"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.breakpoints = {
            'mobile': 768,
            'tablet': 1024,
            'desktop': 1200
        }
        self.current_layout = 'desktop'
        
        # Bind to window resize events
        self.bind('<Configure>', self.on_resize)
        
    def on_resize(self, event=None):
        """Handle window resize events"""
        if event and event.widget == self:
            width = self.winfo_width()
            new_layout = self.get_layout_for_width(width)
            
            if new_layout != self.current_layout:
                self.current_layout = new_layout
                self.adapt_layout()
    
    def get_layout_for_width(self, width: int) -> str:
        """Determine layout based on width"""
        if width <= self.breakpoints['mobile']:
            return 'mobile'
        elif width <= self.breakpoints['tablet']:
            return 'tablet'
        else:
            return 'desktop'
    
    def adapt_layout(self):
        """Override in subclasses to implement responsive behavior"""
        pass

class ResponsiveGrid(ResponsiveFrame):
    """Responsive grid that adjusts columns based on screen size"""
    
    def __init__(self, parent, items: List[tk.Widget], **kwargs):
        super().__init__(parent, **kwargs)
        self.items = items
        self.columns_config = {
            'mobile': 1,
            'tablet': 2,
            'desktop': 4
        }
        self.setup_grid()
    
    def setup_grid(self):
        """Setup initial grid"""
        self.adapt_layout()
    
    def adapt_layout(self):
        """Adapt grid layout based on current screen size"""
        columns = self.columns_config[self.current_layout]
        
        # Clear current grid
        for item in self.items:
            item.grid_forget()
        
        # Rearrange items
        for i, item in enumerate(self.items):
            row = i // columns
            col = i % columns
            item.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
        
        # Configure column weights
        for col in range(columns):
            self.columnconfigure(col, weight=1)

class AdaptiveNotebook(ttk.Notebook):
    """Notebook that can switch between tabs and accordion on mobile"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.is_mobile = False
        self.accordion_frames = []
        
        # Monitor window size
        self.bind('<Configure>', self.check_mobile_layout)
    
    def check_mobile_layout(self, event=None):
        """Check if we should switch to mobile layout"""
        if event and event.widget == self.parent:
            width = self.parent.winfo_width()
            should_be_mobile = width <= 768
            
            if should_be_mobile != self.is_mobile:
                self.is_mobile = should_be_mobile
                self.switch_layout()
    
    def switch_layout(self):
        """Switch between tab and accordion layout"""
        if self.is_mobile:
            self.convert_to_accordion()
        else:
            self.convert_to_tabs()
    
    def convert_to_accordion(self):
        """Convert tabs to accordion layout"""
        # Implementation for accordion layout
        pass
    
    def convert_to_tabs(self):
        """Convert accordion back to tabs"""
        # Implementation for tab layout
        pass

class TouchFriendlyButton(ttk.Button):
    """Button optimized for touch interfaces"""
    
    def __init__(self, parent, **kwargs):
        # Ensure minimum touch target size (44px)
        if 'width' not in kwargs:
            kwargs['width'] = 10
        
        super().__init__(parent, **kwargs)
        
        # Add touch-friendly styling
        self.configure(padding=(10, 8))

class SwipeableFrame(ttk.Frame):
    """Frame that supports swipe gestures"""
    
    def __init__(self, parent, on_swipe_left: Callable = None, 
                 on_swipe_right: Callable = None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.on_swipe_left = on_swipe_left
        self.on_swipe_right = on_swipe_right
        self.start_x = 0
        self.start_y = 0
        
        # Bind touch/mouse events
        self.bind('<Button-1>', self.on_touch_start)
        self.bind('<B1-Motion>', self.on_touch_move)
        self.bind('<ButtonRelease-1>', self.on_touch_end)
    
    def on_touch_start(self, event):
        """Handle touch/click start"""
        self.start_x = event.x
        self.start_y = event.y
    
    def on_touch_move(self, event):
        """Handle touch/drag movement"""
        pass
    
    def on_touch_end(self, event):
        """Handle touch/click end and detect swipe"""
        dx = event.x - self.start_x
        dy = event.y - self.start_y
        
        # Detect horizontal swipe (minimum 50px movement)
        if abs(dx) > 50 and abs(dx) > abs(dy):
            if dx > 0 and self.on_swipe_right:
                self.on_swipe_right()
            elif dx < 0 and self.on_swipe_left:
                self.on_swipe_left()

class MobileOptimizedList(ttk.Frame):
    """List optimized for mobile with large touch targets"""
    
    def __init__(self, parent, items: List[Dict], item_height: int = 60, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.items = items
        self.item_height = item_height
        self.selected_item = None
        
        # Create scrollable canvas
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack components
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Create list items
        self.create_items()
        
        # Bind mouse wheel
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
    
    def create_items(self):
        """Create list items"""
        for i, item in enumerate(self.items):
            item_frame = self.create_list_item(item, i)
            item_frame.pack(fill="x", padx=5, pady=2)
    
    def create_list_item(self, item: Dict, index: int) -> ttk.Frame:
        """Create a single list item"""
        item_frame = ttk.Frame(self.scrollable_frame, height=self.item_height)
        item_frame.pack_propagate(False)
        
        # Main content
        content_frame = ttk.Frame(item_frame)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Title
        title_label = ttk.Label(content_frame, text=item.get('title', ''), 
                               font=('Arial', 12, 'bold'))
        title_label.pack(anchor="w")
        
        # Subtitle
        if 'subtitle' in item:
            subtitle_label = ttk.Label(content_frame, text=item['subtitle'], 
                                     font=('Arial', 10))
            subtitle_label.pack(anchor="w")
        
        # Action button
        if 'action' in item:
            action_btn = TouchFriendlyButton(content_frame, text=item['action']['text'],
                                           command=lambda: item['action']['callback'](item))
            action_btn.pack(side="right", anchor="e")
        
        # Make item clickable
        def on_item_click(event, item_data=item, idx=index):
            self.on_item_selected(item_data, idx)
        
        item_frame.bind("<Button-1>", on_item_click)
        for child in item_frame.winfo_children():
            child.bind("<Button-1>", on_item_click)
        
        return item_frame
    
    def on_item_selected(self, item: Dict, index: int):
        """Handle item selection"""
        self.selected_item = item
        # Highlight selected item (implementation depends on styling needs)
    
    def on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

class MobileDashboard(ResponsiveFrame):
    """Mobile-optimized dashboard"""
    
    def __init__(self, parent, db_manager, current_user, **kwargs):
        super().__init__(parent, **kwargs)
        self.db = db_manager
        self.current_user = current_user
        
        self.setup_mobile_dashboard()
    
    def setup_mobile_dashboard(self):
        """Setup mobile dashboard layout"""
        # Header
        self.create_mobile_header()
        
        # Quick stats cards
        self.create_quick_stats()
        
        # Recent activity
        self.create_recent_activity()
        
        # Quick actions
        self.create_quick_actions()
    
    def create_mobile_header(self):
        """Create mobile header"""
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(header_frame, text="💳 Chèques", 
                               font=('Arial', 18, 'bold'))
        title_label.pack(side="left")
        
        # User info
        user_label = ttk.Label(header_frame, 
                              text=f"👤 {self.current_user['username']}")
        user_label.pack(side="right")
    
    def create_quick_stats(self):
        """Create quick stats cards"""
        stats_frame = ttk.LabelFrame(self, text="📊 Aperçu", padding=10)
        stats_frame.pack(fill="x", padx=10, pady=5)
        
        # Get basic stats
        try:
            stats = self.db.get_dashboard_stats()
            
            # Create stat cards
            stat_items = [
                {"title": "Total", "value": str(stats['total_cheques']), "icon": "📊"},
                {"title": "Montant", "value": f"{stats['total_amount']:,.0f} MAD", "icon": "💰"},
                {"title": "En Attente", "value": str(stats['by_status'].get('en_attente', {}).get('count', 0)), "icon": "⏳"},
                {"title": "En Retard", "value": str(stats['overdue_count']), "icon": "⚠️"}
            ]
            
            # Responsive grid for stats
            stats_grid = ResponsiveGrid(stats_frame, [])
            stats_grid.pack(fill="x")
            
            for stat in stat_items:
                stat_card = self.create_stat_card(stats_grid, stat)
                stats_grid.items.append(stat_card)
            
            stats_grid.setup_grid()
            
        except Exception as e:
            error_label = ttk.Label(stats_frame, text=f"Erreur: {e}")
            error_label.pack()
    
    def create_stat_card(self, parent, stat: Dict) -> ttk.Frame:
        """Create a single stat card"""
        card_frame = ttk.Frame(parent, relief="raised", borderwidth=1)
        card_frame.configure(padding=10)
        
        # Icon
        icon_label = ttk.Label(card_frame, text=stat['icon'], 
                              font=('Arial', 20))
        icon_label.pack()
        
        # Value
        value_label = ttk.Label(card_frame, text=stat['value'], 
                               font=('Arial', 14, 'bold'))
        value_label.pack()
        
        # Title
        title_label = ttk.Label(card_frame, text=stat['title'], 
                               font=('Arial', 10))
        title_label.pack()
        
        return card_frame
    
    def create_recent_activity(self):
        """Create recent activity section"""
        activity_frame = ttk.LabelFrame(self, text="🕒 Activité Récente", padding=10)
        activity_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Get recent cheques
        try:
            recent_cheques = self.db.get_cheques()[:10]  # Last 10 cheques
            
            activity_items = []
            for cheque in recent_cheques:
                activity_items.append({
                    'title': f"Chèque #{cheque['cheque_number']}",
                    'subtitle': f"{cheque['amount']:,.2f} MAD - {cheque.get('client_name', 'N/A')}",
                    'action': {
                        'text': 'Voir',
                        'callback': lambda c=cheque: self.view_cheque(c)
                    }
                })
            
            # Create mobile-optimized list
            activity_list = MobileOptimizedList(activity_frame, activity_items)
            activity_list.pack(fill="both", expand=True)
            
        except Exception as e:
            error_label = ttk.Label(activity_frame, text=f"Erreur: {e}")
            error_label.pack()
    
    def create_quick_actions(self):
        """Create quick actions section"""
        actions_frame = ttk.LabelFrame(self, text="⚡ Actions Rapides", padding=10)
        actions_frame.pack(fill="x", padx=10, pady=5)
        
        # Action buttons
        actions = [
            {"text": "➕ Nouveau Chèque", "command": self.new_cheque},
            {"text": "🔍 Rechercher", "command": self.search_cheques},
            {"text": "📊 Rapports", "command": self.view_reports},
            {"text": "⚙️ Paramètres", "command": self.open_settings}
        ]
        
        # Create responsive grid for actions
        actions_grid = ResponsiveGrid(actions_frame, [])
        actions_grid.pack(fill="x")
        
        for action in actions:
            action_btn = TouchFriendlyButton(actions_grid, **action)
            actions_grid.items.append(action_btn)
        
        actions_grid.columns_config = {
            'mobile': 2,
            'tablet': 2,
            'desktop': 4
        }
        actions_grid.setup_grid()
    
    def adapt_layout(self):
        """Adapt layout based on screen size"""
        if self.current_layout == 'mobile':
            # Mobile-specific adaptations
            self.configure(padding=5)
        elif self.current_layout == 'tablet':
            # Tablet-specific adaptations
            self.configure(padding=10)
        else:
            # Desktop adaptations
            self.configure(padding=15)
    
    # Action methods
    def view_cheque(self, cheque):
        """View cheque details"""
        # Implementation for viewing cheque details
        pass
    
    def new_cheque(self):
        """Create new cheque"""
        # Implementation for new cheque
        pass
    
    def search_cheques(self):
        """Search cheques"""
        # Implementation for search
        pass
    
    def view_reports(self):
        """View reports"""
        # Implementation for reports
        pass
    
    def open_settings(self):
        """Open settings"""
        # Implementation for settings
        pass

class DarkModeManager:
    """Manager for dark mode theme switching"""
    
    def __init__(self):
        self.is_dark_mode = False
        self.themes = {
            'light': {
                'bg': '#ffffff',
                'fg': '#000000',
                'select_bg': '#0078d4',
                'select_fg': '#ffffff',
                'card_bg': '#f8f9fa',
                'border': '#dee2e6'
            },
            'dark': {
                'bg': '#1a1a1a',
                'fg': '#ffffff',
                'select_bg': '#0078d4',
                'select_fg': '#ffffff',
                'card_bg': '#2d2d2d',
                'border': '#404040'
            }
        }
    
    def toggle_dark_mode(self, root):
        """Toggle between light and dark mode"""
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme(root)
    
    def apply_theme(self, root):
        """Apply the current theme"""
        theme_name = 'dark' if self.is_dark_mode else 'light'
        theme = self.themes[theme_name]
        
        # Apply theme to ttk widgets
        style = ttk.Style()
        
        # Configure styles
        style.configure('TLabel', background=theme['bg'], foreground=theme['fg'])
        style.configure('TFrame', background=theme['bg'])
        style.configure('TLabelFrame', background=theme['bg'], foreground=theme['fg'])
        style.configure('TButton', background=theme['card_bg'], foreground=theme['fg'])
        style.configure('TEntry', fieldbackground=theme['card_bg'], foreground=theme['fg'])
        
        # Configure root window
        root.configure(bg=theme['bg'])
        
        # Update all existing widgets recursively
        self._update_widget_theme(root, theme)
    
    def _update_widget_theme(self, widget, theme):
        """Recursively update widget themes"""
        try:
            # Update widget colors if possible
            if hasattr(widget, 'configure'):
                widget_class = widget.winfo_class()
                
                if widget_class in ['Frame', 'Toplevel']:
                    widget.configure(bg=theme['bg'])
                elif widget_class == 'Label':
                    widget.configure(bg=theme['bg'], fg=theme['fg'])
                elif widget_class == 'Button':
                    widget.configure(bg=theme['card_bg'], fg=theme['fg'])
                elif widget_class in ['Entry', 'Text']:
                    widget.configure(bg=theme['card_bg'], fg=theme['fg'])
            
            # Recursively update children
            for child in widget.winfo_children():
                self._update_widget_theme(child, theme)
                
        except Exception:
            # Ignore errors for widgets that don't support certain options
            pass

class KeyboardShortcutManager:
    """Manager for keyboard shortcuts and power-user features"""
    
    def __init__(self, root):
        self.root = root
        self.shortcuts = {}
        self.setup_default_shortcuts()
    
    def setup_default_shortcuts(self):
        """Setup default keyboard shortcuts"""
        self.register_shortcut('<Control-n>', 'new_cheque', "Nouveau chèque")
        self.register_shortcut('<Control-f>', 'search', "Rechercher")
        self.register_shortcut('<Control-s>', 'save', "Sauvegarder")
        self.register_shortcut('<Control-e>', 'export', "Exporter")
        self.register_shortcut('<Control-r>', 'refresh', "Actualiser")
        self.register_shortcut('<Control-q>', 'quit', "Quitter")
        self.register_shortcut('<F1>', 'help', "Aide")
        self.register_shortcut('<F5>', 'refresh', "Actualiser")
        self.register_shortcut('<Escape>', 'cancel', "Annuler")
    
    def register_shortcut(self, key_sequence: str, action: str, description: str):
        """Register a keyboard shortcut"""
        self.shortcuts[key_sequence] = {
            'action': action,
            'description': description
        }
        self.root.bind(key_sequence, lambda e: self.execute_action(action))
    
    def execute_action(self, action: str):
        """Execute a shortcut action"""
        # This would be implemented to call the appropriate method
        # based on the current context
        print(f"Executing action: {action}")
    
    def show_shortcuts_help(self):
        """Show keyboard shortcuts help dialog"""
        help_window = tk.Toplevel(self.root)
        help_window.title("Raccourcis Clavier")
        help_window.geometry("400x500")
        
        # Create scrollable text widget
        text_frame = ttk.Frame(help_window)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(text_frame, wrap="word")
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        # Add shortcuts to text
        text_widget.insert("1.0", "RACCOURCIS CLAVIER\n\n")
        
        for key_sequence, shortcut_info in self.shortcuts.items():
            text_widget.insert("end", f"{key_sequence:<20} {shortcut_info['description']}\n")
        
        text_widget.configure(state="disabled")
        
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Close button
        ttk.Button(help_window, text="Fermer", 
                  command=help_window.destroy).pack(pady=10)