"""
Dashboard de Satisfação v2 — Shiny for Python (Express)
Execução: shiny run dashboard_shiny.py
Reqs: shiny, shinywidgets, pandas, numpy, plotly, scipy, openpyxl
"""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from scipy.stats import chi2_contingency
from typing import Any

from shiny import reactive
from shiny.express import input, render, ui
from shinywidgets import render_plotly

# Dicionários e pesos de classificação
COLORS: dict[str, str] = {"POSITIVA": "#2ecc71", "NEUTRA": "#95a5a6", "NEGATIVA": "#e74c3c", "PUBLICIDADE": "#3498db"}
TIER_WEIGHTS: dict[str, int] = {"Muito Relevante": 3, "Relevante": 2, "Menos Relevante": 1}
TIER_ORDER: list[str] = ["Muito Relevante", "Relevante", "Menos Relevante", "Null"]
TIER_EMOJI: dict[str, str] = {"Muito Relevante": "🔴", "Relevante": "🟠", "Menos Relevante": "🔵", "Null": "⚪"}
NSS_SCALE: list[list[float | str]] = [[0, "#c0392b"], [0.3, "#e74c3c"], [0.5, "#fdfefe"], [0.7, "#82e0aa"], [1, "#1e8449"]]

def nss_simple(df: pd.DataFrame) -> float:
    """Calcula o Net Sentiment Score bruto (não-espacializado/não-ponderado)."""
    ds = df[df["Classificação"] != "PUBLICIDADE"]
    n = len(ds)
    if n == 0: 
        return 0.0
    return float(((ds["Classificação"] == "POSITIVA").sum() - (ds["Classificação"] == "NEGATIVA").sum()) / n * 100)

def nss_weighted(df: pd.DataFrame) -> float:
    """Calcula o NSS ponderado pela relevância estrutural (Tier) do veículo."""
    ds = df[df["Classificação"] != "PUBLICIDADE"]
    if ds.empty: 
        return 0.0
        
    w = ds["Peso"].sum()
    if w == 0: # Evita div/0 caso haja falha topológica nos dados
        return 0.0 
        
    pos_w = ds.loc[ds["Classificação"] == "POSITIVA", "Peso"].sum()
    neg_w = ds.loc[ds["Classificação"] == "NEGATIVA", "Peso"].sum()
    return float((pos_w - neg_w) / w * 100)

def sent_profile(df_in: pd.DataFrame, col: str, min_n: int = 30) -> pd.DataFrame:
    """Agrega o sentimento baseando-se em uma dimensão analítica (coluna)."""
    p = df_in.groupby(col).agg(
        Total=("Classificação", "count"),
        Positiva=("Classificação", lambda x: (x == "POSITIVA").sum()),
        Neutra=("Classificação", lambda x: (x == "NEUTRA").sum()),
        Negativa=("Classificação", lambda x: (x == "NEGATIVA").sum())
    )
    p = p[p["Total"] >= min_n].copy()
    p["%Pos"] = (p["Positiva"] / p["Total"] * 100).round(1)
    p["%Neg"] = (p["Negativa"] / p["Total"] * 100).round(1)
    p["%Neu"] = (p["Neutra"] / p["Total"] * 100).round(1)
    p["NSS"] = ((p["Positiva"] - p["Negativa"]) / p["Total"] * 100).round(1)
    return p

