# ─────────────────────────────────────────────
#  ANALIZADOR SINTÁCTICO
# ─────────────────────────────────────────────

def parse(lines_tokens):
    """
    Gramática:
      programa      → INICIO instrucciones FIN
      instrucciones → instruccion+
      instruccion   → AVANZAR TK_NUMERO
                    | GIRAR DERECHA
                    | GIRAR IZQUIERDA
                    | DETENER
    Retorna (es_valido, mensaje)
    """
    tokens = []
    for _, toks in lines_tokens:
        tokens.extend(toks)

    def expect(i, tipo):
        if i < len(tokens) and tokens[i][0] == tipo:
            return i + 1
        tok = tokens[i] if i < len(tokens) else ('EOF', 'EOF')
        raise SyntaxError(f"Se esperaba '{tipo}' pero se encontró '{tok[1]}'")

    try:
        i = expect(0, 'TK_INICIO')
        if i >= len(tokens) or tokens[i][0] == 'TK_FIN':
            raise SyntaxError("El programa no contiene instrucciones.")

        while i < len(tokens) and tokens[i][0] != 'TK_FIN':
            tipo = tokens[i][0]
            if tipo == 'TK_AVANZAR':
                i += 1
                i = expect(i, 'TK_NUMERO')
            elif tipo == 'TK_GIRAR':
                i += 1
                if i < len(tokens) and tokens[i][0] in ('TK_DERECHA', 'TK_IZQUIERDA'):
                    i += 1
                else:
                    tok = tokens[i] if i < len(tokens) else ('EOF', 'EOF')
                    raise SyntaxError(
                        f"GIRAR debe ir seguido de DERECHA o IZQUIERDA, se encontró '{tok[1]}'"
                    )
            elif tipo == 'TK_DETENER':
                i += 1
            else:
                raise SyntaxError(f"Instrucción no reconocida: '{tokens[i][1]}'")

        i = expect(i, 'TK_FIN')
        if i != len(tokens):
            raise SyntaxError("Se encontraron tokens adicionales después de FIN.")
        return True, "Programa válido ✓"
    except SyntaxError as e:
        return False, f"Error sintáctico: {e}"