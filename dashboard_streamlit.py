"""
Dashboard de Satisfação v2 — Streamlit
═══════════════════════════════════════
Atualizado com drill-down de Veículo, Programa, Categoria × Tier.
Refatorado para utilizar o tema nativo do Streamlit (.streamlit/config.toml)

Execução: streamlit run dashboard_streamlit.py
Reqs: streamlit, pandas, numpy, plotly, scipy, openpyxl
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from scipy.stats import chi2_contingency

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO
# ═══════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Satisfação — Saneamento",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

COLORS = {
    "POSITIVA": "#2ecc71",
    "NEUTRA": "#95a5a6",
    "NEGATIVA": "#e74c3c",
    "PUBLICIDADE": "#3498db",
    "accent": "#f39c12",
}

TIER_WEIGHTS = {"Muito Relevante": 3, "Relevante": 2, "Menos Relevante": 1}
TIER_ORDER = ["Muito Relevante", "Relevante", "Menos Relevante", "Null"]

TIER_COLORS = {
    "Muito Relevante": "#e74c3c",
    "Relevante": "#f39c12",
    "Menos Relevante": "#3498db",
    "Null": "#95a5a6",
}

TIER_EMOJI = {
    "Muito Relevante": "🔴",
    "Relevante": "🟠",
    "Menos Relevante": "🔵",
    "Null": "⚪",
}

NSS_COLORSCALE = [
    [0.0, "#c0392b"],
    [0.3, "#e74c3c"],
    [0.5, "#fdfefe"],
    [0.7, "#82e0aa"],
    [1.0, "#1e8449"],
]


# ═══════════════════════════════════════════════════════════════════════════
# CSS (Apenas componentes customizados)
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
    /* ── KPI cards ─────────────────────────────────────── */
    .kpi-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 12px; padding: 1.2rem 1rem; text-align: center;
        border-left: 4px solid #3498db;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }
    .kpi-card h2 { margin: 0; font-size: 2rem; font-weight: 700; color: #2c3e50 !important; }
    .kpi-card p  { margin: 0.2rem 0 0 0; font-size: 0.85rem; color: #6c757d !important; }
    .kpi-pos { border-left-color: #2ecc71; }
    .kpi-neg { border-left-color: #e74c3c; }
    .kpi-neu { border-left-color: #95a5a6; }
    
    /* ── Stat boxes ────────────────────────────────────── */
    .stat-box {
        background: #2c3e50; color: white !important; border-radius: 10px;
        padding: 1rem; text-align: center; margin-bottom: 0.5rem;
    }
    .stat-box .value { font-size: 1.6rem; font-weight: 700; color: white !important; }
    .stat-box .label { font-size: 0.75rem; opacity: 0.8; color: white !important; }
    
    /* ── Tabs ──────────────────────────────────────────── */
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0; padding: 8px 20px; font-weight: 600;
    }
    
    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# FUNÇÕES
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600, show_spinner="Carregando dados…")
def load_data() -> pd.DataFrame:
    url = (
        "https://docs.google.com/spreadsheets/d/"
        "1LmMi0mTTzRytJno0EHu8P873wcPpQavktO_D_FFXA1E/"
        "export?format=xlsx&gid=1312481019"
    )
    df = pd.read_excel(url, engine="openpyxl")
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df["Ano_Mes"] = df["Data"].dt.to_period("M")
    df["Peso"] = df["Tier"].map(TIER_WEIGHTS).fillna(1)
    
    # Normalizar nome da coluna (local = "Veículo", Google Sheets = "Veículo_de_comunicacao")
    if "Veículo" in df.columns and "Veículo_de_comunicacao" not in df.columns:
        df = df.rename(columns={"Veículo": "Veículo_de_comunicacao"})
    return df


def nss_simple(df: pd.DataFrame) -> float:
    ds = df[df["Classificação"] != "PUBLICIDADE"]
    n = len(ds)
    if n == 0:
        return 0.0
    return ((ds["Classificação"] == "POSITIVA").sum() - (ds["Classificação"] == "NEGATIVA").sum()) / n * 100


def nss_weighted(df: pd.DataFrame) -> float:
    ds = df[df["Classificação"] != "PUBLICIDADE"]
    if len(ds) == 0:
        return 0.0
    w_total = ds["Peso"].sum()
    w_pos = ds.loc[ds["Classificação"] == "POSITIVA", "Peso"].sum()
    w_neg = ds.loc[ds["Classificação"] == "NEGATIVA", "Peso"].sum()
    return (w_pos - w_neg) / w_total * 100


def sentiment_profile(df_input, group_col, min_n=30, top_n=15):
    """Perfil de sentimento genérico agrupado por qualquer coluna."""
    profile = df_input.groupby(group_col).agg(
        Total=("Classificação", "count"),
        Positiva=("Classificação", lambda x: (x == "POSITIVA").sum()),
        Neutra=("Classificação", lambda x: (x == "NEUTRA").sum()),
        Negativa=("Classificação", lambda x: (x == "NEGATIVA").sum()),
    )
    profile = profile[profile["Total"] >= min_n]
    profile["%Pos"] = (profile["Positiva"] / profile["Total"] * 100).round(1)
    profile["%Neg"] = (profile["Negativa"] / profile["Total"] * 100).round(1)
    profile["%Neu"] = (profile["Neutra"] / profile["Total"] * 100).round(1)
    profile["NSS"] = ((profile["Positiva"] - profile["Negativa"]) / profile["Total"] * 100).round(1)
    return profile


def build_nss_matrix(df_input, min_n=30):
    """Matriz NSS Categoria × Tier."""
    results = []
    for cat in df_input["Categoria"].unique():
        for tier in TIER_ORDER:
            subset = df_input[(df_input["Categoria"] == cat) & (df_input["Tier"] == tier)]
            n = len(subset)
            nss = ((subset["Classificação"].eq("POSITIVA").sum() -
                    subset["Classificação"].eq("NEGATIVA").sum()) / n * 100) if n >= min_n else np.nan
            results.append({"Categoria": cat, "Tier": tier, "NSS": nss, "N": n})
    df_r = pd.DataFrame(results)
    nss_m = df_r.pivot(index="Categoria", columns="Tier", values="NSS")[TIER_ORDER]
    n_m = df_r.pivot(index="Categoria", columns="Tier", values="N")[TIER_ORDER]
    cat_order = df_input["Categoria"].value_counts().index
    return nss_m.reindex(cat_order), n_m.reindex(cat_order)


def kpi_card(value, label, css_class=""):
    st.markdown(
        f'<div class="kpi-card {css_class}">'
        f'<h2>{value}</h2><p>{label}</p></div>',
        unsafe_allow_html=True,
    )


def stat_box(value, label):
    st.markdown(
        f'<div class="stat-box"><div class="value">{value}</div>'
        f'<div class="label">{label}</div></div>',
        unsafe_allow_html=True,
    )


def plot_pyramid(df_plot, y_col, height=650):
    """Pirâmide de sentimento estilo pirâmide etária."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df_plot[y_col], x=-df_plot["%Neg"], orientation="h",
        name="% Negativa", marker_color="#e74c3c", marker_opacity=0.85,
        text=df_plot["%Neg"].apply(lambda v: f"{v:.0f}%" if v >= 3 else ""),
        textposition="inside", textfont=dict(color="white", size=11),
        customdata=df_plot[["Negativa", "%Neg", "NSS"]].values,
        hovertemplate="<b>%{y}</b><br>Neg: %{customdata[0]:.0f} (%{customdata[1]:.1f}%)<br>NSS: %{customdata[2]:+.1f}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=df_plot[y_col], x=-df_plot["%Neu"], orientation="h",
        name="% Neutra", marker_color="#bdc3c7", marker_opacity=0.6,
        text=df_plot["%Neu"].apply(lambda v: f"{v:.0f}%" if v >= 8 else ""),
        textposition="inside", textfont=dict(color="#2c3e50", size=10),
        customdata=df_plot[["Neutra", "%Neu"]].values,
        hovertemplate="<b>%{y}</b><br>Neu: %{customdata[0]:.0f} (%{customdata[1]:.1f}%)<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=df_plot[y_col], x=df_plot["%Pos"], orientation="h",
        name="% Positiva", marker_color="#2ecc71", marker_opacity=0.85,
        text=df_plot["%Pos"].apply(lambda v: f"{v:.0f}%" if v >= 3 else ""),
        textposition="inside", textfont=dict(color="white", size=11),
        customdata=df_plot[["Positiva", "%Pos", "NSS"]].values,
        hovertemplate="<b>%{y}</b><br>Pos: %{customdata[0]:.0f} (%{customdata[1]:.1f}%)<br>NSS: %{customdata[2]:+.1f}<extra></extra>",
    ))
    fig.add_vline(x=0, line_width=2, line_color="#2c3e50")
    fig.update_layout(
        template="plotly_white", height=height, barmode="relative",
        xaxis=dict(
            title="Distribuição Percentual", range=[-105, 105],
            tickvals=[-100, -75, -50, -25, 0, 25, 50, 75, 100],
            ticktext=["100%", "75%", "50%", "25%", "0", "25%", "50%", "75%", "100%"],
        ),
        yaxis=dict(title=""),
        margin=dict(l=20, r=20, t=20, b=50),
        legend=dict(orientation="h", y=-0.08, x=0.3),
        font=dict(size=12),
    )
    return fig


