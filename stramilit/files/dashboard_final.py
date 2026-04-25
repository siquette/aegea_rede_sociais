"""
=================================================================================
DASHBOARD FINAL - Funções EXATAS do Notebook
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

st.set_page_config(page_title="Análise de Sentimento", page_icon="📊", layout="wide")

# CSS
st.markdown("""
<style>
    * { font-family: 'Inter', sans-serif !important; }
    .section-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #2d3748;
        margin: 2rem 0 1rem 0;
        border-bottom: 3px solid #667eea;
        padding-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# CARREGAR DADOS
# =============================================================================

@st.cache_data(ttl=3600)
def carregar_dados():
    url = "https://docs.google.com/spreadsheets/d/1UVGM5g7A2pSmg4Nn5eTzjZhd25sAFFDbkBclRfyNgX8/export?format=csv"
    df = pd.read_csv(url)
    df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, format='mixed', errors='coerce')
    df = df.dropna(subset=['Data']).sort_values('Data')
    df['Ano_Mes'] = df['Data'].dt.to_period('M').astype(str)
    
    tier_weights = {'Muito Relevante': 8, 'Relevante': 4, 'Menos Relevante': 1}
    df['Peso'] = df['Tier'].map(tier_weights).fillna(1)
    
    df['Classificação'] = df['Classificação'].astype(str).str.strip()
    df['Tier'] = df['Tier'].fillna('Null')
    df['Categoria'] = df['Categoria'].fillna('Não Categorizado')
    df['Subcategoria'] = df['Subcategoria'].fillna('Não Especificado')
    df['Veículo_de_comunicacao'] = df['Veículo_de_comunicacao'].fillna('Não Informado')
    
    return df

# =============================================================================
# FUNÇÕES DO NOTEBOOK (EXATAS)
# =============================================================================

COLORS_SENTIMENT = {
    'POSITIVA': '#2ecc71',
    'NEUTRA': '#95a5a6',
    'NEGATIVA': '#e74c3c',
    'PUBLICIDADE': '#3498db'
}

def plot_classificacao_dinamica(class_counts: pd.Series):
    """Distribuição dual (barras + pizza)"""
    color_list = [COLORS_SENTIMENT.get(label, '#bdc3c7') for label in class_counts.index]
    
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "xy"}, {"type": "domain"}]],
        subplot_titles=("Frequência Absoluta", "Proporção Relativa")
    )
    
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
    
    fig.add_trace(
        go.Pie(
            labels=class_counts.index,
            values=class_counts.values,
            marker=dict(colors=color_list),
            hole=0.4,
            textinfo='label+percent',
            textfont_size=13
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        title="<b>Distribuição de Sentimentos</b>",
        template="plotly_white",
        height=450,
        showlegend=False
    )
    
    return fig

def plot_top_categorias(df_sentiment: pd.DataFrame, top_n: int = 10):
    """Top N categorias"""
    df_sem_publicidade = df_sentiment[df_sentiment['Classificação'] != 'PUBLICIDADE']
    
    top_categorias = df_sem_publicidade['Categoria'].value_counts().head(top_n).reset_index()
    top_categorias.columns = ['Categoria', 'Contagem']
    top_categorias = top_categorias.sort_values('Contagem', ascending=True)
    
    fig = px.bar(
        top_categorias,
        y='Categoria',
        x='Contagem',
        orientation='h',
        text='Contagem',
        color='Contagem',
        color_continuous_scale='Viridis',
        title=f'<b>Top {top_n} Categorias</b>'
    )
    
    fig.update_traces(texttemplate='%{text:,}', textposition='auto')
    fig.update_layout(template='plotly_white', height=max(400, top_n * 35), margin=dict(l=180))
    
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
    fig.add_trace(go.Scatter(x=agrupado['Ranking'], y=agrupado['Positiva'], fill='tozeroy', line=dict(color='#2ecc71'), name='Positivas', text=agrupado['Veículo_de_comunicacao'], hovertemplate='<b>%{text}</b><br>Positivas: %{y}<extra></extra>'))
    fig.add_trace(go.Scatter(x=agrupado['Ranking'], y=agrupado['Negativa'], fill='tozeroy', line=dict(color='#e74c3c'), name='Negativas', text=agrupado['Veículo_de_comunicacao'], hovertemplate='<b>%{text}</b><br>Negativas: %{y}<extra></extra>'))
    
    fig.add_vline(x=20, line_dash="dash", line_color="#2c3e50", annotation_text="← Top 20 | Cauda Longa →", annotation_position="top right")
    fig.update_layout(title='<b>Curva de Cauda Longa da Imprensa</b>', template='plotly_white', hovermode='x unified', height=500, xaxis_title='Ranking do Veículo')
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
        
        temporal.append({'Mes': mes, 'NSS_Simples': round(nss_simples, 1), 'NSS_Ponderado': round(nss_ponderado, 1)})
    
    df_temporal = pd.DataFrame(temporal)
    df_temporal['Data'] = pd.to_datetime(df_temporal['Mes'] + '-01')
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_temporal['Data'], y=df_temporal['NSS_Simples'], mode='lines+markers', name='NSS Simples', line=dict(color='#2ecc71', width=2)))
    fig.add_trace(go.Scatter(x=df_temporal['Data'], y=df_temporal['NSS_Ponderado'], mode='lines+markers', name='NSS Ponderado (Tier)', line=dict(color='#e74c3c', width=3, dash='dash')))
    fig.add_hline(y=0, line_dash="dot", line_color="gray")
    fig.update_layout(title='<b>Comparativo: NSS Simples vs NSS Ponderado</b>', xaxis_title='Período', yaxis_title='NSS (%)', template='plotly_white', height=500, hovermode='x unified')
    return fig

