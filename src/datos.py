"""Carga, preparación y cálculo de KPI del Catálogo Sísmico del Perú 1960–2025.

Todas las reglas de derivación provienen del marco de diseño (Hito 1):
- superficial < 70 km; intermedio 70–299 km; profundo ≥ 300 km
- sismo fuerte = magnitud ≥ 6,0
- el año 2024 no tiene registros: se muestra como vacío, no se interpola.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

RUTA_DATOS = Path(__file__).resolve().parent.parent / "data" / "Catalogo_Sismico.csv"

CATEGORIAS = ["Superficial (<70 km)", "Intermedio (70–299 km)", "Profundo (≥300 km)"]
BANDAS_MAG = ["3,0–3,9", "4,0–4,9", "5,0–5,9", "6,0–6,9", "≥7,0"]
CAMPOS_CLAVE = ["ID", "fecha", "hora", "LATITUD", "LONGITUD", "PROFUNDIDAD", "MAGNITUD"]
ANIO_MIN, ANIO_MAX = 1960, 2025

# Envolvente preliminar (rectángulo) para señalar coordenadas que conviene verificar.
# No es un límite político: es un control de calidad y los puntos NO se eliminan.
ENVOLVENTE = {"lat_min": -20.0, "lat_max": 0.0, "lon_min": -84.0, "lon_max": -66.0}


def _normalizar_fecha_corte(valor: str) -> pd.Timestamp:
    """FECHA_CORTE mezcla AAAAMMDD y AAAADDMM. Regla explícita: si la posición
    del mes es > 12, se interpreta como AAAADDMM."""
    valor = str(valor).strip()
    if len(valor) != 8 or not valor.isdigit():
        return pd.NaT
    anio, b, c = int(valor[:4]), int(valor[4:6]), int(valor[6:])
    mes, dia = (c, b) if b > 12 else (b, c)
    try:
        return pd.Timestamp(year=anio, month=mes, day=dia)
    except ValueError:
        return pd.NaT


def cargar_catalogo(ruta: Path = RUTA_DATOS) -> pd.DataFrame:
    df = pd.read_csv(
        ruta, sep=";",
        dtype={"FECHA_UTC": "string", "HORA_UTC": "string", "FECHA_CORTE": "string"},
    )
    df.columns = [c.strip() for c in df.columns]
    for col in ["ID", "LATITUD", "LONGITUD", "PROFUNDIDAD", "MAGNITUD"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Fecha y hora UTC (HORA_UTC viene sin ceros a la izquierda: se completa a 6 dígitos)
    df["fecha"] = pd.to_datetime(df["FECHA_UTC"], format="%Y%m%d", errors="coerce")
    hora_txt = df["HORA_UTC"].str.strip().str.zfill(6)
    df["hora"] = pd.to_datetime(hora_txt, format="%H%M%S", errors="coerce").dt.time
    df["anio"] = df["fecha"].dt.year.astype("Int64")
    df["mes"] = df["fecha"].dt.month.astype("Int64")
    df["trimestre"] = df["fecha"].dt.quarter.astype("Int64")
    df["decada"] = (df["anio"] // 10 * 10).astype("Int64")
    df["decada_txt"] = df["decada"].astype(str) + "s"

    df["categoria_prof"] = pd.cut(
        df["PROFUNDIDAD"], bins=[-np.inf, 70, 300, np.inf], right=False, labels=CATEGORIAS
    )
    df["banda_mag"] = pd.cut(
        df["MAGNITUD"], bins=[-np.inf, 4, 5, 6, 7, np.inf], right=False, labels=BANDAS_MAG
    )
    df["es_fuerte"] = df["MAGNITUD"] >= 6
    df["es_superficial"] = df["PROFUNDIDAD"] < 70

    df["fecha_corte_norm"] = df["FECHA_CORTE"].map(_normalizar_fecha_corte)
    df["fuera_envolvente"] = ~(
        df["LATITUD"].between(ENVOLVENTE["lat_min"], ENVOLVENTE["lat_max"])
        & df["LONGITUD"].between(ENVOLVENTE["lon_min"], ENVOLVENTE["lon_max"])
    )
    df["completo"] = df[CAMPOS_CLAVE].notna().all(axis=1)
    return df


# ---------------------------------------------------------------- KPI
@dataclass
class Referencias:
    """Referencias históricas anuales (calculadas sobre el catálogo completo)."""
    mediana_anual: float
    p90_anual: float
    fuertes_mediana: float
    fuertes_p90: float
    sup_p10: float
    sup_p90: float
    prof_med_mediana: float
    prof_med_p10: float
    prof_med_p90: float
    magmax_mediana: float
    magmax_p90: float


def referencias_historicas(df: pd.DataFrame) -> Referencias:
    g = df.groupby("anio")
    n = g.size()
    fuertes = g["es_fuerte"].mean() * 100
    sup = g["es_superficial"].mean() * 100
    prof = g["PROFUNDIDAD"].median()
    magmax = g["MAGNITUD"].max()
    return Referencias(
        mediana_anual=n.median(), p90_anual=n.quantile(0.9),
        fuertes_mediana=fuertes.median(), fuertes_p90=fuertes.quantile(0.9),
        sup_p10=sup.quantile(0.1), sup_p90=sup.quantile(0.9),
        prof_med_mediana=prof.median(), prof_med_p10=prof.quantile(0.1), prof_med_p90=prof.quantile(0.9),
        magmax_mediana=magmax.median(), magmax_p90=magmax.quantile(0.9),
    )


def calcular_kpi(df: pd.DataFrame) -> dict:
    """Seis KPI del diccionario de métricas para el contexto de filtro recibido."""
    n = len(df)
    mag_valida = df["MAGNITUD"].notna().sum()
    prof_valida = df["PROFUNDIDAD"].notna().sum()
    anios = df["anio"].nunique()
    return {
        "kpi01_sismos": n,
        "kpi01_promedio_anual": n / anios if anios else np.nan,
        "anios_observados": anios,
        "kpi02_pct_fuertes": 100 * df["es_fuerte"].sum() / mag_valida if mag_valida else np.nan,
        "n_fuertes": int(df["es_fuerte"].sum()),
        "kpi03_pct_superficiales": 100 * df["es_superficial"].sum() / prof_valida if prof_valida else np.nan,
        "kpi04_prof_mediana": df["PROFUNDIDAD"].median(),
        "kpi05_mag_max": df["MAGNITUD"].max(),
        "kpi06_completitud": 100 * df["completo"].mean() if n else np.nan,
    }


def evento_maximo(df: pd.DataFrame) -> pd.Series | None:
    if df.empty:
        return None
    return df.loc[df["MAGNITUD"].idxmax()]


# ---------------------------------------------------------------- tablas agregadas
def serie_anual(df: pd.DataFrame) -> pd.DataFrame:
    """Conteo por año 1960–2025 con los años sin registros como NaN (no cero)."""
    conteo = df.groupby("anio").size()
    return (
        conteo.reindex(range(ANIO_MIN, ANIO_MAX + 1))
        .rename("sismos").rename_axis("anio").reset_index()
    )


def serie_temporal(df: pd.DataFrame, nivel: str) -> pd.DataFrame:
    freq = {"Anual": "YS", "Mensual": "MS", "Diaria": "D"}[nivel]
    s = df.set_index("fecha").resample(freq).size().rename("sismos")
    return s.reset_index()


def composicion_decada(df: pd.DataFrame) -> pd.DataFrame:
    comp = (
        df.groupby(["decada_txt", "categoria_prof"], observed=False).size()
        .rename("sismos").reset_index()
    )
    tot = comp.groupby("decada_txt")["sismos"].transform("sum")
    comp["porcentaje"] = np.where(tot > 0, 100 * comp["sismos"] / tot.replace(0, np.nan), np.nan)
    return comp[tot > 0]


def fuertes_por_anio(df: pd.DataFrame, top: int = 12) -> pd.DataFrame:
    g = df.groupby("anio")
    t = pd.DataFrame({"fuertes": g["es_fuerte"].sum(), "total": g.size()})
    t["pct"] = 100 * t["fuertes"] / t["total"]
    t = t[t["fuertes"] > 0].sort_values(["fuertes", "pct"], ascending=False).head(top)
    return t.reset_index()


def calor_decada_mes(df: pd.DataFrame) -> pd.DataFrame:
    """Promedio de registros por mes y año observado dentro de cada década."""
    por_mes = df.groupby(["decada_txt", "anio", "mes"]).size().rename("sismos").reset_index()
    anios_dec = df.groupby("decada_txt")["anio"].nunique()
    suma = por_mes.groupby(["decada_txt", "mes"])["sismos"].sum().unstack().reindex(columns=range(1, 13))
    return suma.div(anios_dec, axis=0).fillna(0)


def bootstrap_mediana(valores, n_boot: int = 1000, semilla: int = 42) -> pd.Series:
    x = np.asarray(pd.Series(valores).dropna(), dtype=float)
    if len(x) < 5:
        return pd.Series({"mediana": np.median(x) if len(x) else np.nan, "li": np.nan, "ls": np.nan, "n": len(x)})
    rng = np.random.default_rng(semilla)
    est = np.median(rng.choice(x, size=(n_boot, len(x)), replace=True), axis=1)
    return pd.Series({"mediana": np.median(x), "li": np.quantile(est, 0.025),
                      "ls": np.quantile(est, 0.975), "n": len(x)})


def tabla_calidad(df: pd.DataFrame) -> pd.DataFrame:
    anios_sin = sorted(set(range(ANIO_MIN, ANIO_MAX + 1)) - set(df["anio"].dropna().astype(int)))
    formatos_corte = df["FECHA_CORTE"].nunique()
    n_dup = int(df.duplicated(
        subset=["FECHA_UTC", "HORA_UTC", "LATITUD", "LONGITUD", "PROFUNDIDAD", "MAGNITUD"]).sum())
    filas = [
        ("Completitud de campos clave", f"{100 * df['completo'].mean():.2f} %".replace(".", ","),
         "OK" if df["completo"].mean() >= 0.995 else "Alerta",
         "Mantener la tarjeta KPI-06 y validar en cada actualización."),
        ("Eventos repetidos con distinto ID",
         f"{n_dup}", "OK" if n_dup == 0 else "Verificar", "Revisar con la fuente antes de eliminar."),
        ("ID repetidos", f"{int(df['ID'].duplicated().sum())}",
         "OK" if not df["ID"].duplicated().any() else "Alerta", "ID se usa como clave del evento."),
        ("Años sin registros", ", ".join(map(str, anios_sin)) or "Ninguno",
         "Condicionar" if anios_sin else "OK", "Mostrar el vacío; no interpolar ni unir 2023 con 2025."),
        ("Valores distintos de FECHA_CORTE", f"{formatos_corte} (formatos AAAAMMDD y AAAADDMM)",
         "Condicionar", "Normalizado con regla explícita; se conserva el dato original."),
        ("Rango de magnitud", f"{df['MAGNITUD'].min():.1f} – {df['MAGNITUD'].max():.1f}".replace(".", ","), "OK", "Coherente con un catálogo instrumental."),
        ("Rango de profundidad", f"{df['PROFUNDIDAD'].min():.0f} – {df['PROFUNDIDAD'].max():.0f} km", "OK",
         "Focos > 600 km son raros pero posibles en la placa de Nazca."),
        ("Coordenadas fuera de la envolvente preliminar", f"{int(df['fuera_envolvente'].sum())}",
         "Verificar", "Contrastar con la fuente; no se eliminan automáticamente."),
    ]
    return pd.DataFrame(filas, columns=["Control", "Hallazgo", "Estado", "Tratamiento"])
