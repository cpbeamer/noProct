"""Ultra-modern UI widgets with advanced animations and effects"""
import tkinter as tk
from tkinter import Canvas, Frame
import customtkinter as ctk
from typing import Optional, Callable, Union, Tuple, List
import math
import time
import threading
from PIL import Image, ImageDraw, ImageFilter, ImageTk
import colorsys
from src.gui_components.themes import theme_manager


class GlassmorphicCard(ctk.CTkFrame):
    """Glass-morphic card with blur effect and gradient borders"""
    
    def __init__(self, parent, **kwargs):
        theme = theme_manager.get_theme()
        
        super().__init__(
            parent,
            fg_color=theme["bg_secondary"],
            corner_radius=20,
            border_width=1,
            border_color=theme["accent"],
            **kwargs
        )
        
        # Add subtle animation on hover
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
        # Glass effect overlay
        self.overlay = None
        self._create_glass_effect()
    
    def _hex_to_rgb(self, hex_color):
        """Convert hex to RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _create_glass_effect(self):
        """Create glass morphism effect"""
        self.configure(bg_color=["#1a1a2e", "#0f0f1e"])
        
    def _on_enter(self, event):
        """Hover enter effect"""
        self.configure(border_width=2)
        
    def _on_leave(self, event):
        """Hover leave effect"""
        self.configure(border_width=1)


class NeumorphicButton(ctk.CTkButton):
    """Neumorphic button with soft shadows and depth"""
    
    def __init__(self, parent, text="", command=None, style="raised", **kwargs):
        theme = theme_manager.get_theme()
        
        # Setup colors for neumorphism
        self.bg_color = theme["bg_secondary"]
        self.style = style
        
        super().__init__(
            parent,
            text=text,
            command=self._wrapped_command(command),
            fg_color=self.bg_color,
            hover_color=self._adjust_brightness(self.bg_color, 1.1),
            text_color=theme["fg"],
            font=theme_manager.get_font("button"),
            corner_radius=15,
            border_width=0,
            **kwargs
        )
        
        # Add shadow effects
        self._apply_shadows()
        
        # Bind interactions
        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
    
    def _wrapped_command(self, command):
        """Wrap command with animation"""
        def wrapper():
            self._animate_press()
            if command:
                command()
        return wrapper
    
    def _adjust_brightness(self, hex_color, factor):
        """Adjust color brightness"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        h, l, s = colorsys.rgb_to_hls(*[x/255.0 for x in rgb])
        l = max(0, min(1, l * factor))
        rgb = colorsys.hls_to_rgb(h, l, s)
        return '#{:02x}{:02x}{:02x}'.format(*[int(x*255) for x in rgb])
    
    def _apply_shadows(self):
        """Apply neumorphic shadows"""
        if self.style == "raised":
            # Light shadow on top-left, dark shadow on bottom-right
            self.configure(border_width=0)
        else:
            # Inset style
            self.configure(border_width=1)
    
    def _on_press(self, event):
        """Button press effect"""
        self.style = "inset"
        self._apply_shadows()
        
    def _on_release(self, event):
        """Button release effect"""
        self.style = "raised"
        self._apply_shadows()
    
    def _animate_press(self):
        """Animate button press"""
        self.configure(corner_radius=12)
        self.after(100, lambda: self.configure(corner_radius=15))


