"""System tray integration for background operation"""
import pystray
from PIL import Image, ImageDraw
import threading
from typing import Optional, Callable

class SystemTray:
    """System tray icon with menu"""
    
    def __init__(self, app_window, service_manager):
        self.app_window = app_window
        self.service_manager = service_manager
        self.icon = None
        self.running = False
        
        # Create icon image
        self.icon_image = self._create_icon_image()
        
        # Create system tray icon
        self._create_tray_icon()
    
    def _create_icon_image(self, size=64, color="#0d7377"):
        """Create icon image"""
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw a circle with Q
        draw.ellipse([2, 2, size-2, size-2], fill=color)
        
        # Draw Q letter (simplified)
        draw.ellipse([size//4, size//4, 3*size//4, 3*size//4], 
                    fill=(255, 255, 255, 255))
        draw.ellipse([3*size//8, 3*size//8, 5*size//8, 5*size//8], 
                    fill=color)
        
        # Draw tail of Q
        draw.rectangle([size//2, size//2, 3*size//4, 3*size//4], 
                      fill=(255, 255, 255, 255))
        
        return image
    
    def _create_tray_icon(self):
        """Create the system tray icon"""
        menu = pystray.Menu(
            pystray.MenuItem("Show", self._show_window),
            pystray.MenuItem("Hide", self._hide_window),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Start Service", self._start_service),
            pystray.MenuItem("Stop Service", self._stop_service),
            pystray.MenuItem("Pause Service", self._pause_service),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Statistics", self._show_stats),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self._quit_app)
        )
        
        self.icon = pystray.Icon(
            "QuestionAssistant",
            self.icon_image,
            "Question Assistant - Click to show",
            menu
        )
    
    def start(self):
        """Start system tray icon"""
        if not self.running:
            self.running = True
            thread = threading.Thread(target=self._run)
            thread.daemon = True
            thread.start()
    
    def _run(self):
        """Run system tray icon"""
        self.icon.run()
    
    def stop(self):
        """Stop system tray icon"""
        if self.running and self.icon:
            self.running = False
            self.icon.stop()
    
    def _show_window(self, icon, item):
        """Show main window"""
        self.app_window.root.deiconify()
        self.app_window.root.lift()
    
    def _hide_window(self, icon, item):
        """Hide main window"""
        self.app_window.root.withdraw()
    
    def _start_service(self, icon, item):
        """Start service from tray"""
        if self.service_manager:
            self.service_manager.start()
            self._update_icon_status("running")
    
    def _stop_service(self, icon, item):
        """Stop service from tray"""
        if self.service_manager:
            self.service_manager.stop()
            self._update_icon_status("stopped")
    
    def _pause_service(self, icon, item):
        """Pause service from tray"""
        if self.service_manager:
            self.service_manager.pause()
            self._update_icon_status("paused")
    
    def _show_stats(self, icon, item):
        """Show statistics window"""
        # Show main window and switch to stats tab
        self._show_window(icon, item)
        if hasattr(self.app_window, 'notebook'):
            # Switch to statistics tab
            for i, tab in enumerate(self.app_window.notebook.tabs()):
                if "Statistics" in self.app_window.notebook.tab(tab, "text"):
                    self.app_window.notebook.select(i)
                    break
    
    def _quit_app(self, icon, item):
        """Quit application"""
        self.stop()
        if self.service_manager and self.service_manager.running:
            self.service_manager.stop()
        self.app_window.root.quit()
    
    def _update_icon_status(self, status):
        """Update icon based on status"""
        colors = {
            "running": "#27ae60",  # Green
            "paused": "#f39c12",   # Orange
            "stopped": "#e74c3c"   # Red
        }
        
        color = colors.get(status, "#0d7377")
        self.icon_image = self._create_icon_image(color=color)
        
        if self.icon:
            self.icon.icon = self.icon_image
    
    def show_notification(self, title, message):
        """Show system notification"""
        if self.icon:
            self.icon.notify(message, title)