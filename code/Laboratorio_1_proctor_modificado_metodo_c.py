"""Script principal del laboratorio Proctor modificado (Metodo C).

Modulos:
- `datos_proctor_laboratorio.py`: ingreso de datos.
- `calculos_proctor.py`: calculos base.
- `validaciones_proctor.py`: chequeos normativos.
- `graficas_proctor.py`: generacion de figuras.
"""

from __future__ import annotations

from pathlib import Path

from calculos_proctor import (
    ResultadoPunto,
    calcular_resultado_punto,
    calcular_volumen_molde_cm3,
    estimar_optimo,
    filtrar_resultados_validos,
)
from datos_proctor_laboratorio import ConfiguracionEnsayo, PuntoCompactacion, cargar_datos_laboratorio
from graficas_proctor import graficar_curva_compactacion
from validaciones_proctor import validar_norma

# Carpeta solicitada para guardar resultados.
CARPETA_RESULTADOS = Path(r"C:\Users\Oscar\Desktop\Code_universidad\Laboratorio Pavimentos")


def tabla_resultados(resultados: list[ResultadoPunto]) -> str:
    """Tabla de salida en texto plano para reporte rapido."""

    encabezado = (
        "Punto | w_obj(%) | w_usada(%) | origen_w | M_humeda_molde(g) | "
        "rho_h(g/cm3) | rho_d(g/cm3) | gamma_h(kN/m3) | gamma_d(kN/m3) | estado"
    )
    lineas = [encabezado, "-" * len(encabezado)]

    for r in resultados:
        w_usada = "-" if r.humedad_usada_pct is None else f"{r.humedad_usada_pct:.2f}"
        mh = "-" if r.masa_suelo_humedo_molde_g is None else f"{r.masa_suelo_humedo_molde_g:.1f}"
        rho_h = "-" if r.densidad_humeda_g_cm3 is None else f"{r.densidad_humeda_g_cm3:.4f}"
        rho_d = "-" if r.densidad_seca_g_cm3 is None else f"{r.densidad_seca_g_cm3:.4f}"
        g_h = "-" if r.peso_unitario_humedo_kn_m3 is None else f"{r.peso_unitario_humedo_kn_m3:.3f}"
        g_d = "-" if r.peso_unitario_seco_kn_m3 is None else f"{r.peso_unitario_seco_kn_m3:.3f}"
        lineas.append(
            f"{r.nombre} | {r.humedad_objetivo_pct:.1f} | {w_usada} | {r.origen_humedad} | {mh} | "
            f"{rho_h} | {rho_d} | {g_h} | {g_d} | {r.estado}"
        )
    return "\n".join(lineas)


def texto_referencias_normativas() -> str:
    """Referencias usadas y validacion de ecuaciones de tablero."""

    return "\n".join(
        [
            "REFERENCIAS INV E-142-13 usadas en el script:",
            "1) Tabla 142-1 (pag. E142-1 y E142-2): Metodo C usa molde 152.4 mm, 5 capas, 56 golpes/capa.",
            "2) Numeral 7.4.3 (pag. E142-13): compactacion en cinco capas.",
            "3) Numeral 7.4.4 (pag. E142-13): 56 golpes/capa para molde de 152.4 mm.",
            "4) Numeral 8.2.1 (pag. E142-17): humedad de moldeo calculada segun INV E-122.",
            "5) Ecuacion [142.4], 8.2.2 (pag. E142-17): densidad humeda rho_h = K*(MT-MMD)/V.",
            "6) Ecuacion [142.5], 8.2.3 (pag. E142-17): densidad seca rho_d = rho_h/(1 + w/100).",
            "7) Ecuacion [142.6], 8.2.4 (pag. E142-17) y [142.7] (pag. E142-18): conversion a peso unitario seco.",
            "8) Numeral 8.3.1 (pag. E142-18): curva de compactacion para estimar humedad optima y gamma_d maximo.",
            "9) Numeral 8.4, ecuacion [142.8] (pag. E142-19): curva de saturacion (solo si se dispone de Gs).",
            "10) Numeral 9.1 (pag. E142-20): contenido minimo del informe.",
            "11) Anexo A.4.2.3, ecuacion [142.9] (pag. E142-24): volumen del molde por medida lineal.",
            "",
            "VALIDACION DE ECUACIONES DEL TABLERO (Image #1) frente a norma:",
            "- Formula de humedad con recipiente: corresponde al procedimiento de INV E-122, citado en 8.2.1.",
            "- gamma_total = Wmh / V: coincide con [142.4] cuando K=1 y Wmh ya es solo suelo humedo.",
            "- gamma_d = gamma_total/(1+w): equivalente a [142.5] si w esta en fraccion.",
            "- Si w se maneja en porcentaje, usar gamma_d = gamma_total/(1 + w/100).",
            "- Curva de compactacion gamma_d vs w y punto optimo: corresponde a 8.3.1.",
        ]
    )


