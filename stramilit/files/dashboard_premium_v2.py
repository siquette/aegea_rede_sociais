"""
=================================================================================
DASHBOARD PREMIUM - Análise de Satisfação e Reputação na Mídia
=================================================================================
Versão corrigida com componentes nativos do Streamlit
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
# CSS PROFISSIONAL (APENAS PARA HERO E DIVIDERS)
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
    
    /* Section headers */
    .section-header {
        font-size: 2rem;
        font-weight: 700;
        color: #2d3748;
        margin: 3rem 0 1.5rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #667eea;
    }
    
    /* Métricas */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
    }
    
    /* Divider */
    .divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, #667eea, transparent);
        margin: 3rem 0;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #718096;
        padding: 2rem;
        margin-top: 3rem;
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
# FUNÇÕES DE VISUALIZAÇÃO
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
        title={'text': "<b>Distribuição de Sentimentos</b>", 'font': {'size': 20}},
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
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
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
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
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
    """Pirâmides de veículos - Versão do notebook"""
    df_work = df_input.copy()
    
    # Limpeza
    df_work['Tier'] = df_work['Tier'].fillna('Null')
    df_work['Veículo_de_comunicacao'] = df_work['Veículo_de_comunicacao'].fillna('Desconhecido')
    df_work = df_work[~df_work['Veículo_de_comunicacao'].isin(['Geral', 'N/A', 'Vários'])]
    
    # Agrupamento
    profile = df_work.groupby('Veículo_de_comunicacao').agg(
        Total=('Classificação', 'count'),
        Positiva=('Classificação', lambda x: (x == 'POSITIVA').sum()),
        Negativa=('Classificação', lambda x: (x == 'NEGATIVA').sum()),
        Tier_Dominante=('Tier', lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else 'Null')
    ).reset_index()
    
    # Ícones de Tier
    tier_markers = {
        'Muito Relevante': '🔴',
        'Relevante': '🟠',
        'Menos Relevante': '🔵',
        'Null': '⚪'
    }
    
    # Função auxiliar para criar cada pirâmide
    def criar_piramide(df_plot, title):
        # Labels com ícones
        labels = df_plot.apply(
            lambda r: f"{tier_markers.get(r['Tier_Dominante'], '⚪')} {r['Veículo_de_comunicacao']}", 
            axis=1
        ).tolist()
        
        fig = go.Figure()
        
        # Barras NEGATIVAS (esquerda)
        fig.add_trace(go.Bar(
            y=labels,
            x=-df_plot['Negativa'].values,
            orientation='h',
            name='Menções Negativas',
            marker_color='#e74c3c',
            text=df_plot['Negativa'].apply(lambda v: f'{v:.0f}' if v > 0 else ''),
            textposition='inside',
            textfont=dict(color='white', size=11, family='Arial Black'),
            hovertemplate='<b>%{y}</b><br>Negativas: %{customdata[0]:.0f}<extra></extra>',
            customdata=df_plot[['Negativa']].values,
        ))
        
        # Barras POSITIVAS (direita)
        fig.add_trace(go.Bar(
            y=labels,
            x=df_plot['Positiva'].values,
            orientation='h',
            name='Menções Positivas',
            marker_color='#2ecc71',
            text=df_plot['Positiva'].apply(lambda v: f'{v:.0f}' if v > 0 else ''),
            textposition='inside',
            textfont=dict(color='white', size=11, family='Arial Black'),
            hovertemplate='<b>%{y}</b><br>Positivas: %{customdata[0]:.0f}<extra></extra>',
            customdata=df_plot[['Positiva']].values,
        ))
        
        # Linha vertical central
        fig.add_vline(x=0, line_width=2, line_color='#2c3e50')
        
        # Eixo X sem sinais negativos
        max_val = max(df_plot['Positiva'].max(), df_plot['Negativa'].max())
        if pd.isna(max_val) or max_val <= 0:
            max_val = 10
        
        step = int(np.ceil(max_val / 4 / 10) * 10)
        step = max(step, 5)
        
        tickvals = list(range(-step * 4, step * 5, step))
        ticktext = [str(abs(v)) for v in tickvals]
        
        # Altura dinâmica
        altura = max(500, len(df_plot) * 35)
        
        fig.update_layout(
            title=title,
            template='plotly_white',
            height=altura,
            barmode='relative',
            xaxis=dict(
                title='Volume Absoluto de Menções',
                tickvals=tickvals,
                ticktext=ticktext,
                zeroline=False
            ),
            yaxis=dict(title='', tickfont=dict(size=11)),
            margin=dict(l=320, r=30, t=60, b=40),
            legend=dict(orientation='h', y=-0.08, x=0.3)
        )
        
        return fig
    
    # Criar as duas pirâmides
    figs = []
    
    # TOP Negativos
    df_neg = profile.nlargest(top_n, 'Negativa').sort_values('Negativa', ascending=True)
    if not df_neg.empty:
        fig_neg = criar_piramide(
            df_neg, 
            f'<b>Pirâmide de Crise: Top {top_n} Veículos (Maior Volume NEGATIVO)</b>'
        )
        figs.append(fig_neg)
    
    # TOP Positivos
    df_pos = profile.nlargest(top_n, 'Positiva').sort_values('Positiva', ascending=True)
    if not df_pos.empty:
        fig_pos = criar_piramide(
            df_pos, 
            f'<b>Pirâmide de Sucesso: Top {top_n} Veículos (Maior Volume POSITIVO)</b>'
        )
        figs.append(fig_pos)
    
    return figs

def plot_treemap_tier_categoria(df_input: pd.DataFrame, min_mentions: int = 10):
    """Treemap Tier × Categoria - Versão do notebook com NSS"""
    df_work = df_input.copy()
    
    # Limpeza
    df_work['Tier'] = df_work['Tier'].fillna('Null')
    df_work['Categoria'] = df_work['Categoria'].fillna('Sem Categoria classificada')
    
    # Agregação com cálculo de sentimento
    treemap_data = df_work.groupby(['Tier', 'Categoria']).agg(
        Total=('Classificação', 'count'),
        Positiva=('Classificação', lambda x: (x == 'POSITIVA').sum()),
        Negativa=('Classificação', lambda x: (x == 'NEGATIVA').sum()),
    ).reset_index()
    
    # Filtro de relevância
    treemap_data = treemap_data[treemap_data['Total'] >= min_mentions]
    
    if treemap_data.empty:
        return go.Figure().add_annotation(
            text=f"Sem dados com mínimo de {min_mentions} menções",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=16)
        )
    
    # Calcular NSS
    treemap_data['NSS'] = (
        (treemap_data['Positiva'] - treemap_data['Negativa']) / 
        treemap_data['Total'] * 100
    ).round(1)
    
    # Ordenação estrutural (não alfabética)
    tier_order = {
        'Muito Relevante': 1, 
        'Relevante': 2, 
        'Menos Relevante': 3, 
        'Null': 4
    }
    treemap_data['Tier_Order'] = treemap_data['Tier'].map(tier_order).fillna(5)
    treemap_data = treemap_data.sort_values(['Tier_Order', 'Total'], ascending=[True, False])
    
    # Renderização com escala de cor por NSS
    fig = px.treemap(
        treemap_data,
        path=['Tier', 'Categoria'],
        values='Total',
        color='NSS',  # ← CORES POR SENTIMENTO
        color_continuous_scale=[
            [0.0, '#c0392b'],   # Negativo forte
            [0.3, '#e74c3c'],   # Negativo moderado
            [0.5, '#fdfefe'],   # Neutro (zero)
            [0.7, '#82e0aa'],   # Positivo moderado
            [1.0, '#1e8449'],   # Positivo forte
        ],
        color_continuous_midpoint=0,  # ← Zero no centro da escala
        title=(
            '<b>Mapa Espacial de Sentimento: Escala do Veículo (Tier) × Categoria Temática</b><br>'
            '<sup>Tamanho = Volume | Cor = NSS | Compare a mesma Categoria entre Tiers</sup>'
        )
    )
    
    fig.update_layout(
        template='plotly_white',
        height=700,
        margin=dict(l=10, r=10, t=80, b=10),
        font=dict(family='Inter, Arial', size=12),
        coloraxis_colorbar=dict(title='NSS (%)', ticksuffix='')
    )
    
    fig.update_traces(
        hovertemplate=(
            '<b>%{label}</b><br>'
            'Total: %{value:,} menções<br>'
            'NSS: %{color:+.1f}%<br>'
            '<extra></extra>'
        ),
        textinfo='label+value'  # ← Mostra nome + quantidade
    )
    
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
    
    # ADICIONAR: Anotações com valores NSS dentro das células
    annotations = []
    for i, cat in enumerate(heat_pivot.index):
        for j, mes in enumerate(heat_pivot.columns):
            nss_val = heat_pivot.iloc[i, j]
            n_val = n_pivot.iloc[i, j]
            
            if pd.notna(nss_val):
                # Formatar NSS com sinal (ex: +50, -20)
                text = f"{nss_val:+.0f}"
                # Cor do texto: branco se valor absoluto > 50, cinza escuro caso contrário
                color = 'white' if abs(nss_val) > 50 else '#1a202c'
            else:
                # Célula sem dados suficientes
                text = "—"
                color = '#bdc3c7'
            
            annotations.append(dict(
                x=mes,
                y=cat,
                text=text,
                showarrow=False,
                font=dict(size=10, color=color, weight='bold')
            ))
    
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
            '<b>Positivos:</b> %{customdata[1]:.0f}<br>'
            '<b>Negativos:</b> %{customdata[2]:.0f}<br>'
            '<b>Total:</b> %{customdata[0]:.0f}<br>'
            '<i>NSS = (Pos - Neg) / Total × 100</i>'
            '<extra></extra>'
        )
    ))
    
    fig.update_layout(
        title=(
            '<b>Evolução Temática: NSS por Categoria × Mês</b><br>'
            '<sup>Vermelho = crise | Verde = saudável | — = amostra insuficiente</sup>'
        ),
        template='plotly_white',
        height=max(450, top_n * 40),
        yaxis=dict(autorange='reversed'),
        margin=dict(l=180, r=30, t=80, b=50),
        annotations=annotations,  # ← ADICIONA OS NÚMEROS NAS CÉLULAS
        font=dict(family='Inter, Arial', size=12)
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
        title=(
            '<b>Sunburst: Composição Temática por Sentimento</b><br>'
            '<sup>Clique nas fatias para expandir | Centro → Classificação → Categoria → Subcategoria</sup>'
        )
    )
    
    fig.update_layout(
        height=700,
        margin=dict(l=10, r=10, t=80, b=10),  # ← Margem top maior para título
        font=dict(family='Inter, Arial', size=12)
    )
    
    fig.update_traces(
        textinfo='label+percent parent',  # ← Mostra label + % do nível acima
        hovertemplate=(
            '<b>%{label}</b><br>'
            'Menções: %{value:,}<br>'
            '% do nível acima: %{percentParent:.1%}'
            '<extra></extra>'
        ),
        insidetextorientation='radial'  # ← Texto em orientação radial
    )
    
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
        title=(
            '<b>Sunburst: Tier × Categoria × Sentimento</b><br>'
            '<sup>Clique para expandir | Centro = Tier → Categoria → Classificação</sup>'
        )
    )
    
    fig.update_layout(
        height=700,
        margin=dict(l=10, r=10, t=80, b=10),  # ← Margem top maior
        font=dict(family='Inter, Arial', size=12)
    )
    
    fig.update_traces(
        textinfo='label+percent parent',  # ← Mostra label + % do nível acima
        hovertemplate=(
            '<b>%{label}</b><br>'
            'Menções: %{value:,}<br>'
            '% do nível acima: %{percentParent:.1%}'
            '<extra></extra>'
        ),
        insidetextorientation='radial'  # ← Texto em orientação radial
    )
    
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
    
    st.markdown("### 📐 Metodologia de Análise")
    
    st.markdown("""
