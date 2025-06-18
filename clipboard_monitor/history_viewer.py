#!/usr/bin/env python3
"""
Clipboard History Viewer
A simple GUI application to view and manage clipboard history.
"""

import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from pathlib import Path
import pyperclip

class ClipboardHistoryViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Clipboard History Viewer")
        self.root.geometry("800x600")
        
        # Set up the history file path from config
        self.history_path = self.get_history_path()
        
        # Create the main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create the history list
        self.create_history_list()
        
        # Create the preview area
        self.create_preview_area()
        
        # Create the button bar
        self.create_button_bar()
        
        # Load the history
        self.load_history()

    def get_history_path(self):
        """Get the history file path from config or use default"""
        try:
            # Try to load from config file
            config_path = os.path.expanduser("~/Library/Application Support/ClipboardMonitor/config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    if 'history' in config and 'save_location' in config['history']:
                        return os.path.expanduser(config['history']['save_location'])
        except Exception:
            pass  # Fall back to default

        # Default path
        return os.path.expanduser(
            "~/Library/Application Support/ClipboardMonitor/clipboard_history.json"
        )

    def create_history_list(self):
        """Create the history list widget"""
        list_frame = ttk.LabelFrame(self.main_frame, text="Clipboard History", padding="5")
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create a scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create the listbox
        self.history_list = tk.Listbox(
            list_frame, 
            yscrollcommand=scrollbar.set,
            font=("TkDefaultFont", 12),
            selectmode=tk.SINGLE
        )
        self.history_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure the scrollbar
        scrollbar.config(command=self.history_list.yview)
        
        # Bind selection event
        self.history_list.bind("<<ListboxSelect>>", self.on_item_select)
    
    def create_preview_area(self):
        """Create the preview area widget"""
        preview_frame = ttk.LabelFrame(self.main_frame, text="Content Preview", padding="5")
        preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Create a scrollbar
        scrollbar = ttk.Scrollbar(preview_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create the text widget
        self.preview_text = tk.Text(
            preview_frame,
            yscrollcommand=scrollbar.set,
            wrap=tk.WORD,
            font=("Courier", 12)
        )
        self.preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure the scrollbar
        scrollbar.config(command=self.preview_text.yview)
        
        # Make the text widget read-only
        self.preview_text.config(state=tk.DISABLED)
    
    def create_button_bar(self):
        """Create the button bar widget"""
        button_frame = ttk.Frame(self.root, padding="10")
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create the buttons
        self.copy_button = ttk.Button(
            button_frame, 
            text="Copy to Clipboard",
            command=self.copy_to_clipboard
        )
        self.copy_button.pack(side=tk.LEFT, padx=5)
        
        self.delete_button = ttk.Button(
            button_frame,
            text="Delete Item",
            command=self.delete_item
        )
        self.delete_button.pack(side=tk.LEFT, padx=5)
        
        self.clear_button = ttk.Button(
            button_frame,
            text="Clear History",
            command=self.clear_history
        )
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        self.refresh_button = ttk.Button(
            button_frame,
            text="Refresh",
            command=self.load_history
        )
        self.refresh_button.pack(side=tk.RIGHT, padx=5)
    
    def load_history(self):
        """Load the clipboard history from the file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.history_path), exist_ok=True)
            
            # Load the history file if it exists
            if os.path.exists(self.history_path):
                with open(self.history_path, 'r') as f:
                    self.history = json.load(f)
            else:
                self.history = []
            
            # Clear the listbox
            self.history_list.delete(0, tk.END)
            
            # Add items to the listbox (most recent first)
            # History is already in reverse chronological order, so don't reverse it
            for item in self.history:
                try:
                    timestamp = datetime.datetime.fromtimestamp(item.get('timestamp', 0))
                    content = item.get('content', '')

                    # Truncate content for display
                    display_content = content[:50].replace('\n', ' ').replace('\r', ' ')
                    if len(content) > 50:
                        display_content += '...'

                    # Format the display string
                    display_string = f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {display_content}"

                    # Add to listbox
                    self.history_list.insert(tk.END, display_string)
                except Exception as item_error:
                    # Skip problematic items but continue processing
                    continue
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load history: {e}")
    
    def on_item_select(self, event):
        """Handle item selection in the listbox"""
        try:
            # Get the selected index
            selection = self.history_list.curselection()
            if not selection:
                return
            
            # Get the corresponding history item (direct order since we're not reversing)
            index = selection[0]
            if index < 0 or index >= len(self.history):
                return

            item = self.history[index]
            content = item.get('content', '')
            
            # Update the preview text
            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, content)
            self.preview_text.config(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to display item: {e}")
    
    def copy_to_clipboard(self):
        """Copy the selected item to the clipboard"""
        try:
            # Get the selected index
            selection = self.history_list.curselection()
            if not selection:
                messagebox.showinfo("Info", "No item selected")
                return
            
            # Get the corresponding history item (direct order since we're not reversing)
            index = selection[0]
            if index < 0 or index >= len(self.history):
                return

            item = self.history[index]
            content = item.get('content', '')
            
            # Copy to clipboard
            pyperclip.copy(content)
            
            messagebox.showinfo("Success", "Content copied to clipboard")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy to clipboard: {e}")
    
    def delete_item(self):
        """Delete the selected item from history"""
        try:
            # Get the selected index
            selection = self.history_list.curselection()
            if not selection:
                messagebox.showinfo("Info", "No item selected")
                return
            
            # Get the corresponding history item (direct order since we're not reversing)
            index = selection[0]
            if index < 0 or index >= len(self.history):
                return
            
            # Confirm deletion
            if not messagebox.askyesno("Confirm", "Delete this item from history?"):
                return
            
            # Remove the item
            self.history.pop(index)
            
            # Save the updated history
            self.save_history()
            
            # Reload the history
            self.load_history()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete item: {e}")
    
    def clear_history(self):
        """Clear all history"""
        try:
            # Confirm clearing
            if not messagebox.askyesno("Confirm", "Clear all clipboard history?"):
                return
            
            # Clear the history
            self.history = []
            
            # Save the updated history
            self.save_history()
            
            # Reload the history
            self.load_history()
            
            messagebox.showinfo("Success", "Clipboard history cleared")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear history: {e}")
    
    def save_history(self):
        """Save the history to the file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.history_path), exist_ok=True)
            
            # Save the history
            with open(self.history_path, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save history: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ClipboardHistoryViewer(root)
    root.mainloop()