def nss_matrix(df_in: pd.DataFrame, min_n: int = 30) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Retorna matrizes pivotadas de NSS e Volumes para análise de correlação cruzada."""
    results = []
    for cat in df_in["Categoria"].unique():
        for tier in TIER_ORDER:
            s = df_in[(df_in["Categoria"] == cat) & (df_in["Tier"] == tier)]
            n = len(s)
            nss = ((s["Classificação"].eq("POSITIVA").sum() - s["Classificação"].eq("NEGATIVA").sum()) / n * 100) if n >= min_n else np.nan
            results.append({"Categoria": cat, "Tier": tier, "NSS": nss, "N": n})
            
    r = pd.DataFrame(results)
    nm = r.pivot(index="Categoria", columns="Tier", values="NSS")[TIER_ORDER]
    nn = r.pivot(index="Categoria", columns="Tier", values="N")[TIER_ORDER]
    
    # Ordena pelo volume global de categorias
    idx_order = df_in["Categoria"].value_counts().index
    return nm.reindex(idx_order), nn.reindex(idx_order)

@reactive.calc
def raw_data() -> pd.DataFrame:
    """Pipeline de extração da verdade factual (raw data) do repositório remoto."""
    url = "https://docs.google.com/spreadsheets/d/1LmMi0mTTzRytJno0EHu8P873wcPpQavktO_D_FFXA1E/export?format=xlsx&gid=1312481019"
    df = pd.read_excel(url, engine="openpyxl")
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df["Ano_Mes"] = df["Data"].dt.to_period("M")
    df["Peso"] = df["Tier"].map(TIER_WEIGHTS).fillna(1)
    
    if "Veículo" in df.columns and "Veículo_de_comunicacao" not in df.columns: 
        df = df.rename(columns={"Veículo": "Veículo_de_comunicacao"})
    return df

@reactive.calc
def filt() -> pd.DataFrame:
    """Aplica recortes dimensionais baseados na interface."""
    df = raw_data().copy()
    
    def _safe_filter(val: Any, col: str, is_str: bool = False):
        nonlocal df
        if val:
            if is_str:
                df = df[df[col].str.contains(val.strip(), case=False, na=False)]
            else:
                df = df[df[col].isin(val)]
                
    try:
        if getattr(input, "dates", None) and input.dates():
            df = df[(df["Data"].dt.date >= input.dates()[0]) & (df["Data"].dt.date <= input.dates()[1])]
            
        _safe_filter(getattr(input, "sel_groups", lambda: None)(), "Grupo")
        _safe_filter(getattr(input, "sel_companies", lambda: None)(), "Empresa")
        _safe_filter(getattr(input, "sel_media", lambda: None)(), "Mídia")
        _safe_filter(getattr(input, "sel_tiers", lambda: None)(), "Tier")
        _safe_filter(getattr(input, "sel_cats", lambda: None)(), "Categoria")
        _safe_filter(getattr(input, "veiculo_search", lambda: None)(), "Veículo_de_comunicacao", is_str=True)
        _safe_filter(getattr(input, "programa_search", lambda: None)(), "Programa", is_str=True)
    except Exception as e:
        pass 
        
    return df

@reactive.calc
def sent() -> pd.DataFrame:
    """Gera o subconjunto focado estritamente no sentimento analisável."""
    return filt()[filt()["Classificação"] != "PUBLICIDADE"].copy()

# ==========================================
# Interface (UI) e Componentes Renderizáveis
# ==========================================
ui.page_opts(title="💧 Satisfação — Saneamento", fillable=False) # CORREÇÃO: fillable=False para permitir scroll livre

with ui.sidebar(title="💧 Filtros", width=280, bg="#f8f9fa"):
    @render.ui
    def _d():
        df = raw_data()
        return ui.input_date_range("dates", "Período", start=df["Data"].min().date(), end=df["Data"].max().date())
    @render.ui
    def _g(): return ui.input_selectize("sel_groups", "Grupo", choices=sorted(raw_data()["Grupo"].dropna().unique()), multiple=True)
    @render.ui
    def _e():
        df = raw_data()
        ch = sorted(df[df["Grupo"].isin(input.sel_groups())]["Empresa"].dropna().unique()) if getattr(input, "sel_groups", lambda: None)() else sorted(df["Empresa"].dropna().unique())
        return ui.input_selectize("sel_companies", "Empresa", choices=ch, multiple=True)
    @render.ui
    def _m(): return ui.input_selectize("sel_media", "Mídia", choices=sorted(raw_data()["Mídia"].dropna().unique()), multiple=True)
    @render.ui
    def _t(): return ui.input_selectize("sel_tiers", "Tier", choices=sorted(raw_data()["Tier"].dropna().unique()), multiple=True)
    @render.ui
    def _c(): return ui.input_selectize("sel_cats", "Categoria", choices=sorted(raw_data()["Categoria"].dropna().unique()), multiple=True)
    ui.input_text("veiculo_search", "🔍 Veículo", placeholder="Ex: Globo…")
    ui.input_text("programa_search", "🔍 Programa", placeholder="Ex: Bom Dia…")

ui.h2("💧 Análise de Satisfação — Saneamento")

@render.text
def _sub():
    df = filt()
    if len(df) == 0: return "Nenhum registro."
    return f"{len(df):,} registros · {df['Grupo'].nunique()} grupos · {df['Empresa'].nunique()} empresas · {df['Data'].min().strftime('%b/%Y')} a {df['Data'].max().strftime('%b/%Y')}"

with ui.layout_columns(): # CORREÇÃO: Removido col_widths=(1, 1, 1, 1, 1) para permitir responsividade automática
    with ui.value_box(theme="success"):
        "NSS Simples"
        @render.text
        def _k1(): return f"{nss_simple(filt()):+.1f}"
    with ui.value_box(theme="warning"):
        "NSS Ponderado"
        @render.text
        def _k2(): return f"{nss_weighted(filt()):+.1f}"
    with ui.value_box(theme="success"):
        "% Positivas"
        @render.text
        def _k3():
            ds = sent(); n = len(ds); return f"{(ds['Classificação'] == 'POSITIVA').sum() / n * 100:.1f}%" if n else "—"
    with ui.value_box(theme="danger"):
        "% Negativas"
        @render.text
        def _k4():
            ds = sent(); n = len(ds); return f"{(ds['Classificação'] == 'NEGATIVA').sum() / n * 100:.1f}%" if n else "—"
    with ui.value_box(theme="light"):
        "% Neutras"
        @render.text
        def _k5():
            ds = sent(); n = len(ds); return f"{(ds['Classificação'] == 'NEUTRA').sum() / n * 100:.1f}%" if n else "—"

with ui.navset_card_tab():
    with ui.nav_panel("📈 Temporal"):
        ui.h5("NSS Mensal")
        @render_plotly
        def nss_temporal():
            ds = sent()
            if len(ds) == 0: return go.Figure()
            rows = [{"Data": p.to_timestamp(), "NSS Simples": nss_simple(dm := ds[ds["Ano_Mes"] == p]), "NSS Ponderado": nss_weighted(dm), "N": len(dm)} for p in sorted(ds["Ano_Mes"].unique())]
            ndf = pd.DataFrame(rows); fig = go.Figure()
            fig.add_trace(go.Scatter(x=ndf["Data"], y=ndf["NSS Simples"], mode="lines+markers", name="Simples", line=dict(color=COLORS["POSITIVA"], width=3)))
            fig.add_trace(go.Scatter(x=ndf["Data"], y=ndf["NSS Ponderado"], mode="lines+markers", name="Ponderado", line=dict(color=COLORS["NEGATIVA"], width=3, dash="dash"), marker=dict(symbol="diamond")))
            fig.add_hline(y=0, line_dash="dot", line_color="gray", opacity=0.5)
            fig.update_layout(height=400, template="plotly_white", hovermode="x unified", legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"))
            return fig
            
        with ui.layout_columns():
            with ui.card():
                ui.card_header("Volume")
                @render_plotly
                def _va():
                    ds = sent()
                    if len(ds) == 0: return go.Figure()
                    vol = ds.groupby(["Ano_Mes", "Classificação"]).size().unstack(fill_value=0); vol.index = vol.index.to_timestamp()
                    fig = go.Figure()
                    for c in ["POSITIVA", "NEUTRA", "NEGATIVA"]:
                        if c in vol.columns: fig.add_trace(go.Scatter(x=vol.index, y=vol[c], mode="lines+markers", name=c, line=dict(color=COLORS.get(c), width=2)))
                    fig.update_layout(height=300, template="plotly_white", hovermode="x unified", legend=dict(orientation="h", y=-0.2))
                    return fig
            with ui.card():
                ui.card_header("Proporção (%)")
                @render_plotly
                def _vp():
                    ds = sent()
                    if len(ds) == 0: return go.Figure()
                    vol = ds.groupby(["Ano_Mes", "Classificação"]).size().unstack(fill_value=0); vol.index = vol.index.to_timestamp()
                    vp = vol.div(vol.sum(axis=1), axis=0) * 100; fig = go.Figure()
                    for c in ["POSITIVA", "NEUTRA", "NEGATIVA"]:
                        if c in vp.columns: fig.add_trace(go.Bar(x=vp.index, y=vp[c], name=c, marker_color=COLORS.get(c)))
                    fig.update_layout(barmode="stack", height=300, template="plotly_white", yaxis_range=[0, 100], legend=dict(orientation="h", y=-0.2))
                    return fig

    with ui.nav_panel("🔬 Tier × Classificação"):
        @render.ui
        def _chi():
            ds = sent()
            if len(ds) < 10: 
                return ui.p("Dados insuficientes.")
                
            ct = pd.crosstab(ds["Tier"], ds["Classificação"])
            if "PUBLICIDADE" in ct.columns: 
                ct = ct.drop(columns="PUBLICIDADE")
                
            if ct.shape[0] < 2 or ct.shape[1] < 2:
                return ui.p("Matriz analítica unidimensional: não há graus de liberdade suficientes para o Teste Qui-Quadrado (χ²).", style="color: #e74c3c; font-weight: bold;")
                
            chi2, p, dof, _ = chi2_contingency(ct)
            pt = f"{p:.2e}" if p < 0.001 else f"{p:.4f}"
            
            return ui.layout_columns(
                ui.value_box("χ²", f"{chi2:.1f}", theme="dark"),
                ui.value_box("p-value", pt, theme="dark"),
                ui.value_box("gl", str(dof), theme="dark"),
                ui.value_box("Resultado", "✅ Sig." if p < 0.05 else "❌ Não sig.", theme="dark"),
                col_widths=(1, 1, 1, 1)
            )
            
        ui.h5("Proporção por Tier")
        @render_plotly
        def _tb():
            ds = sent()
            if len(ds) < 10: return go.Figure()
            ct = pd.crosstab(ds["Tier"], ds["Classificação"])
            if "PUBLICIDADE" in ct.columns: ct = ct.drop(columns="PUBLICIDADE")
            cp = ct.div(ct.sum(axis=1), axis=0) * 100; fig = go.Figure()
            for c in ["POSITIVA", "NEUTRA", "NEGATIVA"]:
                if c in cp.columns: fig.add_trace(go.Bar(name=c, y=cp.index, x=cp[c], orientation="h", marker_color=COLORS.get(c), text=[f"{v:.1f}%" for v in cp[c]], textposition="inside"))
            fig.update_layout(barmode="stack", height=280, template="plotly_white", legend=dict(orientation="h", y=-0.2)); return fig
            
        ui.hr(); ui.h5("Heatmap: NSS Categoria × Tier")
        @render_plotly
        def _hm():
            ds = sent()
            if len(ds) < 10: return go.Figure()
            nm, _ = nss_matrix(ds)
            fig = go.Figure(go.Heatmap(z=nm.values, x=nm.columns.tolist(), y=nm.index.tolist(), colorscale=NSS_SCALE, zmid=0, text=nm.values.round(1), texttemplate="%{text:+.1f}", colorbar=dict(title="NSS")))
            fig.update_layout(height=max(450, len(nm) * 38), template="plotly_white", yaxis=dict(autorange="reversed"), margin=dict(l=180)); return fig
            
        ui.hr(); ui.h5("Treemap: Tier × Categoria")
        @render_plotly
        def _tm():
            ds = sent()
            if len(ds) < 10: return go.Figure()
            tm = ds.groupby(["Tier", "Categoria"]).agg(Total=("Classificação", "count"), Positiva=("Classificação", lambda x: (x == "POSITIVA").sum()), Negativa=("Classificação", lambda x: (x == "NEGATIVA").sum())).reset_index()
            tm["NSS"] = ((tm["Positiva"] - tm["Negativa"]) / tm["Total"] * 100).round(1)
            fig = px.treemap(tm, path=["Tier", "Categoria"], values="Total", color="NSS", color_continuous_scale=NSS_SCALE, color_continuous_midpoint=0)
            fig.update_layout(height=550, margin=dict(l=10, r=10, t=10, b=10)); fig.update_traces(textinfo="label+value"); return fig

    with ui.nav_panel("🏷️ Categorias"):
        ui.input_switch("seg_tier_sh", "Segmentar por Tier", value=False)
        ui.input_slider("n_cats_sh", "Categorias", min=5, max=20, value=10)
        @render_plotly
        def _cc():
            ds = sent()
            if len(ds) == 0: return go.Figure()
            if input.seg_tier_sh():
                nm, _ = nss_matrix(ds)
                fig = go.Figure(go.Heatmap(z=nm.values, x=nm.columns.tolist(), y=nm.index.tolist(), colorscale=NSS_SCALE, zmid=0, text=nm.values.round(1), texttemplate="%{text:+.1f}", colorbar=dict(title="NSS")))
                fig.update_layout(height=max(450, len(nm) * 38), template="plotly_white", yaxis=dict(autorange="reversed"))
            else:
                tops = ds["Categoria"].value_counts().head(input.n_cats_sh()).index
                rows = [{"Categoria": c, "N": len(dc := ds[ds["Categoria"] == c]), "NSS": round(((dc["Classificação"] == "POSITIVA").sum() - (dc["Classificação"] == "NEGATIVA").sum()) / len(dc) * 100, 1)} for c in tops]
                cdf = pd.DataFrame(rows).sort_values("NSS")
                fig = go.Figure(go.Bar(x=cdf["NSS"], y=cdf["Categoria"], orientation="h", marker_color=[COLORS["NEGATIVA"] if x < 0 else COLORS["POSITIVA"] for x in cdf["NSS"]], text=[f"{x:+.1f}" for x in cdf["NSS"]], textposition="outside"))
                fig.add_vline(x=0, line_color="black", line_width=1); fig.update_layout(height=max(380, input.n_cats_sh() * 38), template="plotly_white")
            return fig

    with ui.nav_panel("📺 Veículos & Programas"):
        with ui.navset_pill():
            with ui.nav_panel("📰 Veículos"):
                ui.input_select("tier_v", "Tier", choices=TIER_ORDER)
                ui.input_slider("mn_v", "Vol. mínimo", min=10, max=200, value=30)
                @render_plotly
                def _vc():
                    ds = sent()
                    if len(ds) == 0: return go.Figure()
                    pf = sent_profile(ds[ds["Tier"] == input.tier_v()], "Veículo_de_comunicacao", min_n=input.mn_v())
                    if len(pf) == 0: return go.Figure().update_layout(annotations=[dict(text="Sem dados", showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5)])
                    pf = pf.sort_values("Total", ascending=False).head(20).reset_index()
                    fig = go.Figure(go.Bar(y=pf["Veículo_de_comunicacao"], x=pf["NSS"], orientation="h", marker_color=[COLORS["NEGATIVA"] if x < 0 else COLORS["POSITIVA"] for x in pf["NSS"]], text=pf.apply(lambda r: f"{r['NSS']:+.1f} (N={int(r['Total']):,})", axis=1), textposition="outside"))
                    fig.add_vline(x=0, line_width=2, line_color="#2c3e50")
                    fig.update_layout(height=max(400, len(pf) * 30), template="plotly_white", margin=dict(l=10, r=120, t=10, b=30)); return fig
                    
            with ui.nav_panel("🎙️ Programas (Pirâmide)"):
                ui.input_slider("mn_p", "Vol. mínimo", min=10, max=200, value=30)
                @render_plotly
                def _pp():
                    ds = sent()
                    if len(ds) == 0: return go.Figure()
                    pf = sent_profile(ds[ds["Programa"] != "Geral"], "Programa", min_n=input.mn_p())
                    if len(pf) == 0: return go.Figure().update_layout(annotations=[dict(text="Sem dados", showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5)])
                    td = ds[ds["Programa"] != "Geral"].groupby("Programa")["Tier"].agg(lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else "N/A")
                    pf["TD"] = pf.index.map(td)
                    comb = pd.concat([pf.nsmallest(10, "NSS"), pf.nlargest(10, "NSS")]).drop_duplicates().sort_values("NSS").reset_index()
                    comb["Label"] = comb.apply(lambda r: f"{TIER_EMOJI.get(r['TD'], '⚪')} {r['Programa']} (N={int(r['Total']):,})", axis=1)
                    
                    fig = go.Figure()
                    fig.add_trace(go.Bar(y=comb["Label"], x=-comb["%Neg"], orientation="h", name="% Neg", marker_color="#e74c3c", marker_opacity=0.85, text=comb["%Neg"].apply(lambda v: f"{v:.0f}%" if v >= 3 else ""), textposition="inside", textfont=dict(color="white")))
                    fig.add_trace(go.Bar(y=comb["Label"], x=-comb["%Neu"], orientation="h", name="% Neu", marker_color="#bdc3c7", marker_opacity=0.6, text=comb["%Neu"].apply(lambda v: f"{v:.0f}%" if v >= 8 else ""), textposition="inside"))
                    fig.add_trace(go.Bar(y=comb["Label"], x=comb["%Pos"], orientation="h", name="% Pos", marker_color="#2ecc71", marker_opacity=0.85, text=comb["%Pos"].apply(lambda v: f"{v:.0f}%" if v >= 3 else ""), textposition="inside", textfont=dict(color="white")))
                    fig.add_vline(x=0, line_width=2, line_color="#2c3e50")
                    fig.update_layout(height=max(650, len(comb) * 36), barmode="relative", template="plotly_white", xaxis=dict(range=[-105, 105], tickvals=[-100, -75, -50, -25, 0, 25, 50, 75, 100], ticktext=["100%", "75%", "50%", "25%", "0", "25%", "50%", "75%", "100%"]), legend=dict(orientation="h", y=-0.06, x=0.3), margin=dict(l=20, r=20, t=10, b=50))
                    return fig
                ui.p("🔴MR 🟠Rel 🔵LR ⚪Null", style="color:#6c757d;text-align:center;font-size:0.85rem;")

    with ui.nav_panel("🏢 Empresas"):
        ui.input_radio_buttons("vm", "Agrupar:", {"Grupo": "Grupo", "Empresa": "Empresa"}, inline=True)
        ui.input_slider("mn_e", "Vol. mínimo", min=10, max=1000, value=50, step=10)
        @render_plotly
        def _ec():
            ds = sent()
            if len(ds) == 0: return go.Figure()
            pf = sent_profile(ds, input.vm(), min_n=input.mn_e()).reset_index().sort_values("NSS")
            fig = go.Figure(go.Bar(x=pf["NSS"], y=pf[input.vm()], orientation="h", marker_color=[COLORS["NEGATIVA"] if x < 0 else COLORS["POSITIVA"] for x in pf["NSS"]], text=[f"{x:+.1f}" for x in pf["NSS"]], textposition="outside"))
            fig.add_vline(x=0, line_color="black", line_width=1)
            fig.update_layout(height=max(400, len(pf) * 30), template="plotly_white", margin=dict(l=10, r=60, t=10, b=30)); return fig

    with ui.nav_panel("📅 Hipótese Set/2024"):
        @render.ui
        def _per():
            ds = sent()
            if len(ds) == 0: return ui.p("Sem dados.")
            ref = pd.Period("2024-09", freq="M"); dc = ds.copy()
            dc["Per"] = dc["Ano_Mes"].apply(lambda x: "Antes" if x < ref else ("Setembro" if x == ref else "Depois"))
            vals = {}
            for per in ["Antes", "Setembro", "Depois"]:
                dp = dc[dc["Per"] == per]; vals[per] = {"n": len(dp), "nss": round(nss_simple(dp), 1)}
            na, ns, nd = vals["Antes"]["nss"], vals["Setembro"]["nss"], vals["Depois"]["nss"]
            return ui.TagList(
                ui.h5("Hipótese: Mudança em Setembro/2024"),
                ui.p("Antes: início→ago/2024 · Setembro: set/2024 · Depois: out/2024→fim"),
                ui.layout_columns(
                    ui.value_box(f"Antes (N={vals['Antes']['n']:,})", f"{na:+.1f}", theme="success" if na >= 0 else "danger"),
                    ui.value_box(f"Set (N={vals['Setembro']['n']:,})", f"{ns:+.1f}", theme="success" if ns >= 0 else "danger"),
                    ui.value_box(f"Depois (N={vals['Depois']['n']:,})", f"{nd:+.1f}", theme="success" if nd >= 0 else "danger")),
                ui.layout_columns(ui.value_box("Δ Antes→Set", f"{ns-na:+.1f}", theme="light"), ui.value_box("Δ Set→Depois", f"{nd-ns:+.1f}", theme="light")),
                ui.p("⚠️ Set=1 mês. NSS instável. Causalidade deve ser investigada nos recortes espaciais (municípios/polígonos operacionais).", style="color:#6c757d; font-style: italic;"))