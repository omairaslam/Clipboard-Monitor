#!/usr/bin/env python3
"""
Clipboard History Viewer - Ultra Simplified Version
"""

import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import pyperclip

class ClipboardHistoryViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Clipboard History Viewer")
        self.root.geometry("800x600")

        # Ensure window appears on top and gets focus
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after_idle(lambda: self.root.attributes('-topmost', False))
        self.root.focus_force()

        # Set up the history file path
        self.history_path = os.path.expanduser("~/Library/Application Support/ClipboardMonitor/clipboard_history.json")

        # Create text widget instead of listbox (listbox has display issues)
        text_frame = tk.Frame(root)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Create scrollbar
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create text widget
        self.history_text = tk.Text(
            text_frame,
            yscrollcommand=scrollbar.set,
            font=("Courier", 11),
            bg="white",
            fg="black",
            wrap=tk.WORD,
            cursor="hand2",
            state=tk.DISABLED
        )
        self.history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.history_text.yview)

        # Bind events
        self.history_text.bind("<Double-Button-1>", self.on_double_click)
        self.history_text.bind("<Button-1>", self.on_click)

        # Create simple button frame
        button_frame = ttk.Frame(root)
        button_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        ttk.Button(button_frame, text="Copy Selected", command=self.copy_to_clipboard).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Selected", command=self.delete_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear All", command=self.clear_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Refresh", command=self.load_history).pack(side=tk.RIGHT, padx=5)

        # Load the history
        self.load_history()

    def on_double_click(self, event):
        """Handle double-click to copy item"""
        # Get clicked line and try to find corresponding history item
        try:
            index = self.history_text.index(tk.CURRENT)
            line_num = int(index.split('.')[0])
            line_content = self.history_text.get(f"{line_num}.0", f"{line_num}.end")

            # Look for item number in the text
            if line_content.startswith('[') and ']' in line_content:
                item_num_str = line_content.split(']')[0][1:]
                item_num = int(item_num_str) - 1  # Convert to 0-based index

                if 0 <= item_num < len(self.history):
                    content = self.history[item_num].get('content', '')
                    pyperclip.copy(content)
                    messagebox.showinfo("Copied", f"Copied item {item_num + 1} to clipboard")
                    print(f"Copied item {item_num + 1}: {content[:50]}...")
        except Exception as e:
            print(f"Double-click error: {e}")
            self.copy_to_clipboard()  # Fallback
    
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

            # Show status in window title
            self.root.title(f"Clipboard History Viewer ({len(self.history)} items)")

            # Clear and populate text widget
            self.history_text.config(state=tk.NORMAL)
            self.history_text.delete(1.0, tk.END)

            if not self.history:
                self.history_text.insert(tk.END, "No clipboard history found.\nCopy something to start tracking!")
            else:
                # Add each history item with clear formatting
                for i, item in enumerate(self.history):
                    try:
                        timestamp = datetime.datetime.fromtimestamp(item.get('timestamp', 0))
                        content = item.get('content', '').strip()

                        # Format entry
                        time_str = timestamp.strftime('%m/%d %H:%M')
                        separator = "-" * 50

                        # Detect content type for better display
                        content_type = ""
                        display_content = content
                        if content.startswith('{\\rtf') or (content.startswith('{') and 'deff0' in content and 'ttbl' in content):
                            content_type = " [🎨 RTF Content - converted from Markdown]"
                            # Show a more user-friendly preview for RTF
                            display_content = f"RTF Content (Rich Text Format)\n{content}\n\n💡 This RTF content will appear formatted when pasted into compatible applications."

                        # Add item
                        self.history_text.insert(tk.END, f"{separator}\n")
                        self.history_text.insert(tk.END, f"[{i+1}] {time_str}{content_type}\n")
                        self.history_text.insert(tk.END, f"{display_content}\n")
                        self.history_text.insert(tk.END, f"{separator}\n\n")

                    except Exception as item_error:
                        self.history_text.insert(tk.END, f"Error displaying item {i}: {item_error}\n\n")

            # Make read-only
            self.history_text.config(state=tk.DISABLED)

            # Force GUI update
            self.root.update_idletasks()

            print(f"Loaded {len(self.history)} items into text widget")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load history: {e}\nHistory path: {self.history_path}")
    
    def on_click(self, event):
        """Handle click on text widget"""
        # Get clicked line
        index = self.history_text.index(tk.CURRENT)
        line_num = int(index.split('.')[0])
        line_content = self.history_text.get(f"{line_num}.0", f"{line_num}.end")
        print(f"Clicked line {line_num}: {line_content}")

    def copy_to_clipboard(self):
        """Copy selected item to clipboard"""
        # For now, just copy the first item as a fallback
        if self.history:
            content = self.history[0].get('content', '')
            pyperclip.copy(content)
            messagebox.showinfo("Success", "Most recent item copied to clipboard")
        else:
            messagebox.showinfo("Info", "No history items to copy")

    def delete_item(self):
        """Delete functionality - simplified for text widget"""
        messagebox.showinfo("Info", "Individual item deletion not implemented in text widget version.\nUse 'Clear All' to clear entire history.")
    
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
