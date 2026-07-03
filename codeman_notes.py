import os
import json
import requests
import threading
import webbrowser
import customtkinter as ctk
from tkinter import filedialog, messagebox

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class CodemanNotes(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Codeman Notes")
        self.geometry("1100x650")  # Made window wider to comfortably fit both views
        self.current_file = None
        self.api_key = ""
        self.pending_ai_text = ""

        # Configure background color
        self.configure(fg_color="#1e1e24")

        # --- Top Menu/Ribbon Area ---
        self.ribbon_frame = ctk.CTkFrame(self, height=50, corner_radius=0, fg_color="#16161a")
        self.ribbon_frame.pack(side="top", fill="x")

        self.logo_label = ctk.CTkLabel(self.ribbon_frame, text="Codeman Notes 🖥️", font=ctk.CTkFont(size=15, weight="bold"), text_color="#ffffff")
        self.logo_label.pack(side="left", padx=15, pady=10)

        self.btn_new = ctk.CTkButton(self.ribbon_frame, text="New Note", width=90, height=28, fg_color="transparent", hover_color="#2a2a35", text_color="#dfdfdf", command=self.new_note)
        self.btn_new.pack(side="left", padx=5, pady=10)

        self.btn_open = ctk.CTkButton(self.ribbon_frame, text="Open .note", width=90, height=28, fg_color="transparent", hover_color="#2a2a35", text_color="#dfdfdf", command=self.open_note)
        self.btn_open.pack(side="left", padx=5, pady=10)

        self.btn_save = ctk.CTkButton(self.ribbon_frame, text="Save", width=80, height=28, fg_color="transparent", hover_color="#2a2a35", text_color="#dfdfdf", command=self.save_note)
        self.btn_save.pack(side="left", padx=5, pady=10)

        self.btn_ai_help = ctk.CTkButton(self.ribbon_frame, text="✨ AI Help", width=90, height=28, fg_color="#3a3af4", hover_color="#2727c7", text_color="#ffffff", font=ctk.CTkFont(weight="bold"), command=self.open_ai_setup)
        self.btn_ai_help.pack(side="right", padx=15, pady=10)

        # --- Workspace Outer Container ---
        self.workspace_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.workspace_frame.pack(side="top", fill="both", expand=True, padx=20, pady=(15, 5))

        # --- Left Workspace Area (Notepad) ---
        self.main_frame = ctk.CTkFrame(self.workspace_frame, fg_color="transparent")
        self.main_frame.pack(side="left", fill="both", expand=True)

        self.title_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Untitled Note Title...", font=ctk.CTkFont(size=18, weight="bold"), fg_color="#16161a", border_color="#2a2a35", text_color="#ffffff", height=40)
        self.title_entry.pack(fill="x", pady=(0, 15))

        self.content_text = ctk.CTkTextbox(self.main_frame, font=ctk.CTkFont(family="Consolas", size=14), fg_color="#16161a", border_color="#2a2a35", text_color="#e0e0e0", undo=True, border_width=1)
        self.content_text.pack(fill="both", expand=True)

        # --- Right Workspace Area (AI Space - Initially Hidden) ---
        self.ai_panel = ctk.CTkFrame(self.workspace_frame, width=280, fg_color="#16161a", border_color="#2a2a35", border_width=1)
        # self.ai_panel.pack() -> Triggered dynamically on API key submission.

        self.ai_title = ctk.CTkLabel(self.ai_panel, text="Groq Assistant", font=ctk.CTkFont(size=14, weight="bold"), text_color="#3a3af4")
        self.ai_title.pack(pady=10)

        # Permission Banner (Hidden by default, shows up when AI generation finishes)
        self.permission_frame = ctk.CTkFrame(self.ai_panel, fg_color="#2727c7", corner_radius=6)
        self.perm_label = ctk.CTkLabel(self.permission_frame, text="Paste this output to your notes?", text_color="white", font=ctk.CTkFont(size=11, weight="bold"))
        self.perm_label.pack(pady=(5, 2))
        
        self.perm_btn_frame = ctk.CTkFrame(self.permission_frame, fg_color="transparent")
        self.perm_btn_frame.pack(pady=(0, 5))
        self.btn_yes = ctk.CTkButton(self.perm_btn_frame, text="Yes", width=50, height=22, fg_color="#2ecc71", hover_color="#27ae60", command=self.accept_ai_paste)
        self.btn_yes.pack(side="left", padx=5)
        self.btn_no = ctk.CTkButton(self.perm_btn_frame, text="No", width=50, height=22, fg_color="#e74c3c", hover_color="#c0392b", command=self.decline_ai_paste)
        self.btn_no.pack(side="left", padx=5)

        # AI Chat Log view
        self.ai_output = ctk.CTkTextbox(self.ai_panel, font=ctk.CTkFont(size=12), fg_color="#1e1e24", border_width=0, text_color="#d0d0d0")
        self.ai_output.pack(fill="both", expand=True, padx=10, pady=10)

        # AI Prompt Entry Box
        self.ai_input = ctk.CTkEntry(self.ai_panel, placeholder_text="Ask AI assistant anything...", border_color="#2a2a35")
        self.ai_input.pack(fill="x", padx=10, pady=(0, 5))
        self.ai_input.bind("<Return>", lambda event: self.send_ai_prompt())

        self.btn_send_ai = ctk.CTkButton(self.ai_panel, text="Ask Assistant", fg_color="#3a3af4", hover_color="#2727c7", command=self.send_ai_prompt)
        self.btn_send_ai.pack(fill="x", padx=10, pady=(0, 10))

        # --- Bottom Status Bar ---
        self.status_bar = ctk.CTkFrame(self, height=25, corner_radius=0, fg_color="#111114")
        self.status_bar.pack(side="bottom", fill="x")
        
        self.status_label = ctk.CTkLabel(self.status_bar, text="Ln 1, Col 1 | New Unsaved Note", font=ctk.CTkFont(size=11), text_color="#7b7b8f")
        self.status_label.pack(side="left", padx=15, pady=2)

    # --- File Management Functionality ---

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
        file_path = filedialog.askopenfilename(defaultextension=".note", filetypes=[("Codeman Note Files", "*.note"), ("All Files", "*.*")])
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
                note_data = {"title": self.title_entry.get(), "content": self.content_text.get("1.0", "end-1c")}
                with open(self.current_file, "w", encoding="utf-8") as f:
                    json.dump(note_data, f, indent=4)
                self.update_status()
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file:\n{e}")
        else:
            self.save_as_note()

    def save_as_note(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".note", filetypes=[("Codeman Note Files", "*.note"), ("All Files", "*.*")])
        if file_path:
            self.current_file = file_path
            self.save_note()

    # --- AI Help Logic ---

    def open_ai_setup(self):
        self.ai_window = ctk.CTkToplevel(self)
        self.ai_window.title("AI Help Configuration")
        self.ai_window.geometry("450x250")
        self.ai_window.resizable(False, False)
        self.ai_window.after(200, lambda: self.ai_window.focus())

        label = ctk.CTkLabel(self.ai_window, text="Enter Groq API Key:", font=ctk.CTkFont(size=14, weight="bold"))
        label.pack(pady=(25, 10))

        self.api_entry = ctk.CTkEntry(self.ai_window, width=350, placeholder_text="gsk_...", show="*")
        self.api_entry.pack(pady=10)
        if self.api_key:
            self.api_entry.insert(0, self.api_key)

        btn_frame = ctk.CTkFrame(self.ai_window, fg_color="transparent")
        btn_frame.pack(pady=15)

        save_btn = ctk.CTkButton(btn_frame, text="Save Key", width=100, command=self.save_api_key)
        save_btn.pack(side="left", padx=10)

        no_key_btn = ctk.CTkButton(btn_frame, text="Don't have an API key?", width=160, fg_color="transparent", border_width=1, hover_color="#2a2a35", command=self.open_instructions_window)
        no_key_btn.pack(side="left", padx=10)

    def save_api_key(self):
        key = self.api_entry.get().strip()
        if key:
            self.api_key = key
            self.ai_window.destroy()
            
            # Squeezes the notepad layout and pulls the AI module view in seamlessly
            self.ai_panel.pack(side="right", fill="both", before=None, padx=(20, 0))
            messagebox.showinfo("AI Activated", "Groq AI panel successfully opened on the right side!")
        else:
            messagebox.showwarning("Warning", "Please enter a valid key.")

    def open_instructions_window(self):
        instr_window = ctk.CTkToplevel(self.ai_window)
        instr_window.title("How to get a Groq API Key")
        instr_window.geometry("500x320")
        instr_window.resizable(False, False)
        instr_window.after(200, lambda: instr_window.focus())

        title = ctk.CTkLabel(instr_window, text="Instructions to Get an API Key", font=ctk.CTkFont(size=16, weight="bold"), text_color="#3a3af4")
        title.pack(pady=(20, 10))

        instructions_text = (
            "1. Go to the official Groq Console website.\n"
            "2. Create a free account or login.\n"
            "3. Navigate to the 'API Keys' section in the sidebar menu.\n"
            "4. Click on 'Create API Key'.\n"
            "5. Give it a name (e.g., CodemanNotes), then copy the generated key.\n"
            "6. Paste it directly into the input field behind this window!"
        )

        textbox = ctk.CTkTextbox(instr_window, width=440, height=130, font=ctk.CTkFont(size=12))
        textbox.pack(pady=10)
        textbox.insert("1.0", instructions_text)
        textbox.configure(state="disabled")

        link_btn = ctk.CTkButton(instr_window, text="Open Groq Console Website", fg_color="#2ecc71", hover_color="#27ae60", text_color="#ffffff", command=lambda: webbrowser.open("https://console.groq.com/"))
        link_btn.pack(pady=10)

    # --- Live AI Execution and Handlers ---

    def send_ai_prompt(self):
        prompt = self.ai_input.get().strip()
        if not prompt:
            return

        self.ai_output.configure(state="normal")
        self.ai_output.insert("end", f"\nYou: {prompt}\n\nAI Thinking...")
        self.ai_output.configure(state="disabled")
        self.ai_input.delete(0, "end")
        self.permission_frame.pack_forget() # Reset banner element positions

        threading.Thread(target=self.fetch_groq_response, args=(prompt,), daemon=True).start()

    def fetch_groq_response(self, prompt):
        url = "https://api.groq.com/openai/v1/chat/completions"
        clean_key = self.api_key.strip()
        
        headers = {
            "Authorization": f"Bearer {clean_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.1-8b-instant",  # Corrected highly-stable model ID
            "messages": [{"role": "user", "content": prompt}]
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            if response.status_code == 200:
                result_json = response.json()
                ai_text = result_json["choices"][0]["message"]["content"]
                
                self.after(0, lambda: self.display_ai_result(ai_text))
            else:
                self.after(0, lambda: self.display_ai_error(f"Status {response.status_code}: {response.text}"))
        except Exception as e:
            self.after(0, lambda: self.display_ai_error(str(e)))

    def display_ai_result(self, result_text):
        self.pending_ai_text = result_text
        self.ai_output.configure(state="normal")
        
        # Strip off the "AI Thinking..." string indicator smoothly
        self.ai_output.delete("end-12c", "end") 
        self.ai_output.insert("end", f"Assistant: {result_text}\n")
        self.ai_output.configure(state="disabled")
        self.ai_output.see("end")

        # Slide down the notification verification banner safely
        self.permission_frame.pack(side="top", fill="x", padx=10, pady=5, before=self.ai_output)

    def display_ai_error(self, err_msg):
        self.ai_output.configure(state="normal")
        self.ai_output.delete("end-12c", "end")
        self.ai_output.insert("end", f"System Error: {err_msg}\n")
        self.ai_output.configure(state="disabled")

    def accept_ai_paste(self):
        self.content_text.insert("insert", f"\n{self.pending_ai_text}\n")
        self.permission_frame.pack_forget()
        self.pending_ai_text = ""

    def decline_ai_paste(self):
        self.permission_frame.pack_forget()
        self.pending_ai_text = ""


if __name__ == "__main__":
    app = CodemanNotes()
    app.mainloop()