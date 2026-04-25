"""
=================================================================================
DASHBOARD PREMIUM - Análise de Satisfação e Reputação na Mídia
=================================================================================
Versão com layout profissional e textos explicativos completos
=================================================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================================================

st.set_page_config(
    page_title="Análise de Reputação | Aegea",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CSS PROFISSIONAL
# =============================================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    /* Container principal */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }
    
    /* Hero section */
    .hero {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 3rem 2rem;
        border-radius: 16px;
        color: white;
        text-align: center;
        margin-bottom: 3rem;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
    }
    
    .hero h1 {
        font-size: 2.8rem;
        font-weight: 700;
        margin-bottom: 0.8rem;
        line-height: 1.2;
    }
    
    .hero p {
        font-size: 1.2rem;
        opacity: 0.95;
        font-weight: 300;
    }
    
    /* Metodologia box */
    .metodologia {
        background: linear-gradient(135deg, #f5f7fa 0%, #e9ecef 100%);
        border-left: 5px solid #667eea;
        padding: 2rem;
        border-radius: 12px;
        margin: 2rem 0;
    }
    
    .metodologia h3 {
        color: #2d3748;
        font-size: 1.5rem;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    
    .metodologia ul {
        line-height: 1.8;
        color: #4a5568;
    }
    
    .metodologia strong {
        color: #667eea;
        font-weight: 600;
    }
    
    /* Section titles */
    .section-header {
        font-size: 2rem;
        font-weight: 700;
        color: #2d3748;
        margin: 3rem 0 1.5rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #667eea;
    }
    
    /* Insight boxes */
    .insight {
        background: #f8f9ff;
        border-left: 4px solid #4c51bf;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border-radius: 8px;
    }
    
    .insight h4 {
        color: #4c51bf;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .insight p {
        color: #4a5568;
        margin: 0;
        line-height: 1.6;
    }
    
    /* Warning boxes */
    .warning {
        background: #fff5f5;
        border-left: 4px solid #e53e3e;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border-radius: 8px;
    }
    
    .warning h4 {
        color: #e53e3e;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    /* Success boxes */
    .success {
        background: #f0fff4;
        border-left: 4px solid #38a169;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border-radius: 8px;
    }
    
    .success h4 {
        color: #38a169;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    /* Métricas */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: #f7fafc;
    }
    
    /* Divider */
    .divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, #667eea, transparent);
        margin: 3rem 0;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# CORES PADRÃO
# =============================================================================

COLORS_SENTIMENT = {
    'POSITIVA': '#2ecc71',
    'NEUTRA': '#95a5a6',
    'NEGATIVA': '#e74c3c',
    'PUBLICIDADE': '#3498db'
}

# =============================================================================
# CARREGAR DADOS
# =============================================================================

@st.cache_data(ttl=3600)
def carregar_dados():
    """Carrega e processa dados do Google Sheets"""
    url = "https://docs.google.com/spreadsheets/d/1UVGM5g7A2pSmg4Nn5eTzjZhd25sAFFDbkBclRfyNgX8/export?format=csv"
    
    df = pd.read_csv(url)
    df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, format='mixed', errors='coerce')
    df = df.dropna(subset=['Data']).sort_values('Data')
    df['Ano_Mes'] = df['Data'].dt.to_period('M').astype(str)
    
    # Pesos Tier
    tier_weights = {'Muito Relevante': 8, 'Relevante': 4, 'Menos Relevante': 1}
    df['Peso'] = df['Tier'].map(tier_weights).fillna(1)
    
    # Limpeza
    df['Classificação'] = df['Classificação'].astype(str).str.strip()
    df['Tier'] = df['Tier'].fillna('Null')
    df['Categoria'] = df['Categoria'].fillna('Não Categorizado')
    df['Subcategoria'] = df['Subcategoria'].fillna('Não Especificado')
    df['Veículo_de_comunicacao'] = df['Veículo_de_comunicacao'].fillna('Não Informado')
    
    return df

# =============================================================================
# FUNÇÕES DE VISUALIZAÇÃO (DO NOTEBOOK)
# =============================================================================

def plot_classificacao_dinamica(class_counts: pd.Series):
    """Distribuição de sentimentos"""
    color_list = [COLORS_SENTIMENT.get(label, '#bdc3c7') for label in class_counts.index]
    
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "xy"}, {"type": "domain"}]],
        subplot_titles=("Frequência Absoluta", "Proporção Relativa"),
        horizontal_spacing=0.15
    )
    
    fig.add_trace(
        go.Bar(
            x=class_counts.index,
            y=class_counts.values,
            marker_color=color_list,
            showlegend=False,
            text=class_counts.values,
            textposition='auto',
            texttemplate='%{text:,}',
            hovertemplate='<b>%{x}</b><br>Menções: %{y:,}<extra></extra>'
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Pie(
            labels=class_counts.index,
            values=class_counts.values,
            marker=dict(colors=color_list),
            hole=0.4,
            textinfo='label+percent',
            textfont_size=14,
            hovertemplate='<b>%{label}</b><br>%{value:,} menções<br>%{percent}<extra></extra>'
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        title={
            'text': "<b>Distribuição de Sentimentos</b>",
            'font': {'size': 20}
        },
        template="plotly_white",
        height=450,
        showlegend=False
    )
    
    return fig

def plot_top_categorias(df_sentiment: pd.DataFrame, top_n: int = 10):
    """Top categorias"""
    df_sem_pub = df_sentiment[df_sentiment['Classificação'] != 'PUBLICIDADE']
    
    top_cat = df_sem_pub['Categoria'].value_counts().head(top_n).reset_index()
    top_cat.columns = ['Categoria', 'Contagem']
    top_cat = top_cat.sort_values('Contagem', ascending=True)
    
    fig = px.bar(
        top_cat,
        y='Categoria',
        x='Contagem',
        orientation='h',
        text='Contagem',
        color='Contagem',
        color_continuous_scale='Viridis',
        title=f'<b>Top {top_n} Categorias Mais Mencionadas</b>'
    )
    
    fig.update_traces(
        texttemplate='%{text:,}',
        textposition='auto',
        hovertemplate='<b>%{y}</b><br>Menções: %{x:,}<extra></extra>'
    )
    
    fig.update_layout(
        template='plotly_white',
        height=max(400, top_n * 35),
        margin=dict(l=200),
        xaxis_title="Número de Menções",
        yaxis_title="",
        showlegend=False
    )
    
    return fig

def plot_visualizacao_cauda_longa(df_input):
    """Curva de cauda longa"""
    df_w = df_input[~df_input['Veículo_de_comunicacao'].isin(['Geral', 'N/A', 'Vários'])]
    
    agrupado = df_w.groupby('Veículo_de_comunicacao').agg(
        Total=('Classificação', 'count'),
        Positiva=('Classificação', lambda x: (x == 'POSITIVA').sum()),
        Negativa=('Classificação', lambda x: (x == 'NEGATIVA').sum())
    ).sort_values('Total', ascending=False).reset_index()
    
    agrupado['Ranking'] = agrupado.index + 1
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=agrupado['Ranking'],
        y=agrupado['Positiva'],
        fill='tozeroy',
        line=dict(color='#2ecc71', width=2),
        name='Menções Positivas',
        text=agrupado['Veículo_de_comunicacao'],
        hovertemplate='<b>%{text}</b><br>Ranking: %{x}<br>Positivas: %{y}<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=agrupado['Ranking'],
        y=agrupado['Negativa'],
        fill='tozeroy',
        line=dict(color='#e74c3c', width=2),
        name='Menções Negativas',
        text=agrupado['Veículo_de_comunicacao'],
        hovertemplate='<b>%{text}</b><br>Ranking: %{x}<br>Negativas: %{y}<extra></extra>'
    ))
    
    fig.add_vline(
        x=20,
        line_dash="dash",
        line_color="#34495e",
        annotation_text="← Top 20 | Cauda Longa →",
        annotation_position="top right"
    )
    
    fig.update_layout(
        title='<b>Curva de Cauda Longa da Imprensa</b>',
        template='plotly_white',
        hovermode='x unified',
        height=500,
        xaxis_title='Ranking do Veículo (por volume total)',
        yaxis_title='Número de Menções',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def calcular_comparativo_nss(df_input):
    """NSS Simples vs Ponderado"""
    df_temp = df_input.copy()
    
    if 'Ano_Mes' not in df_temp.columns:
        df_temp['Data'] = pd.to_datetime(df_temp['Data'], errors='coerce')
        df_temp['Ano_Mes'] = df_temp['Data'].dt.to_period('M').astype(str)
    
    df_org = df_temp[df_temp['Classificação'] != 'PUBLICIDADE'].copy()
    
    temporal = []
    for mes in sorted(df_org['Ano_Mes'].unique()):
        subset = df_org[df_org['Ano_Mes'] == mes]
        total = len(subset)
        pos = (subset['Classificação'] == 'POSITIVA').sum()
        neg = (subset['Classificação'] == 'NEGATIVA').sum()
        nss_simples = ((pos - neg) / total * 100) if total > 0 else 0
        
        total_pond = subset['Peso'].sum()
        pos_pond = subset[subset['Classificação'] == 'POSITIVA']['Peso'].sum()
        neg_pond = subset[subset['Classificação'] == 'NEGATIVA']['Peso'].sum()
        nss_ponderado = ((pos_pond - neg_pond) / total_pond * 100) if total_pond > 0 else 0
        
        temporal.append({
            'Mes': mes,
            'NSS_Simples': round(nss_simples, 1),
            'NSS_Ponderado': round(nss_ponderado, 1)
        })
    
    df_temporal = pd.DataFrame(temporal)
    df_temporal['Data'] = pd.to_datetime(df_temporal['Mes'] + '-01')
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_temporal['Data'],
        y=df_temporal['NSS_Simples'],
        mode='lines+markers',
        name='NSS Simples',
        line=dict(color='#2ecc71', width=3),
        marker=dict(size=8),
        hovertemplate='NSS Simples: %{y:.1f}%<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=df_temporal['Data'],
        y=df_temporal['NSS_Ponderado'],
        mode='lines+markers',
        name='NSS Ponderado (Tier)',
        line=dict(color='#e74c3c', width=3, dash='dash'),
        marker=dict(size=8),
        hovertemplate='NSS Ponderado: %{y:.1f}%<extra></extra>'
    ))
    
    fig.add_hline(
        y=0,
        line_dash="dot",
        line_color="gray",
        annotation_text="Linha de Neutralidade",
        annotation_position="right"
    )
    
    fig.update_layout(
        title='<b>Comparativo: NSS Simples vs NSS Ponderado</b>',
        xaxis_title='Período',
        yaxis_title='NSS (%)',
        template='plotly_white',
        height=500,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def plot_matriz_espacial(df_input, min_n=1):
    """Matriz espacial NSS × Volume"""
    prof = df_input.groupby("Veículo_de_comunicacao").agg(
        Total=("Classificação", "count"),
        Positiva=("Classificação", lambda x: (x == "POSITIVA").sum()),
        Negativa=("Classificação", lambda x: (x == "NEGATIVA").sum())
    )
    
    prof = prof[prof["Total"] >= min_n].copy()
    prof["NSS"] = ((prof["Positiva"] - prof["Negativa"]) / prof["Total"] * 100).round(1)
    prof = prof.reset_index()
    
    if len(prof) == 0:
        return go.Figure().add_annotation(
            text=f"Sem dados com mínimo de {min_n} menções",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=16)
        )
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=prof["Total"],
        y=prof["NSS"],
        mode="markers",
        marker=dict(
            size=prof["Total"],
            sizemode='area',
            sizeref=2.*max(prof["Total"])/(60.**2),
            sizemin=8,
            color=prof["NSS"],
            colorscale=[[0, "#e74c3c"], [0.5, "#bdc3c7"], [1, "#2ecc71"]],
            showscale=True,
            colorbar=dict(title="NSS (%)")
        ),
        text=prof["Veículo_de_comunicacao"],
        hovertemplate='<b>%{text}</b><br>Volume: %{x}<br>NSS: %{y}%<extra></extra>'
    ))
    
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="#34495e",
        annotation_text="Neutralidade",
        annotation_position="left"
    )
    
    fig.update_layout(
        title=f'<b>Matriz Espacial: Sentimento × Volume (mín. {min_n} menções)</b>',
        xaxis_title="Volume Absoluto (quantidade de menções)",
        yaxis_title="NSS - Net Sentiment Score (%)",
        template="plotly_white",
        height=600
    )
    
    return fig

def plot_piramides_veiculo_absoluto(df_input: pd.DataFrame, top_n: int = 20):
    """Pirâmides de veículos"""
    df_work = df_input.copy()
    df_work = df_work[~df_work['Veículo_de_comunicacao'].isin(['Geral', 'N/A', 'Vários'])]
    
    # Negativos
    neg = df_work[df_work['Classificação'] == 'NEGATIVA']
    top_neg = neg['Veículo_de_comunicacao'].value_counts().head(top_n).reset_index()
    top_neg.columns = ['Veículo', 'Total']
    top_neg = top_neg.sort_values('Total', ascending=True)
    
    # Positivos
    pos = df_work[df_work['Classificação'] == 'POSITIVA']
    top_pos = pos['Veículo_de_comunicacao'].value_counts().head(top_n).reset_index()
    top_pos.columns = ['Veículo', 'Total']
    top_pos = top_pos.sort_values('Total', ascending=True)
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(f'Top {top_n} Veículos NEGATIVOS', f'Top {top_n} Veículos POSITIVOS'),
        horizontal_spacing=0.15
    )
    
    fig.add_trace(
        go.Bar(
            y=top_neg['Veículo'],
            x=top_neg['Total'],
            orientation='h',
            marker_color='#e74c3c',
            showlegend=False,
            text=top_neg['Total'],
            textposition='auto',
            hovertemplate='<b>%{y}</b><br>Menções negativas: %{x}<extra></extra>'
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(
            y=top_pos['Veículo'],
            x=top_pos['Total'],
            orientation='h',
            marker_color='#2ecc71',
            showlegend=False,
            text=top_pos['Total'],
            textposition='auto',
            hovertemplate='<b>%{y}</b><br>Menções positivas: %{x}<extra></extra>'
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        title=f'<b>Pirâmides: Top {top_n} Veículos por Sentimento</b>',
        template='plotly_white',
        height=max(600, top_n*25)
    )
    
    return fig

def plot_treemap_tier_categoria(df_input: pd.DataFrame, min_mentions: int = 10):
    """Treemap Tier × Categoria"""
    df_work = df_input.copy()
    df_work['Tier'] = df_work['Tier'].fillna('Null')
    df_work['Categoria'] = df_work['Categoria'].fillna('Sem Categoria')
    
    tree_data = df_work.groupby(['Tier', 'Categoria']).size().reset_index(name='Total')
    tree_data = tree_data[tree_data['Total'] >= min_mentions]
    
    if tree_data.empty:
        return go.Figure().add_annotation(
            text=f"Sem dados com mínimo de {min_mentions} menções",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=16)
        )
    
    fig = px.treemap(
        tree_data,
        path=['Tier', 'Categoria'],
        values='Total',
        title='<b>Treemap: Hierarquia Tier × Categoria</b>'
    )
    
    fig.update_layout(height=600, margin=dict(l=10, r=10, t=60, b=10))
    fig.update_traces(textinfo="label+value")
    
    return fig

def plot_heatmap_temporal_categoria(df_input: pd.DataFrame, top_n: int = 10, min_monthly: int = 3):
    """Heatmap temporal"""
    df_work = df_input[df_input['Classificação'] != 'PUBLICIDADE'].copy()
    
    if 'Ano_Mes' not in df_work.columns:
        df_work['Data'] = pd.to_datetime(df_work['Data'], errors='coerce')
        df_work['Ano_Mes'] = df_work['Data'].dt.to_period('M').astype(str)
    
    top_cats = df_work['Categoria'].value_counts().head(top_n).index.tolist()
    df_work = df_work[df_work['Categoria'].isin(top_cats)]
    
    results = []
    for cat in top_cats:
        for mes in sorted(df_work['Ano_Mes'].unique()):
            subset = df_work[(df_work['Categoria'] == cat) & (df_work['Ano_Mes'] == mes)]
            n = len(subset)
            if n >= min_monthly:
                pos = (subset['Classificação'] == 'POSITIVA').sum()
                neg = (subset['Classificação'] == 'NEGATIVA').sum()
                nss = round((pos - neg) / n * 100, 1)
            else:
                nss = np.nan
            results.append({
                'Categoria': cat, 'Mês': mes, 'NSS': nss,
                'N': n, 'Pos': pos if n >= min_monthly else 0,
                'Neg': neg if n >= min_monthly else 0
            })
    
    heat_df = pd.DataFrame(results)
    heat_pivot = heat_df.pivot(index='Categoria', columns='Mês', values='NSS').reindex(top_cats)
    n_pivot = heat_df.pivot(index='Categoria', columns='Mês', values='N').reindex(top_cats)
    pos_pivot = heat_df.pivot(index='Categoria', columns='Mês', values='Pos').reindex(top_cats)
    neg_pivot = heat_df.pivot(index='Categoria', columns='Mês', values='Neg').reindex(top_cats)
    
    customdata = np.dstack((n_pivot.values, pos_pivot.values, neg_pivot.values))
    
    fig = go.Figure(go.Heatmap(
        z=heat_pivot.values,
        x=heat_pivot.columns.tolist(),
        y=heat_pivot.index.tolist(),
        customdata=customdata,
        colorscale=[
            [0.0, '#c0392b'], [0.3, '#e74c3c'], [0.5, '#fdfefe'],
            [0.7, '#82e0aa'], [1.0, '#1e8449']
        ],
        zmid=0,
        colorbar=dict(title='NSS (%)'),
        hovertemplate=(
            '<b>%{y}</b><br>'
            'Mês: %{x}<br>'
            'NSS: %{z:+.1f}%<br>'
            'Positivos: %{customdata[1]:.0f}<br>'
            'Negativos: %{customdata[2]:.0f}<br>'
            'Total: %{customdata[0]:.0f}<extra></extra>'
        )
    ))
    
    fig.update_layout(
        title='<b>Heatmap Temporal: NSS por Categoria × Mês</b>',
        template='plotly_white',
        height=500,
        yaxis=dict(autorange='reversed')
    )
    
    return fig

def plot_sunburst_composicao(df_input: pd.DataFrame, min_mentions: int = 5):
    """Sunburst composição"""
    df_work = df_input[df_input['Classificação'] != 'PUBLICIDADE'].copy()
    
    sun_data = df_work.groupby(['Classificação', 'Categoria', 'Subcategoria']).size().reset_index(name='Total')
    sun_data = sun_data[sun_data['Total'] >= min_mentions]
    
    if sun_data.empty:
        return go.Figure().add_annotation(
            text=f"Sem dados com mínimo de {min_mentions} menções",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=16)
        )
    
    fig = px.sunburst(
        sun_data,
        path=['Classificação', 'Categoria', 'Subcategoria'],
        values='Total',
        color='Classificação',
        color_discrete_map=COLORS_SENTIMENT,
        title='<b>Sunburst: Classificação × Categoria × Subcategoria</b>'
    )
    
    fig.update_layout(height=700, margin=dict(l=10, r=10, t=60, b=10))
    
    return fig

def plot_sunburst_tier(df_input: pd.DataFrame, min_mentions: int = 5):
    """Sunburst Tier"""
    df_work = df_input[df_input['Classificação'] != 'PUBLICIDADE'].copy()
    df_work['Tier'] = df_work['Tier'].fillna('Null')
    
    sun_data = df_work.groupby(['Tier', 'Categoria', 'Classificação']).size().reset_index(name='Total')
    sun_data = sun_data[sun_data['Total'] >= min_mentions]
    
    if sun_data.empty:
        return go.Figure().add_annotation(
            text=f"Sem dados com mínimo de {min_mentions} menções",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=16)
        )
    
    fig = px.sunburst(
        sun_data,
        path=['Tier', 'Categoria', 'Classificação'],
        values='Total',
        color='Classificação',
        color_discrete_map=COLORS_SENTIMENT,
        title='<b>Sunburst: Tier × Categoria × Classificação</b>'
    )
    
    fig.update_layout(height=700, margin=dict(l=10, r=10, t=60, b=10))
    
    return fig

# =============================================================================
# INTERFACE PRINCIPAL
# =============================================================================

def main():
    # Carregar dados
    with st.spinner('🔄 Carregando dados...'):
        df = carregar_dados()
    
    if df.empty:
        st.error("❌ Erro ao carregar dados.")
        return
    
    # ==========================================================================
    # SIDEBAR - FILTROS
    # ==========================================================================
    
    st.sidebar.title("🎛️ Painel de Controle")
    st.sidebar.markdown("---")
    
    # Filtro de Grupo
    grupos = ['Todos'] + sorted(df['Grupo'].dropna().unique().tolist())
    grupo_sel = st.sidebar.selectbox("🏢 Grupo Empresarial", grupos, index=0)
    
    # Filtro de Empresa
    if grupo_sel != 'Todos':
        empresas = ['Todas'] + sorted(df[df['Grupo'] == grupo_sel]['Empresa'].dropna().unique().tolist())
    else:
        empresas = ['Todas'] + sorted(df['Empresa'].dropna().unique().tolist())
    
    empresa_sel = st.sidebar.selectbox("🏭 Empresa", empresas, index=0)
    
    # Filtro de Período
    st.sidebar.markdown("---")
    st.sidebar.markdown("**📅 Período de Análise**")
    
    data_min = df['Data'].min().date()
    data_max = df['Data'].max().date()
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        data_inicio = st.date_input("De", value=data_min, min_value=data_min, max_value=data_max)
    with col2:
        data_fim = st.date_input("Até", value=data_max, min_value=data_min, max_value=data_max)
    
    # Aplicar filtros
    df_filtrado = df.copy()
    
    if grupo_sel != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Grupo'] == grupo_sel]
    
    if empresa_sel != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['Empresa'] == empresa_sel]
    
    df_filtrado = df_filtrado[
        (df_filtrado['Data'] >= pd.to_datetime(data_inicio)) &
        (df_filtrado['Data'] <= pd.to_datetime(data_fim))
    ]
    
    # Métricas na Sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("**📊 Indicadores Gerais**")
    
    total_mencoes = len(df_filtrado)
    st.sidebar.metric("📰 Total de Menções", f"{total_mencoes:,}")
    
    df_org = df_filtrado[df_filtrado['Classificação'] != 'PUBLICIDADE']
    st.sidebar.metric("✨ Menções Orgânicas", f"{len(df_org):,}")
    
    if len(df_org) > 0:
        pos = (df_org['Classificação'] == 'POSITIVA').sum()
        neg = (df_org['Classificação'] == 'NEGATIVA').sum()
        nss = ((pos - neg) / len(df_org) * 100)
        
        delta_color = "normal" if nss >= 0 else "inverse"
        st.sidebar.metric(
            "🎯 NSS Global",
            f"{nss:+.1f}%",
            delta=f"{abs(nss):.1f}% {'acima' if nss >= 0 else 'abaixo'} da neutralidade"
        )
    
    # ==========================================================================
    # HERO SECTION
    # ==========================================================================
    
    st.markdown("""
    <div class="hero">
        <h1>📊 Análise de Satisfação e Reputação na Mídia</h1>
        <p>Dashboard de Inteligência de Dados | Metodologia NSS Ponderada por Tier</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ==========================================================================
    # METODOLOGIA
    # ==========================================================================
    
    st.markdown("###  Metodologia de Análise")

    st.markdown("""
Este dashboard não conta apenas quantas vezes a marca apareceu na mídia, mas **mede a qualidade e o impacto dessas aparições**.

- ** Princípios da Análise:**

- **O Filtro Orgânico:** Removemos toda a "Publicidade" paga. Só analisamos o que a mídia falou de forma espontânea.

- **O Peso da Voz (Tier):** Veículos classificados como **Muito Relevantes (peso 8)**, **Relevantes (peso 4)** e **Menos Relevantes (peso 1)**. Uma escala exponencial que amplifica propositalmente a diferença entre Tiers para capturar a realidade de audiência.

- **O Indicador NSS (Net Sentiment Score):** Funciona como um "saldo bancário" da imagem. Fórmula: `(Positivas − Negativas) / Total × 100`. Valores acima de zero são saudáveis; abaixo de zero exigem alerta.
""")
    
    # ==========================================================================
    # SEÇÃO 1: DISTRIBUIÇÃO
    # ==========================================================================
    
    st.markdown('<div class="section-header">1️⃣ Distribuição de Sentimentos</div>', unsafe_allow_html=True)
    
    df_sem_pub = df_filtrado[df_filtrado['Classificação'] != 'PUBLICIDADE']
    
    if len(df_sem_pub) > 0:
        st.plotly_chart(
            plot_classificacao_dinamica(df_sem_pub['Classificação'].value_counts()),
            use_container_width=True
        )
        
        # Insight
        pos_pct = (df_sem_pub['Classificação'] == 'POSITIVA').sum() / len(df_sem_pub) * 100
        neg_pct = (df_sem_pub['Classificação'] == 'NEGATIVA').sum() / len(df_sem_pub) * 100
        
        if pos_pct > neg_pct:
            st.markdown(f"""
            <div class="success">
                <h4>💚 Saldo Positivo</h4>
                <p>O sentimento predominante é <strong>positivo</strong> ({pos_pct:.1f}% das menções), 
                superando as menções negativas ({neg_pct:.1f}%). Isso indica uma reputação favorável no período analisado.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="warning">
                <h4>⚠️ Saldo Negativo</h4>
                <p>O sentimento predominante é <strong>negativo</strong> ({neg_pct:.1f}% das menções), 
                superando as menções positivas ({pos_pct:.1f}%). Isso exige atenção na gestão de reputação.</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # ==========================================================================
    # SEÇÃO 2: TOP CATEGORIAS
    # ==========================================================================
    
    st.markdown('<div class="section-header">2️⃣ Agenda Temática: O Que Se Fala</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="insight">
        <h4>📋 Interpretação</h4>
        <p>Esta análise revela quais temas dominam a conversa na mídia. 
        Categorias com alto volume indicam temas de interesse público ou pontos de atenção da empresa.</p>
    </div>
    """, unsafe_allow_html=True)
    
    top_n_cat = st.slider("Número de categorias a exibir", 5, 20, 10, key='top_cat')
    
    st.plotly_chart(
        plot_top_categorias(df_filtrado, top_n_cat),
        use_container_width=True
    )
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # ==========================================================================
    # SEÇÃO 3: CAUDA LONGA
    # ==========================================================================
    
    st.markdown('<div class="section-header">3️⃣ Curva de Cauda Longa da Imprensa</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="insight">
        <h4>📊 Lei de Pareto na Mídia</h4>
        <p>A <strong>Lei de Pareto</strong> (80/20) se manifesta: poucos veículos (Top 20) concentram 
        a maioria das menções, enquanto a "cauda longa" representa centenas de veículos menores. 
        Esta visualização separa o "barulho" (volume) da relevância (Tier).</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.plotly_chart(
        plot_visualizacao_cauda_longa(df_filtrado),
        use_container_width=True
    )
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # ==========================================================================
    # SEÇÃO 4: NSS COMPARATIVO
    # ==========================================================================
    
    st.markdown('<div class="section-header">4️⃣ NSS Simples vs NSS Ponderado: A Ilusão do Volume</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="warning">
        <h4>⚠️ Por Que Dois Indicadores?</h4>
        <p><strong>NSS Simples</strong> trata todas as menções igualmente (1 blog = 1 Globo).<br>
        <strong>NSS Ponderado</strong> aplica os pesos por Tier, revelando o impacto real.<br><br>
        
        Quando o NSS Ponderado é <strong>menor</strong> que o Simples, significa que veículos de alto impacto 
        estão mais negativos — um sinal de alerta que o volume bruto mascara.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.plotly_chart(
        calcular_comparativo_nss(df_filtrado),
        use_container_width=True
    )
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # ==========================================================================
    # SEÇÃO 5: MATRIZ ESPACIAL
    # ==========================================================================
    
    st.markdown('<div class="section-header">5️⃣ Matriz Espacial: NSS × Volume</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="insight">
        <h4>🎯 Quadrantes Estratégicos</h4>
        <p>Esta matriz posiciona cada veículo em dois eixos:<br>
        • <strong>Eixo X (Volume):</strong> Quantidade de menções<br>
        • <strong>Eixo Y (NSS):</strong> Qualidade do sentimento<br><br>
        
        <strong>Quadrante superior direito:</strong> Alto volume + sentimento positivo (ideal)<br>
        <strong>Quadrante inferior direito:</strong> Alto volume + sentimento negativo (atenção!)</p>
    </div>
    """, unsafe_allow_html=True)
    
    min_n_matriz = st.slider("Mínimo de menções para aparecer", 1, 20, 5, key='matriz')
    
    st.plotly_chart(
        plot_matriz_espacial(df_filtrado, min_n_matriz),
        use_container_width=True
    )
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # ==========================================================================
    # SEÇÃO 6: PIRÂMIDES
    # ==========================================================================
    
    st.markdown('<div class="section-header">6️⃣ Pirâmides: Maiores Influenciadores</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="insight">
        <h4>📡 Mapeamento de Fontes</h4>
        <p>Identifica quais veículos concentram as menções positivas e negativas. 
        Útil para estratégias de relacionamento com a imprensa e gestão de crise.</p>
    </div>
    """, unsafe_allow_html=True)
    
    top_n_pir = st.slider("Top N veículos", 5, 30, 20, key='piramides')
    
    st.plotly_chart(
        plot_piramides_veiculo_absoluto(df_filtrado, top_n_pir),
        use_container_width=True
    )
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # ==========================================================================
    # SEÇÃO 7: TREEMAP
    # ==========================================================================
    
    st.markdown('<div class="section-header">7️⃣ Treemap: Hierarquia Tier × Categoria</div>', unsafe_allow_html=True)
    
    min_tree = st.slider("Mínimo de menções", 5, 20, 10, key='tree')
    
    st.plotly_chart(
        plot_treemap_tier_categoria(df_filtrado, min_tree),
        use_container_width=True
    )
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # ==========================================================================
    # SEÇÃO 8: HEATMAP
    # ==========================================================================
    
    st.markdown('<div class="section-header">8️⃣ Heatmap Temporal: Evolução por Categoria</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="insight">
        <h4>🔥 Mapa de Calor</h4>
        <p>Células vermelhas indicam NSS negativo; células verdes indicam NSS positivo. 
        Permite identificar em qual período e categoria houve deterioração ou melhora de imagem.</p>
    </div>
    """, unsafe_allow_html=True)
    
    top_n_heat = st.slider("Top N categorias", 5, 15, 10, key='heat')
    
    st.plotly_chart(
        plot_heatmap_temporal_categoria(df_filtrado, top_n_heat),
        use_container_width=True
    )
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # ==========================================================================
    # SEÇÃO 9 & 10: SUNBURSTS
    # ==========================================================================
    
    st.markdown('<div class="section-header">9️⃣ Composição Hierárquica</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Sunburst: Classificação × Categoria**")
        min_sun1 = st.slider("Mín. menções", 3, 10, 5, key='sun1')
    
    with col2:
        st.markdown("**Sunburst: Tier × Categoria**")
        min_sun2 = st.slider("Mín. menções", 3, 10, 5, key='sun2')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(
            plot_sunburst_composicao(df_filtrado, min_sun1),
            use_container_width=True
        )
    
    with col2:
        st.plotly_chart(
            plot_sunburst_tier(df_filtrado, min_sun2),
            use_container_width=True
        )
    
    # ==========================================================================
    # FOOTER
    # ==========================================================================
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; color: #718096; padding: 2rem;">
        <p><strong>Dashboard de Inteligência de Reputação</strong></p>
        <p>Metodologia: NSS Ponderado por Tier | Dados atualizados automaticamente</p>
        <p style="font-size: 0.9rem; margin-top: 1rem;">
            📊 Desenvolvido com Streamlit + Plotly | 
            🔄 Última atualização: {data_max.strftime("%d/%m/%Y")}
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
