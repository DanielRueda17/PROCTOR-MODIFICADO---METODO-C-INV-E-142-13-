"""Funciones de graficacion para resultados Proctor."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import AutoMinorLocator

from calculos_proctor import ResultadoPunto


def _paso_escala_x(rango: float) -> float:
    """Selecciona un paso de ticks legible segun el rango de humedad."""
    if rango <= 1.5:
        return 0.1
    if rango <= 3.0:
        return 0.2
    if rango <= 6.0:
        return 0.5
    if rango <= 12.0:
        return 1.0
    return 2.0


def _ordenar_promediar_por_x(
    x_vals: np.ndarray, y_vals: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Ordena por x y promedia y en x duplicados para evitar saltos."""
    orden = np.argsort(x_vals)
    x_ord = x_vals[orden]
    y_ord = y_vals[orden]
    x_unique, inv = np.unique(x_ord, return_inverse=True)
    if len(x_unique) == len(x_ord):
        return x_ord, y_ord
    y_sum = np.zeros_like(x_unique, dtype=float)
    counts = np.zeros_like(x_unique, dtype=float)
    for i, idx in enumerate(inv):
        y_sum[idx] += y_ord[i]
        counts[idx] += 1.0
    y_mean = y_sum / counts
    return x_unique, y_mean


def _pchip_interpolar(
    x_vals: np.ndarray, y_vals: np.ndarray, n: int = 300
) -> tuple[np.ndarray, np.ndarray]:
    """Interpolacion monotona tipo PCHIP sin dependencias externas."""
    if len(x_vals) < 2:
        return x_vals, y_vals
    if len(x_vals) == 2:
        x_new = np.linspace(x_vals[0], x_vals[1], n)
        y_new = np.interp(x_new, x_vals, y_vals)
        return x_new, y_new

    h = np.diff(x_vals)
    delta = np.diff(y_vals) / h
    m = np.zeros_like(x_vals)

    for i in range(1, len(x_vals) - 1):
        if delta[i - 1] * delta[i] <= 0:
            m[i] = 0.0
        else:
            w1 = 2 * h[i] + h[i - 1]
            w2 = h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / delta[i - 1] + w2 / delta[i])

    m[0] = ((2 * h[0] + h[1]) * delta[0] - h[0] * delta[1]) / (h[0] + h[1])
    if np.sign(m[0]) != np.sign(delta[0]):
        m[0] = 0.0
    elif np.sign(delta[0]) != np.sign(delta[1]) and abs(m[0]) > abs(3 * delta[0]):
        m[0] = 3 * delta[0]

    m[-1] = ((2 * h[-1] + h[-2]) * delta[-1] - h[-1] * delta[-2]) / (h[-1] + h[-2])
    if np.sign(m[-1]) != np.sign(delta[-1]):
        m[-1] = 0.0
    elif np.sign(delta[-1]) != np.sign(delta[-2]) and abs(m[-1]) > abs(3 * delta[-1]):
        m[-1] = 3 * delta[-1]

    x_new = np.linspace(x_vals[0], x_vals[-1], n)
    idx = np.searchsorted(x_vals, x_new) - 1
    idx = np.clip(idx, 0, len(x_vals) - 2)
    h_seg = x_vals[idx + 1] - x_vals[idx]
    t = (x_new - x_vals[idx]) / h_seg
    t2 = t * t
    t3 = t2 * t
    y_new = (
        (2 * t3 - 3 * t2 + 1) * y_vals[idx]
        + (t3 - 2 * t2 + t) * h_seg * m[idx]
        + (-2 * t3 + 3 * t2) * y_vals[idx + 1]
        + (t3 - t2) * h_seg * m[idx + 1]
    )
    return x_new, y_new


