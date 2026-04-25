"""
VERSÃO DEBUG - Streamlit Análise de Sentimento
Identifica exatamente onde está o erro
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="DEBUG - Análise Sentimento", layout="wide")

st.title("🔍 MODO DEBUG - Identificando Problemas")

# =============================================================================
# TESTE 1: CARREGAMENTO DE DADOS
# =============================================================================

st.header("Teste 1: Carregamento de Dados")

try:
    url = "https://docs.google.com/spreadsheets/d/1UVGM5g7A2pSmg4Nn5eTzjZhd25sAFFDbkBclRfyNgX8/export?format=csv"
    
    with st.spinner("Carregando dados..."):
        df = pd.read_csv(url)
    
    st.success(f"✅ Dados carregados: {len(df):,} linhas × {df.shape[1]} colunas")
    
    # Mostrar primeiras linhas
    st.subheader("Primeiras 5 linhas:")
    st.dataframe(df.head())
    
    # Mostrar colunas
    st.subheader("Colunas disponíveis:")
    st.write(df.columns.tolist())
    
    # Verificar coluna Data
    st.subheader("Verificação da coluna 'Data':")
    st.write(f"Tipo atual: {df['Data'].dtype}")
    st.write("Amostra:")
    st.write(df['Data'].head(10))
    
except Exception as e:
    st.error(f"❌ ERRO ao carregar dados: {e}")
    st.stop()

st.markdown("---")

# =============================================================================
# TESTE 2: CONVERSÃO DE DATAS
# =============================================================================

st.header("Teste 2: Conversão de Datas")

try:
    df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, format='mixed', errors='coerce')
    
    # Remover NaT
    antes = len(df)
    df = df.dropna(subset=['Data'])
    depois = len(df)
    
    st.success(f"✅ Datas convertidas: {antes:,} → {depois:,} (perdidos: {antes-depois})")
    
    # Mostrar range
    st.write(f"**Período:** {df['Data'].min()} até {df['Data'].max()}")
    
    # Criar features temporais
    df['Ano_Mes'] = df['Data'].dt.to_period('M').astype(str)
    df['Ano'] = df['Data'].dt.year
    df['Mes'] = df['Data'].dt.month
    
    st.success("✅ Features temporais criadas (Ano_Mes, Ano, Mes)")
    
except Exception as e:
    st.error(f"❌ ERRO na conversão de datas: {e}")
    st.stop()

st.markdown("---")

# =============================================================================
# TESTE 3: PESOS E TRATAMENTO
# =============================================================================

st.header("Teste 3: Pesos Tier e Tratamento de Nulos")

try:
    # Pesos
    tier_weights = {'Muito Relevante': 8, 'Relevante': 4, 'Menos Relevante': 1}
    df['Peso'] = df['Tier'].map(tier_weights).fillna(1)
    
    st.success("✅ Pesos Tier criados")
    st.write("Distribuição de pesos:")
    st.write(df['Peso'].value_counts().sort_index())
    
    # Tratamento de nulos
    df['Tier'] = df['Tier'].fillna('Null')
    df['Categoria'] = df['Categoria'].fillna('Não Categorizado')
    df['Veículo_de_comunicacao'] = df['Veículo_de_comunicacao'].fillna('Não Informado')
    
    st.success("✅ Nulos tratados")
    
except Exception as e:
    st.error(f"❌ ERRO no tratamento: {e}")
    st.stop()

st.markdown("---")

# =============================================================================
# TESTE 4: FILTROS
# =============================================================================

st.header("Teste 4: Sistema de Filtros")

st.sidebar.title("🎛️ FILTROS DE TESTE")

# Filtro de Grupo
grupos_disponiveis = ['Todos'] + sorted(df['Grupo'].dropna().unique().tolist())
st.sidebar.write(f"Grupos disponíveis: {len(grupos_disponiveis)-1}")

grupo_selecionado = st.sidebar.selectbox("Grupo", grupos_disponiveis, index=0)

st.write(f"**Grupo selecionado:** {grupo_selecionado}")

# Aplicar filtro
df_filtrado = df.copy()

if grupo_selecionado != 'Todos':
    antes = len(df_filtrado)
    df_filtrado = df_filtrado[df_filtrado['Grupo'] == grupo_selecionado]
    depois = len(df_filtrado)
    st.info(f"Filtro aplicado: {antes:,} → {depois:,} linhas")
else:
    st.info(f"Sem filtro: {len(df_filtrado):,} linhas")

# Filtro de Data
st.sidebar.markdown("---")
data_min = df['Data'].min().date()
data_max = df['Data'].max().date()

col1, col2 = st.sidebar.columns(2)
with col1:
    data_inicio = st.date_input("Início", value=data_min, min_value=data_min, max_value=data_max)
with col2:
    data_fim = st.date_input("Fim", value=data_max, min_value=data_min, max_value=data_max)

st.write(f"**Período selecionado:** {data_inicio} até {data_fim}")

# Aplicar filtro de data
antes = len(df_filtrado)
df_filtrado = df_filtrado[
    (df_filtrado['Data'] >= pd.to_datetime(data_inicio)) &
    (df_filtrado['Data'] <= pd.to_datetime(data_fim))
]
depois = len(df_filtrado)

st.info(f"Após filtro de data: {antes:,} → {depois:,} linhas")

st.markdown("---")

# =============================================================================
# TESTE 5: GRÁFICO SIMPLES
# =============================================================================

st.header("Teste 5: Gráfico de Teste (Pizza)")

try:
    # Remover publicidade
    df_org = df_filtrado[df_filtrado['Classificação'] != 'PUBLICIDADE'].copy()
    
    st.write(f"Dados orgânicos: {len(df_org):,} linhas")
    
    # Contar classificações
    class_counts = df_org['Classificação'].value_counts()
    
    st.write("**Contagem por Classificação:**")
    st.write(class_counts)
    
    # Criar gráfico
    COLORS = {
        'POSITIVA': '#2ecc71',
        'NEUTRA': '#95a5a6',
        'NEGATIVA': '#e74c3c'
    }
    
    color_list = [COLORS.get(label, '#bdc3c7') for label in class_counts.index]
    
    fig = go.Figure(go.Pie(
        labels=class_counts.index,
        values=class_counts.values,
        marker=dict(colors=color_list),
        hole=0.4
    ))
    
    fig.update_layout(
        title="Distribuição de Sentimentos (TESTE)",
        template="plotly_white",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.success("✅ Gráfico renderizado com sucesso!")
    
except Exception as e:
    st.error(f"❌ ERRO ao criar gráfico: {e}")
    import traceback
    st.code(traceback.format_exc())

st.markdown("---")

# =============================================================================
# TESTE 6: GRÁFICO COM FILTRO ESPECÍFICO
# =============================================================================

st.header("Teste 6: Gráfico com Filtro Específico")

# Filtro local
classificacao_filtro = st.selectbox(
    "Filtrar por classificação:",
    ['Todas', 'POSITIVA', 'NEUTRA', 'NEGATIVA']
)

try:
    df_test = df_filtrado[df_filtrado['Classificação'] != 'PUBLICIDADE'].copy()
    
    if classificacao_filtro != 'Todas':
        df_test = df_test[df_test['Classificação'] == classificacao_filtro]
        st.write(f"Filtrado para {classificacao_filtro}: {len(df_test):,} linhas")
    else:
        st.write(f"Sem filtro específico: {len(df_test):,} linhas")
    
    # Top categorias
    top_cat = df_test['Categoria'].value_counts().head(10)
    
    st.write("**Top 10 Categorias:**")
    st.write(top_cat)
    
    # Gráfico
    fig = px.bar(
        x=top_cat.values,
        y=top_cat.index,
        orientation='h',
        title=f"Top 10 Categorias ({classificacao_filtro})"
    )
    
    fig.update_layout(template="plotly_white", height=400)
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.success("✅ Gráfico com filtro específico funcionou!")
    
except Exception as e:
    st.error(f"❌ ERRO: {e}")
    import traceback
    st.code(traceback.format_exc())

st.markdown("---")

# =============================================================================
# DIAGNÓSTICO FINAL
# =============================================================================

st.header("📋 DIAGNÓSTICO FINAL")

if len(df_filtrado) == 0:
    st.error("⚠️ PROBLEMA IDENTIFICADO: DataFrame filtrado está VAZIO!")
    st.write("Possíveis causas:")
    st.write("- Filtros muito restritivos")
    st.write("- Dados não existem para o período selecionado")
    st.write("- Problema na aplicação dos filtros")
else:
    st.success(f"✅ DataFrame filtrado OK: {len(df_filtrado):,} linhas")

st.write("**Informações do DataFrame Filtrado:**")
st.write(f"- Total de linhas: {len(df_filtrado):,}")
st.write(f"- Grupos únicos: {df_filtrado['Grupo'].nunique()}")
st.write(f"- Empresas únicas: {df_filtrado['Empresa'].nunique()}")
st.write(f"- Período: {df_filtrado['Data'].min()} até {df_filtrado['Data'].max()}")
st.write(f"- Classificações: {df_filtrado['Classificação'].unique().tolist()}")

st.markdown("---")
st.info("💡 **PRÓXIMO PASSO:** Envie um print/screenshot desta página mostrando onde o erro aparece!")
