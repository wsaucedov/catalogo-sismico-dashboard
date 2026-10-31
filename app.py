"""Dashboard · Catálogo Sísmico Instrumental del Perú 1960–2025 (Hito 3, versión Python + Streamlit).

Ejecutar:  streamlit run app.py
Navegación: Resumen · Temporal · Espacial y profundidad · Calidad del dato · KPI y método
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from src import graficos as G
from src.datos import (CATEGORIAS, ENVOLVENTE, calcular_kpi, calor_decada_mes, cargar_catalogo,
                       composicion_decada, evento_maximo, fuertes_por_anio, referencias_historicas,
                       serie_anual, serie_temporal, tabla_calidad)

st.set_page_config(page_title="Catálogo Sísmico del Perú · 1960–2025", page_icon="🌎",
                   layout="wide", initial_sidebar_state="expanded")

FUENTE = ("Instituto Geofísico del Perú (IGP) · Catálogo Sísmico Instrumental 1960–2025 · "
          "Plataforma Nacional de Datos Abiertos")


def fmt(x, dec=0, suf=""):
    """Formato numérico en español: espacio de miles y coma decimal."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "—"
    s = f"{x:,.{dec}f}".replace(",", " ").replace(".", ",")
    return s + suf


# ======================================================================= estilos
st.markdown("""
<style>
.block-container {padding-top: 3.6rem; padding-bottom: 2rem; max-width: 1500px;}
[data-testid="stSidebar"] {background: #F2F5F7;}
h1, h2, h3 {color: #1B2B38; letter-spacing: -0.01em;}
.encabezado-app {display:flex; justify-content:space-between; align-items:flex-end; gap:1rem;
  border-bottom:1px solid #E6ECF0; padding-bottom:.6rem; margin-bottom:.9rem; flex-wrap:wrap;}
.encabezado-app h1 {font-size:1.8rem; margin:0; padding:0;}
.encabezado-app .sub {color:#3D5161; font-size:1.05rem; margin-top:.15rem;}
.chip {display:inline-block; font-size:.9rem; padding:.18rem .6rem; border-radius:999px;
  background:#E8F1F6; color:#0B4F79; margin:.12rem .25rem .12rem 0; white-space:nowrap;}
.chip.warn {background:#FBEFF5; color:#7D2457;}
.kpi {border:1px solid #E1E8ED; border-radius:10px; padding:.7rem .85rem .65rem; background:#fff;
  min-height:200px; display:flex; flex-direction:column; gap:.15rem;}
.kpi .id {font-size:.82rem; color:#5B6E7C; letter-spacing:.06em; font-weight:600;}
.kpi .lbl {font-size:1.02rem; color:#3D5161; line-height:1.15;}
.kpi .val {font-size:2.05rem; font-weight:700; color:#1B2B38; line-height:1.1; margin-top:.1rem;}
.kpi .ctx {font-size:.9rem; color:#4F6372; line-height:1.25;}
.kpi .estado {margin-top:auto; font-size:.86rem; font-weight:600; padding:.12rem .5rem; border-radius:6px;
  align-self:flex-start;}
.estado.neutro {background:#EEF2F5; color:#3D5161;}
.estado.revisar {background:#FBEFF5; color:#7D2457;}
.estado.ok {background:#E7F4EC; color:#1E6B3A;}
.estado.alerta {background:#FDF1E3; color:#8A4B00;}
.vista {margin:.6rem 0 .1rem;}
.vista .q {font-size:.88rem; color:#1B6F80; font-weight:700; letter-spacing:.04em; text-transform:uppercase;}
.vista .h {font-size:1.25rem; font-weight:700; color:#1B2B38; line-height:1.3; margin:.1rem 0 .1rem;}
.vista .n {font-size:.98rem; color:#3D5161;}
.hallazgos {background:#F5F8FA; border-left:4px solid #0B4F79; border-radius:6px; padding:.8rem 1rem;}
.hallazgos li {margin-bottom:.3rem;}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {font-size:.98rem !important; color:#3D5161 !important;}
[data-testid="stSidebar"] label p, [data-testid="stSidebar"] p {font-size:1rem;}
.hallazgos {font-size:1.08rem;}
.pie {color:#4F6372; font-size:.9rem; border-top:1px solid #E6ECF0; margin-top:1.5rem; padding-top:.6rem;}
</style>
""", unsafe_allow_html=True)


# ======================================================================= datos
@st.cache_data(show_spinner="Cargando catálogo…")
def datos():
    df = cargar_catalogo()
    return df, referencias_historicas(df)


df, REF = datos()
FECHA_CORTE_MAX = df["fecha_corte_norm"].max()
N_REPETIDOS = int(df.duplicated(subset=["FECHA_UTC", "HORA_UTC", "LATITUD", "LONGITUD", "PROFUNDIDAD",
                                        "MAGNITUD"]).sum())
MAG_MIN, MAG_MAX = float(df["MAGNITUD"].min()), float(df["MAGNITUD"].max())

