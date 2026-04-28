import tkinter as tk
from tkinter import ttk

# ─────────────────────────────────────────────
#  CREDENCIALES
# ─────────────────────────────────────────────
USERS = {
    "admin":   {"password": "admin123", "role": "admin"},
    "cliente": {"password": "cliente123", "role": "cliente"},
}

# ─────────────────────────────────────────────
#  CONSTANTES DE ESTILO
# ─────────────────────────────────────────────
BG      = "#0F172A"
PANEL   = "#1E293B"
ACCENT  = "#38BDF8"
SUCCESS = "#4ADE80"
ERROR   = "#F87171"
TEXT    = "#E2E8F0"
SUBTEXT = "#94A3B8"
SANS    = "Segoe UI"
MONO    = "Courier New"


# ─────────────────────────────────────────────
#  VENTANA DE LOGIN
# ─────────────────────────────────────────────
class LoginWindow(tk.Tk):
    def __init__(self, on_success):
        """
        on_success(role: str) es llamado cuando el login es correcto.
        Recibe el rol del usuario ("admin" o "cliente").
        """
        super().__init__()
        self.on_success = on_success
        self.title("Iniciar sesión")
        self.geometry("420x480")
        self.resizable(False, False)
        self.configure(bg=BG)
        self._build_ui()

    def _build_ui(self):
        # ── Header ──────────────────────────────
        hdr = tk.Frame(self, bg="#0EA5E9", height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="🤖  Robot Móvil",
                 font=(SANS, 14, "bold"), bg="#0EA5E9", fg="white").pack(side="left", padx=20)
        tk.Label(hdr, text="Lenguajes y Autómatas I",
                 font=(SANS, 10), bg="#0EA5E9", fg="#E0F2FE").pack(side="right", padx=20)

        # ── Card central ────────────────────────
        card = tk.Frame(self, bg=PANEL, padx=32, pady=32)
        card.pack(expand=True, fill="both", padx=40, pady=40)

        tk.Label(card, text="Iniciar sesión", font=(SANS, 16, "bold"),
                 bg=PANEL, fg=TEXT).pack(anchor="w", pady=(0, 4))
        tk.Label(card, text="Ingresa tus credenciales para continuar",
                 font=(SANS, 9), bg=PANEL, fg=SUBTEXT).pack(anchor="w", pady=(0, 24))

        # Usuario
        tk.Label(card, text="Usuario", font=(SANS, 10, "bold"),
                 bg=PANEL, fg=SUBTEXT).pack(anchor="w")
        self._user_var = tk.StringVar()
        user_entry = tk.Entry(card, textvariable=self._user_var,
                              font=(MONO, 11), bg="#0F172A", fg=TEXT,
                              insertbackground=ACCENT, relief="flat",
                              highlightthickness=1, highlightbackground="#334155",
                              highlightcolor=ACCENT)
        user_entry.pack(fill="x", ipady=8, pady=(4, 16))

        # Contraseña
        tk.Label(card, text="Contraseña", font=(SANS, 10, "bold"),
                 bg=PANEL, fg=SUBTEXT).pack(anchor="w")
        self._pass_var = tk.StringVar()
        pass_entry = tk.Entry(card, textvariable=self._pass_var, show="●",
                              font=(MONO, 11), bg="#0F172A", fg=TEXT,
                              insertbackground=ACCENT, relief="flat",
                              highlightthickness=1, highlightbackground="#334155",
                              highlightcolor=ACCENT)
        pass_entry.pack(fill="x", ipady=8, pady=(4, 8))

        # Mostrar/ocultar contraseña
        self._show_pass = tk.BooleanVar(value=False)
        tk.Checkbutton(card, text="Mostrar contraseña", variable=self._show_pass,
                       font=(SANS, 9), bg=PANEL, fg=SUBTEXT,
                       activebackground=PANEL, activeforeground=TEXT,
                       selectcolor="#0F172A",
                       command=lambda: pass_entry.config(
                           show="" if self._show_pass.get() else "●"
                       )).pack(anchor="w", pady=(0, 20))

        # Mensaje de error
        self._error_label = tk.Label(card, text="", font=(SANS, 9, "italic"),
                                     bg=PANEL, fg=ERROR)
        self._error_label.pack(anchor="w", pady=(0, 12))

        # Botón de login
        tk.Button(card, text="Ingresar →",
                  font=(SANS, 11, "bold"), relief="flat", cursor="hand2",
                  bg=ACCENT, fg="#0F172A", padx=0, pady=10,
                  command=self._attempt_login).pack(fill="x")

        # Footer de hints
        hint = tk.Frame(card, bg=PANEL)
        hint.pack(fill="x", pady=(20, 0))
        tk.Label(hint, text="👤 admin / cliente", font=(SANS, 8),
                 bg=PANEL, fg="#475569").pack(side="left")
        tk.Label(hint, text="🔑 admin123 / cliente123", font=(SANS, 8),
                 bg=PANEL, fg="#475569").pack(side="right")

        # Bind Enter
        self.bind("<Return>", lambda e: self._attempt_login())
        user_entry.focus()

    def _attempt_login(self):
        username = self._user_var.get().strip()
        password = self._pass_var.get().strip()

        user_data = USERS.get(username)
        if user_data and user_data["password"] == password:
            self._error_label.config(text="")
            role = user_data["role"]
            self.destroy()
            self.on_success(role)
        else:
            self._error_label.config(text="⚠  Usuario o contraseña incorrectos.")
            self._pass_var.set("")