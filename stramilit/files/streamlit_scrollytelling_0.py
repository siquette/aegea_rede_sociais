"""
=================================================================================
ANÁLISE DE SENTIMENTO DE MÍDIA - SCROLLYTELLING INTERATIVO
=================================================================================

Aplicação Streamlit com narrativa scrolling para análise de clipping de mídia.
Implementa conceitos de Behavioral Data Science (Florent Buisson).

Autor: Análise de Satisfação - Saneamento
Data: 2025
=================================================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURAÇÃO GLOBAL
# =============================================================================

st.set_page_config(
    page_title="Análise de Sentimento | Mídia",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS CUSTOMIZADO PARA SCROLLYTELLING
st.markdown("""
<style>
    /* Importar fonte Inter */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    /* Reset e base */
    * {
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Remover padding padrão do Streamlit */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
        max-width: 1200px;
    }
    
    /* Hero section */
    .hero-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 4rem 2rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 3rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .hero-title {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 1rem;
        line-height: 1.2;
    }
    
    .hero-subtitle {
        font-size: 1.3rem;
        font-weight: 400;
        opacity: 0.95;
    }
    
    /* Seções narrativas */
    .narrative-section {
        background: white;
        padding: 3rem 2rem;
        border-radius: 8px;
        margin: 2rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border-left: 4px solid #667eea;
    }
    
    .section-title {
        font-size: 2rem;
        font-weight: 700;
        color: #2d3748;
        margin-bottom: 1rem;
        border-bottom: 3px solid #2ecc71;
        padding-bottom: 0.5rem;
    }
    
    .section-subtitle {
        font-size: 1.2rem;
        color: #4a5568;
        margin-bottom: 1.5rem;
        font-weight: 600;
    }
    
    .narrative-text {
        font-size: 1.1rem;
        line-height: 1.8;
        color: #2d3748;
        margin-bottom: 2rem;
    }
    
    /* Destaque de insights */
    .insight-box {
        background: #f7fafc;
        border-left: 5px solid #2ecc71;
        padding: 1.5rem;
        margin: 2rem 0;
        border-radius: 4px;
    }
    
    .insight-box.warning {
        border-left-color: #e74c3c;
        background: #fef5f5;
    }
    
    .insight-box.info {
        border-left-color: #3498db;
        background: #f0f8ff;
    }
    
    /* Métricas */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-top: 4px solid #667eea;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #2d3748;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #718096;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 0.5rem;
    }
    
    /* Filtros */
    .stSelectbox, .stDateInput, .stSlider {
        margin-bottom: 1rem;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: #f7fafc;
    }
    
    /* Botões */
    .stButton>button {
        background: #667eea;
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        background: #5568d3;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* Espaçamento entre seções */
    .section-spacer {
        height: 3rem;
    }
    
    /* Fórmula NSS */
    .formula-box {
        background: #2d3748;
        color: white;
        padding: 2rem;
        border-radius: 8px;
        text-align: center;
        font-size: 1.3rem;
        font-weight: 600;
        margin: 2rem 0;
        font-family: 'Courier New', monospace !important;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# PALETA DE CORES GLOBAL
# =============================================================================

COLORS_SENTIMENT = {
    'POSITIVA': '#2ecc71',
    'NEUTRA': '#95a5a6',
    'NEGATIVA': '#e74c3c',
    'PUBLICIDADE': '#3498db'
}

# =============================================================================
# FUNÇÕES DE CARREGAMENTO DE DADOS
# =============================================================================

@st.cache_data(ttl=3600)
def carregar_dados():
    """Carrega dados do Google Sheets com cache de 1 hora"""
    url = "https://docs.google.com/spreadsheets/d/1UVGM5g7A2pSmg4Nn5eTzjZhd25sAFFDbkBclRfyNgX8/export?format=csv"
    
    try:
        df = pd.read_csv(url)
        
        # Conversão de datas
        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, format='mixed', errors='coerce')
        df = df.dropna(subset=['Data'])
        df = df.sort_values('Data')
        
        # Engenharia de features temporais
        df['Ano_Mes'] = df['Data'].dt.to_period('M').astype(str)
        df['Ano'] = df['Data'].dt.year
        df['Mes'] = df['Data'].dt.month
        df['Dia_Semana'] = df['Data'].dt.day_name()
        
        # Pesos por Tier
        tier_weights = {
            'Muito Relevante': 8,
            'Relevante': 4,
            'Menos Relevante': 1,
            'Null': 1
        }
        df['Peso'] = df['Tier'].map(tier_weights).fillna(1)
        
        # Tratamento de nulos
        df['Mídia'] = df['Mídia'].fillna('Não Informado')
        df['Veículo_de_comunicacao'] = df['Veículo_de_comunicacao'].fillna('Não Informado')
        df['Categoria'] = df['Categoria'].fillna('Não Categorizado')
        df['Subcategoria'] = df['Subcategoria'].fillna('Não Especificado')
        df['Tier'] = df['Tier'].fillna('Null')
        
        return df
    
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

def aplicar_filtros_globais(df, grupo, empresa, data_inicio, data_fim):
    """Aplica filtros globais ao DataFrame"""
    df_filtrado = df.copy()
    
    if grupo != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Grupo'] == grupo]
    
    if empresa != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['Empresa'] == empresa]
    
    if data_inicio and data_fim:
        df_filtrado = df_filtrado[
            (df_filtrado['Data'] >= pd.to_datetime(data_inicio)) &
            (df_filtrado['Data'] <= pd.to_datetime(data_fim))
        ]
    
    return df_filtrado

