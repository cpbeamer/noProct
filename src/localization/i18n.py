"""Internationalization and localization support"""
import json
import locale
from pathlib import Path
from typing import Dict, Optional, List, Any
import gettext
import logging
from enum import Enum

class Language(Enum):
    """Supported languages"""
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    RUSSIAN = "ru"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"
    ARABIC = "ar"
    HINDI = "hi"
    DUTCH = "nl"
    POLISH = "pl"
    TURKISH = "tr"

class Translator:
    """Main translation system"""
    
    def __init__(self):
        self.logger = logging.getLogger("Translator")
        self.translations_dir = Path("locales")
        self.translations_dir.mkdir(exist_ok=True)
        
        # Current language
        self.current_language = Language.ENGLISH
        
        # Translation cache
        self.translations: Dict[str, Dict[str, str]] = {}
        
        # Fallback language
        self.fallback_language = Language.ENGLISH
        
        # Load all translations
        self.load_all_translations()
        
        # Detect system language
        self.auto_detect_language()
    
    def load_all_translations(self):
        """Load all available translation files"""
        for lang in Language:
            self.load_language(lang)
    
    def load_language(self, language: Language):
        """Load translations for a specific language"""
        lang_file = self.translations_dir / f"{language.value}.json"
        
        if lang_file.exists():
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.translations[language.value] = json.load(f)
                    self.logger.info(f"Loaded translations for {language.value}")
            except Exception as e:
                self.logger.error(f"Failed to load {language.value}: {e}")
                self.translations[language.value] = {}
        else:
            # Create default translations file
            self.create_default_translations(language)
    
    def create_default_translations(self, language: Language):
        """Create default translation file for a language"""
        # Default English translations
        if language == Language.ENGLISH:
            translations = {
                # Application
                "app.name": "Question Assistant",
                "app.version": "Version",
                "app.description": "Automated question detection and answering system",
                
                # Menu items
                "menu.file": "File",
                "menu.edit": "Edit",
                "menu.view": "View",
                "menu.tools": "Tools",
                "menu.help": "Help",
                "menu.settings": "Settings",
                "menu.exit": "Exit",
                
                # Buttons
                "button.start": "Start",
                "button.stop": "Stop",
                "button.pause": "Pause",
                "button.resume": "Resume",
                "button.save": "Save",
                "button.cancel": "Cancel",
                "button.ok": "OK",
                "button.apply": "Apply",
                "button.browse": "Browse",
                "button.refresh": "Refresh",
                "button.export": "Export",
                "button.import": "Import",
                
                # Labels
                "label.context": "Question Context",
                "label.duration": "Duration (minutes)",
                "label.questions": "Number of Questions",
                "label.type": "Question Type",
                "label.api_key": "API Key",
                "label.language": "Language",
                "label.theme": "Theme",
                "label.status": "Status",
                
                # Status messages
                "status.ready": "Ready",
                "status.running": "Running",
                "status.stopped": "Stopped",
                "status.paused": "Paused",
                "status.detecting": "Detecting questions...",
                "status.answering": "Answering question...",
                "status.error": "Error occurred",
                
                # Messages
                "message.welcome": "Welcome to Question Assistant",
                "message.service_started": "Service started successfully",
                "message.service_stopped": "Service stopped",
                "message.question_detected": "Question detected",
                "message.answer_found": "Answer found",
                "message.update_available": "Update available",
                "message.settings_saved": "Settings saved successfully",
                
                # Errors
                "error.invalid_input": "Invalid input",
                "error.api_key_missing": "API key is missing",
                "error.connection_failed": "Connection failed",
                "error.detection_failed": "Detection failed",
                "error.file_not_found": "File not found",
                
                # Tooltips
                "tooltip.start_service": "Start the detection service",
                "tooltip.stop_service": "Stop the detection service",
                "tooltip.open_settings": "Open application settings",
                "tooltip.view_statistics": "View session statistics",
                
                # Dialog titles
                "dialog.confirm": "Confirm",
                "dialog.warning": "Warning",
                "dialog.error": "Error",
                "dialog.info": "Information",
                "dialog.save_changes": "Save Changes?",
                
                # Question types
                "question.multiple_choice": "Multiple Choice",
                "question.true_false": "True/False",
                "question.short_answer": "Short Answer",
                "question.essay": "Essay",
                
                # Time units
                "time.seconds": "seconds",
                "time.minutes": "minutes",
                "time.hours": "hours",
                "time.days": "days"
            }
        
        # Spanish translations
        elif language == Language.SPANISH:
            translations = {
                "app.name": "Asistente de Preguntas",
                "app.version": "Versión",
                "app.description": "Sistema automatizado de detección y respuesta de preguntas",
                "menu.file": "Archivo",
                "menu.edit": "Editar",
                "menu.view": "Ver",
                "menu.tools": "Herramientas",
                "menu.help": "Ayuda",
                "menu.settings": "Configuración",
                "menu.exit": "Salir",
                "button.start": "Iniciar",
                "button.stop": "Detener",
                "button.pause": "Pausar",
                "button.resume": "Reanudar",
                "button.save": "Guardar",
                "button.cancel": "Cancelar",
                "button.ok": "Aceptar",
                "label.context": "Contexto de Pregunta",
                "label.duration": "Duración (minutos)",
                "label.questions": "Número de Preguntas",
                "status.ready": "Listo",
                "status.running": "Ejecutando",
                "status.stopped": "Detenido",
                "message.welcome": "Bienvenido al Asistente de Preguntas",
                "error.invalid_input": "Entrada inválida"
            }
        
        # French translations
        elif language == Language.FRENCH:
            translations = {
                "app.name": "Assistant de Questions",
                "app.version": "Version",
                "app.description": "Système automatisé de détection et de réponse aux questions",
                "menu.file": "Fichier",
                "menu.edit": "Éditer",
                "menu.view": "Afficher",
                "menu.tools": "Outils",
                "menu.help": "Aide",
                "menu.settings": "Paramètres",
                "menu.exit": "Quitter",
                "button.start": "Démarrer",
                "button.stop": "Arrêter",
                "button.pause": "Pause",
                "button.resume": "Reprendre",
                "button.save": "Enregistrer",
                "button.cancel": "Annuler",
                "label.context": "Contexte de Question",
                "label.duration": "Durée (minutes)",
                "status.ready": "Prêt",
                "status.running": "En cours",
                "message.welcome": "Bienvenue dans l'Assistant de Questions"
            }
        
        # German translations
        elif language == Language.GERMAN:
            translations = {
                "app.name": "Fragen-Assistent",
                "app.version": "Version",
                "menu.file": "Datei",
                "menu.edit": "Bearbeiten",
                "menu.view": "Ansicht",
                "menu.tools": "Werkzeuge",
                "menu.help": "Hilfe",
                "menu.settings": "Einstellungen",
                "menu.exit": "Beenden",
                "button.start": "Starten",
                "button.stop": "Stoppen",
                "button.save": "Speichern",
                "button.cancel": "Abbrechen",
                "status.ready": "Bereit",
                "status.running": "Läuft",
                "message.welcome": "Willkommen beim Fragen-Assistenten"
            }
        
        # Chinese translations
        elif language == Language.CHINESE:
            translations = {
                "app.name": "问题助手",
                "app.version": "版本",
                "menu.file": "文件",
                "menu.edit": "编辑",
                "menu.view": "查看",
                "menu.tools": "工具",
                "menu.help": "帮助",
                "menu.settings": "设置",
                "menu.exit": "退出",
                "button.start": "开始",
                "button.stop": "停止",
                "button.save": "保存",
                "button.cancel": "取消",
                "status.ready": "就绪",
                "status.running": "运行中",
                "message.welcome": "欢迎使用问题助手"
            }
        
        # Japanese translations
        elif language == Language.JAPANESE:
            translations = {
                "app.name": "質問アシスタント",
                "app.version": "バージョン",
                "menu.file": "ファイル",
                "menu.edit": "編集",
                "menu.view": "表示",
                "menu.tools": "ツール",
                "menu.help": "ヘルプ",
                "menu.settings": "設定",
                "menu.exit": "終了",
                "button.start": "開始",
                "button.stop": "停止",
                "button.save": "保存",
                "button.cancel": "キャンセル",
                "status.ready": "準備完了",
                "status.running": "実行中",
                "message.welcome": "質問アシスタントへようこそ"
            }
        
        else:
            # For other languages, start with empty translations
            translations = {}
        
        # Save translations file
        self.translations[language.value] = translations
        lang_file = self.translations_dir / f"{language.value}.json"
        
        with open(lang_file, 'w', encoding='utf-8') as f:
            json.dump(translations, f, ensure_ascii=False, indent=2)
    
    def auto_detect_language(self):
        """Auto-detect system language"""
        try:
            system_locale = locale.getdefaultlocale()[0]
            if system_locale:
                lang_code = system_locale.split('_')[0].lower()
                
                # Map to our supported languages
                for lang in Language:
                    if lang.value == lang_code:
                        self.set_language(lang)
                        self.logger.info(f"Auto-detected language: {lang.value}")
                        return
        except:
            pass
        
        # Default to English
        self.set_language(Language.ENGLISH)
    
    def set_language(self, language: Language):
        """Set current language"""
        self.current_language = language
        
        # Ensure translations are loaded
        if language.value not in self.translations:
            self.load_language(language)
    
    def get(self, key: str, **kwargs) -> str:
        """Get translated string"""
        # Try current language
        if self.current_language.value in self.translations:
            translation = self.translations[self.current_language.value].get(key)
            if translation:
                # Format with kwargs if provided
                if kwargs:
                    try:
                        return translation.format(**kwargs)
                    except:
                        pass
                return translation
        
        # Try fallback language
        if self.fallback_language.value in self.translations:
            translation = self.translations[self.fallback_language.value].get(key)
            if translation:
                if kwargs:
                    try:
                        return translation.format(**kwargs)
                    except:
                        pass
                return translation
        
        # Return key if no translation found
        return key
    
    def get_available_languages(self) -> List[Tuple[str, str]]:
        """Get list of available languages"""
        languages = []
        
        language_names = {
            Language.ENGLISH: "English",
            Language.SPANISH: "Español",
            Language.FRENCH: "Français",
            Language.GERMAN: "Deutsch",
            Language.ITALIAN: "Italiano",
            Language.PORTUGUESE: "Português",
            Language.RUSSIAN: "Русский",
            Language.CHINESE: "中文",
            Language.JAPANESE: "日本語",
            Language.KOREAN: "한국어",
            Language.ARABIC: "العربية",
            Language.HINDI: "हिन्दी",
            Language.DUTCH: "Nederlands",
            Language.POLISH: "Polski",
            Language.TURKISH: "Türkçe"
        }
        
        for lang in Language:
            name = language_names.get(lang, lang.value)
            languages.append((lang.value, name))
        
        return languages
    
    def export_for_translation(self, language: Language, output_file: Path):
        """Export strings for translation"""
        # Get English strings as base
        base_strings = self.translations.get(Language.ENGLISH.value, {})
        
        # Get existing translations for target language
        existing = self.translations.get(language.value, {})
        
        # Create export format
        export_data = {
            "language": language.value,
            "translations": []
        }
        
        for key, english_text in base_strings.items():
            export_data["translations"].append({
                "key": key,
                "english": english_text,
                "translation": existing.get(key, "")
            })
        
        # Save export file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    def import_translations(self, import_file: Path):
        """Import translated strings"""
        try:
            with open(import_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            language = data.get("language")
            if not language:
                return False
            
            # Update translations
            if language not in self.translations:
                self.translations[language] = {}
            
            for item in data.get("translations", []):
                key = item.get("key")
                translation = item.get("translation")
                
                if key and translation:
                    self.translations[language][key] = translation
            
            # Save updated translations
            lang_file = self.translations_dir / f"{language}.json"
            with open(lang_file, 'w', encoding='utf-8') as f:
                json.dump(self.translations[language], f, ensure_ascii=False, indent=2)
            
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to import translations: {e}")
            return False

class LocalizedFormatter:
    """Format numbers, dates, and currencies for different locales"""
    
    @staticmethod
    def format_number(value: float, language: Language) -> str:
        """Format number according to locale"""
        locale_map = {
            Language.ENGLISH: 'en_US',
            Language.SPANISH: 'es_ES',
            Language.FRENCH: 'fr_FR',
            Language.GERMAN: 'de_DE',
            Language.ITALIAN: 'it_IT',
            Language.PORTUGUESE: 'pt_PT',
            Language.RUSSIAN: 'ru_RU',
            Language.CHINESE: 'zh_CN',
            Language.JAPANESE: 'ja_JP',
            Language.KOREAN: 'ko_KR'
        }
        
        try:
            locale_str = locale_map.get(language, 'en_US')
            locale.setlocale(locale.LC_NUMERIC, locale_str)
            return locale.format_string("%.2f", value, grouping=True)
        except:
            return f"{value:.2f}"
    
    @staticmethod
    def format_date(date_obj, language: Language) -> str:
        """Format date according to locale"""
        format_map = {
            Language.ENGLISH: "%B %d, %Y",
            Language.SPANISH: "%d de %B de %Y",
            Language.FRENCH: "%d %B %Y",
            Language.GERMAN: "%d. %B %Y",
            Language.CHINESE: "%Y年%m月%d日",
            Language.JAPANESE: "%Y年%m月%d日"
        }
        
        date_format = format_map.get(language, "%Y-%m-%d")
        return date_obj.strftime(date_format)
    
    @staticmethod
    def format_time(time_obj, language: Language) -> str:
        """Format time according to locale"""
        # Most use 24-hour format except English
        if language == Language.ENGLISH:
            return time_obj.strftime("%I:%M %p")
        else:
            return time_obj.strftime("%H:%M")

# Global translator instance
translator = Translator()

# Convenience function
def _(key: str, **kwargs) -> str:
    """Shorthand for translation"""
    return translator.get(key, **kwargs)