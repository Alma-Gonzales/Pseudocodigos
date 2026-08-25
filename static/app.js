// ============================================================
// Este JS permite que se ejecuten las instrucciones del app.py
// Es lo que permite la interacción entre el usuario y la interfaz
// ============================================================

let ejercicioActualId = null;


const pseudocodigo =
    document.getElementById("pseudocodigo");

const nombreEjercicio =
    document.getElementById("nombreEjercicio");

const entradas =
    document.getElementById("entradas");

const resultados =
    document.getElementById("resultados");

const diagrama =
    document.getElementById("diagrama");

const listaEjercicios =
    document.getElementById("listaEjercicios");


mermaid.initialize({
    startOnLoad: false,
    securityLevel: "loose",
    theme: "default"
});


document.addEventListener(
    "DOMContentLoaded",
    function () {

        nuevoEjercicio();

        cargarEjercicios();

    }
);

function nuevoEjercicio() {

    ejercicioActualId = null;

    nombreEjercicio.value = "";

    pseudocodigo.value = "";

    entradas.innerHTML = `
        <div class="empty">
            No hay variables de entrada.
        </div>
    `;

    resultados.innerHTML = `
        <div class="empty">
            Ejecuta el algoritmo para ver los resultados.
        </div>
    `;

    diagrama.innerHTML = `
        <div class="empty">
            El diagrama aparecerá aquí.
        </div>
    `;
}

async function detectarEntradas() {

    const codigo =
        pseudocodigo.value;

    if (!codigo.trim()) {

        entradas.innerHTML = `
            <div class="empty">
                No hay variables de entrada.
            </div>
        `;

        return [];
    }


    const valoresAnteriores =
        obtenerValoresEntrada();


    try {

        const respuesta =
            await fetch(
                "/api/entradas",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        pseudocodigo:
                            codigo
                    })
                }
            );


        if (!respuesta.ok) {

            throw new Error(
                "No se pudieron detectar las variables."
            );
        }


        const datos =
            await respuesta.json();


        const esquema =
            (
                datos.variables ||
                []
            ).map(
                function (variable) {

                    return {
                        variable:
                            variable,

                        cantidad:
                            1
                    };

                }
            );


        mostrarEsquemaEntradas(
            esquema,
            valoresAnteriores
        );


        return datos.variables || [];


    } catch (error) {

        console.error(
            error
        );

        return [];
    }
}

function mostrarEsquemaEntradas(
    esquema,
    valoresAnteriores = {}
) {

    if (
        !esquema ||
        esquema.length === 0
    ) {

        entradas.innerHTML = `
            <div class="empty">
                No hay variables de entrada.
            </div>
        `;

        return;
    }


    entradas.innerHTML = "";


    esquema.forEach(
        function (item) {

            const variable =
                item.variable;

            const cantidad =
                Math.max(
                    1,
                    Number(
                        item.cantidad
                    ) || 1
                );


            let anteriores =
                valoresAnteriores[
                    variable
                ];


            if (
                anteriores === undefined
                ||
                anteriores === null
            ) {

                anteriores = [];

            }

            else if (
                !Array.isArray(
                    anteriores
                )
            ) {

                anteriores = [
                    anteriores
                ];
            }


            for (
                let indice = 0;
                indice < cantidad;
                indice++
            ) {

                const fila =
                    document.createElement(
                        "div"
                    );


                fila.className =
                    "input-row";


                const label =
                    document.createElement(
                        "label"
                    );


                if (
                    cantidad > 1
                ) {

                    label.textContent =
                        variable
                        + " "
                        + (
                            indice + 1
                        );

                } else {

                    label.textContent =
                        variable;
                }


                const input =
                    document.createElement(
                        "input"
                    );


                input.type =
                    "text";


                input.dataset.variable =
                    variable;


                input.dataset.indice =
                    String(
                        indice
                    );


                if (
                    cantidad > 1
                ) {

                    input.placeholder =
                        "Valor "
                        + (
                            indice + 1
                        );

                } else {

                    input.placeholder =
                        "Valor";
                }


                if (
                    indice
                    < anteriores.length
                ) {

                    input.value =
                        anteriores[
                            indice
                        ] ?? "";
                }


                fila.appendChild(
                    label
                );


                fila.appendChild(
                    input
                );


                entradas.appendChild(
                    fila
                );
            }
        }
    );
}

