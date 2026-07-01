import os
import json
import customtkinter as ctk
from tkinter import filedialog, messagebox

# Set up the appearance and theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class CodemanNotes(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Codeman Notes")
        self.geometry("800x600")
        self.current_file = None

        # --- UI Layout ---
        
        # Left Sidebar for Actions
        self.sidebar = ctk.CTkFrame(self, width=160, corner_radius=0)
        self.sidebar.pack(side="left", fill="y", padx=0, pady=0)
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="Codeman Notes", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.pack(padx=20, pady=20)

        self.btn_new = ctk.CTkButton(self.sidebar, text="New Note", command=self.new_note)
        self.btn_new.pack(padx=20, pady=10)

        self.btn_open = ctk.CTkButton(self.sidebar, text="Open .note", command=self.open_note)
        self.btn_open.pack(padx=20, pady=10)

        self.btn_save = ctk.CTkButton(self.sidebar, text="Save", command=self.save_note)
        self.btn_save.pack(padx=20, pady=10)

        self.btn_save_as = ctk.CTkButton(self.sidebar, text="Save As...", command=self.save_as_note)
        self.btn_save_as.pack(padx=20, pady=10)
        
        self.status_label = ctk.CTkLabel(self.sidebar, text="No file open", font=ctk.CTkFont(size=11), text_color="gray")
        self.status_label.pack(side="bottom", padx=10, pady=15)

        # Main Editing Area
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        # Title Entry
        self.title_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Note Title...", font=ctk.CTkFont(size=18, weight="bold"), border_width=1)
        self.title_entry.pack(fill="x", pady=(0, 10))

        # Content Textbox
        self.content_text = ctk.CTkTextbox(self.main_frame, font=ctk.CTkFont(size=14), undo=True)
        self.content_text.pack(fill="both", expand=True)

    # --- Functionality ---

    def update_status(self):
        if self.current_file:
            filename = os.path.basename(self.current_file)
            self.status_label.configure(text=f"Editing: {filename}", text_color="#2ecc71")
        else:
            self.status_label.configure(text="New Unsaved Note", text_color="#e67e22")

    def new_note(self):
        self.title_entry.delete(0, "end")
        self.content_text.delete("1.0", "end")
        self.current_file = None
        self.update_status()

    def open_note(self):
        file_path = filedialog.askopenfilename(
            defaultextension=".note",
            filetypes=[("Codeman Note Files", "*.note"), ("All Files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                self.title_entry.delete(0, "end")
                self.title_entry.insert(0, data.get("title", ""))
                
                self.content_text.delete("1.0", "end")
                self.content_text.insert("1.0", data.get("content", ""))
                
                self.current_file = file_path
                self.update_status()
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file:\n{e}")

    def save_note(self):
        if self.current_file:
            try:
                note_data = {
                    "title": self.title_entry.get(),
                    "content": self.content_text.get("1.0", "end-1c")
                }
                with open(self.current_file, "w", encoding="utf-8") as f:
                    json.dump(note_data, f, indent=4)
                self.update_status()
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file:\n{e}")
        else:
            self.save_as_note()

    def save_as_note(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".note",
            filetypes=[("Codeman Note Files", "*.note"), ("All Files", "*.*")]
        )
        
        if file_path:
            self.current_file = file_path
            self.save_note()


if __name__ == "__main__":
    app = CodemanNotes()
    app.mainloop()