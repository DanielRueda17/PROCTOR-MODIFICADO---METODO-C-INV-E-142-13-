"""Calculos base del ensayo Proctor modificado (INV E-142-13, Metodo C)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

import numpy as np

from datos_proctor_laboratorio import MasaSecaWm, PuntoCompactacion

# factor para convertir densidad en g/cm3 a peso unitario en kN/m3.
K1_KN_M3_POR_G_CM3 = 9.8066
# gamma_w segun INV E-142-13, ecuacion [142.8]:
# peso unitario del agua a 20 C para curva de saturacion.
GAMMA_AGUA_20C_KN_M3 = 9.789


@dataclass
class ResultadoPunto:
    """Resultados calculados para un punto de compactacion."""

    nombre: str
    humedad_objetivo_pct: float
    humedad_usada_pct: Optional[float]
    origen_humedad: str
    masa_suelo_humedo_molde_g: Optional[float]
    densidad_humeda_g_cm3: Optional[float]
    densidad_seca_g_cm3: Optional[float]
    peso_unitario_humedo_kn_m3: Optional[float]
    peso_unitario_seco_kn_m3: Optional[float]
    estado: str


def promedio(valores: list[float]) -> float:
    """Promedio simple."""
    return sum(valores) / len(valores)


def calcular_volumen_molde_cm3(diametros_cm: list[float], alturas_cm: list[float]) -> tuple[float, float, float]:
    """Anexo A.4.2.3, ecuacion [142.9]."""

    diametro_promedio_cm = promedio(diametros_cm)
    altura_promedio_cm = promedio(alturas_cm)
    volumen_cm3 = math.pi * altura_promedio_cm * (diametro_promedio_cm**2) / 4.0
    return volumen_cm3, diametro_promedio_cm, altura_promedio_cm


def calcular_humedad_pct(Wm: Optional[MasaSecaWm], humedad_objetivo_pct: float) -> tuple[float, str]:
    """% contenido de humedad """
    #Validaciones
    if Wm is None:
        return humedad_objetivo_pct, "objetivo (sin ensayo de humedad)"

    if (
        Wm.Wr_g is None
        or Wm.Wr_Wmh_g is None
        or Wm.Wr_Wms_g is None
    ):
        return humedad_objetivo_pct, "objetivo (falta peso seco en recipiente)"

    # w(%) = [((Wmh+rec) - (Wms+rec)) / ((Wms+rec)-rec)] * 100
    # En variables del codigo:
    # (Wmh+rec) -> Wr_Wmh_g
    # (Wms+rec) -> Wr_Wms_g
    # rec       -> Wr_g
    # Alias locales de lectura: tomamos los datos del objeto Wm para escribir la formula en notacion de laboratorio.
    Wr_Wmh = Wm.Wr_Wmh_g
    Wr_Wms = Wm.Wr_Wms_g
    Wr = Wm.Wr_g

    # Masa de agua = (Wmh+rec) - (Wms+rec)
    masa_agua_g = Wr_Wmh - Wr_Wms

    # Masa de suelo seco = (Wms+rec) - rec
    masa_suelo_seco_g = Wr_Wms - Wr
    if masa_suelo_seco_g <= 0:
        raise ValueError("El peso seco del suelo en recipiente no puede ser <= 0.")

    humedad_pct = (masa_agua_g / masa_suelo_seco_g) * 100.0
    return humedad_pct, "medida (INV E-122)"


def calcular_resultado_punto(punto: PuntoCompactacion, volumen_molde_cm3: float) -> ResultadoPunto:
    """Calcula WMh, rho_h, rho_d, gamma_h y gamma_d para un punto."""
    #Validaciones
    if (
        punto.WM is None
        or punto.WM.Wb_g is None
        or punto.WM.Wb_WMh_g is None
    ):
        return ResultadoPunto(
            nombre=punto.nombre,
            humedad_objetivo_pct=punto.humedad_objetivo_pct,
            humedad_usada_pct=None,
            origen_humedad="sin datos de compactacion",
            masa_suelo_humedo_molde_g=None,
            densidad_humeda_g_cm3=None,
            densidad_seca_g_cm3=None,
            peso_unitario_humedo_kn_m3=None,
            peso_unitario_seco_kn_m3=None,
            estado="PENDIENTE: completar masas del punto",
        )

    # WMh = (molde+base+suelo humedo) - (molde+base)
    # En variables del codigo:
    # (WMh+molde+base) -> Wb_WMh_g
    # (molde+base)     -> Wb_g
    masa_suelo_humedo_molde_g = punto.WM.Wb_WMh_g - punto.WM.Wb_g
    if masa_suelo_humedo_molde_g <= 0:
        return ResultadoPunto(
            nombre=punto.nombre,
            humedad_objetivo_pct=punto.humedad_objetivo_pct,
            humedad_usada_pct=None,
            origen_humedad="no aplica",
            masa_suelo_humedo_molde_g=masa_suelo_humedo_molde_g,
            densidad_humeda_g_cm3=None,
            densidad_seca_g_cm3=None,
            peso_unitario_humedo_kn_m3=None,
            peso_unitario_seco_kn_m3=None,
            estado="ERROR: masa humeda en molde <= 0",
        )

    humedad_pct, origen_humedad = calcular_humedad_pct(punto.Wm, punto.humedad_objetivo_pct)

    # 8.2.2 [142.4]: rho_h = WMh / V (K=1, unidades g/cm3 y cm3)
    densidad_humeda_g_cm3 = masa_suelo_humedo_molde_g / volumen_molde_cm3


    # 8.2.3 [142.5]: rho_d = rho_h / (1 + w/100)
    densidad_seca_g_cm3 = densidad_humeda_g_cm3 / (1.0 + humedad_pct / 100.0)

    # 8.2.4 [142.6]: gamma = K1 * rho
    peso_unitario_humedo_kn_m3 = densidad_humeda_g_cm3 * K1_KN_M3_POR_G_CM3
    peso_unitario_seco_kn_m3 = densidad_seca_g_cm3 * K1_KN_M3_POR_G_CM3

    return ResultadoPunto(
        nombre=punto.nombre,
        humedad_objetivo_pct=punto.humedad_objetivo_pct,
        humedad_usada_pct=humedad_pct,
        origen_humedad=origen_humedad,
        masa_suelo_humedo_molde_g=masa_suelo_humedo_molde_g,
        densidad_humeda_g_cm3=densidad_humeda_g_cm3,
        densidad_seca_g_cm3=densidad_seca_g_cm3,
        peso_unitario_humedo_kn_m3=peso_unitario_humedo_kn_m3,
        peso_unitario_seco_kn_m3=peso_unitario_seco_kn_m3,
        estado="OK",
    )


def filtrar_resultados_validos(resultados: list[ResultadoPunto]) -> list[ResultadoPunto]:
    """Solo puntos con calculos completos y consistentes."""
    return [r for r in resultados if r.estado == "OK"]


def estimar_optimo(resultados_validos: list[ResultadoPunto]) -> dict:
    """8.3.1: estima humedad optima y gamma_d maximo.
    
    Criterio aplicado en este script:
    - La norma pide trazar la curva de compactacion con suficientes puntos
       y tomar el punto mas alto de la curva.
    - Con 4 puntos validos, aqui representamos esa curva con una parabola
      (regresion de grado 2) y usamos su vertice como punto optimo.
    """

    humedades_pct = np.array([r.humedad_usada_pct for r in resultados_validos], dtype=float)
    pesos_unitarios_secos = np.array([r.peso_unitario_seco_kn_m3 for r in resultados_validos], dtype=float)

    indice_maximo = int(np.argmax(pesos_unitarios_secos))
    mejor_discreto = {
        "metodo": "maximo medido",
        "humedad_optima_pct": float(humedades_pct[indice_maximo]),
        "peso_unitario_seco_max_kn_m3": float(pesos_unitarios_secos[indice_maximo]),
        "coeficientes": None,
    }
    
    #VALIDACIONES:
    # solo se calcula el optimo por regresion cuando hay al menos 4 puntos validos.
    # Si hay menos, se reporta un valor provisional por maximo medido.
    if len(resultados_validos) < 4:
        mejor_discreto["metodo"] = "maximo medido (provisional, faltan 4 puntos)"
        return mejor_discreto

    # Ajuste parabolico: gamma_d = a*w^2 + b*w + c
    coeficientes = np.polyfit(humedades_pct, pesos_unitarios_secos, 2)
    a, b, c = coeficientes
    if a >= 0:
        # Si la parabola abre hacia arriba, no representa la forma esperada de la
        # curva de compactacion; por seguridad se conserva maximo medido.
        mejor_discreto["metodo"] = "maximo medido (ajuste no representativo)"
        return mejor_discreto

    # Vertice de la parabola (punto optimo teorico de la curva ajustada):
    # w_opt = -b/(2a)
    humedad_vertice_pct = -b / (2 * a)
    peso_vertice_kn_m3 = np.polyval(coeficientes, humedad_vertice_pct)

    # Extrapolacion permitida:
    # Si el vertice cae fuera del rango medido, se conserva igualmente como
    # estimacion matematica del optimo de la parabola ajustada.
    # Esto prioriza precision del ajuste (regresion) sobre restriccion al rango.

    return {
        "metodo": "regresion parabolica con extrapolacion",
        "humedad_optima_pct": float(humedad_vertice_pct),
        "peso_unitario_seco_max_kn_m3": float(peso_vertice_kn_m3),
        "coeficientes": coeficientes,
    }