def graficar_curva_compactacion(
    resultados_validos: list[ResultadoPunto],
    optimo: dict,
    ruta_curva_compactacion: Path,
) -> None:
    """Genera la curva de compactacion con estilo cientifico."""

    humedades_pct = np.array([r.humedad_usada_pct for r in resultados_validos], dtype=float)
    gamma_d_kn_m3 = np.array([r.peso_unitario_seco_kn_m3 for r in resultados_validos], dtype=float)
    x_datos = np.append(humedades_pct, float(optimo["humedad_optima_pct"]))
    x_min = float(np.min(x_datos))
    x_max = float(np.max(x_datos))
    rango_x = max(x_max - x_min, 0.5)
    margen_x = max(0.15, 0.08 * rango_x)
    paso_x = _paso_escala_x(rango_x)
    x_plot_min = np.floor((x_min - margen_x) / paso_x) * paso_x
    x_plot_max = np.ceil((x_max + margen_x) / paso_x) * paso_x
    ticks_x = np.round(np.arange(x_plot_min, x_plot_max + paso_x * 0.5, paso_x), 3)

    # Estilo tecnico/cientifico.
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "DejaVu Serif", "Cambria"],
            "axes.labelsize": 11,
            "axes.titlesize": 12,
            "legend.fontsize": 9,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
        }
    )

    fig, ax = plt.subplots(figsize=(9.2, 6.2), dpi=120)
    ax.set_facecolor("#FAFAFA")
    ax.scatter(
        humedades_pct,
        gamma_d_kn_m3,
        color="#0B5394",
        edgecolor="white",
        linewidth=0.6,
        s=55,
        zorder=3,
        label="Puntos experimentales",
    )

    if len(humedades_pct) >= 2:
        x_ord, y_ord = _ordenar_promediar_por_x(humedades_pct, gamma_d_kn_m3)
        x_suave, y_suave = _pchip_interpolar(x_ord, y_ord, n=400)
        ax.plot(
            x_suave,
            y_suave,
            color="#000000",
            linewidth=1.8,
            linestyle=":",
            label="Linea suavizada (puntos)",
            zorder=2,
        )

    if len(humedades_pct) >= 3:
        a, b, c = np.polyfit(humedades_pct, gamma_d_kn_m3, 2)
        x = np.linspace(x_plot_min, x_plot_max, 500)
        y = a * x**2 + b * x + c
        ax.plot(
            x,
            y,
            color="#C00000",
            linewidth=2.2,
            linestyle="--",
            label="Curva parabólica (ajuste)",
            zorder=1,
        )

    ax.scatter(
        [optimo["humedad_optima_pct"]],
        [optimo["peso_unitario_seco_max_kn_m3"]],
        color="#111111",
        marker="*",
        s=160,
        edgecolor="white",
        linewidth=0.6,
        zorder=3,
        label="Punto óptimo estimado",
    )

    for r in resultados_validos:
        ax.annotate(
            r.nombre,
            (r.humedad_usada_pct, r.peso_unitario_seco_kn_m3),
            textcoords="offset points",
            xytext=(7, 7),
            fontsize=8.5,
            color="#303030",
        )

    ax.set_title("Curva de Compactación - Proctor Modificado (Método C)")
    ax.set_xlabel("Humedad de moldeo, $w$ (%)")
    ax.set_ylabel("Peso unitario seco, $\\gamma_d$ (kN/m$^3$)")
    ax.set_xlim(x_plot_min, x_plot_max)
    ax.set_xticks(ticks_x)

    ax.grid(which="major", linestyle="--", color="#BFBFBF", alpha=0.55, linewidth=0.8)
    ax.grid(which="minor", linestyle=":", color="#D9D9D9", alpha=0.55, linewidth=0.6)
    ax.xaxis.set_minor_locator(AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(AutoMinorLocator(2))
    ax.tick_params(direction="in", length=6, width=1.0)
    ax.tick_params(which="minor", direction="in", length=3, width=0.8)
    for spine in ax.spines.values():
        spine.set_linewidth(1.1)
        spine.set_color("#404040")

    ax.legend(loc="best", frameon=True, edgecolor="#BFBFBF", facecolor="white")
    fig.tight_layout()
    fig.savefig(ruta_curva_compactacion, dpi=400, bbox_inches="tight")
    plt.close(fig)


def graficar_curva_densidad_seca_gcm3(
    resultados_validos: list[ResultadoPunto],
    optimo: dict,
    ruta_curva_densidad: Path,
) -> None:
    """Grafica densidad seca rho_d (g/cm3) vs contenido de humedad w (%)."""

    humedades_pct = np.array([r.humedad_usada_pct for r in resultados_validos], dtype=float)
    rho_d_g_cm3 = np.array([r.densidad_seca_g_cm3 for r in resultados_validos], dtype=float)
    x_datos = np.append(humedades_pct, float(optimo["humedad_optima_pct"]))
    x_min = float(np.min(x_datos))
    x_max = float(np.max(x_datos))
    rango_x = max(x_max - x_min, 0.5)
    margen_x = max(0.15, 0.08 * rango_x)
    paso_x = _paso_escala_x(rango_x)
    x_plot_min = np.floor((x_min - margen_x) / paso_x) * paso_x
    x_plot_max = np.ceil((x_max + margen_x) / paso_x) * paso_x
    ticks_x = np.round(np.arange(x_plot_min, x_plot_max + paso_x * 0.5, paso_x), 3)

    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "DejaVu Serif", "Cambria"],
            "axes.labelsize": 11,
            "axes.titlesize": 12,
            "legend.fontsize": 9,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
        }
    )

    fig, ax = plt.subplots(figsize=(9.2, 6.2), dpi=120)
    ax.set_facecolor("#FAFAFA")
    ax.scatter(
        humedades_pct,
        rho_d_g_cm3,
        color="#0B5394",
        edgecolor="white",
        linewidth=0.6,
        s=55,
        zorder=3,
        label="Puntos experimentales",
    )

    if len(humedades_pct) >= 2:
        x_ord, y_ord = _ordenar_promediar_por_x(humedades_pct, rho_d_g_cm3)
        x_suave, y_suave = _pchip_interpolar(x_ord, y_ord, n=400)
        ax.plot(
            x_suave,
            y_suave,
            color="#000000",
            linewidth=1.8,
            linestyle=":",
            label="Linea suavizada (puntos)",
            zorder=2,
        )

    if len(humedades_pct) >= 3:
        # Ajuste en rho_d para mostrar curva suave en g/cm3.
        a, b, c = np.polyfit(humedades_pct, rho_d_g_cm3, 2)
        x = np.linspace(x_plot_min, x_plot_max, 500)
        y = a * x**2 + b * x + c
        ax.plot(
            x,
            y,
            color="#C00000",
            linewidth=2.2,
            linestyle="--",
            label="Curva parabólica (ajuste)",
            zorder=2,
        )

    # Punto optimo convertido de gamma_d (kN/m3) a rho_d (g/cm3): rho = gamma/K1
    rho_opt = float(optimo["peso_unitario_seco_max_kn_m3"]) / 9.8066
    ax.scatter(
        [optimo["humedad_optima_pct"]],
        [rho_opt],
        color="#111111",
        marker="*",
        s=160,
        edgecolor="white",
        linewidth=0.6,
        zorder=3,
        label="Punto óptimo estimado",
    )

    for r in resultados_validos:
        ax.annotate(
            r.nombre,
            (r.humedad_usada_pct, r.densidad_seca_g_cm3),
            textcoords="offset points",
            xytext=(7, 7),
            fontsize=8.5,
            color="#303030",
        )

    ax.set_title("Curva de Densidad Seca vs Humedad")
    ax.set_xlabel("Contenido de humedad, $w$ (%)")
    ax.set_ylabel("Densidad seca, $\\rho_d$ (g/cm$^3$)")
    ax.set_xlim(x_plot_min, x_plot_max)
    ax.set_xticks(ticks_x)

    ax.grid(which="major", linestyle="--", color="#BFBFBF", alpha=0.55, linewidth=0.8)
    ax.grid(which="minor", linestyle=":", color="#D9D9D9", alpha=0.55, linewidth=0.6)
    ax.xaxis.set_minor_locator(AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(AutoMinorLocator(2))
    ax.tick_params(direction="in", length=6, width=1.0)
    ax.tick_params(which="minor", direction="in", length=3, width=0.8)
    for spine in ax.spines.values():
        spine.set_linewidth(1.1)
        spine.set_color("#404040")

    ax.legend(loc="best", frameon=True, edgecolor="#BFBFBF", facecolor="white")
    fig.tight_layout()
    fig.savefig(ruta_curva_densidad, dpi=400, bbox_inches="tight")
    plt.close(fig)