Este dashboard não conta apenas quantas vezes a marca apareceu na mídia, mas **mede a qualidade e o impacto dessas aparições**.

**🎯 Princípios da Análise:**

- **O Filtro Orgânico:** Removemos toda a "Publicidade" paga. Só analisamos o que a mídia falou de forma espontânea.

- **O Peso da Voz (Tier):** Veículos classificados como **Muito Relevantes (peso 8)**, **Relevantes (peso 4)** e **Menos Relevantes (peso 1)**. Uma escala exponencial que amplifica propositalmente a diferença entre Tiers para capturar a realidade de audiência.

- **O Indicador NSS (Net Sentiment Score):** Funciona como um "saldo bancário" da imagem. Fórmula: `(Positivas − Negativas) / Total × 100`. Valores acima de zero são saudáveis; abaixo de zero exigem alerta.
""")
    
    st.markdown("---")
    
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
        
        # Insight automático
        pos_pct = (df_sem_pub['Classificação'] == 'POSITIVA').sum() / len(df_sem_pub) * 100
        neg_pct = (df_sem_pub['Classificação'] == 'NEGATIVA').sum() / len(df_sem_pub) * 100
        
        if pos_pct > neg_pct:
            st.success(f"""
**💚 Saldo Positivo**

O sentimento predominante é **positivo** ({pos_pct:.1f}% das menções), superando as menções negativas ({neg_pct:.1f}%). 

