"""
📊 Inteligência de Mídia — Relatório Narrativo Interativo
═════════════════════════════════════════════════════════
Estilo scrollytelling: página única, filtros no topo, narrativa entre gráficos.
Inspirado em: pesquisa.codigofonte.com.br/2025

Execução: streamlit run relatorio_midia.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ═══════════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════════

st.set_page_config(page_title="Inteligência de Mídia", page_icon="📊", layout="wide")

COLORS = {"POSITIVA": "#2ecc71", "NEUTRA": "#95a5a6", "NEGATIVA": "#e74c3c", "PUBLICIDADE": "#3498db"}
TIER_W = {"Muito Relevante": 8, "Relevante": 4, "Menos Relevante": 1, "Null": 1}
TIER_EMOJI = {"Muito Relevante": "🔴", "Relevante": "🟠", "Menos Relevante": "🔵", "Null": "⚪"}
NSS_SCALE = [[0, "#c0392b"], [0.3, "#e74c3c"], [0.5, "#fdfefe"], [0.7, "#82e0aa"], [1, "#1e8449"]]
PLOTLY_CFG = dict(template="plotly_white", font=dict(family="Inter, sans-serif"))


# ═══════════════════════════════════════════════════════════════════════════
# CSS — tema claro forçado + estilo editorial
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

    :root, [data-testid="stAppViewContainer"], [data-testid="stApp"],
    .main, .block-container, [data-testid="stHeader"],
    [data-testid="stToolbar"], [data-testid="stBottom"] {
        background-color: #ffffff !important;
        color: #1a202c !important;
    }

    .block-container {
        max-width: 1100px !important;
        padding-top: 2rem !important;
    }

    h1, h2, h3, h4, h5, h6, p, span, label, li, td, th,
    .stMarkdown, .stCaption, .stText {
        color: #1a202c !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* ── Hero ────────────────────────────────────── */
    .hero {
        background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
        padding: 2.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
    }
    .hero h1 { color: #ffffff !important; font-size: 2.2rem; font-weight: 800;
               border-bottom: 4px solid #2ecc71; padding-bottom: 0.5rem; }
    .hero p  { color: #cbd5e0 !important; font-size: 1.05rem; line-height: 1.7; }
    .hero strong { color: #2ecc71 !important; }

    /* ── KPI cards ───────────────────────────────── */
    .kpi {
        background: #f7fafc;
        border-radius: 12px;
        padding: 1.4rem 1rem;
        text-align: center;
        border-left: 5px solid #3498db;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .kpi .val { font-size: 2.2rem; font-weight: 800; color: #2c3e50; }
    .kpi .lab { font-size: 0.82rem; color: #6c757d; margin-top: 0.2rem; }
    .kpi-pos { border-left-color: #2ecc71; }
    .kpi-neg { border-left-color: #e74c3c; }
    .kpi-neu { border-left-color: #f39c12; }

    /* ── Seção narrativa ─────────────────────────── */
    .narr {
        background: #f7fafc;
        border-left: 4px solid #3498db;
        padding: 1.2rem 1.5rem;
        border-radius: 0 10px 10px 0;
        margin: 1.5rem 0;
        font-size: 0.95rem;
        line-height: 1.7;
    }
    .narr strong { color: #2c3e50; }
    .narr em { color: #e74c3c; }

    /* ── Divisor editorial ────────────────────────── */
    .section-head {
        font-size: 1.5rem;
        font-weight: 700;
        color: #2c3e50 !important;
        border-bottom: 3px solid #e2e8f0;
        padding-bottom: 0.5rem;
        margin-top: 3rem;
        margin-bottom: 0.5rem;
    }
    .section-sub {
        font-size: 0.9rem;
        color: #718096 !important;
        margin-bottom: 1.5rem;
    }

    /* ── Filtros ──────────────────────────────────── */
    .filter-bar {
        background: #edf2f7;
        padding: 1.2rem 1.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
    }

    /* ── Esconder boilerplate ─────────────────────── */
    #MainMenu, footer, header { visibility: hidden; }
    [data-testid="stSidebar"] { display: none; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# FUNÇÕES
# ═══════════════════════════════════════════════════════════════════════════

def nss_simple(df):
    ds = df[df["Classificação"] != "PUBLICIDADE"]
    n = len(ds)
    if n == 0: return 0.0
    return ((ds["Classificação"] == "POSITIVA").sum() - (ds["Classificação"] == "NEGATIVA").sum()) / n * 100

def nss_weighted(df):
    ds = df[df["Classificação"] != "PUBLICIDADE"]
    if len(ds) == 0: return 0.0
    w = ds["Peso"].sum()
    return (ds.loc[ds["Classificação"] == "POSITIVA", "Peso"].sum() -
            ds.loc[ds["Classificação"] == "NEGATIVA", "Peso"].sum()) / w * 100

def kpi(val, label, css=""):
    st.markdown(f'<div class="kpi {css}"><div class="val">{val}</div><div class="lab">{label}</div></div>',
                unsafe_allow_html=True)

def section(title, subtitle=""):
    st.markdown(f'<div class="section-head">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="section-sub">{subtitle}</div>', unsafe_allow_html=True)

def narr(text):
    st.markdown(f'<div class="narr">{text}</div>', unsafe_allow_html=True)

def chart(fig, height=None):
    if height:
        fig.update_layout(height=height)
    fig.update_layout(**PLOTLY_CFG)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ═══════════════════════════════════════════════════════════════════════════
# DADOS
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600, show_spinner="Carregando dados…")
def load():
    url = ("https://docs.google.com/spreadsheets/d/"
           "1UVGM5g7A2pSmg4Nn5eTzjZhd25sAFFDbkBclRfyNgX8/export?format=csv")
    df = pd.read_csv(url)
    df["Data"] = pd.to_datetime(df["Data"], dayfirst=True, format="mixed", errors="coerce")
    df = df.dropna(subset=["Data"]).sort_values("Data")
    df["Ano_Mes"] = df["Data"].dt.to_period("M").astype(str)
    df["Peso"] = df["Tier"].map(TIER_W).fillna(1)
    df["Tier"] = df["Tier"].fillna("Null")
    return df

df_raw = load()
df_sent_all = df_raw[df_raw["Classificação"] != "PUBLICIDADE"].copy()


# ═══════════════════════════════════════════════════════════════════════════
# HERO
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="hero">
    <h1>📊 Inteligência de Mídia</h1>
    <p>
        Este relatório transforma dados brutos de clipping de mídia em <strong>inteligência acionável</strong>.
        Use os filtros abaixo para explorar diferentes recortes — cada gráfico e indicador se atualiza
        em tempo real. Os textos explicam <strong>como ler</strong> cada visualização; a análise é sua.
    </p>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# FILTROS — inline no topo (não sidebar)
# ═══════════════════════════════════════════════════════════════════════════

st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
st.markdown("**🔍 Filtros** — selecione o recorte que deseja analisar")

f1, f2, f3, f4 = st.columns(4)
with f1:
    grupos = ["Todos"] + sorted(df_raw["Grupo"].dropna().unique().tolist())
    sel_grupo = st.selectbox("Grupo", grupos, key="fg")
with f2:
    tiers = ["Todos"] + sorted(df_raw["Tier"].dropna().unique().tolist())
    sel_tier = st.selectbox("Tier", tiers, key="ft")
with f3:
    midias = ["Todos"] + sorted(df_raw["Mídia"].dropna().unique().tolist())
    sel_midia = st.selectbox("Mídia", midias, key="fm")
with f4:
    cats = ["Todos"] + sorted(df_raw["Categoria"].dropna().unique().tolist())
    sel_cat = st.selectbox("Categoria", cats, key="fc")

st.markdown("</div>", unsafe_allow_html=True)

# Aplicar filtros
df = df_raw.copy()
if sel_grupo != "Todos":
    df = df[df["Grupo"] == sel_grupo]
if sel_tier != "Todos":
    df = df[df["Tier"] == sel_tier]
if sel_midia != "Todos":
    df = df[df["Mídia"] == sel_midia]
if sel_cat != "Todos":
    df = df[df["Categoria"] == sel_cat]

ds = df[df["Classificação"] != "PUBLICIDADE"].copy()

# Info do filtro
n_total = len(ds)
if n_total == 0:
    st.error("Nenhum registro encontrado para os filtros selecionados.")
    st.stop()

periodo = f"{df['Data'].min().strftime('%b/%Y')} a {df['Data'].max().strftime('%b/%Y')}"
filtro_ativo = sel_grupo != "Todos" or sel_tier != "Todos" or sel_midia != "Todos" or sel_cat != "Todos"
if filtro_ativo:
    filtros_txt = " · ".join([f for f in [
        f"Grupo: {sel_grupo}" if sel_grupo != "Todos" else "",
        f"Tier: {sel_tier}" if sel_tier != "Todos" else "",
        f"Mídia: {sel_midia}" if sel_midia != "Todos" else "",
        f"Categoria: {sel_cat}" if sel_cat != "Todos" else "",
    ] if f])
    st.info(f"🔍 Filtro ativo: {filtros_txt} · **{n_total:,}** menções · {periodo}")
else:
    st.caption(f"**{n_total:,}** menções orgânicas · {periodo}")


# ═══════════════════════════════════════════════════════════════════════════
# KPIs
# ═══════════════════════════════════════════════════════════════════════════

nss_s = nss_simple(df)
nss_w = nss_weighted(df)
n_pos = (ds["Classificação"] == "POSITIVA").sum()
n_neg = (ds["Classificação"] == "NEGATIVA").sum()
n_veiculos = ds["Veículo_de_comunicacao"].nunique()

k1, k2, k3, k4, k5 = st.columns(5)
with k1: kpi(f"{nss_s:+.1f}", "NSS Simples", "kpi-pos" if nss_s >= 0 else "kpi-neg")
with k2: kpi(f"{nss_w:+.1f}", "NSS Ponderado", "kpi-pos" if nss_w >= 0 else "kpi-neg")
with k3: kpi(f"{n_pos:,}", "Positivas", "kpi-pos")
with k4: kpi(f"{n_neg:,}", "Negativas", "kpi-neg")
with k5: kpi(f"{n_veiculos}", "Veículos Únicos", "kpi-neu")

st.markdown("")


# ═══════════════════════════════════════════════════════════════════════════
# SEÇÃO 1 — O SALDO DE IMAGEM
# ═══════════════════════════════════════════════════════════════════════════

section("1. O Saldo de Imagem", "Como está distribuído o sentimento da cobertura?")

narr("""
O <strong>NSS (Net Sentiment Score)</strong> funciona como um saldo bancário da reputação:
<code>(Positivas − Negativas) / Total × 100</code>. Se temos 100 notícias, 70 positivas e 30 negativas,
o NSS é <strong>+40</strong> — um saldo favorável.
<br><br>
<strong>Como ler:</strong> No gráfico da esquerda, a fatia verde mostra o percentual de menções positivas.
No da direita, as barras mostram quais <strong>temas</strong> puxam o saldo para cima (verde, à direita)
ou para baixo (vermelho, à esquerda). Quanto mais longa a barra, maior a contribuição daquele tema.
""")

c1, c2 = st.columns([1, 1.3])

with c1:
    counts = ds["Classificação"].value_counts()
    fig = go.Figure(go.Pie(
        labels=counts.index, values=counts.values, hole=0.45,
        marker_colors=[COLORS.get(c, "#ccc") for c in counts.index],
        textinfo="percent+label",
    ))
    fig.update_layout(height=400, showlegend=False, margin=dict(l=10, r=10, t=30, b=10),
                      title="Composição do Sentimento")
    chart(fig)

with c2:
    top_cats = ds["Categoria"].value_counts().head(12).index
    rows = []
    for c in top_cats:
        dc = ds[ds["Categoria"] == c]
        p = (dc["Classificação"] == "POSITIVA").sum()
        n = (dc["Classificação"] == "NEGATIVA").sum()
        rows.append({"Categoria": c, "N": len(dc), "NSS": round((p - n) / len(dc) * 100, 1)})
    cdf = pd.DataFrame(rows).sort_values("NSS")

    fig = go.Figure(go.Bar(
        x=cdf["NSS"], y=cdf["Categoria"], orientation="h",
        marker_color=[COLORS["NEGATIVA"] if x < 0 else COLORS["POSITIVA"] for x in cdf["NSS"]],
        text=[f"{x:+.1f}" for x in cdf["NSS"]], textposition="outside",
        customdata=cdf["N"],
        hovertemplate="<b>%{y}</b><br>NSS: %{x:+.1f}<br>N=%{customdata:,}<extra></extra>",
    ))
    fig.add_vline(x=0, line_color="#2c3e50", line_width=1)
    fig.update_layout(height=400, margin=dict(l=10, r=60, t=30, b=10),
                      title="NSS por Categoria Temática", xaxis_title="NSS →")
    chart(fig)

st.divider()


# ═══════════════════════════════════════════════════════════════════════════
# SEÇÃO 2 — O EFEITO MEGAFONE
# ═══════════════════════════════════════════════════════════════════════════

section("2. O Efeito Megafone", "Grandes veículos contam uma história diferente?")

narr("""
A mídia não é democrática: uma matéria no Jornal Nacional atinge milhões; um blog local, dezenas.
O <strong>NSS Ponderado</strong> multiplica cada menção pelo peso do veículo
(🔴 Muito Relevante = 8×, 🟠 Relevante = 4×, 🔵 Menos Relevante = 1×).
<br><br>
<strong>Como ler:</strong> A <strong style="color:#2ecc71">linha verde</strong> (Simples) trata todos os veículos
como iguais. A <strong style="color:#e74c3c">linha vermelha tracejada</strong> (Ponderada) amplifica o peso dos grandes.
Se a vermelha fica abaixo da verde, os megafones da mídia são mais críticos que a média.
A distância entre as linhas é a medida do "efeito megafone". A linha cinza no zero é a fronteira
entre saldo positivo e negativo.
""")

nss_monthly = []
for m in sorted(ds["Ano_Mes"].unique()):
    dm = ds[ds["Ano_Mes"] == m]
    nss_monthly.append({"Mês": m, "Simples": nss_simple(dm), "Ponderado": nss_weighted(dm), "N": len(dm)})
nss_df = pd.DataFrame(nss_monthly)

fig = go.Figure()
fig.add_trace(go.Scatter(x=nss_df["Mês"], y=nss_df["Simples"], mode="lines+markers",
    name="NSS Simples", line=dict(color=COLORS["POSITIVA"], width=3),
    marker=dict(size=8), customdata=nss_df["N"],
    hovertemplate="%{x}<br>NSS Simples: %{y:.1f}<br>N=%{customdata:,}<extra></extra>"))
fig.add_trace(go.Scatter(x=nss_df["Mês"], y=nss_df["Ponderado"], mode="lines+markers",
    name="NSS Ponderado", line=dict(color=COLORS["NEGATIVA"], width=3, dash="dash"),
    marker=dict(size=8, symbol="diamond"),
    hovertemplate="%{x}<br>NSS Ponderado: %{y:.1f}<extra></extra>"))
fig.add_hline(y=0, line_dash="dot", line_color="#bdc3c7", opacity=0.6)
fig.update_layout(height=420, hovermode="x unified",
    legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
    title="Evolução Mensal — NSS Simples vs Ponderado",
    margin=dict(l=40, r=20, t=50, b=60))
chart(fig)

st.divider()


# ═══════════════════════════════════════════════════════════════════════════
# SEÇÃO 3 — EVOLUÇÃO TEMÁTICA
# ═══════════════════════════════════════════════════════════════════════════

section("3. Evolução Temática", "Os temas problemáticos estão piorando ou melhorando?")

narr("""
O heatmap cruza <strong>temas</strong> (linhas) com <strong>meses</strong> (colunas).
A cor mostra o NSS: <strong style="color:#2ecc71">verde = saudável</strong>,
<strong style="color:#e74c3c">vermelho = crise</strong>, branco = neutro.
<br><br>
<strong>Como ler:</strong> Procure <em>sequências horizontais de vermelho</em> — são temas com crise persistente.
Uma célula vermelha isolada pode ser evento pontual. Transições de vermelho para verde indicam recuperação.
Células com "—" significam amostra insuficiente (menos de 3 menções naquele cruzamento).
""")

top_cats_heat = ds["Categoria"].value_counts().head(10).index.tolist()
dw = ds[ds["Categoria"].isin(top_cats_heat)]
heat_results = []
for cat in top_cats_heat:
    for mes in sorted(dw["Ano_Mes"].unique()):
        s = dw[(dw["Categoria"] == cat) & (dw["Ano_Mes"] == mes)]
        n = len(s)
        if n >= 3:
            p = (s["Classificação"] == "POSITIVA").sum()
            ng = (s["Classificação"] == "NEGATIVA").sum()
            heat_results.append({"Categoria": cat, "Mês": mes, "NSS": round((p - ng) / n * 100, 1)})
        else:
            heat_results.append({"Categoria": cat, "Mês": mes, "NSS": np.nan})

hp = pd.DataFrame(heat_results).pivot(index="Categoria", columns="Mês", values="NSS").reindex(top_cats_heat)

annots = []
for i, cat in enumerate(hp.index):
    for j, mes in enumerate(hp.columns):
        v = hp.iloc[i, j]
        text = f"{v:+.0f}" if pd.notna(v) else "—"
        color = "white" if pd.notna(v) and abs(v) > 50 else ("#bdc3c7" if pd.isna(v) else "#1a202c")
        annots.append(dict(x=mes, y=cat, text=text, showarrow=False, font=dict(size=10, color=color)))

fig = go.Figure(go.Heatmap(
    z=hp.values, x=hp.columns.tolist(), y=hp.index.tolist(),
    colorscale=NSS_SCALE, zmid=0, colorbar=dict(title="NSS"),
    hovertemplate="<b>%{y}</b><br>Mês: %{x}<br>NSS: %{z:+.1f}<extra></extra>",
))
fig.update_layout(height=max(420, len(top_cats_heat) * 42), yaxis=dict(autorange="reversed"),
    margin=dict(l=180, r=30, t=50, b=50), annotations=annots,
    title="NSS por Categoria × Mês")
chart(fig)

st.divider()


# ═══════════════════════════════════════════════════════════════════════════
# SEÇÃO 4 — RADIOGRAFIA DOS ATORES
# ═══════════════════════════════════════════════════════════════════════════

section("4. Radiografia dos Atores", "Quem são os aliados e os detratores?")

narr("""
Cada bolha é um veículo de mídia. A posição revela seu perfil estratégico.
<br><br>
<strong>Como ler:</strong> O eixo horizontal mostra o <strong>volume</strong> (quantas matérias publicou,
em escala logarítmica). O vertical mostra o <strong>sentimento</strong> (NSS).
A linha tracejada no zero divide aliados (acima) de detratores (abaixo).
O <strong style="color:#e74c3c">quadrante inferior direito</strong> é a zona de perigo —
alto volume com sentimento negativo. Passe o mouse sobre as bolhas para ver os nomes.
""")

min_vol = st.slider("Volume mínimo de menções por veículo", 1, 50, 5, key="mv")

prof = ds.groupby("Veículo_de_comunicacao").agg(
    Total=("Classificação", "count"),
    Pos=("Classificação", lambda x: (x == "POSITIVA").sum()),
    Neg=("Classificação", lambda x: (x == "NEGATIVA").sum()),
)
prof = prof[prof["Total"] >= min_vol].copy()
prof["NSS"] = ((prof["Pos"] - prof["Neg"]) / prof["Total"] * 100).round(1)
prof = prof.reset_index()

if len(prof) > 0:
    fig = go.Figure(go.Scatter(
        x=prof["Total"], y=prof["NSS"], mode="markers",
        marker=dict(size=12, color=prof["NSS"], colorscale=NSS_SCALE, cmid=0,
                    showscale=True, line=dict(width=1, color="#2c3e50"),
                    colorbar=dict(title="NSS")),
        text=prof["Veículo_de_comunicacao"],
        hovertemplate="<b>%{text}</b><br>Volume: %{x:,}<br>NSS: %{y:+.1f}<extra></extra>",
    ))
    fig.add_hline(y=0, line_dash="dash", line_color="#34495e", opacity=0.6)
    fig.update_layout(height=500, xaxis=dict(title="Volume (escala log)", type="log"),
        yaxis_title="NSS (Sentimento)", title="Matriz Estratégica — Volume × Sentimento",
        margin=dict(l=50, r=30, t=50, b=50))
    chart(fig)
else:
    st.info("Nenhum veículo com volume suficiente para o filtro selecionado.")

st.divider()


# ═══════════════════════════════════════════════════════════════════════════
# SEÇÃO 5 — MAPA DE SENTIMENTO POR ESCALA
# ═══════════════════════════════════════════════════════════════════════════

section("5. Mapa de Sentimento por Escala", "O mesmo tema muda de sentimento conforme o tamanho do veículo?")

narr("""
O <strong>Treemap</strong> mostra a hierarquia <strong>Tier → Categoria</strong>.
O tamanho de cada bloco reflete o volume; a cor mostra o NSS.
<br><br>
<strong>Como ler:</strong> Compare a mesma categoria (ex: "Abastecimento") dentro de Tiers diferentes.
Se aparece <strong style="color:#2ecc71">verde</strong> no "Menos Relevante" e
<strong style="color:#e74c3c">vermelho</strong> no "Muito Relevante",
o tema é positivo na mídia local (comunicados) mas negativo na mídia grande (crises).
<strong>Clique nos blocos</strong> para expandir e ver detalhes.
""")

tm = ds.groupby(["Tier", "Categoria"]).agg(
    Total=("Classificação", "count"),
    Pos=("Classificação", lambda x: (x == "POSITIVA").sum()),
    Neg=("Classificação", lambda x: (x == "NEGATIVA").sum()),
).reset_index()
tm = tm[tm["Total"] >= 3]
tm["NSS"] = ((tm["Pos"] - tm["Neg"]) / tm["Total"] * 100).round(1)

if len(tm) > 0:
    fig = px.treemap(tm, path=["Tier", "Categoria"], values="Total", color="NSS",
        color_continuous_scale=NSS_SCALE, color_continuous_midpoint=0)
    fig.update_layout(height=550, margin=dict(l=10, r=10, t=50, b=10),
        title="Treemap — Tier × Categoria")
    fig.update_traces(textinfo="label+value",
        hovertemplate="<b>%{label}</b><br>Total: %{value:,}<br>NSS: %{color:+.1f}<extra></extra>")
    chart(fig)

st.divider()


# ═══════════════════════════════════════════════════════════════════════════
# SEÇÃO 6 — QUEM PROMOVE E QUEM DETRATA
# ═══════════════════════════════════════════════════════════════════════════

section("6. Quem Promove e Quem Detrata", "Os Top 20 veículos em volume de menções positivas e negativas")

narr("""
Os gráficos abaixo mostram o volume <strong>absoluto</strong> de menções por veículo.
A barra <strong style="color:#e74c3c">vermelha</strong> (esquerda) mostra negativas publicadas;
a <strong style="color:#2ecc71">verde</strong> (direita) mostra positivas.
<br><br>
<strong>Como ler:</strong> O ícone indica a relevância do veículo
(🔴 alto impacto, 🟠 médio, 🔵 baixo, ⚪ não classificado).
Veículos com 🔴 e barra vermelha dominante são <strong>prioridade máxima</strong> de gestão.
A barra vermelha de um veículo 🔴 "pesa" 8× mais que a de um 🔵 no NSS Ponderado.
""")

prof2 = ds.groupby("Veículo_de_comunicacao").agg(
    Total=("Classificação", "count"),
    Positiva=("Classificação", lambda x: (x == "POSITIVA").sum()),
    Negativa=("Classificação", lambda x: (x == "NEGATIVA").sum()),
    Tier_Dom=("Tier", lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else "Null"),
).reset_index()
prof2 = prof2[prof2["Total"] >= min_vol]

if len(prof2) > 0:
    top_neg = prof2.nlargest(10, "Negativa")
    top_pos = prof2.nlargest(10, "Positiva")
    comb = pd.concat([top_neg, top_pos]).drop_duplicates(subset="Veículo_de_comunicacao")
    comb["NSS"] = ((comb["Positiva"] - comb["Negativa"]) / comb["Total"] * 100).round(1)
    comb = comb.sort_values("NSS")
    comb["Label"] = comb.apply(
        lambda r: f"{TIER_EMOJI.get(r['Tier_Dom'], '⚪')} {r['Veículo_de_comunicacao']}", axis=1)

    fig = go.Figure()
    fig.add_trace(go.Bar(y=comb["Label"], x=-comb["Negativa"], orientation="h",
        name="Negativas", marker_color="#e74c3c", marker_opacity=0.85,
        text=comb["Negativa"].apply(lambda v: f"{int(v)}" if v > 0 else ""),
        textposition="inside", textfont=dict(color="white")))
    fig.add_trace(go.Bar(y=comb["Label"], x=comb["Positiva"], orientation="h",
        name="Positivas", marker_color="#2ecc71", marker_opacity=0.85,
        text=comb["Positiva"].apply(lambda v: f"{int(v)}" if v > 0 else ""),
        textposition="inside", textfont=dict(color="white")))
    fig.add_vline(x=0, line_width=2, line_color="#2c3e50")
    fig.update_layout(height=max(500, len(comb) * 32), barmode="relative",
        margin=dict(l=20, r=20, t=50, b=30),
        title="Promotores e Detratores — Volume Absoluto",
        legend=dict(orientation="h", y=-0.06, x=0.4))
    chart(fig)

st.divider()


# ═══════════════════════════════════════════════════════════════════════════
# SEÇÃO 7 — SUNBURST (composição interna)
# ═══════════════════════════════════════════════════════════════════════════

section("7. Composição Interna do Sentimento", "De que temas são feitas as menções positivas e negativas?")

narr("""
O <strong>Sunburst</strong> mostra a composição em anéis concêntricos.
O anel central é a <strong>Classificação</strong> (Positiva, Neutra, Negativa).
O anel externo mostra as <strong>Categorias</strong> dentro de cada sentimento.
<br><br>
<strong>Como ler:</strong> <strong>Clique em qualquer fatia</strong> para expandir e ver seus subtemas.
Clique no centro para voltar. O tamanho do arco é proporcional ao volume.
Isso responde: "das menções positivas, quais temas dominam?"
""")

sun = ds.groupby(["Classificação", "Categoria"]).size().reset_index(name="Total")
sun = sun[sun["Total"] >= 3]

if len(sun) > 0:
    fig = px.sunburst(sun, path=["Classificação", "Categoria"], values="Total",
        color="Classificação", color_discrete_map=COLORS)
    fig.update_layout(height=550, margin=dict(l=10, r=10, t=50, b=10),
        title="Sunburst — Classificação × Categoria")
    fig.update_traces(textinfo="label+percent parent", insidetextorientation="radial")
    chart(fig)


# ═══════════════════════════════════════════════════════════════════════════
# RODAPÉ
# ═══════════════════════════════════════════════════════════════════════════

st.divider()
st.markdown("""
<div style="text-align:center; padding:2rem; color:#a0aec0; font-size:0.85rem;">
    <strong>📊 Inteligência de Mídia</strong> · Dados: clipping de mídia (Google Sheets)<br>
    NSS = (Positivas − Negativas) / Total × 100 · Pesos: 🔴8× 🟠4× 🔵1× ⚪1×<br>
    Desenvolvido com Streamlit + Plotly · Análise de sentimento via fornecedor de clipping
</div>
""", unsafe_allow_html=True)
