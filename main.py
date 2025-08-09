import sys
import os
import argparse
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.logger import Logger
from src.core.config import Config
from src.core.service_manager import ServiceManager, install_service

def main():
    """Main entry point with CLI arguments"""
    parser = argparse.ArgumentParser(description='Question Assistant - Automated Q&A Tool')
    parser.add_argument('--mode', choices=['gui', 'tray', 'service', 'install', 'console'], 
                       default='tray', help='Run mode (default: tray)')
    parser.add_argument('--config', type=str, help='Path to config file')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--no-gui', action='store_true', help='Run without GUI')
    
    args = parser.parse_args()
    
    # Setup logging
    logger = Logger.get_logger()
    if args.debug:
        import logging
        logger.setLevel(logging.DEBUG)
    
    logger.info(f"Starting Question Assistant in {args.mode} mode")
    
    try:
        if args.mode == 'tray':
            # Run in system tray mode (default)
            try:
                from src.gui_components.tray_app_fixed import TrayApplication
            except ImportError:
                from src.gui_components.tray_app import TrayApplication
            app = TrayApplication()
            app.run()
            
        elif args.mode == 'gui' and not args.no_gui:
            # Run GUI mode - use simple, clean GUI
            try:
                from src.gui_components.simple_main import SimpleAssistant
                app = SimpleAssistant()
            except ImportError as e:
                logger.error(f"Failed to import GUI: {e}")
                # Fallback to ultra-modern GUI
                try:
                    from src.gui_components.ultra_modern_main import UltraModernAssistant
                    app = UltraModernAssistant()
                except ImportError:
                    # Final fallback
                    from src.gui_components.enhanced_main import ModernQuestionAssistant
                    app = ModernQuestionAssistant()
            app.mainloop()
            
        elif args.mode == 'service':
            # Run as service
            service = ServiceManager(args.config)
            service.start()
            
            # Keep running until interrupted
            try:
                while service.running:
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Interrupt received, stopping service")
                service.stop()
                
        elif args.mode == 'install':
            # Install Windows service
            install_service()
            
        elif args.mode == 'console':
            # Console mode for testing
            run_console_mode(args.config)
            
    except Exception as e:
        logger.error(f"Application error: {e}")
        if args.debug:
            import traceback
            logger.debug(traceback.format_exc())
        sys.exit(1)

def run_console_mode(config_path: Optional[str] = None):
    """Run in console mode for testing"""
    from src.core.config import Config
    from src.core.service_manager import ServiceManager
    
    print("Question Assistant - Console Mode")
    print("=" * 40)
    
    # Load or create config
    config = Config(config_path)
    
    # Interactive configuration
    if not config.get('api_key'):
        api_key = input("Enter Anthropic API key (optional): ").strip()
        if api_key:
            config.set('api_key', api_key)
    
    context = input("Enter question context: ").strip()
    if context:
        config.set('context', context)
    
    duration = input("Session duration (minutes) [60]: ").strip()
    if duration:
        try:
            config.set('duration_minutes', int(duration))
        except:
            pass
    
    # Start service
    print("\nStarting service...")
    print("Press Ctrl+C to stop\n")
    
    service = ServiceManager()
    service.config = config
    service.start()
    
    try:
        while service.running:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping service...")
        service.stop()
        
        # Show statistics
        if service._stats_tracker:
            print("\nSession Statistics:")
            print(service._stats_tracker.generate_report())

if __name__ == "__main__":
    main()