# ═══════════════════════════════════════════════════════════════════════════
# CARREGAR DADOS + FILTROS
# ═══════════════════════════════════════════════════════════════════════════

df_raw = load_data()

with st.sidebar:
    st.markdown("## 💧 Filtros")
    st.markdown("---")

    min_date = df_raw["Data"].min().date()
    max_date = df_raw["Data"].max().date()
    date_range = st.date_input("Período", value=(min_date, max_date),
                               min_value=min_date, max_value=max_date)

    all_groups = sorted(df_raw["Grupo"].dropna().unique())
    sel_groups = st.multiselect("Grupo", all_groups, default=[])

    avail_companies = sorted(
        df_raw[df_raw["Grupo"].isin(sel_groups)]["Empresa"].dropna().unique()
    ) if sel_groups else sorted(df_raw["Empresa"].dropna().unique())
    sel_companies = st.multiselect("Empresa", avail_companies, default=[])

    sel_media = st.multiselect("Mídia", sorted(df_raw["Mídia"].dropna().unique()), default=[])
    sel_tiers = st.multiselect("Tier", sorted(df_raw["Tier"].dropna().unique()), default=[])
    sel_cats = st.multiselect("Categoria", sorted(df_raw["Categoria"].dropna().unique()), default=[])

    st.markdown("---")
    # Filtro de veículo com busca textual
    veiculo_search = st.text_input("🔍 Buscar Veículo", placeholder="Ex: Globo, CBN, Valor…")
    programa_search = st.text_input("🔍 Buscar Programa", placeholder="Ex: Bom Dia, Jornal…")

    st.markdown("---")
    st.caption("Dados: clipping de mídia · Google Sheets")