class AnimatedProgressBar(ctk.CTkFrame):
    """Modern animated progress bar with gradient fill"""
    
    def __init__(self, parent, width=400, height=8, **kwargs):
        super().__init__(parent, width=width, height=height, **kwargs)
        
        theme = theme_manager.get_theme()
        self.theme = theme
        
        # Create canvas for custom drawing
        self.canvas = Canvas(
            self,
            width=width,
            height=height,
            bg=theme["bg_secondary"],
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        
        self.width = width
        self.height = height
        self.progress = 0
        self.target_progress = 0
        self.animation_speed = 0.02
        
        # Gradient colors
        self.gradient_start = theme["accent"]
        self.gradient_end = theme["success"]
        
        self._draw_background()
        self._animate()
    
    def _draw_background(self):
        """Draw background track"""
        self.canvas.create_rectangle(
            0, 0, self.width, self.height,
            fill=self.theme["bg_tertiary"],
            outline=""
        )
    
    def set_progress(self, value: float):
        """Set progress value (0-100)"""
        self.target_progress = max(0, min(100, value))
    
    def _animate(self):
        """Animate progress bar"""
        if abs(self.progress - self.target_progress) > 0.1:
            # Smooth animation
            diff = self.target_progress - self.progress
            self.progress += diff * self.animation_speed
            
            # Redraw progress
            self._draw_progress()
        
        # Continue animation
        self.after(16, self._animate)  # ~60 FPS
    
    def _draw_progress(self):
        """Draw progress with gradient"""
        self.canvas.delete("progress")
        
        if self.progress > 0:
            fill_width = int((self.progress / 100) * self.width)
            
            # Create gradient effect
            for i in range(fill_width):
                ratio = i / max(1, fill_width)
                color = self._interpolate_color(
                    self.gradient_start,
                    self.gradient_end,
                    ratio
                )
                
                self.canvas.create_line(
                    i, 0, i, self.height,
                    fill=color,
                    tags="progress"
                )
            
            # Add glow effect
            glow_color = self._adjust_brightness(self.gradient_end, 1.3)
            self.canvas.create_oval(
                fill_width - 10, -5,
                fill_width + 10, self.height + 5,
                fill=glow_color,
                outline="",
                tags="progress"
            )
    
    def _interpolate_color(self, color1, color2, ratio):
        """Interpolate between two colors"""
        c1 = self._hex_to_rgb(color1)
        c2 = self._hex_to_rgb(color2)
        
        r = int(c1[0] + (c2[0] - c1[0]) * ratio)
        g = int(c1[1] + (c2[1] - c1[1]) * ratio)
        b = int(c1[2] + (c2[2] - c1[2]) * ratio)
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _hex_to_rgb(self, hex_color):
        """Convert hex to RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _adjust_brightness(self, hex_color, factor):
        """Adjust color brightness"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        h, l, s = colorsys.rgb_to_hls(*[x/255.0 for x in rgb])
        l = max(0, min(1, l * factor))
        rgb = colorsys.hls_to_rgb(h, l, s)
        return '#{:02x}{:02x}{:02x}'.format(*[int(x*255) for x in rgb])


class FloatingActionButton(ctk.CTkButton):
    """Material Design floating action button with ripple effect"""
    
    def __init__(self, parent, icon="➕", command=None, size=56, **kwargs):
        theme = theme_manager.get_theme()
        
        super().__init__(
            parent,
            text=icon,
            command=command,
            width=size,
            height=size,
            corner_radius=size//2,
            fg_color=theme["accent"],
            hover_color=self._adjust_brightness(theme["accent"], 1.2),
            text_color="white",
            font=("Segoe UI", size//3),
            **kwargs
        )
        
        # Shadow effect
        self.configure(border_width=0)
        
        # Bind animations
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        
        # Store original position for animation
        self.original_size = size
    
    def _adjust_brightness(self, hex_color, factor):
        """Adjust color brightness"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        h, l, s = colorsys.rgb_to_hls(*[x/255.0 for x in rgb])
        l = max(0, min(1, l * factor))
        rgb = colorsys.hls_to_rgb(h, l, s)
        return '#{:02x}{:02x}{:02x}'.format(*[int(x*255) for x in rgb])
    
    def _on_enter(self, event):
        """Hover animation"""
        new_size = int(self.original_size * 1.1)
        self.configure(width=new_size, height=new_size)
    
    def _on_leave(self, event):
        """Leave animation"""
        self.configure(width=self.original_size, height=self.original_size)
    
    def _on_click(self, event):
        """Ripple effect on click"""
        self._animate_ripple()
    
    def _animate_ripple(self):
        """Create ripple animation"""
        # Scale down then up
        small_size = int(self.original_size * 0.9)
        self.configure(width=small_size, height=small_size)
        self.after(100, lambda: self.configure(
            width=self.original_size,
            height=self.original_size
        ))


class ModernSwitch(ctk.CTkSwitch):
    """iOS-style animated switch with smooth transitions"""
    
    def __init__(self, parent, text="", command=None, **kwargs):
        theme = theme_manager.get_theme()
        
        super().__init__(
            parent,
            text=text,
            command=command,
            progress_color=theme["success"],
            button_color="white",
            button_hover_color="#f0f0f0",
            fg_color=theme["bg_tertiary"],
            font=theme_manager.get_font("body"),
            **kwargs
        )
        
        # Smooth animation
        self.configure(switch_width=48, switch_height=24)


class AnimatedSidebar(ctk.CTkFrame):
    """Collapsible sidebar with smooth animations"""
    
    def __init__(self, parent, width=250, **kwargs):
        theme = theme_manager.get_theme()
        
        super().__init__(
            parent,
            width=width,
            fg_color=theme["bg_secondary"],
            **kwargs
        )
        
        self.width = width
        self.collapsed_width = 60
        self.is_collapsed = False
        self.animation_duration = 300  # ms
        self.animation_steps = 20
        
        # Prevent frame from shrinking
        self.pack_propagate(False)
        
        # Toggle button
        self.toggle_btn = ctk.CTkButton(
            self,
            text="☰",
            width=40,
            height=40,
            fg_color="transparent",
            hover_color=theme["bg_tertiary"],
            command=self.toggle
        )
        self.toggle_btn.pack(anchor="ne", padx=10, pady=10)
    
    def toggle(self):
        """Toggle sidebar collapse/expand"""
        if self.is_collapsed:
            self.expand()
        else:
            self.collapse()
    
    def collapse(self):
        """Animate sidebar collapse"""
        if not self.is_collapsed:
            self.is_collapsed = True
            self._animate_width(self.width, self.collapsed_width)
    
    def expand(self):
        """Animate sidebar expansion"""
        if self.is_collapsed:
            self.is_collapsed = False
            self._animate_width(self.collapsed_width, self.width)
    
    def _animate_width(self, start, end):
        """Animate width change"""
        step_size = (end - start) / self.animation_steps
        step_duration = self.animation_duration // self.animation_steps
        
        def animate_step(current_step):
            if current_step <= self.animation_steps:
                new_width = start + (step_size * current_step)
                self.configure(width=int(new_width))
                self.after(step_duration, lambda: animate_step(current_step + 1))
        
        animate_step(0)


class PulsingBadge(ctk.CTkLabel):
    """Notification badge with pulsing animation"""
    
    def __init__(self, parent, text="", size=20, **kwargs):
        theme = theme_manager.get_theme()
        
        super().__init__(
            parent,
            text=text,
            width=size,
            height=size,
            fg_color=theme["error"],
            text_color="white",
            corner_radius=size//2,
            font=("Segoe UI Bold", size//2),
            **kwargs
        )
        
        self.pulsing = False
        self.original_size = size
    
    def start_pulsing(self):
        """Start pulsing animation"""
        if not self.pulsing:
            self.pulsing = True
            self._pulse()
    
    def stop_pulsing(self):
        """Stop pulsing animation"""
        self.pulsing = False
    
    def _pulse(self):
        """Pulse animation"""
        if self.pulsing:
            # Scale up
            self.configure(
                width=int(self.original_size * 1.2),
                height=int(self.original_size * 1.2)
            )
            
            # Scale down after delay
            self.after(500, lambda: self.configure(
                width=self.original_size,
                height=self.original_size
            ))
            
            # Repeat
            self.after(1000, self._pulse)


class ModernTooltip:
    """Modern tooltip with fade animation"""
    
    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip = None
        self.show_timer = None
        
        # Bind events
        self.widget.bind("<Enter>", self._on_enter)
        self.widget.bind("<Leave>", self._on_leave)
        self.widget.bind("<Button-1>", self._on_leave)
    
    def _on_enter(self, event):
        """Show tooltip after delay"""
        self.show_timer = self.widget.after(self.delay, self._show_tooltip)
    
    def _on_leave(self, event):
        """Hide tooltip"""
        if self.show_timer:
            self.widget.after_cancel(self.show_timer)
            self.show_timer = None
        self._hide_tooltip()
    
    def _show_tooltip(self):
        """Display tooltip"""
        if self.tooltip:
            return
        
        theme = theme_manager.get_theme()
        
        # Create tooltip window
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        
        # Position near widget
        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        # Create tooltip content
        label = ctk.CTkLabel(
            self.tooltip,
            text=self.text,
            fg_color=theme["bg_tertiary"],
            text_color=theme["fg"],
            corner_radius=8,
            padx=10,
            pady=5
        )
        label.pack()
        
        # Fade in animation
        self.tooltip.attributes("-alpha", 0.0)
        self._fade_in()
    
    def _hide_tooltip(self):
        """Hide and destroy tooltip"""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
    
    def _fade_in(self):
        """Fade in animation"""
        if self.tooltip:
            alpha = self.tooltip.attributes("-alpha")
            if alpha < 0.9:
                self.tooltip.attributes("-alpha", alpha + 0.1)
                self.tooltip.after(20, self._fade_in)


class WaveLoader(ctk.CTkFrame):
    """Wave animation loader"""
    
    def __init__(self, parent, num_bars=5, **kwargs):
        super().__init__(parent, **kwargs)
        
        theme = theme_manager.get_theme()
        self.bars = []
        
        # Create animated bars
        for i in range(num_bars):
            bar = ctk.CTkFrame(
                self,
                width=8,
                height=30,
                fg_color=theme["accent"],
                corner_radius=4
            )
            bar.grid(row=0, column=i, padx=2)
            self.bars.append(bar)
        
        self.animating = False
    
    def start(self):
        """Start wave animation"""
        self.animating = True
        self._animate_wave(0)
    
    def stop(self):
        """Stop animation"""
        self.animating = False
    
    def _animate_wave(self, offset):
        """Animate bars in wave pattern"""
        if not self.animating:
            return
        
        for i, bar in enumerate(self.bars):
            # Calculate height based on sine wave
            angle = (offset + i * 30) % 360
            height = 15 + 15 * math.sin(math.radians(angle))
            bar.configure(height=int(height))
        
        # Continue animation
        self.after(50, lambda: self._animate_wave(offset + 10))


class GradientFrame(ctk.CTkFrame):
    """Frame with animated gradient background"""
    
    def __init__(self, parent, colors=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        if colors is None:
            theme = theme_manager.get_theme()
            colors = [theme["accent"], theme["success"]]
        
        self.colors = colors
        self.gradient_offset = 0
        
        # Create canvas for gradient
        self.canvas = Canvas(self, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # Start animation
        self._animate_gradient()
    
    def _create_gradient(self):
        """Create gradient effect"""
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        if width <= 1 or height <= 1:
            return
        
        self.canvas.delete("gradient")
        
        # Create gradient lines
        for i in range(width):
            ratio = (i + self.gradient_offset) % width / width
            color = self._interpolate_colors(ratio)
            
            self.canvas.create_line(
                i, 0, i, height,
                fill=color,
                tags="gradient"
            )
    
    def _interpolate_colors(self, ratio):
        """Interpolate between gradient colors"""
        # Simple two-color interpolation
        c1 = self._hex_to_rgb(self.colors[0])
        c2 = self._hex_to_rgb(self.colors[1])
        
        r = int(c1[0] + (c2[0] - c1[0]) * ratio)
        g = int(c1[1] + (c2[1] - c1[1]) * ratio)
        b = int(c1[2] + (c2[2] - c1[2]) * ratio)
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _hex_to_rgb(self, hex_color):
        """Convert hex to RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _animate_gradient(self):
        """Animate gradient movement"""
        self.gradient_offset = (self.gradient_offset + 1) % self.canvas.winfo_width()
        self._create_gradient()
        self.after(50, self._animate_gradient)