FILTROS_DEF = {"f_anios": (1960, 2025), "f_mag": (MAG_MIN, MAG_MAX), "f_prof": CATEGORIAS.copy()}
for k, v in FILTROS_DEF.items():
    st.session_state.setdefault(k, v)


def restablecer():
    for k, v in FILTROS_DEF.items():
        st.session_state[k] = v if not isinstance(v, list) else v.copy()
    for k in ("sel_mapa", "anio_detalle"):
        st.session_state.pop(k, None)


# ======================================================================= filtros globales
with st.sidebar:
    st.markdown("### Filtros")
    st.caption("Se aplican a **todas** las páginas, KPI y gráficos.")
    st.slider("Años", 1960, 2025, key="f_anios", help="Año de la fecha del evento (UTC).")
    st.slider("Magnitud", MAG_MIN, MAG_MAX, step=0.1, key="f_mag",
              help="Sismo fuerte = magnitud ≥ 6,0 (regla del proyecto).")
    st.multiselect("Profundidad del foco", CATEGORIAS, key="f_prof",
                   help="Superficial < 70 km · Intermedio 70–299 km · Profundo ≥ 300 km")
    st.button("↺ Restablecer filtros", on_click=restablecer, width="stretch")

a0, a1 = st.session_state.f_anios
m0, m1 = st.session_state.f_mag
prof_sel = st.session_state.f_prof or CATEGORIAS
mask = (df["anio"].between(a0, a1) & df["MAGNITUD"].between(m0 - 1e-9, m1 + 1e-9)
        & df["categoria_prof"].isin(prof_sel))
dff = df.loc[mask]

filtros_activos = []
if (a0, a1) != (1960, 2025):
    filtros_activos.append(f"Años {a0}–{a1}")
if (m0, m1) != (MAG_MIN, MAG_MAX):
    filtros_activos.append(f"M {fmt(m0, 1)}–{fmt(m1, 1)}")
if set(prof_sel) != set(CATEGORIAS):
    filtros_activos.append(" + ".join(c.split(" (")[0] for c in prof_sel))

with st.sidebar:
    st.markdown("---")
    st.markdown(f"**Selección actual:** {fmt(len(dff))} de {fmt(len(df))} eventos "
                f"({fmt(100 * len(dff) / len(df), 1)} %)")
    if filtros_activos:
        st.markdown("".join(f"<span class='chip'>{f}</span>" for f in filtros_activos),
                    unsafe_allow_html=True)
    else:
        st.caption("Sin filtros: catálogo completo.")
    st.markdown("---")
    st.caption(f"**Fuente:** {FUENTE}.  \n**Periodo:** 13/01/1960 – 31/12/2025 (UTC).  \n"
               f"**Última fecha de corte:** {FECHA_CORTE_MAX:%d/%m/%Y}.")
    st.caption("Análisis **descriptivo**. No predice sismos ni reemplaza información oficial.")


# ======================================================================= componentes
def encabezado(titulo: str, subtitulo: str):
    chips = "".join(f"<span class='chip'>{f}</span>" for f in filtros_activos) or \
        "<span class='chip'>Catálogo completo</span>"
    if a0 <= 2024 <= a1:
        chips += "<span class='chip warn'>2024 sin registros (no se interpola)</span>"
    st.markdown(f"""<div class="encabezado-app"><div><h1>{titulo}</h1><div class="sub">{subtitulo}</div></div>
    <div>{chips}</div></div>""", unsafe_allow_html=True)


def vista(codigo: str, pregunta: str, hallazgo: str, nota: str = ""):
    """Título de cada gráfico: pregunta analítica (contexto) + hallazgo (mensaje)."""
    st.markdown(f"""<div class="vista"><div class="q">{codigo} · {pregunta}</div>
    <div class="h">{hallazgo}</div>{f'<div class="n">{nota}</div>' if nota else ''}</div>""",
                unsafe_allow_html=True)


def tarjeta(col, kid, etiqueta, valor, contexto, estado, clase):
    col.markdown(f"""<div class="kpi" role="group" aria-label="{etiqueta}: {valor}">
    <div class="id">{kid}</div><div class="lbl">{etiqueta}</div><div class="val">{valor}</div>
    <div class="ctx">{contexto}</div><div class="estado {clase}">{estado}</div></div>""",
                 unsafe_allow_html=True)


