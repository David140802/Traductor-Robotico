# ─────────────────────────────────────────────
#  TRADUCTOR
# ─────────────────────────────────────────────

def translate(lines_tokens):
    """Convierte tokens en mensajes de simulación."""
    output = []
    tokens = []
    for _, toks in lines_tokens:
        tokens.extend(toks)

    i = 0
    while i < len(tokens):
        tipo, lexema = tokens[i]
        if tipo == 'TK_INICIO':
            output.append("🤖  Robot inicia ejecución.")
        elif tipo == 'TK_FIN':
            output.append("🏁  Robot finaliza ejecución.")
        elif tipo == 'TK_AVANZAR':
            num = tokens[i + 1][1] if i + 1 < len(tokens) else '?'
            output.append(f"➡️   Robot avanza {num} pasos.")
            i += 1
        elif tipo == 'TK_GIRAR':
            dir_tok = tokens[i + 1][0] if i + 1 < len(tokens) else ''
            if dir_tok == 'TK_DERECHA':
                output.append("↩️   Robot gira hacia la derecha.")
            elif dir_tok == 'TK_IZQUIERDA':
                output.append("↪️   Robot gira hacia la izquierda.")
            i += 1
        elif tipo == 'TK_DETENER':
            output.append("⛔  Robot se detiene.")
        i += 1
    return output