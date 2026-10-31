"""Tema visual y funciones de graficado (Plotly). Una función por pregunta analítica."""
from __future__ import annotations

import os

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .datos import ANIO_MAX, ANIO_MIN, CATEGORIAS, bootstrap_mediana

# Paleta apta para daltonismo (Okabe–Ito), fijada en el Hito 1
COLORES = dict(zip(CATEGORIAS, ["#D55E00", "#E69F00", "#0072B2"]))
TEMA = {
    "tinta": "#1B2B38",
    "texto": "#3D5161",
    "suave": "#6B7F8E",
    "grilla": "#E6ECF0",
    "principal": "#0B4F79",
    "secundario": "#1792A4",
    "referencia": "#A23B72",   # umbrales de revisión (no alertas)
    "fondo": "#FFFFFF",
}
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
# Estilo base del mapa (requiere internet para las teselas). "white-bg" funciona sin conexión.
ESTILO_MAPA = os.environ.get("MAPA_ESTILO", "carto-positron")
CONFIG_PLOTLY = {"displaylogo": False, "locale": "es",
                 "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d"]}


def estilo(fig: go.Figure, titulo: str | None = None, subtitulo: str | None = None, alto: int = 380) -> go.Figure:
    """Tema común. En la app los títulos se escriben como texto HTML encima del gráfico
    (pregunta + hallazgo), por eso aquí el título de Plotly es opcional y se omite por defecto.
    `titulo` y `subtitulo` se conservan como documentación de la pregunta que responde la figura."""
    fig.update_layout(
        title=None,
        font={"family": "Inter, Segoe UI, Arial, sans-serif", "color": TEMA["texto"], "size": 14},
        paper_bgcolor=TEMA["fondo"], plot_bgcolor=TEMA["fondo"],
        margin={"l": 10, "r": 10, "t": 24, "b": 10},
        height=alto, legend={"title_text": "", "orientation": "h", "y": 1.0, "yanchor": "bottom", "x": 0},
        hoverlabel={"bgcolor": "white", "font_size": 14},
        separators=", ",
    )
    fig.update_xaxes(showgrid=False, linecolor=TEMA["grilla"], ticks="outside", tickcolor=TEMA["grilla"],
                     tickfont={"size": 13}, title_font={"size": 15})
    fig.update_yaxes(gridcolor=TEMA["grilla"], zeroline=False, tickfont={"size": 13}, title_font={"size": 15})
    return fig


# ---------------------------------------------------------------- P1 · D1
def fig_anual(anual: pd.DataFrame, mediana: float, p90: float, anio_sel: int | None = None) -> go.Figure:
    """Línea anual con mediana y P90 históricos. 2024 queda como hueco (NaN)."""
    sobre = anual["sismos"] > p90
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=anual["anio"], y=anual["sismos"], mode="lines+markers", connectgaps=False,
        line={"color": TEMA["principal"], "width": 2.2},
        marker={"size": np.where(sobre, 9, 5),
                "color": np.where(sobre, TEMA["referencia"], TEMA["principal"])},
        name="Sismos por año",
        hovertemplate="<b>%{x}</b><br>%{y:,.0f} sismos<extra></extra>",
    ))
    for valor, etiqueta in [(mediana, "Mediana histórica"), (p90, "P90 · umbral de revisión")]:
        fig.add_hline(y=valor, line_dash="dot", line_width=1, line_color=TEMA["referencia"],
                      annotation_text=f"{etiqueta}: {valor:,.0f}".replace(",", " "),
                      annotation_position="top left", annotation_font_color=TEMA["referencia"],
                      annotation_font_size=13)
    if anual["sismos"].isna().any():
        for a in anual.loc[anual["sismos"].isna(), "anio"]:
            if ANIO_MIN < a < ANIO_MAX + 1:
                fig.add_vrect(x0=a - 0.5, x1=a + 0.5, fillcolor="#9AA9B4", opacity=0.18, line_width=0)
                fig.add_annotation(x=a - 0.6, y=1, yref="paper", text=f"{a}: sin registros", showarrow=False,
                                   font={"size": 12, "color": TEMA["suave"]}, yanchor="top", xanchor="right")
    if anio_sel is not None:
        fig.add_vline(x=anio_sel, line_color=TEMA["secundario"], line_width=2)
    fig.update_xaxes(title="Año", dtick=10, tickangle=0, range=[ANIO_MIN - 1, ANIO_MAX + 1])
    fig.update_yaxes(title="Sismos registrados", rangemode="tozero")
    fig.update_layout(showlegend=False, clickmode="event+select")
    return estilo(fig, "¿Cómo ha evolucionado el número anual de sismos registrados?",
                  "Puntos magenta = años sobre el P90 (prioridad de revisión, D1). Haga clic en un año para ver su detalle.")