def plot_matriz_espacial(df_input, min_n=1):
    """Scatter NSS × Volume"""
    prof = df_input.groupby("Veículo_de_comunicacao").agg(
        Total=("Classificação", "count"),
        Positiva=("Classificação", lambda x: (x == "POSITIVA").sum()),
        Negativa=("Classificação", lambda x: (x == "NEGATIVA").sum())
    )
    prof = prof[prof["Total"] >= min_n].copy()
    prof["NSS"] = ((prof["Positiva"] - prof["Negativa"]) / prof["Total"] * 100).round(1)
    prof = prof.reset_index()
    
    if len(prof) == 0:
        return go.Figure().add_annotation(text=f"Sem dados (mín {min_n})", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=prof["Total"], y=prof["NSS"], mode="markers",
        marker=dict(size=prof["Total"], sizemode='area', sizeref=2.*max(prof["Total"])/(50.**2), sizemin=8, color=prof["NSS"], colorscale=[[0, "#e74c3c"], [0.5, "#bdc3c7"], [1, "#2ecc71"]], showscale=True),
        text=prof["Veículo_de_comunicacao"], hovertemplate="<b>%{text}</b><br>Volume: %{x}<br>NSS: %{y}%<extra></extra>"
    ))
    fig.add_hline(y=0, line_dash="dash", line_color="#34495e")
    fig.update_layout(title=f"<b>Matriz Espacial: Sentimento × Volume (Mínimo {min_n} menções)</b>", xaxis_title="Volume Absoluto (Barulho)", yaxis_title="NSS (Sentimento)", template="plotly_white", height=600)
    return fig

def plot_piramides_veiculo_absoluto(df_input: pd.DataFrame, top_n: int = 20):
    """Pirâmides"""
    df_work = df_input.copy()
    df_work = df_work[~df_work['Veículo_de_comunicacao'].isin(['Geral', 'N/A', 'Vários'])]
    
    neg = df_work[df_work['Classificação'] == 'NEGATIVA']
    top_neg = neg['Veículo_de_comunicacao'].value_counts().head(top_n).reset_index()
    top_neg.columns = ['Veículo', 'Total']
    top_neg = top_neg.sort_values('Total', ascending=True)
    
    pos = df_work[df_work['Classificação'] == 'POSITIVA']
    top_pos = pos['Veículo_de_comunicacao'].value_counts().head(top_n).reset_index()
    top_pos.columns = ['Veículo', 'Total']
    top_pos = top_pos.sort_values('Total', ascending=True)
    
    fig = make_subplots(rows=1, cols=2, subplot_titles=(f'Top {top_n} NEGATIVOS', f'Top {top_n} POSITIVOS'))
    fig.add_trace(go.Bar(y=top_neg['Veículo'], x=top_neg['Total'], orientation='h', marker_color='#e74c3c', showlegend=False), row=1, col=1)
    fig.add_trace(go.Bar(y=top_pos['Veículo'], x=top_pos['Total'], orientation='h', marker_color='#2ecc71', showlegend=False), row=1, col=2)
    fig.update_layout(title=f'<b>Pirâmides: Top {top_n} Veículos</b>', template='plotly_white', height=max(600, top_n*25))
    return fig