function obtenerValoresEntrada() {

    const grupos = {};


    const inputs =
        entradas.querySelectorAll(
            "input[data-variable]"
        );


    inputs.forEach(
        function (input) {

            const variable =
                input.dataset.variable;


            if (
                !grupos[
                    variable
                ]
            ) {

                grupos[
                    variable
                ] = [];
            }


            grupos[
                variable
            ].push(
                input.value
            );

        }
    );


    const valores = {};


    Object.entries(
        grupos
    ).forEach(
        function (
            [
                variable,
                lista
            ]
        ) {

            if (
                lista.length === 1
            ) {

                valores[
                    variable
                ] = lista[0];

            } else {

                valores[
                    variable
                ] = lista;
            }

        }
    );


    return valores;
}

function obtenerCantidadesActuales() {

    const cantidades = {};


    const inputs =
        entradas.querySelectorAll(
            "input[data-variable]"
        );


    inputs.forEach(
        function (input) {

            const variable =
                input.dataset.variable;


            cantidades[
                variable
            ] =
                (
                    cantidades[
                        variable
                    ] || 0
                )
                + 1;

        }
    );


    return cantidades;
}

function esquemaCambio(
    esquema
) {

    const actuales =
        obtenerCantidadesActuales();


    for (
        const item
        of esquema
    ) {

        const cantidad =
            Math.max(
                1,
                Number(
                    item.cantidad
                ) || 1
            );


        if (
            (
                actuales[
                    item.variable
                ] || 0
            )
            !== cantidad
        ) {

            return true;
        }
    }


    const variablesEsquema =
        esquema.map(
            function (item) {

                return item.variable;
            }
        );


    for (
        const variable
        of Object.keys(
            actuales
        )
    ) {

        if (
            !variablesEsquema.includes(
                variable
            )
        ) {

            return true;
        }
    }


    return false;
}

async function prepararEntradasRepetidas() {

    const codigo =
        pseudocodigo.value.trim();


    const valores =
        obtenerValoresEntrada();


    try {

        const respuesta =
            await fetch(
                "/api/preparar_entradas",
                {
                    method:
                        "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            pseudocodigo:
                                codigo,

                            entradas:
                                valores
                        })
                }
            );


        const datos =
            await respuesta.json();


        if (
            !respuesta.ok
            ||
            !datos.ok
        ) {

            throw new Error(
                datos.error
                ||
                "No se pudieron preparar las entradas."
            );
        }


        const esquema =
            datos.esquema || [];


        if (
            esquemaCambio(
                esquema
            )
        ) {

            mostrarEsquemaEntradas(
                esquema,
                valores
            );


            resultados.innerHTML = `
                <div class="empty">
                    Se detectaron entradas repetidas.
                    Completa todos los valores solicitados
                    y vuelve a presionar Ejecutar.
                </div>
            `;


            return false;
        }


        return true;


    } catch (error) {

        console.error(
            error
        );


        resultados.innerHTML = `
            <div class="result-line error">
                Error:
                ${escapeHtml(
                    error.message
                )}
            </div>
        `;


        return false;
    }
}

function existenEntradasVacias() {

    const inputs =
        entradas.querySelectorAll(
            "input[data-variable]"
        );


    for (
        const input
        of inputs
    ) {

        if (
            input.value.trim() === ""
        ) {

            input.focus();

            return true;
        }
    }


    return false;
}

async function ejecutarAlgoritmo() {

    const codigo =
        pseudocodigo.value.trim();


    if (!codigo) {

        alert(
            "Primero escribe un pseudocódigo."
        );

        return;
    }


    const inputsExistentes =
        entradas.querySelectorAll(
            "input[data-variable]"
        );


    if (
        inputsExistentes.length === 0
    ) {

        await detectarEntradas();
    }

    const listo =
        await prepararEntradasRepetidas();


    if (!listo) {

        return;
    }

    if (
        existenEntradasVacias()
    ) {

        alert(
            "Completa todos los valores de entrada."
        );

        return;
    }


    const valores =
        obtenerValoresEntrada();


    resultados.innerHTML = `
        <div class="empty">
            Ejecutando algoritmo...
        </div>
    `;


    try {

        const respuesta =
            await fetch(
                "/api/ejecutar",
                {
                    method:
                        "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            pseudocodigo:
                                codigo,

                            entradas:
                                valores
                        })
                }
            );


        const datos =
            await respuesta.json();


        if (
            !respuesta.ok
            ||
            !datos.ok
        ) {

            throw new Error(
                datos.error
                ||
                "No se pudo ejecutar el algoritmo."
            );
        }


        mostrarResultados(
            datos
        );


    } catch (error) {

        console.error(
            error
        );


        resultados.innerHTML = `
            <div class="result-line error">
                Error:
                ${escapeHtml(
                    error.message
                )}
            </div>
        `;
    }
}