# =============================================================================
# FUNÇÕES DE VISUALIZAÇÃO
# =============================================================================

def plot_classificacao_dinamica(df_input):
    """Distribuição de sentimentos: barras + pizza"""
    df_work = df_input[df_input['Classificação'] != 'PUBLICIDADE'].copy()
    class_counts = df_work['Classificação'].value_counts()
    
    color_list = [COLORS_SENTIMENT.get(label, '#bdc3c7') for label in class_counts.index]
    
    fig = make_subplots(
        rows=1, cols=2, 
        specs=[[{"type": "xy"}, {"type": "domain"}]],
        subplot_titles=("Frequência Absoluta", "Proporção (Share)")
    )
    
    # Barras
    fig.add_trace(
        go.Bar(
            x=class_counts.index, 
            y=class_counts.values, 
            marker_color=color_list, 
            showlegend=False,
            text=class_counts.values,
            textposition='auto',
            texttemplate='%{text:,}'
        ), 
        row=1, col=1
    )
    
    # Pizza
    fig.add_trace(
        go.Pie(
            labels=class_counts.index, 
            values=class_counts.values, 
            marker=dict(colors=color_list), 
            hole=0.4,
            textinfo='percent+label',
            textfont=dict(size=13)
        ), 
        row=1, col=2
    )
    
    fig.update_layout(
        title_text="<b>Distribuição Global de Sentimentos</b><br><sup>Visão Panorâmica: Volume vs Proporção</sup>",
        template="plotly_white", 
        height=450,
        font=dict(family='Inter, Arial', size=12)
    )
    
    return fig

def plot_top_categorias(df_input, classificacao='Todas', top_n=10):
    """Top N categorias com filtro de sentimento"""
    df_work = df_input[df_input['Classificação'] != 'PUBLICIDADE'].copy()
    
    if classificacao != 'Todas':
        df_work = df_work[df_work['Classificação'] == classificacao]
    
    top_cat = df_work['Categoria'].value_counts().head(top_n).reset_index()
    top_cat.columns = ['Categoria', 'Contagem']
    top_cat = top_cat.sort_values(by='Contagem', ascending=True)
    
    titulo_base = f'Top {top_n} Categorias'
    if classificacao != 'Todas':
        titulo_base += f' ({classificacao}s)'
    
    fig = px.bar(
        top_cat, 
        y='Categoria', 
        x='Contagem', 
        orientation='h',
        text='Contagem',
        title=f'<b>{titulo_base}</b><br><sup>O que a mídia está falando?</sup>',
        color='Contagem', 
        color_continuous_scale='Viridis'
    )
    
    fig.update_layout(
        template="plotly_white", 
        height=max(400, top_n * 35),
        margin=dict(l=180, r=30, t=80, b=50),
        font=dict(family='Inter, Arial', size=12)
    )
    
    fig.update_traces(texttemplate='%{text:,}', textposition='outside')
    
    return fig

def plot_volume_temporal(df_input, agregacao='Mês'):
    """Volume de menções ao longo do tempo"""
    df_work = df_input.copy()
    
    if agregacao == 'Dia':
        df_work['Periodo'] = df_work['Data']
        formato_x = '%d/%m/%Y'
    elif agregacao == 'Semana':
        df_work['Periodo'] = df_work['Data'].dt.to_period('W').dt.start_time
        formato_x = 'Semana %U/%Y'
    else:  # Mês
        df_work['Periodo'] = df_work['Data'].dt.to_period('M').dt.to_timestamp()
        formato_x = '%b/%Y'
    
    temporal = df_work.groupby('Periodo').size().reset_index(name='Volume')
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=temporal['Periodo'],
        y=temporal['Volume'],
        mode='lines+markers',
        line=dict(color='#667eea', width=3),
        marker=dict(size=8, color='#667eea'),
        fill='tozeroy',
        fillcolor='rgba(102, 126, 234, 0.1)',
        name='Volume',
        hovertemplate='<b>%{x}</b><br>Volume: %{y:,}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f'<b>Evolução Temporal do Volume de Menções</b><br><sup>Agregação: {agregacao}</sup>',
        xaxis_title='Período',
        yaxis_title='Número de Menções',
        template='plotly_white',
        height=450,
        font=dict(family='Inter, Arial', size=12),
        hovermode='x unified'
    )
    
    return fig

