from flask import Blueprint, request, jsonify
import re


# ============================================================
# BLUEPRINT
# ============================================================

traductor_bp = Blueprint(
    "traductor",
    __name__
)


# ============================================================
# FUNCIONES GENERALES
# ============================================================

def quitar_comentarios(linea):

    if "//" in linea:
        linea = linea.split("//", 1)[0]

    return linea.strip()


def dividir_argumentos(texto):

    partes = []

    actual = ""

    dentro_comillas = False

    profundidad = 0


    for caracter in texto:

        if caracter == '"':

            dentro_comillas = not dentro_comillas

            actual += caracter

            continue


        if not dentro_comillas:

            if caracter == "(":

                profundidad += 1

            elif caracter == ")":

                profundidad -= 1

            elif (
                caracter == ","
                and profundidad == 0
            ):

                partes.append(
                    actual.strip()
                )

                actual = ""

                continue


        actual += caracter


    if actual.strip():

        partes.append(
            actual.strip()
        )


    return partes


# ============================================================
# TIPOS
# ============================================================

def normalizar_tipo(tipo):

    tipo = tipo.lower().strip()


    if tipo in (
        "entero",
        "entera"
    ):

        return "entero"


    if tipo in (
        "real",
        "decimal"
    ):

        return "real"


    if tipo in (
        "cadena",
        "caracter",
        "carácter",
        "texto"
    ):

        return "cadena"


    if tipo in (
        "logico",
        "lógico",
        "booleano"
    ):

        return "logico"


    return "real"


# ============================================================
# PROTEGER VARIABLES
#
# Evita que una variable llamada "y" se convierta
# accidentalmente en "and" o "&&".
# ============================================================

def proteger_variables(texto, variables):

    reemplazos = {}

    contador = 0


    for variable in sorted(
        variables,
        key=len,
        reverse=True
    ):

        patron = (
            rf"\b{re.escape(variable)}\b"
        )


        marcador = (
            f"__VAR_{contador}__"
        )


        nuevo_texto, cantidad = re.subn(
            patron,
            marcador,
            texto
        )


        if cantidad > 0:

            texto = nuevo_texto

            reemplazos[
                marcador
            ] = variable

            contador += 1


    return texto, reemplazos


def restaurar_variables(
    texto,
    reemplazos
):

    for marcador, variable in reemplazos.items():

        texto = texto.replace(
            marcador,
            variable
        )


    return texto


# ============================================================
# EXPRESIONES PYTHON
# ============================================================

def expresion_python(
    texto,
    variables=None
):

    variables = variables or set()

    texto = texto.strip()


    texto, protegidas = proteger_variables(
        texto,
        variables
    )


    # Diferente
    texto = texto.replace(
        "<>",
        "!="
    )


    # Lógicos
    texto = re.sub(
        r"\bY\b",
        "and",
        texto,
        flags=re.IGNORECASE
    )


    texto = re.sub(
        r"\bO\b",
        "or",
        texto,
        flags=re.IGNORECASE
    )


    texto = re.sub(
        r"\bNO\b",
        "not",
        texto,
        flags=re.IGNORECASE
    )


    # Booleanos
    texto = re.sub(
        r"\bVerdadero\b",
        "True",
        texto,
        flags=re.IGNORECASE
    )


    texto = re.sub(
        r"\bFalso\b",
        "False",
        texto,
        flags=re.IGNORECASE
    )


    # MOD
    texto = re.sub(
        r"\bMOD\b",
        "%",
        texto,
        flags=re.IGNORECASE
    )


    # Potencia
    texto = texto.replace(
        "^",
        "**"
    )


    # Raíz cuadrada
    texto = re.sub(
        r"\bRC\s*\((.*?)\)",
        r"math.sqrt(\1)",
        texto,
        flags=re.IGNORECASE
    )


    # Igualdad
    texto = re.sub(
        r"(?<![<>=!])=(?!=)",
        "==",
        texto
    )


    texto = restaurar_variables(
        texto,
        protegidas
    )


    return texto


# ============================================================
# EXPRESIONES C++
# ============================================================

