"""Validaciones normativas para Proctor modificado (INV E-142-13)."""

from __future__ import annotations

from typing import Optional

from calculos_proctor import GAMMA_AGUA_20C_KN_M3, ResultadoPunto
from datos_proctor_laboratorio import ConfiguracionEnsayo


def validar_norma(
    config: ConfiguracionEnsayo,
    diametro_promedio_cm: float,
    resultados_validos: list[ResultadoPunto],
    optimo: dict,
    gs: Optional[float],
) -> list[str]:
    """Devuelve mensajes simples de conformidad y alerta."""

    mensajes: list[str] = []

    # Tabla 142-1, 7.4.3 y 7.4.4
    if config.metodo.upper() == "C":
        mensajes.append("OK metodo C seleccionado (Tabla 142-1).")
    else:
        mensajes.append("ALERTA el ensayo no esta configurado como Metodo C (Tabla 142-1).")

    if config.capas == 5:
        mensajes.append("OK se usan 5 capas (Tabla 142-1 y 7.4.3).")
    else:
        mensajes.append(f"ALERTA capas={config.capas}; la norma exige 5 capas para Metodo C.")

    if config.golpes_por_capa == 56:
        mensajes.append("OK se usan 56 golpes/capa (Tabla 142-1 y 7.4.4).")
    else:
        mensajes.append(
            f"ALERTA golpes/capa={config.golpes_por_capa}; la norma exige 56 para molde de 152.4 mm."
        )

    # Para metodo C, diametro nominal 15.24 cm.
    delta_diametro = abs(diametro_promedio_cm - 15.24)
    if delta_diametro <= 0.2:
        mensajes.append(
            f"OK diametro promedio del molde {diametro_promedio_cm:.2f} cm, consistente con Metodo C."
        )
    else:
        mensajes.append(
            f"ALERTA diametro promedio {diametro_promedio_cm:.2f} cm; revisar calibracion del molde (Anexo A.4.2)."
        )

    # 7.2.1 y 7.5: minimo 4 puntos y suficiente informacion alrededor del optimo.
    numero_puntos = len(resultados_validos)
    if numero_puntos >= 4:
        mensajes.append("OK hay al menos 4 puntos de compactacion (7.2.1).")
    else:
        mensajes.append(
            f"ALERTA solo hay {numero_puntos} puntos validos. Se requieren al menos 4 y preferiblemente 2 a cada lado del optimo (7.2.1 y 7.5)."
        )

    if numero_puntos > 0:
        humedad_optima = optimo["humedad_optima_pct"]
        humedades = [r.humedad_usada_pct for r in resultados_validos]
        puntos_izquierda = sum(1 for h in humedades if h < humedad_optima)
        puntos_derecha = sum(1 for h in humedades if h > humedad_optima)
        if puntos_izquierda >= 2 and puntos_derecha >= 2:
            mensajes.append("OK hay 2 puntos o mas en ambos lados de la humedad optima (7.2.1).")
        else:
            mensajes.append(
                f"ALERTA distribucion alrededor del optimo insuficiente: izquierda={puntos_izquierda}, derecha={puntos_derecha} (7.2.1 y 7.5)."
            )

    # 8.4 Nota 6: chequeo solo si existe gravedad especifica.
    if gs is not None and numero_puntos > 0:
        puntos_sobre_saturacion = 0
        for r in resultados_validos:
            humedad_sat_teorica = ((GAMMA_AGUA_20C_KN_M3 * gs) - r.peso_unitario_seco_kn_m3) / (
                r.peso_unitario_seco_kn_m3 * gs
            ) * 100.0
            if r.humedad_usada_pct > humedad_sat_teorica:
                puntos_sobre_saturacion += 1

        if puntos_sobre_saturacion == 0:
            mensajes.append("OK los puntos no sobrepasan la curva de saturacion (8.4, Nota 6).")
        else:
            mensajes.append(
                f"ALERTA {puntos_sobre_saturacion} punto(s) sobre la saturacion teorica; revisar Gs, pesadas o calculos (8.4, Nota 6)."
            )
    else:
        mensajes.append("INFO no se valida saturacion porque no hay gravedad especifica (Gs).")

    # Verificaciones de consistencia de calculo (INV 8.2.2, 8.2.3 y 8.2.4).
    inconsistencias = 0
    for r in resultados_validos:
        if r.humedad_usada_pct is not None and r.humedad_usada_pct < 0:
            inconsistencias += 1
        if (
            r.densidad_humeda_g_cm3 is not None
            and r.densidad_seca_g_cm3 is not None
            and r.densidad_seca_g_cm3 > r.densidad_humeda_g_cm3 + 1e-9
        ):
            inconsistencias += 1
        if (
            r.peso_unitario_humedo_kn_m3 is not None
            and r.peso_unitario_seco_kn_m3 is not None
            and r.peso_unitario_seco_kn_m3 > r.peso_unitario_humedo_kn_m3 + 1e-9
        ):
            inconsistencias += 1

    if inconsistencias == 0:
        mensajes.append("OK consistencia interna de calculos verificada (8.2.2 a 8.2.4).")
    else:
        mensajes.append(
            f"ALERTA se detectaron {inconsistencias} inconsistencia(s) internas en calculos; revisar datos de entrada."
        )

    return mensajes
