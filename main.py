import tkinter as tk
from tkinter import ttk, filedialog, messagebox
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
PANEL2  = "#162032"
ACCENT  = "#38BDF8"
SUCCESS = "#4ADE80"
ERROR   = "#F87171"
WARNING = "#FBBF24"
TEXT    = "#E2E8F0"
SUBTEXT = "#94A3B8"
BORDER  = "#334155"
MONO    = "Courier New"
SANS    = "Segoe UI"

# Colores para tipos de token en la tabla
TOKEN_COLORS = {
    'TK_INICIO':    "#38BDF8",
    'TK_FIN':       "#38BDF8",
    'TK_AVANZAR':   "#4ADE80",
    'TK_GIRAR':     "#4ADE80",
    'TK_DERECHA':   "#FBBF24",
    'TK_IZQUIERDA': "#FBBF24",
    'TK_DETENER':   "#F87171",
    'TK_NUMERO':    "#C084FC",
}


# ─────────────────────────────────────────────
#  WIDGET: ÁRBOL SINTÁCTICO EN CANVAS
# ─────────────────────────────────────────────
class TreeCanvas(tk.Canvas):
    NODE_W  = 110
    NODE_H  = 32
    H_GAP   = 24
    V_GAP   = 52

    COLORS = {
        'programa':      ("#0EA5E9", "#E0F2FE"),
        'instrucciones': ("#8B5CF6", "#EDE9FE"),
        'instruccion':   ("#6366F1", "#E0E7FF"),
        'TK_INICIO':     ("#0EA5E9", "#E0F2FE"),
        'TK_FIN':        ("#0EA5E9", "#E0F2FE"),
        'TK_AVANZAR':    ("#22C55E", "#DCFCE7"),
        'TK_GIRAR':      ("#F59E0B", "#FEF3C7"),
        'TK_DERECHA':    ("#F59E0B", "#FEF3C7"),
        'TK_IZQUIERDA':  ("#F59E0B", "#FEF3C7"),
        'TK_DETENER':    ("#EF4444", "#FEE2E2"),
        'TK_NUMERO':     ("#A855F7", "#F3E8FF"),
        'ERROR':         ("#F87171", "#FEE2E2"),
    }
    DEFAULT_COLOR = ("#475569", "#F1F5F9")

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=BG, highlightthickness=0, **kw)
        self._positions = {}

    def draw_tree(self, root_node):
        self.delete("all")
        if root_node is None:
            self.create_text(200, 100, text="Sin árbol generado",
                             fill=SUBTEXT, font=(SANS, 11))
            return

        # Forzar que el canvas tenga dimensiones reales
        self.update_idletasks()

        # Calcular posiciones
        positions = {}
        self._assign_positions(root_node, positions, x_counter=[0])

        if not positions:
            return

        all_x = [x for x, _ in positions.values()]
        all_d = [d for _, d in positions.values()]
        min_x, max_x = min(all_x), max(all_x)
        max_depth = max(all_d)

        num_cols  = int(max_x - min_x) + 1
        canvas_w  = max(self.winfo_width(), num_cols * (self.NODE_W + self.H_GAP) + 80)
        canvas_h  = (max_depth + 1) * (self.NODE_H + self.V_GAP) + 80

        self.configure(scrollregion=(0, 0, canvas_w, canvas_h))

        # Centrar horizontalmente si el árbol cabe en el canvas
        offset_x = max(20, (canvas_w - num_cols * (self.NODE_W + self.H_GAP)) // 2)

        # Pixel positions
        px = {}
        for node_id, (col, depth) in positions.items():
            x = offset_x + (col - min_x) * (self.NODE_W + self.H_GAP)
            y = 30 + depth * (self.NODE_H + self.V_GAP)
            px[node_id] = (x, y)

        # Dibujar líneas primero
        self._draw_edges(root_node, px)
        # Dibujar nodos encima
        self._draw_nodes(root_node, px)

    def _assign_positions(self, node, positions, x_counter, depth=0):
        if not node.children:
            positions[id(node)] = (x_counter[0], depth)
            x_counter[0] += 1
        else:
            child_xs = []
            for child in node.children:
                self._assign_positions(child, positions, x_counter, depth + 1)
                child_xs.append(positions[id(child)][0])
            center = (child_xs[0] + child_xs[-1]) / 2
            positions[id(node)] = (center, depth)

    def _draw_edges(self, node, px):
        if id(node) not in px:
            return
        nx, ny = px[id(node)]
        for child in node.children:
            if id(child) in px:
                cx, cy = px[id(child)]
                self.create_line(
                    nx + self.NODE_W // 2, ny + self.NODE_H,
                    cx + self.NODE_W // 2, cy,
                    fill=BORDER, width=1.5, smooth=True
                )
            self._draw_edges(child, px)

    def _draw_nodes(self, node, px):
        if id(node) not in px:
            return
        x, y = px[id(node)]
        cx = x + self.NODE_W // 2

        key = node.token_type or node.label
        border_c, fill_c = self.COLORS.get(key, self.DEFAULT_COLOR)

        # sombra (tkinter no soporta alpha, usamos color sólido oscuro)
        self.create_rectangle(x+3, y+3, x+self.NODE_W+3, y+self.NODE_H+3,
                               fill="#0A111E", outline="")
        # fondo del nodo
        self.create_rectangle(x, y, x+self.NODE_W, y+self.NODE_H,
                               fill="#1E293B", outline=border_c, width=2)
        # texto
        label = node.label
        if len(label) > 13:
            label = label[:12] + "…"
        self.create_text(cx, y + self.NODE_H // 2,
                         text=label, fill=border_c,
                         font=(MONO, 8, "bold"))

        for child in node.children:
            self._draw_nodes(child, px)


# ─────────────────────────────────────────────
#  APLICACIÓN PRINCIPAL
# ─────────────────────────────────────────────
class TraductorApp(tk.Tk):
    def __init__(self, role="cliente"):
        super().__init__()
        self._role     = role
        self._filepath = None
        self._tree_root = None

        self.title("Traductor de Lenguaje Formal — Robot Móvil")
        self.geometry("1280x780")
        self.minsize(1000, 640)
        self.configure(bg=BG)

        self._style_ttk()
        self._build_ui()

    # ── estilos ttk ─────────────────────────────
    def _style_ttk(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TNotebook",        background=BG,    borderwidth=0)
        s.configure("TNotebook.Tab",    background=PANEL,  foreground=SUBTEXT,
                    padding=[14, 6],   font=(SANS, 9, "bold"))
        s.map("TNotebook.Tab",
              background=[("selected", BG)],
              foreground=[("selected", ACCENT)])
        s.configure("Treeview",         background=PANEL2, foreground=TEXT,
                    fieldbackground=PANEL2, rowheight=26,
                    font=(MONO, 9))
        s.configure("Treeview.Heading", background=PANEL, foreground=ACCENT,
                    font=(SANS, 9, "bold"), relief="flat")
        s.map("Treeview", background=[("selected", "#1E3A5F")])
        s.configure("TScrollbar", background=PANEL, troughcolor=BG, borderwidth=0)

    # ── UI ──────────────────────────────────────
    def _build_ui(self):
        self._build_header()
        self._build_toolbar()
        self._build_body()
        self._build_footer()

    def _build_header(self):
        hdr = tk.Frame(self, bg="#0EA5E9", height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="🤖  Traductor de Lenguaje Formal — Robot Móvil",
                 font=(SANS, 13, "bold"), bg="#0EA5E9", fg="white").pack(side="left", padx=20)
        role_icon = "🛠" if self._role == "admin" else "👤"
        tk.Label(hdr, text=f"{role_icon}  {self._role.capitalize()}",
                 font=(SANS, 9, "bold"), bg="#0EA5E9", fg="#E0F2FE").pack(side="right", padx=20)
        tk.Label(hdr, text="Lenguajes y Autómatas I  |",
                 font=(SANS, 9), bg="#0EA5E9", fg="#E0F2FE").pack(side="right", padx=4)

    def _build_toolbar(self):
        bar = tk.Frame(self, bg=PANEL, pady=8)
        bar.pack(fill="x")

        btn = dict(font=(SANS, 9, "bold"), relief="flat", cursor="hand2", padx=12, pady=5)

        tk.Button(bar, text="📂  Abrir archivo", bg=ACCENT, fg="#0F172A",
                  command=self._load_file, **btn).pack(side="left", padx=(12, 4))

        self._save_btn = tk.Button(bar, text="💾  Guardar", bg="#475569", fg=TEXT,
                                   command=self._save_file, state="disabled", **btn)
        self._save_btn.pack(side="left", padx=4)

        self._run_btn = tk.Button(bar, text="▶  Analizar & Traducir", bg="#22C55E", fg="#0F172A",
                                  command=self._run, state="disabled", **btn)
        self._run_btn.pack(side="left", padx=4)

        tk.Button(bar, text="🗑  Limpiar todo", bg="#334155", fg=TEXT,
                  command=self._clear, **btn).pack(side="left", padx=4)

        # Badge de estado
        self._status_badge = tk.Label(bar, text="— Sin analizar —",
                                      font=(SANS, 9, "bold"), bg=PANEL, fg=SUBTEXT)
        self._status_badge.pack(side="left", padx=20)

        # Nombre de archivo
        self._file_label = tk.Label(bar, text="Sin archivo",
                                    font=(MONO, 9), bg=PANEL, fg=SUBTEXT)
        self._file_label.pack(side="right", padx=16)

    def _build_body(self):
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=12, pady=10)
        body.columnconfigure(0, weight=5)
        body.columnconfigure(1, weight=4)
        body.rowconfigure(0, weight=1)

        # ════════════════════════════════════════
        #  PANEL IZQUIERDO — Notebook con pestañas
        # ════════════════════════════════════════
        left = tk.Frame(body, bg=BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)

        self._left_nb = ttk.Notebook(left)
        self._left_nb.grid(row=0, column=0, sticky="nsew")

        # ── Tab 1: Editor ────────────────────────
        tab_editor = tk.Frame(self._left_nb, bg=BG)
        self._left_nb.add(tab_editor, text="  ✏️  Editor  ")
        tab_editor.rowconfigure(0, weight=1)
        tab_editor.columnconfigure(0, weight=1)

        editor_frame = tk.Frame(tab_editor, bg=PANEL)
        editor_frame.grid(row=0, column=0, sticky="nsew", pady=(4, 0))
        editor_frame.rowconfigure(0, weight=1)
        editor_frame.columnconfigure(0, weight=1)

        # números de línea + editor
        line_frame = tk.Frame(editor_frame, bg=PANEL)
        line_frame.grid(row=0, column=0, sticky="nsew")
        line_frame.rowconfigure(0, weight=1)
        line_frame.columnconfigure(1, weight=1)

        self._line_numbers = tk.Text(
            line_frame, width=4, font=(MONO, 10), bg="#162032", fg="#475569",
            relief="flat", state="disabled", cursor="arrow",
            selectbackground="#162032", padx=4
        )
        self._line_numbers.grid(row=0, column=0, sticky="ns")

        self._editor = tk.Text(
            line_frame, font=(MONO, 10), bg="#0F172A", fg=TEXT,
            insertbackground=ACCENT, relief="flat", wrap="none",
            selectbackground=BORDER, undo=True, padx=8
        )
        sb_e = ttk.Scrollbar(line_frame, command=self._sync_scroll)
        self._editor.configure(yscrollcommand=self._on_editor_scroll)
        self._editor.grid(row=0, column=1, sticky="nsew")
        sb_e.grid(row=0, column=2, sticky="ns")

        self._editor.bind("<KeyRelease>", self._on_editor_change)
        self._editor.bind("<Button-1>",   self._on_editor_change)
        self._editor.bind("<<Modified>>", self._on_editor_change)

        # hint cuando está vacío
        self._hint = tk.Label(
            editor_frame,
            text="Abre un archivo .txt  o  escribe directamente aquí\n\nEjemplo:\nINICIO\nAVANZAR 5\nGIRAR DERECHA\nDETENER\nFIN",
            font=(MONO, 10), bg="#0F172A", fg="#334155",
            justify="left"
        )
        self._hint.place(x=50, y=40)
        self._editor.bind("<FocusIn>",  lambda e: self._hint.place_forget())
        self._editor.bind("<FocusOut>", self._maybe_show_hint)

        # ── Tab 2: Tabla de Tokens ───────────────
        tab_tokens = tk.Frame(self._left_nb, bg=BG)
        self._left_nb.add(tab_tokens, text="  🔤  Tokens  ")
        tab_tokens.rowconfigure(0, weight=3)   # análisis ocupa más espacio
        tab_tokens.rowconfigure(1, weight=0)   # separador fijo
        tab_tokens.rowconfigure(2, weight=0)   # label referencia fijo
        tab_tokens.rowconfigure(3, weight=1)   # referencia menos espacio
        tab_tokens.columnconfigure(0, weight=1)

        # ── Sección superior: tokens del análisis actual ──
        tk.Label(tab_tokens, text="Tokens encontrados en el análisis",
                 font=(SANS, 9, "bold"), bg=BG, fg=ACCENT).grid(
            row=0, column=0, sticky="nw", padx=8, pady=(6, 0))

        tok_frame = tk.Frame(tab_tokens, bg=PANEL)
        tok_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=(22, 0))
        tok_frame.rowconfigure(0, weight=1)
        tok_frame.columnconfigure(0, weight=1)

        cols = ("linea", "pos", "tipo", "lexema", "descripcion")
        self._tok_tree = ttk.Treeview(tok_frame, columns=cols, show="headings",
                                      selectmode="browse")
        self._tok_tree.heading("linea",       text="Línea")
        self._tok_tree.heading("pos",         text="#")
        self._tok_tree.heading("tipo",        text="Tipo de Token")
        self._tok_tree.heading("lexema",      text="Lexema")
        self._tok_tree.heading("descripcion", text="Descripción")
        self._tok_tree.column("linea",        width=50,  anchor="center")
        self._tok_tree.column("pos",          width=35,  anchor="center")
        self._tok_tree.column("tipo",         width=130, anchor="w")
        self._tok_tree.column("lexema",       width=90,  anchor="center")
        self._tok_tree.column("descripcion",  width=150, anchor="w")

        sb_t = ttk.Scrollbar(tok_frame, command=self._tok_tree.yview)
        self._tok_tree.configure(yscrollcommand=sb_t.set)
        self._tok_tree.grid(row=0, column=0, sticky="nsew")
        sb_t.grid(row=0, column=1, sticky="ns")

        for tok_type, color in TOKEN_COLORS.items():
            self._tok_tree.tag_configure(tok_type, foreground=color)

        # ── Separador ────────────────────────────
        tk.Frame(tab_tokens, bg=BORDER, height=1).grid(
            row=1, column=0, sticky="ew", pady=2)

        # ── Label referencia ─────────────────────
        tk.Label(tab_tokens, text="Tokens válidos del lenguaje  (referencia)",
                 font=(SANS, 9, "bold"), bg=BG, fg=ACCENT).grid(
            row=2, column=0, sticky="w", padx=8, pady=(2, 2))

        # ── Sección inferior: referencia siempre visible ──
        ref_frame = tk.Frame(tab_tokens, bg=PANEL)
        ref_frame.grid(row=3, column=0, sticky="nsew")
        ref_frame.rowconfigure(0, weight=1)
        ref_frame.columnconfigure(0, weight=1)

        ref_cols = ("token", "lexema_ej", "descripcion")
        self._ref_tree = ttk.Treeview(ref_frame, columns=ref_cols, show="headings",
                                      selectmode="none", height=8)
        self._ref_tree.heading("token",      text="Token")
        self._ref_tree.heading("lexema_ej",  text="Ejemplo")
        self._ref_tree.heading("descripcion",text="Descripción")
        self._ref_tree.column("token",       width=130, anchor="w")
        self._ref_tree.column("lexema_ej",   width=90,  anchor="center")
        self._ref_tree.column("descripcion", width=200, anchor="w")

        REFERENCE_TOKENS = [
            ("TK_INICIO",    "INICIO",     "Palabra reservada — inicia el programa"),
            ("TK_FIN",       "FIN",        "Palabra reservada — termina el programa"),
            ("TK_AVANZAR",   "AVANZAR",    "Instrucción — mueve el robot hacia adelante"),
            ("TK_GIRAR",     "GIRAR",      "Instrucción — rota el robot"),
            ("TK_DERECHA",   "DERECHA",    "Dirección — combinar con GIRAR"),
            ("TK_IZQUIERDA", "IZQUIERDA",  "Dirección — combinar con GIRAR"),
            ("TK_DETENER",   "DETENER",    "Instrucción — detiene el robot"),
            ("TK_NUMERO",    "1, 5, 10…",  "Literal numérico — pasos para AVANZAR"),
        ]
        for tok, ej, desc in REFERENCE_TOKENS:
            color = TOKEN_COLORS.get(tok, TEXT)
            self._ref_tree.tag_configure(f"ref_{tok}", foreground=color)
            self._ref_tree.insert("", "end", values=(tok, ej, desc), tags=(f"ref_{tok}",))

        sb_r = ttk.Scrollbar(ref_frame, command=self._ref_tree.yview)
        self._ref_tree.configure(yscrollcommand=sb_r.set)
        self._ref_tree.grid(row=0, column=0, sticky="nsew")
        sb_r.grid(row=0, column=1, sticky="ns")

        # ── Tab 3: Log de Análisis ───────────────
        tab_log = tk.Frame(self._left_nb, bg=BG)
        self._left_nb.add(tab_log, text="  📋  Log  ")
        tab_log.rowconfigure(0, weight=1)
        tab_log.columnconfigure(0, weight=1)

        log_frame = tk.Frame(tab_log, bg=PANEL)
        log_frame.grid(row=0, column=0, sticky="nsew")
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)

        self._log_text = tk.Text(
            log_frame, font=(MONO, 9), bg=PANEL2, fg=TEXT,
            relief="flat", state="disabled", wrap="none",
            selectbackground=BORDER, padx=10, pady=10, spacing1=3
        )
        sb_l = ttk.Scrollbar(log_frame, command=self._log_text.yview)
        self._log_text.configure(yscrollcommand=sb_l.set)
        self._log_text.grid(row=0, column=0, sticky="nsew")
        sb_l.grid(row=0, column=1, sticky="ns")

        self._log_text.tag_configure("header",  foreground=ACCENT,   font=(MONO, 9, "bold"))
        self._log_text.tag_configure("ok",       foreground=SUCCESS)
        self._log_text.tag_configure("error",    foreground=ERROR)
        self._log_text.tag_configure("info",     foreground=SUBTEXT)
        self._log_text.tag_configure("line_hdr", foreground=WARNING,  font=(MONO, 9, "bold"))
        self._log_text.tag_configure("sum_ok",   foreground=SUCCESS,  font=(MONO, 9, "bold"))
        self._log_text.tag_configure("sum_err",  foreground=ERROR,    font=(MONO, 9, "bold"))

        # ════════════════════════════════════════
        #  PANEL DERECHO — Simulación + Árbol
        # ════════════════════════════════════════
        right = tk.Frame(body, bg=BG)
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)

        self._right_nb = ttk.Notebook(right)
        self._right_nb.grid(row=0, column=0, sticky="nsew")

        # ── Tab A: Simulación ────────────────────
        tab_sim = tk.Frame(self._right_nb, bg=BG)
        self._right_nb.add(tab_sim, text="  📡  Simulación  ")
        tab_sim.rowconfigure(0, weight=1)
        tab_sim.columnconfigure(0, weight=1)

        sim_frame = tk.Frame(tab_sim, bg=PANEL)
        sim_frame.grid(row=0, column=0, sticky="nsew", pady=(4, 0))
        sim_frame.rowconfigure(0, weight=1)
        sim_frame.columnconfigure(0, weight=1)

        self._trad_text = tk.Text(
            sim_frame, font=(SANS, 11), bg=PANEL, fg=TEXT,
            insertbackground=ACCENT, relief="flat", wrap="word",
            state="disabled", selectbackground=BORDER,
            padx=14, pady=12, spacing1=6, spacing3=6
        )
        sb_s = ttk.Scrollbar(sim_frame, command=self._trad_text.yview)
        self._trad_text.configure(yscrollcommand=sb_s.set)
        self._trad_text.grid(row=0, column=0, sticky="nsew")
        sb_s.grid(row=0, column=1, sticky="ns")

        self._trad_text.tag_configure("inicio",    foreground=ACCENT,   font=(SANS, 11, "bold"))
        self._trad_text.tag_configure("fin",        foreground=ACCENT,   font=(SANS, 11, "bold"))
        self._trad_text.tag_configure("avanzar",    foreground=SUCCESS)
        self._trad_text.tag_configure("girar",      foreground=WARNING)
        self._trad_text.tag_configure("detener",    foreground=ERROR)
        self._trad_text.tag_configure("error_msg",  foreground=ERROR,    font=(SANS, 11, "italic"))

        # ── Tab B: Árbol Sintáctico ──────────────
        tab_tree = tk.Frame(self._right_nb, bg=BG)
        self._right_nb.add(tab_tree, text="  🌳  Árbol Sintáctico  ")
        tab_tree.rowconfigure(0, weight=1)
        tab_tree.columnconfigure(0, weight=1)

        tree_outer = tk.Frame(tab_tree, bg=PANEL)
        tree_outer.grid(row=0, column=0, sticky="nsew", pady=(4, 0))
        tree_outer.rowconfigure(0, weight=1)
        tree_outer.columnconfigure(0, weight=1)

        self._tree_canvas = TreeCanvas(tree_outer)
        sb_tx = ttk.Scrollbar(tree_outer, orient="horizontal",
                               command=self._tree_canvas.xview)
        sb_ty = ttk.Scrollbar(tree_outer, command=self._tree_canvas.yview)
        self._tree_canvas.configure(xscrollcommand=sb_tx.set,
                                    yscrollcommand=sb_ty.set)
        self._tree_canvas.grid(row=0, column=0, sticky="nsew")
        sb_ty.grid(row=0, column=1, sticky="ns")
        sb_tx.grid(row=1, column=0, sticky="ew")

        self._tree_canvas.create_text(
            200, 80, text="Presiona  ▶ Analizar & Traducir\npara generar el árbol.",
            fill=SUBTEXT, font=(SANS, 10), justify="center"
        )

    def _build_footer(self):
        ft = tk.Frame(self, bg="#0A1628", height=28)
        ft.pack(fill="x", side="bottom")
        ft.pack_propagate(False)
        tk.Label(ft, text="BRUGUERA · CASTILLO · TORRES  —  Lenguajes y Autómatas I",
                 font=(SANS, 8), bg="#0A1628", fg="#475569").pack(side="right", padx=16)

    # ── Editor: helpers ─────────────────────────
    def _on_editor_scroll(self, *args):
        self._line_numbers.yview_moveto(args[0])
        # scrollbar no existe como atributo, se pasa directo al text
        return

    def _sync_scroll(self, *args):
        self._editor.yview(*args)
        self._line_numbers.yview(*args)

    def _on_editor_change(self, event=None):
        self._update_line_numbers()
        # habilitar botones si hay contenido
        content = self._editor.get("1.0", "end").strip()
        state = "normal" if content else "disabled"
        self._run_btn.config(state=state)
        self._save_btn.config(state=state if self._filepath else "disabled")
        # quitar hint
        if content:
            self._hint.place_forget()

    def _update_line_numbers(self):
        self._line_numbers.config(state="normal")
        self._line_numbers.delete("1.0", "end")
        lines = self._editor.get("1.0", "end").split("\n")
        nums = "\n".join(str(i) for i in range(1, len(lines)))
        self._line_numbers.insert("1.0", nums)
        self._line_numbers.config(state="disabled")

    def _maybe_show_hint(self, event=None):
        if not self._editor.get("1.0", "end").strip():
            self._hint.place(x=50, y=40)

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
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self._editor.delete("1.0", "end")
        self._editor.insert("1.0", content)
        self._hint.place_forget()
        self._update_line_numbers()
        self._run_btn.config(state="normal")
        self._save_btn.config(state="normal")
        self._clear_results()

    def _save_file(self):
        content = self._editor.get("1.0", "end-1c")
        if self._filepath:
            with open(self._filepath, "w", encoding="utf-8") as f:
                f.write(content)
            self._file_label.config(text=f"💾  {os.path.basename(self._filepath)}", fg=SUCCESS)
            self.after(2000, lambda: self._file_label.config(
                text=os.path.basename(self._filepath), fg=TEXT))
        else:
            path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Archivos de texto", "*.txt")]
            )
            if path:
                self._filepath = path
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                self._file_label.config(text=os.path.basename(path), fg=TEXT)

    def _run(self):
        code = self._editor.get("1.0", "end-1c").strip()
        if not code:
            return

        self._clear_results()

        # ── Análisis Léxico ──────────────────────
        lines_tokens, lex_errors, lex_log = tokenize(code)
        self._populate_log(lex_log)

        # Mostrar tokens siempre, aunque haya errores sintácticos
        self._populate_tokens(lines_tokens)

        if lex_errors:
            self._set_status(False, "Error léxico")
            self._set_translation(
                [("error_msg", "⚠  Errores léxicos encontrados:\n")] +
                [("error_msg", f"   {e}\n") for e in lex_errors]
            )
            # Aun con error léxico, intentar construir árbol parcial con los tokens válidos
            if lines_tokens:
                _, _, tree_root, _ = parse(lines_tokens)
                self._tree_root = tree_root
                self.after(100, self._draw_tree)
            self._left_nb.select(2)   # ir a Log
            return

        # ── Análisis Sintáctico ──────────────────
        valido, msg, tree_root, syn_log = parse(lines_tokens)
        self._populate_log(syn_log)
        self._set_status(valido, msg)

        # Mostrar árbol siempre — parcial si hay error, completo si es válido
        self._tree_root = tree_root
        self.after(100, self._draw_tree)

        if not valido:
            self._set_translation([("error_msg", f"⚠  {msg}")])
            self._left_nb.select(2)   # ir a Log
            return

        # ── Traducción ───────────────────────────
        lines_out = translate(lines_tokens)
        tagged = []
        for line in lines_out:
            if "inicia"   in line: tagged.append(("inicio",  line + "\n"))
            elif "finaliza" in line: tagged.append(("fin",   line + "\n"))
            elif "avanza"   in line: tagged.append(("avanzar", line + "\n"))
            elif "gira"     in line: tagged.append(("girar",  line + "\n"))
            elif "detiene"  in line: tagged.append(("detener", line + "\n"))
            else:                    tagged.append(("",        line + "\n"))
        self._set_translation(tagged)

        # Cambiar a la pestaña de simulación
        self._right_nb.select(0)
        self._left_nb.select(1)   # mostrar tokens

    def _clear(self):
        self._filepath = None
        self._file_label.config(text="Sin archivo", fg=SUBTEXT)
        self._editor.delete("1.0", "end")
        self._update_line_numbers()
        self._run_btn.config(state="disabled")
        self._save_btn.config(state="disabled")
        self._maybe_show_hint()
        self._clear_results()

    # ── Poblar paneles ───────────────────────────
    def _populate_tokens(self, lines_tokens):
        for item in self._tok_tree.get_children():
            self._tok_tree.delete(item)

        TOKEN_DESC = {
            'TK_INICIO':    'Palabra reservada',
            'TK_FIN':       'Palabra reservada',
            'TK_AVANZAR':   'Instrucción de movimiento',
            'TK_GIRAR':     'Instrucción de rotación',
            'TK_DERECHA':   'Dirección',
            'TK_IZQUIERDA': 'Dirección',
            'TK_DETENER':   'Instrucción de parada',
            'TK_NUMERO':    'Literal numérico',
        }

        for lineno, toks in lines_tokens:
            for pos, (tipo, lexema) in enumerate(toks, 1):
                desc = TOKEN_DESC.get(tipo, "")
                tag  = tipo if tipo in TOKEN_COLORS else ""
                self._tok_tree.insert("", "end",
                                      values=(lineno, pos, tipo, lexema, desc),
                                      tags=(tag,))

    def _populate_log(self, log_entries):
        self._log_text.config(state="normal")
        for entry in log_entries:
            t    = entry.get('type', 'info')
            msg  = entry.get('msg', '') + "\n"
            if t == 'header':
                self._log_text.insert("end", msg, "header")
            elif t in ('token_ok', 'ok'):
                self._log_text.insert("end", msg, "ok")
            elif t in ('token_error', 'error'):
                self._log_text.insert("end", msg, "error")
            elif t == 'line_start':
                self._log_text.insert("end", msg, "line_hdr")
            elif t == 'summary_ok':
                self._log_text.insert("end", msg, "sum_ok")
            elif t == 'summary_error':
                self._log_text.insert("end", msg, "sum_err")
            else:
                self._log_text.insert("end", msg, "info")
        self._log_text.insert("end", "\n")
        self._log_text.config(state="disabled")
        self._log_text.see("end")

    def _draw_tree(self):
        if self._tree_root:
            # Cambiar a la pestaña del árbol para forzar que el canvas tenga tamaño real
            self._right_nb.select(1)
            self.update_idletasks()
            self._tree_canvas.draw_tree(self._tree_root)

    # ── Helpers de UI ───────────────────────────
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
        self._set_status_neutral()
        self._set_translation([])
        for item in self._tok_tree.get_children():
            self._tok_tree.delete(item)
        self._log_text.config(state="normal")
        self._log_text.delete("1.0", "end")
        self._log_text.config(state="disabled")
        self._tree_canvas.delete("all")
        self._tree_canvas.create_text(
            200, 80, text="Presiona  ▶ Analizar & Traducir\npara generar el árbol.",
            fill=SUBTEXT, font=(SANS, 10), justify="center"
        )

    def _set_status_neutral(self):
        self._status_badge.config(text="— Sin analizar —", fg=SUBTEXT)


# ─────────────────────────────────────────────
#  PUNTO DE ENTRADA
# ─────────────────────────────────────────────
def launch_app(role):
    app = TraductorApp(role=role)
    app.mainloop()

if __name__ == "__main__":
    login = LoginWindow(on_success=launch_app)
    login.mainloop()