def banda_kpi(d: pd.DataFrame, nota: str | None = None):
    k = calcular_kpi(d)
    cols = st.columns(6, gap="small")
    prom = k["kpi01_promedio_anual"]
    tarjeta(cols[0], "KPI-01", "Sismos registrados", fmt(k["kpi01_sismos"]),
            f"{fmt(prom)} por año observado ({k['anios_observados']} años)<br>"
            f"Ref.: mediana anual {fmt(REF.mediana_anual)} · P90 {fmt(REF.p90_anual)}",
            "Promedio sobre P90 · revisar" if prom > REF.p90_anual else "Promedio ≤ P90",
            "revisar" if prom > REF.p90_anual else "neutro")
    v = k["kpi02_pct_fuertes"]
    tarjeta(cols[1], "KPI-02", "Sismos fuertes (M ≥ 6)", fmt(v, 2, " %"),
            f"{k['n_fuertes']} eventos<br>Ref.: mediana anual {fmt(REF.fuertes_mediana, 2)} % · "
            f"P90 {fmt(REF.fuertes_p90, 2)} %",
            "Sobre P90 · revisar" if v > REF.fuertes_p90 else "≤ P90",
            "revisar" if v > REF.fuertes_p90 else "neutro")
    v = k["kpi03_pct_superficiales"]
    fuera = not (REF.sup_p10 <= v <= REF.sup_p90)
    tarjeta(cols[2], "KPI-03", "Sismos superficiales (< 70 km)", fmt(v, 1, " %"),
            f"Rango histórico anual P10–P90:<br>{fmt(REF.sup_p10, 1)}–{fmt(REF.sup_p90, 1)} %",
            "Fuera del rango · revisar" if fuera else "Dentro del rango", "revisar" if fuera else "neutro")
    v = k["kpi04_prof_mediana"]
    fuera = not (REF.prof_med_p10 <= v <= REF.prof_med_p90)
    tarjeta(cols[3], "KPI-04", "Profundidad mediana", fmt(v, 0, " km"),
            f"Ref.: mediana de medianas anuales {fmt(REF.prof_med_mediana, 1)} km<br>"
            f"P10–P90: {fmt(REF.prof_med_p10, 1)}–{fmt(REF.prof_med_p90, 1)} km",
            "Fuera del rango · revisar" if fuera else "Dentro del rango", "revisar" if fuera else "neutro")
    v = k["kpi05_mag_max"]
    ev = evento_maximo(d)
    ctx = (f"{ev['fecha']:%d/%m/%Y} · {fmt(ev['PROFUNDIDAD'])} km · "
           f"({fmt(ev['LATITUD'], 2)}; {fmt(ev['LONGITUD'], 2)})" if ev is not None else "")
    tarjeta(cols[4], "KPI-05", "Magnitud máxima", fmt(v, 1),
            f"{ctx}<br>Ref.: mediana de máximos anuales {fmt(REF.magmax_mediana, 1)} · P90 {fmt(REF.magmax_p90, 1)}",
            "≥ P90 · extremo" if v >= REF.magmax_p90 else "< P90",
            "revisar" if v >= REF.magmax_p90 else "neutro")
    v = k["kpi06_completitud"]
    tarjeta(cols[5], "KPI-06", "Completitud de campos clave", fmt(v, 1, " %"),
            "ID, fecha, hora, latitud, longitud, profundidad y magnitud<br>Meta 100 % · alerta < 99,5 %",
            "Cumple la meta" if v >= 99.5 else "Alerta de calidad", "ok" if v >= 99.5 else "alerta")
    st.caption(nota or "Los umbrales son **de revisión analítica**, no alertas sísmicas. "
               "Los KPI no tienen dirección deseada: un valor mayor no es «mejor» ni «peor».")


def mostrar(fig, key=None, **kw):
    return st.plotly_chart(fig, width="stretch", config=G.CONFIG_PLOTLY, key=key, **kw)


def sin_datos() -> bool:
    if dff.empty:
        st.warning("La selección no contiene registros. Amplíe los filtros o use «Restablecer filtros».")
        return True
    return False


def promedio_decada(d: pd.DataFrame, dec: str) -> float:
    x = d[d["decada_txt"] == dec]
    return len(x) / x["anio"].nunique() if len(x) else np.nan


