"""Simple, clean UI for Question Assistant"""
import tkinter as tk
import customtkinter as ctk
from pathlib import Path
import sys
import threading
import time

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.config import Config
from src.core.service_manager import ServiceManager
from src.utils.logger import get_logger

# Configure appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class SimpleAssistant(ctk.CTk):
    """Simple, functional UI for Question Assistant"""
    
    def __init__(self):
        super().__init__()
        
        # Window setup
        self.title("Question Assistant")
        self.geometry("900x600")
        self.minsize(800, 500)
        
        # Initialize components
        self.config = Config()
        self.service_manager = None
        self.logger = get_logger("GUI")
        self.is_running = False
        
        # Colors
        self.colors = {
            "bg": "#1a1a1a",
            "sidebar": "#242424",
            "card": "#2d2d2d",
            "accent": "#4a9eff",
            "text": "#ffffff",
            "text_dim": "#888888",
            "success": "#4caf50",
            "error": "#f44336"
        }
        
        self.configure(fg_color=self.colors["bg"])
        
        # Create UI
        self._create_ui()
        
        # Keyboard shortcuts
        self.bind("<Control-s>", lambda e: self._start_service())
        self.bind("<Control-x>", lambda e: self._stop_service())
        self.bind("<Escape>", lambda e: self._stop_service())
        
        # Close handler
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _create_ui(self):
        """Create the main UI layout"""
        # Main container
        main_frame = ctk.CTkFrame(self, fg_color=self.colors["bg"])
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Top bar with controls
        self._create_top_bar(main_frame)
        
        # Main content area
        content_frame = ctk.CTkFrame(main_frame, fg_color=self.colors["card"], corner_radius=10)
        content_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        # Two column layout
        left_column = ctk.CTkFrame(content_frame, fg_color="transparent")
        left_column.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        
        right_column = ctk.CTkFrame(content_frame, fg_color="transparent")
        right_column.pack(side="right", fill="both", expand=True, padx=(0, 20), pady=20)
        
        # Configuration section
        self._create_config_section(left_column)
        
        # Statistics section
        self._create_stats_section(right_column)
        
        # Activity log at bottom
        self._create_activity_log(main_frame)
    
    def _create_top_bar(self, parent):
        """Create top control bar"""
        top_bar = ctk.CTkFrame(parent, fg_color=self.colors["card"], height=60, corner_radius=10)
        top_bar.pack(fill="x")
        top_bar.pack_propagate(False)
        
        # Inner frame for controls
        controls = ctk.CTkFrame(top_bar, fg_color="transparent")
        controls.pack(expand=True)
        
        # Status indicator
        self.status_frame = ctk.CTkFrame(controls, fg_color="transparent")
        self.status_frame.pack(side="left", padx=20)
        
        self.status_dot = ctk.CTkLabel(
            self.status_frame,
            text="●",
            font=("Arial", 16),
            text_color=self.colors["text_dim"]
        )
        self.status_dot.pack(side="left", padx=(0, 10))
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready",
            font=("Arial", 14),
            text_color=self.colors["text"]
        )
        self.status_label.pack(side="left")
        
        # Control buttons
        button_frame = ctk.CTkFrame(controls, fg_color="transparent")
        button_frame.pack(side="left", padx=40)
        
        self.start_btn = ctk.CTkButton(
            button_frame,
            text="Start",
            width=100,
            height=35,
            command=self._start_service,
            fg_color=self.colors["accent"],
            hover_color="#3a8eef"
        )
        self.start_btn.pack(side="left", padx=5)
        
        self.stop_btn = ctk.CTkButton(
            button_frame,
            text="Stop",
            width=100,
            height=35,
            command=self._stop_service,
            fg_color=self.colors["error"],
            hover_color="#d32f2f",
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=5)
        
        # Time remaining
        self.time_label = ctk.CTkLabel(
            controls,
            text="",
            font=("Arial", 12),
            text_color=self.colors["text_dim"]
        )
        self.time_label.pack(side="right", padx=20)
    
    def _create_config_section(self, parent):
        """Create configuration section"""
        # Title
        title = ctk.CTkLabel(
            parent,
            text="Configuration",
            font=("Arial", 18, "bold"),
            text_color=self.colors["text"]
        )
        title.pack(anchor="w", pady=(0, 15))
        
        # Context input
        context_label = ctk.CTkLabel(
            parent,
            text="Context/Subject:",
            font=("Arial", 12),
            text_color=self.colors["text_dim"]
        )
        context_label.pack(anchor="w", pady=(10, 5))
        
        self.context_entry = ctk.CTkEntry(
            parent,
            placeholder_text="e.g., Mathematics, History, Science",
            height=35,
            fg_color=self.colors["sidebar"],
            border_color=self.colors["accent"],
            border_width=1
        )
        self.context_entry.pack(fill="x", pady=(0, 10))
        
        # Duration slider
        duration_label = ctk.CTkLabel(
            parent,
            text="Duration (minutes):",
            font=("Arial", 12),
            text_color=self.colors["text_dim"]
        )
        duration_label.pack(anchor="w", pady=(10, 5))
        
        duration_frame = ctk.CTkFrame(parent, fg_color="transparent")
        duration_frame.pack(fill="x", pady=(0, 10))
        
        self.duration_slider = ctk.CTkSlider(
            duration_frame,
            from_=5,
            to=180,
            number_of_steps=35,
            progress_color=self.colors["accent"],
            button_color=self.colors["accent"],
            button_hover_color="#3a8eef"
        )
        self.duration_slider.set(30)
        self.duration_slider.pack(side="left", fill="x", expand=True)
        
        self.duration_value = ctk.CTkLabel(
            duration_frame,
            text="30 min",
            font=("Arial", 12),
            text_color=self.colors["text"]
        )
        self.duration_value.pack(side="right", padx=(10, 0))
        
        self.duration_slider.configure(command=self._update_duration)
        
        # API Key input
        api_label = ctk.CTkLabel(
            parent,
            text="API Key (optional):",
            font=("Arial", 12),
            text_color=self.colors["text_dim"]
        )
        api_label.pack(anchor="w", pady=(10, 5))
        
        self.api_entry = ctk.CTkEntry(
            parent,
            placeholder_text="sk-...",
            height=35,
            show="*",
            fg_color=self.colors["sidebar"],
            border_color=self.colors["accent"],
            border_width=1
        )
        self.api_entry.pack(fill="x", pady=(0, 10))
        
        # Options
        options_label = ctk.CTkLabel(
            parent,
            text="Options:",
            font=("Arial", 12),
            text_color=self.colors["text_dim"]
        )
        options_label.pack(anchor="w", pady=(10, 5))
        
        self.auto_detect = ctk.CTkCheckBox(
            parent,
            text="Auto-detect questions",
            fg_color=self.colors["accent"],
            hover_color="#3a8eef",
            text_color=self.colors["text"]
        )
        self.auto_detect.pack(anchor="w", pady=2)
        self.auto_detect.select()
        
        self.sound_enabled = ctk.CTkCheckBox(
            parent,
            text="Sound notifications",
            fg_color=self.colors["accent"],
            hover_color="#3a8eef",
            text_color=self.colors["text"]
        )
        self.sound_enabled.pack(anchor="w", pady=2)
    
    def _create_stats_section(self, parent):
        """Create statistics section"""
        # Title
        title = ctk.CTkLabel(
            parent,
            text="Statistics",
            font=("Arial", 18, "bold"),
            text_color=self.colors["text"]
        )
        title.pack(anchor="w", pady=(0, 15))
        
        # Stats grid
        stats = [
            ("Questions Detected", "0"),
            ("Questions Answered", "0"),
            ("Success Rate", "0%"),
            ("Average Time", "0s"),
            ("Current Session", "00:00:00"),
            ("Total Sessions", "0")
        ]
        
        self.stat_labels = {}
        
        for label, value in stats:
            stat_frame = ctk.CTkFrame(parent, fg_color=self.colors["sidebar"], corner_radius=8)
            stat_frame.pack(fill="x", pady=5)
            
            label_widget = ctk.CTkLabel(
                stat_frame,
                text=label,
                font=("Arial", 11),
                text_color=self.colors["text_dim"]
            )
            label_widget.pack(side="left", padx=15, pady=10)
            
            value_widget = ctk.CTkLabel(
                stat_frame,
                text=value,
                font=("Arial", 12, "bold"),
                text_color=self.colors["accent"]
            )
            value_widget.pack(side="right", padx=15, pady=10)
            
            self.stat_labels[label] = value_widget
    
    def _create_activity_log(self, parent):
        """Create activity log section"""
        # Log frame
        log_frame = ctk.CTkFrame(parent, fg_color=self.colors["card"], height=150, corner_radius=10)
        log_frame.pack(fill="x", pady=(10, 0))
        log_frame.pack_propagate(False)
        
        # Title
        log_title = ctk.CTkLabel(
            log_frame,
            text="Activity Log",
            font=("Arial", 14, "bold"),
            text_color=self.colors["text"]
        )
        log_title.pack(anchor="w", padx=20, pady=(10, 5))
        
        # Log text area
        self.log_text = ctk.CTkTextbox(
            log_frame,
            height=100,
            fg_color=self.colors["sidebar"],
            text_color=self.colors["text_dim"],
            font=("Consolas", 10)
        )
        self.log_text.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        self.log_text.insert("1.0", "Ready to start...\n")
        self.log_text.configure(state="disabled")
    
    def _update_duration(self, value):
        """Update duration label"""
        self.duration_value.configure(text=f"{int(value)} min")
    
    def _add_log(self, message):
        """Add message to activity log"""
        self.log_text.configure(state="normal")
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
    
    def _start_service(self):
        """Start the service"""
        if self.is_running:
            return
        
        try:
            # Update config
            self.config.set('context', self.context_entry.get() or "General")
            self.config.set('duration_minutes', int(self.duration_slider.get()))
            if self.api_entry.get():
                self.config.set('api_key', self.api_entry.get())
            
            # Start service
            self.service_manager = ServiceManager()
            self.service_manager.config = self.config
            
            # Start in thread
            thread = threading.Thread(target=self.service_manager.start)
            thread.daemon = True
            thread.start()
            
            # Update UI
            self.is_running = True
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            self.status_dot.configure(text_color=self.colors["success"])
            self.status_label.configure(text="Running")
            
            self._add_log("Service started successfully")
            
            # Start timer update
            self._update_timer()
            
        except Exception as e:
            self._add_log(f"Error starting service: {str(e)}")
            self.status_dot.configure(text_color=self.colors["error"])
            self.status_label.configure(text="Error")
    
    def _stop_service(self):
        """Stop the service"""
        if not self.is_running:
            return
        
        try:
            if self.service_manager:
                self.service_manager.running = False
                self.service_manager.stop()
                self.service_manager = None
            
            # Update UI
            self.is_running = False
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            self.status_dot.configure(text_color=self.colors["text_dim"])
            self.status_label.configure(text="Ready")
            self.time_label.configure(text="")
            
            self._add_log("Service stopped")
            
        except Exception as e:
            self._add_log(f"Error stopping service: {str(e)}")
    
    def _update_timer(self):
        """Update timer display"""
        if self.is_running and self.service_manager:
            if self.service_manager.start_time:
                elapsed = time.time() - self.service_manager.start_time.timestamp()
                hours = int(elapsed // 3600)
                minutes = int((elapsed % 3600) // 60)
                seconds = int(elapsed % 60)
                
                self.time_label.configure(text=f"Elapsed: {hours:02d}:{minutes:02d}:{seconds:02d}")
                
                # Update session time stat
                self.stat_labels["Current Session"].configure(
                    text=f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                )
            
            # Schedule next update
            self.after(1000, self._update_timer)
    
    def _on_closing(self):
        """Handle window closing"""
        if self.is_running:
            self._stop_service()
        self.destroy()


if __name__ == "__main__":
    app = SimpleAssistant()
    app.mainloop()