def expresion_cpp(
    texto,
    variables=None
):

    variables = variables or set()

    texto = texto.strip()


    texto, protegidas = proteger_variables(
        texto,
        variables
    )


    texto = texto.replace(
        "<>",
        "!="
    )


    texto = re.sub(
        r"\bY\b",
        "&&",
        texto,
        flags=re.IGNORECASE
    )


    texto = re.sub(
        r"\bO\b",
        "||",
        texto,
        flags=re.IGNORECASE
    )


    texto = re.sub(
        r"\bNO\b",
        "!",
        texto,
        flags=re.IGNORECASE
    )


    texto = re.sub(
        r"\bVerdadero\b",
        "true",
        texto,
        flags=re.IGNORECASE
    )


    texto = re.sub(
        r"\bFalso\b",
        "false",
        texto,
        flags=re.IGNORECASE
    )


    texto = re.sub(
        r"\bMOD\b",
        "%",
        texto,
        flags=re.IGNORECASE
    )


    texto = re.sub(
        r"\bRC\s*\((.*?)\)",
        r"sqrt(\1)",
        texto,
        flags=re.IGNORECASE
    )


    texto = re.sub(
        r"(?<![<>=!])=(?!=)",
        "==",
        texto
    )


    # --------------------------------------------------------
    # POTENCIAS SIMPLES
    # --------------------------------------------------------

    patron_potencia = re.compile(
        r"("
        r"__VAR_\d+__"
        r"|[A-Za-z_][A-Za-z0-9_]*"
        r"|\d+(?:\.\d+)?"
        r")"
        r"\s*\^\s*"
        r"("
        r"__VAR_\d+__"
        r"|[A-Za-z_][A-Za-z0-9_]*"
        r"|\d+(?:\.\d+)?"
        r")"
    )


    while patron_potencia.search(
        texto
    ):

        texto = patron_potencia.sub(
            r"pow(\1, \2)",
            texto
        )


    texto = restaurar_variables(
        texto,
        protegidas
    )


    return texto


# ============================================================
# CONVERTIR VALOR A PYTHON
# ============================================================

def valor_python(
    valor,
    tipo
):

    valor = str(
        valor
    ).strip()


    if tipo == "cadena":

        return repr(
            valor
        )


    if tipo == "logico":

        return (
            "True"
            if valor.lower() in (
                "verdadero",
                "true",
                "1",
                "si",
                "sí"
            )
            else "False"
        )


    return valor


# ============================================================
# CONVERTIR VALOR A C++
# ============================================================

def valor_cpp(
    valor,
    tipo
):

    valor = str(
        valor
    ).strip()


    if tipo == "cadena":

        valor = (
            valor
            .replace(
                "\\",
                "\\\\"
            )
            .replace(
                '"',
                '\\"'
            )
        )


        return (
            '"'
            + valor
            + '"'
        )


    if tipo == "logico":

        return (
            "true"
            if valor.lower() in (
                "verdadero",
                "true",
                "1",
                "si",
                "sí"
            )
            else "false"
        )


    return valor


# ============================================================
# ANALIZAR VARIABLES
# ============================================================

def obtener_tipos(lineas):

    tipos = {}


    for linea in lineas:

        coincidencia = re.match(
            r"^Definir\s+(.+?)\s+Como\s+(.+)$",
            linea,
            flags=re.IGNORECASE
        )


        if coincidencia:

            variables = (
                coincidencia.group(1)
            )


            tipo = normalizar_tipo(
                coincidencia.group(2)
            )


            for variable in variables.split(
                ","
            ):

                variable = (
                    variable.strip()
                )


                if variable:

                    tipos[
                        variable
                    ] = tipo


    return tipos


# ============================================================
# GENERAR PYTHON
# ============================================================

