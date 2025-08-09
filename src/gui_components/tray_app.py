"""System tray application for Question Assistant"""
import sys
import threading
import time
from pathlib import Path
import customtkinter as ctk
import pystray
from PIL import Image, ImageDraw
from pystray import MenuItem as item
import tkinter as tk

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.config import Config
from src.core.service_manager import ServiceManager
from src.utils.logger import get_logger
from src.gui_components.simple_main import SimpleAssistant


class TrayApplication:
    """System tray application that runs in background"""
    
    def __init__(self):
        self.config = Config()
        self.service_manager = None
        self.logger = get_logger("TrayApp")
        self.is_running = False
        self.window = None
        self.icon = None
        self.window_visible = False
        
        # Create system tray icon
        self._create_tray_icon()
        
        # Auto-start in tray
        self.logger.info("Question Assistant started in system tray")
    
    def _create_icon_image(self, color="#4a9eff"):
        """Create icon image for system tray"""
        # Create a simple icon
        width = 64
        height = 64
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw a circle for the icon
        if self.is_running:
            # Green dot when running
            draw.ellipse([16, 16, 48, 48], fill="#4caf50")
        else:
            # Blue dot when idle
            draw.ellipse([16, 16, 48, 48], fill=color)
        
        # Add Q letter
        try:
            from PIL import ImageFont
            # Try to use a font
            font = ImageFont.truetype("arial.ttf", 24)
            draw.text((28, 20), "Q", fill="white", font=font)
        except:
            # Fallback to default font
            draw.text((28, 24), "Q", fill="white")
        
        return image
    
    def _create_tray_icon(self):
        """Create system tray icon with menu"""
        # Create icon
        image = self._create_icon_image()
        
        # Create menu
        menu = pystray.Menu(
            item('Show/Hide Window', self._toggle_window, default=True),
            item('Start Service', self._start_from_tray, visible=lambda item: not self.is_running),
            item('Stop Service', self._stop_from_tray, visible=lambda item: self.is_running),
            pystray.Menu.SEPARATOR,
            item('Configuration', self._show_config),
            item('View Logs', self._show_logs),
            pystray.Menu.SEPARATOR,
            item('Exit', self._quit_app)
        )
        
        # Create system tray icon
        self.icon = pystray.Icon(
            "QuestionAssistant",
            image,
            "Question Assistant",
            menu
        )
        
        # Run icon in separate thread
        icon_thread = threading.Thread(target=self.icon.run, daemon=True)
        icon_thread.start()
    
    def _update_icon(self):
        """Update tray icon based on status"""
        if self.icon:
            self.icon.icon = self._create_icon_image()
            
            # Update tooltip
            if self.is_running:
                self.icon.title = "Question Assistant - Running"
            else:
                self.icon.title = "Question Assistant - Idle"
    
    def _toggle_window(self, icon=None, item=None):
        """Show or hide the main window"""
        if self.window and self.window_visible:
            self._hide_window()
        else:
            self._show_window()
    
    def _show_window(self):
        """Show the main window"""
        if not self.window:
            # Create window if it doesn't exist
            self.window = TrayMainWindow(self)
            self.window.protocol("WM_DELETE_WINDOW", self._hide_window)
        
        # Show window
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()
        self.window_visible = True
        self.logger.info("Window shown")
    
    def _hide_window(self):
        """Hide the main window but keep app running"""
        if self.window:
            self.window.withdraw()
            self.window_visible = False
            self.logger.info("Window hidden - app still running in tray")
    
    def _start_from_tray(self, icon=None, item=None):
        """Start service from tray menu"""
        if not self.is_running:
            self.start_service()
    
    def _stop_from_tray(self, icon=None, item=None):
        """Stop service from tray menu"""
        if self.is_running:
            self.stop_service()
    
    def _show_config(self, icon=None, item=None):
        """Show configuration window"""
        self._show_window()
        if self.window:
            self.window.show_config_page()
    
    def _show_logs(self, icon=None, item=None):
        """Show logs window"""
        self._show_window()
        if self.window:
            self.window.show_logs_page()
    
    def start_service(self):
        """Start the service"""
        try:
            if self.is_running:
                return
            
            # Start service
            self.service_manager = ServiceManager()
            self.service_manager.config = self.config
            
            # Start in thread
            thread = threading.Thread(target=self.service_manager.start)
            thread.daemon = True
            thread.start()
            
            self.is_running = True
            self._update_icon()
            
            # Show notification
            if self.icon:
                self.icon.notify("Service Started", "Question Assistant is now running")
            
            self.logger.info("Service started from tray")
            
            # Update window if visible
            if self.window:
                self.window.update_status(True)
                
        except Exception as e:
            self.logger.error(f"Error starting service: {e}")
            if self.icon:
                self.icon.notify("Error", f"Failed to start service: {str(e)}")
    
    def stop_service(self):
        """Stop the service"""
        try:
            if not self.is_running:
                return
            
            if self.service_manager:
                self.service_manager.running = False
                self.service_manager.stop()
                self.service_manager = None
            
            self.is_running = False
            self._update_icon()
            
            # Show notification
            if self.icon:
                self.icon.notify("Service Stopped", "Question Assistant has stopped")
            
            self.logger.info("Service stopped from tray")
            
            # Update window if visible
            if self.window:
                self.window.update_status(False)
                
        except Exception as e:
            self.logger.error(f"Error stopping service: {e}")
    
    def _quit_app(self, icon=None, item=None):
        """Quit the application completely"""
        self.logger.info("Quitting application")
        
        # Stop service if running
        if self.is_running:
            self.stop_service()
        
        # Close window if open
        if self.window:
            self.window.destroy()
        
        # Stop icon
        if self.icon:
            self.icon.stop()
        
        # Exit
        sys.exit(0)
    
    def run(self):
        """Run the application"""
        # Start with window hidden
        self.logger.info("Running in system tray mode")
        
        # Keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self._quit_app()


