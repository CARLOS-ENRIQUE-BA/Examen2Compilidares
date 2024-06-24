from flask import Flask, request, render_template_string
import ply.lex as lex
import ply.yacc as yacc

app = Flask(__name__)

# Palabras reservadas y tokens
reservadas = {
    'int': 'INT',
    'DO': 'DO',
    'ENDDO': 'ENDDO',
    'WHILE': 'WHILE',
    'ENDWHILE': 'ENDWHILE'
}

tokens = (
    'ID', 'ASSIGN', 'NUMBER', 'SEMICOLON', 'PLUS', 'TIMES', 'LPAREN', 'RPAREN', 'EQUALS'
) + tuple(reservadas.values())

# Definición de tokens
t_ASSIGN = r'='
t_SEMICOLON = r';'
t_PLUS = r'\+'
t_TIMES = r'\*'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_EQUALS = r'=='

# Definición de identificadores y números
def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reservadas.get(t.value, 'ID')
    return t

def t_DOTNUMBER(t):
    r'\.\d+'
    print(f"Error: Número de punto flotante '{t.value}'")
    t.lexer.skip(1)

def t_NUMBERDOT(t):
    r'\d+\.'
    print(f"Error: Número de punto flotante '{t.value}'")
    t.lexer.skip(1)
    
def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

# Ignorar espacios y tabulaciones
t_ignore = ' \t'

# Manejo de errores léxicos
def t_error(t):
    print(f"Carácter ilegal '{t.value[0]}'")
    t.lexer.skip(1)

# Construcción del lexer
analizadorLexico = lex.lex()

# --- Análisis Sintáctico ---
# Almacén de variables declaradas
variables = set()
errores = []

# Definición de la gramática
def p_programa(p):
    '''programa : declaraciones DO bloque ENDDO WHILE LPAREN condicion RPAREN ENDWHILE'''
    p[0] = ('programa', p[1], p[3], p[7])

def p_declaraciones(p):
    '''declaraciones : declaraciones declaracion
                     | declaracion'''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

def p_declaracion(p):
    '''declaracion : INT ID ASSIGN NUMBER SEMICOLON'''
    if p[2] in variables:
        errores.append(f"Error: Variable '{p[2]}' redeclarada.")
    else:
        variables.add(p[2])
    p[0] = ('declaracion', p[2], p[4])

def p_bloque(p):
    '''bloque : bloque sentencia
              | sentencia'''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

def p_sentencia(p):
    '''sentencia : ID ASSIGN expresion SEMICOLON'''
    if p[1] not in variables:
        errores.append(f"Error: Variable '{p[1]}' no declarada.")
    p[0] = ('sentencia', p[1], p[3])

def p_expresion(p):
    '''expresion : termino
                 | termino PLUS termino'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ('+', p[1], p[3])

def p_termino(p):
    '''termino : factor
               | factor TIMES factor'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ('*', p[1], p[3])

def p_factor(p):
    '''factor : NUMBER
              | ID'''
    if isinstance(p[1], str) and p[1] not in variables:
        errores.append(f"Error: Variable '{p[1]}' no declarada.")
    p[0] = p[1]

def p_condicion(p):
    '''condicion : INT ID EQUALS NUMBER'''
    if p[2] in variables:
        errores.append(f"Error: Variable '{p[2]}' redeclarada.")
    else:
        variables.add(p[2])
    p[0] = ('condicion', p[2], p[4])

# Manejo de errores sintácticos
def p_error(p):
    if p:
        print(f"Error de sintaxis en '{p.value}'")
        errores.append(f"Error de sintaxis en '{p.value}'")
    else:
        print("Error de sintaxis en EOF")
        errores.append("Error de sintaxis en EOF")

# Construcción del parser
analizadorSintactico = yacc.yacc()

# --- Aplicación Flask ---
@app.route('/', methods=['GET', 'POST'])
def index():
    global errores
    global variables
    errores = []
    variables = set()
    resultado = ""
    conteoTokens = {
        'ID': 0, 'PR': 0, 'NUMEROS': 0, 'SIMBOLOS': 0, 'ERRORES': 0, 'TOTAL': 0
    }
    if request.method == 'POST':
        codigo = request.form['codigo']
        analizadorLexico.input(codigo)
        listaTokens = []
        while True:
            tok = analizadorLexico.token()
            if not tok:
                break
            listaTokens.append(str(tok))
            if tok.type in conteoTokens:
                conteoTokens[tok.type] += 1
            elif tok.type in reservadas.values():
                conteoTokens['PR'] += 1
            else:
                conteoTokens['SIMBOLOS'] += 1

        try:
            analizadorSintactico.parse(codigo)
            if errores:
                resultado = "\n".join(errores)
                conteoTokens['ERRORES'] = len(errores)
            else:
                resultado = "Compilación exitosa:\n" + "\n".join(listaTokens)
        except SyntaxError as e:
            resultado = str(e)
            conteoTokens['ERRORES'] += 1
        except Exception as e:
            resultado = "Ocurrió un error inesperado: " + str(e)
            conteoTokens['ERRORES'] += 1

        conteoTokens['TOTAL'] = sum(conteoTokens.values())

    return render_template_string('''
        <!doctype html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Analizador Léxico, Sintáctico y Semántico</title>
        </head>
        <body>
            <div class="container">
                <div class="left-panel">
                    <form method="post">
                        <textarea name="codigo" rows="10" placeholder="Introduce tu código aquí...">{{ request.form['codigo'] }}</textarea><br>
                        <input type="submit" value="Compilar">
                    </form>
                </div>
                <div class="right-panel">
                    {% if resultado %}
                        <h2>Resultado:</h2>
                        <pre>{{ resultado }}</pre>
                        <table>
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>PR</th>
                                    <th>Números</th>
                                    <th>Símbolos</th>
                                    <th>Errores</th>
                                    <th>Total</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>{{ conteoTokens['ID'] }}</td>
                                    <td>{{ conteoTokens['PR'] }}</td>
                                    <td>{{ conteoTokens['NUMEROS'] }}</td>
                                    <td>{{ conteoTokens['SIMBOLOS'] }}</td>
                                    <td>{{ conteoTokens['ERRORES'] }}</td>
                                    <td>{{ conteoTokens['TOTAL'] }}</td>
                                </tr>
                            </tbody>
                        </table>
                    {% endif %}
                </div>
            </div>
        </body>
        </html>
    ''', resultado=resultado, conteoTokens=conteoTokens)

if __name__ == '__main__':
    app.run(debug=True)
