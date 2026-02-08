"""Modulo interactivo para gestionar el ensayo Proctor Modificado Metodo C.

Permite:
- Ver datos actuales de entrada.
- Editar datos por punto de compactacion.
- Ejecutar el calculo completo y generar productos (TXT, PNG, XLSX).
"""

from __future__ import annotations

from typing import Optional

from Laboratorio_1_proctor_modificado_metodo_c import CARPETA_RESULTADOS, procesar_ensayo
from datos_proctor_laboratorio import MasaHumedaWM, MasaSecaWm, PuntoCompactacion, cargar_datos_laboratorio


def _fmt(v: Optional[float], n: int = 3) -> str:
    if v is None:
        return "-"
    return f"{v:.{n}f}"


def _leer_float(prompt: str, actual: Optional[float], permitir_none: bool = True) -> Optional[float]:
    valor_actual = "-" if actual is None else str(actual)
    while True:
        txt = input(f"{prompt} [{valor_actual}]: ").strip()
        if txt == "":
            return actual
        if permitir_none and txt.lower() in {"none", "-", "na", "n/a"}:
            return None
        try:
            return float(txt.replace(",", "."))
        except ValueError:
            print("Valor invalido. Ingrese un numero, o vacio para conservar.")


def mostrar_datos(datos: dict) -> None:
    print("\n=== DATOS DE ENTRADA ACTUALES ===")
    config = datos["configuracion"]
    molde = datos["molde"]
    print(
        f"Norma={config.norma} | Metodo={config.metodo} | Preparacion={config.preparacion_muestra} | "
        f"Capas={config.capas} | Golpes/capa={config.golpes_por_capa}"
    )
    print(
        f"Molde: d={molde['diametros_cm']} cm | h={molde['alturas_cm']} cm"
    )
    print(
        "Punto | w_obj | M_inicial | Agua_add | Wb | Wb+WMh | Wr | Wr+Wmh | Wr+Wms"
    )
    print("-" * 95)
    for p in datos["puntos"]:
        WM = p.WM if p.WM is not None else MasaHumedaWM()
        Wm = p.Wm if p.Wm is not None else MasaSecaWm()
        print(
            f"{p.nombre:5} | {_fmt(p.humedad_objetivo_pct,2):>5} | {_fmt(p.masa_muestra_inicial_g,1):>8} | "
            f"{_fmt(p.agua_adicionada_g,1):>8} | {_fmt(WM.Wb_g,1):>6} | {_fmt(WM.Wb_WMh_g,1):>8} | "
            f"{_fmt(Wm.Wr_g,1):>6} | {_fmt(Wm.Wr_Wmh_g,1):>8} | {_fmt(Wm.Wr_Wms_g,1):>8}"
        )


def _editar_punto(punto: PuntoCompactacion) -> None:
    print(f"\n--- Editando {punto.nombre} ---")

    punto.humedad_objetivo_pct = _leer_float("Humedad objetivo (%)", punto.humedad_objetivo_pct, permitir_none=False)
    punto.masa_muestra_inicial_g = _leer_float("Masa muestra inicial (g)", punto.masa_muestra_inicial_g, permitir_none=False)
    punto.agua_adicionada_g = _leer_float("Agua adicionada (g)", punto.agua_adicionada_g, permitir_none=False)

    if punto.WM is None:
        punto.WM = MasaHumedaWM()
    punto.WM.Wb_g = _leer_float("Wb = molde+base (g)", punto.WM.Wb_g, permitir_none=True)
    punto.WM.Wb_WMh_g = _leer_float("Wb+WMh = molde+base+muestra humeda (g)", punto.WM.Wb_WMh_g, permitir_none=True)

    if punto.Wm is None:
        punto.Wm = MasaSecaWm()
    punto.Wm.Wr_g = _leer_float("Wr = recipiente (g)", punto.Wm.Wr_g, permitir_none=True)
    punto.Wm.Wr_Wmh_g = _leer_float("Wr+Wmh = recipiente+muestra humeda (g)", punto.Wm.Wr_Wmh_g, permitir_none=True)
    punto.Wm.Wr_Wms_g = _leer_float("Wr+Wms = recipiente+muestra seca (g)", punto.Wm.Wr_Wms_g, permitir_none=True)


