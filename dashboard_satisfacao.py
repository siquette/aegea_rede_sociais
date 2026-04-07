"""
Dashboard de Análise de Satisfação - Empresas de Saneamento
============================================================

Métricas:
- NSS Simples: (POSITIVA - NEGATIVA) / TOTAL × 100
- NSS Ponderado: Mesmo cálculo, mas ponderado por relevância do veículo (Tier)
- Frequências absolutas e relativas de todas as classificações
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from scipy.stats import chi2_contingency

# ========================================
# CONFIGURAÇÃO DA PÁGINA
# ========================================

st.set_page_config(
    page_title="Dashboard de Satisfação",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 Dashboard de Análise de Satisfação")
st.markdown("""
Análise de sentimento em comentários sobre empresas de saneamento.  
**Foco**: Verificar evolução temporal e impacto da pesquisa de setembro/2025
""")

# ========================================
# FUNÇÕES AUXILIARES
# ========================================

@st.cache_data
def load_data(url):
    """
    Carrega dados do Google Sheets.
    
    Transformações:
    - Converte 'Data' para datetime
    - Cria coluna 'Ano_Mes' para agregação temporal
    - Cria coluna 'Peso' baseada em Tier
    - Mantém PUBLICIDADE para análise de frequência
    
    Returns:
        pd.DataFrame: Dados completos
    """
    df = pd.read_excel(url, engine='openpyxl')
    
    # Conversão de data
    df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
    
    # Criar coluna de ano-mês para agregação temporal
    df['Ano_Mes'] = df['Data'].dt.to_period('M')
    
    # Criar coluna de ano
    df['Ano'] = df['Data'].dt.year
    
    # CRIAR PESO BASEADO EM TIER
    # Muito Relevante = 3, Relevante = 2, Menos Relevante = 1, Null = 1
    tier_weights = {
        'Muito Relevante': 3,
        'Relevante': 2,
        'Menos Relevante': 1
    }
    
    df['Peso'] = df['Tier'].map(tier_weights).fillna(1)
    
    return df


def calculate_nss_simple(df):
    """
    NSS Simples (não ponderado).
    
    NSS = (POSITIVA - NEGATIVA) / TOTAL × 100
    
    Exclui PUBLICIDADE do cálculo (não é sentimento orgânico).
    
    Returns:
        float: NSS simples
    """
    # Filtrar apenas sentimento orgânico
    df_sentiment = df[df['Classificação'] != 'PUBLICIDADE']
    
    total = len(df_sentiment)
    if total == 0:
        return 0
    
    positivos = len(df_sentiment[df_sentiment['Classificação'] == 'POSITIVA'])
    negativos = len(df_sentiment[df_sentiment['Classificação'] == 'NEGATIVA'])
    
    nss = ((positivos - negativos) / total) * 100
    return nss


def calculate_nss_weighted(df):
    """
    NSS Ponderado por Tier.
    
    NSS_w = (Σ(POSITIVA × Peso) - Σ(NEGATIVA × Peso)) / Σ(TOTAL × Peso) × 100
    
    Comentários em veículos "Muito Relevante" têm peso 3.
    Comentários em veículos "Menos Relevante" têm peso 1.
    
    Returns:
        float: NSS ponderado
    """
    # Filtrar apenas sentimento orgânico
    df_sentiment = df[df['Classificação'] != 'PUBLICIDADE']
    
    total_weight = df_sentiment['Peso'].sum()
    if total_weight == 0:
        return 0
    
    peso_positivo = df_sentiment[df_sentiment['Classificação'] == 'POSITIVA']['Peso'].sum()
    peso_negativo = df_sentiment[df_sentiment['Classificação'] == 'NEGATIVA']['Peso'].sum()
    
    nss_weighted = ((peso_positivo - peso_negativo) / total_weight) * 100
    return nss_weighted


def calculate_frequencies(df):
    """
    Calcula frequências absolutas e relativas de todas as classificações.
    
    Inclui PUBLICIDADE.
    
    Returns:
        pd.DataFrame: Tabela com contagens e percentuais
    """
    total = len(df)
    
    freq_abs = df['Classificação'].value_counts()
    freq_rel = (freq_abs / total * 100).round(2)
    
    result = pd.DataFrame({
        'Frequência Absoluta': freq_abs,
        'Frequência Relativa (%)': freq_rel
    })
    
    # Garantir ordem lógica
    order = ['POSITIVA', 'NEUTRA', 'NEGATIVA', 'PUBLICIDADE']
    result = result.reindex([c for c in order if c in result.index])
    
    return result


def create_temporal_analysis(df):
    """
    Análise temporal com NSS simples e NSS ponderado.
    
    Returns:
        pd.DataFrame: Análise temporal mensal
    """
    # Filtrar apenas sentimento orgânico para NSS
    df_sentiment = df[df['Classificação'] != 'PUBLICIDADE']
    
    monthly = []
    
    for mes in df_sentiment['Ano_Mes'].dropna().unique():
        df_mes = df_sentiment[df_sentiment['Ano_Mes'] == mes]
        
        total = len(df_mes)
        positivos = len(df_mes[df_mes['Classificação'] == 'POSITIVA'])
        neutros = len(df_mes[df_mes['Classificação'] == 'NEUTRA'])
        negativos = len(df_mes[df_mes['Classificação'] == 'NEGATIVA'])
        
        # NSS simples
        nss_simple = ((positivos - negativos) / total * 100) if total > 0 else 0
        
        # NSS ponderado
        total_weight = df_mes['Peso'].sum()
        peso_pos = df_mes[df_mes['Classificação'] == 'POSITIVA']['Peso'].sum()
        peso_neg = df_mes[df_mes['Classificação'] == 'NEGATIVA']['Peso'].sum()
        nss_weighted = ((peso_pos - peso_neg) / total_weight * 100) if total_weight > 0 else 0
        
        monthly.append({
            'Ano_Mes': mes,
            'Total': total,
            'POSITIVA': positivos,
            'NEUTRA': neutros,
            'NEGATIVA': negativos,
            'NSS_Simples': nss_simple,
            'NSS_Ponderado': nss_weighted,
            'Perc_Positiva': (positivos / total * 100) if total > 0 else 0,
            'Perc_Neutra': (neutros / total * 100) if total > 0 else 0,
            'Perc_Negativa': (negativos / total * 100) if total > 0 else 0
        })
    
    monthly_df = pd.DataFrame(monthly)
    monthly_df['Data'] = monthly_df['Ano_Mes'].dt.to_timestamp()
    monthly_df = monthly_df.sort_values('Data')
    
    return monthly_df


def test_september_hypothesis(df):
    """
    Testa hipótese de mudança em setembro/2025.
    
    Returns:
        dict: Resultados do teste e NSS por período
    """
    # Filtrar apenas sentimento orgânico
    df_sentiment = df[df['Classificação'] != 'PUBLICIDADE'].copy()
    
    # Definir períodos
    setembro_2025 = pd.Period('2025-09', freq='M')
    
    df_sentiment['Periodo'] = df_sentiment['Ano_Mes'].apply(lambda x: 
        'Antes de Set/2025' if x < setembro_2025 else
        'Setembro/2025' if x == setembro_2025 else
        'Depois de Set/2025'
    )
    
    # Tabela de contingência
    contingency = pd.crosstab(df_sentiment['Periodo'], df_sentiment['Classificação'])
    
    # Teste qui-quadrado
    chi2, p_value, dof, expected = chi2_contingency(contingency)
    
    # Calcular NSS por período (simples e ponderado)
    nss_by_period = {}
    for periodo in ['Antes de Set/2025', 'Setembro/2025', 'Depois de Set/2025']:
        df_periodo = df_sentiment[df_sentiment['Periodo'] == periodo]
        nss_by_period[periodo] = {
            'simples': calculate_nss_simple(df_periodo),
            'ponderado': calculate_nss_weighted(df_periodo)
        }
    
    return {
        'contingency_table': contingency,
        'chi2': chi2,
        'p_value': p_value,
        'nss_by_period': nss_by_period,
        'significativo': p_value < 0.05
    }


# ========================================
# URL DOS DADOS
# ========================================

url = "https://docs.google.com/spreadsheets/d/1LmMi0mTTzRytJno0EHu8P873wcPpQavktO_D_FFXA1E/export?format=xlsx&gid=1312481019"

# ========================================
# CARREGAR DADOS
# ========================================

try:
    df = load_data(url)
    st.sidebar.success(f"✅ {len(df):,} registros carregados")
    
    # ========================================
    # FILTROS INTERATIVOS
    # ========================================
    
    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Filtros")
    
    # Filtro de período
    min_date = df['Data'].min()
    max_date = df['Data'].max()
    
    date_range = st.sidebar.date_input(
        "Período",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Filtro de Grupo
    grupos = ['Todos'] + sorted(df['Grupo'].dropna().unique().tolist())
    grupo_selecionado = st.sidebar.selectbox("Grupo", grupos)
    
    # Filtro de Empresa (dinâmico)
    if grupo_selecionado != 'Todos':
        empresas_filtradas = df[df['Grupo'] == grupo_selecionado]['Empresa'].dropna().unique()
    else:
        empresas_filtradas = df['Empresa'].dropna().unique()
    
    empresas = ['Todas'] + sorted(empresas_filtradas.tolist())
    empresa_selecionada = st.sidebar.selectbox("Empresa", empresas)
    
    # ========================================
    # APLICAR FILTROS
    # ========================================
    
    df_filtered = df.copy()
    
    # Filtro de data
    if len(date_range) == 2:
        df_filtered = df_filtered[
            (df_filtered['Data'] >= pd.to_datetime(date_range[0])) &
            (df_filtered['Data'] <= pd.to_datetime(date_range[1]))
        ]
    
    # Filtro de grupo
    if grupo_selecionado != 'Todos':
        df_filtered = df_filtered[df_filtered['Grupo'] == grupo_selecionado]
    
    # Filtro de empresa
    if empresa_selecionada != 'Todas':
        df_filtered = df_filtered[df_filtered['Empresa'] == empresa_selecionada]
    
    # ========================================
    # KPIS PRINCIPAIS
    # ========================================
    
    st.markdown("---")
    st.subheader("📈 Indicadores Principais")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    nss_simple = calculate_nss_simple(df_filtered)
    nss_weighted = calculate_nss_weighted(df_filtered)
    freq_table = calculate_frequencies(df_filtered)
    
    with col1:
        st.metric(
            label="NSS Simples",
            value=f"{nss_simple:.1f}",
            help="Net Sentiment Score não ponderado: (POSITIVA - NEGATIVA) / TOTAL × 100"
        )
    
    with col2:
        st.metric(
            label="NSS Ponderado",
            value=f"{nss_weighted:.1f}",
            help="NSS ponderado por relevância do veículo (Tier). Veículos 'Muito Relevante' têm peso 3x"
        )
    
    with col3:
        delta = nss_weighted - nss_simple
        st.metric(
            label="Diferença",
            value=f"{delta:+.1f}",
            help="Diferença entre NSS Ponderado e NSS Simples. Positivo = veículos relevantes são mais positivos"
        )
    
    with col4:
        perc_pos = freq_table.loc['POSITIVA', 'Frequência Relativa (%)']
        st.metric(
            label="% Positivos",
            value=f"{perc_pos:.1f}%"
        )
    
    with col5:
        perc_neg = freq_table.loc['NEGATIVA', 'Frequência Relativa (%)']
        st.metric(
            label="% Negativos",
            value=f"{perc_neg:.1f}%"
        )
    
    # ========================================
    # TABELA DE FREQUÊNCIAS
    # ========================================
    
    st.markdown("---")
    st.subheader("📊 Distribuição de Classificações")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("**Tabela de Frequências:**")
        st.dataframe(
            freq_table.style.format({
                'Frequência Absoluta': '{:,.0f}',
                'Frequência Relativa (%)': '{:.2f}%'
            }),
            use_container_width=True
        )
    
    with col2:
        # Gráfico de pizza
        fig_pie = go.Figure(data=[go.Pie(
            labels=freq_table.index,
            values=freq_table['Frequência Absoluta'],
            hole=0.3,
            marker=dict(colors=['#2ecc71', '#95a5a6', '#e74c3c', '#3498db'])
        )])
        
        fig_pie.update_layout(
            title="Proporção de Classificações",
            height=300
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # ========================================
    # ANÁLISE TEMPORAL: NSS SIMPLES VS PONDERADO
    # ========================================
    
    st.markdown("---")
    st.subheader("📅 Evolução Temporal: NSS Simples vs NSS Ponderado")
    
    monthly_data = create_temporal_analysis(df_filtered)
    
    # Gráfico comparativo
    fig_temporal = go.Figure()
    
    # NSS Simples
    fig_temporal.add_trace(go.Scatter(
        x=monthly_data['Data'],
        y=monthly_data['NSS_Simples'],
        mode='lines+markers',
        name='NSS Simples',
        line=dict(color='#3498db', width=2),
        marker=dict(size=6)
    ))
    
    # NSS Ponderado
    fig_temporal.add_trace(go.Scatter(
        x=monthly_data['Data'],
        y=monthly_data['NSS_Ponderado'],
        mode='lines+markers',
        name='NSS Ponderado (Tier)',
        line=dict(color='#e74c3c', width=2, dash='dash'),
        marker=dict(size=6)
    ))
    
    # Destacar setembro/2025
    setembro_2025 = pd.Timestamp('2025-09-01')
    if setembro_2025 in monthly_data['Data'].values:
        df_set = monthly_data[monthly_data['Data'] == setembro_2025]
        
        fig_temporal.add_trace(go.Scatter(
            x=[setembro_2025, setembro_2025],
            y=[df_set['NSS_Simples'].values[0], df_set['NSS_Ponderado'].values[0]],
            mode='markers',
            name='Setembro/2025',
            marker=dict(size=12, color='gold', symbol='star', line=dict(color='black', width=1))
        ))
    
    # Linha zero
    fig_temporal.add_hline(
        y=0, 
        line_dash="dot", 
        line_color="gray",
        annotation_text="NSS = 0",
        annotation_position="right"
    )
    
    fig_temporal.update_layout(
        title="Comparação: NSS Simples vs NSS Ponderado ao Longo do Tempo",
        xaxis_title="Mês",
        yaxis_title="NSS",
        hovermode='x unified',
        height=500,
        showlegend=True,
        legend=dict(x=0.01, y=0.99)
    )
    
    st.plotly_chart(fig_temporal, use_container_width=True)
    
    # Explicação da diferença
    st.info("""
    **Interpretação:**
    - **NSS Simples** (azul): Cada comentário vale 1, independente do veículo
    - **NSS Ponderado** (vermelho tracejado): Comentários em veículos "Muito Relevante" valem 3x mais
    - **Se NSS Ponderado > NSS Simples**: Veículos de maior alcance são mais positivos
    - **Se NSS Ponderado < NSS Simples**: Veículos menores são mais positivos (veículos grandes têm mais críticas)
    """)
    
    # ========================================
    # ANÁLISE DA HIPÓTESE SETEMBRO/2025
    # ========================================
    
    st.markdown("---")
    st.subheader("🔬 Análise da Hipótese: Setembro/2025")
    
    hypothesis_results = test_september_hypothesis(df_filtered)
    
    # KPIs por período
    col1, col2, col3 = st.columns(3)
    
    nss_antes = hypothesis_results['nss_by_period']['Antes de Set/2025']
    nss_set = hypothesis_results['nss_by_period']['Setembro/2025']
    nss_depois = hypothesis_results['nss_by_period']['Depois de Set/2025']
    
    with col1:
        st.markdown("**Antes de Setembro/2025**")
        st.metric("NSS Simples", f"{nss_antes['simples']:.1f}")
        st.metric("NSS Ponderado", f"{nss_antes['ponderado']:.1f}")
    
    with col2:
        delta_simples = nss_set['simples'] - nss_antes['simples']
        delta_pond = nss_set['ponderado'] - nss_antes['ponderado']
        
        st.markdown("**Setembro/2025**")
        st.metric("NSS Simples", f"{nss_set['simples']:.1f}", delta=f"{delta_simples:+.1f}")
        st.metric("NSS Ponderado", f"{nss_set['ponderado']:.1f}", delta=f"{delta_pond:+.1f}")
    
    with col3:
        delta_simples_dep = nss_depois['simples'] - nss_set['simples']
        delta_pond_dep = nss_depois['ponderado'] - nss_set['ponderado']
        
        st.markdown("**Depois de Setembro/2025**")
        st.metric("NSS Simples", f"{nss_depois['simples']:.1f}", delta=f"{delta_simples_dep:+.1f}")
        st.metric("NSS Ponderado", f"{nss_depois['ponderado']:.1f}", delta=f"{delta_pond_dep:+.1f}")
    
    # Teste estatístico
    st.markdown("### Teste Estatístico (Qui-Quadrado)")
    
    if hypothesis_results['significativo']:
        st.success(f"""
        ✅ **Diferença estatisticamente significativa** (p-value = {hypothesis_results['p_value']:.4f} < 0.05)
        
        Há evidência de que a distribuição de sentimentos mudou entre os períodos.
        """)
    else:
        st.warning(f"""
        ⚠️ **Diferença NÃO significativa** (p-value = {hypothesis_results['p_value']:.4f} ≥ 0.05)
        
        Mudanças podem ser devido ao acaso.
        """)
    
    with st.expander("📊 Ver Tabela de Contingência"):
        st.dataframe(hypothesis_results['contingency_table'])
    
    # ========================================
    # ANÁLISE POR CATEGORIA
    # ========================================
    
    st.markdown("---")
    st.subheader("🏷️ NSS por Categoria")
    
    # Filtrar sentimento orgânico
    df_sentiment = df_filtered[df_filtered['Classificação'] != 'PUBLICIDADE']
    
    category_analysis = []
    for cat in df_sentiment['Categoria'].dropna().unique():
        df_cat = df_sentiment[df_sentiment['Categoria'] == cat]
        
        category_analysis.append({
            'Categoria': cat,
            'Total': len(df_cat),
            'NSS_Simples': calculate_nss_simple(df_cat),
            'NSS_Ponderado': calculate_nss_weighted(df_cat)
        })
    
    cat_df = pd.DataFrame(category_analysis).sort_values('NSS_Simples', ascending=False)
    
    # Gráfico comparativo
    fig_cat = go.Figure()
    
    fig_cat.add_trace(go.Bar(
        y=cat_df['Categoria'],
        x=cat_df['NSS_Simples'],
        name='NSS Simples',
        orientation='h',
        marker=dict(color='#3498db')
    ))
    
    fig_cat.add_trace(go.Bar(
        y=cat_df['Categoria'],
        x=cat_df['NSS_Ponderado'],
        name='NSS Ponderado',
        orientation='h',
        marker=dict(color='#e74c3c')
    ))
    
    fig_cat.update_layout(
        title="NSS por Categoria: Simples vs Ponderado",
        xaxis_title="NSS",
        yaxis_title="Categoria",
        barmode='group',
        height=600
    )
    
    st.plotly_chart(fig_cat, use_container_width=True)
    
    # ========================================
    # DADOS DETALHADOS
    # ========================================
    
    st.markdown("---")
    st.subheader("📋 Dados Mensais Detalhados")
    
    display_df = monthly_data[[
        'Ano_Mes', 'Total', 'POSITIVA', 'NEUTRA', 'NEGATIVA', 
        'NSS_Simples', 'NSS_Ponderado'
    ]].copy()
    
    display_df.columns = [
        'Mês', 'Total', 'Positivos', 'Neutros', 'Negativos',
        'NSS Simples', 'NSS Ponderado'
    ]
    
    display_df['Mês'] = display_df['Mês'].astype(str)
    
    st.dataframe(
        display_df.sort_values('Mês', ascending=False).style.format({
            'Total': '{:,.0f}',
            'Positivos': '{:,.0f}',
            'Neutros': '{:,.0f}',
            'Negativos': '{:,.0f}',
            'NSS Simples': '{:.1f}',
            'NSS Ponderado': '{:.1f}'
        }),
        use_container_width=True,
        hide_index=True
    )
    
    # Download
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="⬇️ Baixar dados mensais (CSV)",
        data=csv,
        file_name="analise_mensal_satisfacao.csv",
        mime="text/csv"
    )

except Exception as e:
    st.error(f"❌ Erro ao carregar dados: {e}")
    st.info("Verifique se a URL do Google Sheets está correta e acessível.")