def fig_temporal(serie: pd.DataFrame, nivel: str) -> go.Figure:
    fmt = {"Anual": "%Y", "Mensual": "%b %Y", "Diaria": "%d/%m/%Y"}[nivel]
    fig = px.line(serie, x="fecha", y="sismos", markers=nivel != "Diaria")
    fig.update_traces(line_color=TEMA["secundario"], marker_size=4,
                      hovertemplate=f"%{{x|{fmt}}}<br>%{{y:,}} sismos<extra></extra>")
    fig.update_xaxes(title="Periodo")
    fig.update_yaxes(title="Sismos registrados", rangemode="tozero")
    return estilo(fig, f"Registros en el periodo filtrado · vista {nivel.lower()}",
                  "La granularidad se ajusta al rango para no dibujar 66 años como miles de puntos diarios.")


# ---------------------------------------------------------------- P2 · D2
def fig_mapa(df: pd.DataFrame, alto: int = 560, seleccionable: bool = False) -> go.Figure:
    datos = df.dropna(subset=["LATITUD", "LONGITUD"]).sort_values("MAGNITUD")
    fig = go.Figure()
    for cat in CATEGORIAS:
        d = datos[datos["categoria_prof"] == cat]
        if d.empty:
            continue
        fig.add_trace(go.Scattermap(
            lat=d["LATITUD"], lon=d["LONGITUD"], mode="markers", name=cat,
            marker={"size": 2 + (d["MAGNITUD"] - 3) ** 1.6, "color": COLORES[cat], "opacity": 0.65,
                    "sizemode": "diameter"},
            customdata=np.stack([d["ID"], d["fecha"].dt.strftime("%d/%m/%Y"), d["MAGNITUD"],
                                 d["PROFUNDIDAD"]], axis=-1),
            hovertemplate=("<b>M %{customdata[2]:.1f}</b> · %{customdata[3]:.0f} km<br>"
                           "%{customdata[1]} (UTC)<br>Lat %{lat:.2f}, Lon %{lon:.2f}"
                           "<br>ID %{customdata[0]}<extra>" + cat + "</extra>"),
        ))
    fig.update_layout(
        map={"style": ESTILO_MAPA, "center": {"lat": -9.3, "lon": -75.2}, "zoom": 4.1},
        dragmode="lasso" if seleccionable else "pan",
    )
    fig = estilo(fig, "¿Dónde se concentran los epicentros y cómo varían por magnitud y profundidad?",
                 "Tamaño = magnitud · color = profundidad del foco" +
                 (" · use lazo o caja para seleccionar un área" if seleccionable else ""), alto=alto)
    fig.update_layout(margin={"l": 0, "r": 0, "t": 0, "b": 0},
                      legend={"orientation": "h", "y": 0.01, "x": 0.01, "bgcolor": "rgba(255,255,255,.85)"})
    return fig


# ---------------------------------------------------------------- P3 · D2/D4
def fig_hist_magnitud(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Histogram(
        x=df["MAGNITUD"], xbins={"start": 2.95, "end": 8.55, "size": 0.1},
        marker_color=TEMA["principal"], marker_line_width=0,
        hovertemplate="M %{x}<br>%{y:,} sismos<extra></extra>",
    ))
    fig.add_vline(x=5.95, line_dash="dot", line_color=TEMA["referencia"],
                  annotation_text="M ≥ 6 · sismo fuerte", annotation_font_color=TEMA["referencia"],
                  annotation_font_size=13)
    fig.update_xaxes(title="Magnitud")
    fig.update_yaxes(title="Sismos (escala log)", type="log", tickvals=[1, 10, 100, 1000], ticktext=["1", "10", "100", "1 000"])
    return estilo(fig, "¿Cómo se distribuyen las magnitudes?",
                  "Eje Y logarítmico: hace visibles los pocos eventos fuertes de la cola derecha.")