def plot_treemap_tier_categoria(df_input: pd.DataFrame, min_mentions: int = 10):
    """Treemap"""
    df_work = df_input.copy()
    df_work['Tier'] = df_work['Tier'].fillna('Null')
    df_work['Categoria'] = df_work['Categoria'].fillna('Sem Categoria')
    
    tree_data = df_work.groupby(['Tier', 'Categoria']).size().reset_index(name='Total')
    tree_data = tree_data[tree_data['Total'] >= min_mentions]
    
    if tree_data.empty:
        return go.Figure().add_annotation(text=f"Sem dados (mín {min_mentions})", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
    
    fig = px.treemap(tree_data, path=['Tier', 'Categoria'], values='Total', title='<b>Treemap: Tier × Categoria</b>')
    fig.update_layout(height=600, margin=dict(l=10, r=10, t=60, b=10))
    return fig

def plot_heatmap_temporal_categoria(df_input: pd.DataFrame, top_n: int = 10, min_monthly: int = 3):
    """Heatmap"""
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
            results.append({'Categoria': cat, 'Mês': mes, 'NSS': nss, 'N': n, 'Pos': pos if n >= min_monthly else 0, 'Neg': neg if n >= min_monthly else 0})
    
    heat_df = pd.DataFrame(results)
    heat_pivot = heat_df.pivot(index='Categoria', columns='Mês', values='NSS').reindex(top_cats)
    n_pivot = heat_df.pivot(index='Categoria', columns='Mês', values='N').reindex(top_cats)
    pos_pivot = heat_df.pivot(index='Categoria', columns='Mês', values='Pos').reindex(top_cats)
    neg_pivot = heat_df.pivot(index='Categoria', columns='Mês', values='Neg').reindex(top_cats)
    
    customdata = np.dstack((n_pivot.values, pos_pivot.values, neg_pivot.values))
    
    fig = go.Figure(go.Heatmap(
        z=heat_pivot.values, x=heat_pivot.columns.tolist(), y=heat_pivot.index.tolist(), customdata=customdata,
        colorscale=[[0.0, '#c0392b'], [0.3, '#e74c3c'], [0.5, '#fdfefe'], [0.7, '#82e0aa'], [1.0, '#1e8449']],
        zmid=0, colorbar=dict(title='NSS'),
        hovertemplate='<b>%{y}</b><br>Mês: %{x}<br>NSS: %{z:+.1f}<br>Pos: %{customdata[1]:.0f}<br>Neg: %{customdata[2]:.0f}<br>Total: %{customdata[0]:.0f}<extra></extra>'
    ))
    fig.update_layout(title='<b>Heatmap Temporal: NSS × Categoria × Mês</b>', template='plotly_white', height=500, yaxis=dict(autorange='reversed'))
    return fig

def plot_sunburst_composicao(df_input: pd.DataFrame, min_mentions: int = 5):
    """Sunburst 1"""
    df_work = df_input[df_input['Classificação'] != 'PUBLICIDADE'].copy()
    sun_data = df_work.groupby(['Classificação', 'Categoria', 'Subcategoria']).size().reset_index(name='Total')
    sun_data = sun_data[sun_data['Total'] >= min_mentions]
    
    if sun_data.empty:
        return go.Figure().add_annotation(text=f"Sem dados (mín {min_mentions})", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
    
    fig = px.sunburst(sun_data, path=['Classificação', 'Categoria', 'Subcategoria'], values='Total', color='Classificação', color_discrete_map=COLORS_SENTIMENT, title='<b>Sunburst: Classificação × Categoria × Subcategoria</b>')
    fig.update_layout(height=700, margin=dict(l=10, r=10, t=60, b=10))
    return fig

def plot_sunburst_tier(df_input: pd.DataFrame, min_mentions: int = 5):
    """Sunburst 2"""
    df_work = df_input[df_input['Classificação'] != 'PUBLICIDADE'].copy()
    df_work['Tier'] = df_work['Tier'].fillna('Null')
    sun_data = df_work.groupby(['Tier', 'Categoria', 'Classificação']).size().reset_index(name='Total')
    sun_data = sun_data[sun_data['Total'] >= min_mentions]
    
    if sun_data.empty:
        return go.Figure().add_annotation(text=f"Sem dados (mín {min_mentions})", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
    
    fig = px.sunburst(sun_data, path=['Tier', 'Categoria', 'Classificação'], values='Total', color='Classificação', color_discrete_map=COLORS_SENTIMENT, title='<b>Sunburst: Tier × Categoria × Classificação</b>')
    fig.update_layout(height=700, margin=dict(l=10, r=10, t=60, b=10))
    return fig

# =============================================================================
# INTERFACE
# =============================================================================

def main():
    with st.spinner('Carregando...'):
        df = carregar_dados()
    
    # SIDEBAR
    st.sidebar.title("🎛️ Filtros")
    grupos = ['Todos'] + sorted(df['Grupo'].dropna().unique().tolist())
    grupo_sel = st.sidebar.selectbox("Grupo", grupos)
    
    if grupo_sel != 'Todos':
        empresas = ['Todas'] + sorted(df[df['Grupo'] == grupo_sel]['Empresa'].dropna().unique().tolist())
    else:
        empresas = ['Todas'] + sorted(df['Empresa'].dropna().unique().tolist())
    empresa_sel = st.sidebar.selectbox("Empresa", empresas)
    
    data_min, data_max = df['Data'].min().date(), df['Data'].max().date()
    col1, col2 = st.sidebar.columns(2)
    with col1:
        data_inicio = st.date_input("Início", value=data_min, min_value=data_min, max_value=data_max)
    with col2:
        data_fim = st.date_input("Fim", value=data_max, min_value=data_min, max_value=data_max)
    
    # Filtrar
    df_filtrado = df.copy()
    if grupo_sel != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Grupo'] == grupo_sel]
    if empresa_sel != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['Empresa'] == empresa_sel]
    df_filtrado = df_filtrado[(df_filtrado['Data'] >= pd.to_datetime(data_inicio)) & (df_filtrado['Data'] <= pd.to_datetime(data_fim))]
    
    # Métricas
    st.sidebar.markdown("---")
    st.sidebar.metric("Total", f"{len(df_filtrado):,}")
    df_org = df_filtrado[df_filtrado['Classificação'] != 'PUBLICIDADE']
    st.sidebar.metric("Orgânicas", f"{len(df_org):,}")
    if len(df_org) > 0:
        pos = (df_org['Classificação'] == 'POSITIVA').sum()
        neg = (df_org['Classificação'] == 'NEGATIVA').sum()
        nss = ((pos - neg) / len(df_org) * 100)
        st.sidebar.metric("NSS", f"{nss:+.1f}%")
    
    # HERO
    st.markdown('<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 12px; color: white; text-align: center; margin-bottom: 2rem;"><h1 style="margin: 0;">📊 Análise de Sentimento</h1></div>', unsafe_allow_html=True)
    
    # GRÁFICOS
    st.markdown('<div class="section-title">1. Distribuição de Sentimentos</div>', unsafe_allow_html=True)
    df_sem_pub = df_filtrado[df_filtrado['Classificação'] != 'PUBLICIDADE']
    st.plotly_chart(plot_classificacao_dinamica(df_sem_pub['Classificação'].value_counts()), use_container_width=True)
    
    st.markdown('<div class="section-title">2. Top Categorias</div>', unsafe_allow_html=True)
    top_n_cat = st.slider("Top N", 5, 20, 10, key='top')
    st.plotly_chart(plot_top_categorias(df_filtrado, top_n_cat), use_container_width=True)
    
    st.markdown('<div class="section-title">3. Cauda Longa</div>', unsafe_allow_html=True)
    st.plotly_chart(plot_visualizacao_cauda_longa(df_filtrado), use_container_width=True)
    
    st.markdown('<div class="section-title">4. NSS Simples vs Ponderado</div>', unsafe_allow_html=True)
    st.plotly_chart(calcular_comparativo_nss(df_filtrado), use_container_width=True)
    
    st.markdown('<div class="section-title">5. Matriz Espacial</div>', unsafe_allow_html=True)
    min_n = st.slider("Mín. menções", 1, 20, 5, key='matriz')
    st.plotly_chart(plot_matriz_espacial(df_filtrado, min_n), use_container_width=True)
    
    st.markdown('<div class="section-title">6. Pirâmides</div>', unsafe_allow_html=True)
    top_pir = st.slider("Top N", 5, 30, 20, key='pir')
    st.plotly_chart(plot_piramides_veiculo_absoluto(df_filtrado, top_pir), use_container_width=True)
    
    st.markdown('<div class="section-title">7. Treemap</div>', unsafe_allow_html=True)
    min_tree = st.slider("Mín. menções", 5, 20, 10, key='tree')
    st.plotly_chart(plot_treemap_tier_categoria(df_filtrado, min_tree), use_container_width=True)
    
    st.markdown('<div class="section-title">8. Heatmap Temporal</div>', unsafe_allow_html=True)
    top_heat = st.slider("Top N", 5, 15, 10, key='heat')
    st.plotly_chart(plot_heatmap_temporal_categoria(df_filtrado, top_heat), use_container_width=True)
    
    st.markdown('<div class="section-title">9. Sunburst 1</div>', unsafe_allow_html=True)
    min_sun1 = st.slider("Mín. menções", 3, 10, 5, key='sun1')
    st.plotly_chart(plot_sunburst_composicao(df_filtrado, min_sun1), use_container_width=True)
    
    st.markdown('<div class="section-title">10. Sunburst 2</div>', unsafe_allow_html=True)
    min_sun2 = st.slider("Mín. menções", 3, 10, 5, key='sun2')
    st.plotly_chart(plot_sunburst_tier(df_filtrado, min_sun2), use_container_width=True)

if __name__ == "__main__":
    main()
