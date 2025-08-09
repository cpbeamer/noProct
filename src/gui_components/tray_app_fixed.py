"""System tray application for Question Assistant - Fixed version"""
import sys
import threading
import time
import queue
from pathlib import Path
import tkinter as tk
import customtkinter as ctk
import pystray
from PIL import Image, ImageDraw
from pystray import MenuItem as item

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.config import Config
from src.core.service_manager import ServiceManager
from src.utils.logger import get_logger


class TrayApplication:
    """System tray application that runs in background"""
    
    def __init__(self):
        self.config = Config()
        self.service_manager = None
        self.logger = get_logger("TrayApp")
        self.is_running = False
        self.icon = None
        self.root = None
        self.window = None
        self.window_visible = False
        self.command_queue = queue.Queue()
        
        # Setup main thread for GUI
        self._setup_gui_thread()
        
        self.logger.info("Question Assistant started in system tray")
    
    def _setup_gui_thread(self):
        """Setup GUI in main thread"""
        # Create root window in main thread
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the root window
        
        # Process commands from queue
        self._process_queue()
    
    def _process_queue(self):
        """Process commands from the queue"""
        try:
            while True:
                try:
                    command = self.command_queue.get_nowait()
                    command()
                except queue.Empty:
                    break
        except Exception as e:
            self.logger.error(f"Error processing queue: {e}")
        finally:
            # Schedule next check
            self.root.after(100, self._process_queue)
    
    def _create_icon_image(self):
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
            draw.ellipse([16, 16, 48, 48], fill="#4a9eff")
        
        # Add Q letter
        draw.text((26, 20), "Q", fill="white", font=None)
        
        return image
    
    def _create_tray_icon(self):
        """Create system tray icon with menu"""
        # Create icon
        image = self._create_icon_image()
        
        # Create menu
        menu = pystray.Menu(
            item('Show Window', self._queue_show_window, default=True),
            item('Hide Window', self._queue_hide_window),
            pystray.Menu.SEPARATOR,
            item('Start Service', self._queue_start_service, visible=lambda item: not self.is_running),
            item('Stop Service', self._queue_stop_service, visible=lambda item: self.is_running),
            pystray.Menu.SEPARATOR,
            item('Exit', self._queue_quit)
        )
        
        # Create system tray icon
        self.icon = pystray.Icon(
            "QuestionAssistant",
            image,
            "Question Assistant",
            menu
        )
    
    def _queue_show_window(self, icon=None, item=None):
        """Queue show window command"""
        self.command_queue.put(self._show_window)
    
    def _queue_hide_window(self, icon=None, item=None):
        """Queue hide window command"""
        self.command_queue.put(self._hide_window)
    
    def _queue_start_service(self, icon=None, item=None):
        """Queue start service command"""
        self.command_queue.put(self.start_service)
    
    def _queue_stop_service(self, icon=None, item=None):
        """Queue stop service command"""
        self.command_queue.put(self.stop_service)
    
    def _queue_quit(self, icon=None, item=None):
        """Queue quit command"""
        self.command_queue.put(self._quit_app)
    
    def _show_window(self):
        """Show the main window"""
        try:
            if not self.window:
                # Create window if it doesn't exist
                self.window = TrayMainWindow(self.root, self)
                
            # Show window
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()
            self.window_visible = True
            self.logger.info("Window shown")
        except Exception as e:
            self.logger.error(f"Error showing window: {e}")
    
    def _hide_window(self):
        """Hide the main window but keep app running"""
        try:
            if self.window:
                self.window.withdraw()
                self.window_visible = False
                self.logger.info("Window hidden - app still running in tray")
        except Exception as e:
            self.logger.error(f"Error hiding window: {e}")
    
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
            
            self.logger.info("Service started")
            
            # Update window if visible
            if self.window:
                self.window.update_status(True)
                
        except Exception as e:
            self.logger.error(f"Error starting service: {e}")
    
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
            
            self.logger.info("Service stopped")
            
            # Update window if visible
            if self.window:
                self.window.update_status(False)
                
        except Exception as e:
            self.logger.error(f"Error stopping service: {e}")
    
    def _update_icon(self):
        """Update tray icon based on status"""
        if self.icon:
            self.icon.icon = self._create_icon_image()
            
            # Update tooltip
            if self.is_running:
                self.icon.title = "Question Assistant - Running"
            else:
                self.icon.title = "Question Assistant - Idle"
    
    def _quit_app(self):
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
        
        # Quit root
        if self.root:
            self.root.quit()
            self.root.destroy()
        
        # Exit
        sys.exit(0)
    
    def run(self):
        """Run the application"""
        # Create tray icon
        self._create_tray_icon()
        
        # Run icon in separate thread
        icon_thread = threading.Thread(target=self.icon.run, daemon=True)
        icon_thread.start()
        
        # Run GUI main loop in main thread
        self.logger.info("Running in system tray mode")
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self._quit_app()