# ======================================================================= páginas
def pagina_resumen():
    encabezado("Sismicidad registrada en el Perú, 1960–2025",
               "Panorama para priorizar periodos y zonas de revisión técnica · análisis descriptivo")
    if sin_datos():
        return
    banda_kpi(dff)

    anual = serie_anual(dff)
    sobre = anual.loc[anual["sismos"] > REF.p90_anual, "anio"].astype(int).tolist()
    col1, col2 = st.columns([1.25, 1], gap="large")
    with col1:
        cel = G.tabla_geoceldas(dff, top=3)
        top_txt = cel.iloc[0]["celda"] if len(cel) else "—"
        vista("P2 · D2", "¿Dónde se concentran los epicentros?",
              f"La mayor concentración está en la celda {top_txt} "
              f"({fmt(cel.iloc[0]['pct_total'], 1)} % de los eventos filtrados)" if len(cel) else "Sin datos",
              "Tamaño = magnitud · color = profundidad del foco. Detalle y selección por área en «Espacial».")
        mostrar(G.fig_mapa(dff, alto=520), key="mapa_resumen")
    with col2:
        vista("P1 · D1", "¿Cómo evolucionó el número anual de registros?",
              f"{len(sobre)} años superan el umbral de revisión (P90 = {fmt(REF.p90_anual)})"
              if sobre else "Ningún año de la selección supera el P90 histórico",
              "Puntos magenta = sobre el P90. El aumento refleja sobre todo mayor cobertura instrumental.")
        mostrar(G.fig_anual(anual, REF.mediana_anual, REF.p90_anual), key="anual_resumen")
        comp = composicion_decada(dff)
        sup = comp[comp["categoria_prof"] == CATEGORIAS[0]].set_index("decada_txt")["porcentaje"]
        vista("P6 · D3", "¿Cómo cambió la composición por profundidad?",
              f"Los superficiales son mayoría en todas las décadas ({fmt(sup.min(), 0)}–{fmt(sup.max(), 0)} %)"
              if len(sup) and sup.min() > 50 else "Composición por década",
              "Barras al 100 %: compara proporciones, no volumen.")
        fig = G.fig_composicion(comp)
        fig.update_layout(height=300)
        mostrar(fig, key="comp_resumen")

    # Hallazgos (narrativa: contexto → evidencia → hallazgo → recomendación)
    p60, p10 = promedio_decada(dff, "1960s"), promedio_decada(dff, "2010s")
    k = calcular_kpi(dff)
    puntos = []
    if not np.isnan(p60) and not np.isnan(p10) and p60 > 0:
        puntos.append(f"<b>Volumen:</b> de ~{fmt(p60)} registros por año en los 60 a ~{fmt(p10)} en los 2010 "
                      f"(×{fmt(p10 / p60, 1)}). Es un cambio de <i>detección</i>, no evidencia de que «tiembla más».")
    if sobre:
        puntos.append(f"<b>Periodos a priorizar (D1):</b> {', '.join(map(str, sobre))}.")
    if len(sup):
        puntos.append(f"<b>Perfil de profundidad (D3):</b> {fmt(k['kpi03_pct_superficiales'], 1)} % de focos "
                      f"superficiales; la década con menor proporción es {sup.idxmin()} ({fmt(sup.min(), 0)} %).")
    ev = evento_maximo(dff)
    if ev is not None:
        puntos.append(f"<b>Evento extremo (D4):</b> M {fmt(ev['MAGNITUD'], 1)} el {ev['fecha']:%d/%m/%Y} "
                      f"a {fmt(ev['PROFUNDIDAD'])} km; {k['n_fuertes']} eventos M ≥ 6 en la selección.")
    puntos.append(f"<b>Calidad (D5):</b> no hay registros de 2024 y existen {N_REPETIDOS} eventos repetidos con distinto ID; "
                  "condicionar comparaciones recientes y verificar con la fuente (ver «Calidad del dato»).")
    st.markdown("#### Hallazgos y recomendación")
    st.markdown("<div class='hallazgos'><ul>" + "".join(f"<li>{p}</li>" for p in puntos) +
                "</ul><b>Recomendación:</b> revisar primero los años sobre el P90 y las celdas con mayor "
                "concentración, separando el efecto de cobertura de la red antes de comparar periodos.</div>",
                unsafe_allow_html=True)


def _al_seleccionar_anio():
    ev = st.session_state.get("sel_anual")
    try:
        pts = ev["selection"]["points"]
        if pts:
            st.session_state["anio_detalle"] = int(pts[0]["x"])
    except (KeyError, TypeError, IndexError):
        pass


