import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
from pathlib import Path
import threading
import json

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.config import Config
from src.core.service_manager import ServiceManager
from src.utils.logger import get_logger

class EnhancedGUI:
    """Enhanced GUI with tabs and advanced features"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Question Assistant Pro")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        self.config = Config()
        self.service_manager = None
        self.logger = get_logger("GUI")
        
        # Set theme
        self.setup_theme()
        
        # Create UI
        self.create_menu()
        self.create_tabs()
        self.create_status_bar()
        
        # Center window
        self.center_window()
        
        # Bind events
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_theme(self):
        """Setup application theme"""
        style = ttk.Style()
        
        if sys.platform == 'win32':
            style.theme_use('vista')
        else:
            style.theme_use('default')
        
        # Custom colors
        self.colors = {
            'bg': '#f0f0f0',
            'fg': '#333333',
            'accent': '#0078d4',
            'success': '#107c10',
            'warning': '#ff8c00',
            'error': '#d13438'
        }
        
        self.root.configure(bg=self.colors['bg'])
    
    def create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Config", command=self.load_config)
        file_menu.add_command(label="Save Config", command=self.save_config)
        file_menu.add_separator()
        file_menu.add_command(label="Export Statistics", command=self.export_stats)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Service menu
        service_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Service", menu=service_menu)
        service_menu.add_command(label="Start", command=self.start_service)
        service_menu.add_command(label="Stop", command=self.stop_service)
        service_menu.add_command(label="Pause", command=self.pause_service)
        service_menu.add_command(label="Resume", command=self.resume_service)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Test OCR", command=self.test_ocr)
        tools_menu.add_command(label="Test Detection", command=self.test_detection)
        tools_menu.add_command(label="Capture Templates", command=self.capture_templates)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_docs)
        help_menu.add_command(label="About", command=self.show_about)
    
    def create_tabs(self):
        """Create tabbed interface"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Configuration tab
        self.config_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.config_frame, text="Configuration")
        self.create_config_tab()
        
        # Advanced tab
        self.advanced_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.advanced_frame, text="Advanced")
        self.create_advanced_tab()
        
        # Statistics tab
        self.stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_frame, text="Statistics")
        self.create_stats_tab()
        
        # Logs tab
        self.logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.logs_frame, text="Logs")
        self.create_logs_tab()
    
    def create_config_tab(self):
        """Create configuration tab"""
        # Main settings frame
        main_frame = ttk.LabelFrame(self.config_frame, text="Main Settings", padding=10)
        main_frame.pack(fill='x', padx=10, pady=5)
        
        # Context
        ttk.Label(main_frame, text="Question Context:").grid(row=0, column=0, sticky='w', pady=5)
        self.context_text = tk.Text(main_frame, height=3, width=50)
        self.context_text.grid(row=1, column=0, columnspan=2, pady=5)
        
        # Duration
        ttk.Label(main_frame, text="Duration (minutes):").grid(row=2, column=0, sticky='w', pady=5)
        self.duration_var = tk.IntVar(value=60)
        duration_spin = ttk.Spinbox(main_frame, from_=1, to=600, textvariable=self.duration_var, width=10)
        duration_spin.grid(row=2, column=1, sticky='w', pady=5)
        
        # Number of questions
        ttk.Label(main_frame, text="Max Questions:").grid(row=3, column=0, sticky='w', pady=5)
        self.questions_var = tk.IntVar(value=10)
        questions_spin = ttk.Spinbox(main_frame, from_=1, to=100, textvariable=self.questions_var, width=10)
        questions_spin.grid(row=3, column=1, sticky='w', pady=5)
        
        # Question type
        ttk.Label(main_frame, text="Question Type:").grid(row=4, column=0, sticky='w', pady=5)
        self.type_var = tk.StringVar(value="Multiple Choice")
        type_combo = ttk.Combobox(main_frame, textvariable=self.type_var, 
                                 values=["Multiple Choice", "True/False", "Short Answer", "Mixed"],
                                 state='readonly', width=20)
        type_combo.grid(row=4, column=1, sticky='w', pady=5)
        
        # API settings frame
        api_frame = ttk.LabelFrame(self.config_frame, text="API Settings", padding=10)
        api_frame.pack(fill='x', padx=10, pady=5)
        
        # API Provider
        ttk.Label(api_frame, text="AI Provider:").grid(row=0, column=0, sticky='w', pady=5)
        self.provider_var = tk.StringVar(value="Anthropic")
        provider_combo = ttk.Combobox(api_frame, textvariable=self.provider_var,
                                     values=["Anthropic", "OpenAI", "Local", "Web Search"],
                                     state='readonly', width=20)
        provider_combo.grid(row=0, column=1, sticky='w', pady=5)
        
        # API Key
        ttk.Label(api_frame, text="API Key:").grid(row=1, column=0, sticky='w', pady=5)
        self.api_key_var = tk.StringVar()
        api_entry = ttk.Entry(api_frame, textvariable=self.api_key_var, show='*', width=40)
        api_entry.grid(row=1, column=1, sticky='w', pady=5)
        
        # Show/Hide key button
        self.show_key_var = tk.BooleanVar(value=False)
        show_btn = ttk.Checkbutton(api_frame, text="Show", variable=self.show_key_var,
                                  command=lambda: api_entry.config(show='' if self.show_key_var.get() else '*'))
        show_btn.grid(row=1, column=2, padx=5)
        
        # Control buttons
        button_frame = ttk.Frame(self.config_frame)
        button_frame.pack(pady=20)
        
        self.start_btn = ttk.Button(button_frame, text="Start Service", 
                                   command=self.start_service, style='Accent.TButton')
        self.start_btn.pack(side='left', padx=5)
        
        self.stop_btn = ttk.Button(button_frame, text="Stop Service", 
                                  command=self.stop_service, state='disabled')
        self.stop_btn.pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="Save Config", command=self.save_current_config).pack(side='left', padx=5)
    
    def create_advanced_tab(self):
        """Create advanced settings tab"""
        # Performance frame
        perf_frame = ttk.LabelFrame(self.advanced_frame, text="Performance", padding=10)
        perf_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(perf_frame, text="Monitoring Interval (seconds):").grid(row=0, column=0, sticky='w', pady=5)
        self.interval_var = tk.IntVar(value=5)
        ttk.Spinbox(perf_frame, from_=1, to=30, textvariable=self.interval_var, width=10).grid(row=0, column=1, sticky='w')
        
        ttk.Label(perf_frame, text="Confidence Threshold:").grid(row=1, column=0, sticky='w', pady=5)
        self.confidence_var = tk.DoubleVar(value=0.5)
        ttk.Scale(perf_frame, from_=0.1, to=1.0, variable=self.confidence_var, 
                 orient='horizontal', length=200).grid(row=1, column=1, sticky='w')
        ttk.Label(perf_frame, textvariable=self.confidence_var).grid(row=1, column=2)
        
        self.cache_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(perf_frame, text="Enable Caching", variable=self.cache_var).grid(row=2, column=0, sticky='w', pady=5)
        
        self.parallel_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(perf_frame, text="Parallel Processing", variable=self.parallel_var).grid(row=3, column=0, sticky='w', pady=5)
        
        # Human simulation frame
        human_frame = ttk.LabelFrame(self.advanced_frame, text="Human Simulation", padding=10)
        human_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(human_frame, text="Typing Speed:").grid(row=0, column=0, sticky='w', pady=5)
        self.typing_speed_var = tk.StringVar(value="Normal")
        ttk.Combobox(human_frame, textvariable=self.typing_speed_var,
                    values=["Slow", "Normal", "Fast"], state='readonly', width=15).grid(row=0, column=1, sticky='w')
        
        ttk.Label(human_frame, text="Mouse Speed:").grid(row=1, column=0, sticky='w', pady=5)
        self.mouse_speed_var = tk.StringVar(value="Normal")
        ttk.Combobox(human_frame, textvariable=self.mouse_speed_var,
                    values=["Slow", "Normal", "Fast"], state='readonly', width=15).grid(row=1, column=1, sticky='w')
        
        self.typos_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(human_frame, text="Simulate Typos", variable=self.typos_var).grid(row=2, column=0, sticky='w', pady=5)
        
        self.overshoot_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(human_frame, text="Mouse Overshoot", variable=self.overshoot_var).grid(row=3, column=0, sticky='w', pady=5)
        
        # Detection frame
        detect_frame = ttk.LabelFrame(self.advanced_frame, text="Detection Settings", padding=10)
        detect_frame.pack(fill='x', padx=10, pady=5)
        
        self.ocr_preprocess_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(detect_frame, text="OCR Preprocessing", variable=self.ocr_preprocess_var).grid(row=0, column=0, sticky='w', pady=5)
        
        self.template_matching_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(detect_frame, text="Template Matching", variable=self.template_matching_var).grid(row=1, column=0, sticky='w', pady=5)
        
        ttk.Label(detect_frame, text="Tesseract Path:").grid(row=2, column=0, sticky='w', pady=5)
        self.tesseract_var = tk.StringVar(value=r"C:\Program Files\Tesseract-OCR\tesseract.exe")
        ttk.Entry(detect_frame, textvariable=self.tesseract_var, width=40).grid(row=2, column=1, sticky='w')
        ttk.Button(detect_frame, text="Browse", command=self.browse_tesseract).grid(row=2, column=2, padx=5)
    
    def create_stats_tab(self):
        """Create statistics tab"""
        # Current session frame
        current_frame = ttk.LabelFrame(self.stats_frame, text="Current Session", padding=10)
        current_frame.pack(fill='x', padx=10, pady=5)
        
        self.stats_text = tk.Text(current_frame, height=10, width=60)
        self.stats_text.pack(fill='both', expand=True)
        
        # Historical stats frame
        history_frame = ttk.LabelFrame(self.stats_frame, text="Historical Statistics", padding=10)
        history_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create treeview for historical data
        columns = ('Session', 'Questions', 'Success Rate', 'Duration')
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=150)
        
        self.history_tree.pack(fill='both', expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(history_frame, orient='vertical', command=self.history_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        # Refresh button
        ttk.Button(self.stats_frame, text="Refresh Statistics", 
                  command=self.refresh_stats).pack(pady=10)
    
    def create_logs_tab(self):
        """Create logs tab"""
        # Log viewer
        self.log_text = tk.Text(self.logs_frame, height=20, width=80, wrap='word')
        self.log_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.log_text, orient='vertical', command=self.log_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # Control buttons
        button_frame = ttk.Frame(self.logs_frame)
        button_frame.pack(pady=5)
        
        ttk.Button(button_frame, text="Load Log", command=self.load_log).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Clear", command=lambda: self.log_text.delete(1.0, tk.END)).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Auto-Scroll", command=self.toggle_autoscroll).pack(side='left', padx=5)
        
        self.autoscroll = True
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(fill='x', side='bottom')
        
        self.status_label = ttk.Label(self.status_bar, text="Ready", relief='sunken')
        self.status_label.pack(side='left', fill='x', expand=True)
        
        self.service_status = ttk.Label(self.status_bar, text="Service: Stopped", relief='sunken')
        self.service_status.pack(side='right', padx=5)
    
    def center_window(self):
        """Center window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def start_service(self):
        """Start the service"""
        # Validate inputs
        if not self.validate_inputs():
            return
        
        # Update config
        self.update_config()
        
        # Start service in thread
        def run_service():
            try:
                self.service_manager = ServiceManager()
                self.service_manager.config = self.config
                self.service_manager.start()
                
                self.root.after(0, lambda: self.update_service_status("Running"))
                self.root.after(0, lambda: self.start_btn.config(state='disabled'))
                self.root.after(0, lambda: self.stop_btn.config(state='normal'))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Service Error", str(e)))
        
        service_thread = threading.Thread(target=run_service)
        service_thread.daemon = True
        service_thread.start()
        
        self.status_label.config(text="Service started")
    
    def stop_service(self):
        """Stop the service"""
        if self.service_manager:
            self.service_manager.stop()
            self.update_service_status("Stopped")
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            self.status_label.config(text="Service stopped")
            
            # Show statistics
            if self.service_manager._stats_tracker:
                report = self.service_manager._stats_tracker.generate_report()
                self.stats_text.delete(1.0, tk.END)
                self.stats_text.insert(1.0, report)
    
    def pause_service(self):
        """Pause the service"""
        if self.service_manager and self.service_manager.running:
            self.service_manager.pause()
            self.update_service_status("Paused")
            self.status_label.config(text="Service paused")
    
    def resume_service(self):
        """Resume the service"""
        if self.service_manager and self.service_manager.running:
            self.service_manager.resume()
            self.update_service_status("Running")
            self.status_label.config(text="Service resumed")
    
    def update_service_status(self, status: str):
        """Update service status display"""
        self.service_status.config(text=f"Service: {status}")
    
    def validate_inputs(self) -> bool:
        """Validate user inputs"""
        context = self.context_text.get(1.0, tk.END).strip()
        if not context:
            messagebox.showerror("Validation Error", "Please enter question context")
            return False
        
        if self.duration_var.get() < 1:
            messagebox.showerror("Validation Error", "Duration must be at least 1 minute")
            return False
        
        return True
    
    def update_config(self):
        """Update configuration from GUI values"""
        self.config.set('context', self.context_text.get(1.0, tk.END).strip())
        self.config.set('duration_minutes', self.duration_var.get())
        self.config.set('num_questions', self.questions_var.get())
        self.config.set('question_type', self.type_var.get())
        self.config.set('api_key', self.api_key_var.get())
        self.config.set('monitoring_interval', self.interval_var.get())
        self.config.set('confidence_threshold', self.confidence_var.get())
        self.config.set('tesseract_path', self.tesseract_var.get())
        
        # Advanced settings
        self.config.set('performance.enable_caching', self.cache_var.get())
        self.config.set('performance.parallel_processing', self.parallel_var.get())
        self.config.set('ocr_preprocessing', self.ocr_preprocess_var.get())
    
    def save_current_config(self):
        """Save current configuration"""
        self.update_config()
        if self.config.save():
            messagebox.showinfo("Success", "Configuration saved")
        else:
            messagebox.showerror("Error", "Failed to save configuration")
    
    def load_config(self):
        """Load configuration from file"""
        filename = filedialog.askopenfilename(
            title="Load Configuration",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.config = Config(filename)
            self.populate_from_config()
            messagebox.showinfo("Success", "Configuration loaded")
    
    def save_config(self):
        """Save configuration to file"""
        filename = filedialog.asksaveasfilename(
            title="Save Configuration",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.update_config()
            self.config.config_path = Path(filename)
            if self.config.save():
                messagebox.showinfo("Success", "Configuration saved")
    
    def populate_from_config(self):
        """Populate GUI from configuration"""
        self.context_text.delete(1.0, tk.END)
        self.context_text.insert(1.0, self.config.get('context', ''))
        self.duration_var.set(self.config.get('duration_minutes', 60))
        self.questions_var.set(self.config.get('num_questions', 10))
        self.type_var.set(self.config.get('question_type', 'Multiple Choice'))
        self.api_key_var.set(self.config.get('api_key', ''))
        self.interval_var.set(self.config.get('monitoring_interval', 5))
        self.confidence_var.set(self.config.get('confidence_threshold', 0.5))
        self.tesseract_var.set(self.config.get('tesseract_path', r"C:\Program Files\Tesseract-OCR\tesseract.exe"))
    
    def browse_tesseract(self):
        """Browse for Tesseract executable"""
        filename = filedialog.askopenfilename(
            title="Select Tesseract Executable",
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")]
        )
        if filename:
            self.tesseract_var.set(filename)
    
    def test_ocr(self):
        """Test OCR functionality"""
        messagebox.showinfo("OCR Test", "OCR test functionality not yet implemented")
    
    def test_detection(self):
        """Test detection functionality"""
        messagebox.showinfo("Detection Test", "Detection test functionality not yet implemented")
    
    def capture_templates(self):
        """Capture UI templates"""
        messagebox.showinfo("Template Capture", "Template capture functionality not yet implemented")
    
    def refresh_stats(self):
        """Refresh statistics display"""
        # This would load and display statistics
        pass
    
    def load_log(self):
        """Load log file"""
        from pathlib import Path
        log_dir = Path("logs")
        if log_dir.exists():
            log_files = list(log_dir.glob("*.log"))
            if log_files:
                latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
                with open(latest_log, 'r') as f:
                    content = f.read()
                    self.log_text.delete(1.0, tk.END)
                    self.log_text.insert(1.0, content)
                    if self.autoscroll:
                        self.log_text.see(tk.END)
    
    def toggle_autoscroll(self):
        """Toggle auto-scroll for logs"""
        self.autoscroll = not self.autoscroll
    
    def export_stats(self):
        """Export statistics to file"""
        filename = filedialog.asksaveasfilename(
            title="Export Statistics",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            # This would export statistics
            messagebox.showinfo("Export", "Statistics export functionality not yet implemented")
    
    def show_docs(self):
        """Show documentation"""
        import webbrowser
        webbrowser.open("https://github.com/yourusername/questionassistant/wiki")
    
    def show_about(self):
        """Show about dialog"""
        about_text = """Question Assistant Pro
Version 2.0
        
Advanced automated question detection and answering tool.
        
© 2024 Question Assistant Team"""
        messagebox.showinfo("About", about_text)
    
    def on_closing(self):
        """Handle window closing"""
        if self.service_manager and self.service_manager.running:
            if messagebox.askokcancel("Quit", "Service is running. Stop and quit?"):
                self.service_manager.stop()
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        """Run the GUI"""
        self.root.mainloop()