function mostrarResultados(
    datos
) {

    let html = "";


    html += `
        <div class="output-title">
            Salida
        </div>
    `;


    if (
        datos.salidas
        &&
        datos.salidas.length > 0
    ) {

        datos.salidas.forEach(
            function (salida) {

                const texto =
                    String(
                        salida
                    );


                html += `
                    <div class="result-line">
                        ${escapeHtml(
                            texto
                        )}
                    </div>
                `;

            }
        );

    } else {

        html += `
            <div class="empty">
                El algoritmo no produjo salida.
            </div>
        `;
    }


    if (
        datos.variables
    ) {

        const variables =
            Object.entries(
                datos.variables
            );


        if (
            variables.length > 0
        ) {

            html += `
                <div class="variables">

                    <strong>
                        Variables
                    </strong>
            `;


            variables.forEach(
                function (
                    [
                        nombre,
                        valor
                    ]
                ) {

                    html += `
                        <div class="variable">

                            <span>
                                ${escapeHtml(
                                    nombre
                                )}
                            </span>

                            <span>
                                ${escapeHtml(
                                    String(
                                        valor
                                    )
                                )}
                            </span>

                        </div>
                    `;

                }
            );


            html += `
                </div>
            `;
        }
    }


    resultados.innerHTML =
        html;
}

async function generarDiagrama() {

    const codigo =
        pseudocodigo.value.trim();


    if (!codigo) {

        alert(
            "Primero escribe un pseudocódigo."
        );

        return;
    }


    diagrama.innerHTML = `
        <div class="empty">
            Generando diagrama...
        </div>
    `;


    try {

        const respuesta =
            await fetch(
                "/api/diagrama",
                {
                    method:
                        "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            pseudocodigo:
                                codigo
                        })
                }
            );


        const datos =
            await respuesta.json();


        if (
            !respuesta.ok
            ||
            !datos.ok
        ) {

            throw new Error(
                datos.error
                ||
                "No se pudo generar el diagrama."
            );
        }


        diagrama.innerHTML = `
            <div class="mermaid">
                ${escapeHtmlMermaid(
                    datos.mermaid
                )}
            </div>
        `;


        await mermaid.run({
            nodes:
                diagrama.querySelectorAll(
                    ".mermaid"
                )
        });


    } catch (error) {

        console.error(
            error
        );


        diagrama.innerHTML = `
            <div class="empty">
                Error al generar el diagrama:
                ${escapeHtml(
                    error.message
                )}
            </div>
        `;
    }
}

async function guardarEjercicio() {

    const codigo =
        pseudocodigo.value.trim();


    if (!codigo) {

        alert(
            "No puedes guardar un ejercicio vacío."
        );

        return;
    }


    let nombre =
        nombreEjercicio.value.trim();


    if (!nombre) {

        nombre =
            "Ejercicio";


        nombreEjercicio.value =
            nombre;
    }


    const datos = {

        nombre:
            nombre,

        pseudocodigo:
            codigo

    };


    try {

        let respuesta;


        if (
            ejercicioActualId
        ) {

            respuesta =
                await fetch(
                    `/api/ejercicios/${ejercicioActualId}`,
                    {
                        method:
                            "PUT",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body:
                            JSON.stringify(
                                datos
                            )
                    }
                );

        } else {

            respuesta =
                await fetch(
                    "/api/ejercicios",
                    {
                        method:
                            "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body:
                            JSON.stringify(
                                datos
                            )
                    }
                );
        }


        const resultado =
            await respuesta.json();


        if (
            !respuesta.ok
            ||
            !resultado.ok
        ) {

            throw new Error(
                resultado.error
                ||
                "No se pudo guardar."
            );
        }


        if (
            !ejercicioActualId
        ) {

            ejercicioActualId =
                resultado.id;
        }


        await cargarEjercicios();


        alert(
            "Ejercicio guardado correctamente."
        );


    } catch (error) {

        console.error(
            error
        );


        alert(
            "Error al guardar: "
            + error.message
        );
    }
}

async function cargarEjercicios() {

    try {

        const respuesta =
            await fetch(
                "/api/ejercicios"
            );


        if (
            !respuesta.ok
        ) {

            throw new Error(
                "No se pudieron cargar los ejercicios."
            );
        }


        const ejercicios =
            await respuesta.json();


        mostrarEjercicios(
            ejercicios
        );


    } catch (error) {

        console.error(
            error
        );
    }
}


