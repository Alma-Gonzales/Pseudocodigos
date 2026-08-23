from flask import Flask, request, jsonify, render_template
import sqlite3
import re
import os
import webbrowser
import threading


# ============================================================
# CONFIGURACIÓN
# ============================================================

app = Flask(__name__)


# ============================================================
# RUTAS LOCALES
# ============================================================

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
# DATABASE_URL
#
# Si existe:
#     usamos Supabase PostgreSQL
#
# Si NO existe:
#     usamos SQLite local
# ============================================================

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    ""
).strip()

USAR_POSTGRES = bool(
    DATABASE_URL
)


# ============================================================
# CONEXIÓN A BASE DE DATOS
# ============================================================

def get_db():

    # ========================================================
    # POSTGRESQL / SUPABASE
    # ========================================================

    if USAR_POSTGRES:

        import psycopg

        from psycopg.rows import dict_row

        conn = psycopg.connect(
            DATABASE_URL,
            row_factory=dict_row
        )

        return conn


    # ========================================================
    # SQLITE LOCAL
    # ========================================================

    conn = sqlite3.connect(
        SQLITE_DB
    )

    conn.row_factory = sqlite3.Row

    return conn


# ============================================================
# INICIALIZAR BASE DE DATOS
# ============================================================

def init_db():

    conn = get_db()

    cursor = conn.cursor()


    # ========================================================
    # SUPABASE / POSTGRESQL
    # ========================================================

    if USAR_POSTGRES:

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ejercicios (
                id BIGSERIAL PRIMARY KEY,
                nombre TEXT NOT NULL,
                pseudocodigo TEXT NOT NULL,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


    # ========================================================
    # SQLITE
    # ========================================================

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


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

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


# ============================================================
# NORMALIZAR OPERADORES
# ============================================================

def normalizar_operadores(texto):

    # Diferente
    texto = texto.replace(
        "<>",
        "!="
    )


    # Y lógico
    texto = re.sub(
        r"\bY\b",
        " and ",
        texto,
        flags=re.IGNORECASE
    )


    # O lógico
    texto = re.sub(
        r"\bO\b",
        " or ",
        texto,
        flags=re.IGNORECASE
    )


    # NO lógico
    texto = re.sub(
        r"\bNO\b",
        " not ",
        texto,
        flags=re.IGNORECASE
    )


    # Potencia
    texto = texto.replace(
        "^",
        "**"
    )


    # Verdadero
    texto = re.sub(
        r"\bVerdadero\b",
        "True",
        texto,
        flags=re.IGNORECASE
    )


    # Falso
    texto = re.sub(
        r"\bFalso\b",
        "False",
        texto,
        flags=re.IGNORECASE
    )


    # Igualdad
    texto = re.sub(
        r"(?<![<>=!])=(?!=)",
        "==",
        texto
    )


    return texto


# ============================================================
# DETECTAR VARIABLES DE LEER
# ============================================================

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

            contenido = (
                coincidencia.group(1)
            )


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


# ============================================================
# CONVERTIR VALOR
# ============================================================

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


    # Entero
    try:

        return int(
            valor
        )

    except ValueError:

        pass


    # Decimal
    try:

        return float(
            valor
        )

    except ValueError:

        pass


    # Texto
    return valor


# ============================================================
# EVALUAR EXPRESIONES
# ============================================================

def evaluar_expresion(
    expresion,
    variables
):

    expresion = expresion.strip()


    # ========================================================
    # TEXTO
    # ========================================================

    if (
        len(expresion) >= 2
        and expresion[0] == '"'
        and expresion[-1] == '"'
    ):

        return expresion[1:-1]


    # ========================================================
    # SUSTITUIR VARIABLES PRIMERO
    #
    # Esto evita que una variable llamada "y"
    # sea confundida con el operador lógico Y.
    # ========================================================

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


    # ========================================================
    # OPERADORES
    # ========================================================

    expresion = normalizar_operadores(
        expresion
    )


    # ========================================================
    # RAÍZ CUADRADA
    # ========================================================

    expresion = re.sub(
        r"\bRC\((.*?)\)",
        r"(\1 ** 0.5)",
        expresion,
        flags=re.IGNORECASE
    )


    # ========================================================
    # VALIDACIÓN
    # ========================================================

    permitidos = re.fullmatch(
        r"[0-9A-Za-z_+\-*/().%, '<>=!&|]*",
        expresion
    )


    if not permitidos:

        return expresion


    # ========================================================
    # EVALUAR
    # ========================================================

    try:

        return eval(
            expresion,
            {
                "__builtins__": {}
            }
        )


    except Exception:

        return expresion


# ============================================================
# EVALUAR CONDICIONES
# ============================================================

def evaluar_condicion(
    condicion,
    variables
):

    condicion = condicion.strip()


    # ========================================================
    # SUSTITUIR VARIABLES PRIMERO
    # ========================================================

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


    # ========================================================
    # OPERADORES
    # ========================================================

    condicion = normalizar_operadores(
        condicion
    )


    # ========================================================
    # EVALUAR
    # ========================================================

    try:

        resultado = eval(
            condicion,
            {
                "__builtins__": {}
            }
        )


        return bool(
            resultado
        )


    except Exception:

        return False


# ============================================================
# DIVIDIR ESCRIBIR
# ============================================================

def dividir_escribir(
    contenido
):

    partes = []

    actual = ""

    dentro_comillas = False


    for caracter in contenido:

        if caracter == '"':

            dentro_comillas = (
                not dentro_comillas
            )

            actual += caracter


        elif (
            caracter == ","
            and not dentro_comillas
        ):

            partes.append(
                actual.strip()
            )

            actual = ""


        else:

            actual += caracter


    if actual.strip():

        partes.append(
            actual.strip()
        )


    return partes


# ============================================================
# EJECUTOR DE PSEUDOCÓDIGO
# ============================================================

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


    # ========================================================
    # EJECUTAR BLOQUE
    # ========================================================

    def ejecutar_bloque(
        self,
        inicio,
        fin
    ):

        i = inicio


        while i < fin:

            linea = self.lineas[i]

            mayus = linea.upper()


            # =================================================
            # ALGORITMO
            # =================================================

            if mayus.startswith(
                "ALGORITMO"
            ):

                i += 1

                continue


            # =================================================
            # FINALGORITMO
            # =================================================

            if mayus == "FINALGORITMO":

                i += 1

                continue


            # =================================================
            # DEFINIR
            # =================================================

            if mayus.startswith(
                "DEFINIR"
            ):

                i += 1

                continue


            # =================================================
            # LEER
            # =================================================

            coincidencia = re.match(
                r"^Leer\s+(.+)$",
                linea,
                flags=re.IGNORECASE
            )


            if coincidencia:

                contenido = (
                    coincidencia.group(1)
                )


                for variable in contenido.split(","):

                    variable = variable.strip()


                    if variable not in self.variables:

                        self.variables[
                            variable
                        ] = ""


                i += 1

                continue


            # =================================================
            # ESCRIBIR
            # =================================================

            coincidencia = re.match(
                r"^Escribir\s*(.*)$",
                linea,
                flags=re.IGNORECASE
            )


            if coincidencia:

                contenido = (
                    coincidencia.group(1)
                )


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


            # =================================================
            # ASIGNACIÓN
            # =================================================

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


            # =================================================
            # SI
            # =================================================

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


            # =================================================
            # PARA
            # =================================================

            coincidencia = re.match(
                r"^Para\s+(\w+)\s*<-\s*(.+?)\s+Hasta\s+(.+?)(?:\s+Con\s+Paso\s+(.+?))?\s+Hacer$",
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


            # =================================================
            # MIENTRAS
            # =================================================

            coincidencia = re.match(
                r"^Mientras\s+(.+?)\s+Hacer$",
                linea,
                flags=re.IGNORECASE
            )


            if coincidencia:

                condicion = coincidencia.group(1)


                fin_mientras = (
                    self.buscar_fin_mientras(i)
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


            # =================================================
            # REPETIR
            # =================================================

            if mayus == "REPETIR":

                fin_repetir = (
                    self.buscar_hasta_que(i)
                )


                contador_seguridad = 0


                while True:

                    self.ejecutar_bloque(
                        i + 1,
                        fin_repetir
                    )


                    condicion_linea = (
                        self.lineas[
                            fin_repetir
                        ]
                    )


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


    # ========================================================
    # BUSCAR FIN SI
    # ========================================================

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

            mayus = self.lineas[i].upper()


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


    # ========================================================
    # BUSCAR FIN PARA
    # ========================================================

    def buscar_fin_para(
        self,
        posicion
    ):

        profundidad = 0


        for i in range(
            posicion + 1,
            len(self.lineas)
        ):

            mayus = self.lineas[i].upper()


            if mayus.startswith(
                "PARA "
            ):

                profundidad += 1


            if mayus == "FINPARA":

                if profundidad == 0:

                    return i


                profundidad -= 1


        return len(self.lineas) - 1


    # ========================================================
    # BUSCAR FIN MIENTRAS
    # ========================================================

    def buscar_fin_mientras(
        self,
        posicion
    ):

        profundidad = 0


        for i in range(
            posicion + 1,
            len(self.lineas)
        ):

            mayus = self.lineas[i].upper()


            if mayus.startswith(
                "MIENTRAS "
            ):

                profundidad += 1


            if mayus == "FINMIENTRAS":

                if profundidad == 0:

                    return i


                profundidad -= 1


        return len(self.lineas) - 1


    # ========================================================
    # BUSCAR HASTA QUE
    # ========================================================

    def buscar_hasta_que(
        self,
        posicion
    ):

        for i in range(
            posicion + 1,
            len(self.lineas)
        ):

            if self.lineas[i].upper().startswith(
                "HASTA QUE"
            ):

                return i


        return len(self.lineas) - 1


# ============================================================
# EJECUTAR PSEUDOCÓDIGO
# ============================================================

def ejecutar_pseudocodigo(
    pseudocodigo,
    entradas
):

    ejecutor = Ejecutor(
        pseudocodigo,
        entradas
    )


    return {
        "salidas": ejecutor.salidas,
        "tabla": ejecutor.tabla_filas,
        "variables": ejecutor.variables
    }


# ============================================================
# ESCAPAR TEXTO PARA MERMAID
# ============================================================

def escapar_mermaid(
    texto
):

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


# ============================================================
# GENERAR DIAGRAMA
# ============================================================

def generar_diagrama(
    pseudocodigo
):

    lineas = pseudocodigo.splitlines()

    mermaid = []


    mermaid.append(
        "flowchart TD"
    )


    # ========================================================
    # COLORES
    # ========================================================

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


    contador = 0


    mermaid.append(
        'inicio(["INICIO"]):::inicio'
    )


    anterior = "inicio"

    pila = []


    for linea in lineas:

        linea = quitar_comentarios(
            linea
        ).strip()


        if not linea:

            continue


        mayus = linea.upper()


        # ====================================================
        # ALGORITMO
        # ====================================================

        if mayus.startswith(
            "ALGORITMO"
        ):

            continue


        # ====================================================
        # FINALGORITMO
        # ====================================================

        if mayus == "FINALGORITMO":

            continue


        # ====================================================
        # DEFINIR
        # ====================================================

        if mayus.startswith(
            "DEFINIR"
        ):

            continue


        # ====================================================
        # LEER
        # ====================================================

        if mayus.startswith(
            "LEER "
        ):

            variable = linea[5:].strip()

            contador += 1

            nodo = f"n{contador}"


            texto = escapar_mermaid(
                f"LEER<br/>{variable}"
            )


            mermaid.append(
                f'{nodo}["{texto}"]:::leer'
            )


            mermaid.append(
                f"{anterior} --> {nodo}"
            )


            anterior = nodo

            continue


        # ====================================================
        # ESCRIBIR
        # ====================================================

        if mayus.startswith(
            "ESCRIBIR"
        ):

            texto = linea[8:].strip()

            texto = escapar_mermaid(
                f"ESCRIBIR<br/>{texto}"
            )


            contador += 1

            nodo = f"n{contador}"


            mermaid.append(
                f'{nodo}["{texto}"]:::escribir'
            )


            mermaid.append(
                f"{anterior} --> {nodo}"
            )


            anterior = nodo

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

            condicion = coincidencia.group(1)

            condicion = escapar_mermaid(
                condicion
            )


            contador += 1

            nodo = f"n{contador}"


            mermaid.append(
                f'{nodo}{{"{condicion}"}}:::decision'
            )


            mermaid.append(
                f"{anterior} --> {nodo}"
            )


            pila.append({
                "tipo": "si",
                "nodo": nodo,
                "salida_no": None
            })


            anterior = nodo

            continue


        # ====================================================
        # SINO
        # ====================================================

        if mayus in (
            "SINO",
            "SI NO"
        ):

            if pila:

                actual = pila[-1]

                decision = actual[
                    "nodo"
                ]


                contador += 1

                nodo = f"n{contador}"


                mermaid.append(
                    f'{nodo}["NO"]:::decision'
                )


                mermaid.append(
                    f"{decision} -->|NO| {nodo}"
                )


                actual[
                    "salida_no"
                ] = nodo


                anterior = nodo


            continue


        # ====================================================
        # FIN SI
        # ====================================================

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
                    "salida_no"
                ] is None:

                    mermaid.append(
                        f"{decision} -->|SÍ| {anterior}"
                    )


                else:

                    contador += 1

                    union = f"n{contador}"


                    mermaid.append(
                        f'{union}(( )):::decision'
                    )


                    mermaid.append(
                        f"{decision} -->|SÍ| {union}"
                    )


                    mermaid.append(
                        f"{anterior} --> {union}"
                    )


                    anterior = union


            continue


        # ====================================================
        # PARA
        # ====================================================

        coincidencia = re.match(
            r"^Para\s+(\w+)",
            linea,
            flags=re.IGNORECASE
        )


        if coincidencia:

            variable = coincidencia.group(1)

            contador += 1

            nodo = f"n{contador}"


            mermaid.append(
                f'{nodo}{{"PARA<br/>{variable}"}}:::para'
            )


            mermaid.append(
                f"{anterior} --> {nodo}"
            )


            anterior = nodo

            continue


        # ====================================================
        # MIENTRAS
        # ====================================================

        if mayus.startswith(
            "MIENTRAS "
        ):

            condicion = linea[9:].strip()


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


            mermaid.append(
                f"{anterior} --> {nodo}"
            )


            anterior = nodo

            continue


        # ====================================================
        # REPETIR
        # ====================================================

        if mayus == "REPETIR":

            contador += 1

            nodo = f"n{contador}"


            mermaid.append(
                f'{nodo}{{"REPETIR"}}:::repetir'
            )


            mermaid.append(
                f"{anterior} --> {nodo}"
            )


            anterior = nodo

            continue


        # ====================================================
        # ASIGNACIÓN
        # ====================================================

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


            mermaid.append(
                f"{anterior} --> {nodo}"
            )


            anterior = nodo

            continue


    # ========================================================
    # FIN
    # ========================================================

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


# ============================================================
# API EJERCICIOS - OBTENER
# ============================================================

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
            "id": f["id"],
            "nombre": f["nombre"],
            "pseudocodigo": f["pseudocodigo"],
            "fecha": str(
                f["fecha"]
            )
        }

        for f in filas
    ])


