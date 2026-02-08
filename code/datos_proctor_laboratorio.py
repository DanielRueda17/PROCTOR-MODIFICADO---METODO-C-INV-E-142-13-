"""Datos de entrada para el ensayo Proctor modificado (INV E-142-13, Metodo C).

Este archivo solo contiene ingreso de datos. Los calculos estan en
`Laboratorio_1_proctor_modificado_metodo_c.py`.

Nomenclatura usada:
- W: masa/peso
- M: muestra principal compactada en molde
- m: submuestra pequena para humedad en horno
- h: humeda
- s: seca
- r: recipiente
- b: molde + base
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class MasaHumedaWM:
    """Masa humeda de la probeta compactada (WM).

    Nomenclatura usada:
    - W: masa/peso.
    - M: muestra principal compactada en el molde.
    - WM: peso de la muestra principal del Proctor.
    - Wm: peso de la submuestra pequena para horno.
    """

    # Wb = (molde + base)
    Wb_g: Optional[float] = None
    # Wb_WMh = (molde + base + muestra principal humeda)
    Wb_WMh_g: Optional[float] = None


@dataclass
class MasaSecaWm:
    """Pesos para contenido de humedad de muestra pequena (Wm), INV E-122.

    Nomenclatura usada:
    - Wr_g -> recipiente
    - Wr_Wmh_g -> (Wmh + recipiente)
    - Wr_Wms_g -> (Wms + recipiente)
    """

    Wr_g: Optional[float] = None
    Wr_Wmh_g: Optional[float] = None
    Wr_Wms_g: Optional[float] = None


@dataclass
class PuntoCompactacion:
    """Datos de un punto de la curva de compactacion."""

    nombre: str
    humedad_objetivo_pct: float
    masa_muestra_inicial_g: float
    agua_adicionada_g: float
    WM: Optional[MasaHumedaWM] = None
    Wm: Optional[MasaSecaWm] = None


@dataclass
class ConfiguracionEnsayo:
    norma: str
    metodo: str
    preparacion_muestra: str
    capas: int
    golpes_por_capa: int
    gravedad_especifica_gs: Optional[float]


def cargar_datos_laboratorio() -> dict:
    """Retorna un diccionario simple con todos los datos de entrada.

    Quedan programados 4 puntos de humedad: 2, 4, 5 y 7 %.
    Actualmente solo hay datos completos en tablero para 2 y 4 %.
    """

    configuracion = ConfiguracionEnsayo(
        norma="INV E-142-13",
        metodo="C",
        preparacion_muestra="via humeda",
        capas=5,
        golpes_por_capa=56,
        gravedad_especifica_gs=None,  # Sin Gs reportada: no se usa curva de saturacion.
    )

    # Medidas del molde : h = [12, 11.7, 11.7] cm y d = 15.2 cm.
    molde = {
        "diametros_cm": [15.2, 15.2, 15.2],
        "alturas_cm": [12.0, 11.7, 11.7],
    }

    puntos = [
        PuntoCompactacion(
            nombre="Punto 1",
            humedad_objetivo_pct= 2.0,
            masa_muestra_inicial_g=5000.0,
            agua_adicionada_g=100.0,
            WM=MasaHumedaWM(
                Wb_g=6040.0,
                Wb_WMh_g=10400.0,
            ),
            Wm=MasaSecaWm(
                Wr_g=254.7,
                Wr_Wmh_g=1051.1,
                Wr_Wms_g=1028.1,
            ),
        ),
        PuntoCompactacion(
            nombre="Punto 2",
            humedad_objetivo_pct=4.0,
            masa_muestra_inicial_g=5000.0,
            agua_adicionada_g=200.0,
            WM=MasaHumedaWM(
                Wb_g=6040.0,
                Wb_WMh_g=10470.0,
            ),
            Wm=MasaSecaWm(
                Wr_g=252.7,
                Wr_Wmh_g=878.5,
                Wr_Wms_g=849.1,
            ),
        ),
        PuntoCompactacion(
            nombre="Punto 3",
            humedad_objetivo_pct=5.0,
            masa_muestra_inicial_g=5000.0,
            agua_adicionada_g=250.0,
            WM=MasaHumedaWM(
                Wb_g=6040,
                Wb_WMh_g=10820,
            ),
            Wm=MasaSecaWm(
                Wr_g=190.6,
                Wr_Wmh_g=843.3,
                Wr_Wms_g=808.3,
            ),
        ),
        PuntoCompactacion(
            nombre="Punto 4",
            humedad_objetivo_pct=7.0,
            masa_muestra_inicial_g=5000.0,
            agua_adicionada_g=350.0,
            WM=MasaHumedaWM(
                Wb_g=6040,
                Wb_WMh_g=11030,
            ),
            Wm=MasaSecaWm(
                Wr_g=251.9,
                Wr_Wmh_g=962.2,
                Wr_Wms_g= 911.9,
            ),
        ),
    ]

    return {
        "configuracion": configuracion,
        "molde": molde,
        "puntos": puntos,
    }
