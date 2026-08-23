from flask import Blueprint, request, jsonify
import re


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
# EXPRESIONES PYTHON
# ============================================================

def expresion_python(texto):

    texto = texto.strip()


    texto = texto.replace(
        "<>",
        "!="
    )


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


    texto = re.sub(
        r"\bMOD\b",
        "%",
        texto,
        flags=re.IGNORECASE
    )


    texto = texto.replace(
        "^",
        "**"
    )


    texto = re.sub(
        r"\bRC\s*\((.*?)\)",
        r"math.sqrt(\1)",
        texto,
        flags=re.IGNORECASE
    )


    texto = re.sub(
        r"(?<![<>=!])=(?!=)",
        "==",
        texto
    )


    return texto


# ============================================================
# EXPRESIONES C++
# ============================================================

def expresion_cpp(texto):

    texto = texto.strip()


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


    # Potencias simples:
    # x ^ 2
    # a ^ b

    patron_potencia = re.compile(
        r"([A-Za-z_][A-Za-z0-9_]*|\d+(?:\.\d+)?)"
        r"\s*\^\s*"
        r"([A-Za-z_][A-Za-z0-9_]*|\d+(?:\.\d+)?)"
    )


    while patron_potencia.search(texto):

        texto = patron_potencia.sub(
            r"pow(\1, \2)",
            texto
        )


    return texto


# ============================================================
# GENERAR PYTHON
# ============================================================