class TrayMainWindow(ctk.CTkToplevel):
    """Minimal window for tray application"""
    
    def __init__(self, parent, tray_app):
        super().__init__(parent)
        
        self.tray_app = tray_app
        
        # Window setup
        self.title("Question Assistant")
        self.geometry("600x400")
        self.minsize(500, 350)
        
        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self.hide_window)
        
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
        
        # Configure appearance
        ctk.set_appearance_mode("dark")
        self.configure(fg_color=self.colors["bg"])
        
        # Create UI
        self._create_ui()
        
        # Start hidden
        self.withdraw()
    
    def hide_window(self):
        """Hide window instead of destroying"""
        self.withdraw()
        self.tray_app.window_visible = False
    
    def _create_ui(self):
        """Create minimal UI"""
        # Main container
        main_frame = ctk.CTkFrame(self, fg_color=self.colors["bg"])
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header
        header = ctk.CTkFrame(main_frame, fg_color=self.colors["card"], height=60, corner_radius=10)
        header.pack(fill="x", pady=(0, 10))
        header.pack_propagate(False)
        
        # Title and status
        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(expand=True)
        
        title = ctk.CTkLabel(
            header_content,
            text="Question Assistant",
            font=("Arial", 18, "bold"),
            text_color=self.colors["text"]
        )
        title.pack(side="left", padx=20)
        
        self.status_label = ctk.CTkLabel(
            header_content,
            text="● Idle",
            font=("Arial", 14),
            text_color=self.colors["text_dim"]
        )
        self.status_label.pack(side="left", padx=20)
        
        # Control buttons
        button_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        button_frame.pack(side="right", padx=20)
        
        self.start_btn = ctk.CTkButton(
            button_frame,
            text="Start",
            width=80,
            height=35,
            command=self.tray_app.start_service,
            fg_color=self.colors["success"],
            hover_color="#45a049"
        )
        self.start_btn.pack(side="left", padx=5)
        
        self.stop_btn = ctk.CTkButton(
            button_frame,
            text="Stop",
            width=80,
            height=35,
            command=self.tray_app.stop_service,
            fg_color=self.colors["error"],
            hover_color="#da190b",
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=5)
        
        # Content area
        content = ctk.CTkFrame(main_frame, fg_color=self.colors["card"], corner_radius=10)
        content.pack(fill="both", expand=True, pady=(0, 10))
        
        # Info text
        info_frame = ctk.CTkFrame(content, fg_color="transparent")
        info_frame.pack(expand=True)
        
        info = ctk.CTkLabel(
            info_frame,
            text="Question Assistant is running in the system tray",
            font=("Arial", 16),
            text_color=self.colors["text"]
        )
        info.pack(pady=(20, 10))
        
        info2 = ctk.CTkLabel(
            info_frame,
            text="You can safely close this window.\nThe app will continue running in the background.",
            font=("Arial", 12),
            text_color=self.colors["text_dim"],
            justify="center"
        )
        info2.pack(pady=10)
        
        # Quick stats
        stats_frame = ctk.CTkFrame(content, fg_color=self.colors["bg"], corner_radius=8)
        stats_frame.pack(pady=20, padx=40, fill="x")
        
        self.stats_label = ctk.CTkLabel(
            stats_frame,
            text="Service Status: Idle\nQuestions Detected: 0\nQuestions Answered: 0",
            font=("Arial", 11),
            text_color=self.colors["text_dim"],
            justify="left"
        )
        self.stats_label.pack(pady=15, padx=20)
        
        # Bottom info
        bottom = ctk.CTkFrame(main_frame, fg_color=self.colors["card"], height=40, corner_radius=10)
        bottom.pack(fill="x")
        bottom.pack_propagate(False)
        
        tip_label = ctk.CTkLabel(
            bottom,
            text="💡 Tip: Right-click the tray icon for more options",
            font=("Arial", 11),
            text_color=self.colors["text_dim"]
        )
        tip_label.pack(expand=True)
        
        # Keyboard shortcuts
        self.bind("<Escape>", lambda e: self.hide_window())
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
            self.stats_label.configure(
                text="Service Status: Running\nQuestions Detected: 0\nQuestions Answered: 0"
            )
        else:
            self.status_label.configure(
                text="● Idle",
                text_color=self.colors["text_dim"]
            )
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            self.stats_label.configure(
                text="Service Status: Idle\nQuestions Detected: 0\nQuestions Answered: 0"
            )


if __name__ == "__main__":
    app = TrayApplication()
    app.run()