def pagina_temporal():
    encabezado("Análisis temporal", "D1 · priorizar periodos atípicos — D4 · revisar años con eventos fuertes")
    if sin_datos():
        return
    anual = serie_anual(dff)
    anios_disp = sorted(dff["anio"].dropna().astype(int).unique().tolist())
    if st.session_state.get("anio_detalle") not in anios_disp:
        st.session_state["anio_detalle"] = int(anual.loc[anual["sismos"].idxmax(), "anio"])

    col1, col2 = st.columns([1.6, 1], gap="large")
    with col1:
        sobre = anual.loc[anual["sismos"] > REF.p90_anual, "anio"].astype(int).tolist()
        maxi = anual.loc[anual["sismos"].idxmax()]
        vista("P1 · D1", "¿Cómo ha evolucionado la cantidad anual de sismos registrados?",
              f"El máximo es {int(maxi['anio'])} con {fmt(maxi['sismos'])} registros; "
              f"{len(sobre)} años superan el P90",
              "Haga clic en un punto para ver el detalle del año a la derecha.")
        mostrar(G.fig_anual(anual, REF.mediana_anual, REF.p90_anual, st.session_state["anio_detalle"]),
                key="sel_anual", on_select=_al_seleccionar_anio, selection_mode="points")
    with col2:
        anio = st.selectbox("Año en detalle", anios_disp, key="anio_detalle")
        da = dff[dff["anio"] == anio]
        prev = dff[dff["anio"] == anio - 1]
        ka = calcular_kpi(da)
        st.markdown(f"<div class='vista'><div class='q'>Detalle · {anio}</div>"
                    f"<div class='h'>{fmt(len(da))} sismos registrados</div></div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2, gap="small")
        var = (f"{'+' if len(da) >= len(prev) else '−'}{fmt(abs(len(da) - len(prev)))} vs {anio - 1}"
               if len(prev) else f"{anio - 1}: sin registros")
        sobre_p90 = len(da) > REF.p90_anual
        tarjeta(c1, "KPI-01", "Sismos del año", fmt(len(da)),
                f"{var}<br>×{fmt(len(da) / REF.mediana_anual, 2)} la mediana histórica",
                "Sobre P90 · priorizar" if sobre_p90 else "≤ P90", "revisar" if sobre_p90 else "neutro")
        v = ka["kpi02_pct_fuertes"]
        tarjeta(c2, "KPI-02", "Sismos fuertes (M ≥ 6)", fmt(v, 2, " %"),
                f"{ka['n_fuertes']} eventos · máx. M {fmt(ka['kpi05_mag_max'], 1)}<br>"
                f"Prof. mediana {fmt(ka['kpi04_prof_mediana'])} km",
                "Sobre P90 · revisar" if v > REF.fuertes_p90 else "≤ P90",
                "revisar" if v > REF.fuertes_p90 else "neutro")
        st.caption("Eventos más fuertes del año")
        top = da.nlargest(5, "MAGNITUD")[["fecha", "MAGNITUD", "PROFUNDIDAD", "LATITUD", "LONGITUD"]]
        top["fecha"] = top["fecha"].dt.strftime("%d/%m/%Y")
        st.dataframe(top.rename(columns={"fecha": "Fecha (UTC)", "MAGNITUD": "Mag.", "PROFUNDIDAD": "Prof. (km)",
                                         "LATITUD": "Lat.", "LONGITUD": "Lon."}),
                     hide_index=True, width="stretch", height=213)

    col3, col4 = st.columns(2, gap="large")
    with col3:
        fz = fuertes_por_anio(dff)
        if len(fz):
            r = fz.iloc[0]
            vista("P7 · D4", "¿Qué años registraron más sismos de magnitud ≥ 6?",
                  f"{int(r['anio'])} encabeza con {int(r['fuertes'])} eventos M ≥ 6",
                  "En los años 60 la proporción de fuertes es alta porque la red casi solo detectaba sismos grandes.")
            mostrar(G.fig_fuertes(fz), key="fuertes")
        else:
            vista("P7 · D4", "¿Qué años registraron más sismos de magnitud ≥ 6?",
                  "La selección no contiene eventos de magnitud ≥ 6")
    with col4:
        calor = calor_decada_mes(dff)
        mx = calor.stack().idxmax()
        vista("P8 · D1", "¿En qué combinaciones de década y mes se concentran los registros?",
              f"La intensidad crece por década; el valor más alto es {mx[0]} · {G.MESES[mx[1] - 1]}",
              "Promedio mensual por año observado (corrige que 2020s tenga solo 5 años con datos).")
        mostrar(G.fig_calor(calor), key="calor")

    with st.expander("Serie a otra escala temporal (anual · mensual · diaria)"):
        dias = (a1 - a0 + 1) * 365
        nivel = st.segmented_control("Granularidad", ["Automática", "Anual", "Mensual", "Diaria"],
                                     default="Automática", key="gran")
        nivel = nivel or "Automática"
        if nivel == "Automática":
            nivel = "Anual" if dias > 730 else "Mensual"
        if nivel == "Diaria" and dias > 366:
            st.info("La vista diaria en un periodo largo oculta el patrón; reduzca el rango de años.")
        mostrar(G.fig_temporal(serie_temporal(dff, nivel), nivel), key="temporal")


def pagina_espacial():
    encabezado("Análisis espacial y de profundidad",
               "D2 · concentraciones espaciales — D3 · perfil de profundidad")
    if sin_datos():
        return
    col_m, col_c = st.columns([1.5, 1], gap="large")
    with col_c:
        modo = st.segmented_control("Representación del mapa", ["Epicentros", "Densidad"],
                                    default="Epicentros", key="modo_mapa",
                                    help="«Densidad» evita que la superposición de puntos oculte las zonas más activas.")
        modo = modo or "Epicentros"
    sel_ids = None
    with col_m:
        if modo == "Epicentros":
            vista("P2 · D2", "¿Dónde se concentran los epicentros y cómo varían por magnitud y profundidad?",
                  "Los focos superficiales bordean la costa y los intermedios/profundos avanzan hacia el este",
                  "Use la herramienta <b>lazo</b> o <b>caja</b> del mapa para seleccionar un área: "
                  "los KPI y gráficos de esta página se recalculan para esa zona.")
            ev = mostrar(G.fig_mapa(dff, alto=560, seleccionable=True), key="sel_mapa",
                         on_select="rerun", selection_mode=("lasso", "box"))
            try:
                pts = ev.selection.points if ev else []
                if pts:
                    sel_ids = {int(float(p["customdata"][0])) for p in pts if p.get("customdata") is not None}
            except AttributeError:
                sel_ids = None
        else:
            vista("P2 · D2", "¿Dónde se concentran los epicentros?",
                  "La densidad resalta los núcleos de actividad que el mapa de puntos satura",
                  "Estimación de densidad de kernel sobre las coordenadas del epicentro (sin magnitud).")
            mostrar(G.fig_densidad(dff, alto=560), key="dens")
    with col_c:
        cel = G.tabla_geoceldas(dff, top=8)
        st.markdown("<div class='vista'><div class='q'>Geoceldas 1° × 1°</div>"
                    "<div class='h'>Áreas con más registros</div>"
                    "<div class='n'>Celdas regulares (no regiones políticas). % sobre la selección.</div></div>",
                    unsafe_allow_html=True)
        st.dataframe(
            cel[["celda", "sismos", "pct_total", "fuertes", "mag_max", "prof_mediana"]].rename(columns={
                "celda": "Celda", "sismos": "Sismos", "pct_total": "% total", "fuertes": "M≥6",
                "mag_max": "M máx.", "prof_mediana": "Prof. med. (km)"}),
            hide_index=True, width="stretch",
            column_config={"% total": st.column_config.ProgressColumn(format="%.1f %%", min_value=0,
                                                                       max_value=float(cel["pct_total"].max()))})

    dsel = dff[dff["ID"].isin(sel_ids)] if sel_ids else dff
    if sel_ids:
        c1, c2 = st.columns([4, 1])
        c1.info(f"**Área seleccionada en el mapa:** {fmt(len(dsel))} eventos. KPI y gráficos inferiores "
                "corresponden solo a esa área.")
        c2.button("Quitar selección", on_click=lambda: st.session_state.pop("sel_mapa", None), width="stretch")
    banda_kpi(dsel, "KPI calculados para " + ("el área seleccionada en el mapa." if sel_ids else
                                               "los filtros actuales. Seleccione un área en el mapa para comparar."))

    c1, c2 = st.columns(2, gap="large")
    with c1:
        p_fuerte = 100 * dsel["es_fuerte"].mean()
        vista("P3 · D2/D4", "¿Cómo se distribuyen las magnitudes?",
              f"La mayoría está entre M 4 y 5; solo el {fmt(p_fuerte, 2)} % alcanza M ≥ 6",
              "Eje Y logarítmico (declarado) para que la cola de eventos fuertes sea visible.")
        mostrar(G.fig_hist_magnitud(dsel), key="hist")
    with c2:
        vista("P4 · D2/D3", "¿Cómo se distribuye la profundidad y qué atípicos presenta?",
              f"La mediana es {fmt(dsel['PROFUNDIDAD'].median())} km; el foco más profundo llega a {fmt(dsel['PROFUNDIDAD'].max())} km",
              "Eje invertido: la profundidad crece hacia abajo. Líneas en los cortes de 70 y 300 km.")
        mostrar(G.fig_caja_profundidad(dsel), key="caja")
    c3, c4 = st.columns(2, gap="large")
    with c3:
        r = dsel[["PROFUNDIDAD", "MAGNITUD"]].corr(method="spearman").iloc[0, 1] if len(dsel) > 3 else np.nan
        vista("P5 · D2", "¿Existe relación entre profundidad y magnitud?",
              f"No hay una relación monótona fuerte (ρ de Spearman = {fmt(r, 2)})",
              "Cada punto es un evento; la transparencia permite ver densidad.")
        mostrar(G.fig_dispersion(dsel), key="disp")
    with c4:
        vista("Incertidumbre · D3", "¿Qué tan estable es la profundidad mediana por década?",
              "Los intervalos se estrechan cuando hay más registros",
              "IC bootstrap 95 % (1 000 remuestreos). Es incertidumbre muestral, no del instrumento.")
        mostrar(G.fig_incertidumbre(dsel), key="ic")

    if sel_ids:
        st.download_button("Descargar eventos del área seleccionada (CSV)",
                           dsel.drop(columns=["hora"]).to_csv(index=False, sep=";").encode("utf-8-sig"),
                           "eventos_area_seleccionada.csv", "text/csv")


def pagina_calidad():
    encabezado("Calidad del dato", "D5 · aceptar, condicionar o detener una interpretación")
    k = calcular_kpi(df)
    c1, c2, c3, c4 = st.columns(4)
    tarjeta(c1, "KPI-06", "Completitud de campos clave", fmt(k["kpi06_completitud"], 1, " %"),
            "Catálogo completo · meta 100 %", "Cumple la meta", "ok")
    tarjeta(c2, "Continuidad", "Años sin registros", "2024",
            "Se muestra como vacío en las series; no se interpola", "Condicionar", "alerta")
    n_dup = N_REPETIDOS
    tarjeta(c3, "Unicidad", "Eventos repetidos con distinto ID", fmt(n_dup),
            "Misma fecha, hora, posición, profundidad y magnitud", "Verificar con la fuente", "revisar")
    tarjeta(c4, "Rangos", "Coordenadas fuera de la envolvente", fmt(int(df["fuera_envolvente"].sum())),
            f"Lat {ENVOLVENTE['lat_min']:.0f}° a {ENVOLVENTE['lat_max']:.0f}° · "
            f"Lon {ENVOLVENTE['lon_min']:.0f}° a {ENVOLVENTE['lon_max']:.0f}°", "Verificar", "revisar")

    st.markdown("#### Controles aplicados")
    tq = tabla_calidad(df)
    st.dataframe(tq, hide_index=True, width="stretch",
                 column_config={"Estado": st.column_config.TextColumn(width="small")})
    st.caption("Regla de decisión (D5): **Aceptar** si todos los controles están en OK; **Condicionar** la "
               "interpretación cuando hay vacíos o formatos mezclados (declararlo en el análisis); **Detener** si "
               "la completitud baja de 99,5 %.")

    t1, t2, t3 = st.tabs(["Eventos repetidos", "Fuera de la envolvente", "Fecha de corte"])
    with t1:
        cols = ["FECHA_UTC", "HORA_UTC", "LATITUD", "LONGITUD", "PROFUNDIDAD", "MAGNITUD"]
        rep = df[df.duplicated(subset=cols, keep=False)].sort_values(cols + ["ID"])
        st.dataframe(rep[["ID"] + cols], hide_index=True, width="stretch")
        st.caption("Se conservan en el análisis hasta confirmar con el IGP si son duplicados de carga.")
    with t2:
        fe = df[df["fuera_envolvente"]]
        st.dataframe(fe[["ID", "fecha", "LATITUD", "LONGITUD", "PROFUNDIDAD", "MAGNITUD"]], hide_index=True,
                     width="stretch", column_config={"fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY")})
        st.caption("La envolvente es un rectángulo de control, no un límite político. Los puntos no se eliminan.")
    with t3:
        fc = (df.groupby(["FECHA_CORTE", "fecha_corte_norm"]).size().rename("registros").reset_index()
              .rename(columns={"FECHA_CORTE": "Valor original", "fecha_corte_norm": "Fecha normalizada"}))
        st.dataframe(fc, hide_index=True, width="stretch",
                     column_config={"Fecha normalizada": st.column_config.DateColumn(format="DD/MM/YYYY")})
        st.caption("Regla: si los dígitos 5–6 son mayores que 12, el valor se interpreta como AAAADDMM.")

    st.markdown("#### Datos de la selección actual")
    st.download_button(f"Descargar {fmt(len(dff))} eventos filtrados (CSV)",
                       dff.drop(columns=["hora"]).to_csv(index=False, sep=";").encode("utf-8-sig"),
                       "catalogo_filtrado.csv", "text/csv")