# ---------------------------------------------------------------- P4 · D2/D3
def fig_caja_profundidad(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for dec in sorted(df["decada_txt"].dropna().unique()):
        v = df.loc[df["decada_txt"] == dec, "PROFUNDIDAD"]
        fig.add_trace(go.Box(y=v, name=dec, marker_color=TEMA["secundario"], line_width=1.2,
                             boxpoints="outliers", marker={"size": 2.5, "opacity": 0.35},
                             hoverinfo="y"))
    fig.add_hline(y=70, line_dash="dot", line_color=COLORES[CATEGORIAS[0]],
                  annotation_text="70 km", annotation_position="bottom left", annotation_font_size=13)
    fig.add_hline(y=300, line_dash="dot", line_color=COLORES[CATEGORIAS[2]],
                  annotation_text="300 km", annotation_position="bottom left", annotation_font_size=13)
    fig.update_yaxes(title="Profundidad (km)", autorange="reversed")
    fig.update_xaxes(title="Década")
    fig.update_layout(showlegend=False)
    return estilo(fig, "¿Cómo se distribuye la profundidad y qué atípicos presenta?",
                  "Eje invertido (la profundidad crece hacia abajo) · líneas en los cortes de categoría.")


# ---------------------------------------------------------------- P5 · D2
def fig_dispersion(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for cat in CATEGORIAS:
        d = df[df["categoria_prof"] == cat]
        if d.empty:
            continue
        fig.add_trace(go.Scattergl(
            x=d["PROFUNDIDAD"], y=d["MAGNITUD"], mode="markers", name=cat,
            marker={"color": COLORES[cat], "size": 4, "opacity": 0.35},
            hovertemplate="%{x:.0f} km · M %{y:.1f}<extra></extra>",
        ))
    fig.update_xaxes(title="Profundidad (km)")
    fig.update_yaxes(title="Magnitud")
    return estilo(fig, "¿Existe relación entre profundidad y magnitud?",
                  "Cada punto es un evento; la transparencia muestra densidad.")


# ---------------------------------------------------------------- P6 · D3
def fig_composicion(comp: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for cat in CATEGORIAS:
        d = comp[comp["categoria_prof"] == cat]
        fig.add_trace(go.Bar(
            x=d["decada_txt"], y=d["porcentaje"], name=cat, marker_color=COLORES[cat],
            text=[f"{v:.0f} %" if v >= 6 else "" for v in d["porcentaje"].fillna(0)],
            textposition="inside", insidetextanchor="middle", textangle=0,
            # Texto oscuro sobre el ámbar (blanco no alcanza contraste AA)
            textfont={"color": TEMA["tinta"] if cat == CATEGORIAS[1] else "white", "size": 13},
            customdata=d["sismos"],
            hovertemplate="%{x} · " + cat + "<br>%{y:.1f} % (%{customdata:,} sismos)<extra></extra>",
        ))
    fig.update_layout(barmode="stack", bargap=0.25)
    fig.update_yaxes(title="Porcentaje de sismos", range=[0, 100], ticksuffix=" %")
    fig.update_xaxes(title="Década")
    return estilo(fig, "¿Cómo cambió por década la composición por profundidad?",
                  "Barras al 100 %: se compara composición, no volumen. 2020s incompleta y sin 2024.")


# ---------------------------------------------------------------- P7 · D4
def fig_fuertes(tabla: pd.DataFrame) -> go.Figure:
    t = tabla.sort_values(["fuertes", "pct"])
    fig = go.Figure(go.Bar(
        x=t["fuertes"], y=t["anio"].astype(str), orientation="h",
        marker_color=TEMA["referencia"], text=t["fuertes"], textposition="outside",
        customdata=np.stack([t["total"], t["pct"]], axis=-1),
        hovertemplate=("<b>%{y}</b><br>%{x} sismos M ≥ 6<br>de %{customdata[0]:,} registros"
                       " (%{customdata[1]:.1f} %)<extra></extra>"),
    ))
    fig.update_yaxes(type="category", title="")
    fig.update_xaxes(title="Sismos de magnitud ≥ 6")
    return estilo(fig, "¿Qué años registraron más sismos de magnitud ≥ 6?",
                  "Ordenado por número de eventos fuertes; el tooltip muestra su proporción (KPI-02).",
                  alto=420)


# ---------------------------------------------------------------- P8 · D1
def fig_calor(tabla: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Heatmap(
        z=tabla.values, x=MESES, y=tabla.index.tolist(), colorscale="Blues",
        colorbar={"title": {"text": "Prom.<br>mensual", "font": {"size": 13}}, "thickness": 14},
        hovertemplate="%{y} · %{x}<br>%{z:.1f} sismos por mes (promedio)<extra></extra>",
        xgap=2, ygap=2,
    ))
    fig.update_yaxes(autorange="reversed", title="Década", type="category")
    fig.update_xaxes(title="Mes (UTC)", side="bottom", tickangle=0)
    return estilo(fig, "¿En qué combinaciones de década y mes se concentran los registros?",
                  "Promedio por año observado: corrige que la década 2020s tenga menos años.", alto=420)


# ---------------------------------------------------------------- Incertidumbre
def fig_incertidumbre(df: pd.DataFrame) -> go.Figure:
    u = df.groupby("decada_txt")["PROFUNDIDAD"].apply(bootstrap_mediana).unstack().reset_index()
    fig = go.Figure(go.Scatter(
        x=u["decada_txt"], y=u["mediana"], mode="lines+markers",
        line={"color": TEMA["secundario"], "width": 2}, marker={"size": 9},
        error_y={"type": "data", "symmetric": False, "array": u["ls"] - u["mediana"],
                 "arrayminus": u["mediana"] - u["li"], "color": TEMA["suave"], "thickness": 1.4, "width": 6},
        customdata=u[["li", "ls", "n"]],
        hovertemplate=("%{x}<br>Mediana %{y:.1f} km<br>IC 95 % [%{customdata[0]:.1f}; "
                       "%{customdata[1]:.1f}]<br>n = %{customdata[2]:,.0f}<extra></extra>"),
    ))
    fig.update_yaxes(title="Profundidad mediana (km)")
    fig.update_xaxes(title="Década")
    return estilo(fig, "¿Qué tan estable es la profundidad mediana por década?",
                  "Barras = IC bootstrap 95 % (1 000 remuestreos). Es incertidumbre muestral, no instrumental.")


# ---------------------------------------------------------------- P2 normalizado
def fig_densidad(df: pd.DataFrame, alto: int = 560) -> go.Figure:
    """Densidad de epicentros (kernel). Responde 'dónde se concentran' sin que la
    superposición de miles de puntos oculte las zonas más activas."""
    d = df.dropna(subset=["LATITUD", "LONGITUD"])
    fig = go.Figure(go.Densitymap(
        lat=d["LATITUD"], lon=d["LONGITUD"], radius=9, colorscale="YlOrRd", opacity=0.8,
        colorbar={"title": {"text": "Densidad<br>relativa", "font": {"size": 13}}, "thickness": 14},
        hoverinfo="skip",
    ))
    fig.update_layout(map={"style": ESTILO_MAPA, "center": {"lat": -9.3, "lon": -75.2}, "zoom": 4.1})
    fig = estilo(fig, alto=alto)
    fig.update_layout(margin={"l": 0, "r": 0, "t": 0, "b": 0})
    return fig


def tabla_geoceldas(df: pd.DataFrame, tam: float = 1.0, top: int = 10) -> pd.DataFrame:
    """Geoceldas de 1°×1°: conteo y porcentaje del total filtrado. No se inventan regiones."""
    d = df.dropna(subset=["LATITUD", "LONGITUD"]).copy()
    d["lat_c"] = np.floor(d["LATITUD"] / tam) * tam
    d["lon_c"] = np.floor(d["LONGITUD"] / tam) * tam
    g = d.groupby(["lat_c", "lon_c"]).agg(
        sismos=("ID", "size"), mag_max=("MAGNITUD", "max"),
        prof_mediana=("PROFUNDIDAD", "median"), fuertes=("es_fuerte", "sum")).reset_index()
    g["pct_total"] = 100 * g["sismos"] / len(d)
    g["celda"] = g.apply(lambda r: f"{abs(r.lat_c)-tam:.0f}–{abs(r.lat_c):.0f}° S · "
                                   f"{abs(r.lon_c)-tam:.0f}–{abs(r.lon_c):.0f}° O", axis=1)
    return g.sort_values("sismos", ascending=False).head(top)