# ── Aplicar filtros ──────────────────────────────────────────────────────
df = df_raw.copy()
if len(date_range) == 2:
    df = df[(df["Data"].dt.date >= date_range[0]) & (df["Data"].dt.date <= date_range[1])]
if sel_groups:
    df = df[df["Grupo"].isin(sel_groups)]
if sel_companies:
    df = df[df["Empresa"].isin(sel_companies)]
if sel_media:
    df = df[df["Mídia"].isin(sel_media)]
if sel_tiers:
    df = df[df["Tier"].isin(sel_tiers)]
if sel_cats:
    df = df[df["Categoria"].isin(sel_cats)]
if veiculo_search.strip():
    df = df[df["Veículo_de_comunicacao"].str.contains(veiculo_search.strip(), case=False, na=False)]
if programa_search.strip():
    df = df[df["Programa"].str.contains(programa_search.strip(), case=False, na=False)]

df_sent = df[df["Classificação"] != "PUBLICIDADE"].copy()


# ═══════════════════════════════════════════════════════════════════════════
# HEADER + KPIs
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("# 💧 Análise de Satisfação — Saneamento")
st.caption(
    f"**{len(df):,}** registros · "
    f"{df['Grupo'].nunique()} grupos · "
    f"{df['Empresa'].nunique()} empresas · "
    f"{df['Data'].min().strftime('%b/%Y') if len(df) > 0 else '—'} a "
    f"{df['Data'].max().strftime('%b/%Y') if len(df) > 0 else '—'}"
)

# Banner de alerta para Tier Null
if len(df_sent) > 0:
    pct_null = (df_sent["Tier"] == "Null").sum() / len(df_sent) * 100
    if pct_null > 20:
        st.info(
            f"⚠️ **{pct_null:.0f}%** dos registros não têm Tier classificado (Null). "
            f"O NSS Ponderado trata esses registros com peso 1. "
            f"Esse grupo tende a ser mais negativo (ver aba Tier × Classificação)."
        )

nss_s = nss_simple(df)
nss_w = nss_weighted(df)
n_pos = (df_sent["Classificação"] == "POSITIVA").sum()
n_neg = (df_sent["Classificação"] == "NEGATIVA").sum()
n_neu = (df_sent["Classificação"] == "NEUTRA").sum()
total_sent = len(df_sent)

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    kpi_card(f"{nss_s:+.1f}", "NSS Simples", "kpi-pos" if nss_s >= 0 else "kpi-neg")
with k2:
    kpi_card(f"{nss_w:+.1f}", "NSS Ponderado", "kpi-pos" if nss_w >= 0 else "kpi-neg")
with k3:
    kpi_card(f"{n_pos/total_sent*100:.1f}%" if total_sent else "—", f"Positivas ({n_pos:,})", "kpi-pos")
with k4:
    kpi_card(f"{n_neg/total_sent*100:.1f}%" if total_sent else "—", f"Negativas ({n_neg:,})", "kpi-neg")
with k5:
    kpi_card(f"{n_neu/total_sent*100:.1f}%" if total_sent else "—", f"Neutras ({n_neu:,})", "kpi-neu")

st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════════

tab_temporal, tab_distrib, tab_tier, tab_cat, tab_veic, tab_empresa, tab_periodo = st.tabs([
    "📈 Temporal",
    "📊 Distribuições",
    "🔬 Tier × Classificação",
    "🏷️ Categorias",
    "📺 Veículos & Programas",
    "🏢 Empresas",
    "📅 Hipótese Set/2024",
])


# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 — TEMPORAL
# ═══════════════════════════════════════════════════════════════════════════

