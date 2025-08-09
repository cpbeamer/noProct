"""Localized GUI components with multi-language support"""
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from src.localization.i18n import translator, Language, LocalizedFormatter, _
from src.gui_components.themes import theme_manager
from src.gui_components.custom_widgets import AnimatedButton, ModernCard
from typing import Dict, Callable

class LanguageSelector(ctk.CTkFrame):
    """Language selection widget"""
    
    def __init__(self, parent, on_change: Callable = None):
        super().__init__(parent, fg_color="transparent")
        
        self.on_change = on_change
        
        # Language label
        self.label = ctk.CTkLabel(
            self,
            text=_("label.language"),
            font=theme_manager.get_font("body")
        )
        self.label.pack(side="left", padx=(0, 10))
        
        # Language dropdown
        languages = translator.get_available_languages()
        self.language_var = tk.StringVar(value=translator.current_language.value)
        
        self.dropdown = ctk.CTkComboBox(
            self,
            values=[name for code, name in languages],
            variable=self.language_var,
            command=self._on_language_change,
            width=150
        )
        
        # Set current language display
        for code, name in languages:
            if code == translator.current_language.value:
                self.dropdown.set(name)
                break
        
        self.dropdown.pack(side="left")
    
    def _on_language_change(self, choice):
        """Handle language change"""
        # Find language code from name
        languages = translator.get_available_languages()
        for code, name in languages:
            if name == choice:
                # Set new language
                for lang in Language:
                    if lang.value == code:
                        translator.set_language(lang)
                        
                        # Trigger callback
                        if self.on_change:
                            self.on_change(lang)
                        
                        # Show notification
                        self._show_language_notification(lang)
                        break
                break
    
    def _show_language_notification(self, language: Language):
        """Show language change notification"""
        from src.gui_components.custom_widgets import NotificationToast
        
        # Get parent window
        parent = self.winfo_toplevel()
        
        # Show toast in new language
        message = _("message.language_changed")
        NotificationToast(parent, message, "info")

class LocalizedMenuBar(tk.Menu):
    """Menu bar with localization support"""
    
    def __init__(self, parent, commands: Dict[str, Callable]):
        super().__init__(parent)
        
        self.commands = commands
        self.menus = {}
        
        self._create_menus()
    
    def _create_menus(self):
        """Create localized menus"""
        # File menu
        file_menu = tk.Menu(self, tearoff=0)
        self.add_cascade(label=_("menu.file"), menu=file_menu)
        self.menus['file'] = file_menu
        
        file_menu.add_command(
            label=_("menu.new"),
            command=self.commands.get('new'),
            accelerator="Ctrl+N"
        )
        file_menu.add_command(
            label=_("menu.open"),
            command=self.commands.get('open'),
            accelerator="Ctrl+O"
        )
        file_menu.add_command(
            label=_("menu.save"),
            command=self.commands.get('save'),
            accelerator="Ctrl+S"
        )
        file_menu.add_separator()
        file_menu.add_command(
            label=_("menu.exit"),
            command=self.commands.get('exit'),
            accelerator="Alt+F4"
        )
        
        # Edit menu
        edit_menu = tk.Menu(self, tearoff=0)
        self.add_cascade(label=_("menu.edit"), menu=edit_menu)
        self.menus['edit'] = edit_menu
        
        edit_menu.add_command(
            label=_("menu.cut"),
            command=self.commands.get('cut'),
            accelerator="Ctrl+X"
        )
        edit_menu.add_command(
            label=_("menu.copy"),
            command=self.commands.get('copy'),
            accelerator="Ctrl+C"
        )
        edit_menu.add_command(
            label=_("menu.paste"),
            command=self.commands.get('paste'),
            accelerator="Ctrl+V"
        )
        
        # View menu
        view_menu = tk.Menu(self, tearoff=0)
        self.add_cascade(label=_("menu.view"), menu=view_menu)
        self.menus['view'] = view_menu
        
        view_menu.add_command(
            label=_("menu.dashboard"),
            command=self.commands.get('dashboard')
        )
        view_menu.add_command(
            label=_("menu.statistics"),
            command=self.commands.get('statistics')
        )
        view_menu.add_command(
            label=_("menu.logs"),
            command=self.commands.get('logs')
        )
        
        # Tools menu
        tools_menu = tk.Menu(self, tearoff=0)
        self.add_cascade(label=_("menu.tools"), menu=tools_menu)
        self.menus['tools'] = tools_menu
        
        tools_menu.add_command(
            label=_("menu.settings"),
            command=self.commands.get('settings'),
            accelerator="Ctrl+,"
        )
        tools_menu.add_command(
            label=_("menu.plugins"),
            command=self.commands.get('plugins')
        )
        
        # Help menu
        help_menu = tk.Menu(self, tearoff=0)
        self.add_cascade(label=_("menu.help"), menu=help_menu)
        self.menus['help'] = help_menu
        
        help_menu.add_command(
            label=_("menu.documentation"),
            command=self.commands.get('docs'),
            accelerator="F1"
        )
        help_menu.add_command(
            label=_("menu.about"),
            command=self.commands.get('about')
        )
    
    def refresh_labels(self):
        """Refresh menu labels after language change"""
        # Update cascade labels
        self.entryconfig(0, label=_("menu.file"))
        self.entryconfig(1, label=_("menu.edit"))
        self.entryconfig(2, label=_("menu.view"))
        self.entryconfig(3, label=_("menu.tools"))
        self.entryconfig(4, label=_("menu.help"))
        
        # Update menu items
        # This would need to track and update all menu items

