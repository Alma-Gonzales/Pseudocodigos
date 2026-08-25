from flask import Flask, request, jsonify, render_template
from traductor import traductor_bp

import sqlite3
import re
import os
import webbrowser
import threading
import math


# ============================================================
# CONFIGURACIÓN PARA CONVERTIR PSEUDOCÓDIGO A PYTHON Y C++
# ============================================================

app = Flask(__name__)

app.register_blueprint(traductor_bp)



BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATOS_DIR = os.path.join(
    BASE_DIR,
    "datos"
)

os.makedirs(
    DATOS_DIR,
    exist_ok=True
)

SQLITE_DB = os.path.join(
    DATOS_DIR,
    "pseudocodigo.db"
)


# ============================================================
# BASE DE DATOS
# SQLITE LOCAL Y POSTGRESQL SUPABASE EN RENDER
# ============================================================

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    ""
).strip()

USAR_POSTGRES = bool(
    DATABASE_URL
)



def get_db():

    if USAR_POSTGRES:

        import psycopg
        from psycopg.rows import dict_row

        conn = psycopg.connect(
            DATABASE_URL,
            row_factory=dict_row
        )

        return conn


    conn = sqlite3.connect(
        SQLITE_DB
    )

    conn.row_factory = sqlite3.Row

    return conn


