"""Custom widgets with modern styling and animations"""
import tkinter as tk
from tkinter import ttk, Canvas
import customtkinter as ctk
from typing import Optional, Callable, List, Tuple
import math
from src.gui_components.themes import theme_manager

class AnimatedButton(ctk.CTkButton):
    """Button with hover animations and ripple effect"""
    
    def __init__(self, parent, text="", command=None, **kwargs):
        theme = theme_manager.get_theme()
        
        super().__init__(
            parent,
            text=text,
            command=command,
            fg_color=theme["button_bg"],
            hover_color=theme["button_hover"],
            text_color=theme["button_fg"],
            font=theme_manager.get_font("button"),
            corner_radius=8,
            **kwargs
        )
        
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
    
    def _on_enter(self, event):
        """Hover enter animation"""
        self.configure(cursor="hand2")
        self._animate_scale(1.02)
    
    def _on_leave(self, event):
        """Hover leave animation"""
        self._animate_scale(1.0)
    
    def _on_click(self, event):
        """Click animation"""
        self._animate_scale(0.98)
        self.after(100, lambda: self._animate_scale(1.0))
    
    def _animate_scale(self, scale):
        """Simple scale animation"""
        # This is a placeholder - actual scaling would require canvas
        pass

class GlowingEntry(ctk.CTkEntry):
    """Entry field with glowing border on focus"""
    
    def __init__(self, parent, **kwargs):
        theme = theme_manager.get_theme()
        
        super().__init__(
            parent,
            fg_color=theme["input_bg"],
            border_color=theme["input_border"],
            text_color=theme["fg"],
            font=theme_manager.get_font("body"),
            corner_radius=6,
            **kwargs
        )
        
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
    
    def _on_focus_in(self, event):
        """Add glow effect on focus"""
        theme = theme_manager.get_theme()
        self.configure(border_color=theme["accent"])
        self.configure(border_width=2)
    
    def _on_focus_out(self, event):
        """Remove glow effect on focus out"""
        theme = theme_manager.get_theme()
        self.configure(border_color=theme["input_border"])
        self.configure(border_width=1)

class CircularProgress(Canvas):
    """Circular progress indicator with animation"""
    
    def __init__(self, parent, size=100, width=10, **kwargs):
        theme = theme_manager.get_theme()
        
        super().__init__(
            parent,
            width=size,
            height=size,
            bg=theme["bg"],
            highlightthickness=0,
            **kwargs
        )
        
        self.size = size
        self.width = width
        self.progress = 0
        self.arc = None
        self.text = None
        
        self._draw_background()
        self._update_progress()
    
    def _draw_background(self):
        """Draw background circle"""
        theme = theme_manager.get_theme()
        padding = self.width / 2
        
        self.create_oval(
            padding, padding,
            self.size - padding, self.size - padding,
            outline=theme["bg_tertiary"],
            width=self.width
        )
    
    def _update_progress(self):
        """Update progress arc"""
        theme = theme_manager.get_theme()
        padding = self.width / 2
        
        if self.arc:
            self.delete(self.arc)
        if self.text:
            self.delete(self.text)
        
        # Draw progress arc
        extent = -360 * self.progress
        self.arc = self.create_arc(
            padding, padding,
            self.size - padding, self.size - padding,
            start=90,
            extent=extent,
            outline=theme["accent"],
            width=self.width,
            style="arc"
        )
        
        # Draw percentage text
        self.text = self.create_text(
            self.size / 2, self.size / 2,
            text=f"{int(self.progress * 100)}%",
            fill=theme["fg"],
            font=theme_manager.get_font("heading")
        )
    
    def set_progress(self, value: float, animate: bool = True):
        """Set progress value with optional animation"""
        target = max(0, min(1, value))
        
        if animate:
            steps = 20
            delta = (target - self.progress) / steps
            
            def animate_step(step):
                if step < steps:
                    self.progress += delta
                    self._update_progress()
                    self.after(20, lambda: animate_step(step + 1))
                else:
                    self.progress = target
                    self._update_progress()
            
            animate_step(0)
        else:
            self.progress = target
            self._update_progress()

