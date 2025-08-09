"""Modern theme system for the application"""
from typing import Dict, Any
import json
from pathlib import Path

class ThemeManager:
    """Manages application themes and styling"""
    
    # Ultra-modern color schemes with glassmorphism support
    THEMES = {
        "dark": {
            "bg": "#0a0a0f",
            "bg_secondary": "#12121a",
            "bg_tertiary": "#1a1a25",
            "fg": "#ffffff",
            "fg_secondary": "#a8a8b8",
            "fg_tertiary": "#787886",
            "accent": "#6366f1",
            "accent_hover": "#818cf8",
            "success": "#10b981",
            "warning": "#f59e0b",
            "error": "#ef4444",
            "border": "#2a2a3e",
            "input_bg": "#16161e",
            "input_border": "#2a2a3e",
            "button_bg": "#1e1e2e",
            "button_fg": "#ffffff",
            "button_hover": "#2a2a3e",
            "disabled": "#4a4a5e",
            "chart_colors": ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"],
            "gradient_start": "#6366f1",
            "gradient_end": "#8b5cf6",
            "glass_bg": "rgba(18, 18, 26, 0.7)",
            "shadow_light": "rgba(99, 102, 241, 0.1)",
            "shadow_dark": "rgba(0, 0, 0, 0.3)",
            "glow": "#6366f1"
        },
        "light": {
            "bg": "#ffffff",
            "bg_secondary": "#f5f5f5",
            "bg_tertiary": "#e8e8e8",
            "fg": "#2c3e50",
            "fg_secondary": "#555555",
            "fg_tertiary": "#777777",
            "accent": "#3498db",
            "accent_hover": "#2980b9",
            "success": "#2ecc71",
            "warning": "#f1c40f",
            "error": "#e74c3c",
            "border": "#dcdcdc",
            "input_bg": "#ffffff",
            "input_border": "#dcdcdc",
            "button_bg": "#3498db",
            "button_fg": "#ffffff",
            "button_hover": "#2980b9",
            "disabled": "#cccccc",
            "chart_colors": ["#3498db", "#2ecc71", "#f1c40f", "#e74c3c", "#9b59b6"],
            "gradient_start": "#3498db",
            "gradient_end": "#2980b9"
        },
        "midnight": {
            "bg": "#0f0f23",
            "bg_secondary": "#1a1a2e",
            "bg_tertiary": "#252542",
            "fg": "#eeeee4",
            "fg_secondary": "#ccccbc",
            "fg_tertiary": "#999989",
            "accent": "#f39c12",
            "accent_hover": "#e67e22",
            "success": "#00ff41",
            "warning": "#ffff00",
            "error": "#ff0040",
            "border": "#303050",
            "input_bg": "#1a1a2e",
            "input_border": "#303050",
            "button_bg": "#f39c12",
            "button_fg": "#0f0f23",
            "button_hover": "#e67e22",
            "disabled": "#555566",
            "chart_colors": ["#f39c12", "#00ff41", "#ffff00", "#ff0040", "#9966ff"],
            "gradient_start": "#f39c12",
            "gradient_end": "#e67e22"
        },
        "ocean": {
            "bg": "#0c2233",
            "bg_secondary": "#1a3a52",
            "bg_tertiary": "#2a5a7a",
            "fg": "#e0f2f1",
            "fg_secondary": "#b2dfdb",
            "fg_tertiary": "#80cbc4",
            "accent": "#00acc1",
            "accent_hover": "#00bcd4",
            "success": "#4caf50",
            "warning": "#ff9800",
            "error": "#f44336",
            "border": "#1e4d6b",
            "input_bg": "#1a3a52",
            "input_border": "#1e4d6b",
            "button_bg": "#00acc1",
            "button_fg": "#ffffff",
            "button_hover": "#00bcd4",
            "disabled": "#4a6b82",
            "chart_colors": ["#00acc1", "#4caf50", "#ff9800", "#f44336", "#7c4dff"],
            "gradient_start": "#00acc1",
            "gradient_end": "#00bcd4"
        }
    }
    
    # Font configurations
    FONTS = {
        "heading_xl": ("Segoe UI", 24, "bold"),
        "heading_lg": ("Segoe UI", 18, "bold"),
        "heading": ("Segoe UI", 14, "bold"),
        "subheading": ("Segoe UI", 12, "normal"),
        "body": ("Segoe UI", 11, "normal"),
        "body_small": ("Segoe UI", 10, "normal"),
        "mono": ("Consolas", 10, "normal"),
        "button": ("Segoe UI", 11, "normal"),
        "status": ("Segoe UI", 9, "normal")
    }
    
    # Animation settings
    ANIMATIONS = {
        "transition_duration": 200,  # milliseconds
        "hover_delay": 50,
        "fade_steps": 10,
        "slide_distance": 20,
        "bounce_height": 5,
        "pulse_scale": 1.05
    }
    
    def __init__(self):
        self.current_theme = "dark"
        self.custom_themes = self._load_custom_themes()
    
    def _load_custom_themes(self) -> Dict:
        """Load custom themes from file"""
        theme_file = Path("config/custom_themes.json")
        if theme_file.exists():
            try:
                with open(theme_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def get_theme(self, theme_name: str = None) -> Dict[str, Any]:
        """Get theme configuration"""
        if theme_name is None:
            theme_name = self.current_theme
        
        if theme_name in self.custom_themes:
            return self.custom_themes[theme_name]
        
        return self.THEMES.get(theme_name, self.THEMES["dark"])
    
    def set_theme(self, theme_name: str):
        """Set current theme"""
        if theme_name in self.THEMES or theme_name in self.custom_themes:
            self.current_theme = theme_name
            return True
        return False
    
    def get_font(self, font_type: str) -> tuple:
        """Get font configuration"""
        return self.FONTS.get(font_type, self.FONTS["body"])
    
    def get_animation(self, animation_type: str) -> int:
        """Get animation setting"""
        return self.ANIMATIONS.get(animation_type, 200)
    
    def save_custom_theme(self, name: str, theme: Dict):
        """Save a custom theme"""
        self.custom_themes[name] = theme
        theme_file = Path("config/custom_themes.json")
        theme_file.parent.mkdir(exist_ok=True)
        
        with open(theme_file, 'w') as f:
            json.dump(self.custom_themes, f, indent=2)
    
    def get_gradient(self, steps: int = 10) -> list:
        """Generate gradient colors for current theme"""
        theme = self.get_theme()
        start = theme["gradient_start"]
        end = theme["gradient_end"]
        
        # Convert hex to RGB
        start_rgb = tuple(int(start[i:i+2], 16) for i in (1, 3, 5))
        end_rgb = tuple(int(end[i:i+2], 16) for i in (1, 3, 5))
        
        # Generate gradient
        colors = []
        for i in range(steps):
            t = i / (steps - 1) if steps > 1 else 0
            r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * t)
            g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * t)
            b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * t)
            colors.append(f"#{r:02x}{g:02x}{b:02x}")
        
        return colors

# Global theme manager instance
theme_manager = ThemeManager()