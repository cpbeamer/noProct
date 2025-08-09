import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config_manager import ConfigManager

class QuestionAssistantGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Question Assistant Setup")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        self.config_manager = ConfigManager()
        
        self.setup_styles()
        self.create_widgets()
        self.center_window()
    
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('vista' if sys.platform == 'win32' else 'default')
        
        self.root.configure(bg='#f0f0f0')
    
    def center_window(self):
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 500) // 2
        y = (screen_height - 400) // 2
        self.root.geometry(f"500x400+{x}+{y}")
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        title_label = ttk.Label(main_frame, text="Question Assistant Configuration", 
                               font=('Arial', 14, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        ttk.Label(main_frame, text="Question Context:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.context_text = tk.Text(main_frame, height=4, width=50)
        self.context_text.grid(row=2, column=0, columnspan=2, pady=5)
        self.context_text.insert('1.0', "e.g., History questions on World War II")
        
        ttk.Label(main_frame, text="Session Duration (minutes):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.duration_var = tk.StringVar(value="60")
        duration_entry = ttk.Entry(main_frame, textvariable=self.duration_var, width=20)
        duration_entry.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(main_frame, text="Number of Questions:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.num_questions_var = tk.StringVar(value="10")
        num_questions_entry = ttk.Entry(main_frame, textvariable=self.num_questions_var, width=20)
        num_questions_entry.grid(row=4, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(main_frame, text="Question Type:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.question_type_var = tk.StringVar(value="Multiple Choice")
        question_type_combo = ttk.Combobox(main_frame, textvariable=self.question_type_var, 
                                          values=["Multiple Choice", "True/False", "Short Answer", "Mixed"],
                                          state="readonly", width=18)
        question_type_combo.grid(row=5, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(main_frame, text="API Key (Anthropic):").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.api_key_var = tk.StringVar()
        api_key_entry = ttk.Entry(main_frame, textvariable=self.api_key_var, show="*", width=40)
        api_key_entry.grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=5, padx=(120, 0))
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=30)
        
        start_btn = ttk.Button(button_frame, text="Start Service", command=self.start_service)
        start_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.root.quit)
        cancel_btn.pack(side=tk.LEFT, padx=5)
    
    def validate_inputs(self):
        context = self.context_text.get('1.0', tk.END).strip()
        if not context or context == "e.g., History questions on World War II":
            messagebox.showerror("Input Error", "Please enter a valid question context")
            return False
        
        try:
            duration = int(self.duration_var.get())
            if duration <= 0 or duration > 300:
                raise ValueError
        except ValueError:
            messagebox.showerror("Input Error", "Duration must be between 1 and 300 minutes")
            return False
        
        try:
            num_questions = int(self.num_questions_var.get())
            if num_questions <= 0 or num_questions > 100:
                raise ValueError
        except ValueError:
            messagebox.showerror("Input Error", "Number of questions must be between 1 and 100")
            return False
        
        if not self.api_key_var.get().strip():
            messagebox.showwarning("API Key", "No API key provided. AI features will be limited.")
        
        return True
    
    def start_service(self):
        if not self.validate_inputs():
            return
        
        config_data = {
            "context": self.context_text.get('1.0', tk.END).strip(),
            "duration_minutes": int(self.duration_var.get()),
            "num_questions": int(self.num_questions_var.get()),
            "question_type": self.question_type_var.get(),
            "api_key": self.api_key_var.get().strip(),
            "monitoring_interval": 5,
            "abort_key": "ctrl+alt+q"
        }
        
        if self.config_manager.save_config(config_data):
            messagebox.showinfo("Success", "Configuration saved. Starting background service...")
            self.root.quit()
            self.launch_background_service()
        else:
            messagebox.showerror("Error", "Failed to save configuration")
    
    def launch_background_service(self):
        import subprocess
        service_path = os.path.join(os.path.dirname(__file__), "background_service.py")
        try:
            subprocess.Popen([sys.executable, service_path], 
                           creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
        except Exception as e:
            print(f"Failed to launch background service: {e}")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = QuestionAssistantGUI()
    app.run()