Isso indica uma reputação favorável no período analisado.
            """)
        else:
            st.warning(f"""
**⚠️ Saldo Negativo**

O sentimento predominante é **negativo** ({neg_pct:.1f}% das menções), superando as menções positivas ({pos_pct:.1f}%). 

Isso exige atenção na gestão de reputação.
            """)
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # ==========================================================================
    # SEÇÃO 2: TOP CATEGORIAS
    # ==========================================================================
    
    st.markdown('<div class="section-header">2️⃣ Agenda Temática: O Que Se Fala</div>', unsafe_allow_html=True)
    
    st.info("""
**📋 Interpretação**

Esta análise revela quais temas dominam a conversa na mídia. Categorias com alto volume indicam temas de interesse público ou pontos de atenção da empresa.
    """)
    
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
    
    st.info("""
**📊 Lei de Pareto na Mídia**

A **Lei de Pareto** (80/20) se manifesta: poucos veículos (Top 20) concentram a maioria das menções, enquanto a "cauda longa" representa centenas de veículos menores. 

Esta visualização separa o "barulho" (volume) da relevância (Tier).
    """)
    
    st.plotly_chart(
        plot_visualizacao_cauda_longa(df_filtrado),
        use_container_width=True
    )
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # ==========================================================================
    # SEÇÃO 4: NSS COMPARATIVO
    # ==========================================================================
    
    st.markdown('<div class="section-header">4️⃣ NSS Simples vs NSS Ponderado: A Ilusão do Volume</div>', unsafe_allow_html=True)
    
    st.warning("""