# ============================================================
# API EJERCICIOS - CREAR
# ============================================================

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


    # ========================================================
    # POSTGRES
    # ========================================================

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


    # ========================================================
    # SQLITE
    # ========================================================

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


        nuevo_id = (
            cursor.lastrowid
        )


    conn.commit()


    cursor.close()

    conn.close()


    return jsonify({
        "ok": True,
        "id": nuevo_id
    })


# ============================================================
# API EJERCICIOS - ACTUALIZAR
# ============================================================

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


# ============================================================
# API EJERCICIOS - ELIMINAR
# ============================================================

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


# ============================================================
# API ENTRADAS
# ============================================================

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
        "variables": variables
    })


# ============================================================
# API EJECUTAR
# ============================================================

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
            "ok": True,

            "salidas":
                resultado["salidas"],

            "tabla":
                resultado["tabla"],

            "variables":
                resultado["variables"],

            "entradas":
                datos.get(
                    "entradas",
                    {}
                )
        })


    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400


# ============================================================
# API DIAGRAMA
# ============================================================

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


    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400


# ============================================================
# PÁGINA PRINCIPAL
# ============================================================

@app.route("/")
def index():

    return render_template(
        "index.html"
    )


# ============================================================
# INICIALIZAR TABLAS
#
# IMPORTANTE:
# Esto también se ejecuta cuando Gunicorn importa app.py
# en Render.
# ============================================================

init_db()


# ============================================================
# ABRIR NAVEGADOR LOCAL
# ============================================================

def abrir_navegador():

    webbrowser.open(
        "http://127.0.0.1:5000"
    )


# ============================================================
# EJECUTAR LOCALMENTE
# ============================================================

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