class LocalizedDialog(ctk.CTkToplevel):
    """Base class for localized dialogs"""
    
    def __init__(self, parent, title_key: str):
        super().__init__(parent)
        
        self.title(_([title_key]))
        self.geometry("400x300")
        
        theme = theme_manager.get_theme()
        self.configure(fg_color=theme["bg"])
        
        # Center dialog
        self.transient(parent)
        self.grab_set()
        self._center_window()
    
    def _center_window(self):
        """Center dialog on parent"""
        self.update_idletasks()
        
        # Get parent position
        parent = self.master
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        # Calculate position
        width = self.winfo_width()
        height = self.winfo_height()
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        
        self.geometry(f"+{x}+{y}")

class LocalizedMessageBox:
    """Localized message box dialogs"""
    
    @staticmethod
    def show_info(parent, message_key: str, **kwargs):
        """Show information dialog"""
        messagebox.showinfo(
            _("dialog.info"),
            _(message_key, **kwargs)
        )
    
    @staticmethod
    def show_warning(parent, message_key: str, **kwargs):
        """Show warning dialog"""
        messagebox.showwarning(
            _("dialog.warning"),
            _(message_key, **kwargs)
        )
    
    @staticmethod
    def show_error(parent, message_key: str, **kwargs):
        """Show error dialog"""
        messagebox.showerror(
            _("dialog.error"),
            _(message_key, **kwargs)
        )
    
    @staticmethod
    def ask_yes_no(parent, message_key: str, **kwargs) -> bool:
        """Show yes/no dialog"""
        return messagebox.askyesno(
            _("dialog.confirm"),
            _(message_key, **kwargs)
        )

class LocalizedStatusBar(ctk.CTkFrame):
    """Status bar with localized messages"""
    
    def __init__(self, parent):
        super().__init__(parent, height=30)
        
        theme = theme_manager.get_theme()
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self,
            text=_("status.ready"),
            font=theme_manager.get_font("status"),
            anchor="w"
        )
        self.status_label.pack(side="left", padx=10, fill="x", expand=True)
        
        # Separator
        separator = ctk.CTkFrame(self, width=2, fg_color=theme["border"])
        separator.pack(side="left", fill="y", padx=5)
        
        # Language indicator
        self.language_label = ctk.CTkLabel(
            self,
            text=translator.current_language.value.upper(),
            font=theme_manager.get_font("status")
        )
        self.language_label.pack(side="left", padx=10)
        
        # Time display
        self.time_label = ctk.CTkLabel(
            self,
            text="",
            font=theme_manager.get_font("status")
        )
        self.time_label.pack(side="right", padx=10)
        
        self._update_time()
    
    def set_status(self, message_key: str, **kwargs):
        """Set status message"""
        self.status_label.configure(text=_(message_key, **kwargs))
    
    def _update_time(self):
        """Update time display"""
        from datetime import datetime
        
        # Format time according to language
        time_str = LocalizedFormatter.format_time(
            datetime.now(),
            translator.current_language
        )
        
        self.time_label.configure(text=time_str)
        
        # Schedule next update
        self.after(1000, self._update_time)
    
    def update_language(self):
        """Update after language change"""
        self.language_label.configure(
            text=translator.current_language.value.upper()
        )

class LocalizedSettingsPanel(ctk.CTkScrollableFrame):
    """Settings panel with localization"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        theme = theme_manager.get_theme()
        
        # Title
        title = ctk.CTkLabel(
            self,
            text=_("menu.settings"),
            font=theme_manager.get_font("heading_lg")
        )
        title.pack(pady=20)
        
        # Language section
        self._create_language_section()
        
        # Theme section
        self._create_theme_section()
        
        # ML section
        self._create_ml_section()
    
    def _create_language_section(self):
        """Create language settings section"""
        section = ModernCard(self)
        section.pack(fill="x", padx=20, pady=10)
        
        # Section title
        title = ctk.CTkLabel(
            section,
            text=_("settings.language_region"),
            font=theme_manager.get_font("heading")
        )
        title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # Language selector
        lang_selector = LanguageSelector(
            section,
            on_change=self._on_language_change
        )
        lang_selector.pack(padx=15, pady=10)
        
        # Date format preview
        from datetime import datetime
        date_preview = ctk.CTkLabel(
            section,
            text=f"{_('label.date_format')}: {LocalizedFormatter.format_date(datetime.now(), translator.current_language)}",
            font=theme_manager.get_font("body_small")
        )
        date_preview.pack(anchor="w", padx=15, pady=(5, 15))
    
    def _create_theme_section(self):
        """Create theme settings section"""
        section = ModernCard(self)
        section.pack(fill="x", padx=20, pady=10)
        
        title = ctk.CTkLabel(
            section,
            text=_("settings.appearance"),
            font=theme_manager.get_font("heading")
        )
        title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # Theme selector
        themes = ["Dark", "Light", "Midnight", "Ocean"]
        theme_var = tk.StringVar(value=theme_manager.current_theme)
        
        theme_dropdown = ctk.CTkComboBox(
            section,
            values=themes,
            variable=theme_var,
            command=self._on_theme_change
        )
        theme_dropdown.pack(padx=15, pady=(10, 15))
    
    def _create_ml_section(self):
        """Create ML settings section"""
        section = ModernCard(self)
        section.pack(fill="x", padx=20, pady=10)
        
        title = ctk.CTkLabel(
            section,
            text=_("settings.ml_detection"),
            font=theme_manager.get_font("heading")
        )
        title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # ML enable switch
        ml_frame = ctk.CTkFrame(section, fg_color="transparent")
        ml_frame.pack(fill="x", padx=15, pady=5)
        
        ml_label = ctk.CTkLabel(
            ml_frame,
            text=_("settings.enable_ml"),
            font=theme_manager.get_font("body")
        )
        ml_label.pack(side="left")
        
        from src.gui_components.custom_widgets import ToggleSwitch
        ml_switch = ToggleSwitch(ml_frame)
        ml_switch.pack(side="right", padx=15)
        ml_switch.set_state(True)
        
        # Active learning switch
        al_frame = ctk.CTkFrame(section, fg_color="transparent")
        al_frame.pack(fill="x", padx=15, pady=5)
        
        al_label = ctk.CTkLabel(
            al_frame,
            text=_("settings.active_learning"),
            font=theme_manager.get_font("body")
        )
        al_label.pack(side="left")
        
        al_switch = ToggleSwitch(al_frame)
        al_switch.pack(side="right", padx=15)
        al_switch.set_state(True)
        
        # Retrain button
        retrain_btn = AnimatedButton(
            section,
            text=_("button.retrain_models"),
            command=self._retrain_models
        )
        retrain_btn.pack(pady=(10, 15))
    
    def _on_language_change(self, language: Language):
        """Handle language change"""
        # Refresh all UI elements
        parent = self.winfo_toplevel()
        if hasattr(parent, 'refresh_ui'):
            parent.refresh_ui()
    
    def _on_theme_change(self, choice):
        """Handle theme change"""
        theme_manager.set_theme(choice.lower())
        LocalizedMessageBox.show_info(
            self,
            "message.restart_required"
        )
    
    def _retrain_models(self):
        """Trigger model retraining"""
        from src.detection.ml_detector import MLEnhancedDetector
        # This would trigger retraining
        LocalizedMessageBox.show_info(
            self,
            "message.retraining_started"
        )