def generar_python(pseudocodigo):

    lineas_originales = (
        pseudocodigo.splitlines()
    )

    lineas = []


    for linea in lineas_originales:

        linea = quitar_comentarios(
            linea
        )

        if linea:

            lineas.append(
                linea
            )


    tipos = {}

    necesita_para = False


    # ========================================================
    # PRIMER RECORRIDO - TIPOS
    # ========================================================

    for linea in lineas:

        coincidencia = re.match(
            r"^Definir\s+(.+?)\s+Como\s+(.+)$",
            linea,
            flags=re.IGNORECASE
        )


        if coincidencia:

            variables = coincidencia.group(1)

            tipo = normalizar_tipo(
                coincidencia.group(2)
            )


            for variable in variables.split(","):

                variable = variable.strip()

                tipos[
                    variable
                ] = tipo


        if re.match(
            r"^Para\s+",
            linea,
            flags=re.IGNORECASE
        ):

            necesita_para = True


    resultado = []


    resultado.append(
        "import math"
    )

    resultado.append("")


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


    for linea in lineas:

        mayus = linea.upper()


        # ====================================================
        # ALGORITMO
        # ====================================================

        if mayus.startswith(
            "ALGORITMO"
        ):

            continue


        if mayus == "FINALGORITMO":

            continue


        # ====================================================
        # DEFINIR
        # ====================================================

        coincidencia = re.match(
            r"^Definir\s+(.+?)\s+Como\s+(.+)$",
            linea,
            flags=re.IGNORECASE
        )


        if coincidencia:

            variables = coincidencia.group(1)

            tipo = normalizar_tipo(
                coincidencia.group(2)
            )


            valores_iniciales = {
                "entero": "0",
                "real": "0.0",
                "cadena": '""',
                "logico": "False"
            }


            for variable in variables.split(","):

                variable = variable.strip()


                agregar(
                    f"{variable} = "
                    f"{valores_iniciales[tipo]}"
                )


            continue


        # ====================================================
        # LEER
        # ====================================================

        coincidencia = re.match(
            r"^Leer\s+(.+)$",
            linea,
            flags=re.IGNORECASE
        )


        if coincidencia:

            variables = (
                coincidencia.group(1)
                .split(",")
            )


            for variable in variables:

                variable = variable.strip()

                tipo = tipos.get(
                    variable,
                    "cadena"
                )


                if tipo == "entero":

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
                        f"in ('verdadero', 'true', '1')"
                    )


                else:

                    agregar(
                        f"{variable} = input()"
                    )


            continue


        # ====================================================
        # ESCRIBIR
        # ====================================================

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
                expresion_python(x)
                for x in partes
            ]


            agregar(
                "print("
                + ", ".join(partes_python)
                + ', sep="")'
            )


            continue


        # ====================================================
        # ASIGNACION
        # ====================================================

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
                coincidencia.group(2)
            )


            agregar(
                f"{variable} = {expresion}"
            )


            continue


        # ====================================================
        # SI
        # ====================================================

        coincidencia = re.match(
            r"^Si\s+(.+?)\s+Entonces$",
            linea,
            flags=re.IGNORECASE
        )


        if coincidencia:

            condicion = expresion_python(
                coincidencia.group(1)
            )


            agregar(
                f"if {condicion}:"
            )


            indentacion += 1

            continue


        # ====================================================
        # SINO
        # ====================================================

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


        # ====================================================
        # FIN SI
        # ====================================================

        if mayus in (
            "FINSI",
            "FIN SI"
        ):

            indentacion = max(
                0,
                indentacion - 1
            )

            continue


        # ====================================================
        # PARA
        # ====================================================

        coincidencia = re.match(
            r"^Para\s+(\w+)\s*<-\s*(.+?)"
            r"\s+Hasta\s+(.+?)"
            r"(?:\s+Con\s+Paso\s+(.+?))?"
            r"\s+Hacer$",
            linea,
            flags=re.IGNORECASE
        )


        if coincidencia:

            variable = coincidencia.group(1)

            inicio = expresion_python(
                coincidencia.group(2)
            )

            fin = expresion_python(
                coincidencia.group(3)
            )

            paso = coincidencia.group(4)


            if paso:

                paso = expresion_python(
                    paso
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


        # ====================================================
        # MIENTRAS
        # ====================================================

        coincidencia = re.match(
            r"^Mientras\s+(.+?)\s+Hacer$",
            linea,
            flags=re.IGNORECASE
        )


        if coincidencia:

            condicion = expresion_python(
                coincidencia.group(1)
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


        # ====================================================
        # REPETIR
        # ====================================================

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
                coincidencia.group(1)
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


        # ====================================================
        # LINEA NO RECONOCIDA
        # ====================================================

        agregar(
            "# " + linea
        )


    return "\n".join(
        resultado
    )


# ============================================================
# GENERAR C++
# ============================================================

def generar_cpp(pseudocodigo):

    lineas_originales = (
        pseudocodigo.splitlines()
    )

    lineas = []


    for linea in lineas_originales:

        linea = quitar_comentarios(
            linea
        )


        if linea:

            lineas.append(
                linea
            )


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


            for variable in variables.split(","):

                tipos[
                    variable.strip()
                ] = tipo


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


        if mayus.startswith(
            "ALGORITMO"
        ):

            continue


        if mayus == "FINALGORITMO":

            continue


        # ====================================================
        # DEFINIR
        # ====================================================

        coincidencia = re.match(
            r"^Definir\s+(.+?)\s+Como\s+(.+)$",
            linea,
            flags=re.IGNORECASE
        )


        if coincidencia:

            variables = [
                x.strip()
                for x in
                coincidencia.group(1)
                .split(",")
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
                tipos_cpp[tipo]
                + " "
                + ", ".join(variables)
                + ";"
            )


            continue


        # ====================================================
        # LEER
        # ====================================================

        coincidencia = re.match(
            r"^Leer\s+(.+)$",
            linea,
            flags=re.IGNORECASE
        )


        if coincidencia:

            variables = [
                x.strip()
                for x in
                coincidencia.group(1)
                .split(",")
            ]


            agregar(
                "cin >> "
                + " >> ".join(variables)
                + ";"
            )


            continue


        # ====================================================
        # ESCRIBIR
        # ====================================================

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
                expresion_cpp(x)
                for x in partes
            ]


            agregar(
                "cout << "
                + " << ".join(partes_cpp)
                + " << endl;"
            )


            continue


        # ====================================================
        # ASIGNACIÓN
        # ====================================================

        coincidencia = re.match(
            r"^([A-Za-z_][A-Za-z0-9_]*)"
            r"\s*<-\s*(.+)$",
            linea
        )


        if coincidencia:

            agregar(
                coincidencia.group(1)
                + " = "
                + expresion_cpp(
                    coincidencia.group(2)
                )
                + ";"
            )


            continue


        # ====================================================
        # SI
        # ====================================================

        coincidencia = re.match(
            r"^Si\s+(.+?)\s+Entonces$",
            linea,
            flags=re.IGNORECASE
        )


        if coincidencia:

            agregar(
                "if ("
                + expresion_cpp(
                    coincidencia.group(1)
                )
                + ")"
            )

            agregar(
                "{"
            )


            indentacion += 1

            continue


        # ====================================================
        # SINO
        # ====================================================

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


        # ====================================================
        # FIN SI
        # ====================================================

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


        # ====================================================
        # PARA
        # ====================================================

        coincidencia = re.match(
            r"^Para\s+(\w+)\s*<-\s*(.+?)"
            r"\s+Hasta\s+(.+?)"
            r"(?:\s+Con\s+Paso\s+(.+?))?"
            r"\s+Hacer$",
            linea,
            flags=re.IGNORECASE
        )


        if coincidencia:

            variable = coincidencia.group(1)

            inicio = expresion_cpp(
                coincidencia.group(2)
            )

            fin = expresion_cpp(
                coincidencia.group(3)
            )

            paso_original = (
                coincidencia.group(4)
            )


            paso = (
                expresion_cpp(
                    paso_original
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


        # ====================================================
        # MIENTRAS
        # ====================================================

        coincidencia = re.match(
            r"^Mientras\s+(.+?)\s+Hacer$",
            linea,
            flags=re.IGNORECASE
        )


        if coincidencia:

            agregar(
                "while ("
                + expresion_cpp(
                    coincidencia.group(1)
                )
                + ")"
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


        # ====================================================
        # REPETIR
        # ====================================================

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


            agregar(
                "} while (!("
                + expresion_cpp(
                    coincidencia.group(1)
                )
                + "));"
            )


            continue


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


    if not pseudocodigo.strip():

        return jsonify({
            "ok": True,
            "python": "",
            "cpp": ""
        })


    try:

        codigo_python = generar_python(
            pseudocodigo
        )


        codigo_cpp = generar_cpp(
            pseudocodigo
        )


        return jsonify({
            "ok": True,
            "python": codigo_python,
            "cpp": codigo_cpp
        })


    except Exception as error:

        return jsonify({
            "ok": False,
            "error": str(error)
        }), 400