def _renombrar_puntos(datos: dict) -> None:
    for i, p in enumerate(datos["puntos"], start=1):
        p.nombre = f"Punto {i}"


def _agregar_punto(datos: dict) -> None:
    puntos: list[PuntoCompactacion] = datos["puntos"]
    ultimo = puntos[-1] if puntos else None
    nuevo_num = len(puntos) + 1

    punto = PuntoCompactacion(
        nombre=f"Punto {nuevo_num}",
        humedad_objetivo_pct=(ultimo.humedad_objetivo_pct + 1.0) if ultimo else 0.0,
        masa_muestra_inicial_g=ultimo.masa_muestra_inicial_g if ultimo else 5000.0,
        agua_adicionada_g=0.0,
        WM=MasaHumedaWM(),
        Wm=MasaSecaWm(),
    )
    puntos.append(punto)
    print(f"Se agrego {punto.nombre}.")
    _editar_punto(punto)


def _eliminar_punto(datos: dict) -> None:
    puntos: list[PuntoCompactacion] = datos["puntos"]
    if len(puntos) <= 1:
        print("No se puede eliminar: debe existir al menos un punto.")
        return

    mostrar_datos(datos)
    idx_txt = input(f"\nNumero de punto a eliminar [1-{len(puntos)}]: ").strip()
    if not idx_txt.isdigit():
        print("Indice invalido.")
        return
    idx = int(idx_txt) - 1
    if idx < 0 or idx >= len(puntos):
        print("Indice fuera de rango.")
        return

    eliminado = puntos.pop(idx)
    _renombrar_puntos(datos)
    print(f"Se elimino {eliminado.nombre}.")


def ejecutar_interactivo() -> None:
    datos = cargar_datos_laboratorio()

    while True:
        print("\n====== MENU INTERACTIVO PROCTOR ======")
        print("1) Ver datos actuales")
        print("2) Editar punto de compactacion")
        print("3) Agregar nuevo punto")
        print("4) Eliminar punto")
        print("5) Ejecutar calculo y generar productos")
        print("6) Restablecer datos base")
        print("7) Salir")
        opcion = input("Seleccione una opcion [1-7]: ").strip()

        if opcion == "1":
            mostrar_datos(datos)
        elif opcion == "2":
            mostrar_datos(datos)
            idx_txt = input(f"\nNumero de punto a editar [1-{len(datos['puntos'])}]: ").strip()
            if not idx_txt.isdigit():
                print("Indice invalido.")
                continue
            idx = int(idx_txt) - 1
            if idx < 0 or idx >= len(datos["puntos"]):
                print("Indice fuera de rango.")
                continue
            _editar_punto(datos["puntos"][idx])
            print("Punto actualizado.")
        elif opcion == "3":
            _agregar_punto(datos)
        elif opcion == "4":
            _eliminar_punto(datos)
        elif opcion == "5":
            salida = procesar_ensayo(datos=datos, carpeta_resultados=CARPETA_RESULTADOS)
            print("\nProductos generados:")
            print(f"- TXT:  {salida['ruta_reporte']}")
            print(f"- PNG:  {salida['ruta_curva_compactacion']}")
            print(f"- PNG:  {salida['ruta_curva_densidad']}")
            print(f"- XLSX: {salida['ruta_excel']}")
        elif opcion == "6":
            datos = cargar_datos_laboratorio()
            print("Datos restablecidos a la configuracion base del archivo.")
        elif opcion == "7":
            print("Saliendo del modulo interactivo.")
            break
        else:
            print("Opcion invalida. Use 1, 2, 3, 4, 5, 6 o 7.")


if __name__ == "__main__":
    ejecutar_interactivo()