def generar_python(
    pseudocodigo,
    entradas=None
):

    entradas = entradas or {}


    # --------------------------------------------------------
    # LIMPIAR LÍNEAS
    # --------------------------------------------------------

    lineas = []


    for linea in pseudocodigo.splitlines():

        linea = quitar_comentarios(
            linea
        )


        if linea:

            lineas.append(
                linea
            )


    tipos = obtener_tipos(
        lineas
    )

    nombres_variables = set(
        tipos.keys()
    )


    necesita_para = any(
        re.match(
            r"^Para\s+",
            linea,
            flags=re.IGNORECASE
        )
        for linea in lineas
    )


    resultado = [
        "import math",
        ""
    ]


    # ========================================================
    # RANGE INCLUSIVO
    # ========================================================

    if necesita_para:

        resultado.extend([
            "def rango_inclusivo(inicio, fin, paso=1):",
            "    if paso == 0:",
            "        paso = 1",
            "",
            "    if paso > 0:",
            "        return range(inicio, fin + 1, paso)",
            "",
            "    return range(inicio, fin - 1, paso)",
            "",
            ""
        ])


    indentacion = 0


    def agregar(texto=""):

        resultado.append(
            "    " * indentacion
            + texto
        )


    # ========================================================
    # PROCESAR
    # ========================================================

    for linea in lineas:

        mayus = linea.upper()


        # ----------------------------------------------------
        # ALGORITMO
        # ----------------------------------------------------

        if mayus.startswith(
            "ALGORITMO"
        ):

            continue


        if mayus == "FINALGORITMO":

            continue


        # ----------------------------------------------------
        # DEFINIR
        # ----------------------------------------------------

        coincidencia = re.match(
            r"^Definir\s+(.+?)\s+Como\s+(.+)$",
            linea,
            flags=re.IGNORECASE
        )


        if coincidencia:

            variables = (
                coincidencia.group(1)
            )


            tipo = normalizar_tipo(
                coincidencia.group(2)
            )


            valores_iniciales = {
                "entero": "0",
                "real": "0.0",
                "cadena": '""',
                "logico": "False"
            }


            for variable in variables.split(
                ","
            ):

                variable = (
                    variable.strip()
                )


                if not variable:

                    continue


                agregar(
                    f"{variable} = "
                    f"{valores_iniciales[tipo]}"
                )


            continue


        # ----------------------------------------------------
        # LEER
        # ----------------------------------------------------

        coincidencia = re.match(
            r"^Leer\s+(.+)$",
            linea,
            flags=re.IGNORECASE
        )


        if coincidencia:

            variables = [
                variable.strip()
                for variable in
                coincidencia
                .group(1)
                .split(",")
                if variable.strip()
            ]


            for variable in variables:

                tipo = tipos.get(
                    variable,
                    "cadena"
                )


                # ============================================
                # SI EL USUARIO YA EJECUTÓ CON UN VALOR
                # ============================================

                if (
                    variable in entradas
                    and str(
                        entradas[
                            variable
                        ]
                    ).strip() != ""
                ):

                    valor = valor_python(
                        entradas[
                            variable
                        ],
                        tipo
                    )


                    agregar(
                        f"{variable} = {valor}"
                    )


                # ============================================
                # SI NO HAY VALOR, MANTENER INPUT NORMAL
                # ============================================

                elif tipo == "entero":

                    agregar(
                        f"{variable} = int(input())"
                    )


                elif tipo == "real":

                    agregar(
                        f"{variable} = float(input())"
                    )


                elif tipo == "logico":

                    agregar(
                        f"{variable} = "
                        f"input().strip().lower() "
                        f"in ('verdadero', 'true', '1', 'si', 'sí')"
                    )


                else:

                    agregar(
                        f"{variable} = input()"
                    )


            continue


        # ----------------------------------------------------
        # ESCRIBIR
        # ----------------------------------------------------

        coincidencia = re.match(
            r"^Escribir\s*(.*)$",
            linea,
            flags=re.IGNORECASE
        )


        if coincidencia:

            contenido = (
                coincidencia.group(1)
                .strip()
            )


            if not contenido:

                agregar(
                    "print()"
                )

                continue


            partes = dividir_argumentos(
                contenido
            )


            partes_python = [
                expresion_python(
                    parte,
                    nombres_variables
                )
                for parte in partes
            ]


            agregar(
                "print("
                + ", ".join(
                    partes_python
                )
                + ', sep="")'
            )


            continue


        # ----------------------------------------------------
        # ASIGNACIÓN
        # ----------------------------------------------------

        coincidencia = re.match(
            r"^([A-Za-z_][A-Za-z0-9_]*)"
            r"\s*<-\s*(.+)$",
            linea
        )


        if coincidencia:

            variable = (
                coincidencia.group(1)
            )


            expresion = expresion_python(
                coincidencia.group(2),
                nombres_variables
            )


            agregar(
                f"{variable} = {expresion}"
            )


            continue


        # ----------------------------------------------------
        # SI
        # ----------------------------------------------------

        coincidencia = re.match(
            r"^Si\s+(.+?)\s+Entonces$",
            linea,
            flags=re.IGNORECASE
        )


        if coincidencia:

            condicion = expresion_python(
                coincidencia.group(1),
                nombres_variables
            )


            agregar(
                f"if {condicion}:"
            )


            indentacion += 1

            continue


        # ----------------------------------------------------
        # SINO
        # ----------------------------------------------------

        if mayus in (
            "SINO",
            "SI NO"
        ):

            indentacion = max(
                0,
                indentacion - 1
            )


            agregar(
                "else:"
            )


            indentacion += 1

            continue


        # ----------------------------------------------------
        # FINSI
        # ----------------------------------------------------

        if mayus in (
            "FINSI",
            "FIN SI"
        ):

            indentacion = max(
                0,
                indentacion - 1
            )

            continue


        # ----------------------------------------------------
        # PARA
        # ----------------------------------------------------

        coincidencia = re.match(
            r"^Para\s+(\w+)\s*<-\s*(.+?)"
            r"\s+Hasta\s+(.+?)"
            r"(?:\s+Con\s+Paso\s+(.+?))?"
            r"\s+Hacer$",
            linea,
            flags=re.IGNORECASE
        )


        if coincidencia:

            variable = (
                coincidencia.group(1)
            )


            inicio = expresion_python(
                coincidencia.group(2),
                nombres_variables
            )


            fin = expresion_python(
                coincidencia.group(3),
                nombres_variables
            )


            paso = (
                coincidencia.group(4)
            )


            if paso:

                paso = expresion_python(
                    paso,
                    nombres_variables
                )


                agregar(
                    f"for {variable} in "
                    f"rango_inclusivo("
                    f"{inicio}, {fin}, {paso}):"
                )


            else:

                agregar(
                    f"for {variable} in "
                    f"rango_inclusivo("
                    f"{inicio}, {fin}):"
                )


            indentacion += 1

            continue


        if mayus == "FINPARA":

            indentacion = max(
                0,
                indentacion - 1
            )

            continue


        # ----------------------------------------------------
        # MIENTRAS
        # ----------------------------------------------------

        coincidencia = re.match(
            r"^Mientras\s+(.+?)\s+Hacer$",
            linea,
            flags=re.IGNORECASE
        )


        if coincidencia:

            condicion = expresion_python(
                coincidencia.group(1),
                nombres_variables
            )


            agregar(
                f"while {condicion}:"
            )


            indentacion += 1

            continue


        if mayus == "FINMIENTRAS":

            indentacion = max(
                0,
                indentacion - 1
            )

            continue


        # ----------------------------------------------------
        # REPETIR
        # ----------------------------------------------------

        if mayus == "REPETIR":

            agregar(
                "while True:"
            )


            indentacion += 1

            continue


        coincidencia = re.match(
            r"^Hasta\s+Que\s+(.+)$",
            linea,
            flags=re.IGNORECASE
        )


        if coincidencia:

            condicion = expresion_python(
                coincidencia.group(1),
                nombres_variables
            )


            agregar(
                f"if {condicion}:"
            )


            agregar(
                "    break"
            )


            indentacion = max(
                0,
                indentacion - 1
            )


            continue


        # ----------------------------------------------------
        # NO RECONOCIDA
        # ----------------------------------------------------

        agregar(
            "# " + linea
        )


    return "\n".join(
        resultado
    )