def plot_distribuicao_semanal(df_input):
    """Distribuição por dia da semana"""
    df_work = df_input.copy()
    
    # Ordem correta dos dias
    dias_ordem = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    dias_pt = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    
    semanal = df_work['Dia_Semana'].value_counts().reindex(dias_ordem).reset_index()
    semanal.columns = ['Dia', 'Volume']
    semanal['Dia_PT'] = dias_pt
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=semanal['Dia_PT'],
        y=semanal['Volume'],
        marker_color='#667eea',
        text=semanal['Volume'],
        texttemplate='%{text:,}',
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Volume: %{y:,}<extra></extra>'
    ))
    
    fig.update_layout(
        title='<b>Distribuição por Dia da Semana</b><br><sup>Quando a mídia publica?</sup>',
        xaxis_title='Dia da Semana',
        yaxis_title='Volume de Menções',
        template='plotly_white',
        height=400,
        font=dict(family='Inter, Arial', size=12)
    )
    
    return fig

def plot_tier_classificacao(df_input, categoria_filtro=None):
    """Heatmap Tier × Classificação"""
    df_work = df_input[df_input['Classificação'] != 'PUBLICIDADE'].copy()
    
    if categoria_filtro and categoria_filtro != 'Todas':
        df_work = df_work[df_work['Categoria'] == categoria_filtro]
    
    # Contingência
    contingency = pd.crosstab(
        df_work['Tier'],
        df_work['Classificação'],
        normalize='index'
    ) * 100
    
    # Ordenar tiers
    tier_order = ['Muito Relevante', 'Relevante', 'Menos Relevante', 'Null']
    contingency = contingency.reindex([t for t in tier_order if t in contingency.index])
    
    # Ordenar classificações
    class_order = ['POSITIVA', 'NEUTRA', 'NEGATIVA']
    contingency = contingency[[c for c in class_order if c in contingency.columns]]
    
    fig = go.Figure()
    
    for col in contingency.columns:
        fig.add_trace(go.Bar(
            name=col,
            x=contingency.index,
            y=contingency[col],
            marker_color=COLORS_SENTIMENT.get(col, '#bdc3c7'),
            text=contingency[col].round(1),
            texttemplate='%{text}%',
            textposition='inside',
            hovertemplate='<b>%{x}</b><br>' + col + ': %{y:.1f}%<extra></extra>'
        ))
    
    titulo = '<b>Tier × Classificação: Composição de Sentimento</b><br><sup>Como cada Tier distribui suas menções?</sup>'
    if categoria_filtro and categoria_filtro != 'Todas':
        titulo = f'<b>Tier × Classificação: {categoria_filtro}</b><br><sup>Categoria filtrada</sup>'
    
    fig.update_layout(
        title=titulo,
        xaxis_title='Tier de Relevância',
        yaxis_title='Proporção (%)',
        barmode='stack',
        template='plotly_white',
        height=450,
        font=dict(family='Inter, Arial', size=12),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def plot_nss_temporal(df_input, categoria_filtro=None, modo='simples'):
    """Evolução do NSS ao longo do tempo"""
    df_work = df_input[df_input['Classificação'] != 'PUBLICIDADE'].copy()
    
    if categoria_filtro and categoria_filtro != 'Todas':
        df_work = df_work[df_work['Categoria'] == categoria_filtro]
    
    # Calcular NSS por mês
    temporal = []
    for mes in sorted(df_work['Ano_Mes'].unique()):
        subset = df_work[df_work['Ano_Mes'] == mes]
        total = len(subset)
        pos = (subset['Classificação'] == 'POSITIVA').sum()
        neg = (subset['Classificação'] == 'NEGATIVA').sum()
        
        if modo == 'ponderado':
            total_pond = subset['Peso'].sum()
            pos_pond = subset[subset['Classificação'] == 'POSITIVA']['Peso'].sum()
            neg_pond = subset[subset['Classificação'] == 'NEGATIVA']['Peso'].sum()
            nss = ((pos_pond - neg_pond) / total_pond * 100) if total_pond > 0 else 0
        else:
            nss = ((pos - neg) / total * 100) if total > 0 else 0
        
        temporal.append({
            'Mes': mes,
            'NSS': nss,
            'Volume': total,
            'Positivos': pos,
            'Negativos': neg
        })
    
    df_temporal = pd.DataFrame(temporal)
    df_temporal['Data'] = pd.to_datetime(df_temporal['Mes'] + '-01')
    
    fig = go.Figure()
    
    # Linha NSS
    fig.add_trace(go.Scatter(
        x=df_temporal['Data'],
        y=df_temporal['NSS'],
        mode='lines+markers',
        name='NSS',
        line=dict(color='#667eea', width=3),
        marker=dict(size=10, color='#667eea'),
        customdata=np.stack((
            df_temporal['Volume'],
            df_temporal['Positivos'],
            df_temporal['Negativos']
        ), axis=-1),
        hovertemplate=(
            '<b>%{x|%b/%Y}</b><br>'
            'NSS: %{y:+.1f}<br>'
            'Positivos: %{customdata[1]}<br>'
            'Negativos: %{customdata[2]}<br>'
            'Volume: %{customdata[0]}'
            '<extra></extra>'
        )
    ))
    
    # Linha zero
    fig.add_hline(
        y=0, 
        line_dash="dash", 
        line_color="gray", 
        annotation_text="Equilíbrio",
        annotation_position="right"
    )
    
    titulo = f'<b>Evolução do NSS ao Longo do Tempo</b><br><sup>Modo: {modo.title()}</sup>'
    if categoria_filtro and categoria_filtro != 'Todas':
        titulo = f'<b>NSS Temporal: {categoria_filtro}</b><br><sup>Modo: {modo.title()}</sup>'
    
    fig.update_layout(
        title=titulo,
        xaxis_title='Período',
        yaxis_title='NSS (%)',
        template='plotly_white',
        height=450,
        font=dict(family='Inter, Arial', size=12),
        hovermode='x unified'
    )
    
    return fig

def plot_heatmap_categoria_tier(df_input, min_monthly=3):
    """Heatmap temporal: NSS por Categoria × Mês"""
    df_work = df_input[df_input['Classificação'] != 'PUBLICIDADE'].copy()
    
    # Top 10 categorias
    top_cats = df_work['Categoria'].value_counts().head(10).index.tolist()
    df_work = df_work[df_work['Categoria'].isin(top_cats)]
    
    # Calcular NSS por Categoria × Mês
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
                'Categoria': cat, 
                'Mês': mes, 
                'NSS': nss, 
                'N': n,
                'Positivos': pos if n >= min_monthly else 0,
                'Negativos': neg if n >= min_monthly else 0
            })
    
    heat_df = pd.DataFrame(results)
    heat_pivot = heat_df.pivot(index='Categoria', columns='Mês', values='NSS')
    n_pivot = heat_df.pivot(index='Categoria', columns='Mês', values='N')
    pos_pivot = heat_df.pivot(index='Categoria', columns='Mês', values='Positivos')
    neg_pivot = heat_df.pivot(index='Categoria', columns='Mês', values='Negativos')
    
    # Reordenar
    heat_pivot = heat_pivot.reindex(top_cats)
    n_pivot = n_pivot.reindex(top_cats)
    pos_pivot = pos_pivot.reindex(top_cats)
    neg_pivot = neg_pivot.reindex(top_cats)
    
    # Customdata
    customdata = np.dstack((
        n_pivot.values,
        pos_pivot.values,
        neg_pivot.values
    ))
    
    fig = go.Figure(go.Heatmap(
        z=heat_pivot.values,
        x=heat_pivot.columns.tolist(),
        y=heat_pivot.index.tolist(),
        customdata=customdata,
        colorscale=[
            [0.0, '#c0392b'], [0.3, '#e74c3c'], [0.5, '#fdfefe'],
            [0.7, '#82e0aa'], [1.0, '#1e8449'],
        ],
        zmid=0,
        colorbar=dict(title='NSS (%)'),
        hovertemplate=(
            '<b>%{y}</b><br>'
            'Mês: %{x}<br>'
            'NSS: %{z:+.1f}<br>'
            '<b>Positivos:</b> %{customdata[1]:.0f}<br>'
            '<b>Negativos:</b> %{customdata[2]:.0f}<br>'
            '<b>Total:</b> %{customdata[0]:.0f}<br>'
            '<i>NSS = (Pos - Neg) / Total × 100</i>'
            '<extra></extra>'
        ),
    ))
    
    fig.update_layout(
        title='<b>Evolução Temática: NSS por Categoria × Mês</b><br>'
              '<sup>Vermelho = crise | Verde = saudável | Branco = neutro</sup>',
        template='plotly_white',
        height=500,
        yaxis=dict(autorange='reversed'),
        margin=dict(l=180, r=30, t=80, b=50),
        font=dict(family='Inter, Arial', size=12),
    )
    
    return fig