**⚠️ Por Que Dois Indicadores?**

**NSS Simples** trata todas as menções igualmente (1 blog = 1 Globo).  
**NSS Ponderado** aplica os pesos por Tier, revelando o impacto real.

Quando o NSS Ponderado é **menor** que o Simples, significa que veículos de alto impacto estão mais negativos — um sinal de alerta que o volume bruto mascara.
    """)
    
    st.plotly_chart(
        calcular_comparativo_nss(df_filtrado),
        use_container_width=True
    )
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # ==========================================================================
    # SEÇÃO 5: MATRIZ ESPACIAL
    # ==========================================================================
    
    st.markdown('<div class="section-header">5️⃣ Matriz Espacial: NSS × Volume</div>', unsafe_allow_html=True)
    
    st.info("""
**🎯 Quadrantes Estratégicos**

Esta matriz posiciona cada veículo em dois eixos:  
• **Eixo X (Volume):** Quantidade de menções  
• **Eixo Y (NSS):** Qualidade do sentimento

**Quadrante superior direito:** Alto volume + sentimento positivo (ideal)  
**Quadrante inferior direito:** Alto volume + sentimento negativo (atenção!)
    """)
    
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
    
    st.info("""
**📡 Mapeamento de Fontes**

Identifica quais veículos concentram as menções positivas e negativas. Útil para estratégias de relacionamento com a imprensa e gestão de crise.
    """)
    
    top_n_pir = st.slider("Top N veículos", 5, 30, 20, key='piramides')
    
    # A função agora retorna uma LISTA de figuras
    figs_piramides = plot_piramides_veiculo_absoluto(df_filtrado, top_n_pir)
    
    # Exibir cada figura separadamente
    for fig in figs_piramides:
        st.plotly_chart(fig, use_container_width=True)
    
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
    
    st.info("""
**🔥 Mapa de Calor**

Células vermelhas indicam NSS negativo; células verdes indicam NSS positivo. 

Permite identificar em qual período e categoria houve deterioração ou melhora de imagem.
    """)
    
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
    # FOOTER - OPÇÃO B (Divisores Sutis e Gradiente)
    # ==========================================================================
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    footer_b = f"""
<div class="footer">
<p><strong>Dashboard de Inteligência de Reputação</strong></p>
<p>Metodologia: NSS Ponderado por Tier | Dados atualizados automaticamente</p>

<div style="margin: 1.5rem 0; height: 1px; background: linear-gradient(90deg, transparent, #667eea, transparent);"></div>

<p style="font-size: 0.9rem; color: #718096;">
Desenvolvido com Streamlit + Plotly | Última atualização: {data_max.strftime("%d/%m/%Y")}
</p>

<div style="margin-top: 1.5rem; padding: 1rem 0; border-top: 1px solid #e2e8f0;">
<p style="margin: 0; font-size: 0.95rem; color: #2d3748;">
<strong>Analista Responsável:</strong> Rodrigo Aroni Siquette
</p>
<p style="margin: 0.3rem 0 0 0; font-size: 0.85rem; color: #718096;">
Geógrafo | MBA em Ciência de Dados | Especialização em IA
</p>
<p style="margin: 0.3rem 0 0 0; font-size: 0.8rem;">
<a href="https://linkedin.com/in/rodrigo-siquette" style="color: #667eea; text-decoration: none;" target="_blank">LinkedIn</a>
</p>
</div>
</div>
"""
    st.markdown(footer_b, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
