import re

# ─────────────────────────────────────────────
#  ANALIZADOR LÉXICO
# ─────────────────────────────────────────────
TOKEN_PATTERNS = [
    ('TK_INICIO',    r'\bINICIO\b'),
    ('TK_FIN',       r'\bFIN\b'),
    ('TK_AVANZAR',   r'\bAVANZAR\b'),
    ('TK_GIRAR',     r'\bGIRAR\b'),
    ('TK_DERECHA',   r'\bDERECHA\b'),
    ('TK_IZQUIERDA', r'\bIZQUIERDA\b'),
    ('TK_DETENER',   r'\bDETENER\b'),
    ('TK_NUMERO',    r'\b[1-9][0-9]*\b'),
    ('SKIP',         r'[ \t]+'),
    ('ERROR',        r'\S+'),
]

COMPILED = [(name, re.compile(pat)) for name, pat in TOKEN_PATTERNS]


def tokenize(code):
    """Retorna lista de (lineno, [(tipo, lexema), ...]) y lista de errores."""
    lines_tokens = []
    errors = []
    for lineno, line in enumerate(code.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        pos = 0
        toks = []
        while pos < len(line):
            matched = False
            for name, regex in COMPILED:
                m = regex.match(line, pos)
                if m:
                    if name == 'ERROR':
                        errors.append(f"Línea {lineno}: token no reconocido '{m.group()}'")
                    elif name != 'SKIP':
                        toks.append((name, m.group()))
                    pos = m.end()
                    matched = True
                    break
            if not matched:
                pos += 1
        if toks:
            lines_tokens.append((lineno, toks))
    return lines_tokens, errors