def plot_treemap_midia(df_input, top_veiculos=10, min_mentions=3):
    """Treemap: Mídia → Veículo → Classificação → Categoria"""
    df_work = df_input[df_input['Classificação'] != 'PUBLICIDADE'].copy()
    
    # Top veículos
    top_veiculos_list = (
        df_work['Veículo_de_comunicacao']
        .value_counts()
        .head(top_veiculos)
        .index
        .tolist()
    )
    
    df_work = df_work[df_work['Veículo_de_comunicacao'].isin(top_veiculos_list)]
    
    # Agregar
    tree_data = df_work.groupby([
        'Mídia', 
        'Veículo_de_comunicacao', 
        'Classificação', 
        'Categoria'
    ]).size().reset_index(name='Total')
    
    tree_data = tree_data[tree_data['Total'] >= min_mentions]
    
    if tree_data.empty:
        return go.Figure().add_annotation(
            text="Sem dados suficientes para este filtro",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
    
    fig = px.treemap(
        tree_data,
        path=['Mídia', 'Veículo_de_comunicacao', 'Classificação', 'Categoria'],
        values='Total',
        color='Classificação',
        color_discrete_map=COLORS_SENTIMENT,
        title=f'<b>Treemap: Top {top_veiculos} Veículos — Hierarquia Completa</b><br>'
              '<sup>Mídia → Veículo → Sentimento → Tema | Tamanho = Volume</sup>',
    )
    
    fig.update_layout(
        height=700,
        margin=dict(l=10, r=10, t=80, b=10),
        font=dict(family='Inter, Arial', size=11),
    )
    
    fig.update_traces(
        textposition='middle center',
        hovertemplate=(
            '<b>%{label}</b><br>'
            'Menções: %{value:,}<br>'
            '% do nível acima: %{percentParent:.1%}<br>'
            '% do total: %{percentRoot:.1%}'
            '<extra></extra>'
        ),
        marker=dict(line=dict(width=2, color='white'))
    )
    
    return fig

# =============================================================================
# INTERFACE PRINCIPAL
# =============================================================================

def main():
    # Carregar dados
    with st.spinner('Carregando dados...'):
        df = carregar_dados()
    
    if df.empty:
        st.error("Não foi possível carregar os dados.")
        return
    
    # ==========================================================================
    # SIDEBAR - FILTROS GLOBAIS
    # ==========================================================================
    
    st.sidebar.title("🎛️ Filtros Globais")
    st.sidebar.markdown("Estes filtros se aplicam a **todas** as visualizações")
    
    # Filtro de Grupo
    grupos_disponiveis = ['Todos'] + sorted(df['Grupo'].dropna().unique().tolist())
    grupo_selecionado = st.sidebar.selectbox(
        "🏢 Grupo",
        grupos_disponiveis,
        index=0,
        help="Filtrar por grupo empresarial"
    )
    
    # Filtro de Empresa
    if grupo_selecionado != 'Todos':
        empresas_disponiveis = ['Todas'] + sorted(
            df[df['Grupo'] == grupo_selecionado]['Empresa'].dropna().unique().tolist()
        )
    else:
        empresas_disponiveis = ['Todas'] + sorted(df['Empresa'].dropna().unique().tolist())
    
    empresa_selecionada = st.sidebar.selectbox(
        "🏭 Empresa",
        empresas_disponiveis,
        index=0,
        help="Filtrar por empresa específica"
    )
    
    # Filtro de Data
    st.sidebar.markdown("---")
    st.sidebar.markdown("**📅 Período de Análise**")
    
    data_min = df['Data'].min().date()
    data_max = df['Data'].max().date()
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        data_inicio = st.date_input(
            "Início",
            value=data_min,
            min_value=data_min,
            max_value=data_max
        )
    with col2:
        data_fim = st.date_input(
            "Fim",
            value=data_max,
            min_value=data_min,
            max_value=data_max
        )
    
    # Aplicar filtros globais
    df_filtrado = aplicar_filtros_globais(
        df, 
        grupo_selecionado, 
        empresa_selecionada, 
        data_inicio, 
        data_fim
    )
    
    # Métricas resumo
    st.sidebar.markdown("---")
    st.sidebar.markdown("**📊 Dados Filtrados**")
    st.sidebar.metric("Total de Menções", f"{len(df_filtrado):,}")
    
    df_org = df_filtrado[df_filtrado['Classificação'] != 'PUBLICIDADE']
    st.sidebar.metric("Menções Orgânicas", f"{len(df_org):,}")
    
    if len(df_org) > 0:
        pos = (df_org['Classificação'] == 'POSITIVA').sum()
        neg = (df_org['Classificação'] == 'NEGATIVA').sum()
        nss_global = ((pos - neg) / len(df_org) * 100)
        st.sidebar.metric(
            "NSS Global", 
            f"{nss_global:+.1f}%",
            delta="Positivo" if nss_global > 0 else "Negativo"
        )
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Resetar Filtros"):
        st.rerun()
    
    # ==========================================================================
    # HERO SECTION
    # ==========================================================================
    
    st.markdown("""
    <div class="hero-section">
        <div class="hero-title">📊 Análise de Sentimento de Mídia</div>
        <div class="hero-subtitle">
            Como a mídia fala sobre saneamento? Esta análise revela padrões ocultos 
            na cobertura jornalística através de dados comportamentais.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ==========================================================================
    # SEÇÃO 1: CONCEITO E PANORAMA
    # ==========================================================================
    
    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="narrative-section">
        <div class="section-title">1. O que estamos medindo?</div>
        <div class="narrative-text">
            Empresas de saneamento são constantemente citadas na mídia — em notícias de TV, 
            rádio, jornais e sites. Mas <strong>será que toda cobertura importa igual?</strong> 
            Um comentário no Jornal Nacional tem o mesmo impacto que um post em um blog local?
            <br><br>
            Para responder isso, usamos o <strong>NSS (Net Sentiment Score)</strong> — 
            um indicador que funciona como o "saldo bancário" da reputação:
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="formula-box">
        NSS = (POSITIVAS − NEGATIVAS) / TOTAL × 100
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    df_org = df_filtrado[df_filtrado['Classificação'] != 'PUBLICIDADE']
    total = len(df_org)
    pos = (df_org['Classificação'] == 'POSITIVA').sum()
    neg = (df_org['Classificação'] == 'NEGATIVA').sum()
    neu = (df_org['Classificação'] == 'NEUTRA').sum()
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #2ecc71;">{pos:,}</div>
            <div class="metric-label">Menções Positivas</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #95a5a6;">{neu:,}</div>
            <div class="metric-label">Menções Neutras</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #e74c3c;">{neg:,}</div>
            <div class="metric-label">Menções Negativas</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    
    # Gráfico 1: Distribuição de Sentimentos
    st.plotly_chart(
        plot_classificacao_dinamica(df_filtrado),
        use_container_width=True,
        key="grafico_dist_sentimentos"
    )
    
    if total > 0:
        nss_calc = ((pos - neg) / total * 100)
        cor_nss = "#2ecc71" if nss_calc > 0 else "#e74c3c"
        
        st.markdown(f"""
        <div class="insight-box {'info' if nss_calc > 0 else 'warning'}">
            <strong>💡 Interpretação:</strong> O NSS atual é <strong style="color: {cor_nss};">{nss_calc:+.1f}%</strong>. 
            Isso significa que, em média, há <strong>{abs(nss_calc):.1f} menções {'a mais de positivas' if nss_calc > 0 else 'a mais de negativas'}</strong> 
            a cada 100 publicações. {'✅ Saldo favorável.' if nss_calc > 0 else '⚠️ Saldo desfavorável — requer atenção.'}
        </div>
        """, unsafe_allow_html=True)
    
    # ==========================================================================
    # SEÇÃO 2: AGENDA DA MÍDIA
    # ==========================================================================
    
    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="narrative-section">
        <div class="section-title">2. Sobre o que a mídia está falando?</div>
        <div class="narrative-text">
            Nem todo tema recebe a mesma atenção. Algumas categorias dominam a pauta, 
            enquanto outras passam despercebidas. Vamos identificar <strong>a agenda temática</strong> 
            e entender se temas negativos ou positivos lideram a cobertura.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown("**Filtros Específicos:**")
        classificacao_cat = st.selectbox(
            "Sentimento",
            ['Todas', 'POSITIVA', 'NEUTRA', 'NEGATIVA'],
            key="filtro_class_categorias"
        )
        top_n_cat = st.slider(
            "Top N",
            min_value=5,
            max_value=20,
            value=10,
            step=1,
            key="slider_top_n_cat"
        )
    
    with col2:
        st.plotly_chart(
            plot_top_categorias(df_filtrado, classificacao_cat, top_n_cat),
            use_container_width=True,
            key="grafico_top_categorias"
        )
    
    st.markdown("""
    <div class="insight-box">
        <strong>💡 Como ler:</strong> As categorias no topo são as mais citadas. 
        Se você filtrar apenas menções <strong>negativas</strong>, verá os temas que geram mais críticas. 
        Se filtrar <strong>positivas</strong>, encontra oportunidades de amplificação.
    </div>
    """, unsafe_allow_html=True)
    
    # ==========================================================================
    # SEÇÃO 3: EVOLUÇÃO TEMPORAL
    # ==========================================================================
    
    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="narrative-section">
        <div class="section-title">3. A cobertura mudou ao longo do tempo?</div>
        <div class="narrative-text">
            O volume de menções é constante ou há picos? 
            Existe sazonalidade (mais notícias em certos meses)? 
            Vamos visualizar a <strong>trajetória temporal</strong> da cobertura.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Controle de agregação
    agregacao_temporal = st.radio(
        "Nível de agregação temporal:",
        ['Dia', 'Semana', 'Mês'],
        index=2,
        horizontal=True,
        key="radio_agregacao_temporal"
    )
    
    st.plotly_chart(
        plot_volume_temporal(df_filtrado, agregacao_temporal),
        use_container_width=True,
        key="grafico_volume_temporal"
    )
    
    # Distribuição semanal
    st.markdown("### Quando a mídia publica?")
    
    st.plotly_chart(
        plot_distribuicao_semanal(df_filtrado),
        use_container_width=True,
        key="grafico_dist_semanal"
    )
    
    # ==========================================================================
    # SEÇÃO 4: TIER × SENTIMENTO (A ILUSÃO ESTATÍSTICA)
    # ==========================================================================
    
    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="narrative-section">
        <div class="section-title">4. Todo veículo importa igual?</div>
        <div class="section-subtitle">A Ilusão do NSS Não-Ponderado</div>
        <div class="narrative-text">
            Aqui está o <strong>ponto crítico</strong> da análise. Imagine que pequenos blogs 
            publicam 100 notícias positivas sobre obras locais, enquanto a TV Globo publica 
            10 reportagens negativas sobre falta de água. O NSS simples mostraria um saldo positivo 
            (110 - 10 = +90 de saldo). Mas <strong>qual tem mais impacto na reputação pública?</strong>
            <br><br>
            É aí que entra o <strong>Tier de Relevância</strong> — uma classificação que pondera 
            veículos pelo alcance de audiência:
            <ul>
                <li><strong>Muito Relevante</strong> (peso 8): TV Globo, Folha de S.Paulo, Valor Econômico</li>
                <li><strong>Relevante</strong> (peso 4): Jornais regionais, rádios médias</li>
                <li><strong>Menos Relevante</strong> (peso 1): Blogs, sites locais</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Filtro de categoria para drill-down
    categorias_disponiveis = ['Todas'] + sorted(
        df_filtrado[df_filtrado['Classificação'] != 'PUBLICIDADE']['Categoria'].unique().tolist()
    )
    
    categoria_tier = st.selectbox(
        "🔍 Filtrar por categoria (drill-down):",
        categorias_disponiveis,
        key="select_categoria_tier"
    )
    
    st.plotly_chart(
        plot_tier_classificacao(df_filtrado, categoria_tier),
        use_container_width=True,
        key="grafico_tier_class"
    )
    
    st.markdown("""
    <div class="insight-box warning">
        <strong>⚠️ Insight Crítico:</strong> Se veículos <strong>Muito Relevantes</strong> 
        têm proporção maior de menções <strong>negativas</strong> do que veículos menores, 
        isso indica que <strong>o NSS ponderado será pior que o simples</strong>. 
        A percepção pública é moldada pelos grandes veículos, não pela média aritmética.
    </div>
    """, unsafe_allow_html=True)
    
    # ==========================================================================
    # SEÇÃO 5: EVOLUÇÃO DO NSS
    # ==========================================================================
    
    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="narrative-section">
        <div class="section-title">5. O NSS melhorou ou piorou?</div>
        <div class="narrative-text">
            Agora que entendemos a diferença entre NSS simples e ponderado, 
            vamos observar como ambos evoluíram ao longo do tempo. 
            Se houver <strong>divergência</strong> entre as duas curvas, isso revela 
            uma mudança no perfil de veículos que estão cobrindo o tema.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown("**Configurações:**")
        categoria_nss = st.selectbox(
            "Categoria",
            categorias_disponiveis,
            key="select_categoria_nss"
        )
        modo_nss = st.radio(
            "Modo de cálculo",
            ['simples', 'ponderado'],
            key="radio_modo_nss"
        )
    
    with col2:
        st.plotly_chart(
            plot_nss_temporal(df_filtrado, categoria_nss, modo_nss),
            use_container_width=True,
            key="grafico_nss_temporal"
        )
    
    st.markdown("""
    <div class="insight-box">
        <strong>💡 Como comparar:</strong> Execute o gráfico duas vezes — 
        primeiro em modo <strong>simples</strong>, depois em <strong>ponderado</strong>. 
        Se o ponderado estiver sistematicamente abaixo, significa que grandes veículos 
        estão sendo mais críticos do que a média.
    </div>
    """, unsafe_allow_html=True)
    
    # ==========================================================================
    # SEÇÃO 6: HEATMAP TEMPORAL CATEGORIA × MÊS
    # ==========================================================================
    
    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="narrative-section">
        <div class="section-title">6. Quais temas pioraram ou melhoraram?</div>
        <div class="narrative-text">
            Nem todas as categorias seguem a mesma trajetória. Algumas podem melhorar 
            enquanto outras pioram. O <strong>heatmap temporal</strong> revela 
            esses padrões cruzados — categorias que precisam de atenção urgente 
            aparecem em <span style="color: #c0392b;"><strong>vermelho intenso</strong></span>.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.plotly_chart(
        plot_heatmap_categoria_tier(df_filtrado, min_monthly=3),
        use_container_width=True,
        key="grafico_heatmap_temporal"
    )
    
    st.markdown("""
    <div class="insight-box warning">
        <strong>⚠️ Priorização:</strong> Categorias com células vermelhas persistentes 
        (3+ meses consecutivos) indicam <strong>problemas estruturais</strong>, não eventos isolados. 
        Essas devem ser priorizadas em planos de ação.
    </div>
    """, unsafe_allow_html=True)
    
    # ==========================================================================
    # SEÇÃO 7: HIERARQUIA DE MÍDIA (TREEMAP)
    # ==========================================================================
    
    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="narrative-section">
        <div class="section-title">7. Explorando a hierarquia completa</div>
        <div class="narrative-text">
            A cobertura de mídia é hierárquica: <strong>Mídia → Veículo → Sentimento → Tema</strong>. 
            Um treemap interativo permite navegar por essa estrutura, 
            revelando qual <strong>tipo de mídia</strong> (TV, online, rádio) 
            publica <strong>quais veículos</strong>, com <strong>qual sentimento</strong>, 
            sobre <strong>quais temas</strong>.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown("**Configurações:**")
        top_veiculos_tree = st.slider(
            "Top N Veículos",
            min_value=5,
            max_value=20,
            value=10,
            step=1,
            key="slider_top_veiculos_tree"
        )
        min_mentions_tree = st.slider(
            "Mín. Menções",
            min_value=1,
            max_value=10,
            value=3,
            step=1,
            key="slider_min_mentions_tree"
        )
    
    with col2:
        st.plotly_chart(
            plot_treemap_midia(df_filtrado, top_veiculos_tree, min_mentions_tree),
            use_container_width=True,
            key="grafico_treemap"
        )
    
    st.markdown("""
    <div class="insight-box">
        <strong>💡 Como navegar:</strong> Clique em qualquer retângulo para dar zoom. 
        O <strong>tamanho</strong> representa volume de menções, 
        e a <strong>cor</strong> representa o sentimento (verde = positivo, vermelho = negativo).
    </div>
    """, unsafe_allow_html=True)
    
    # ==========================================================================
    # SEÇÃO 8: CONCLUSÕES E PRÓXIMOS PASSOS
    # ==========================================================================
    
    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="narrative-section">
        <div class="section-title">8. Conclusões e Recomendações</div>
        <div class="narrative-text">
            Esta análise revelou que <strong>nem toda voz tem o mesmo peso</strong>. 
            O NSS ponderado por Tier captura melhor a <strong>percepção pública real</strong> 
            do que a média aritmética de menções.
            <br><br>
            <strong>Principais achados:</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Calcular insights finais
    df_org = df_filtrado[df_filtrado['Classificação'] != 'PUBLICIDADE']
    
    # NSS por Tier
    tier_nss = {}
    for tier in ['Muito Relevante', 'Relevante', 'Menos Relevante']:
        subset = df_org[df_org['Tier'] == tier]
        if len(subset) > 0:
            pos = (subset['Classificação'] == 'POSITIVA').sum()
            neg = (subset['Classificação'] == 'NEGATIVA').sum()
            tier_nss[tier] = ((pos - neg) / len(subset) * 100)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'Muito Relevante' in tier_nss:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color: {'#2ecc71' if tier_nss['Muito Relevante'] > 0 else '#e74c3c'};">
                    {tier_nss['Muito Relevante']:+.1f}%
                </div>
                <div class="metric-label">NSS Muito Relevante</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        if 'Relevante' in tier_nss:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color: {'#2ecc71' if tier_nss['Relevante'] > 0 else '#e74c3c'};">
                    {tier_nss['Relevante']:+.1f}%
                </div>
                <div class="metric-label">NSS Relevante</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        if 'Menos Relevante' in tier_nss:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color: {'#2ecc71' if tier_nss['Menos Relevante'] > 0 else '#e74c3c'};">
                    {tier_nss['Menos Relevante']:+.1f}%
                </div>
                <div class="metric-label">NSS Menos Relevante</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="insight-box info">
        <strong>📋 Próximos Passos Recomendados:</strong>
        <ul>
            <li><strong>Análise por Empresa:</strong> Cruzar qual empresa sofre mais em cada categoria</li>
            <li><strong>Scatter NSS × Volume:</strong> Mapear veículos estratégicos (aliados vs detratores)</li>
            <li><strong>NLP nos Conteúdos:</strong> Validar classificação automática com modelo próprio</li>
            <li><strong>Análise Geoespacial:</strong> Se houver dados de localização, mapear padrões territoriais</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Footer
    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #718096; padding: 2rem 0;">
        <strong>Análise de Sentimento de Mídia</strong><br>
        Framework: Behavioral Data Science (Florent Buisson)<br>
        Desenvolvido com Streamlit + Plotly
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# EXECUTAR APLICAÇÃO
# =============================================================================

if __name__ == "__main__":
    main()