class TrayMainWindow(ctk.CTk):
    """Minimal window for tray application"""
    
    def __init__(self, tray_app):
        super().__init__()
        
        self.tray_app = tray_app
        
        # Window setup
        self.title("Question Assistant")
        self.geometry("600x400")
        self.minsize(500, 350)
        
        # Colors
        self.colors = {
            "bg": "#1a1a1a",
            "card": "#2d2d2d",
            "accent": "#4a9eff",
            "success": "#4caf50",
            "error": "#f44336",
            "text": "#ffffff",
            "text_dim": "#888888"
        }
        
        self.configure(fg_color=self.colors["bg"])
        
        # Create UI
        self._create_ui()
        
        # Start hidden
        self.withdraw()
    
    def _create_ui(self):
        """Create minimal UI"""
        # Header
        header = ctk.CTkFrame(self, fg_color=self.colors["card"], height=50)
        header.pack(fill="x", padx=10, pady=(10, 5))
        header.pack_propagate(False)
        
        # Title and status
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(expand=True)
        
        title = ctk.CTkLabel(
            title_frame,
            text="Question Assistant",
            font=("Arial", 16, "bold"),
            text_color=self.colors["text"]
        )
        title.pack(side="left", padx=10)
        
        self.status_label = ctk.CTkLabel(
            title_frame,
            text="● Idle",
            font=("Arial", 12),
            text_color=self.colors["text_dim"]
        )
        self.status_label.pack(side="left", padx=20)
        
        # Control buttons
        button_frame = ctk.CTkFrame(title_frame, fg_color="transparent")
        button_frame.pack(side="right", padx=10)
        
        self.start_btn = ctk.CTkButton(
            button_frame,
            text="Start",
            width=70,
            height=30,
            command=self.tray_app.start_service,
            fg_color=self.colors["success"]
        )
        self.start_btn.pack(side="left", padx=5)
        
        self.stop_btn = ctk.CTkButton(
            button_frame,
            text="Stop",
            width=70,
            height=30,
            command=self.tray_app.stop_service,
            fg_color=self.colors["error"],
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=5)
        
        # Content area
        self.content = ctk.CTkFrame(self, fg_color=self.colors["card"])
        self.content.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Info text
        info = ctk.CTkLabel(
            self.content,
            text="Question Assistant is running in the system tray.\n\nYou can close this window and the app will continue running.\nAccess controls from the system tray icon.",
            font=("Arial", 12),
            text_color=self.colors["text_dim"],
            justify="center"
        )
        info.pack(expand=True)
        
        # Bottom info
        bottom = ctk.CTkFrame(self, fg_color=self.colors["card"], height=30)
        bottom.pack(fill="x", padx=10, pady=(5, 10))
        
        info_label = ctk.CTkLabel(
            bottom,
            text="💡 Tip: Press ESC to quickly hide this window",
            font=("Arial", 10),
            text_color=self.colors["text_dim"]
        )
        info_label.pack(pady=5)
        
        # Keyboard shortcuts
        self.bind("<Escape>", lambda e: self.tray_app._hide_window())
        self.bind("<Control-s>", lambda e: self.tray_app.start_service())
        self.bind("<Control-x>", lambda e: self.tray_app.stop_service())
    
    def update_status(self, is_running):
        """Update status display"""
        if is_running:
            self.status_label.configure(
                text="● Running",
                text_color=self.colors["success"]
            )
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
        else:
            self.status_label.configure(
                text="● Idle",
                text_color=self.colors["text_dim"]
            )
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
    
    def show_config_page(self):
        """Show configuration page"""
        # Clear content
        for widget in self.content.winfo_children():
            widget.destroy()
        
        # Add config UI
        config_label = ctk.CTkLabel(
            self.content,
            text="Configuration",
            font=("Arial", 14, "bold"),
            text_color=self.colors["text"]
        )
        config_label.pack(pady=10)
        
        # Add basic config options
        context_label = ctk.CTkLabel(
            self.content,
            text="Context:",
            font=("Arial", 11),
            text_color=self.colors["text_dim"]
        )
        context_label.pack(pady=(10, 5))
        
        context_entry = ctk.CTkEntry(
            self.content,
            placeholder_text="e.g., Mathematics",
            width=300
        )
        context_entry.pack()
    
    def show_logs_page(self):
        """Show logs page"""
        # Clear content
        for widget in self.content.winfo_children():
            widget.destroy()
        
        # Add logs UI
        logs_label = ctk.CTkLabel(
            self.content,
            text="Activity Logs",
            font=("Arial", 14, "bold"),
            text_color=self.colors["text"]
        )
        logs_label.pack(pady=10)
        
        # Log text area
        log_text = ctk.CTkTextbox(
            self.content,
            fg_color=self.colors["bg"],
            text_color=self.colors["text_dim"]
        )
        log_text.pack(fill="both", expand=True, padx=20, pady=10)
        log_text.insert("1.0", "Application logs will appear here...")


if __name__ == "__main__":
    app = TrayApplication()
    app.run()