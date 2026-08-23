// ============================================================
// Esto permitira que se genere lo que sale en el el Pseudocodigo 
// y lo convierte en codigo de python o C++
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        const editor =
            document.getElementById(
                "pseudocodigo"
            );

        const visor =
            document.getElementById(
                "codigoGenerado"
            );

        const btnPython =
            document.getElementById(
                "btnPython"
            );

        const btnCpp =
            document.getElementById(
                "btnCpp"
            );

        const btnLimpiar =
            document.getElementById(
                "btnLimpiar"
            );


        if (
            !editor ||
            !visor ||
            !btnPython ||
            !btnCpp
        ) {

            return;
        }


        let codigoPython = "";

        let codigoCpp = "";

        let lenguajeActual =
            "python";

        let temporizador = null;


        // ====================================================
        // permite que se muestren los codigos en python o c++
        // en el apartado especifico
        // ====================================================

        function mostrarCodigo() {

            let codigo = "";


            if (
                lenguajeActual ===
                "python"
            ) {

                codigo =
                    codigoPython;

            } else {

                codigo =
                    codigoCpp;
            }


            if (!codigo.trim()) {

                visor.textContent =
                    "El código generado aparecerá aquí.";

                return;
            }


            visor.textContent =
                codigo;
        }


        // ====================================================
        // Este es la funcion que permite que se limpie el codigo
        // realizado y quede vacio de nuevo. 
        // ====================================================

        function limpiarCodigoGenerado() {

            codigoPython = "";

            codigoCpp = "";

            lenguajeActual =
                "python";


            btnPython.classList.add(
                "active"
            );


            btnCpp.classList.remove(
                "active"
            );


            visor.textContent =
                "El código generado aparecerá aquí.";
        }


        // ====================================================
        // Permite que se muestre el codigo en Python o c++
        // ====================================================

        btnPython.addEventListener(
            "click",
            function () {

                lenguajeActual =
                    "python";


                btnPython.classList.add(
                    "active"
                );


                btnCpp.classList.remove(
                    "active"
                );


                mostrarCodigo();
            }
        );


        btnCpp.addEventListener(
            "click",
            function () {

                lenguajeActual =
                    "cpp";


                btnCpp.classList.add(
                    "active"
                );


                btnPython.classList.remove(
                    "active"
                );


                mostrarCodigo();
            }
        );



function obtenerEntradasActuales() {

    const valores = {};

    const contenedorEntradas =
        document.getElementById(
            "entradas"
        );


    if (!contenedorEntradas) {

        return valores;
    }


    const inputs =
        contenedorEntradas.querySelectorAll(
            "input[data-variable]"
        );


    inputs.forEach(
        function (input) {

            const variable =
                input.dataset.variable;


            const valor =
                input.value.trim();


            if (
                variable &&
                valor !== ""
            ) {

                valores[
                    variable
                ] = valor;
            }

        }
    );


    return valores;
}



        async function generarCodigo() {

            const pseudocodigo =
                editor.value.trim();


            if (!pseudocodigo) {

                limpiarCodigoGenerado();

                return;
            }


            try {

                const respuesta =
                    await fetch(
                        "/api/traducir",
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
                                        pseudocodigo,

                                         entradas:
                                          obtenerEntradasActuales()
                                })
                        }
                    );


                const datos =
                    await respuesta.json();


                if (
                    !respuesta.ok ||
                    !datos.ok
                ) {

                    throw new Error(
                        datos.error ||
                        "No se pudo generar el código."
                    );
                }


                codigoPython =
                    datos.python || "";

                codigoCpp =
                    datos.cpp || "";


                mostrarCodigo();


            } catch (error) {

                console.error(
                    error
                );


                visor.textContent =
                    "Error al generar código: "
                    + error.message;
            }
        }


        editor.addEventListener(
            "input",
            function () {

                clearTimeout(
                    temporizador
                );


                temporizador =
                    setTimeout(
                        generarCodigo,
                        500
                    );
            }
        );


        const btnDiagrama =
            document.getElementById(
                "btnDiagrama"
            );


        if (btnDiagrama) {

            btnDiagrama.addEventListener(
                "click",
                generarCodigo
            );
        }


        const btnEjecutar =
            document.getElementById(
                "btnEjecutar"
            );


        if (btnEjecutar) {

    btnEjecutar.addEventListener(
        "click",
        function () {

            setTimeout(
                generarCodigo,
                300
            );

        }
    );
}



        if (btnLimpiar) {

            btnLimpiar.addEventListener(
                "click",
                function () {

                    clearTimeout(
                        temporizador
                    );


                    limpiarCodigoGenerado();

                }
            );
        }

    }
);