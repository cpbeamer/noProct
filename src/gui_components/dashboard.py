"""Modern dashboard with real-time visualizations"""
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
from collections import deque
import threading
import time

from src.gui_components.themes import theme_manager
from src.gui_components.custom_widgets import (
    CircularProgress, ModernCard, StatusIndicator, AnimatedButton
)

class Dashboard(ctk.CTkFrame):
    """Main dashboard with real-time stats and visualizations"""
    
    def __init__(self, parent, service_manager=None):
        theme = theme_manager.get_theme()
        
        super().__init__(parent, fg_color=theme["bg"])
        
        self.service_manager = service_manager
        self.update_interval = 1000  # milliseconds
        
        # Data storage for graphs
        self.time_data = deque(maxlen=60)
        self.detection_data = deque(maxlen=60)
        self.confidence_data = deque(maxlen=60)
        self.success_data = deque(maxlen=60)
        
        # Initialize with zeros
        for _ in range(60):
            self.time_data.append(datetime.now() - timedelta(seconds=60-_))
            self.detection_data.append(0)
            self.confidence_data.append(0)
            self.success_data.append(0)
        
        self._create_layout()
        self._start_updates()
    
    def _create_layout(self):
        """Create dashboard layout"""
        theme = theme_manager.get_theme()
        
        # Header
        header_frame = ctk.CTkFrame(self, fg_color=theme["bg"])
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        title = ctk.CTkLabel(
            header_frame,
            text="Question Assistant Dashboard",
            font=theme_manager.get_font("heading_xl"),
            text_color=theme["fg"]
        )
        title.pack(side="left")
        
        # Status indicator
        self.status_indicator = StatusIndicator(header_frame, size=16, status="offline")
        self.status_indicator.pack(side="left", padx=10)
        
        self.status_label = ctk.CTkLabel(
            header_frame,
            text="Service Stopped",
            font=theme_manager.get_font("body"),
            text_color=theme["fg_secondary"]
        )
        self.status_label.pack(side="left")
        
        # Main content area with grid
        content_frame = ctk.CTkFrame(self, fg_color=theme["bg"])
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Configure grid
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_columnconfigure(2, weight=1)
        content_frame.grid_rowconfigure(1, weight=1)
        
        # Stats cards row
        self._create_stats_cards(content_frame)
        
        # Charts row
        self._create_charts(content_frame)
        
        # Activity feed
        self._create_activity_feed(content_frame)
    
    def _create_stats_cards(self, parent):
        """Create statistics cards"""
        theme = theme_manager.get_theme()
        
        # Questions Detected Card
        self.questions_card = self._create_stat_card(
            parent,
            title="Questions Detected",
            value="0",
            subtitle="Total this session",
            icon="❓",
            color=theme["accent"]
        )
        self.questions_card.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        # Success Rate Card
        self.success_card = self._create_stat_card(
            parent,
            title="Success Rate",
            value="0%",
            subtitle="Correctly answered",
            icon="✓",
            color=theme["success"]
        )
        self.success_card.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Active Time Card
        self.time_card = self._create_stat_card(
            parent,
            title="Active Time",
            value="00:00",
            subtitle="Session duration",
            icon="⏱",
            color=theme["warning"]
        )
        self.time_card.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
    
    def _create_stat_card(self, parent, title, value, subtitle, icon, color):
        """Create a statistics card"""
        theme = theme_manager.get_theme()
        
        card = ModernCard(parent)
        
        # Icon and title row
        header_frame = ctk.CTkFrame(card, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(15, 5))
        
        icon_label = ctk.CTkLabel(
            header_frame,
            text=icon,
            font=("Segoe UI", 24),
            text_color=color
        )
        icon_label.pack(side="left", padx=(0, 10))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text=title,
            font=theme_manager.get_font("subheading"),
            text_color=theme["fg_secondary"]
        )
        title_label.pack(side="left")
        
        # Value
        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=theme_manager.get_font("heading_lg"),
            text_color=theme["fg"]
        )
        value_label.pack(padx=15, pady=5)
        
        # Store reference for updates
        card.value_label = value_label
        
        # Subtitle
        subtitle_label = ctk.CTkLabel(
            card,
            text=subtitle,
            font=theme_manager.get_font("body_small"),
            text_color=theme["fg_tertiary"]
        )
        subtitle_label.pack(padx=15, pady=(0, 15))
        
        return card
    
    def _create_charts(self, parent):
        """Create chart visualizations"""
        theme = theme_manager.get_theme()
        
        # Charts container
        charts_frame = ctk.CTkFrame(parent, fg_color=theme["bg_secondary"], corner_radius=12)
        charts_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        
        # Chart title
        chart_title = ctk.CTkLabel(
            charts_frame,
            text="Real-time Performance Metrics",
            font=theme_manager.get_font("heading"),
            text_color=theme["fg"]
        )
        chart_title.pack(padx=15, pady=(15, 5))
        
        # Configure matplotlib style
        plt.style.use('dark_background' if theme_manager.current_theme == "dark" else 'default')
        
        # Create figure
        self.fig = Figure(figsize=(8, 4), dpi=80, facecolor=theme["bg_secondary"])
        
        # Create subplots
        self.ax1 = self.fig.add_subplot(121)
        self.ax2 = self.fig.add_subplot(122)
        
        # Style axes
        for ax in [self.ax1, self.ax2]:
            ax.set_facecolor(theme["bg_secondary"])
            ax.tick_params(colors=theme["fg_secondary"])
            ax.spines['bottom'].set_color(theme["border"])
            ax.spines['left'].set_color(theme["border"])
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
        
        # Initialize plots
        self.detection_line, = self.ax1.plot([], [], color=theme["accent"], linewidth=2)
        self.ax1.set_title("Detection Rate", color=theme["fg"], fontsize=10)
        self.ax1.set_xlabel("Time", color=theme["fg_secondary"], fontsize=8)
        self.ax1.set_ylabel("Detections/min", color=theme["fg_secondary"], fontsize=8)
        self.ax1.grid(True, alpha=0.2)
        
        self.confidence_line, = self.ax2.plot([], [], color=theme["success"], linewidth=2)
        self.ax2.set_title("Confidence Score", color=theme["fg"], fontsize=10)
        self.ax2.set_xlabel("Time", color=theme["fg_secondary"], fontsize=8)
        self.ax2.set_ylabel("Confidence", color=theme["fg_secondary"], fontsize=8)
        self.ax2.grid(True, alpha=0.2)
        
        # Embed in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, charts_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=(5, 15))
        
        # Initial empty plot
        self._update_charts()
    
    def _create_activity_feed(self, parent):
        """Create activity feed"""
        theme = theme_manager.get_theme()
        
        # Activity container
        activity_frame = ctk.CTkFrame(parent, fg_color=theme["bg_secondary"], corner_radius=12)
        activity_frame.grid(row=1, column=2, padx=5, pady=5, sticky="nsew")
        
        # Title
        title = ctk.CTkLabel(
            activity_frame,
            text="Activity Feed",
            font=theme_manager.get_font("heading"),
            text_color=theme["fg"]
        )
        title.pack(padx=15, pady=(15, 10))
        
        # Activity list with scrollbar
        list_frame = ctk.CTkFrame(activity_frame, fg_color="transparent")
        list_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Scrollable frame
        self.activity_scroll = ctk.CTkScrollableFrame(
            list_frame,
            fg_color="transparent",
            height=300
        )
        self.activity_scroll.pack(fill="both", expand=True)
        
        # Sample activities (will be updated dynamically)
        self.activity_items = []
        self._add_activity("Service initialized", "info")
    
    def _add_activity(self, message, activity_type="info"):
        """Add item to activity feed"""
        theme = theme_manager.get_theme()
        
        # Activity item frame
        item_frame = ctk.CTkFrame(
            self.activity_scroll,
            fg_color=theme["bg_tertiary"],
            corner_radius=8
        )
        item_frame.pack(fill="x", pady=2)
        
        # Icon based on type
        icons = {
            "info": ("ℹ", theme["accent"]),
            "success": ("✓", theme["success"]),
            "warning": ("⚠", theme["warning"]),
            "error": ("✕", theme["error"])
        }
        
        icon, color = icons.get(activity_type, ("•", theme["fg_secondary"]))
        
        # Icon label
        icon_label = ctk.CTkLabel(
            item_frame,
            text=icon,
            font=("Segoe UI", 12),
            text_color=color,
            width=20
        )
        icon_label.pack(side="left", padx=(10, 5))
        
        # Message
        msg_label = ctk.CTkLabel(
            item_frame,
            text=message,
            font=theme_manager.get_font("body_small"),
            text_color=theme["fg_secondary"],
            anchor="w"
        )
        msg_label.pack(side="left", fill="x", expand=True, pady=8)
        
        # Time
        time_label = ctk.CTkLabel(
            item_frame,
            text=datetime.now().strftime("%H:%M:%S"),
            font=theme_manager.get_font("status"),
            text_color=theme["fg_tertiary"]
        )
        time_label.pack(side="right", padx=(5, 10))
        
        # Keep only last 20 items
        self.activity_items.append(item_frame)
        if len(self.activity_items) > 20:
            self.activity_items[0].destroy()
            self.activity_items.pop(0)
    
    def _update_charts(self):
        """Update chart data"""
        if not self.canvas:
            return
        
        try:
            # Convert time data for plotting
            if len(self.time_data) > 1:
                times = list(self.time_data)
                time_nums = [(t - times[0]).total_seconds() for t in times]
                
                # Update detection rate plot
                self.detection_line.set_data(time_nums, list(self.detection_data))
                self.ax1.relim()
                self.ax1.autoscale_view()
                
                # Update confidence plot
                self.confidence_line.set_data(time_nums, list(self.confidence_data))
                self.ax2.relim()
                self.ax2.autoscale_view()
                self.ax2.set_ylim(0, 1)
                
                # Redraw
                self.canvas.draw_idle()
        except:
            pass
    
    def _start_updates(self):
        """Start periodic updates"""
        self._update_dashboard()
    
    def _update_dashboard(self):
        """Update dashboard with latest data"""
        if self.service_manager and hasattr(self.service_manager, '_stats_tracker'):
            stats = self.service_manager._stats_tracker.get_current_stats()
            
            # Update cards
            self.questions_card.value_label.configure(text=str(stats.get('questions_detected', 0)))
            
            success_rate = stats.get('success_rate', 0) * 100
            self.success_card.value_label.configure(text=f"{success_rate:.1f}%")
            
            runtime = stats.get('runtime', 0)
            hours, remainder = divmod(int(runtime), 3600)
            minutes, seconds = divmod(remainder, 60)
            self.time_card.value_label.configure(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            
            # Update status
            if self.service_manager.running:
                self.status_indicator.set_status("online")
                self.status_label.configure(text="Service Running")
            else:
                self.status_indicator.set_status("offline")
                self.status_label.configure(text="Service Stopped")
            
            # Add data points for graphs
            self.time_data.append(datetime.now())
            self.detection_data.append(stats.get('questions_detected', 0))
            self.confidence_data.append(stats.get('avg_confidence', 0))
            self.success_data.append(success_rate / 100)
            
            # Update charts
            self._update_charts()
        
        # Schedule next update
        self.after(self.update_interval, self._update_dashboard)
    
    def log_activity(self, message: str, activity_type: str = "info"):
        """Public method to log activity"""
        self._add_activity(message, activity_type)