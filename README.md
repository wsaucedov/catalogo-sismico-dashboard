# Dashboard · Catálogo Sísmico Instrumental del Perú 1960–2025

**Curso:** Visualización de Datos · **Estudiante:** Walter Saucedo Vega
**Entrega:** Hito 3 — versión Python + Streamlit (base de comparación con Power BI)

Dashboard descriptivo para un **analista de monitoreo sísmico o de gestión del riesgo**. Permite priorizar
periodos atípicos (D1), localizar concentraciones de epicentros (D2), comparar perfiles de profundidad (D3),
revisar años con eventos fuertes (D4) y controlar la calidad del dato antes de interpretar (D5).
**No predice sismos ni reemplaza información oficial.**

---

## 1. Cómo ejecutarlo (elija una opción)

| Opción | Requisito | Pasos |
|---|---|---|
| **A. Enlace web** | Navegador | Abrir: `PEGAR AQUÍ EL ENLACE DE STREAMLIT COMMUNITY CLOUD` |
| **B. Windows, doble clic** | Python 3.10–3.13 | Descomprimir la carpeta y hacer doble clic en **`ejecutar_app.bat`**. La primera vez crea un entorno `.venv` e instala dependencias (2–4 min). Se abre `http://localhost:8501`. |
| **C. Docker** | Docker Desktop | Doble clic en **`ejecutar_docker.bat`**, o en terminal: `docker compose up --build` y abrir `http://localhost:8501`. Detener: `docker compose down`. |
| **D. Manual** (cualquier SO) | Python 3.10–3.13 | `python -m venv .venv` → activar → `pip install -r requirements.txt` → `streamlit run app.py`. En macOS/Linux: `./ejecutar_app.sh`. |

> El mapa usa teselas de CartoDB y requiere conexión a internet. Sin conexión, ejecute con
> `MAPA_ESTILO=white-bg` (fondo blanco, los epicentros se dibujan igual).

## 2. Estructura

```
├── app.py                  # Aplicación: filtros globales, KPI y 5 páginas
├── src/
│   ├── datos.py            # Carga, derivaciones, KPI, referencias históricas, controles de calidad
│   └── graficos.py         # Tema visual y una función de graficado por pregunta (P1–P8)
├── data/Catalogo_Sismico.csv   # Fuente original, sin modificar (separador «;»)
├── .streamlit/config.toml  # Tema (colores, tipografía)
├── requirements.txt        # Dependencias
├── Dockerfile · docker-compose.yml
├── ejecutar_app.bat · ejecutar_docker.bat · ejecutar_app.sh
└── AUTOAUDITORIA.md        # Revisión del tablero con la plantilla de auditoría del curso
```

## 3. Contenido del dashboard

| Página | Decisiones | Contenido |
|---|---|---|
| **Resumen** | D1–D5 | 6 KPI con referencia histórica · mapa de epicentros (P2) · serie anual con mediana y P90 (P1) · composición por profundidad (P6) · hallazgos y recomendación |
| **Temporal** | D1, D4 | Serie anual **clicable** → detalle del año (variación vs año anterior, M ≥ 6, top 5 eventos) · años con más M ≥ 6 (P7) · mapa de calor década × mes (P8) · serie anual/mensual/diaria |
| **Espacial y profundidad** | D2, D3 | Mapa de epicentros o densidad · **selección por lazo/caja que recalcula KPI y gráficos** · geoceldas 1° × 1° · histograma (P3) · caja (P4) · dispersión (P5) · IC bootstrap 95 % (incertidumbre) |
| **Calidad del dato** | D5 | Completitud (KPI-06) · año sin registros · eventos repetidos · coordenadas fuera de envolvente · normalización de FECHA_CORTE · descarga CSV |
| **KPI y método** | — | Diccionario de KPI con valores de validación y equivalentes DAX · reglas de derivación · matriz de preguntas |

**Interacción:** filtros globales (años, magnitud, profundidad) que afectan a todas las páginas, chips con el
estado del filtro, botón «Restablecer filtros», clic en la serie anual y selección espacial en el mapa.

## 4. KPI y valores de validación (catálogo completo)

| KPI | Valor | Referencia histórica anual |
|---|---|---|
| KPI-01 Sismos registrados | 24 289 | Mediana 306 · P90 811,6 |
| KPI-02 % sismos fuertes (M ≥ 6) | 1,25 % | Mediana 1,28 % · P90 4,88 % |
| KPI-03 % superficiales (< 70 km) | 64,10 % | P10–P90: 51,23–75,40 % |
| KPI-04 Profundidad mediana | 48 km | Mediana de medianas 52,5 km · P10–P90 38,8–67,0 |
| KPI-05 Magnitud máxima | 8,4 | Mediana de máximos 6,7 · P90 7,7 |
| KPI-06 Completitud de campos clave | 100 % | Meta 100 % · alerta < 99,5 % |

Estos valores coinciden con el marco de diseño (Hito 1) y son los que deben reproducir las medidas DAX en Power BI.

## 5. Calidad del dato (hallazgos nuevos respecto al Hito 1)

- **2024 sin registros**: las series lo muestran como vacío; no se interpola.
- **8 eventos repetidos con distinto ID** (misma fecha, hora, coordenadas, profundidad y magnitud; 2022–2023).
  En el Hito 1 se informó «0 duplicados» porque se comparaban filas completas, incluido el ID.
  Se conservan y se señalan para verificar con el IGP.
- **FECHA_CORTE** con formatos mezclados (AAAAMMDD y AAAADDMM): se normaliza con regla explícita.
- **13 coordenadas** fuera de la envolvente explícita lat −20° a 0°, lon −84° a −66° (el Hito 1 reportó 15 con una
  envolvente preliminar no documentada). No se eliminan.

## 6. Fuente y dependencias

- **Datos:** Instituto Geofísico del Perú. *Catálogo Sísmico Instrumental del Perú 1960–2025*. Plataforma Nacional de
  Datos Abiertos: https://www.datosabiertos.gob.pe/dataset/catalogo-sismico — fecha de corte más reciente del archivo: 28/05/2026.
- **Software:** Python 3.10–3.13, Streamlit, Plotly, pandas, NumPy (ver `requirements.txt`).
  Probado con Streamlit 1.50 y 1.66, pandas 2.2 y 3.1.

## 7. Publicar el enlace (Streamlit Community Cloud)

1. Crear un repositorio público en GitHub y subir **todo** el contenido de esta carpeta (incluida `data/`).
2. Entrar a https://share.streamlit.io con la cuenta de GitHub → **Create app** → elegir el repositorio,
   rama `main` y archivo `app.py`.
3. Copiar el enlace generado (`https://<nombre>.streamlit.app`) en la tabla de la sección 1.

## 8. Alcance

Análisis descriptivo. El aumento del número de registros refleja en gran parte la ampliación de la red sísmica
(cobertura instrumental), no un aumento de la ocurrencia física. Los umbrales (P90, rangos P10–P90) son
**de revisión analítica**, no alertas.
