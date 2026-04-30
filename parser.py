# ─────────────────────────────────────────────
#  ANALIZADOR SINTÁCTICO  +  ÁRBOL SINTÁCTICO
# ─────────────────────────────────────────────

class Node:
    """Nodo del árbol sintáctico."""
    def __init__(self, label, token_type=None, lexema=None):
        self.label      = label        # texto que se muestra en el nodo
        self.token_type = token_type   # tipo de token (hoja) o None (interno)
        self.lexema     = lexema       # valor léxico (hoja) o None (interno)
        self.children   = []

    def add(self, child):
        self.children.append(child)
        return child


def parse(lines_tokens):
    """
    Gramática:
        programa     → INICIO instrucciones FIN
        instrucciones→ instruccion+
        instruccion  → AVANZAR TK_NUMERO
                     | GIRAR DERECHA
                     | GIRAR IZQUIERDA
                     | DETENER

    Retorna (es_valido, mensaje, arbol_raiz, log_entries)
    """
    tokens = []
    for _, toks in lines_tokens:
        tokens.extend(toks)

    log_entries = []
    log_entries.append({
        'type': 'header',
        'msg': '── Iniciando Análisis Sintáctico ──────────────'
    })

    root = Node("programa")
    tree_ok = True

    def log_ok(msg):
        log_entries.append({'type': 'ok',    'msg': f'  ✅  {msg}'})

    def log_err(msg):
        log_entries.append({'type': 'error', 'msg': f'  ❌  {msg}'})

    def log_info(msg):
        log_entries.append({'type': 'info',  'msg': f'  ℹ️   {msg}'})

    def expect(i, tipo):
        if i < len(tokens) and tokens[i][0] == tipo:
            return i + 1
        tok = tokens[i] if i < len(tokens) else ('EOF', 'EOF')
        raise SyntaxError(f"Se esperaba '{tipo}' pero se encontró '{tok[1]}'")

    try:
        # ── INICIO ──
        log_info(f"Verificando token INICIO en posición 0...")
        i = expect(0, 'TK_INICIO')
        node_inicio = root.add(Node("INICIO", "TK_INICIO", "INICIO"))
        log_ok("Token INICIO encontrado ✓")

        if i >= len(tokens) or tokens[i][0] == 'TK_FIN':
            raise SyntaxError("El programa no contiene instrucciones.")

        # ── INSTRUCCIONES ──
        node_instrs = root.add(Node("instrucciones"))
        instr_count = 0

        while i < len(tokens) and tokens[i][0] != 'TK_FIN':
            tipo = tokens[i][0]
            lex  = tokens[i][1]
            node_instr = Node("instruccion")

            if tipo == 'TK_AVANZAR':
                log_info(f"Instrucción AVANZAR detectada — esperando número...")
                node_instr.add(Node("AVANZAR", "TK_AVANZAR", "AVANZAR"))
                i += 1
                if i < len(tokens) and tokens[i][0] == 'TK_NUMERO':
                    num = tokens[i][1]
                    node_instr.add(Node(num, "TK_NUMERO", num))
                    log_ok(f"AVANZAR {num} → instrucción válida ✓")
                    i += 1
                else:
                    tok = tokens[i] if i < len(tokens) else ('EOF', 'EOF')
                    raise SyntaxError(f"AVANZAR debe ir seguido de un número, se encontró '{tok[1]}'")

            elif tipo == 'TK_GIRAR':
                log_info(f"Instrucción GIRAR detectada — esperando dirección...")
                node_instr.add(Node("GIRAR", "TK_GIRAR", "GIRAR"))
                i += 1
                if i < len(tokens) and tokens[i][0] in ('TK_DERECHA', 'TK_IZQUIERDA'):
                    dir_lex  = tokens[i][1]
                    dir_type = tokens[i][0]
                    node_instr.add(Node(dir_lex, dir_type, dir_lex))
                    log_ok(f"GIRAR {dir_lex} → instrucción válida ✓")
                    i += 1
                else:
                    tok = tokens[i] if i < len(tokens) else ('EOF', 'EOF')
                    raise SyntaxError(
                        f"GIRAR debe ir seguido de DERECHA o IZQUIERDA, se encontró '{tok[1]}'"
                    )

            elif tipo == 'TK_DETENER':
                node_instr.add(Node("DETENER", "TK_DETENER", "DETENER"))
                log_ok("DETENER → instrucción válida ✓")
                i += 1

            else:
                raise SyntaxError(f"Instrucción no reconocida: '{lex}'")

            node_instrs.add(node_instr)
            instr_count += 1

        # ── FIN ──
        log_info(f"Verificando token FIN...")
        i = expect(i, 'TK_FIN')
        root.add(Node("FIN", "TK_FIN", "FIN"))
        log_ok("Token FIN encontrado ✓")

        if i != len(tokens):
            raise SyntaxError("Se encontraron tokens adicionales después de FIN.")

        log_entries.append({
            'type': 'summary_ok',
            'msg': f'\n✅  Análisis sintáctico correcto — {instr_count} instrucción(es) válida(s).'
        })
        return True, "Programa válido ✓", root, log_entries

    except SyntaxError as e:
        log_err(str(e))
        log_entries.append({
            'type': 'summary_error',
            'msg': f'\n⚠  Análisis sintáctico fallido.'
        })
        # Agregar nodo de error al árbol para mostrar dónde tronó
        # Mensaje corto y descriptivo para que quepa en el nodo
        msg_corto = (str(e)
                     .replace("Se esperaba", "Esperado:")
                     .replace("se encontró", "→")
                     .replace("debe ir seguido de", "→")
                     .replace("El programa no contiene instrucciones.", "Sin instrucciones")
                     .replace("Se encontraron tokens adicionales después de FIN.", "Tokens extra tras FIN")
                     .replace("Instrucción no reconocida:", "Instr. inválida:"))
        error_node = Node(f"❌ {msg_corto[:20]}", "ERROR", str(e))
        root.add(error_node)
        return False, f"Error sintáctico: {e}", root, log_entries