with tab_temporal:
    if len(df_sent) == 0:
        st.warning("Sem dados para os filtros selecionados.")
    else:
        st.subheader("NSS Mensal — Simples vs Ponderado")
        nss_monthly = []
        for period in sorted(df_sent["Ano_Mes"].unique()):
            dm = df_sent[df_sent["Ano_Mes"] == period]
            nss_monthly.append({
                "Data": period.to_timestamp(),
                "NSS Simples": nss_simple(dm),
                "NSS Ponderado": nss_weighted(dm),
                "N": len(dm),
            })
        nss_df = pd.DataFrame(nss_monthly)

        fig_nss = go.Figure()
        fig_nss.add_trace(go.Scatter(
            x=nss_df["Data"], y=nss_df["NSS Simples"],
            mode="lines+markers", name="NSS Simples",
            line=dict(color=COLORS["POSITIVA"], width=3), marker=dict(size=7),
            hovertemplate="%{x|%b/%Y}<br>NSS: %{y:.1f}<br>N=%{customdata}<extra></extra>",
            customdata=nss_df["N"],
        ))
        fig_nss.add_trace(go.Scatter(
            x=nss_df["Data"], y=nss_df["NSS Ponderado"],
            mode="lines+markers", name="NSS Ponderado",
            line=dict(color=COLORS["NEGATIVA"], width=3, dash="dash"),
            marker=dict(size=7, symbol="diamond"),
        ))
        fig_nss.add_hline(y=0, line_dash="dot", line_color="gray", opacity=0.5)
        fig_nss.update_layout(
            height=420, template="plotly_white", hovermode="x unified",
            legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
            margin=dict(l=40, r=20, t=30, b=60),
        )
        st.plotly_chart(fig_nss, use_container_width=True, theme=None)

        with st.expander("ℹ️ Como interpretar"):
            st.markdown(
                "**Linha verde** = NSS Simples (cada menção vale 1). "
                "**Linha vermelha tracejada** = NSS Ponderado (veículos de maior Tier pesam mais). "
                "Se a vermelha fica abaixo da verde, grandes veículos são mais negativos."
            )

        # Volume + proporção
        c1, c2 = st.columns(2)
        vol = df_sent.groupby(["Ano_Mes", "Classificação"]).size().unstack(fill_value=0)
        vol.index = vol.index.to_timestamp()

        with c1:
            st.subheader("Volume Mensal")
            fig_vol = go.Figure()
            for cls in ["POSITIVA", "NEUTRA", "NEGATIVA"]:
                if cls in vol.columns:
                    fig_vol.add_trace(go.Scatter(
                        x=vol.index, y=vol[cls], mode="lines+markers",
                        name=cls, line=dict(color=COLORS.get(cls), width=2),
                    ))
            fig_vol.update_layout(
                height=350, template="plotly_white", hovermode="x unified",
                legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
                margin=dict(l=40, r=20, t=20, b=60),
            )
            st.plotly_chart(fig_vol, use_container_width=True, theme=None)

        with c2:
            st.subheader("Proporção Mensal (%)")
            vol_pct = vol.div(vol.sum(axis=1), axis=0) * 100
            fig_pct = go.Figure()
            for cls in ["POSITIVA", "NEUTRA", "NEGATIVA"]:
                if cls in vol_pct.columns:
                    fig_pct.add_trace(go.Bar(
                        x=vol_pct.index, y=vol_pct[cls], name=cls,
                        marker_color=COLORS.get(cls),
                    ))
            fig_pct.update_layout(
                barmode="stack", height=350, template="plotly_white",
                yaxis_range=[0, 100], yaxis_title="%",
                legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
                margin=dict(l=40, r=20, t=20, b=60),
            )
            st.plotly_chart(fig_pct, use_container_width=True, theme=None)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 — DISTRIBUIÇÕES
# ═══════════════════════════════════════════════════════════════════════════

with tab_distrib:
    if len(df) == 0:
        st.warning("Sem dados.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Classificação")
            cls_counts = df["Classificação"].value_counts()
            fig = go.Figure(go.Pie(
                labels=cls_counts.index, values=cls_counts.values, hole=0.4,
                marker_colors=[COLORS.get(c, "#ccc") for c in cls_counts.index],
                textinfo="percent+label",
            ))
            fig.update_layout(height=360, showlegend=False, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True, theme=None)

        with c2:
            st.subheader("Tier")
            tier_counts = df["Tier"].value_counts()
            fig = go.Figure(go.Bar(
                x=tier_counts.values, y=tier_counts.index, orientation="h",
                marker_color=[TIER_COLORS.get(t, "#ccc") for t in tier_counts.index],
                text=[f"{v:,}" for v in tier_counts.values], textposition="outside",
            ))
            fig.update_layout(height=360, template="plotly_white", margin=dict(l=10, r=50, t=10, b=30))
            st.plotly_chart(fig, use_container_width=True, theme=None)

        c3, c4 = st.columns(2)
        with c3:
            st.subheader("Mídia")
            mc = df["Mídia"].value_counts()
            fig = go.Figure(go.Bar(x=mc.index, y=mc.values, marker_color="#3498db",
                                   text=[f"{v:,}" for v in mc.values], textposition="outside"))
            fig.update_layout(height=340, template="plotly_white", margin=dict(l=30, r=10, t=10, b=30))
            st.plotly_chart(fig, use_container_width=True, theme=None)

        with c4:
            st.subheader("Top 10 Categorias")
            tc = df["Categoria"].value_counts().head(10)
            fig = go.Figure(go.Bar(
                x=tc.values, y=tc.index, orientation="h",
                marker_color=px.colors.sequential.Viridis[:10],
                text=[f"{v:,}" for v in tc.values], textposition="outside",
            ))
            fig.update_layout(height=380, template="plotly_white",
                              yaxis=dict(autorange="reversed"), margin=dict(l=10, r=50, t=10, b=30))
            st.plotly_chart(fig, use_container_width=True, theme=None)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 — TIER × CLASSIFICAÇÃO