# ============================================================
# GENERAR C++
# ============================================================

def generar_cpp(
    pseudocodigo,
    entradas=None
):

    entradas = entradas or {}


    lineas = []


    for linea in pseudocodigo.splitlines():

        linea = quitar_comentarios(
            linea
        )


        if linea:

            lineas.append(
                linea
            )


    tipos = obtener_tipos(
        lineas
    )

    nombres_variables = set(
        tipos.keys()
    )


    resultado = [
        "#include <iostream>",
        "#include <string>",
        "#include <cmath>",
        "",
        "using namespace std;",
        "",
        "int main()",
        "{"
    ]


    indentacion = 1


    def agregar(texto=""):

        resultado.append(
            "    " * indentacion
            + texto
        )


    for linea in lineas:

        mayus = linea.upper()


        # ----------------------------------------------------
        # ALGORITMO
        # ----------------------------------------------------

        if mayus.startswith(
            "ALGORITMO"
        ):

            continue


        if mayus == "FINALGORITMO":

            continue


        # ----------------------------------------------------
        # DEFINIR
        # ----------------------------------------------------

        coincidencia = re.match(
            r"^Definir\s+(.+?)\s+Como\s+(.+)$",
            linea,
            flags=re.IGNORECASE
        )


        if coincidencia:

            variables = [
                variable.strip()
                for variable in
                coincidencia
                .group(1)
                .split(",")
                if variable.strip()
            ]


            tipo = normalizar_tipo(
                coincidencia.group(2)
            )


            tipos_cpp = {
                "entero": "int",
                "real": "double",
                "cadena": "string",
                "logico": "bool"
            }


            agregar(
                tipos_cpp[
                    tipo
                ]
                + " "
                + ", ".join(
                    variables
                )
                + ";"
            )


            continue


        # ----------------------------------------------------
        # LEER
        # ----------------------------------------------------

        coincidencia = re.match(
            r"^Leer\s+(.+)$",
            linea,
            flags=re.IGNORECASE
        )


        if coincidencia:

            variables = [
                variable.strip()
                for variable in
                coincidencia
                .group(1)
                .split(",")
                if variable.strip()
            ]


            for variable in variables:

                tipo = tipos.get(
                    variable,
                    "cadena"
                )


                # ============================================
                # HAY VALOR INTRODUCIDO
                # ============================================

                if (
                    variable in entradas
                    and str(
                        entradas[
                            variable
                        ]
                    ).strip() != ""
                ):

                    valor = valor_cpp(
                        entradas[
                            variable
                        ],
                        tipo
                    )


                    agregar(
                        f"{variable} = {valor};"
                    )


                # ============================================
                # NO HAY VALOR
                # ============================================

                else:

                    agregar(
                        f"cin >> {variable};"
                    )


            continue


        # ----------------------------------------------------
        # ESCRIBIR
        # ----------------------------------------------------

        coincidencia = re.match(
            r"^Escribir\s*(.*)$",
            linea,
            flags=re.IGNORECASE
        )


        if coincidencia:

            contenido = (
                coincidencia.group(1)
                .strip()
            )


            if not contenido:

                agregar(
                    "cout << endl;"
                )

                continue


            partes = dividir_argumentos(
                contenido
            )


            partes_cpp = [
                expresion_cpp(
                    parte,
                    nombres_variables
                )
                for parte in partes
            ]


            agregar(
                "cout << "
                + " << ".join(
                    partes_cpp
                )
                + " << endl;"
            )


            continue


        # ----------------------------------------------------
        # ASIGNACIÓN
        # ----------------------------------------------------

        coincidencia = re.match(
            r"^([A-Za-z_][A-Za-z0-9_]*)"
            r"\s*<-\s*(.+)$",
            linea
        )


        if coincidencia:

            variable = (
                coincidencia.group(1)
            )


            expresion = expresion_cpp(
                coincidencia.group(2),
                nombres_variables
            )


            agregar(
                f"{variable} = "
                f"{expresion};"
            )


            continue


        # ----------------------------------------------------
        # SI
        # ----------------------------------------------------

        coincidencia = re.match(
            r"^Si\s+(.+?)\s+Entonces$",
            linea,
            flags=re.IGNORECASE
        )


        if coincidencia:

            condicion = expresion_cpp(
                coincidencia.group(1),
                nombres_variables
            )


            agregar(
                f"if ({condicion})"
            )

            agregar(
                "{"
            )


            indentacion += 1

            continue


        # ----------------------------------------------------
        # SINO
        # ----------------------------------------------------

        if mayus in (
            "SINO",
            "SI NO"
        ):

            indentacion = max(
                1,
                indentacion - 1
            )


            agregar(
                "}"
            )

            agregar(
                "else"
            )

            agregar(
                "{"
            )


            indentacion += 1

            continue


        # ----------------------------------------------------
        # FINSI
        # ----------------------------------------------------

        if mayus in (
            "FINSI",
            "FIN SI"
        ):

            indentacion = max(
                1,
                indentacion - 1
            )


            agregar(
                "}"
            )


            continue


        # ----------------------------------------------------
        # PARA
        # ----------------------------------------------------

        coincidencia = re.match(
            r"^Para\s+(\w+)\s*<-\s*(.+?)"
            r"\s+Hasta\s+(.+?)"
            r"(?:\s+Con\s+Paso\s+(.+?))?"
            r"\s+Hacer$",
            linea,
            flags=re.IGNORECASE
        )


        if coincidencia:

            variable = (
                coincidencia.group(1)
            )


            inicio = expresion_cpp(
                coincidencia.group(2),
                nombres_variables
            )


            fin = expresion_cpp(
                coincidencia.group(3),
                nombres_variables
            )


            paso_original = (
                coincidencia.group(4)
            )


            paso = (
                expresion_cpp(
                    paso_original,
                    nombres_variables
                )
                if paso_original
                else "1"
            )


            declaracion = (
                variable
                if variable in tipos
                else "int " + variable
            )


            agregar(
                f"for ({declaracion} = {inicio}; "
                f"({paso}) > 0 ? "
                f"{variable} <= {fin} : "
                f"{variable} >= {fin}; "
                f"{variable} += {paso})"
            )


            agregar(
                "{"
            )


            indentacion += 1

            continue


        if mayus == "FINPARA":

            indentacion = max(
                1,
                indentacion - 1
            )


            agregar(
                "}"
            )


            continue


        # ----------------------------------------------------
        # MIENTRAS
        # ----------------------------------------------------

        coincidencia = re.match(
            r"^Mientras\s+(.+?)\s+Hacer$",
            linea,
            flags=re.IGNORECASE
        )


        if coincidencia:

            condicion = expresion_cpp(
                coincidencia.group(1),
                nombres_variables
            )


            agregar(
                f"while ({condicion})"
            )

            agregar(
                "{"
            )


            indentacion += 1

            continue


        if mayus == "FINMIENTRAS":

            indentacion = max(
                1,
                indentacion - 1
            )


            agregar(
                "}"
            )


            continue


        # ----------------------------------------------------
        # REPETIR
        # ----------------------------------------------------

        if mayus == "REPETIR":

            agregar(
                "do"
            )

            agregar(
                "{"
            )


            indentacion += 1

            continue


        coincidencia = re.match(
            r"^Hasta\s+Que\s+(.+)$",
            linea,
            flags=re.IGNORECASE
        )


        if coincidencia:

            indentacion = max(
                1,
                indentacion - 1
            )


            condicion = expresion_cpp(
                coincidencia.group(1),
                nombres_variables
            )


            agregar(
                f"}} while (!({condicion}));"
            )


            continue


        # ----------------------------------------------------
        # NO RECONOCIDA
        # ----------------------------------------------------

        agregar(
            "// " + linea
        )


    agregar("")

    agregar(
        "return 0;"
    )


    resultado.append(
        "}"
    )


    return "\n".join(
        resultado
    )


# ============================================================
# API DE TRADUCCIÓN
# ============================================================

@traductor_bp.route(
    "/api/traducir",
    methods=["POST"]
)
def traducir():

    datos = request.get_json(
        silent=True
    ) or {}


    pseudocodigo = datos.get(
        "pseudocodigo",
        ""
    )


    entradas = datos.get(
        "entradas",
        {}
    ) or {}


    if not pseudocodigo.strip():

        return jsonify({
            "ok": True,
            "python": "",
            "cpp": ""
        })


    try:

        codigo_python = generar_python(
            pseudocodigo,
            entradas
        )


        codigo_cpp = generar_cpp(
            pseudocodigo,
            entradas
        )


        return jsonify({
            "ok": True,
            "python": codigo_python,
            "cpp": codigo_cpp
        })


    except Exception as error:

        return jsonify({
            "ok": False,
            "error": str(
                error
            )
        }), 400