def guardar_reporte(path_reporte: Path, contenido: str) -> None:
    path_reporte.write_text(contenido, encoding="utf-8")


def ejecutar() -> None:
    """Orquesta el proceso completo de forma simple y legible."""

    # 1) Cargar datos de laboratorio.
    datos = cargar_datos_laboratorio()
    config: ConfiguracionEnsayo = datos["configuracion"]
    molde = datos["molde"]
    puntos: list[PuntoCompactacion] = datos["puntos"]

    # 2) Calcular volumen de molde con medidas lineales (Anexo A.4.2.3).
    volumen_cm3, diametro_promedio_cm, altura_promedio_cm = calcular_volumen_molde_cm3(
        diametros_cm=molde["diametros_cm"],
        alturas_cm=molde["alturas_cm"],
    )

    # 3) Calcular resultados por punto y filtrar los validos.
    resultados = [calcular_resultado_punto(punto, volumen_cm3) for punto in puntos]
    resultados_validos = filtrar_resultados_validos(resultados)
    if not resultados_validos:
        raise RuntimeError("No hay puntos validos para calcular.")

    # 4) Estimar optimo (regresion parabolica si hay >= 3 puntos validos).
    optimo = estimar_optimo(resultados_validos)

    # 5) Validar contra condiciones clave de la norma.
    mensajes_validacion = validar_norma(
        config=config,
        diametro_promedio_cm=diametro_promedio_cm,
        resultados_validos=resultados_validos,
        optimo=optimo,
        gs=config.gravedad_especifica_gs,
    )

    # 6) Generar solo la curva de compactacion.
    CARPETA_RESULTADOS.mkdir(parents=True, exist_ok=True)
    ruta_curva_compactacion = CARPETA_RESULTADOS / "curva_compactacion_metodo_c.png"
    graficar_curva_compactacion(
        resultados_validos=resultados_validos,
        optimo=optimo,
        ruta_curva_compactacion=ruta_curva_compactacion,
    )

    # 7) Consolidar reporte final.
    reporte: list[str] = []
    reporte.append("LABORATORIO PROCTOR MODIFICADO - METODO C (INV E-142-13)")
    reporte.append("")
    reporte.append("DATOS DE MOLDE")
    reporte.append(
        f"- Diametro promedio: {diametro_promedio_cm:.3f} cm | "
        f"Altura promedio: {altura_promedio_cm:.3f} cm | Volumen: {volumen_cm3:.2f} cm3"
    )
    reporte.append("")
    reporte.append("RESULTADOS POR PUNTO")
    reporte.append(tabla_resultados(resultados))
    reporte.append("")
    reporte.append("OPTIMO ESTIMADO")
    reporte.append(
        f"- Metodo: {optimo['metodo']} | Humedad optima: {optimo['humedad_optima_pct']:.2f} % | "
        f"Peso unitario seco maximo: {optimo['peso_unitario_seco_max_kn_m3']:.3f} kN/m3"
    )
    reporte.append("")
    reporte.append("VALIDACION NORMATIVA")
    reporte.extend(f"- {mensaje}" for mensaje in mensajes_validacion)
    reporte.append("")
    reporte.append("GRAFICAS GENERADAS")
    reporte.append(f"- {ruta_curva_compactacion}")
    reporte.append("")
    reporte.append(texto_referencias_normativas())

    texto_reporte = "\n".join(reporte)
    print(texto_reporte)

    ruta_reporte = CARPETA_RESULTADOS / "reporte_proctor_metodo_c.txt"
    guardar_reporte(ruta_reporte, texto_reporte)
    print(f"\nReporte guardado en: {ruta_reporte}")


if __name__ == "__main__":
    ejecutar()