def init_db():

    conn = get_db()

    cursor = conn.cursor()


    if USAR_POSTGRES:

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ejercicios (
                id BIGSERIAL PRIMARY KEY,
                nombre TEXT NOT NULL,
                pseudocodigo TEXT NOT NULL,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    else:

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ejercicios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                pseudocodigo TEXT NOT NULL,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


    conn.commit()

    cursor.close()

    conn.close()


def limpiar_linea(linea):

    return (
        linea
        .strip()
        .replace("\t", " ")
    )


def quitar_comentarios(linea):

    if "//" in linea:

        linea = linea.split(
            "//",
            1
        )[0]

    return linea



def redon_pseint(valor):

    if valor >= 0:

        return math.floor(
            valor + 0.5
        )

    return math.ceil(
        valor - 0.5
    )



def normalizar_operadores(texto):

   
    texto = texto.replace(
        "<>",
        "!="
    )

    texto = re.sub(
        r"\bMOD\b",
        "%",
        texto,
        flags=re.IGNORECASE
    )

    texto = re.sub(
        r"\bDIV\b",
        "//",
        texto,
        flags=re.IGNORECASE
    )

    texto = re.sub(
        r"\bTRUNC\s*\(",
        "trunc(",
        texto,
        flags=re.IGNORECASE
    )


    texto = re.sub(
        r"\bREDON\s*\(",
        "redon(",
        texto,
        flags=re.IGNORECASE
    )


    texto = re.sub(
        r"\bRC\s*\(",
        "sqrt(",
        texto,
        flags=re.IGNORECASE
    )


    texto = re.sub(
        r"\bABS\s*\(",
        "abs(",
        texto,
        flags=re.IGNORECASE
    )


 
    texto = re.sub(
        r"\bLN\s*\(",
        "log(",
        texto,
        flags=re.IGNORECASE
    )


    texto = re.sub(
        r"\bEXP\s*\(",
        "exp(",
        texto,
        flags=re.IGNORECASE
    )


    texto = re.sub(
        r"\bSEN\s*\(",
        "sin(",
        texto,
        flags=re.IGNORECASE
    )


    texto = re.sub(
        r"\bCOS\s*\(",
        "cos(",
        texto,
        flags=re.IGNORECASE
    )



    texto = re.sub(
        r"\bTAN\s*\(",
        "tan(",
        texto,
        flags=re.IGNORECASE
    )



    texto = re.sub(
        r"\bASEN\s*\(",
        "asin(",
        texto,
        flags=re.IGNORECASE
    )



    texto = re.sub(
        r"\bACOS\s*\(",
        "acos(",
        texto,
        flags=re.IGNORECASE
    )



    texto = re.sub(
        r"\bATAN\s*\(",
        "atan(",
        texto,
        flags=re.IGNORECASE
    )



    texto = re.sub(
        r"\bY\b",
        " and ",
        texto,
        flags=re.IGNORECASE
    )


    texto = re.sub(
        r"\bO\b",
        " or ",
        texto,
        flags=re.IGNORECASE
    )



    texto = re.sub(
        r"\bNO\b",
        " not ",
        texto,
        flags=re.IGNORECASE
    )


    texto = texto.replace(
        "^",
        "**"
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
        r"(?<![<>=!])=(?!=)",
        "==",
        texto
    )


    return texto



def obtener_funciones_permitidas():

    return {
        "sqrt": math.sqrt,
        "abs": abs,
        "trunc": math.trunc,
        "redon": redon_pseint,
        "log": math.log,
        "exp": math.exp,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "asin": math.asin,
        "acos": math.acos,
        "atan": math.atan,
        "True": True,
        "False": False
    }



def detectar_variables_entrada(
    pseudocodigo
):

    variables = []


    for linea in pseudocodigo.splitlines():

        linea = quitar_comentarios(
            linea
        ).strip()


        if not linea:

            continue


        coincidencia = re.match(
            r"^Leer\s+(.+)$",
            linea,
            flags=re.IGNORECASE
        )


        if coincidencia:

            contenido = coincidencia.group(1)

            partes = contenido.split(",")


            for parte in partes:

                variable = parte.strip()


                if re.fullmatch(
                    r"[A-Za-z_][A-Za-z0-9_]*",
                    variable
                ):

                    if variable not in variables:

                        variables.append(
                            variable
                        )


    return variables


def convertir_valor(valor):

    if valor is None:

        return ""


    valor = str(
        valor
    ).strip()


    if valor == "":

        return ""


    if valor.lower() == "verdadero":

        return True


    if valor.lower() == "falso":

        return False


    try:

        return int(
            valor
        )

    except ValueError:

        pass


    try:

        return float(
            valor
        )

    except ValueError:

        pass


    return valor



def evaluar_expresion(
    expresion,
    variables
):

    expresion = expresion.strip()


    # Texto entre comillas
    if (
        len(expresion) >= 2
        and expresion[0] == '"'
        and expresion[-1] == '"'
    ):

        return expresion[1:-1]


    # Sustituir variables por valores
    nombres = sorted(
        variables.keys(),
        key=len,
        reverse=True
    )


    for nombre in nombres:

        valor = variables[
            nombre
        ]


        expresion = re.sub(
            rf"\b{re.escape(nombre)}\b",
            repr(valor),
            expresion
        )


    expresion = normalizar_operadores(
        expresion
    )


    # Validación básica
    permitidos = re.fullmatch(
        r"[0-9A-Za-z_+\-*/().%, '<>=!&|]*",
        expresion
    )


    if not permitidos:

        return expresion


    try:

        return eval(
            expresion,
            {
                "__builtins__": {}
            },
            obtener_funciones_permitidas()
        )


    except Exception:

        return expresion



def evaluar_condicion(
    condicion,
    variables
):

    condicion = condicion.strip()


    nombres = sorted(
        variables.keys(),
        key=len,
        reverse=True
    )


    for nombre in nombres:

        valor = variables[
            nombre
        ]


        condicion = re.sub(
            rf"\b{re.escape(nombre)}\b",
            repr(valor),
            condicion
        )


    condicion = normalizar_operadores(
        condicion
    )


    try:

        resultado = eval(
            condicion,
            {
                "__builtins__": {}
            },
            obtener_funciones_permitidas()
        )


        return bool(
            resultado
        )


    except Exception:

        return False



def dividir_escribir(
    contenido
):

    partes = []

    actual = ""

    dentro_comillas = False

    profundidad_parentesis = 0


    for caracter in contenido:

        if caracter == '"':

            dentro_comillas = (
                not dentro_comillas
            )

            actual += caracter

            continue


        if not dentro_comillas:

            if caracter == "(":

                profundidad_parentesis += 1


            elif caracter == ")":

                profundidad_parentesis -= 1


            elif (
                caracter == ","
                and profundidad_parentesis == 0
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



class Ejecutor:

    def __init__(
        self,
        pseudocodigo,
        entradas
    ):

        self.lineas = []


        for linea in pseudocodigo.splitlines():

            linea = quitar_comentarios(
                linea
            )

            linea = limpiar_linea(
                linea
            )


            if linea:

                self.lineas.append(
                    linea
                )


        self.variables = {}


        for nombre, valor in entradas.items():

            self.variables[
                nombre
            ] = convertir_valor(
                valor
            )


        self.salidas = []

        self.tabla_filas = []


        self.ejecutar_bloque(
            0,
            len(self.lineas)
        )



    def ejecutar_bloque(
        self,
        inicio,
        fin
    ):

        i = inicio


        while i < fin:

            linea = self.lineas[i]

            mayus = linea.upper()



            if mayus.startswith(
                "ALGORITMO"
            ):

                i += 1

                continue


            if mayus == "FINALGORITMO":

                i += 1

                continue


            if mayus.startswith(
                "DEFINIR"
            ):

                i += 1

                continue


            coincidencia = re.match(
                r"^Leer\s+(.+)$",
                linea,
                flags=re.IGNORECASE
            )


            if coincidencia:

                contenido = coincidencia.group(1)

                variables_leer = []


                for variable in contenido.split(","):

                    variable = variable.strip()


                    if not variable:

                        continue


                    variables_leer.append(
                        variable
                    )


                    if variable not in self.variables:

                        self.variables[
                            variable
                        ] = ""


                anterior_es_escribir = False


                if i > 0:

                    linea_anterior = self.lineas[
                        i - 1
                    ]


                    anterior_es_escribir = bool(
                        re.match(
                            r"^Escribir\b",
                            linea_anterior,
                            flags=re.IGNORECASE
                        )
                    )


                if (
                    anterior_es_escribir
                    and self.salidas
                ):

                    valores = []


                    for variable in variables_leer:

                        valor = self.variables.get(
                            variable,
                            ""
                        )


                        valores.append(
                            str(valor)
                        )


                    texto_valores = " ".join(
                        valores
                    )


                    texto_anterior = str(
                        self.salidas[-1]
                    )


                    if texto_valores:

                        if (
                            texto_anterior
                            and not texto_anterior.endswith(
                                (
                                    " ",
                                    "\t",
                                    "\n"
                                )
                            )
                        ):

                            texto_anterior += " "


                        self.salidas[-1] = (
                            texto_anterior
                            + texto_valores
                        )


                else:

                    for variable in variables_leer:

                        valor = self.variables.get(
                            variable,
                            ""
                        )


                        self.salidas.append(
                            f"{variable} = {valor}"
                        )


                i += 1

                continue


            coincidencia = re.match(
                r"^Escribir\s*(.*)$",
                linea,
                flags=re.IGNORECASE
            )


            if coincidencia:

                contenido = coincidencia.group(1)


                if contenido.strip() == "":

                    self.salidas.append(
                        ""
                    )

                    i += 1

                    continue


                partes = dividir_escribir(
                    contenido
                )


                valores = []


                for parte in partes:

                    valor = evaluar_expresion(
                        parte,
                        self.variables
                    )


                    valores.append(
                        str(valor)
                    )


                texto_completo = "".join(
                    valores
                )


                self.salidas.append(
                    texto_completo
                )


                if "|" in texto_completo:

                    columnas = [
                        x.strip()
                        for x in texto_completo.split("|")
                    ]


                    self.tabla_filas.append(
                        columnas
                    )


                i += 1

                continue


            coincidencia = re.match(
                r"^([A-Za-z_][A-Za-z0-9_]*)\s*<-\s*(.+)$",
                linea
            )


            if coincidencia:

                variable = coincidencia.group(1)

                expresion = coincidencia.group(2)


                valor = evaluar_expresion(
                    expresion,
                    self.variables
                )


                self.variables[
                    variable
                ] = valor


                i += 1

                continue


            coincidencia = re.match(
                r"^Si\s+(.+?)\s+Entonces$",
                linea,
                flags=re.IGNORECASE
            )


            if coincidencia:

                condicion = coincidencia.group(1)


                fin_si, posicion_sino = (
                    self.buscar_fin_si(i)
                )


                resultado = evaluar_condicion(
                    condicion,
                    self.variables
                )


                if resultado:

                    inicio_bloque = i + 1


                    fin_bloque = (
                        posicion_sino
                        if posicion_sino is not None
                        else fin_si
                    )


                    self.ejecutar_bloque(
                        inicio_bloque,
                        fin_bloque
                    )


                elif posicion_sino is not None:

                    self.ejecutar_bloque(
                        posicion_sino + 1,
                        fin_si
                    )


                i = fin_si + 1

                continue


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

                inicio_expr = coincidencia.group(2)

                fin_expr = coincidencia.group(3)

                paso_expr = coincidencia.group(4)


                inicio_valor = evaluar_expresion(
                    inicio_expr,
                    self.variables
                )


                fin_valor = evaluar_expresion(
                    fin_expr,
                    self.variables
                )


                if paso_expr:

                    paso_valor = evaluar_expresion(
                        paso_expr,
                        self.variables
                    )

                else:

                    paso_valor = 1


                fin_para = self.buscar_fin_para(
                    i
                )


                try:

                    inicio_num = int(
                        inicio_valor
                    )

                    fin_num = int(
                        fin_valor
                    )

                    paso_num = int(
                        paso_valor
                    )


                except Exception:

                    i = fin_para + 1

                    continue


                if paso_num == 0:

                    paso_num = 1


                valor = inicio_num


                while (
                    valor <= fin_num
                    if paso_num > 0
                    else valor >= fin_num
                ):

                    self.variables[
                        variable
                    ] = valor


                    self.ejecutar_bloque(
                        i + 1,
                        fin_para
                    )


                    valor += paso_num


                i = fin_para + 1

                continue



            coincidencia = re.match(
                r"^Mientras\s+(.+?)\s+Hacer$",
                linea,
                flags=re.IGNORECASE
            )


            if coincidencia:

                condicion = coincidencia.group(1)


                fin_mientras = (
                    self.buscar_fin_mientras(
                        i
                    )
                )


                contador_seguridad = 0


                while evaluar_condicion(
                    condicion,
                    self.variables
                ):

                    self.ejecutar_bloque(
                        i + 1,
                        fin_mientras
                    )


                    contador_seguridad += 1


                    if contador_seguridad > 10000:

                        break


                i = fin_mientras + 1

                continue


            if mayus == "REPETIR":

                fin_repetir = (
                    self.buscar_hasta_que(
                        i
                    )
                )


                contador_seguridad = 0


                while True:

                    self.ejecutar_bloque(
                        i + 1,
                        fin_repetir
                    )


                    condicion_linea = self.lineas[
                        fin_repetir
                    ]


                    condicion = re.sub(
                        r"^Hasta\s+Que\s+",
                        "",
                        condicion_linea,
                        flags=re.IGNORECASE
                    )


                    if evaluar_condicion(
                        condicion,
                        self.variables
                    ):

                        break


                    contador_seguridad += 1


                    if contador_seguridad > 10000:

                        break


                i = fin_repetir + 1

                continue


            i += 1


    def buscar_fin_si(
        self,
        posicion
    ):

        profundidad = 0

        posicion_sino = None


        for i in range(
            posicion + 1,
            len(self.lineas)
        ):

            mayus = self.lineas[
                i
            ].upper()


            if re.match(
                r"^SI\s+",
                self.lineas[i],
                flags=re.IGNORECASE
            ):

                profundidad += 1


            if (
                mayus in (
                    "SINO",
                    "SI NO"
                )
                and profundidad == 0
            ):

                posicion_sino = i


            if mayus in (
                "FINSI",
                "FIN SI"
            ):

                if profundidad == 0:

                    return (
                        i,
                        posicion_sino
                    )


                profundidad -= 1


        return (
            len(self.lineas) - 1,
            posicion_sino
        )



    def buscar_fin_para(
        self,
        posicion
    ):

        profundidad = 0


        for i in range(
            posicion + 1,
            len(self.lineas)
        ):

            mayus = self.lineas[
                i
            ].upper()


            if mayus.startswith(
                "PARA "
            ):

                profundidad += 1


            if mayus == "FINPARA":

                if profundidad == 0:

                    return i


                profundidad -= 1


        return len(
            self.lineas
        ) - 1



    def buscar_fin_mientras(
        self,
        posicion
    ):

        profundidad = 0


        for i in range(
            posicion + 1,
            len(self.lineas)
        ):

            mayus = self.lineas[
                i
            ].upper()


            if mayus.startswith(
                "MIENTRAS "
            ):

                profundidad += 1


            if mayus == "FINMIENTRAS":

                if profundidad == 0:

                    return i


                profundidad -= 1


        return len(
            self.lineas
        ) - 1



    def buscar_hasta_que(
        self,
        posicion
    ):

        profundidad = 0


        for i in range(
            posicion + 1,
            len(self.lineas)
        ):

            mayus = self.lineas[
                i
            ].upper()


            if mayus == "REPETIR":

                profundidad += 1


            if mayus.startswith(
                "HASTA QUE"
            ):

                if profundidad == 0:

                    return i


                profundidad -= 1


        return len(
            self.lineas
        ) - 1




def ejecutar_pseudocodigo(
    pseudocodigo,
    entradas
):

    ejecutor = Ejecutor(
        pseudocodigo,
        entradas
    )


    return {
        "salidas":
            ejecutor.salidas,

        "tabla":
            ejecutor.tabla_filas,

        "variables":
            ejecutor.variables
    }



def escapar_mermaid(
    texto
):

    texto = str(
        texto
    )


    texto = texto.replace(
        '"',
        "'"
    )


    texto = texto.replace(
        "[",
        "("
    )


    texto = texto.replace(
        "]",
        ")"
    )


    texto = texto.replace(
        "\n",
        "<br/>"
    )


    return texto


def generar_diagrama(
    pseudocodigo
):

    lineas = pseudocodigo.splitlines()

    mermaid = []

    mermaid.append(
        "flowchart TD"
    )


    mermaid.append(
        "classDef inicio fill:#2563eb,stroke:#1d4ed8,color:#ffffff,stroke-width:2px"
    )

    mermaid.append(
        "classDef leer fill:#22c55e,stroke:#15803d,color:#ffffff,stroke-width:2px"
    )

    mermaid.append(
        "classDef escribir fill:#60a5fa,stroke:#2563eb,color:#ffffff,stroke-width:2px"
    )

    mermaid.append(
        "classDef asignacion fill:#14b8a6,stroke:#0f766e,color:#ffffff,stroke-width:2px"
    )

    mermaid.append(
        "classDef decision fill:#a855f7,stroke:#7e22ce,color:#ffffff,stroke-width:2px"
    )

    mermaid.append(
        "classDef para fill:#f97316,stroke:#c2410c,color:#ffffff,stroke-width:2px"
    )

    mermaid.append(
        "classDef mientras fill:#facc15,stroke:#ca8a04,color:#111827,stroke-width:2px"
    )

    mermaid.append(
        "classDef repetir fill:#ec4899,stroke:#be185d,color:#ffffff,stroke-width:2px"
    )

    mermaid.append(
        "classDef union fill:#a855f7,stroke:#7e22ce,color:#a855f7,stroke-width:2px"
    )


    contador = 0


    mermaid.append(
        'inicio(["INICIO"]):::inicio'
    )


    anterior = "inicio"

    pila = []


    def conectar_nodo(
        nodo
    ):

        nonlocal anterior


        if (
            pila
            and pila[-1].get(
                "esperando_inicio_si",
                False
            )
        ):

            decision = pila[-1][
                "nodo"
            ]


            mermaid.append(
                f"{decision} -->|SÍ| {nodo}"
            )


            pila[-1][
                "esperando_inicio_si"
            ] = False


        elif (
            pila
            and pila[-1].get(
                "esperando_inicio_no",
                False
            )
        ):

            decision = pila[-1][
                "nodo"
            ]


            mermaid.append(
                f"{decision} -->|NO| {nodo}"
            )


            pila[-1][
                "esperando_inicio_no"
            ] = False


        else:

            mermaid.append(
                f"{anterior} --> {nodo}"
            )


        anterior = nodo


    for linea in lineas:

        linea = quitar_comentarios(
            linea
        ).strip()


        if not linea:

            continue


        mayus = linea.upper()


        if mayus.startswith(
            "ALGORITMO"
        ):

            continue


        if mayus == "FINALGORITMO":

            continue


        if mayus.startswith(
            "DEFINIR"
        ):

            continue


        if mayus.startswith(
            "LEER "
        ):

            variable = linea[
                5:
            ].strip()


            contador += 1

            nodo = f"n{contador}"


            texto = escapar_mermaid(
                f"LEER<br/>{variable}"
            )


            mermaid.append(
                f'{nodo}["{texto}"]:::leer'
            )


            conectar_nodo(
                nodo
            )


            continue



        if mayus.startswith(
            "ESCRIBIR"
        ):

            texto = linea[
                8:
            ].strip()


            texto = escapar_mermaid(
                f"ESCRIBIR<br/>{texto}"
            )


            contador += 1

            nodo = f"n{contador}"


            mermaid.append(
                f'{nodo}["{texto}"]:::escribir'
            )


            conectar_nodo(
                nodo
            )


            continue



        coincidencia = re.match(
            r"^Si\s+(.+?)\s+Entonces$",
            linea,
            flags=re.IGNORECASE
        )


        if coincidencia:

            condicion = coincidencia.group(
                1
            )


            condicion = escapar_mermaid(
                condicion
            )


            contador += 1

            nodo = f"n{contador}"


            mermaid.append(
                f'{nodo}{{"{condicion}"}}:::decision'
            )


            if (
                pila
                and pila[-1].get(
                    "esperando_inicio_si",
                    False
                )
            ):

                decision_padre = pila[-1][
                    "nodo"
                ]


                mermaid.append(
                    f"{decision_padre} -->|SÍ| {nodo}"
                )


                pila[-1][
                    "esperando_inicio_si"
                ] = False


            elif (
                pila
                and pila[-1].get(
                    "esperando_inicio_no",
                    False
                )
            ):

                decision_padre = pila[-1][
                    "nodo"
                ]


                mermaid.append(
                    f"{decision_padre} -->|NO| {nodo}"
                )


                pila[-1][
                    "esperando_inicio_no"
                ] = False


            else:

                mermaid.append(
                    f"{anterior} --> {nodo}"
                )


            pila.append({
                "tipo": "si",
                "nodo": nodo,
                "fin_si": None,
                "fin_no": None,
                "tiene_sino": False,
                "esperando_inicio_si": True,
                "esperando_inicio_no": False
            })


            anterior = nodo

            continue



        if mayus in (
            "SINO",
            "SI NO"
        ):

            if pila:

                actual = pila[-1]


                actual[
                    "fin_si"
                ] = anterior


                actual[
                    "tiene_sino"
                ] = True


                actual[
                    "esperando_inicio_no"
                ] = True


                anterior = actual[
                    "nodo"
                ]


            continue



        if mayus in (
            "FINSI",
            "FIN SI"
        ):

            if pila:

                actual = pila.pop()

                decision = actual[
                    "nodo"
                ]


                if actual[
                    "tiene_sino"
                ]:

                    actual[
                        "fin_no"
                    ] = anterior


                    contador += 1

                    union = f"n{contador}"


                    mermaid.append(
                        f'{union}(( )):::union'
                    )


                    if actual[
                        "fin_si"
                    ]:

                        mermaid.append(
                            f'{actual["fin_si"]} --> {union}'
                        )

                    else:

                        mermaid.append(
                            f"{decision} -->|SÍ| {union}"
                        )


                    if actual[
                        "fin_no"
                    ]:

                        mermaid.append(
                            f'{actual["fin_no"]} --> {union}'
                        )

                    else:

                        mermaid.append(
                            f"{decision} -->|NO| {union}"
                        )


                    anterior = union


                else:

                    contador += 1

                    union = f"n{contador}"


                    mermaid.append(
                        f'{union}(( )):::union'
                    )


                    mermaid.append(
                        f"{anterior} --> {union}"
                    )


                    mermaid.append(
                        f"{decision} -->|NO| {union}"
                    )


                    anterior = union


            continue


        coincidencia = re.match(
            r"^Para\s+(\w+)",
            linea,
            flags=re.IGNORECASE
        )


        if coincidencia:

            variable = coincidencia.group(
                1
            )


            contador += 1

            nodo = f"n{contador}"


            mermaid.append(
                f'{nodo}{{"PARA<br/>{variable}"}}:::para'
            )


            conectar_nodo(
                nodo
            )


            continue



        if mayus.startswith(
            "MIENTRAS "
        ):

            condicion = linea[
                9:
            ].strip()


            condicion = re.sub(
                r"\s+Hacer$",
                "",
                condicion,
                flags=re.IGNORECASE
            )


            condicion = escapar_mermaid(
                condicion
            )


            contador += 1

            nodo = f"n{contador}"


            mermaid.append(
                f'{nodo}{{"MIENTRAS<br/>{condicion}"}}:::mientras'
            )


            conectar_nodo(
                nodo
            )


            continue


        if mayus == "REPETIR":

            contador += 1

            nodo = f"n{contador}"


            mermaid.append(
                f'{nodo}{{"REPETIR"}}:::repetir'
            )


            conectar_nodo(
                nodo
            )


            continue



        if "<-" in linea:

            partes = linea.split(
                "<-",
                1
            )


            texto = (
                partes[0].strip()
                + " ← "
                + partes[1].strip()
            )


            texto = escapar_mermaid(
                texto
            )


            contador += 1

            nodo = f"n{contador}"


            mermaid.append(
                f'{nodo}["{texto}"]:::asignacion'
            )


            conectar_nodo(
                nodo
            )


            continue


    contador += 1

    fin = f"n{contador}"


    mermaid.append(
        f'{fin}(["FIN"]):::inicio'
    )


    mermaid.append(
        f"{anterior} --> {fin}"
    )


    return "\n".join(
        mermaid
    )


@app.route(
    "/api/ejercicios",
    methods=["GET"]
)
def obtener_ejercicios():

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""
        SELECT
            id,
            nombre,
            pseudocodigo,
            fecha
        FROM ejercicios
        ORDER BY id DESC
    """)


    filas = cursor.fetchall()


    cursor.close()

    conn.close()


    return jsonify([
        {
            "id":
                fila["id"],

            "nombre":
                fila["nombre"],

            "pseudocodigo":
                fila["pseudocodigo"],

            "fecha":
                str(
                    fila["fecha"]
                )
        }

        for fila in filas
    ])




@app.route(
    "/api/ejercicios",
    methods=["POST"]
)
def crear_ejercicio():

    datos = request.get_json(
        silent=True
    ) or {}


    nombre = datos.get(
        "nombre",
        "Ejercicio"
    )


    pseudocodigo = datos.get(
        "pseudocodigo",
        ""
    )


    conn = get_db()

    cursor = conn.cursor()


    if USAR_POSTGRES:

        cursor.execute(
            """
            INSERT INTO ejercicios
            (nombre, pseudocodigo)
            VALUES (%s, %s)
            RETURNING id
            """,
            (
                nombre,
                pseudocodigo
            )
        )


        fila = cursor.fetchone()

        nuevo_id = fila[
            "id"
        ]


    else:

        cursor.execute(
            """
            INSERT INTO ejercicios
            (nombre, pseudocodigo)
            VALUES (?, ?)
            """,
            (
                nombre,
                pseudocodigo
            )
        )


        nuevo_id = cursor.lastrowid


    conn.commit()

    cursor.close()

    conn.close()


    return jsonify({
        "ok": True,
        "id": nuevo_id
    })


@app.route(
    "/api/ejercicios/<int:id>",
    methods=["PUT"]
)
def actualizar_ejercicio(id):

    datos = request.get_json(
        silent=True
    ) or {}


    nombre = datos.get(
        "nombre",
        "Ejercicio"
    )


    pseudocodigo = datos.get(
        "pseudocodigo",
        ""
    )


    conn = get_db()

    cursor = conn.cursor()


    if USAR_POSTGRES:

        cursor.execute(
            """
            UPDATE ejercicios
            SET
                nombre = %s,
                pseudocodigo = %s
            WHERE id = %s
            """,
            (
                nombre,
                pseudocodigo,
                id
            )
        )


    else:

        cursor.execute(
            """
            UPDATE ejercicios
            SET
                nombre = ?,
                pseudocodigo = ?
            WHERE id = ?
            """,
            (
                nombre,
                pseudocodigo,
                id
            )
        )


    conn.commit()

    cursor.close()

    conn.close()


    return jsonify({
        "ok": True
    })



@app.route(
    "/api/ejercicios/<int:id>",
    methods=["DELETE"]
)
def eliminar_ejercicio(id):

    conn = get_db()

    cursor = conn.cursor()


    if USAR_POSTGRES:

        cursor.execute(
            """
            DELETE FROM ejercicios
            WHERE id = %s
            """,
            (id,)
        )


    else:

        cursor.execute(
            """
            DELETE FROM ejercicios
            WHERE id = ?
            """,
            (id,)
        )


    conn.commit()

    cursor.close()

    conn.close()


    return jsonify({
        "ok": True
    })



@app.route(
    "/api/entradas",
    methods=["POST"]
)
def entradas():

    datos = request.get_json(
        silent=True
    ) or {}


    variables = detectar_variables_entrada(
        datos.get(
            "pseudocodigo",
            ""
        )
    )


    return jsonify({
        "variables":
            variables
    })



@app.route(
    "/api/ejecutar",
    methods=["POST"]
)
def ejecutar():

    datos = request.get_json(
        silent=True
    ) or {}


    try:

        resultado = ejecutar_pseudocodigo(
            datos.get(
                "pseudocodigo",
                ""
            ),
            datos.get(
                "entradas",
                {}
            )
        )


        return jsonify({
            "ok":
                True,

            "salidas":
                resultado[
                    "salidas"
                ],

            "tabla":
                resultado[
                    "tabla"
                ],

            "variables":
                resultado[
                    "variables"
                ],

            "entradas":
                datos.get(
                    "entradas",
                    {}
                )
        })


    except Exception as error:

        return jsonify({
            "ok": False,
            "error": str(
                error
            )
        }), 400




@app.route(
    "/api/diagrama",
    methods=["POST"]
)
def diagrama():

    datos = request.get_json(
        silent=True
    ) or {}


    try:

        codigo = generar_diagrama(
            datos.get(
                "pseudocodigo",
                ""
            )
        )


        return jsonify({
            "ok": True,
            "mermaid": codigo
        })


    except Exception as error:

        return jsonify({
            "ok": False,
            "error": str(
                error
            )
        }), 400



@app.route("/")
def index():

    return render_template(
        "index.html"
    )



init_db()



def abrir_navegador():

    webbrowser.open(
        "http://127.0.0.1:5000"
    )


if __name__ == "__main__":

    threading.Timer(
        1.5,
        abrir_navegador
    ).start()


    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )