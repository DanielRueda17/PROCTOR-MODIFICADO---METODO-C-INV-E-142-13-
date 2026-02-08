# Proctor Modificado - Metodo C (INV E-142-13)

Script en Python para procesar el ensayo Proctor Modificado, Metodo C, de forma simple y legible.

## Que hace

- Lee datos de laboratorio (4 puntos de humedad objetivo: 2, 4, 5, 7).
- Calcula:
  - Contenido de humedad (`w`)
  - Densidad humeda (`rho_h`)
  - Densidad seca (`rho_d`)
  - Peso unitario humedo y seco (`gamma_h`, `gamma_d`)
- Estima el punto optimo de compactacion:
  - Provisional por maximo medido si faltan puntos.
  - Regresion parabolica si hay 4 puntos validos.
- Valida criterios clave de la norma.
- Genera:
  - Curva de compactacion (`curva_compactacion_metodo_c.png`)
  - Reporte (`reporte_proctor_metodo_c.txt`)

## Estructura

- `code/datos_proctor_laboratorio.py`: ingreso de datos.
- `code/calculos_proctor.py`: calculos base.
- `code/validaciones_proctor.py`: validaciones normativas.
- `code/graficas_proctor.py`: grafica de compactacion.
- `code/Laboratorio_1_proctor_modificado_metodo_c.py`: script principal.

## Como ejecutar

Desde la carpeta `code`:

```bash
python Laboratorio_1_proctor_modificado_metodo_c.py
```

## Salida

Los resultados se guardan en:

- `C:\Users\Oscar\Desktop\Code_universidad\Laboratorio Pavimentos\curva_compactacion_metodo_c.png`
- `C:\Users\Oscar\Desktop\Code_universidad\Laboratorio Pavimentos\reporte_proctor_metodo_c.txt`