class ModernCard(ctk.CTkFrame):
    """Card component with shadow and hover effects"""
    
    def __init__(self, parent, title="", content="", **kwargs):
        theme = theme_manager.get_theme()
        
        super().__init__(
            parent,
            fg_color=theme["bg_secondary"],
            corner_radius=12,
            **kwargs
        )
        
        # Title
        if title:
            title_label = ctk.CTkLabel(
                self,
                text=title,
                font=theme_manager.get_font("heading"),
                text_color=theme["fg"]
            )
            title_label.pack(anchor="w", padx=15, pady=(15, 5))
        
        # Content
        if content:
            content_label = ctk.CTkLabel(
                self,
                text=content,
                font=theme_manager.get_font("body"),
                text_color=theme["fg_secondary"],
                justify="left"
            )
            content_label.pack(anchor="w", padx=15, pady=(5, 15))
        
        # Hover effect
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
    
    def _on_enter(self, event):
        """Hover enter effect"""
        theme = theme_manager.get_theme()
        self.configure(fg_color=theme["bg_tertiary"])
    
    def _on_leave(self, event):
        """Hover leave effect"""
        theme = theme_manager.get_theme()
        self.configure(fg_color=theme["bg_secondary"])

class StatusIndicator(Canvas):
    """Animated status indicator dot"""
    
    def __init__(self, parent, size=12, status="offline", **kwargs):
        theme = theme_manager.get_theme()
        
        super().__init__(
            parent,
            width=size,
            height=size,
            bg=theme["bg"],
            highlightthickness=0,
            **kwargs
        )
        
        self.size = size
        self.status = status
        self.dot = None
        self.pulse_animation = None
        
        self._update_status()
    
    def _update_status(self):
        """Update status indicator"""
        theme = theme_manager.get_theme()
        
        if self.dot:
            self.delete(self.dot)
        
        colors = {
            "online": theme["success"],
            "busy": theme["warning"],
            "error": theme["error"],
            "offline": theme["disabled"]
        }
        
        color = colors.get(self.status, theme["disabled"])
        
        # Draw dot
        padding = 2
        self.dot = self.create_oval(
            padding, padding,
            self.size - padding, self.size - padding,
            fill=color,
            outline=""
        )
        
        # Start pulse animation for active states
        if self.status in ["online", "busy"]:
            self._start_pulse()
        else:
            self._stop_pulse()
    
    def _start_pulse(self):
        """Start pulse animation"""
        if self.pulse_animation:
            return
        
        def pulse():
            if not self.pulse_animation:
                return
            
            # Create pulse effect
            current_size = self.coords(self.dot)
            if current_size:
                # Expand
                self.coords(self.dot, 0, 0, self.size, self.size)
                self.after(500, lambda: self.coords(self.dot, 2, 2, self.size-2, self.size-2))
            
            self.pulse_animation = self.after(1000, pulse)
        
        self.pulse_animation = self.after(100, pulse)
    
    def _stop_pulse(self):
        """Stop pulse animation"""
        if self.pulse_animation:
            self.after_cancel(self.pulse_animation)
            self.pulse_animation = None
    
    def set_status(self, status: str):
        """Set status"""
        self.status = status
        self._update_status()

