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
from ficha_tecnica_excel import exportar_ficha_tecnica_excel
from graficas_proctor import graficar_curva_compactacion, graficar_curva_densidad_seca_gcm3
from reporte_txt_proctor import generar_ficha_tecnica_txt
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


def procesar_ensayo(datos: dict, carpeta_resultados: Path = CARPETA_RESULTADOS) -> dict:
    """Ejecuta calculos, validaciones y exportes para un conjunto de datos."""

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

    # 4) Estimar optimo (regresion parabolica si hay >= 4 puntos validos).
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
    carpeta_resultados.mkdir(parents=True, exist_ok=True)
    ruta_curva_compactacion = carpeta_resultados / "curva_compactacion_metodo_c.png"
    graficar_curva_compactacion(
        resultados_validos=resultados_validos,
        optimo=optimo,
        ruta_curva_compactacion=ruta_curva_compactacion,
    )
    ruta_curva_densidad = carpeta_resultados / "curva_densidad_seca_gcm3.png"
    graficar_curva_densidad_seca_gcm3(
        resultados_validos=resultados_validos,
        optimo=optimo,
        ruta_curva_densidad=ruta_curva_densidad,
    )

    molde_con_calculos = {
        **molde,
        "volumen_cm3": volumen_cm3,
        "diametro_promedio_cm": diametro_promedio_cm,
        "altura_promedio_cm": altura_promedio_cm,
    }
    ruta_excel = carpeta_resultados / "ficha_tecnica_proctor_metodo_c.xlsx"
    exportar_ficha_tecnica_excel(
        ruta_excel=ruta_excel,
        config=config,
        molde=molde_con_calculos,
        puntos=puntos,
        resultados=resultados,
        resultados_validos=resultados_validos,
        optimo=optimo,
        mensajes_validacion=mensajes_validacion,
        texto_referencias=texto_referencias_normativas(),
    )

    # 7) Consolidar reporte final (ficha tecnica TXT mejorada).
    texto_reporte = generar_ficha_tecnica_txt(
        config=config,
        volumen_cm3=volumen_cm3,
        diametro_promedio_cm=diametro_promedio_cm,
        altura_promedio_cm=altura_promedio_cm,
        resultados=resultados,
        resultados_validos=resultados_validos,
        optimo=optimo,
        mensajes_validacion=mensajes_validacion,
        ruta_curva_compactacion=str(ruta_curva_compactacion),
        ruta_curva_densidad=str(ruta_curva_densidad),
        ruta_excel=str(ruta_excel),
        referencias_normativas=texto_referencias_normativas(),
    )
    print(texto_reporte)

    ruta_reporte = carpeta_resultados / "reporte_proctor_metodo_c.txt"
    guardar_reporte(ruta_reporte, texto_reporte)
    print(f"\nReporte guardado en: {ruta_reporte}")
    return {
        "ruta_reporte": ruta_reporte,
        "ruta_curva_compactacion": ruta_curva_compactacion,
        "ruta_curva_densidad": ruta_curva_densidad,
        "ruta_excel": ruta_excel,
        "resultados": resultados,
        "resultados_validos": resultados_validos,
        "optimo": optimo,
        "mensajes_validacion": mensajes_validacion,
        "texto_reporte": texto_reporte,
    }


def ejecutar() -> None:
    """Orquesta el proceso completo de forma simple y legible."""

    # 1) Cargar datos de laboratorio.
    datos = cargar_datos_laboratorio()
    procesar_ensayo(datos=datos, carpeta_resultados=CARPETA_RESULTADOS)


if __name__ == "__main__":
    ejecutar()
