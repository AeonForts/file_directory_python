#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, messagebox
import os
import ctypes
import pathlib
import string
import datetime  # Add this import at the top of your file

# Increase Dots Per inch so it looks sharper
ctypes.windll.shcore.SetProcessDpiAwareness(True)

class FileExplorer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Enhanced File Explorer')
        self.geometry('800x600')
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.current_path = tk.StringVar(self, value=str(pathlib.Path.home()))
        self.current_path.trace('w', self.path_change)

        self.setup_ui()
        self.path_change()

    def setup_ui(self):
        # Top frame for navigation
        nav_frame = ttk.Frame(self)
        nav_frame.grid(row=0, column=0, columnspan=2, sticky='ew', padx=5, pady=5)

        ttk.Button(nav_frame, text='⬆️ Up', command=self.go_back).pack(side=tk.LEFT, padx=2)
        ttk.Button(nav_frame, text='🏠 Home', command=self.go_home).pack(side=tk.LEFT, padx=2)
        ttk.Button(nav_frame, text='🔄 Refresh', command=self.refresh).pack(side=tk.LEFT, padx=2)

        self.path_entry = ttk.Entry(nav_frame, textvariable=self.current_path, width=50)
        self.path_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.path_entry.bind('<Return>', self.path_change)

        # Drive selection
        self.drive_var = tk.StringVar(self)
        self.drives = self.get_drives()
        self.drive_var.set(self.drives[0])
        self.drive_menu = ttk.OptionMenu(nav_frame, self.drive_var, self.drives[0], *self.drives, command=self.change_drive)
        self.drive_menu.pack(side=tk.LEFT, padx=2)

        # Main content area
        content_frame = ttk.Frame(self)
        content_frame.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=5, pady=5)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        # Treeview for file list
        self.tree = ttk.Treeview(content_frame, columns=('Size', 'Date Modified'), selectmode='browse')
        self.tree.heading('#0', text='Name', anchor=tk.W)
        self.tree.heading('Size', text='Size', anchor=tk.E)
        self.tree.heading('Date Modified', text='Date Modified', anchor=tk.W)
        self.tree.column('Size', anchor=tk.E, width=100)
        self.tree.column('Date Modified', width=150)
        self.tree.grid(row=0, column=0, sticky='nsew')

        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(content_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.bind('<Double-1>', self.item_selected)
        self.tree.bind('<Return>', self.item_selected)

        # Status bar
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self, textvariable=self.status_var, anchor=tk.W)
        status_bar.grid(row=2, column=0, columnspan=2, sticky='ew', padx=5, pady=2)

        # Menu
        self.create_menu()

    def create_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Folder", command=self.create_folder)
        file_menu.add_command(label="Refresh", command=self.refresh)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)

        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Cut", command=self.not_implemented)
        edit_menu.add_command(label="Copy", command=self.not_implemented)
        edit_menu.add_command(label="Paste", command=self.not_implemented)
        edit_menu.add_command(label="Delete", command=self.delete_selected)

    def path_change(self, *args):
        path = self.current_path.get()
        try:
            # Clear the treeview
            self.tree.delete(*self.tree.get_children())
            
            # List directories first, then files
            dirs = []
            files = []
            with os.scandir(path) as entries:
                for entry in entries:
                    info = entry.stat()
                    date_modified = info.st_mtime
                    date_modified_str = datetime.datetime.fromtimestamp(date_modified).strftime('%Y-%m-%d %H:%M:%S')
                    if entry.is_dir():
                        dirs.append((entry.name, '', date_modified_str))
                    else:
                        size = self.format_size(info.st_size)
                        files.append((entry.name, size, date_modified_str))
            
            # Insert directories
            for item in sorted(dirs):
                self.tree.insert('', 'end', text=item[0], values=item[1:])
            
            # Insert files
            for item in sorted(files):
                self.tree.insert('', 'end', text=item[0], values=item[1:])

            self.status_var.set(f"{len(dirs)} folders, {len(files)} files")
        except PermissionError:
            messagebox.showerror("Error", f"Permission denied: {path}")
        except FileNotFoundError:
            messagebox.showerror("Error", f"Directory not found: {path}")

    def item_selected(self, event):
        selected_item = self.tree.focus()
        if selected_item:
            item_text = self.tree.item(selected_item, 'text')
            path = os.path.join(self.current_path.get(), item_text)
            if os.path.isdir(path):
                self.current_path.set(path)
            else:
                os.startfile(path)

    def go_back(self):
        parent = pathlib.Path(self.current_path.get()).parent
        self.current_path.set(str(parent))

    def go_home(self):
        self.current_path.set(str(pathlib.Path.home()))

    def refresh(self):
        self.path_change()

    def change_drive(self, *args):
        self.current_path.set(self.drive_var.get())

    def get_drives(self):
        return [f"{letter}:\\" for letter in string.ascii_uppercase if os.path.exists(f"{letter}:\\")]

    def create_folder(self):
        folder_name = tk.simpledialog.askstring("New Folder", "Enter folder name:")
        if folder_name:
            new_folder_path = os.path.join(self.current_path.get(), folder_name)
            try:
                os.mkdir(new_folder_path)
                self.refresh()
            except OSError:
                messagebox.showerror("Error", f"Failed to create folder: {new_folder_path}")

    def delete_selected(self):
        selected_item = self.tree.focus()
        if selected_item:
            item_text = self.tree.item(selected_item, 'text')
            path = os.path.join(self.current_path.get(), item_text)
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {item_text}?"):
                try:
                    if os.path.isdir(path):
                        os.rmdir(path)
                    else:
                        os.remove(path)
                    self.refresh()
                except OSError as e:
                    messagebox.showerror("Error", f"Failed to delete {item_text}: {e}")

    def not_implemented(self):
        messagebox.showinfo("Not Implemented", "This feature is not yet implemented.")

    @staticmethod
    def format_size(size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0

    def get_icon(self, name):
        # This is a placeholder. You can implement actual icon fetching here.
        return None

if __name__ == "__main__":
    app = FileExplorer()
    app.mainloop()