"""Ultra-modern GUI with cutting-edge design and animations"""
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import sys
import tempfile
from pathlib import Path
import threading
import time

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.config import Config
from src.core.service_manager import ServiceManager
from src.gui_components.themes import theme_manager
from src.gui_components.dashboard import Dashboard
from src.gui_components.ultra_modern_widgets import (
    GlassmorphicCard, NeumorphicButton, AnimatedProgressBar,
    FloatingActionButton, ModernSwitch, AnimatedSidebar,
    PulsingBadge, ModernTooltip, WaveLoader, GradientFrame
)
from src.gui_components.custom_widgets import (
    AnimatedButton, GlowingEntry, ToggleSwitch, 
    NotificationToast, SearchBar
)
from src.gui_components.system_tray import SystemTray
from src.utils.logger import get_logger

# Set CustomTkinter appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class UltraModernAssistant(ctk.CTk):
    """Ultra-modern question assistant with cutting-edge UI"""
    
    def __init__(self):
        super().__init__()
        
        self.title("Question Assistant Pro 2024")
        self.geometry("1400x800")
        self.minsize(1200, 700)
        
        # Set window transparency for modern look
        self.attributes("-alpha", 0.98)
        
        # Initialize components
        self.config = Config()
        self.service_manager = None
        self.logger = get_logger("GUI")
        self.system_tray = None
        
        # Theme
        self.current_theme = "dark"
        theme = theme_manager.get_theme(self.current_theme)
        self.configure(fg_color=theme["bg"])
        
        # Create modern UI
        self._create_modern_ui()
        
        # Setup keyboard shortcuts
        self._setup_shortcuts()
        
        # Center window with fade-in animation
        self._center_window()
        self._fade_in_animation()
        
        # Protocol handlers
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Start system tray
        self._init_system_tray()
        
        # Start background animations
        self._start_background_animations()
    
    def _create_modern_ui(self):
        """Create ultra-modern UI layout"""
        theme = theme_manager.get_theme()
        
        # Main container with gradient background
        self.main_container = GradientFrame(
            self,
            colors=["#1a1a2e", "#0f0f1e"]
        )
        self.main_container.pack(fill="both", expand=True)
        
        # Create animated sidebar
        self._create_animated_sidebar()
        
        # Create main content area with glassmorphism
        self.content_area = ctk.CTkFrame(
            self.main_container,
            fg_color="transparent"
        )
        self.content_area.pack(side="right", fill="both", expand=True)
        
        # Create modern header
        self._create_modern_header()
        
        # Create content with cards
        self._create_content_area()
        
        # Add floating action button
        self._create_floating_button()
        
        # Create status bar
        self._create_status_bar()
    
    def _create_animated_sidebar(self):
        """Create animated collapsible sidebar"""
        theme = theme_manager.get_theme()
        
        # Use animated sidebar widget
        self.sidebar = AnimatedSidebar(
            self.main_container,
            width=280
        )
        self.sidebar.pack(side="left", fill="y", padx=(10, 0), pady=10)
        
        # Logo section with animation
        logo_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_container.pack(pady=(60, 30))
        
        # Animated logo
        self.logo_label = ctk.CTkLabel(
            logo_container,
            text="🚀",
            font=("Segoe UI", 48)
        )
        self.logo_label.pack()
        self._animate_logo()
        
        # App title with gradient text effect
        self.title_label = ctk.CTkLabel(
            logo_container,
            text="Question Assistant",
            font=("Segoe UI Bold", 20),
            text_color=theme["accent"]
        )
        self.title_label.pack(pady=(10, 0))
        
        # Version badge with pulse
        self.version_badge = PulsingBadge(
            logo_container,
            text="3.0",
            size=30
        )
        self.version_badge.pack(pady=5)
        self.version_badge.start_pulsing()
        
        # Navigation items with hover effects
        self._create_nav_items()
    
    def _create_nav_items(self):
        """Create navigation items with modern styling"""
        theme = theme_manager.get_theme()
        
        nav_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_container.pack(fill="both", expand=True, padx=20)
        
        # Navigation items with icons
        nav_items = [
            ("🏠", "Dashboard", "dashboard"),
            ("⚙️", "Configuration", "config"),
            ("📊", "Analytics", "analytics"),
            ("🔬", "Advanced", "advanced"),
            ("📝", "Logs", "logs"),
            ("ℹ️", "About", "about")
        ]
        
        self.nav_buttons = {}
        
        for icon, text, page_id in nav_items:
            btn_frame = ctk.CTkFrame(nav_container, fg_color="transparent")
            btn_frame.pack(fill="x", pady=3)
            
            btn = NeumorphicButton(
                btn_frame,
                text=f"{icon}  {text}",
                command=lambda p=page_id: self._show_page(p),
                anchor="w",
                width=240,
                height=45
            )
            btn.pack(fill="x")
            
            # Add tooltip
            ModernTooltip(btn, f"Navigate to {text}")
            
            self.nav_buttons[page_id] = btn
        
        # Theme toggle at bottom
        theme_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        theme_container.pack(side="bottom", pady=20, padx=20)
        
        theme_label = ctk.CTkLabel(
            theme_container,
            text="🌓 Dark Mode",
            font=theme_manager.get_font("small")
        )
        theme_label.pack(side="left")
        
        self.theme_switch = ModernSwitch(
            theme_container,
            text="",
            command=self._toggle_theme
        )
        self.theme_switch.pack(side="right", padx=10)
        self.theme_switch.select()
    
    def _create_modern_header(self):
        """Create modern header with search and controls"""
        theme = theme_manager.get_theme()
        
        # Header with glass effect
        self.header = GlassmorphicCard(self.content_area)
        self.header.pack(fill="x", padx=20, pady=(20, 10))
        
        # Search section
        search_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        search_frame.pack(side="left", padx=20, pady=15)
        
        self.search_bar = SearchBar(
            search_frame,
            placeholder="🔍 Search anything...",
            command=self._handle_search,
            width=400
        )
        self.search_bar.pack()
        
        # Control buttons with modern styling
        controls_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        controls_frame.pack(side="right", padx=20)
        
        # Start button with animation
        self.start_btn = NeumorphicButton(
            controls_frame,
            text="▶️ Start",
            command=self._start_service,
            width=100
        )
        self.start_btn.pack(side="left", padx=5)
        
        # Stop button
        self.stop_btn = NeumorphicButton(
            controls_frame,
            text="⏹️ Stop",
            command=self._stop_service,
            width=100
        )
        self.stop_btn.pack(side="left", padx=5)
        self.stop_btn.configure(state="disabled")
        
        # Settings button
        settings_btn = FloatingActionButton(
            controls_frame,
            icon="⚙️",
            command=lambda: self._show_page("config"),
            size=40
        )
        settings_btn.pack(side="left", padx=10)
    
    def _create_content_area(self):
        """Create main content area with pages"""
        # Scrollable content
        self.content_frame = ctk.CTkScrollableFrame(
            self.content_area,
            fg_color="transparent"
        )
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Create pages
        self.pages = {}
        self._create_pages()
        
        # Show dashboard by default
        self._show_page("dashboard")
    
    def _create_pages(self):
        """Create content pages with modern design"""
        # Dashboard page with cards
        self.pages["dashboard"] = self._create_dashboard_page()
        
        # Configuration page
        self.pages["config"] = self._create_config_page()
        
        # Analytics page
        self.pages["analytics"] = self._create_analytics_page()
        
        # Advanced settings
        self.pages["advanced"] = self._create_advanced_page()
        
        # Logs page
        self.pages["logs"] = self._create_logs_page()
        
        # About page
        self.pages["about"] = self._create_about_page()
    
    def _create_dashboard_page(self):
        """Create modern dashboard with cards"""
        page = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        
        # Title with animation
        title = ctk.CTkLabel(
            page,
            text="Dashboard",
            font=("Segoe UI Bold", 32),
            text_color=theme_manager.get_theme()["fg"]
        )
        title.pack(anchor="w", pady=(0, 20))
        
        # Stats cards grid
        stats_grid = ctk.CTkFrame(page, fg_color="transparent")
        stats_grid.pack(fill="x", pady=10)
        
        # Create stat cards
        self._create_stat_card(stats_grid, "🎯", "Questions Detected", "0", 0, 0)
        self._create_stat_card(stats_grid, "✅", "Answered", "0", 0, 1)
        self._create_stat_card(stats_grid, "⚡", "Success Rate", "0%", 1, 0)
        self._create_stat_card(stats_grid, "⏱️", "Avg Response", "0ms", 1, 1)
        
        # Activity graph card
        graph_card = GlassmorphicCard(page)
        graph_card.pack(fill="x", pady=20)
        
        graph_title = ctk.CTkLabel(
            graph_card,
            text="📈 Activity Monitor",
            font=("Segoe UI Bold", 18)
        )
        graph_title.pack(anchor="w", padx=20, pady=(15, 10))
        
        # Animated progress bars
        self.activity_progress = AnimatedProgressBar(graph_card)
        self.activity_progress.pack(padx=20, pady=10)
        
        # Wave loader for processing indication
        self.processing_indicator = WaveLoader(graph_card)
        self.processing_indicator.pack(pady=10)
        
        return page
    
    def _create_stat_card(self, parent, icon, title, value, row, col):
        """Create a statistics card"""
        card = GlassmorphicCard(parent)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="ew")
        
        # Configure grid weight
        parent.grid_columnconfigure(col, weight=1)
        
        # Icon
        icon_label = ctk.CTkLabel(
            card,
            text=icon,
            font=("Segoe UI", 32)
        )
        icon_label.pack(pady=(15, 5))
        
        # Value
        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=("Segoe UI Bold", 24),
            text_color=theme_manager.get_theme()["accent"]
        )
        value_label.pack()
        
        # Title
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=("Segoe UI", 12),
            text_color=theme_manager.get_theme()["fg_secondary"]
        )
        title_label.pack(pady=(5, 15))
        
        return card
    
    def _create_config_page(self):
        """Create configuration page with modern inputs"""
        theme = theme_manager.get_theme()
        page = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        
        title = ctk.CTkLabel(
            page,
            text="Configuration",
            font=("Segoe UI Bold", 32),
            text_color=theme["fg"]
        )
        title.pack(anchor="w", pady=(0, 20))
        
        # Main settings card
        settings_card = GlassmorphicCard(page)
        settings_card.pack(fill="x", pady=10)
        
        # Context input with modern styling
        context_label = ctk.CTkLabel(
            settings_card,
            text="📝 Question Context",
            font=("Segoe UI Bold", 14),
            text_color=theme["fg"]
        )
        context_label.pack(anchor="w", padx=20, pady=(15, 5))
        
        self.context_entry = ctk.CTkTextbox(
            settings_card,
            height=100,
            fg_color=theme["bg_tertiary"],
            text_color=theme["fg"],
            font=theme_manager.get_font("body"),
            corner_radius=10
        )
        self.context_entry.pack(fill="x", padx=20, pady=(0, 15))
        
        # Duration slider with value display
        duration_frame = ctk.CTkFrame(settings_card, fg_color="transparent")
        duration_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            duration_frame,
            text="⏰ Session Duration",
            font=("Segoe UI Bold", 14),
            text_color=theme["fg"]
        ).pack(side="left")
        
        self.duration_value = ctk.CTkLabel(
            duration_frame,
            text="60 min",
            font=("Segoe UI", 14),
            text_color=theme["accent"]
        )
        self.duration_value.pack(side="right")
        
        self.duration_slider = ctk.CTkSlider(
            settings_card,
            from_=5,
            to=180,
            number_of_steps=35,
            command=self._update_duration,
            progress_color=theme["accent"],
            button_color=theme["accent"],
            button_hover_color=theme["success"]
        )
        self.duration_slider.pack(fill="x", padx=20, pady=(0, 20))
        self.duration_slider.set(60)
        
        # API settings with secure input
        api_card = GlassmorphicCard(page)
        api_card.pack(fill="x", pady=10)
        
        api_label = ctk.CTkLabel(
            api_card,
            text="🔐 API Configuration",
            font=("Segoe UI Bold", 14),
            text_color=theme["fg"]
        )
        api_label.pack(anchor="w", padx=20, pady=(15, 10))
        
        self.api_key_entry = GlowingEntry(
            api_card,
            placeholder_text="Enter API Key (optional)",
            show="•"
        )
        self.api_key_entry.pack(fill="x", padx=20, pady=(0, 15))
        
        return page
    
    def _create_analytics_page(self):
        """Create analytics page with charts"""
        theme = theme_manager.get_theme()
        page = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        
        title = ctk.CTkLabel(
            page,
            text="Analytics",
            font=("Segoe UI Bold", 32),
            text_color=theme["fg"]
        )
        title.pack(anchor="w", pady=(0, 20))
        
        # Performance metrics
        metrics_card = GlassmorphicCard(page)
        metrics_card.pack(fill="x", pady=10)
        
        metrics_title = ctk.CTkLabel(
            metrics_card,
            text="📊 Performance Metrics",
            font=("Segoe UI Bold", 18)
        )
        metrics_title.pack(anchor="w", padx=20, pady=15)
        
        # Add animated progress bars for different metrics
        metrics = [
            ("CPU Usage", 25, theme["success"]),
            ("Memory Usage", 45, theme["warning"]),
            ("Network Activity", 10, theme["accent"]),
            ("Detection Accuracy", 85, theme["success"])
        ]
        
        for metric_name, value, color in metrics:
            metric_frame = ctk.CTkFrame(metrics_card, fg_color="transparent")
            metric_frame.pack(fill="x", padx=20, pady=5)
            
            ctk.CTkLabel(
                metric_frame,
                text=metric_name,
                font=("Segoe UI", 12)
            ).pack(side="left")
            
            ctk.CTkLabel(
                metric_frame,
                text=f"{value}%",
                font=("Segoe UI Bold", 12),
                text_color=color
            ).pack(side="right")
            
            progress = AnimatedProgressBar(
                metrics_card,
                height=6,
                width=400
            )
            progress.pack(padx=20, pady=(0, 10))
            progress.set_progress(value)
        
        return page
    
    def _create_advanced_page(self):
        """Create advanced settings page"""
        theme = theme_manager.get_theme()
        page = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        
        title = ctk.CTkLabel(
            page,
            text="Advanced Settings",
            font=("Segoe UI Bold", 32),
            text_color=theme["fg"]
        )
        title.pack(anchor="w", pady=(0, 20))
        
        # Feature toggles
        features_card = GlassmorphicCard(page)
        features_card.pack(fill="x", pady=10)
        
        features_title = ctk.CTkLabel(
            features_card,
            text="🔧 Feature Toggles",
            font=("Segoe UI Bold", 18)
        )
        features_title.pack(anchor="w", padx=20, pady=15)
        
        features = [
            ("🚀 Hardware Acceleration", True),
            ("🧠 AI Enhancement", True),
            ("🔄 Auto-retry Failed Detections", False),
            ("📸 Screenshot Optimization", True),
            ("🎯 Smart Targeting", True),
            ("💾 Local Caching", False)
        ]
        
        for feature_name, default in features:
            feature_frame = ctk.CTkFrame(features_card, fg_color="transparent")
            feature_frame.pack(fill="x", padx=20, pady=8)
            
            ctk.CTkLabel(
                feature_frame,
                text=feature_name,
                font=("Segoe UI", 14)
            ).pack(side="left")
            
            switch = ModernSwitch(
                feature_frame,
                text="",
                command=lambda: None
            )
            switch.pack(side="right", padx=10)
            if default:
                switch.select()
        
        return page
    
    def _create_logs_page(self):
        """Create logs page"""
        theme = theme_manager.get_theme()
        page = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        
        # Header with controls
        header_frame = ctk.CTkFrame(page, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        title = ctk.CTkLabel(
            header_frame,
            text="Logs",
            font=("Segoe UI Bold", 32),
            text_color=theme["fg"]
        )
        title.pack(side="left")
        
        # Log controls
        controls = ctk.CTkFrame(header_frame, fg_color="transparent")
        controls.pack(side="right")
        
        clear_btn = NeumorphicButton(
            controls,
            text="🗑️ Clear",
            width=80
        )
        clear_btn.pack(side="left", padx=5)
        
        export_btn = NeumorphicButton(
            controls,
            text="📤 Export",
            width=80
        )
        export_btn.pack(side="left", padx=5)
        
        # Log viewer
        log_card = GlassmorphicCard(page)
        log_card.pack(fill="both", expand=True)
        
        self.log_viewer = ctk.CTkTextbox(
            log_card,
            fg_color=theme["bg_tertiary"],
            text_color=theme["fg"],
            font=("Consolas", 11),
            corner_radius=10
        )
        self.log_viewer.pack(fill="both", expand=True, padx=20, pady=20)
        
        return page
    
    def _create_about_page(self):
        """Create about page"""
        theme = theme_manager.get_theme()
        page = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        
        # Center content
        about_card = GlassmorphicCard(page)
        about_card.pack(expand=True, pady=50)
        
        # Logo with animation
        logo = ctk.CTkLabel(
            about_card,
            text="🚀",
            font=("Segoe UI", 72)
        )
        logo.pack(pady=20)
        
        # Title
        title = ctk.CTkLabel(
            about_card,
            text="Question Assistant Pro",
            font=("Segoe UI Bold", 28),
            text_color=theme["accent"]
        )
        title.pack()
        
        # Version
        version = ctk.CTkLabel(
            about_card,
            text="Version 3.0.0",
            font=("Segoe UI", 14),
            text_color=theme["fg_secondary"]
        )
        version.pack(pady=5)
        
        # Description
        desc = ctk.CTkLabel(
            about_card,
            text="Next-generation automated assistant\nwith AI-powered intelligence",
            font=("Segoe UI", 12),
            text_color=theme["fg_secondary"],
            justify="center"
        )
        desc.pack(pady=20)
        
        # Links
        links_frame = ctk.CTkFrame(about_card, fg_color="transparent")
        links_frame.pack(pady=20)
        
        github_btn = NeumorphicButton(
            links_frame,
            text="📚 Documentation",
            width=140
        )
        github_btn.pack(side="left", padx=5)
        
        support_btn = NeumorphicButton(
            links_frame,
            text="💬 Support",
            width=140
        )
        support_btn.pack(side="left", padx=5)
        
        # Copyright
        copyright_label = ctk.CTkLabel(
            about_card,
            text="© 2024 Question Assistant. All rights reserved.",
            font=("Segoe UI", 10),
            text_color=theme["fg_secondary"]
        )
        copyright_label.pack(pady=(20, 30))
        
        return page
    
    def _create_floating_button(self):
        """Create floating action button"""
        self.fab = FloatingActionButton(
            self.content_area,
            icon="💬",
            command=self._show_quick_actions,
            size=60
        )
        self.fab.place(relx=0.95, rely=0.92, anchor="center")
    
    def _create_status_bar(self):
        """Create modern status bar"""
        theme = theme_manager.get_theme()
        
        self.status_bar = ctk.CTkFrame(
            self,
            height=30,
            fg_color=theme["bg_secondary"]
        )
        self.status_bar.pack(side="bottom", fill="x")
        
        # Status text
        self.status_text = ctk.CTkLabel(
            self.status_bar,
            text="🟢 Ready",
            font=("Segoe UI", 11)
        )
        self.status_text.pack(side="left", padx=10)
        
        # Connection indicator
        self.connection_indicator = ctk.CTkLabel(
            self.status_bar,
            text="🌐 Connected",
            font=("Segoe UI", 11),
            text_color=theme["success"]
        )
        self.connection_indicator.pack(side="right", padx=10)
    
    def _show_page(self, page_id):
        """Show specific page with animation"""
        # Hide all pages
        for page in self.pages.values():
            page.pack_forget()
        
        # Show selected page with fade animation
        if page_id in self.pages:
            self.pages[page_id].pack(fill="both", expand=True)
            self._fade_in_page(self.pages[page_id])
        
        # Update nav button states
        theme = theme_manager.get_theme()
        for btn_id, btn in self.nav_buttons.items():
            if btn_id == page_id:
                btn.configure(fg_color=theme["accent"])
            else:
                btn.configure(fg_color=theme["bg_secondary"])
    
    def _fade_in_page(self, page):
        """Fade in animation for page"""
        # This would require actual opacity control
        # For now, just a placeholder
        pass
    
    def _animate_logo(self):
        """Animate logo rotation"""
        # Simple rotation animation
        current = self.logo_label.cget("text")
        if current == "🚀":
            self.logo_label.configure(text="✨")
        else:
            self.logo_label.configure(text="🚀")
        
        self.after(2000, self._animate_logo)
    
    def _fade_in_animation(self):
        """Fade in window on start"""
        alpha = 0.0
        while alpha < 0.98:
            alpha += 0.02
            self.attributes("-alpha", alpha)
            self.update()
            time.sleep(0.01)
    
    def _toggle_theme(self):
        """Toggle theme with animation"""
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        NotificationToast(self, f"Switched to {self.current_theme} theme", "info")
    
    def _update_duration(self, value):
        """Update duration display"""
        self.duration_value.configure(text=f"{int(value)} min")
    
    def _handle_search(self, query):
        """Handle search with animation"""
        if query:
            self.processing_indicator.start()
            self.after(2000, self.processing_indicator.stop)
            NotificationToast(self, f"Searching: {query}", "info")
    
    def _show_quick_actions(self):
        """Show quick actions menu"""
        NotificationToast(self, "Quick actions menu", "info")
    
    def _start_service(self):
        """Start service with animation"""
        try:
            # Show processing
            self.processing_indicator.start()
            self.status_text.configure(text="🔄 Starting...")
            
            # Update config
            self.config.set('context', self.context_entry.get("1.0", "end").strip())
            self.config.set('duration_minutes', int(self.duration_slider.get()))
            self.config.set('api_key', self.api_key_entry.get())
            
            # Start service
            self.service_manager = ServiceManager()
            self.service_manager.config = self.config
            self.service_manager.start()
            
            # Update UI
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            self.status_text.configure(text="🟢 Running")
            
            # Animate progress
            self.activity_progress.set_progress(75)
            
            NotificationToast(self, "Service started successfully", "success")
            
        except Exception as e:
            self.status_text.configure(text="🔴 Error")
            NotificationToast(self, f"Failed to start: {str(e)}", "error")
        finally:
            self.processing_indicator.stop()
    
    def _stop_service(self):
        """Stop service"""
        if self.service_manager:
            self.service_manager.stop()
            self.service_manager = None
            
            # Update UI
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            self.status_text.configure(text="🟢 Ready")
            self.activity_progress.set_progress(0)
            
            NotificationToast(self, "Service stopped", "info")
    
    def _start_background_animations(self):
        """Start background animations"""
        # Animate progress bars periodically
        def animate():
            if self.service_manager and self.service_manager.running:
                import random
                self.activity_progress.set_progress(random.randint(60, 90))
            self.after(3000, animate)
        
        animate()
    
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        self.bind("<Control-q>", lambda e: self.quit())
        self.bind("<Control-s>", lambda e: self._start_service())
        self.bind("<Control-x>", lambda e: self._stop_service())
        self.bind("<F1>", lambda e: self._show_page("about"))
    
    def _center_window(self):
        """Center window on screen"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def _init_system_tray(self):
        """Initialize system tray"""
        try:
            from src.gui_components.system_tray import SystemTray
            self.system_tray = SystemTray(self)
            self.system_tray.start()
        except Exception as e:
            self.logger.warning(f"Could not initialize system tray: {e}")
    
    def _on_closing(self):
        """Handle window closing"""
        if self.service_manager and self.service_manager.running:
            result = messagebox.askyesnocancel(
                "Service Running",
                "Service is running. Do you want to:\n\n"
                "Yes - Minimize to system tray\n"
                "No - Stop service and exit\n"
                "Cancel - Keep window open"
            )
            
            if result is True:
                self.withdraw()
                if self.system_tray:
                    self.system_tray.show_notification(
                        "Question Assistant",
                        "Minimized to system tray"
                    )
            elif result is False:
                self._stop_service()
                if self.system_tray:
                    self.system_tray.stop()
                self.quit()
        else:
            if self.system_tray:
                self.system_tray.stop()
            self.quit()


def main():
    """Main entry point"""
    app = UltraModernAssistant()
    app.mainloop()


if __name__ == "__main__":
    main()