def pagina_metodo():
    encabezado("KPI, método y validación", "Diccionario de métricas y valores de referencia para contrastar con Power BI")
    st.markdown("""
**Problema.** Transformar 24 289 registros instrumentales (1960–2025) en información comprensible para
identificar periodos atípicos, caracterizar la distribución espacial y el perfil de profundidad, y evaluar la
calidad del dato antes de interpretar cambios. **Usuario:** analista de monitoreo sísmico o de gestión del
riesgo. **Límite:** el tablero es descriptivo; no pronostica sismos ni emite alertas.
""")
    k_all, k_f = calcular_kpi(df), calcular_kpi(dff)
    filas = [
        ("KPI-01", "Sismos registrados", "COUNT(ID)", "eventos", k_all["kpi01_sismos"], k_f["kpi01_sismos"],
         f"Mediana anual {fmt(REF.mediana_anual)} · P90 {fmt(REF.p90_anual, 1)}", "P1 · D1",
         "Sismos = COUNTROWS(Sismos)"),
        ("KPI-02", "% sismos fuertes", "100·COUNT(M≥6)/COUNT(M válida)", "%", k_all["kpi02_pct_fuertes"],
         k_f["kpi02_pct_fuertes"], f"Mediana anual {fmt(REF.fuertes_mediana, 2)} % · P90 {fmt(REF.fuertes_p90, 2)} %",
         "P7 · D4", "% Fuertes = DIVIDE(CALCULATE([Sismos], Sismos[MAGNITUD] >= 6), [Sismos])"),
        ("KPI-03", "% sismos superficiales", "100·COUNT(prof<70)/COUNT(prof válida)", "%",
         k_all["kpi03_pct_superficiales"], k_f["kpi03_pct_superficiales"],
         f"P10–P90 anual {fmt(REF.sup_p10, 2)}–{fmt(REF.sup_p90, 2)} %", "P6 · D3",
         "% Superficiales = DIVIDE(CALCULATE([Sismos], Sismos[PROFUNDIDAD] < 70), [Sismos])"),
        ("KPI-04", "Profundidad mediana", "MEDIAN(prof)", "km", k_all["kpi04_prof_mediana"],
         k_f["kpi04_prof_mediana"], f"Mediana de medianas anuales {fmt(REF.prof_med_mediana, 1)} km", "P4 · D3",
         "Prof. mediana = MEDIAN(Sismos[PROFUNDIDAD])"),
        ("KPI-05", "Magnitud máxima", "MAX(mag)", "magnitud", k_all["kpi05_mag_max"], k_f["kpi05_mag_max"],
         f"Mediana de máximos anuales {fmt(REF.magmax_mediana, 1)} · P90 {fmt(REF.magmax_p90, 1)}", "P2/P3 · D2",
         "Mag. máxima = MAX(Sismos[MAGNITUD])"),
        ("KPI-06", "Completitud campos clave", "100·filas completas/filas", "%", k_all["kpi06_completitud"],
         k_f["kpi06_completitud"], "Meta 100 % · alerta < 99,5 %", "Calidad · D5",
         "Completitud = DIVIDE(COUNTROWS(FILTER(Sismos, NOT ISBLANK(Sismos[MAGNITUD]) && …)), [Sismos])"),
    ]
    t = pd.DataFrame(filas, columns=["ID", "KPI", "Fórmula", "Unidad", "Catálogo completo", "Selección actual",
                                     "Referencia histórica", "Pregunta · decisión", "Equivalente DAX (Power BI)"])
    st.dataframe(t, hide_index=True, width="stretch",
                 column_config={"Catálogo completo": st.column_config.NumberColumn(format="%.2f"),
                                "Selección actual": st.column_config.NumberColumn(format="%.2f")})
    st.caption("La columna «Catálogo completo» es el valor de validación: las medidas DAX de Power BI deben "
               "reproducirlo sin filtros (24 289 · 1,25 % · 64,10 % · 48 km · 8,4 · 100 %).")

    st.markdown("#### Reglas de derivación")
    st.markdown("""
- **Fecha** desde `FECHA_UTC` (AAAAMMDD) · **hora** desde `HORA_UTC` completada a 6 dígitos. Ambas en UTC, no hora local.
- **Categoría de profundidad:** superficial < 70 km · intermedio 70–299 km · profundo ≥ 300 km.
- **Sismo fuerte:** magnitud ≥ 6,0. **Década:** ⌊año/10⌋·10.
- **Referencias históricas:** percentiles sobre los 65 años con registros (interpolación lineal; 2024 excluido por no tener datos).
- **Incertidumbre:** IC bootstrap 95 % de la mediana de profundidad por década (1 000 remuestreos, semilla 42).
""")
    st.markdown("#### Matriz de preguntas")
    st.dataframe(pd.DataFrame([
        ("P1", "¿Cómo evolucionó la cantidad anual de sismos?", "Línea + referencias", "Temporal · Resumen", "D1"),
        ("P2", "¿Dónde se concentran los epicentros?", "Mapa de símbolos / densidad + geoceldas", "Espacial · Resumen", "D2"),
        ("P3", "¿Cómo se distribuyen las magnitudes?", "Histograma (eje log)", "Espacial", "D2/D4"),
        ("P4", "¿Cómo se distribuye la profundidad?", "Diagrama de caja por década", "Espacial", "D2/D3"),
        ("P5", "¿Hay relación profundidad–magnitud?", "Dispersión", "Espacial", "D2"),
        ("P6", "¿Cómo cambió la composición por profundidad?", "Barras 100 %", "Resumen", "D3"),
        ("P7", "¿Qué años tuvieron más sismos M ≥ 6?", "Barras horizontales ordenadas", "Temporal", "D4"),
        ("P8", "¿Qué combinaciones década–mes concentran registros?", "Mapa de calor", "Temporal", "D1"),
    ], columns=["ID", "Pregunta", "Gráfico", "Página", "Decisión"]), hide_index=True, width="stretch")


# ======================================================================= navegación
pg = st.navigation([
    st.Page(pagina_resumen, title="Resumen", icon=":material/dashboard:", default=True),
    st.Page(pagina_temporal, title="Temporal", icon=":material/timeline:", url_path="temporal"),
    st.Page(pagina_espacial, title="Espacial y profundidad", icon=":material/public:", url_path="espacial"),
    st.Page(pagina_calidad, title="Calidad del dato", icon=":material/fact_check:", url_path="calidad"),
    st.Page(pagina_metodo, title="KPI y método", icon=":material/menu_book:", url_path="metodo"),
], position="top")
pg.run()

st.markdown(f"<div class='pie'>Fuente: {FUENTE}. Fecha de corte más reciente del archivo: "
            f"{FECHA_CORTE_MAX:%d/%m/%Y}. Dashboard descriptivo elaborado para el curso Visualización de Datos · "
            "Walter Saucedo Vega.</div>", unsafe_allow_html=True)