# ═══════════════════════════════════════════════════════════════════════════

with tab_tier:
    if len(df_sent) < 10:
        st.warning("Dados insuficientes.")
    else:
        st.subheader("Associação Tier × Classificação")

        # ── Qui-quadrado ──────────────────────────────────────────────────
        ct = pd.crosstab(df_sent["Tier"], df_sent["Classificação"])
        if "PUBLICIDADE" in ct.columns:
            ct = ct.drop(columns="PUBLICIDADE")
        chi2, p_val, dof, expected = chi2_contingency(ct)
        residuals = pd.DataFrame(
            ((ct.values - expected) / np.sqrt(expected)).round(2),
            index=ct.index, columns=ct.columns,
        )

        s1, s2, s3, s4 = st.columns(4)
        with s1: stat_box(f"{chi2:.1f}", "χ² (Qui-Quadrado)")
        with s2: stat_box(f"{p_val:.2e}" if p_val < 0.001 else f"{p_val:.4f}", "p-value")
        with s3: stat_box(str(dof), "Graus de Liberdade")
        with s4: stat_box("✅ Significativo" if p_val < 0.05 else "❌ Não significativo", "α = 0.05")

        # ── Proporção empilhada por Tier ──────────────────────────────────
        ct_pct = ct.div(ct.sum(axis=1), axis=0) * 100
        fig = go.Figure()
        for cls in ["POSITIVA", "NEUTRA", "NEGATIVA"]:
            if cls in ct_pct.columns:
                fig.add_trace(go.Bar(
                    name=cls, y=ct_pct.index, x=ct_pct[cls], orientation="h",
                    marker_color=COLORS.get(cls),
                    text=[f"{v:.1f}%" for v in ct_pct[cls]], textposition="inside",
                ))
        fig.update_layout(barmode="stack", height=300, template="plotly_white",
                          margin=dict(l=10, r=10, t=10, b=40),
                          legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"))
        st.plotly_chart(fig, use_container_width=True, theme=None)

        # ── Resíduos padronizados ─────────────────────────────────────────
        with st.expander("🔍 Heatmap de Resíduos Padronizados"):
            fig = go.Figure(go.Heatmap(
                z=residuals.values, x=residuals.columns.tolist(), y=residuals.index.tolist(),
                colorscale="RdBu_r", zmid=0, text=residuals.values,
                texttemplate="%{text:.2f}", textfont=dict(size=14),
                colorbar=dict(title="Resíduo"),
            ))
            fig.update_layout(height=320, template="plotly_white", margin=dict(l=10, r=10, t=10, b=30))
            st.plotly_chart(fig, use_container_width=True, theme=None)
            st.caption("Resíduo > +2: ocorre MAIS que o esperado. < −2: MENOS que o esperado.")

        st.markdown("---")

        # ══════════════════════════════════════════════════════════════════
        # Heatmap NSS Categoria × Tier
        # ══════════════════════════════════════════════════════════════════
        st.subheader("Heatmap: NSS por Categoria × Tier")
        st.caption("Mesmo tema, sentimentos opostos conforme o Tier?")

        nss_m, n_m = build_nss_matrix(df_sent)

        annotations = []
        for i, cat in enumerate(nss_m.index):
            for j, tier in enumerate(nss_m.columns):
                nss_val = nss_m.iloc[i, j]
                n_val = n_m.iloc[i, j]
                text = f"{nss_val:+.1f}<br><sub>N={int(n_val):,}</sub>" if pd.notna(nss_val) else "N<30"
                annotations.append(dict(
                    x=tier, y=cat, text=text, showarrow=False,
                    font=dict(size=10, color="#1a202c" if pd.isna(nss_val) or abs(nss_val) < 60 else "white"),
                ))

        fig = go.Figure(go.Heatmap(
            z=nss_m.values, x=nss_m.columns.tolist(), y=nss_m.index.tolist(),
            colorscale=NSS_COLORSCALE, zmid=0, colorbar=dict(title="NSS"),
            hovertemplate="<b>%{y}</b><br>Tier: %{x}<br>NSS: %{z:+.1f}<extra></extra>",
        ))
        fig.update_layout(
            height=max(500, len(nss_m) * 40), template="plotly_white",
            yaxis=dict(autorange="reversed"), annotations=annotations,
            margin=dict(l=180, r=30, t=10, b=40),
        )
        st.plotly_chart(fig, use_container_width=True, theme=None)

        # Divergência
        div = (nss_m["Menos Relevante"] - nss_m["Muito Relevante"]).dropna().sort_values(ascending=False)
        with st.expander("📊 Divergência MR → LR (tabela)"):
            div_df = pd.DataFrame({
                "Categoria": div.index,
                "Δ NSS (LR − MR)": div.values.round(1),
                "MR": [nss_m.loc[c, "Muito Relevante"] for c in div.index],
                "LR": [nss_m.loc[c, "Menos Relevante"] for c in div.index],
            })
            st.dataframe(div_df.style.format({"Δ NSS (LR − MR)": "{:+.1f}", "MR": "{:+.1f}", "LR": "{:+.1f}"}),
                         use_container_width=True)

        st.markdown("---")

        # ══════════════════════════════════════════════════════════════════
        # Treemap Tier > Categoria
        # ══════════════════════════════════════════════════════════════════
        st.subheader("Treemap: Tier × Categoria")
        st.caption("Tamanho = volume | Cor = NSS | Clique para expandir")

        tm_data = df_sent.groupby(["Tier", "Categoria"]).agg(
            Total=("Classificação", "count"),
            Positiva=("Classificação", lambda x: (x == "POSITIVA").sum()),
            Negativa=("Classificação", lambda x: (x == "NEGATIVA").sum()),
        ).reset_index()
        tm_data["NSS"] = ((tm_data["Positiva"] - tm_data["Negativa"]) / tm_data["Total"] * 100).round(1)

        fig = px.treemap(
            tm_data, path=["Tier", "Categoria"], values="Total", color="NSS",
            color_continuous_scale=NSS_COLORSCALE, color_continuous_midpoint=0,
        )
        fig.update_layout(height=600, margin=dict(l=10, r=10, t=10, b=10))
        fig.update_traces(textinfo="label+value",
                          hovertemplate="<b>%{label}</b><br>Total: %{value:,}<br>NSS: %{color:+.1f}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True, theme=None)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 4 — CATEGORIAS
# ═══════════════════════════════════════════════════════════════════════════

with tab_cat:
    if len(df_sent) == 0:
        st.warning("Sem dados.")
    else:
        st.subheader("NSS por Categoria")
        segment_tier = st.toggle("Segmentar por Tier", value=False, key="seg_tier")

        if not segment_tier:
            # Visão flat original
            n_cats = st.slider("Categorias", 5, 20, 10, key="n_cats")
            top_cats = df_sent["Categoria"].value_counts().head(n_cats).index
            rows = []
            for cat in top_cats:
                dc = df_sent[df_sent["Categoria"] == cat]
                pos = (dc["Classificação"] == "POSITIVA").sum()
                neg = (dc["Classificação"] == "NEGATIVA").sum()
                n = len(dc)
                rows.append({"Categoria": cat, "N": n, "% Pos": round(pos/n*100, 1),
                             "% Neg": round(neg/n*100, 1), "NSS": round((pos-neg)/n*100, 1)})
            cat_df = pd.DataFrame(rows).sort_values("NSS")

            fig = go.Figure(go.Bar(
                x=cat_df["NSS"], y=cat_df["Categoria"], orientation="h",
                marker_color=[COLORS["NEGATIVA"] if x < 0 else COLORS["POSITIVA"] for x in cat_df["NSS"]],
                text=[f"{x:+.1f}" for x in cat_df["NSS"]], textposition="outside",
                customdata=cat_df["N"],
                hovertemplate="<b>%{y}</b><br>NSS: %{x:.1f}<br>N=%{customdata:,}<extra></extra>",
            ))
            fig.add_vline(x=0, line_color="black", line_width=1)
            fig.update_layout(height=max(400, n_cats*38), template="plotly_white",
                              margin=dict(l=10, r=60, t=10, b=30))
            st.plotly_chart(fig, use_container_width=True, theme=None)
        else:
            # Visão segmentada por Tier — heatmap
            st.caption("Heatmap NSS Categoria × Tier (mesmo da aba Tier × Classificação)")
            nss_m, n_m = build_nss_matrix(df_sent)
            fig = go.Figure(go.Heatmap(
                z=nss_m.values, x=nss_m.columns.tolist(), y=nss_m.index.tolist(),
                colorscale=NSS_COLORSCALE, zmid=0, colorbar=dict(title="NSS"),
                text=nss_m.values.round(1), texttemplate="%{text:+.1f}",
            ))
            fig.update_layout(height=max(500, len(nss_m)*40), template="plotly_white",
                              yaxis=dict(autorange="reversed"), margin=dict(l=180, r=30, t=10, b=40))
            st.plotly_chart(fig, use_container_width=True, theme=None)

        with st.expander("📋 Tabela completa"):
            if not segment_tier:
                st.dataframe(cat_df.sort_values("NSS", ascending=False).style.format(
                    {"NSS": "{:+.1f}", "% Pos": "{:.1f}%", "% Neg": "{:.1f}%", "N": "{:,}"}
                ), use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 5 — VEÍCULOS & PROGRAMAS
# ═══════════════════════════════════════════════════════════════════════════

with tab_veic:
    if len(df_sent) == 0:
        st.warning("Sem dados.")
    else:
        sub_veic, sub_prog = st.tabs(["📰 Veículos", "🎙️ Programas"])

        # ── VEÍCULOS ──────────────────────────────────────────────────────
        with sub_veic:
            st.subheader("Top Veículos por Tier")
            sel_tier_v = st.selectbox("Tier", TIER_ORDER, key="tier_veic")
            min_n_v = st.slider("Volume mínimo", 10, 200, 30, key="min_n_veic")

            prof_v = sentiment_profile(df_sent[df_sent["Tier"] == sel_tier_v], "Veículo_de_comunicacao", min_n=min_n_v)
            if len(prof_v) == 0:
                st.info("Nenhum veículo com volume suficiente nesse Tier.")
            else:
                prof_v = prof_v.sort_values("Total", ascending=False).head(20).reset_index()

                fig = go.Figure(go.Bar(
                    y=prof_v["Veículo_de_comunicacao"], x=prof_v["NSS"], orientation="h",
                    marker_color=[COLORS["NEGATIVA"] if x < 0 else COLORS["POSITIVA"] for x in prof_v["NSS"]],
                    text=prof_v.apply(lambda r: f"{r['NSS']:+.1f} (N={int(r['Total']):,})", axis=1),
                    textposition="outside",
                    hovertemplate="<b>%{y}</b><br>NSS: %{x:+.1f}<extra></extra>",
                ))
                fig.add_vline(x=0, line_width=2, line_color="#2c3e50")
                fig.update_layout(
                    height=max(400, len(prof_v)*30), template="plotly_white",
                    margin=dict(l=10, r=120, t=10, b=30),
                )
                st.plotly_chart(fig, use_container_width=True, theme=None)

                with st.expander("📋 Tabela"):
                    st.dataframe(prof_v.style.format({
                        "NSS": "{:+.1f}", "%Pos": "{:.1f}%", "%Neg": "{:.1f}%", "Total": "{:,}"
                    }), use_container_width=True)

        # ── PROGRAMAS ──────────────────────────────────────────
        with sub_prog:
            st.subheader("Pirâmide de Sentimento — Programas")
            st.caption("10 mais negativos + 10 mais positivos (excl. 'Geral')")

            min_n_p = st.slider("Volume mínimo", 10, 200, 30, key="min_n_prog")

            prof_p = sentiment_profile(
                df_sent[df_sent["Programa"] != "Geral"], "Programa", min_n=min_n_p,
            )
            if len(prof_p) == 0:
                st.info("Nenhum programa com volume suficiente.")
            else:
                tier_dom = (
                    df_sent[df_sent["Programa"] != "Geral"]
                    .groupby("Programa")["Tier"]
                    .agg(lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else "N/A")
                )
                prof_p["Tier_Dom"] = prof_p.index.map(tier_dom)

                neg = prof_p.nsmallest(10, "NSS")
                pos = prof_p.nlargest(10, "NSS")
                combined = pd.concat([neg, pos]).drop_duplicates().sort_values("NSS")

                combined = combined.reset_index()
                combined["Label"] = combined.apply(
                    lambda r: f"{TIER_EMOJI.get(r['Tier_Dom'], '⚪')} {r['Programa']} (N={int(r['Total']):,})",
                    axis=1,
                )

                fig = plot_pyramid(combined, "Label", height=max(650, len(combined)*36))
                st.plotly_chart(fig, use_container_width=True, theme=None)

                st.caption("Emojis: 🔴 Muito Relevante  🟠 Relevante  🔵 Menos Relevante  ⚪ Null")


# ═══════════════════════════════════════════════════════════════════════════
# TAB 6 — EMPRESAS
# ═══════════════════════════════════════════════════════════════════════════

with tab_empresa:
    if len(df_sent) == 0:
        st.warning("Sem dados.")
    else:
        view_mode = st.radio("Agrupar por:", ["Grupo", "Empresa"], horizontal=True)
        min_n_e = st.slider("Volume mínimo", 10, 1000, 50, step=10, key="min_n_emp")

        prof_e = sentiment_profile(df_sent, view_mode, min_n=min_n_e).reset_index().sort_values("NSS")

        st.subheader(f"NSS por {view_mode}")
        fig = go.Figure(go.Bar(
            x=prof_e["NSS"], y=prof_e[view_mode], orientation="h",
            marker_color=[COLORS["NEGATIVA"] if x < 0 else COLORS["POSITIVA"] for x in prof_e["NSS"]],
            text=[f"{x:+.1f}" for x in prof_e["NSS"]], textposition="outside",
            customdata=prof_e["Total"],
            hovertemplate=f"<b>%{{y}}</b><br>NSS: %{{x:.1f}}<br>N=%{{customdata:,}}<extra></extra>",
        ))
        fig.add_vline(x=0, line_color="black", line_width=1)
        fig.update_layout(height=max(400, len(prof_e)*30), template="plotly_white",
                          margin=dict(l=10, r=60, t=10, b=30))
        st.plotly_chart(fig, use_container_width=True, theme=None)

        # Heatmap mensal
        st.subheader(f"NSS Mensal por {view_mode} (Heatmap)")
        top_ent = prof_e.nlargest(15, "Total")[view_mode].tolist()
        df_heat = df_sent[df_sent[view_mode].isin(top_ent)].copy()

        if len(df_heat) > 0:
            heat_data = []
            for entity in top_ent:
                for period in sorted(df_heat[df_heat[view_mode] == entity]["Ano_Mes"].unique()):
                    dm = df_heat[(df_heat[view_mode] == entity) & (df_heat["Ano_Mes"] == period)]
                    heat_data.append({view_mode: entity, "Mês": str(period), "NSS": round(nss_simple(dm), 1)})
            hp = pd.DataFrame(heat_data).pivot(index=view_mode, columns="Mês", values="NSS")

            fig = go.Figure(go.Heatmap(
                z=hp.values, x=hp.columns.tolist(), y=hp.index.tolist(),
                colorscale="RdYlGn", zmid=0, text=hp.values,
                texttemplate="%{text:.0f}", textfont=dict(size=10),
                colorbar=dict(title="NSS"),
            ))
            fig.update_layout(height=max(350, len(top_ent)*30), template="plotly_white",
                              margin=dict(l=10, r=10, t=10, b=30))
            st.plotly_chart(fig, use_container_width=True, theme=None)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 7 — HIPÓTESE SET/2024
# ═══════════════════════════════════════════════════════════════════════════

with tab_periodo:
    if len(df_sent) == 0:
        st.warning("Sem dados.")
    else:
        st.subheader("Hipótese: Mudança em Setembro/2024")
        st.markdown(
            "**Antes**: início → ago/2024 · **Setembro**: set/2024 · **Depois**: out/2024 → fim"
        )

        set_ref = pd.Period("2024-09", freq="M")
        df_per = df_sent.copy()
        df_per["Periodo"] = df_per["Ano_Mes"].apply(
            lambda x: "Antes" if x < set_ref else ("Setembro" if x == set_ref else "Depois")
        )

        rows = []
        for per in ["Antes", "Setembro", "Depois"]:
            dp = df_per[df_per["Periodo"] == per]
            n = len(dp)
            pos = (dp["Classificação"] == "POSITIVA").sum()
            neg = (dp["Classificação"] == "NEGATIVA").sum()
            neu = (dp["Classificação"] == "NEUTRA").sum()
            rows.append({
                "Período": per, "N": n,
                "Positivas": pos, "Negativas": neg, "Neutras": neu,
                "NSS Simples": round(nss_simple(dp), 1),
                "NSS Ponderado": round(nss_weighted(dp), 1),
            })
        per_df = pd.DataFrame(rows)

        p1, p2, p3 = st.columns(3)
        for col_st, idx in zip([p1, p2, p3], range(len(per_df))):
            row = per_df.iloc[idx]
            nss_val = row["NSS Simples"]
            with col_st:
                css = "kpi-pos" if nss_val >= 0 else "kpi-neg"
                kpi_card(f"{nss_val:+.1f}", f"{row['Período']} (N={row['N']:,})", css)

        st.markdown("")
        st.dataframe(
            per_df.style.format({
                "N": "{:,}", "Positivas": "{:,}", "Negativas": "{:,}", "Neutras": "{:,}",
                "NSS Simples": "{:+.1f}", "NSS Ponderado": "{:+.1f}",
            }),
            use_container_width=True,
        )

        if len(per_df) == 3:
            d1, d2 = st.columns(2)
            with d1:
                delta = per_df.iloc[1]["NSS Simples"] - per_df.iloc[0]["NSS Simples"]
                st.metric("Δ Antes → Set", f"{per_df.iloc[1]['NSS Simples']:+.1f}", f"{delta:+.1f}")
            with d2:
                delta = per_df.iloc[2]["NSS Simples"] - per_df.iloc[1]["NSS Simples"]
                st.metric("Δ Set → Depois", f"{per_df.iloc[2]['NSS Simples']:+.1f}", f"{delta:+.1f}")

        with st.expander("ℹ️ Notas metodológicas"):
            st.markdown(
                "O período 'Setembro' contém apenas 1 mês — o NSS é instável. "
                "Diferenças entre períodos não implicam causalidade."
            )