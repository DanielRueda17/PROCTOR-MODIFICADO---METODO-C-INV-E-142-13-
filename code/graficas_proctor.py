"""Funciones de graficacion para resultados Proctor."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from calculos_proctor import ResultadoPunto


def graficar_curva_compactacion(
    resultados_validos: list[ResultadoPunto],
    optimo: dict,
    ruta_curva_compactacion: Path,
) -> None:
    """Genera solo la curva de compactacion."""

    humedades_pct = np.array([r.humedad_usada_pct for r in resultados_validos], dtype=float)
    gamma_d_kn_m3 = np.array([r.peso_unitario_seco_kn_m3 for r in resultados_validos], dtype=float)
    orden = np.argsort(humedades_pct)

    # Figura principal: curva de compactacion.
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.scatter(humedades_pct, gamma_d_kn_m3, color="tab:blue", label="Puntos medidos")
    ax.plot(humedades_pct[orden], gamma_d_kn_m3[orden], color="tab:blue", alpha=0.5)

    if optimo["coeficientes"] is not None:
        a, b, c = optimo["coeficientes"]
        x = np.linspace(float(np.min(humedades_pct)), float(np.max(humedades_pct)), 300)
        y = a * x**2 + b * x + c
        ax.plot(x, y, color="tab:red", label="Ajuste parabolico")

    ax.scatter(
        [optimo["humedad_optima_pct"]],
        [optimo["peso_unitario_seco_max_kn_m3"]],
        color="black",
        zorder=3,
        label="Optimo estimado",
    )

    for r in resultados_validos:
        ax.annotate(
            r.nombre,
            (r.humedad_usada_pct, r.peso_unitario_seco_kn_m3),
            textcoords="offset points",
            xytext=(5, 5),
            fontsize=8,
        )

    ax.set_title("Curva de compactacion Proctor modificado - Metodo C")
    ax.set_xlabel("Humedad de moldeo, w (%)")
    ax.set_ylabel("Peso unitario seco, gamma_d (kN/m3)")
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(ruta_curva_compactacion, dpi=300)
    plt.close(fig)
