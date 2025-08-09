#!/usr/bin/env python3
"""
Question Assistant Uninstaller
Safely removes Question Assistant and all associated files from your system.
"""

import os
import sys
import shutil
import time
import subprocess
import argparse
from pathlib import Path


class Uninstaller:
    """Handles the uninstallation process"""
    
    def __init__(self, silent=False):
        self.silent = silent
        self.app_name = "Question Assistant"
        self.service_name = "QuestionAssistantService"
        self.errors = []
        
    def log(self, message, level="INFO"):
        """Print log message"""
        if not self.silent or level == "ERROR":
            print(f"[{level}] {message}")
    
    def confirm_uninstall(self):
        """Ask user for confirmation"""
        if self.silent:
            return True
            
        print("\n" + "="*60)
        print(f"    {self.app_name} UNINSTALLER")
        print("="*60)
        print("\nThis will completely remove Question Assistant including:")
        print("  • All application files")
        print("  • Configuration and logs")
        print("  • Windows service (if installed)")
        print("  • Registry entries")
        print("  • Startup entries")
        print("\n⚠️  This action cannot be undone!")
        
        response = input("\nDo you want to continue? (yes/no): ").strip().lower()
        return response in ['yes', 'y']
    
    def stop_running_processes(self):
        """Stop any running Question Assistant processes"""
        self.log("Stopping running processes...")
        
        try:
            # Stop the main application
            subprocess.run(["taskkill", "/F", "/IM", "main.exe"], 
                         capture_output=True, text=True)
            subprocess.run(["taskkill", "/F", "/IM", "python.exe", "/FI", 
                          f"WINDOWTITLE eq {self.app_name}*"], 
                         capture_output=True, text=True)
        except Exception as e:
            self.log(f"Could not stop processes: {e}", "WARNING")
        
        time.sleep(2)  # Wait for processes to terminate
    
    def uninstall_service(self):
        """Remove Windows service"""
        self.log("Removing Windows service...")
        
        try:
            # Stop service
            result = subprocess.run(["net", "stop", self.service_name], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.log(f"Service {self.service_name} stopped")
            
            # Delete service
            result = subprocess.run(["sc", "delete", self.service_name], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.log(f"Service {self.service_name} removed")
            elif "FAILED 1060" not in result.stderr:
                self.log(f"Service removal warning: {result.stderr}", "WARNING")
                
        except Exception as e:
            self.log(f"Service removal error: {e}", "WARNING")
    
    def remove_startup_entries(self):
        """Remove from Windows startup"""
        self.log("Removing startup entries...")
        
        try:
            import winreg
            
            # Remove from Run registry
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0,
                    winreg.KEY_ALL_ACCESS
                )
                try:
                    winreg.DeleteValue(key, self.app_name.replace(" ", ""))
                    self.log("Removed from startup registry")
                except FileNotFoundError:
                    pass
                winreg.CloseKey(key)
            except Exception as e:
                self.log(f"Registry cleanup warning: {e}", "WARNING")
            
            # Remove from startup folder
            startup_folder = Path(os.environ['APPDATA']) / \
                           "Microsoft/Windows/Start Menu/Programs/Startup"
            shortcut = startup_folder / f"{self.app_name}.lnk"
            if shortcut.exists():
                shortcut.unlink()
                self.log("Removed from startup folder")
                
        except Exception as e:
            self.log(f"Startup removal error: {e}", "WARNING")
    
    def remove_application_files(self):
        """Remove application directory"""
        self.log("Removing application files...")
        
        # Get application directory
        if getattr(sys, 'frozen', False):
            # Running as compiled exe
            app_dir = Path(sys.executable).parent
        else:
            # Running as script
            app_dir = Path(__file__).parent
        
        self.log(f"Application directory: {app_dir}")
        
        # Create list of files to preserve (this uninstaller)
        preserve = [Path(__file__).name] if not getattr(sys, 'frozen', False) else []
        
        try:
            # Remove all files except uninstaller
            for item in app_dir.iterdir():
                if item.name not in preserve:
                    if item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                        self.log(f"Removed directory: {item.name}")
                    else:
                        try:
                            item.unlink()
                            self.log(f"Removed file: {item.name}")
                        except:
                            pass
            
            self.log("Application files removed")
            
        except Exception as e:
            self.errors.append(f"File removal error: {e}")
            self.log(f"File removal error: {e}", "ERROR")
    
    def remove_user_data(self):
        """Remove user configuration and data"""
        self.log("Removing user data...")
        
        data_locations = [
            Path(os.environ.get('APPDATA', '')) / self.app_name.replace(" ", ""),
            Path(os.environ.get('LOCALAPPDATA', '')) / self.app_name.replace(" ", ""),
            Path.home() / ".question_assistant",
            Path.home() / "Documents" / self.app_name,
        ]
        
        for location in data_locations:
            if location.exists():
                try:
                    shutil.rmtree(location, ignore_errors=True)
                    self.log(f"Removed: {location}")
                except Exception as e:
                    self.log(f"Could not remove {location}: {e}", "WARNING")
    
    def remove_shortcuts(self):
        """Remove desktop and start menu shortcuts"""
        self.log("Removing shortcuts...")
        
        shortcut_locations = [
            Path.home() / "Desktop" / f"{self.app_name}.lnk",
            Path(os.environ.get('APPDATA', '')) / 
            f"Microsoft/Windows/Start Menu/Programs/{self.app_name}.lnk",
            Path(os.environ.get('PROGRAMDATA', '')) / 
            f"Microsoft/Windows/Start Menu/Programs/{self.app_name}.lnk",
        ]
        
        for shortcut in shortcut_locations:
            if shortcut.exists():
                try:
                    shortcut.unlink()
                    self.log(f"Removed shortcut: {shortcut}")
                except Exception as e:
                    self.log(f"Could not remove shortcut: {e}", "WARNING")
    
    def cleanup_registry(self):
        """Clean up registry entries"""
        self.log("Cleaning registry...")
        
        try:
            import winreg
            
            # Remove uninstall entry
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                    0,
                    winreg.KEY_ALL_ACCESS
                )
                winreg.DeleteKey(key, self.app_name.replace(" ", ""))
                winreg.CloseKey(key)
                self.log("Removed uninstall registry entry")
            except:
                pass
            
            # Remove application registry keys
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"SOFTWARE",
                    0,
                    winreg.KEY_ALL_ACCESS
                )
                winreg.DeleteKey(key, self.app_name.replace(" ", ""))
                winreg.CloseKey(key)
                self.log("Removed application registry keys")
            except:
                pass
                
        except Exception as e:
            self.log(f"Registry cleanup warning: {e}", "WARNING")
    
    def run(self):
        """Run the complete uninstallation process"""
        if not self.confirm_uninstall():
            print("\nUninstallation cancelled.")
            return False
        
        print("\n" + "="*60)
        print("Starting uninstallation process...")
        print("="*60 + "\n")
        
        # Run uninstallation steps
        steps = [
            self.stop_running_processes,
            self.uninstall_service,
            self.remove_startup_entries,
            self.remove_shortcuts,
            self.cleanup_registry,
            self.remove_user_data,
            self.remove_application_files,
        ]
        
        for step in steps:
            try:
                step()
            except Exception as e:
                self.errors.append(f"{step.__name__}: {e}")
                self.log(f"Error in {step.__name__}: {e}", "ERROR")
        
        # Print summary
        print("\n" + "="*60)
        if self.errors:
            print("⚠️  Uninstallation completed with warnings:")
            for error in self.errors:
                print(f"  • {error}")
            print("\nSome files may need to be removed manually.")
        else:
            print("✅ Uninstallation completed successfully!")
            print(f"\n{self.app_name} has been removed from your system.")
        print("="*60)
        
        if not self.silent:
            input("\nPress Enter to exit...")
        
        return len(self.errors) == 0
    
    def self_delete(self):
        """Delete the uninstaller itself"""
        if getattr(sys, 'frozen', False):
            # If running as exe, create batch file to delete it
            batch_content = f'''@echo off
echo Cleaning up...
timeout /t 2 /nobreak > nul
del "{sys.executable}"
del "%~f0"
'''
            batch_path = Path(sys.executable).parent / "cleanup.bat"
            with open(batch_path, 'w') as f:
                f.write(batch_content)
            
            subprocess.Popen(["cmd", "/c", str(batch_path)], 
                           creationflags=subprocess.CREATE_NO_WINDOW)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Uninstall Question Assistant")
    parser.add_argument('--silent', '-s', action='store_true',
                       help='Run uninstaller without prompts')
    parser.add_argument('--keep-data', action='store_true',
                       help='Keep user data and configuration')
    
    args = parser.parse_args()
    
    # Check for admin privileges on Windows
    if sys.platform == 'win32':
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            print("⚠️  Warning: Running without administrator privileges.")
            print("Some components may not be removed completely.")
            print("\nFor complete removal, please run as Administrator.")
            response = input("\nContinue anyway? (yes/no): ").strip().lower()
            if response not in ['yes', 'y']:
                print("Uninstallation cancelled.")
                return 1
    
    # Run uninstaller
    uninstaller = Uninstaller(silent=args.silent)
    
    # Skip user data removal if requested
    if args.keep_data:
        uninstaller.remove_user_data = lambda: uninstaller.log("Keeping user data (--keep-data flag)")
    
    success = uninstaller.run()
    
    # Attempt self-deletion
    if success and not args.keep_data:
        uninstaller.self_delete()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())