function mostrarEjercicios(
    ejercicios
) {

    if (
        !ejercicios.length
    ) {

        listaEjercicios.innerHTML = `
            <div class="empty">
                No hay ejercicios guardados.
            </div>
        `;

        return;
    }


    listaEjercicios.innerHTML =
        "";


    ejercicios.forEach(
        function (ejercicio) {

            const item =
                document.createElement(
                    "div"
                );


            item.className =
                "exercise-item";


            const info =
                document.createElement(
                    "div"
                );


            info.className =
                "exercise-info";


            const nombre =
                document.createElement(
                    "div"
                );


            nombre.className =
                "exercise-name";


            nombre.textContent =
                ejercicio.nombre;


            const fecha =
                document.createElement(
                    "div"
                );


            fecha.className =
                "exercise-date";


            fecha.textContent =
                ejercicio.fecha || "";


            info.appendChild(
                nombre
            );


            info.appendChild(
                fecha
            );


            const acciones =
                document.createElement(
                    "div"
                );


            acciones.className =
                "exercise-actions";


            const abrir =
                document.createElement(
                    "button"
                );


            abrir.className =
                "small-btn load-btn";


            abrir.textContent =
                "Abrir";


            abrir.addEventListener(
                "click",
                function () {

                    cargarEjercicio(
                        ejercicio
                    );
                }
            );


            const eliminar =
                document.createElement(
                    "button"
                );


            eliminar.className =
                "small-btn delete-btn";


            eliminar.textContent =
                "Eliminar";


            eliminar.addEventListener(
                "click",
                function () {

                    eliminarEjercicio(
                        ejercicio.id
                    );
                }
            );


            acciones.appendChild(
                abrir
            );


            acciones.appendChild(
                eliminar
            );


            item.appendChild(
                info
            );


            item.appendChild(
                acciones
            );


            listaEjercicios.appendChild(
                item
            );

        }
    );
}


function cargarEjercicio(
    ejercicio
) {

    ejercicioActualId =
        ejercicio.id;


    nombreEjercicio.value =
        ejercicio.nombre;


    pseudocodigo.value =
        ejercicio.pseudocodigo;


    resultados.innerHTML = `
        <div class="empty">
            Ejecuta el algoritmo para ver los resultados.
        </div>
    `;


    diagrama.innerHTML = `
        <div class="empty">
            El diagrama aparecerá aquí.
        </div>
    `;


    detectarEntradas();
}


async function eliminarEjercicio(
    id
) {

    const confirmar =
        confirm(
            "¿Seguro que deseas eliminar este ejercicio?"
        );


    if (
        !confirmar
    ) {

        return;
    }


    try {

        const respuesta =
            await fetch(
                `/api/ejercicios/${id}`,
                {
                    method:
                        "DELETE"
                }
            );


        const datos =
            await respuesta.json();


        if (
            !respuesta.ok
            ||
            !datos.ok
        ) {

            throw new Error(
                datos.error
                ||
                "No se pudo eliminar."
            );
        }


        if (
            ejercicioActualId === id
        ) {

            nuevoEjercicio();
        }


        await cargarEjercicios();


    } catch (error) {

        console.error(
            error
        );


        alert(
            "Error al eliminar: "
            + error.message
        );
    }
}


function limpiarEditor() {

    pseudocodigo.value =
        "";


    entradas.innerHTML = `
        <div class="empty">
            No hay variables de entrada.
        </div>
    `;


    resultados.innerHTML = `
        <div class="empty">
            Ejecuta el algoritmo para ver los resultados.
        </div>
    `;


    diagrama.innerHTML = `
        <div class="empty">
            El diagrama aparecerá aquí.
        </div>
    `;
}



function escapeHtml(
    texto
) {

    return String(
        texto
    )
        .replaceAll(
            "&",
            "&amp;"
        )
        .replaceAll(
            "<",
            "&lt;"
        )
        .replaceAll(
            ">",
            "&gt;"
        )
        .replaceAll(
            '"',
            "&quot;"
        )
        .replaceAll(
            "'",
            "&#039;"
        );
}



function escapeHtmlMermaid(
    texto
) {

    return String(
        texto
    )
        .replaceAll(
            "&",
            "&amp;"
        )
        .replaceAll(
            "<",
            "&lt;"
        )
        .replaceAll(
            ">",
            "&gt;"
        );
}



document
    .getElementById(
        "btnNuevo"
    )
    .addEventListener(
        "click",
        nuevoEjercicio
    );


document
    .getElementById(
        "btnGuardar"
    )
    .addEventListener(
        "click",
        guardarEjercicio
    );


document
    .getElementById(
        "btnEjecutar"
    )
    .addEventListener(
        "click",
        ejecutarAlgoritmo
    );


document
    .getElementById(
        "btnDiagrama"
    )
    .addEventListener(
        "click",
        generarDiagrama
    );


document
    .getElementById(
        "btnLimpiar"
    )
    .addEventListener(
        "click",
        limpiarEditor
    );



pseudocodigo.addEventListener(
    "input",
    function () {

        clearTimeout(
            window.timerEntradas
        );


        window.timerEntradas =
            setTimeout(
                detectarEntradas,
                300
            );
    }
);