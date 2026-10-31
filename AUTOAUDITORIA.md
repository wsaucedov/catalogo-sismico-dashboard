# Autoauditoría del dashboard (versión Streamlit)

Aplicación de la *Plantilla de auditoría de dashboard* del curso a la versión Python + Streamlit.
Escala: Cumple · Parcial · No cumple · N/A.

| Equipo / estudiante | Walter Saucedo Vega | Dashboard auditado | Catálogo Sísmico del Perú 1960–2025 (Streamlit) |
|---|---|---|---|
| **Usuario objetivo** | Analista de monitoreo sísmico / gestión del riesgo | **Decisión principal** | Priorizar periodos y zonas para revisión técnica (D1–D5) |
| **Dataset / fuente** | IGP · Catálogo Sísmico Instrumental 1960–2025 (Datos Abiertos) | **Problema** | Reconocer patrones y comparar periodos con cobertura instrumental cambiante |

## Criterios

| Dimensión | Criterio | Estado | Evidencia / observación | Mejora propuesta |
|---|---|---|---|---|
| 1. Propósito y usuario | Problema, usuario y decisión | Cumple | Encabezado de cada página con la decisión (D1–D5); página «KPI y método» declara problema, usuario y límite. | — |
| 1. Propósito y usuario | Preguntas analíticas | Cumple | Cada gráfico lleva su código y pregunta (P1–P8) sobre el título. | — |
| 2. KPI y métricas | Pertinencia de los KPI | Cumple | 6 KPI, cada uno ligado a una pregunta y decisión (tabla en «KPI y método»). | — |
| 2. KPI y métricas | Definición y contexto | Cumple | Tarjetas con unidad, referencia histórica (mediana, P90, P10–P90) y estado. Se declara que no hay dirección deseada. | — |
| 3. Selección de gráficos | Adecuación gráfico–pregunta | Cumple | Línea (evolución), mapa (localización), histograma y caja (distribución), dispersión (relación), barras 100 % (composición), barras ordenadas (comparar), calor (patrón 2D). | — |
| 3. Selección de gráficos | Marcas y canales | Parcial | Mapa codifica posición + tamaño (magnitud) + color (profundidad); con 24 mil puntos hay superposición. | Se añadió el modo «Densidad» y la tabla de geoceldas. |
| 4. Jerarquía y layout | Orden de lectura y prioridad | Cumple | KPI arriba → mapa (mayor área) y serie anual → composición → hallazgos. Coincide con el wireframe del Hito 1. | — |
| 4. Jerarquía y layout | Gestalt, alineación y espacio | Cumple | Grid de 6 tarjetas iguales; pares de gráficos alineados; detalle en páginas separadas para no saturar. | — |
| 5. Color y accesibilidad | Uso del color | Cumple | Paleta Okabe–Ito fija por categoría de profundidad; magenta reservado a umbrales; secuencial (azules) en el mapa de calor. | — |
| 5. Color y accesibilidad | Contraste y accesibilidad | Cumple | Color no es el único canal (etiquetas, % dentro de barras, texto de estado en KPI). Texto oscuro sobre el ámbar #E69F00, porque el blanco no alcanzaba contraste AA. Tooltips con valor y unidad. | — |
| 6. Escalas y ética | Ejes y escalas | Cumple | Eje log del histograma declarado en el subtítulo; barras desde cero; profundidad con eje invertido y explicado. | — |
| 6. Escalas y ética | Representación no engañosa | Cumple | Sin doble eje ni 3D; barras 100 % para no confundir volumen con proporción; 2024 como hueco, no interpolado. | — |
| 7. Narrativa | Títulos y anotaciones | Cumple | Títulos con el **hallazgo** calculado según el filtro (p. ej. «7 años superan el umbral de revisión»); anotaciones de mediana, P90 y vacío de 2024. | — |
| 7. Narrativa | Secuencia narrativa | Cumple | Resumen termina en «Hallazgos y recomendación» (contexto → evidencia → hallazgo → acción). | — |
| 8. Interacción | Filtros y controles | Cumple | 3 filtros globales con función clara; clic en año (detalle); lazo en mapa (zona). | — |
| 8. Interacción | Consistencia de filtros | Cumple | Chips de estado en cada página, contador de eventos seleccionados, «Restablecer filtros» y «Quitar selección». | — |
| 9. Modelo y datos | Consistencia de resultados | Cumple | KPI del catálogo completo coinciden con Hito 1 (24 289; 1,25 %; 64,10 %; 48 km; 8,4; 100 %). Se detectaron 8 eventos repetidos con distinto ID. | Verificar repetidos con el IGP. |
| 9. Modelo y datos | Modelo y relaciones | Parcial | En Python se usa una tabla plana (un evento por fila) con columnas derivadas; no hay relaciones. | Implementar modelo estrella en Power BI (hecho + dimensiones Fecha y Profundidad). |
| 10. Tiempo y comparación | Contexto temporal | Cumple | Periodo y fecha de corte visibles; detalle anual con variación vs año anterior y razón frente a la mediana histórica. | — |
| 11. Geografía | Representación espacial | Parcial | Mapa de puntos + densidad + geoceldas regulares de 1° (no se inventan regiones). Los conteos no se normalizan por cobertura de estaciones (dato no disponible). | Declarado en la interpretación; posible mejora con densidad de estaciones del IGP. |
| 12. Coherencia global | Consistencia visual | Cumple | Un solo módulo de tema; formato numérico español (espacio de miles, coma decimal); unidades en ejes y tarjetas. | — |
| 12. Coherencia global | Carga cognitiva | Cumple | 5 páginas temáticas; vista inicial con 6 KPI + 3 gráficos; detalle bajo demanda (expander, pestañas). | — |

## Cambios priorizados (aplicados respecto al prototipo del Hito 2)

| # | Problema detectado | Evidencia | Cambio | Principio | Impacto | Prioridad |
|---|---|---|---|---|---|---|
| 1 | Títulos solo descriptivos | «Distribución de magnitudes registradas» | Título = hallazgo calculado; pregunta como antetítulo | Narrativa: títulos que comunican | El usuario lee la conclusión sin interpretar el gráfico | Alta |
| 2 | KPI sin referencia | Tarjeta «1,25 %» aislada | Referencia histórica (mediana, P90 o P10–P90) y estado textual en cada KPI | Definición y contexto de métricas | Permite saber si un valor merece revisión (D1, D4) | Alta |
| 3 | Superposición en el mapa | 24 mil puntos tapan las zonas activas | Modo densidad + geoceldas 1° con % del total | Representación espacial; marcas y canales | Identifica concentraciones sin sesgo de superposición (D2) | Media |
| 4 | Vistas no conectadas con la zona | Filtros solo en barra lateral | Selección por lazo en el mapa recalcula KPI y gráficos | Interacción útil | Compara el perfil de una zona con el total (D2–D3) | Media |
| 5 | Calidad oculta | Advertencia de 2024 solo como texto | Página «Calidad» con 4 controles, tablas de casos y regla aceptar/condicionar/detener | Consistencia de resultados; ética | Evita conclusiones sobre datos dudosos (D5) | Media |

## Conclusión

El dashboard apoya bien la priorización de periodos y zonas: cada vista responde una pregunta, los KPI tienen
referencia y los títulos comunican el hallazgo. Su principal límite es interpretativo, no técnico: el número de
registros depende de la cobertura de la red, que el catálogo no informa. El cambio más importante para su
utilidad analítica sería incorporar un indicador de cobertura instrumental (número de estaciones activas por año)
para separar el efecto de detección del de ocurrencia.
