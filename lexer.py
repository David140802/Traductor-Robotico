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


def tokenize(code):
    """
    Retorna:
      lines_tokens : lista de (lineno, [(tipo, lexema), ...])
      errors       : lista de strings de error
      log_entries  : lista de dicts con info detallada para el log visual
    """
    lines_tokens = []
    errors = []
    log_entries = []

    log_entries.append({
        'type': 'header',
        'msg': '── Iniciando Análisis Léxico ──────────────────'
    })

    for lineno, line in enumerate(code.splitlines(), 1):
        raw_line = line
        line = line.strip()
        if not line:
            continue

        log_entries.append({
            'type': 'line_start',
            'lineno': lineno,
            'content': raw_line.strip(),
            'msg': f'Línea {lineno}: "{raw_line.strip()}"'
        })

        pos = 0
        toks = []

        while pos < len(line):
            matched = False
            for name, regex in COMPILED:
                m = regex.match(line, pos)
                if m:
                    lexema = m.group()
                    if name == 'ERROR':
                        errors.append(f"Línea {lineno}: token no reconocido '{lexema}'")
                        log_entries.append({
                            'type': 'token_error',
                            'lineno': lineno,
                            'lexema': lexema,
                            'msg': f'  ❌  Token no reconocido: "{lexema}"'
                        })
                    elif name == 'SKIP':
                        pass  # espacios, no se loguean
                    else:
                        toks.append((name, lexema))
                        log_entries.append({
                            'type': 'token_ok',
                            'lineno': lineno,
                            'token_type': name,
                            'lexema': lexema,
                            'desc': TOKEN_DESC.get(name, ''),
                            'msg': f'  ✅  {name:<16} →  "{lexema}"  ({TOKEN_DESC.get(name, "")})'
                        })
                    pos = m.end()
                    matched = True
                    break
            if not matched:
                pos += 1

        if toks:
            lines_tokens.append((lineno, toks))

    if errors:
        log_entries.append({
            'type': 'summary_error',
            'msg': f'\n⚠  Análisis léxico finalizado con {len(errors)} error(s).'
        })
    else:
        total = sum(len(t) for _, t in lines_tokens)
        log_entries.append({
            'type': 'summary_ok',
            'msg': f'\n✅  Análisis léxico correcto — {total} token(s) reconocidos.'
        })

    return lines_tokens, errors, log_entries