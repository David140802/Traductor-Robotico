import tkinter as tk
from tkinter import ttk, filedialog
import os

from lexer import tokenize
from parser import parse
from translator import translate
from login import LoginWindow

# ─────────────────────────────────────────────
#  CONSTANTES DE ESTILO
# ─────────────────────────────────────────────
BG      = "#0F172A"
PANEL   = "#1E293B"
ACCENT  = "#38BDF8"
SUCCESS = "#4ADE80"
ERROR   = "#F87171"
WARNING = "#FBBF24"
TEXT    = "#E2E8F0"
SUBTEXT = "#94A3B8"
MONO    = "Courier New"
SANS    = "Segoe UI"


# ─────────────────────────────────────────────
#  INTERFAZ GRÁFICA
# ─────────────────────────────────────────────
class TraductorApp(tk.Tk):
    def __init__(self, role="cliente"):
        super().__init__()
        self._role = role
        self.title("Traductor de Lenguaje Formal — Robot Móvil")
        self.geometry("960x680")
        self.minsize(820, 580)
        self.configure(bg=BG)
        self._filepath = None
        self._build_ui()

    # ── UI ──────────────────────────────────────
    def _build_ui(self):
        self._build_header()
        self._build_file_bar()
        self._build_body()
        self._build_footer()

    def _build_header(self):
        hdr = tk.Frame(self, bg="#0EA5E9", height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="🤖  Traductor de Lenguaje Formal — Robot Móvil",
                 font=(SANS, 14, "bold"), bg="#0EA5E9", fg="white").pack(side="left", padx=20)
        role_icon = "🛠" if self._role == "admin" else "👤"
        tk.Label(hdr, text=f"{role_icon}  {self._role.capitalize()}",
                 font=(SANS, 10, "bold"), bg="#0EA5E9", fg="#E0F2FE").pack(side="right", padx=20)
        tk.Label(hdr, text="Lenguajes y Autómatas I  |",
                 font=(SANS, 10), bg="#0EA5E9", fg="#E0F2FE").pack(side="right", padx=4)

    def _build_file_bar(self):
        bar = tk.Frame(self, bg=PANEL, pady=10)
        bar.pack(fill="x", padx=0)

        tk.Label(bar, text="Archivo .txt:", font=(SANS, 10),
                 bg=PANEL, fg=SUBTEXT).pack(side="left", padx=(16, 6))

        self._file_label = tk.Label(bar, text="Ningún archivo seleccionado",
                                    font=(MONO, 10), bg=PANEL, fg=SUBTEXT,
                                    anchor="w", width=52)
        self._file_label.pack(side="left")

        btn_style = dict(font=(SANS, 10, "bold"), relief="flat",
                         cursor="hand2", padx=14, pady=5)

        tk.Button(bar, text="📂  Cargar archivo", bg=ACCENT, fg="#0F172A",
                  command=self._load_file, **btn_style).pack(side="left", padx=(8, 4))

        self._run_btn = tk.Button(bar, text="▶  Traducir", bg="#22C55E", fg="#0F172A",
                                  command=self._run, state="disabled", **btn_style)
        self._run_btn.pack(side="left", padx=4)

        tk.Button(bar, text="🗑  Limpiar", bg="#475569", fg=TEXT,
                  command=self._clear, **btn_style).pack(side="left", padx=4)

    def _build_body(self):
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=16, pady=(12, 0))
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # ── Izquierda: Análisis Sintáctico ──────
        left = tk.Frame(body, bg=BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)

        self._mk_section_label(left, "🔍  Análisis Sintáctico").grid(
            row=0, column=0, sticky="w", pady=(0, 6))

        sint_frame = tk.Frame(left, bg=PANEL, bd=0)
        sint_frame.grid(row=1, column=0, sticky="nsew")
        sint_frame.rowconfigure(0, weight=0)
        sint_frame.rowconfigure(1, weight=1)
        sint_frame.columnconfigure(0, weight=1)

        self._status_badge = tk.Label(sint_frame, text="— Sin analizar —",
                                      font=(SANS, 12, "bold"), bg=PANEL, fg=SUBTEXT,
                                      pady=14)
        self._status_badge.grid(row=0, column=0, sticky="ew", padx=12)

        tk.Frame(sint_frame, bg="#334155", height=1).grid(row=1, column=0, sticky="ew")

        self._mk_section_label(sint_frame, "Código fuente").grid(
            row=2, column=0, sticky="w", padx=12, pady=(10, 4))

        txt_frame = tk.Frame(sint_frame, bg=PANEL)
        txt_frame.grid(row=3, column=0, sticky="nsew", padx=12, pady=(0, 12))
        txt_frame.rowconfigure(0, weight=1)
        txt_frame.columnconfigure(0, weight=1)
        sint_frame.rowconfigure(3, weight=1)

        self._code_text = tk.Text(txt_frame, font=(MONO, 10), bg="#0F172A", fg=TEXT,
                                  insertbackground=ACCENT, relief="flat",
                                  wrap="none", state="disabled",
                                  selectbackground="#334155")
        sb1 = ttk.Scrollbar(txt_frame, command=self._code_text.yview)
        self._code_text.configure(yscrollcommand=sb1.set)
        self._code_text.grid(row=0, column=0, sticky="nsew")
        sb1.grid(row=0, column=1, sticky="ns")

        # ── Derecha: Traducción ─────────────────
        right = tk.Frame(body, bg=BG)
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        self._mk_section_label(right, "📡  Simulación del Robot").grid(
            row=0, column=0, sticky="w", pady=(0, 6))

        trad_frame = tk.Frame(right, bg=PANEL, bd=0)
        trad_frame.grid(row=1, column=0, sticky="nsew")
        trad_frame.rowconfigure(0, weight=1)
        trad_frame.columnconfigure(0, weight=1)

        self._trad_text = tk.Text(trad_frame, font=(SANS, 11), bg=PANEL, fg=TEXT,
                                  insertbackground=ACCENT, relief="flat",
                                  wrap="word", state="disabled",
                                  selectbackground="#334155", padx=14, pady=12,
                                  spacing1=6, spacing3=6)
        sb2 = ttk.Scrollbar(trad_frame, command=self._trad_text.yview)
        self._trad_text.configure(yscrollcommand=sb2.set)
        self._trad_text.grid(row=0, column=0, sticky="nsew")
        sb2.grid(row=0, column=1, sticky="ns")

        self._trad_text.tag_configure("inicio",   foreground=ACCENT,  font=(SANS, 11, "bold"))
        self._trad_text.tag_configure("fin",       foreground=ACCENT,  font=(SANS, 11, "bold"))
        self._trad_text.tag_configure("avanzar",   foreground=SUCCESS)
        self._trad_text.tag_configure("girar",     foreground=WARNING)
        self._trad_text.tag_configure("detener",   foreground=ERROR)
        self._trad_text.tag_configure("error_msg", foreground=ERROR,   font=(SANS, 11, "italic"))

    def _build_footer(self):
        ft = tk.Frame(self, bg="#0F172A", height=30)
        ft.pack(fill="x", side="bottom")
        ft.pack_propagate(False)
        tk.Label(ft, text="BRUGUERA · CASTILLO · TORRES  —  Lenguajes y Autómatas I",
                 font=(SANS, 8), bg="#0F172A", fg="#475569").pack(side="right", padx=16)

    def _mk_section_label(self, parent, text):
        return tk.Label(parent, text=text, font=(SANS, 10, "bold"),
                        bg=parent.cget("bg"), fg=ACCENT)

    # ── Acciones ────────────────────────────────
    def _load_file(self):
        path = filedialog.askopenfilename(
            title="Seleccionar archivo de comandos",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos", "*.*")]
        )
        if not path:
            return
        self._filepath = path
        self._file_label.config(text=os.path.basename(path), fg=TEXT)
        self._run_btn.config(state="normal")

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self._set_code(content)
        self._clear_results()

    def _run(self):
        if not self._filepath:
            return
        with open(self._filepath, "r", encoding="utf-8") as f:
            code = f.read()

        # Léxico
        lines_tokens, lex_errors = tokenize(code)
        if lex_errors:
            self._set_status(False, "Error léxico")
            self._set_translation(
                [("error_msg", "⚠  Errores léxicos encontrados:\n")] +
                [("error_msg", f"   {e}\n") for e in lex_errors]
            )
            return

        # Sintáctico
        valido, msg = parse(lines_tokens)
        self._set_status(valido, msg)
        if not valido:
            self._set_translation([("error_msg", f"⚠  {msg}")])
            return

        # Traducción
        lines_out = translate(lines_tokens)
        tagged = []
        for line in lines_out:
            if "inicia" in line:
                tagged.append(("inicio", line + "\n"))
            elif "finaliza" in line:
                tagged.append(("fin", line + "\n"))
            elif "avanza" in line:
                tagged.append(("avanzar", line + "\n"))
            elif "gira" in line:
                tagged.append(("girar", line + "\n"))
            elif "detiene" in line:
                tagged.append(("detener", line + "\n"))
            else:
                tagged.append(("", line + "\n"))
        self._set_translation(tagged)

    def _clear(self):
        self._filepath = None
        self._file_label.config(text="Ningún archivo seleccionado", fg=SUBTEXT)
        self._run_btn.config(state="disabled")
        self._set_code("")
        self._clear_results()

    # ── Helpers de UI ───────────────────────────
    def _set_code(self, text):
        self._code_text.config(state="normal")
        self._code_text.delete("1.0", "end")
        self._code_text.insert("1.0", text)
        self._code_text.config(state="disabled")

    def _set_status(self, ok, msg):
        color = SUCCESS if ok else ERROR
        icon  = "✅" if ok else "❌"
        self._status_badge.config(text=f"{icon}  {msg}", fg=color)

    def _set_translation(self, tagged_lines):
        self._trad_text.config(state="normal")
        self._trad_text.delete("1.0", "end")
        for tag, line in tagged_lines:
            if tag:
                self._trad_text.insert("end", line, tag)
            else:
                self._trad_text.insert("end", line)
        self._trad_text.config(state="disabled")

    def _clear_results(self):
        self._status_badge.config(text="— Sin analizar —", fg=SUBTEXT)
        self._set_translation([])


# ─────────────────────────────────────────────
#  PUNTO DE ENTRADA
# ─────────────────────────────────────────────
def launch_app(role):
    app = TraductorApp(role=role)
    app.mainloop()

if __name__ == "__main__":
    login = LoginWindow(on_success=launch_app)
    login.mainloop()