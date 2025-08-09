"""Enhanced main GUI with modern features"""
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import sys
import tempfile
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.config import Config
from src.core.service_manager import ServiceManager
from src.gui_components.themes import theme_manager
from src.gui_components.dashboard import Dashboard
from src.gui_components.custom_widgets import (
    AnimatedButton, GlowingEntry, ToggleSwitch, 
    NotificationToast, SearchBar, ModernCard
)
from src.gui_components.system_tray import SystemTray
from src.gui_components.main_window import EnhancedGUI as BaseGUI
from src.utils.logger import get_logger

# Set CustomTkinter appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ModernQuestionAssistant(ctk.CTk):
    """Modern enhanced GUI application"""
    
    def __init__(self):
        super().__init__()
        
        self.title("Question Assistant Pro")
        self.geometry("1200x700")
        self.minsize(1000, 600)
        
        # Initialize components
        self.config = Config()
        self.service_manager = None
        self.logger = get_logger("GUI")
        self.system_tray = None
        
        # Theme
        self.current_theme = "dark"
        theme = theme_manager.get_theme(self.current_theme)
        self.configure(fg_color=theme["bg"])
        
        # Create UI
        self._create_ui()
        
        # Setup keyboard shortcuts
        self._setup_shortcuts()
        
        # Center window
        self._center_window()
        
        # Protocol handlers
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Start system tray
        self._init_system_tray()
    
    def _create_ui(self):
        """Create the main UI"""
        theme = theme_manager.get_theme()
        
        # Create sidebar
        self._create_sidebar()
        
        # Create main content area
        self.main_frame = ctk.CTkFrame(self, fg_color=theme["bg"])
        self.main_frame.pack(side="right", fill="both", expand=True)
        
        # Create header
        self._create_header()
        
        # Create content pages
        self.pages = {}
        self._create_pages()
        
        # Show dashboard by default
        self._show_page("dashboard")
    
    def _create_sidebar(self):
        """Create modern sidebar navigation"""
        theme = theme_manager.get_theme()
        
        self.sidebar = ctk.CTkFrame(self, width=250, fg_color=theme["bg_secondary"])
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        # Logo/Title
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(pady=(30, 20))
        
        logo_label = ctk.CTkLabel(
            logo_frame,
            text="🎯",
            font=("Segoe UI", 32)
        )
        logo_label.pack()
        
        app_name = ctk.CTkLabel(
            logo_frame,
            text="Question Assistant",
            font=theme_manager.get_font("heading"),
            text_color=theme["fg"]
        )
        app_name.pack()
        
        version_label = ctk.CTkLabel(
            logo_frame,
            text="Version 3.0 Pro",
            font=theme_manager.get_font("body_small"),
            text_color=theme["fg_tertiary"]
        )
        version_label.pack()
        
        # Navigation buttons
        nav_items = [
            ("🏠", "Dashboard", "dashboard"),
            ("⚙️", "Configuration", "config"),
            ("📊", "Statistics", "stats"),
            ("🔧", "Advanced", "advanced"),
            ("📝", "Logs", "logs"),
            ("ℹ️", "About", "about")
        ]
        
        self.nav_buttons = {}
        for icon, text, page_id in nav_items:
            btn = self._create_nav_button(icon, text, page_id)
            self.nav_buttons[page_id] = btn
        
        # Spacer
        ctk.CTkFrame(self.sidebar, fg_color="transparent").pack(fill="y", expand=True)
        
        # Theme toggle at bottom
        theme_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        theme_frame.pack(pady=20)
        
        theme_label = ctk.CTkLabel(
            theme_frame,
            text="Dark Mode",
            font=theme_manager.get_font("body_small"),
            text_color=theme["fg_secondary"]
        )
        theme_label.pack(side="left", padx=5)
        
        self.theme_switch = ToggleSwitch(
            theme_frame,
            command=self._toggle_theme,
            width=50,
            height=25
        )
        self.theme_switch.pack(side="left")
        self.theme_switch.set_state(self.current_theme == "dark")
    
    def _create_nav_button(self, icon, text, page_id):
        """Create navigation button"""
        theme = theme_manager.get_theme()
        
        frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=50)
        frame.pack(fill="x", padx=10, pady=2)
        frame.pack_propagate(False)
        
        btn = ctk.CTkButton(
            frame,
            text=f"{icon}  {text}",
            font=theme_manager.get_font("body"),
            fg_color="transparent",
            text_color=theme["fg_secondary"],
            hover_color=theme["bg_tertiary"],
            anchor="w",
            command=lambda: self._show_page(page_id)
        )
        btn.pack(fill="both", expand=True)
        
        return btn
    
    def _create_header(self):
        """Create header bar"""
        theme = theme_manager.get_theme()
        
        self.header = ctk.CTkFrame(self.main_frame, height=60, fg_color=theme["bg_secondary"])
        self.header.pack(fill="x")
        self.header.pack_propagate(False)
        
        # Search bar
        self.search_bar = SearchBar(
            self.header,
            placeholder="Search settings, logs, help...",
            command=self._handle_search
        )
        self.search_bar.pack(side="left", padx=20, pady=15)
        
        # Action buttons
        button_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        button_frame.pack(side="right", padx=20)
        
        # Service control buttons
        self.start_btn = AnimatedButton(
            button_frame,
            text="▶ Start",
            command=self._start_service,
            width=100
        )
        self.start_btn.pack(side="left", padx=5)
        
        self.stop_btn = AnimatedButton(
            button_frame,
            text="⏹ Stop",
            command=self._stop_service,
            width=100
        )
        self.stop_btn.pack(side="left", padx=5)
        self.stop_btn.configure(state="disabled")
    
    def _create_pages(self):
        """Create content pages"""
        theme = theme_manager.get_theme()
        
        # Dashboard page
        self.pages["dashboard"] = Dashboard(self.main_frame, self.service_manager)
        
        # Configuration page
        self.pages["config"] = self._create_config_page()
        
        # Statistics page
        self.pages["stats"] = self._create_stats_page()
        
        # Advanced page
        self.pages["advanced"] = self._create_advanced_page()
        
        # Logs page
        self.pages["logs"] = self._create_logs_page()
        
        # About page
        self.pages["about"] = self._create_about_page()
    
    def _create_config_page(self):
        """Create configuration page"""
        theme = theme_manager.get_theme()
        
        page = ctk.CTkScrollableFrame(self.main_frame, fg_color=theme["bg"])
        
        # Title
        title = ctk.CTkLabel(
            page,
            text="Configuration",
            font=theme_manager.get_font("heading_lg"),
            text_color=theme["fg"]
        )
        title.pack(anchor="w", padx=20, pady=(20, 10))
        
        # Main settings card
        main_card = ModernCard(page)
        main_card.pack(fill="x", padx=20, pady=10)
        
        # Context input
        ctk.CTkLabel(
            main_card,
            text="Question Context",
            font=theme_manager.get_font("subheading"),
            text_color=theme["fg"]
        ).pack(anchor="w", padx=15, pady=(15, 5))
        
        self.context_entry = ctk.CTkTextbox(
            main_card,
            height=80,
            fg_color=theme["input_bg"],
            text_color=theme["fg"],
            font=theme_manager.get_font("body")
        )
        self.context_entry.pack(fill="x", padx=15, pady=(0, 10))
        
        # Duration slider
        ctk.CTkLabel(
            main_card,
            text="Session Duration (minutes)",
            font=theme_manager.get_font("subheading"),
            text_color=theme["fg"]
        ).pack(anchor="w", padx=15, pady=5)
        
        self.duration_slider = ctk.CTkSlider(
            main_card,
            from_=1,
            to=300,
            number_of_steps=299,
            command=self._update_duration_label
        )
        self.duration_slider.pack(fill="x", padx=15, pady=5)
        self.duration_slider.set(60)
        
        self.duration_label = ctk.CTkLabel(
            main_card,
            text="60 minutes",
            font=theme_manager.get_font("body"),
            text_color=theme["fg_secondary"]
        )
        self.duration_label.pack(padx=15, pady=(0, 15))
        
        # API settings card
        api_card = ModernCard(page)
        api_card.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            api_card,
            text="API Configuration",
            font=theme_manager.get_font("subheading"),
            text_color=theme["fg"]
        ).pack(anchor="w", padx=15, pady=(15, 10))
        
        # API key input
        self.api_key_entry = GlowingEntry(
            api_card,
            placeholder_text="Enter your API key...",
            show="*"
        )
        self.api_key_entry.pack(fill="x", padx=15, pady=(0, 15))
        
        return page
    
    def _create_stats_page(self):
        """Create statistics page"""
        theme = theme_manager.get_theme()
        
        page = ctk.CTkFrame(self.main_frame, fg_color=theme["bg"])
        
        title = ctk.CTkLabel(
            page,
            text="Statistics",
            font=theme_manager.get_font("heading_lg"),
            text_color=theme["fg"]
        )
        title.pack(anchor="w", padx=20, pady=20)
        
        # Stats content
        stats_text = ctk.CTkTextbox(
            page,
            fg_color=theme["bg_secondary"],
            text_color=theme["fg"],
            font=theme_manager.get_font("mono")
        )
        stats_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        return page
    
    def _create_advanced_page(self):
        """Create advanced settings page"""
        theme = theme_manager.get_theme()
        
        page = ctk.CTkScrollableFrame(self.main_frame, fg_color=theme["bg"])
        
        title = ctk.CTkLabel(
            page,
            text="Advanced Settings",
            font=theme_manager.get_font("heading_lg"),
            text_color=theme["fg"]
        )
        title.pack(anchor="w", padx=20, pady=20)
        
        # Performance settings
        perf_card = ModernCard(page)
        perf_card.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            perf_card,
            text="Performance",
            font=theme_manager.get_font("subheading"),
            text_color=theme["fg"]
        ).pack(anchor="w", padx=15, pady=(15, 10))
        
        # Toggle switches for features
        features = [
            ("Enable Caching", True),
            ("Parallel Processing", True),
            ("OCR Preprocessing", True),
            ("Template Matching", False),
            ("Human Simulation", True)
        ]
        
        for feature, default in features:
            frame = ctk.CTkFrame(perf_card, fg_color="transparent")
            frame.pack(fill="x", padx=15, pady=5)
            
            ctk.CTkLabel(
                frame,
                text=feature,
                font=theme_manager.get_font("body"),
                text_color=theme["fg_secondary"]
            ).pack(side="left")
            
            switch = ToggleSwitch(frame, width=40, height=20)
            switch.pack(side="right", padx=15)
            switch.set_state(default)
        
        # Application Management card
        app_card = ModernCard(page)
        app_card.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            app_card,
            text="Application Management",
            font=theme_manager.get_font("subheading"),
            text_color=theme["fg"]
        ).pack(anchor="w", padx=15, pady=(15, 10))
        
        # Service installation status
        service_frame = ctk.CTkFrame(app_card, fg_color="transparent")
        service_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(
            service_frame,
            text="Windows Service:",
            font=theme_manager.get_font("body"),
            text_color=theme["fg_secondary"]
        ).pack(side="left")
        
        self.service_status_label = ctk.CTkLabel(
            service_frame,
            text="Not Installed",
            font=theme_manager.get_font("body"),
            text_color=theme["warning"]
        )
        self.service_status_label.pack(side="left", padx=10)
        
        # Service management buttons
        service_btn_frame = ctk.CTkFrame(app_card, fg_color="transparent")
        service_btn_frame.pack(fill="x", padx=15, pady=10)
        
        self.install_service_btn = AnimatedButton(
            service_btn_frame,
            text="Install Service",
            width=120,
            command=self._install_service
        )
        self.install_service_btn.pack(side="left", padx=5)
        
        self.uninstall_service_btn = AnimatedButton(
            service_btn_frame,
            text="Uninstall Service",
            width=120,
            command=self._uninstall_service
        )
        self.uninstall_service_btn.pack(side="left", padx=5)
        
        # Separator
        ctk.CTkFrame(app_card, height=1, fg_color=theme["bg_secondary"]).pack(
            fill="x", padx=15, pady=15
        )
        
        # Application uninstall section
        uninstall_frame = ctk.CTkFrame(app_card, fg_color="transparent")
        uninstall_frame.pack(fill="x", padx=15, pady=(10, 20))
        
        ctk.CTkLabel(
            uninstall_frame,
            text="⚠️ Danger Zone",
            font=theme_manager.get_font("body"),
            text_color=theme["error"]
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            uninstall_frame,
            text="Completely remove Question Assistant from your system",
            font=theme_manager.get_font("small"),
            text_color=theme["fg_secondary"]
        ).pack(anchor="w", pady=(5, 10))
        
        uninstall_btn = ctk.CTkButton(
            uninstall_frame,
            text="Uninstall Application",
            fg_color=theme["error"],
            hover_color="#cc0000",
            width=150,
            height=35,
            command=self._uninstall_application
        )
        uninstall_btn.pack(anchor="w")
        
        # Check service status on page creation
        self._check_service_status()
        
        return page
    
    def _create_logs_page(self):
        """Create logs page"""
        theme = theme_manager.get_theme()
        
        page = ctk.CTkFrame(self.main_frame, fg_color=theme["bg"])
        
        # Header with controls
        header = ctk.CTkFrame(page, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            header,
            text="Application Logs",
            font=theme_manager.get_font("heading_lg"),
            text_color=theme["fg"]
        ).pack(side="left")
        
        # Log controls
        AnimatedButton(
            header,
            text="Clear",
            width=80
        ).pack(side="right", padx=5)
        
        AnimatedButton(
            header,
            text="Export",
            width=80
        ).pack(side="right", padx=5)
        
        # Log viewer
        self.log_viewer = ctk.CTkTextbox(
            page,
            fg_color=theme["bg_secondary"],
            text_color=theme["fg"],
            font=theme_manager.get_font("mono")
        )
        self.log_viewer.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        return page
    
    def _create_about_page(self):
        """Create about page"""
        theme = theme_manager.get_theme()
        
        page = ctk.CTkFrame(self.main_frame, fg_color=theme["bg"])
        
        # Center content
        content = ctk.CTkFrame(page, fg_color="transparent")
        content.place(relx=0.5, rely=0.5, anchor="center")
        
        # Logo
        ctk.CTkLabel(
            content,
            text="🎯",
            font=("Segoe UI", 64)
        ).pack(pady=20)
        
        # Title
        ctk.CTkLabel(
            content,
            text="Question Assistant Pro",
            font=theme_manager.get_font("heading_xl"),
            text_color=theme["fg"]
        ).pack()
        
        # Version
        ctk.CTkLabel(
            content,
            text="Version 3.0",
            font=theme_manager.get_font("body"),
            text_color=theme["fg_secondary"]
        ).pack(pady=10)
        
        # Description
        ctk.CTkLabel(
            content,
            text="Advanced automated question detection and answering system\nwith AI-powered intelligence and human-like interaction",
            font=theme_manager.get_font("body"),
            text_color=theme["fg_secondary"],
            justify="center"
        ).pack(pady=20)
        
        # Links
        link_frame = ctk.CTkFrame(content, fg_color="transparent")
        link_frame.pack(pady=20)
        
        AnimatedButton(
            link_frame,
            text="Documentation",
            width=120
        ).pack(side="left", padx=5)
        
        AnimatedButton(
            link_frame,
            text="GitHub",
            width=120
        ).pack(side="left", padx=5)
        
        return page
    
    def _show_page(self, page_id):
        """Show a specific page"""
        # Hide all pages
        for page in self.pages.values():
            page.pack_forget()
        
        # Show selected page
        if page_id in self.pages:
            self.pages[page_id].pack(fill="both", expand=True)
        
        # Update nav button states
        theme = theme_manager.get_theme()
        for btn_id, btn in self.nav_buttons.items():
            if btn_id == page_id:
                btn.configure(fg_color=theme["bg_tertiary"], text_color=theme["accent"])
            else:
                btn.configure(fg_color="transparent", text_color=theme["fg_secondary"])
    
    def _toggle_theme(self, state):
        """Toggle between dark and light theme"""
        self.current_theme = "dark" if state else "light"
        theme_manager.set_theme(self.current_theme)
        
        # Show notification
        NotificationToast(
            self,
            f"Switched to {self.current_theme} theme",
            "info"
        )
        
        # Note: Full theme update would require recreating widgets
        # For now, just show notification
    
    def _update_duration_label(self, value):
        """Update duration label"""
        self.duration_label.configure(text=f"{int(value)} minutes")
    
    def _handle_search(self, query):
        """Handle search query"""
        if query:
            NotificationToast(self, f"Searching for: {query}", "info")
    
    def _start_service(self):
        """Start the service"""
        try:
            # Update config
            self.config.set('context', self.context_entry.get("1.0", "end").strip())
            self.config.set('duration_minutes', int(self.duration_slider.get()))
            self.config.set('api_key', self.api_key_entry.get())
            
            # Initialize and start service
            self.service_manager = ServiceManager()
            self.service_manager.config = self.config
            self.service_manager.start()
            
            # Update UI
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            
            # Update dashboard
            if "dashboard" in self.pages:
                self.pages["dashboard"].service_manager = self.service_manager
            
            # Show notification
            NotificationToast(self, "Service started successfully", "success")
            
            # Log activity
            if hasattr(self.pages["dashboard"], 'log_activity'):
                self.pages["dashboard"].log_activity("Service started", "success")
            
        except Exception as e:
            NotificationToast(self, f"Failed to start service: {str(e)}", "error")
    
    def _stop_service(self):
        """Stop the service"""
        if self.service_manager:
            self.service_manager.stop()
            
            # Update UI
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            
            # Show notification
            NotificationToast(self, "Service stopped", "info")
            
            # Log activity
            if hasattr(self.pages["dashboard"], 'log_activity'):
                self.pages["dashboard"].log_activity("Service stopped", "warning")
    
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        shortcuts = {
            "<Control-q>": lambda e: self.quit(),
            "<Control-s>": lambda e: self._start_service(),
            "<Control-x>": lambda e: self._stop_service(),
            "<F1>": lambda e: self._show_page("about"),
            "<F5>": lambda e: self._refresh_dashboard(),
            "<Control-d>": lambda e: self._show_page("dashboard"),
            "<Control-l>": lambda e: self._show_page("logs")
        }
        
        for key, handler in shortcuts.items():
            self.bind(key, handler)
    
    def _refresh_dashboard(self):
        """Refresh dashboard data"""
        if "dashboard" in self.pages:
            self.pages["dashboard"]._update_dashboard()
            NotificationToast(self, "Dashboard refreshed", "info")
    
    def _init_system_tray(self):
        """Initialize system tray"""
        try:
            self.system_tray = SystemTray(self, self.service_manager)
            self.system_tray.start()
        except Exception as e:
            self.logger.warning(f"Could not initialize system tray: {e}")
    
    def _center_window(self):
        """Center window on screen"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def _check_service_status(self):
        """Check Windows service installation status"""
        try:
            import win32serviceutil
            import win32service
            
            service_name = "QuestionAssistantService"
            
            try:
                status = win32serviceutil.QueryServiceStatus(service_name)
                if status:
                    self.service_status_label.configure(
                        text="Installed",
                        text_color=theme_manager.get_theme()["success"]
                    )
                    self.install_service_btn.configure(state="disabled")
                    self.uninstall_service_btn.configure(state="normal")
            except:
                self.service_status_label.configure(
                    text="Not Installed",
                    text_color=theme_manager.get_theme()["warning"]
                )
                self.install_service_btn.configure(state="normal")
                self.uninstall_service_btn.configure(state="disabled")
        except ImportError:
            self.service_status_label.configure(
                text="Service support not available",
                text_color=theme_manager.get_theme()["fg_secondary"]
            )
            self.install_service_btn.configure(state="disabled")
            self.uninstall_service_btn.configure(state="disabled")
    
    def _install_service(self):
        """Install Windows service"""
        result = messagebox.askyesno(
            "Install Service",
            "This will install Question Assistant as a Windows service.\n\n"
            "Administrator privileges are required.\n\n"
            "Continue?"
        )
        
        if result:
            try:
                import ctypes
                import sys
                import subprocess
                
                # Check if running as admin
                if not ctypes.windll.shell32.IsUserAnAdmin():
                    # Request admin privileges
                    ctypes.windll.shell32.ShellExecuteW(
                        None,
                        "runas",
                        sys.executable,
                        f'"{sys.argv[0]}" --mode install',
                        None,
                        1
                    )
                    NotificationToast(
                        self,
                        "Please grant administrator privileges to install the service",
                        "info"
                    )
                else:
                    # Install service
                    subprocess.run([sys.executable, "main.py", "--mode", "install"], check=True)
                    NotificationToast(self, "Service installed successfully", "success")
                    self._check_service_status()
                    
            except Exception as e:
                messagebox.showerror("Installation Failed", f"Failed to install service:\n{str(e)}")
    
    def _uninstall_service(self):
        """Uninstall Windows service"""
        result = messagebox.askyesno(
            "Uninstall Service",
            "This will remove the Question Assistant Windows service.\n\n"
            "Administrator privileges are required.\n\n"
            "Continue?"
        )
        
        if result:
            try:
                import ctypes
                import subprocess
                import sys
                
                # Check if running as admin
                if not ctypes.windll.shell32.IsUserAnAdmin():
                    messagebox.showinfo(
                        "Admin Required",
                        "Please run the application as Administrator to uninstall the service"
                    )
                else:
                    # Stop service first if running
                    try:
                        subprocess.run(["net", "stop", "QuestionAssistantService"], capture_output=True)
                    except:
                        pass
                    
                    # Uninstall service
                    subprocess.run(["sc", "delete", "QuestionAssistantService"], check=True)
                    NotificationToast(self, "Service uninstalled successfully", "success")
                    self._check_service_status()
                    
            except Exception as e:
                messagebox.showerror("Uninstall Failed", f"Failed to uninstall service:\n{str(e)}")
    
    def _uninstall_application(self):
        """Completely uninstall the application"""
        result = messagebox.askyesno(
            "Uninstall Application",
            "⚠️ WARNING ⚠️\n\n"
            "This will completely remove Question Assistant from your system:\n\n"
            "• Remove all application files\n"
            "• Delete configuration and logs\n"
            "• Uninstall Windows service (if installed)\n"
            "• Remove registry entries\n\n"
            "This action cannot be undone!\n\n"
            "Are you sure you want to continue?",
            icon='warning'
        )
        
        if result:
            # Double confirmation for safety
            confirm = messagebox.askyesno(
                "Final Confirmation",
                "This is your last chance to cancel.\n\n"
                "Delete Question Assistant and all its data?",
                icon='warning'
            )
            
            if confirm:
                self._perform_uninstall()
    
    def _perform_uninstall(self):
        """Perform the actual uninstallation"""
        try:
            import shutil
            import subprocess
            import sys
            import os
            
            # Stop service if running
            if self.service_manager and self.service_manager.running:
                self.service_manager.stop()
            
            # Create uninstaller script
            uninstall_script = '''
import os
import sys
import shutil
import time
import subprocess

def uninstall():
    try:
        print("Starting uninstallation...")
        
        # Stop and remove Windows service
        try:
            subprocess.run(["net", "stop", "QuestionAssistantService"], capture_output=True)
            subprocess.run(["sc", "delete", "QuestionAssistantService"], capture_output=True)
            print("Service removed")
        except:
            pass
        
        # Remove from startup (if added)
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                0,
                winreg.KEY_ALL_ACCESS
            )
            try:
                winreg.DeleteValue(key, "QuestionAssistant")
            except:
                pass
            winreg.CloseKey(key)
            print("Startup entry removed")
        except:
            pass
        
        # Wait for main app to close
        time.sleep(2)
        
        # Get application directory
        app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        parent_dir = os.path.dirname(app_dir)
        
        # Remove application directory
        try:
            os.chdir(parent_dir)  # Change to parent directory
            shutil.rmtree(app_dir, ignore_errors=True)
            print(f"Application files removed from {app_dir}")
        except Exception as e:
            print(f"Error removing files: {e}")
        
        # Remove config directory from user profile
        config_dir = os.path.join(os.environ.get('APPDATA', ''), 'QuestionAssistant')
        if os.path.exists(config_dir):
            shutil.rmtree(config_dir, ignore_errors=True)
            print("Configuration files removed")
        
        print("\\nUninstallation complete!")
        print("Thank you for using Question Assistant.")
        input("Press Enter to exit...")
        
    except Exception as e:
        print(f"Uninstallation error: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    uninstall()
'''
            
            # Save uninstaller script
            uninstaller_path = os.path.join(tempfile.gettempdir(), "uninstall_qa.py")
            with open(uninstaller_path, 'w') as f:
                f.write(uninstall_script)
            
            # Show progress
            messagebox.showinfo(
                "Uninstalling",
                "The uninstaller will now run.\n\n"
                "The application will close and all files will be removed."
            )
            
            # Launch uninstaller in new process
            subprocess.Popen([sys.executable, uninstaller_path], 
                           creationflags=subprocess.CREATE_NEW_CONSOLE)
            
            # Close the application
            if self.system_tray:
                self.system_tray.stop()
            
            # Exit immediately
            os._exit(0)
            
        except Exception as e:
            messagebox.showerror(
                "Uninstall Error",
                f"Failed to uninstall application:\n{str(e)}\n\n"
                "You may need to manually delete the application files."
            )
    
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
            
            if result is True:  # Minimize to tray
                self.withdraw()
                if self.system_tray:
                    self.system_tray.show_notification(
                        "Question Assistant",
                        "Application minimized to system tray"
                    )
            elif result is False:  # Stop and exit
                self.service_manager.stop()
                if self.system_tray:
                    self.system_tray.stop()
                self.quit()
        else:
            if self.system_tray:
                self.system_tray.stop()
            self.quit()

def main():
    """Main entry point"""
    app = ModernQuestionAssistant()
    app.mainloop()

if __name__ == "__main__":
    main()