// ============================================================
// GENERADOR DE CÓDIGO PYTHON / C++
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
        // MOSTRAR CÓDIGO
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
        // BOTÓN PYTHON
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


        // ====================================================
        // BOTÓN C++
        // ====================================================

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


        // ====================================================
        // GENERAR
        // ====================================================

        async function generarCodigo() {

            const pseudocodigo =
                editor.value.trim();


            if (!pseudocodigo) {

                codigoPython = "";

                codigoCpp = "";

                mostrarCodigo();

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
                                        pseudocodigo
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


        // ====================================================
        // GENERAR AUTOMÁTICAMENTE AL ESCRIBIR
        // ====================================================

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


        // ====================================================
        // ACTUALIZAR CUANDO SE PULSE GENERAR DIAGRAMA
        // ====================================================

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


        // ====================================================
        // ACTUALIZAR CUANDO SE PULSE EJECUTAR
        // ====================================================

        const btnEjecutar =
            document.getElementById(
                "btnEjecutar"
            );


        if (btnEjecutar) {

            btnEjecutar.addEventListener(
                "click",
                generarCodigo
            );
        }

    }
);