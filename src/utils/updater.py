"""Auto-update system for the application"""
import requests
import json
import hashlib
import tempfile
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple
from packaging import version
import logging
import zipfile

class AutoUpdater:
    """Handles automatic application updates"""
    
    def __init__(self):
        self.current_version = self._get_current_version()
        self.update_url = "https://api.github.com/repos/yourusername/questionassistant/releases/latest"
        self.logger = logging.getLogger("AutoUpdater")
        
        # Update settings
        self.settings = {
            'check_on_startup': True,
            'auto_download': True,
            'auto_install': False,
            'channel': 'stable'  # stable, beta, dev
        }
        
        self._load_settings()
    
    def _get_current_version(self) -> str:
        """Get current application version"""
        version_file = Path("version.txt")
        
        if version_file.exists():
            return version_file.read_text().strip()
        
        return "3.0.0"
    
    def _load_settings(self):
        """Load update settings"""
        settings_file = Path("config/update_settings.json")
        
        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    loaded = json.load(f)
                    self.settings.update(loaded)
            except:
                pass
    
    def check_for_updates(self) -> Optional[Dict]:
        """Check for available updates"""
        try:
            # Mock response for demonstration
            # In production, this would fetch from actual update server
            latest_info = self._fetch_latest_release_info()
            
            if not latest_info:
                return None
            
            latest_version = latest_info['version']
            
            # Compare versions
            if version.parse(latest_version) > version.parse(self.current_version):
                return {
                    'available': True,
                    'current_version': self.current_version,
                    'latest_version': latest_version,
                    'download_url': latest_info.get('download_url'),
                    'release_notes': latest_info.get('release_notes', ''),
                    'size': latest_info.get('size', 0),
                    'checksum': latest_info.get('checksum')
                }
            
            return {'available': False, 'current_version': self.current_version}
        
        except Exception as e:
            self.logger.error(f"Failed to check for updates: {e}")
            return None
    
    def _fetch_latest_release_info(self) -> Optional[Dict]:
        """Fetch latest release information"""
        # Mock implementation - in production, fetch from GitHub API or update server
        return {
            'version': '3.1.0',
            'download_url': 'https://example.com/download/questionassistant-3.1.0.zip',
            'release_notes': 'New features and bug fixes',
            'size': 25 * 1024 * 1024,  # 25 MB
            'checksum': 'abc123def456'
        }
        
        # Real implementation would be:
        # try:
        #     response = requests.get(self.update_url, timeout=10)
        #     response.raise_for_status()
        #     data = response.json()
        #     
        #     return {
        #         'version': data['tag_name'].lstrip('v'),
        #         'download_url': data['assets'][0]['browser_download_url'],
        #         'release_notes': data['body'],
        #         'size': data['assets'][0]['size']
        #     }
        # except Exception as e:
        #     self.logger.error(f"Failed to fetch release info: {e}")
        #     return None
    
    def download_update(self, download_url: str, progress_callback=None) -> Optional[Path]:
        """Download update package"""
        try:
            # Create temp directory
            temp_dir = Path(tempfile.mkdtemp())
            download_path = temp_dir / "update.zip"
            
            # Download with progress
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback:
                            progress = (downloaded / total_size) * 100 if total_size else 0
                            progress_callback(progress, downloaded, total_size)
            
            self.logger.info(f"Update downloaded to {download_path}")
            return download_path
        
        except Exception as e:
            self.logger.error(f"Failed to download update: {e}")
            return None
    
    def verify_update(self, file_path: Path, expected_checksum: str) -> bool:
        """Verify update package integrity"""
        try:
            # Calculate file checksum
            sha256_hash = hashlib.sha256()
            
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            
            calculated = sha256_hash.hexdigest()
            
            return calculated == expected_checksum
        
        except Exception as e:
            self.logger.error(f"Failed to verify update: {e}")
            return False
    
    def install_update(self, update_path: Path) -> bool:
        """Install update package"""
        try:
            # Extract update
            extract_dir = update_path.parent / "extracted"
            
            with zipfile.ZipFile(update_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Create update script
            update_script = self._create_update_script(extract_dir)
            
            # Launch updater and exit current process
            if sys.platform == 'win32':
                subprocess.Popen(['cmd', '/c', str(update_script)], 
                               creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen(['sh', str(update_script)])
            
            self.logger.info("Update installer launched")
            
            # Schedule application exit
            import threading
            threading.Timer(2.0, sys.exit).start()
            
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to install update: {e}")
            return False
    
    def _create_update_script(self, source_dir: Path) -> Path:
        """Create update installation script"""
        script_path = source_dir / "update.bat" if sys.platform == 'win32' else source_dir / "update.sh"
        
        app_dir = Path.cwd()
        
        if sys.platform == 'win32':
            script_content = f"""@echo off
echo Updating Question Assistant...
timeout /t 3 /nobreak > nul
xcopy /s /e /y "{source_dir}\\*" "{app_dir}\\"
echo Update complete!
start "" "{app_dir}\\QuestionAssistant.exe"
del "%~f0"
"""
        else:
            script_content = f"""#!/bin/bash
echo "Updating Question Assistant..."
sleep 3
cp -r "{source_dir}/"* "{app_dir}/"
echo "Update complete!"
"{app_dir}/QuestionAssistant" &
rm "$0"
"""
        
        script_path.write_text(script_content)
        
        if sys.platform != 'win32':
            script_path.chmod(0o755)
        
        return script_path
    
    def rollback_update(self):
        """Rollback to previous version"""
        backup_dir = Path("backup")
        
        if not backup_dir.exists():
            self.logger.error("No backup available for rollback")
            return False
        
        try:
            # Restore from backup
            for item in backup_dir.iterdir():
                dest = Path.cwd() / item.name
                
                if item.is_file():
                    shutil.copy2(item, dest)
                else:
                    shutil.copytree(item, dest, dirs_exist_ok=True)
            
            self.logger.info("Rollback completed")
            return True
        
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            return False
    
    def create_backup(self):
        """Create backup before update"""
        backup_dir = Path("backup")
        
        # Clear old backup
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        
        backup_dir.mkdir()
        
        # Backup important files
        important_files = [
            "main.py",
            "src",
            "config",
            "version.txt"
        ]
        
        for item_name in important_files:
            item = Path(item_name)
            if item.exists():
                dest = backup_dir / item_name
                
                if item.is_file():
                    shutil.copy2(item, dest)
                else:
                    shutil.copytree(item, dest)
        
        self.logger.info("Backup created")

class UpdateUI:
    """UI for update notifications and progress"""
    
    @staticmethod
    def show_update_dialog(update_info: Dict) -> bool:
        """Show update available dialog"""
        import tkinter as tk
        from tkinter import messagebox
        
        root = tk.Tk()
        root.withdraw()
        
        message = f"""A new version is available!

Current version: {update_info['current_version']}
Latest version: {update_info['latest_version']}

Release notes:
{update_info['release_notes'][:200]}...

Would you like to download and install the update?"""
        
        result = messagebox.askyesno("Update Available", message)
        root.destroy()
        
        return result
    
    @staticmethod
    def show_progress_dialog(title: str = "Downloading Update"):
        """Show download progress dialog"""
        import tkinter as tk
        from tkinter import ttk
        
        class ProgressDialog:
            def __init__(self):
                self.root = tk.Toplevel()
                self.root.title(title)
                self.root.geometry("400x150")
                self.root.resizable(False, False)
                
                # Center window
                self.root.update_idletasks()
                x = (self.root.winfo_screenwidth() // 2) - 200
                y = (self.root.winfo_screenheight() // 2) - 75
                self.root.geometry(f"+{x}+{y}")
                
                # Progress label
                self.label = ttk.Label(self.root, text="Preparing download...")
                self.label.pack(pady=20)
                
                # Progress bar
                self.progress = ttk.Progressbar(
                    self.root,
                    length=350,
                    mode='determinate'
                )
                self.progress.pack(pady=10)
                
                # Status label
                self.status = ttk.Label(self.root, text="")
                self.status.pack(pady=10)
            
            def update_progress(self, percent: float, downloaded: int, total: int):
                """Update progress display"""
                self.progress['value'] = percent
                
                mb_downloaded = downloaded / (1024 * 1024)
                mb_total = total / (1024 * 1024)
                
                self.label.config(text=f"Downloading update... {percent:.1f}%")
                self.status.config(text=f"{mb_downloaded:.1f} MB / {mb_total:.1f} MB")
                
                self.root.update()
            
            def close(self):
                """Close dialog"""
                self.root.destroy()
        
        return ProgressDialog()

# Global updater instance
auto_updater = AutoUpdater()