class ToggleSwitch(Canvas):
    """Modern toggle switch"""
    
    def __init__(self, parent, command: Optional[Callable] = None, 
                 width=50, height=25, **kwargs):
        theme = theme_manager.get_theme()
        
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=theme["bg"],
            highlightthickness=0,
            **kwargs
        )
        
        self.width = width
        self.height = height
        self.command = command
        self.state = False
        
        self._draw_switch()
        self.bind("<Button-1>", self._toggle)
    
    def _draw_switch(self):
        """Draw the switch"""
        theme = theme_manager.get_theme()
        self.delete("all")
        
        # Background
        bg_color = theme["accent"] if self.state else theme["bg_tertiary"]
        self.create_rounded_rectangle(
            0, 0, self.width, self.height,
            radius=self.height/2,
            fill=bg_color,
            outline=""
        )
        
        # Knob
        knob_x = self.width - self.height + 2 if self.state else 2
        self.create_oval(
            knob_x, 2,
            knob_x + self.height - 4, self.height - 2,
            fill=theme["bg"],
            outline=""
        )
    
    def create_rounded_rectangle(self, x1, y1, x2, y2, radius=10, **kwargs):
        """Create rounded rectangle"""
        points = []
        for x, y in [(x1, y1 + radius), (x1, y2 - radius), 
                     (x1 + radius, y2), (x2 - radius, y2),
                     (x2, y2 - radius), (x2, y1 + radius),
                     (x2 - radius, y1), (x1 + radius, y1)]:
            points.extend([x, y])
        
        return self.create_polygon(points, smooth=True, **kwargs)
    
    def _toggle(self, event=None):
        """Toggle the switch"""
        self.state = not self.state
        self._animate_toggle()
        
        if self.command:
            self.command(self.state)
    
    def _animate_toggle(self):
        """Animate toggle transition"""
        self._draw_switch()
    
    def set_state(self, state: bool):
        """Set switch state"""
        self.state = state
        self._draw_switch()

class NotificationToast(tk.Toplevel):
    """Toast notification popup"""
    
    def __init__(self, parent, message: str, toast_type: str = "info", 
                 duration: int = 3000):
        super().__init__(parent)
        
        theme = theme_manager.get_theme()
        
        # Window setup
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.9)
        
        # Style based on type
        colors = {
            "info": theme["accent"],
            "success": theme["success"],
            "warning": theme["warning"],
            "error": theme["error"]
        }
        
        bg_color = colors.get(toast_type, theme["accent"])
        
        # Frame
        frame = tk.Frame(self, bg=bg_color, padx=15, pady=10)
        frame.pack()
        
        # Icon
        icons = {
            "info": "ℹ",
            "success": "✓",
            "warning": "⚠",
            "error": "✕"
        }
        
        icon_label = tk.Label(
            frame,
            text=icons.get(toast_type, "ℹ"),
            font=("Segoe UI", 14),
            bg=bg_color,
            fg="white"
        )
        icon_label.pack(side="left", padx=(0, 10))
        
        # Message
        msg_label = tk.Label(
            frame,
            text=message,
            font=theme_manager.get_font("body"),
            bg=bg_color,
            fg="white"
        )
        msg_label.pack(side="left")
        
        # Position
        self.update_idletasks()
        x = parent.winfo_x() + parent.winfo_width() - self.winfo_width() - 20
        y = parent.winfo_y() + 50
        self.geometry(f"+{x}+{y}")
        
        # Auto close
        self.after(duration, self.destroy)
        
        # Fade in animation
        self._fade_in()
    
    def _fade_in(self):
        """Fade in animation"""
        alpha = 0
        
        def fade():
            nonlocal alpha
            if alpha < 0.9:
                alpha += 0.1
                self.attributes("-alpha", alpha)
                self.after(20, fade)
        
        fade()

class SearchBar(ctk.CTkFrame):
    """Modern search bar with suggestions"""
    
    def __init__(self, parent, placeholder="Search...", command=None, **kwargs):
        theme = theme_manager.get_theme()
        
        super().__init__(
            parent,
            fg_color=theme["bg_secondary"],
            corner_radius=20,
            **kwargs
        )
        
        self.command = command
        
        # Search icon
        icon_label = ctk.CTkLabel(
            self,
            text="🔍",
            font=("Segoe UI", 14),
            text_color=theme["fg_secondary"]
        )
        icon_label.pack(side="left", padx=(10, 5))
        
        # Entry
        self.entry = ctk.CTkEntry(
            self,
            placeholder_text=placeholder,
            border_width=0,
            fg_color=theme["bg_secondary"],
            text_color=theme["fg"],
            font=theme_manager.get_font("body")
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.entry.bind("<Return>", self._on_search)
        self.entry.bind("<KeyRelease>", self._on_type)
    
    def _on_search(self, event=None):
        """Handle search"""
        if self.command:
            self.command(self.entry.get())
    
    def _on_type(self, event=None):
        """Handle typing for suggestions"""
        # Could implement suggestions here
        pass