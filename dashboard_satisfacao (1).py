"""
Dashboard de Análise de Satisfação - VERSÃO COMPLETA
=====================================================

Inclui análises críticas:
- Evolução temporal de cada classificação
- Tier × Classificação × Tempo (ANÁLISE CRÍTICA)
- Alertas automáticos se "Muito Relevante" piorou
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
    page_title="Dashboard de Satisfação - Análise Completa",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 Dashboard de Análise de Satisfação")
st.markdown("""
Análise completa de sentimento com **foco especial em Tier × Classificação × Tempo**.  
**Objetivo**: Verificar se mudanças ocorreram de forma generalizada ou concentrada em veículos menos relevantes.
""")

# ========================================
# FUNÇÕES AUXILIARES
# ========================================

@st.cache_data
def load_data(url):
    """Carrega dados do Google Sheets."""
    df = pd.read_excel(url, engine='openpyxl')
    
    # Conversão de data
    df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
    df['Ano_Mes'] = df['Data'].dt.to_period('M')
    df['Ano'] = df['Data'].dt.year
    
    # Criar pesos por Tier
    tier_weights = {
        'Muito Relevante': 3,
        'Relevante': 2,
        'Menos Relevante': 1
    }
    df['Peso'] = df['Tier'].map(tier_weights).fillna(1)
    
    return df


def calculate_nss_simple(df):
    """NSS Simples: (POSITIVA - NEGATIVA) / TOTAL × 100"""
    df_sent = df[df['Classificação'] != 'PUBLICIDADE']
    total = len(df_sent)
    if total == 0:
        return 0
    pos = len(df_sent[df_sent['Classificação'] == 'POSITIVA'])
    neg = len(df_sent[df_sent['Classificação'] == 'NEGATIVA'])
    return ((pos - neg) / total) * 100


def calculate_nss_weighted(df):
    """NSS Ponderado por Tier"""
    df_sent = df[df['Classificação'] != 'PUBLICIDADE']
    total_weight = df_sent['Peso'].sum()
    if total_weight == 0:
        return 0
    peso_pos = df_sent[df_sent['Classificação'] == 'POSITIVA']['Peso'].sum()
    peso_neg = df_sent[df_sent['Classificação'] == 'NEGATIVA']['Peso'].sum()
    return ((peso_pos - peso_neg) / total_weight) * 100


def calculate_frequencies(df):
    """Frequências absolutas e relativas"""
    total = len(df)
    freq_abs = df['Classificação'].value_counts()
    freq_rel = (freq_abs / total * 100).round(2)
    
    result = pd.DataFrame({
        'Frequência Absoluta': freq_abs,
        'Frequência Relativa (%)': freq_rel
    })
    
    order = ['POSITIVA', 'NEUTRA', 'NEGATIVA', 'PUBLICIDADE']
    result = result.reindex([c for c in order if c in result.index])
    return result


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
    
    # Dataset de sentimento
    df_sentiment = df[df['Classificação'] != 'PUBLICIDADE'].copy()
    
    # Definir períodos
    setembro_2025 = pd.Period('2025-09', freq='M')
    df_sentiment['Periodo'] = df_sentiment['Ano_Mes'].apply(lambda x:
        'Antes' if x < setembro_2025 else
        'Setembro' if x == setembro_2025 else
        'Depois'
    )
    
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
    
    # Filtro de Empresa
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
    df_sentiment_filtered = df_sentiment.copy()
    
    # Filtro de data
    if len(date_range) == 2:
        df_filtered = df_filtered[
            (df_filtered['Data'] >= pd.to_datetime(date_range[0])) &
            (df_filtered['Data'] <= pd.to_datetime(date_range[1]))
        ]
        df_sentiment_filtered = df_sentiment_filtered[
            (df_sentiment_filtered['Data'] >= pd.to_datetime(date_range[0])) &
            (df_sentiment_filtered['Data'] <= pd.to_datetime(date_range[1]))
        ]
    
    # Filtro de grupo
    if grupo_selecionado != 'Todos':
        df_filtered = df_filtered[df_filtered['Grupo'] == grupo_selecionado]
        df_sentiment_filtered = df_sentiment_filtered[df_sentiment_filtered['Grupo'] == grupo_selecionado]
    
    # Filtro de empresa
    if empresa_selecionada != 'Todas':
        df_filtered = df_filtered[df_filtered['Empresa'] == empresa_selecionada]
        df_sentiment_filtered = df_sentiment_filtered[df_sentiment_filtered['Empresa'] == empresa_selecionada]
    
    # ========================================
    # TABS DO DASHBOARD
    # ========================================
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Visão Geral",
        "📈 Análise Temporal Detalhada",
        "🎯 Análise por Tier (CRÍTICA)",
        "🏷️ Análise por Categoria",
        "🔬 Hipótese Setembro/2025",
        "📋 Dados Detalhados"
    ])
    
    # ========================================
    # TAB 1: VISÃO GERAL
    # ========================================
    
    with tab1:
        st.header("📊 Indicadores Principais")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        nss_simple = calculate_nss_simple(df_filtered)
        nss_weighted = calculate_nss_weighted(df_filtered)
        freq_table = calculate_frequencies(df_filtered)
        
        with col1:
            st.metric(
                label="NSS Simples",
                value=f"{nss_simple:.1f}",
                help="(POSITIVA - NEGATIVA) / TOTAL × 100"
            )
        
        with col2:
            st.metric(
                label="NSS Ponderado",
                value=f"{nss_weighted:.1f}",
                help="NSS ponderado por Tier (Muito Relevante = peso 3)"
            )
        
        with col3:
            delta = nss_weighted - nss_simple
            st.metric(
                label="Diferença",
                value=f"{delta:+.1f}",
                help="NSS Ponderado - NSS Simples"
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
        
        # Frequências
        st.markdown("---")
        st.subheader("Distribuição de Classificações")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.dataframe(
                freq_table.style.format({
                    'Frequência Absoluta': '{:,.0f}',
                    'Frequência Relativa (%)': '{:.2f}%'
                }),
                use_container_width=True
            )
        
        with col2:
            fig_pie = go.Figure(data=[go.Pie(
                labels=freq_table.index,
                values=freq_table['Frequência Absoluta'],
                hole=0.3,
                marker=dict(colors=['#2ecc71', '#95a5a6', '#e74c3c', '#3498db'])
            )])
            fig_pie.update_layout(title="Proporção de Classificações", height=300)
            st.plotly_chart(fig_pie, use_container_width=True)
    
    # ========================================
    # TAB 2: ANÁLISE TEMPORAL DETALHADA
    # ========================================
    
    with tab2:
        st.header("📈 Evolução Temporal de Cada Classificação")
        
        st.info("""
        **Objetivo**: Ver a evolução de POSITIVA, NEUTRA, NEGATIVA separadamente.  
        **Por quê?** NSS pode subir mas reclamações absolutas também podem aumentar.
        """)
        
        # Criar análise temporal por classificação
        temporal_class = df_sentiment_filtered.groupby(['Ano_Mes', 'Classificação']).size().unstack(fill_value=0)
        temporal_class = temporal_class.reset_index()
        temporal_class['Data'] = temporal_class['Ano_Mes'].dt.to_timestamp()
        
        # Calcular percentuais
        temporal_class['Total'] = temporal_class[['POSITIVA', 'NEUTRA', 'NEGATIVA']].sum(axis=1)
        temporal_class['Pct_POSITIVA'] = (temporal_class['POSITIVA'] / temporal_class['Total'] * 100)
        temporal_class['Pct_NEUTRA'] = (temporal_class['NEUTRA'] / temporal_class['Total'] * 100)
        temporal_class['Pct_NEGATIVA'] = (temporal_class['NEGATIVA'] / temporal_class['Total'] * 100)
        
        # Gráfico 1: Números Absolutos
        st.subheader("Números Absolutos")
        
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=temporal_class['Data'], y=temporal_class['POSITIVA'],
            mode='lines+markers', name='POSITIVA',
            line=dict(color='#2ecc71', width=2), marker=dict(size=6)
        ))
        fig1.add_trace(go.Scatter(
            x=temporal_class['Data'], y=temporal_class['NEUTRA'],
            mode='lines+markers', name='NEUTRA',
            line=dict(color='#95a5a6', width=2), marker=dict(size=6)
        ))
        fig1.add_trace(go.Scatter(
            x=temporal_class['Data'], y=temporal_class['NEGATIVA'],
            mode='lines+markers', name='NEGATIVA',
            line=dict(color='#e74c3c', width=2), marker=dict(size=6)
        ))
        
        setembro_2025_ts = pd.Timestamp('2025-09-01')
        if setembro_2025_ts in temporal_class['Data'].values:
            fig1.add_vline(x=setembro_2025_ts, line_dash="dot", line_color="gold", 
                          annotation_text="Setembro/2025")
        
        fig1.update_layout(
            title="Evolução em Números Absolutos",
            xaxis_title="Mês", yaxis_title="Contagem",
            hovermode='x unified', height=400
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        st.markdown("💡 **Interpretação**: Se POSITIVA cresceu MAIS que NEGATIVA → NSS subiu. Se NEGATIVA cresceu em termos absolutos → Mais reclamações.")
        
        # Gráfico 2: Percentuais
        st.subheader("Percentuais (Proporções)")
        
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=temporal_class['Data'], y=temporal_class['Pct_POSITIVA'],
            mode='lines+markers', name='% POSITIVA',
            line=dict(color='#2ecc71', width=2), marker=dict(size=6)
        ))
        fig2.add_trace(go.Scatter(
            x=temporal_class['Data'], y=temporal_class['Pct_NEUTRA'],
            mode='lines+markers', name='% NEUTRA',
            line=dict(color='#95a5a6', width=2), marker=dict(size=6)
        ))
        fig2.add_trace(go.Scatter(
            x=temporal_class['Data'], y=temporal_class['Pct_NEGATIVA'],
            mode='lines+markers', name='% NEGATIVA',
            line=dict(color='#e74c3c', width=2), marker=dict(size=6)
        ))
        
        if setembro_2025_ts in temporal_class['Data'].values:
            fig2.add_vline(x=setembro_2025_ts, line_dash="dot", line_color="gold",
                          annotation_text="Setembro/2025")
        
        fig2.update_layout(
            title="Evolução em Percentuais",
            xaxis_title="Mês", yaxis_title="Percentual (%)",
            hovermode='x unified', height=400
        )
        st.plotly_chart(fig2, use_container_width=True)
        
        st.markdown("💡 **Interpretação**: Percentuais mostram a PROPORÇÃO (como pesquisas medem). Se % NEGATIVA caiu → Satisfação relativa melhorou.")
        
        # Gráfico 3: Área Empilhada
        st.subheader("Composição ao Longo do Tempo")
        
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=temporal_class['Data'], y=temporal_class['Pct_POSITIVA'],
            mode='lines', name='POSITIVA', stackgroup='one',
            line=dict(width=0.5, color='#2ecc71'), fillcolor='rgba(46, 204, 113, 0.7)'
        ))
        fig3.add_trace(go.Scatter(
            x=temporal_class['Data'], y=temporal_class['Pct_NEUTRA'],
            mode='lines', name='NEUTRA', stackgroup='one',
            line=dict(width=0.5, color='#95a5a6'), fillcolor='rgba(149, 165, 166, 0.7)'
        ))
        fig3.add_trace(go.Scatter(
            x=temporal_class['Data'], y=temporal_class['Pct_NEGATIVA'],
            mode='lines', name='NEGATIVA', stackgroup='one',
            line=dict(width=0.5, color='#e74c3c'), fillcolor='rgba(231, 76, 60, 0.7)'
        ))
        
        if setembro_2025_ts in temporal_class['Data'].values:
            fig3.add_vline(x=setembro_2025_ts, line_dash="dot", line_color="gold",
                          annotation_text="Setembro/2025")
        
        fig3.update_layout(
            title="Composição (% Empilhadas)",
            xaxis_title="Mês", yaxis_title="Percentual (%)",
            hovermode='x unified', height=400
        )
        st.plotly_chart(fig3, use_container_width=True)
        
        st.markdown("💡 **Interpretação**: Se área verde (POSITIVA) aumentou → Mais positivos proporcionalmente. Se área vermelha (NEGATIVA) diminuiu → Menos reclamações.")
    
    # ========================================
    # TAB 3: ANÁLISE POR TIER (CRÍTICA)
    # ========================================
    
    with tab3:
        st.header("🎯 Análise por Tier: ONDE ocorreu a mudança?")
        
        st.warning("""
        **⚠️ ANÁLISE CRÍTICA**: NSS geral pode subir, mas a mudança pode estar concentrada em veículos MENOS relevantes.  
        **Por quê isso importa?** Veículos "Muito Relevante" têm MAIS ALCANCE. Se eles pioraram, a percepção pública pode ter piorado.
        """)
        
        # Criar análise Tier × Classificação × Tempo
        tier_class_tempo = []
        
        for mes in df_sentiment_filtered['Ano_Mes'].dropna().unique():
            for tier in df_sentiment_filtered['Tier'].dropna().unique():
                df_subset = df_sentiment_filtered[
                    (df_sentiment_filtered['Ano_Mes'] == mes) & 
                    (df_sentiment_filtered['Tier'] == tier)
                ]
                
                if len(df_subset) > 0:
                    total = len(df_subset)
                    pos = len(df_subset[df_subset['Classificação'] == 'POSITIVA'])
                    neu = len(df_subset[df_subset['Classificação'] == 'NEUTRA'])
                    neg = len(df_subset[df_subset['Classificação'] == 'NEGATIVA'])
                    
                    tier_class_tempo.append({
                        'Ano_Mes': mes,
                        'Tier': tier,
                        'Total': total,
                        'POSITIVA': pos,
                        'NEUTRA': neu,
                        'NEGATIVA': neg,
                        'Pct_POSITIVA': (pos / total * 100) if total > 0 else 0,
                        'Pct_NEGATIVA': (neg / total * 100) if total > 0 else 0,
                        'NSS': ((pos - neg) / total * 100) if total > 0 else 0
                    })
        
        tier_class_tempo_df = pd.DataFrame(tier_class_tempo)
        tier_class_tempo_df['Data'] = tier_class_tempo_df['Ano_Mes'].dt.to_timestamp()
        tier_class_tempo_df = tier_class_tempo_df.sort_values('Data')
        
        # Gráficos por Tier
        st.subheader("Evolução por Tier")
        
        fig_tier = make_subplots(
            rows=3, cols=1,
            subplot_titles=('% POSITIVA por Tier', '% NEGATIVA por Tier', 'NSS por Tier'),
            vertical_spacing=0.1
        )
        
        colors_tier = {'Muito Relevante': '#e74c3c', 'Relevante': '#f39c12', 'Menos Relevante': '#3498db'}
        
        for tier in tier_class_tempo_df['Tier'].unique():
            df_tier = tier_class_tempo_df[tier_class_tempo_df['Tier'] == tier]
            color = colors_tier.get(tier, '#95a5a6')
            
            fig_tier.add_trace(
                go.Scatter(x=df_tier['Data'], y=df_tier['Pct_POSITIVA'],
                          mode='lines+markers', name=tier, line=dict(color=color),
                          legendgroup=tier, showlegend=True),
                row=1, col=1
            )
            
            fig_tier.add_trace(
                go.Scatter(x=df_tier['Data'], y=df_tier['Pct_NEGATIVA'],
                          mode='lines+markers', name=tier, line=dict(color=color),
                          legendgroup=tier, showlegend=False),
                row=2, col=1
            )
            
            fig_tier.add_trace(
                go.Scatter(x=df_tier['Data'], y=df_tier['NSS'],
                          mode='lines+markers', name=tier, line=dict(color=color),
                          legendgroup=tier, showlegend=False),
                row=3, col=1
            )
        
        if setembro_2025_ts in tier_class_tempo_df['Data'].values:
            for row in [1, 2, 3]:
                fig_tier.add_vline(x=setembro_2025_ts, line_dash="dot", line_color="gold",
                                  row=row, col=1)
        
        fig_tier.update_xaxes(title_text="Mês", row=3, col=1)
        fig_tier.update_yaxes(title_text="% POSITIVA", row=1, col=1)
        fig_tier.update_yaxes(title_text="% NEGATIVA", row=2, col=1)
        fig_tier.update_yaxes(title_text="NSS", row=3, col=1)
        
        fig_tier.update_layout(height=900, hovermode='x unified')
        st.plotly_chart(fig_tier, use_container_width=True)
        
        st.markdown("""
        💡 **Interpretação**:
        - Se todas as linhas subiram → Melhoria GENERALIZADA ✅
        - Se apenas "Menos Relevante" subiu → Melhoria concentrada em veículos PEQUENOS ⚠️
        - Se "Muito Relevante" caiu → Veículos GRANDES pioraram 🚨 **ALERTA!**
        """)
        
        # Delta por Tier em Setembro
        st.subheader("Mudança em Setembro por Tier")
        
        delta_tier = []
        
        for tier in df_sentiment_filtered['Tier'].dropna().unique():
            df_antes = df_sentiment_filtered[
                (df_sentiment_filtered['Tier'] == tier) & 
                (df_sentiment_filtered['Periodo'] == 'Antes')
            ]
            df_set = df_sentiment_filtered[
                (df_sentiment_filtered['Tier'] == tier) & 
                (df_sentiment_filtered['Periodo'] == 'Setembro')
            ]
            
            if len(df_antes) > 0 and len(df_set) > 0:
                nss_antes = calculate_nss_simple(df_antes)
                nss_set = calculate_nss_simple(df_set)
                
                delta_tier.append({
                    'Tier': tier,
                    'NSS_Antes': nss_antes,
                    'NSS_Setembro': nss_set,
                    'Delta_NSS': nss_set - nss_antes
                })
        
        delta_tier_df = pd.DataFrame(delta_tier)
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.dataframe(
                delta_tier_df.style.format({
                    'NSS_Antes': '{:.2f}',
                    'NSS_Setembro': '{:.2f}',
                    'Delta_NSS': '{:+.2f}'
                }).background_gradient(subset=['Delta_NSS'], cmap='RdYlGn', vmin=-20, vmax=20),
                use_container_width=True,
                hide_index=True
            )
        
        with col2:
            fig_delta = go.Figure()
            colors = ['#2ecc71' if x > 0 else '#e74c3c' for x in delta_tier_df['Delta_NSS']]
            
            fig_delta.add_trace(go.Bar(
                x=delta_tier_df['Tier'],
                y=delta_tier_df['Delta_NSS'],
                marker_color=colors,
                text=delta_tier_df['Delta_NSS'].round(2),
                textposition='outside'
            ))
            
            fig_delta.update_layout(
                title="Delta NSS (Setembro - Antes)",
                xaxis_title="Tier",
                yaxis_title="Pontos de NSS",
                showlegend=False,
                height=350
            )
            fig_delta.add_hline(y=0, line_dash="dash", line_color="gray")
            
            st.plotly_chart(fig_delta, use_container_width=True)
        
        # ALERTA CRÍTICO
        muito_rel = delta_tier_df[delta_tier_df['Tier'] == 'Muito Relevante']
        if len(muito_rel) > 0:
            delta_muito_rel = muito_rel['Delta_NSS'].values[0]
            
            if delta_muito_rel < 0:
                st.error(f"""
                🚨 **ALERTA CRÍTICO**: Veículos "Muito Relevante" PIORARAM {abs(delta_muito_rel):.2f} pontos!
                
                **Implicações:**
                - Veículos de MAIOR ALCANCE estão mais negativos
                - Percepção pública pode ter PIORADO mesmo se NSS geral subiu
                - Pesquisa pode estar "certa" em média, mas ENGANOSA sobre percepção real
                
                **Recomendação:** Investigar por que grandes veículos pioraram.
                """)
            else:
                st.success(f"""
                ✅ Veículos "Muito Relevante" MELHORARAM {delta_muito_rel:+.2f} pontos.
                
                **Implicação:** Melhoria REAL na percepção pública (veículos grandes alcançam mais pessoas).
                """)
    
    # ========================================
    # TAB 4: ANÁLISE POR CATEGORIA
    # ========================================
    
    with tab4:
        st.header("🏷️ NSS por Categoria")
        
        category_analysis = []
        for cat in df_sentiment_filtered['Categoria'].dropna().unique():
            df_cat = df_sentiment_filtered[df_sentiment_filtered['Categoria'] == cat]
            
            category_analysis.append({
                'Categoria': cat,
                'Total': len(df_cat),
                'NSS_Simples': calculate_nss_simple(df_cat),
                'NSS_Ponderado': calculate_nss_weighted(df_cat)
            })
        
        cat_df = pd.DataFrame(category_analysis).sort_values('NSS_Simples', ascending=False)
        
        fig_cat = go.Figure()
        
        fig_cat.add_trace(go.Bar(
            y=cat_df['Categoria'], x=cat_df['NSS_Simples'],
            name='NSS Simples', orientation='h',
            marker=dict(color='#3498db')
        ))
        
        fig_cat.add_trace(go.Bar(
            y=cat_df['Categoria'], x=cat_df['NSS_Ponderado'],
            name='NSS Ponderado', orientation='h',
            marker=dict(color='#e74c3c')
        ))
        
        fig_cat.update_layout(
            title="NSS por Categoria",
            xaxis_title="NSS", yaxis_title="Categoria",
            barmode='group', height=600
        )
        
        st.plotly_chart(fig_cat, use_container_width=True)
    
    # ========================================
    # TAB 5: HIPÓTESE SETEMBRO/2025
    # ========================================
    
    with tab5:
        st.header("🔬 Análise da Hipótese: Setembro/2025")
        
        periodo_analysis = []
        
        for periodo in ['Antes', 'Setembro', 'Depois']:
            df_per = df_sentiment_filtered[df_sentiment_filtered['Periodo'] == periodo]
            
            periodo_analysis.append({
                'Periodo': periodo,
                'Total': len(df_per),
                'Positivos': len(df_per[df_per['Classificação'] == 'POSITIVA']),
                'Negativos': len(df_per[df_per['Classificação'] == 'NEGATIVA']),
                'NSS_Simples': calculate_nss_simple(df_per),
                'NSS_Ponderado': calculate_nss_weighted(df_per)
            })
        
        periodo_df = pd.DataFrame(periodo_analysis)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Antes de Setembro**")
            st.metric("NSS Simples", f"{periodo_df.iloc[0]['NSS_Simples']:.1f}")
            st.metric("NSS Ponderado", f"{periodo_df.iloc[0]['NSS_Ponderado']:.1f}")
        
        with col2:
            st.markdown("**Setembro/2025**")
            delta_s = periodo_df.iloc[1]['NSS_Simples'] - periodo_df.iloc[0]['NSS_Simples']
            delta_p = periodo_df.iloc[1]['NSS_Ponderado'] - periodo_df.iloc[0]['NSS_Ponderado']
            st.metric("NSS Simples", f"{periodo_df.iloc[1]['NSS_Simples']:.1f}", delta=f"{delta_s:+.1f}")
            st.metric("NSS Ponderado", f"{periodo_df.iloc[1]['NSS_Ponderado']:.1f}", delta=f"{delta_p:+.1f}")
        
        with col3:
            st.markdown("**Depois de Setembro**")
            delta_s2 = periodo_df.iloc[2]['NSS_Simples'] - periodo_df.iloc[1]['NSS_Simples']
            delta_p2 = periodo_df.iloc[2]['NSS_Ponderado'] - periodo_df.iloc[1]['NSS_Ponderado']
            st.metric("NSS Simples", f"{periodo_df.iloc[2]['NSS_Simples']:.1f}", delta=f"{delta_s2:+.1f}")
            st.metric("NSS Ponderado", f"{periodo_df.iloc[2]['NSS_Ponderado']:.1f}", delta=f"{delta_p2:+.1f}")
        
        # Teste qui-quadrado
        st.subheader("Teste Estatístico")
        
        contingency = pd.crosstab(df_sentiment_filtered['Periodo'], df_sentiment_filtered['Classificação'])
        chi2, p_value, dof, expected = chi2_contingency(contingency)
        
        if p_value < 0.05:
            st.success(f"""
            ✅ Diferença ESTATISTICAMENTE SIGNIFICATIVA (p = {p_value:.4f} < 0.05)
            
            Há evidência de mudança real entre os períodos.
            """)
        else:
            st.warning(f"""
            ⚠️ Diferença NÃO significativa (p = {p_value:.4f} ≥ 0.05)
            
            Mudanças podem ser devido ao acaso.
            """)
    
    # ========================================
    # TAB 6: DADOS DETALHADOS
    # ========================================
    
    with tab6:
        st.header("📋 Dados Mensais Detalhados")
        
        # Criar análise mensal
        monthly_list = []
        
        for mes in df_sentiment_filtered['Ano_Mes'].dropna().unique():
            df_mes = df_sentiment_filtered[df_sentiment_filtered['Ano_Mes'] == mes]
            
            total = len(df_mes)
            pos = len(df_mes[df_mes['Classificação'] == 'POSITIVA'])
            neu = len(df_mes[df_mes['Classificação'] == 'NEUTRA'])
            neg = len(df_mes[df_mes['Classificação'] == 'NEGATIVA'])
            
            monthly_list.append({
                'Ano_Mes': mes,
                'Total': total,
                'Positivos': pos,
                'Neutros': neu,
                'Negativos': neg,
                'NSS_Simples': calculate_nss_simple(df_mes),
                'NSS_Ponderado': calculate_nss_weighted(df_mes)
            })
        
        monthly_df = pd.DataFrame(monthly_list)
        monthly_df = monthly_df.sort_values('Ano_Mes', ascending=False)
        monthly_df['Ano_Mes'] = monthly_df['Ano_Mes'].astype(str)
        
        st.dataframe(
            monthly_df.style.format({
                'Total': '{:,.0f}',
                'Positivos': '{:,.0f}',
                'Neutros': '{:,.0f}',
                'Negativos': '{:,.0f}',
                'NSS_Simples': '{:.1f}',
                'NSS_Ponderado': '{:.1f}'
            }),
            use_container_width=True,
            hide_index=True
        )
        
        csv = monthly_df.to_csv(index=False)
        st.download_button(
            label="⬇️ Baixar dados mensais (CSV)",
            data=csv,
            file_name="analise_mensal_satisfacao.csv",
            mime="text/csv"
        )

except Exception as e:
    st.error(f"❌ Erro ao carregar dados: {e}")
    st.info("Verifique se a URL do Google Sheets está correta e acessível.")
