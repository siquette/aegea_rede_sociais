"""
VERSÃO DEBUG COM DIAGNÓSTICO - Identificar problema nos cálculos
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="DEBUG - Cálculos", layout="wide")

# Carregar dados
@st.cache_data
def carregar_dados():
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
    
    return df

df = carregar_dados()

st.title("🔬 DIAGNÓSTICO COMPLETO - Análise de Cálculos")

# =============================================================================
# DIAGNÓSTICO 1: DISTRIBUIÇÃO DE PESOS
# =============================================================================

st.header("1. Verificação dos Pesos Tier")

st.write("**Distribuição de Pesos:**")
peso_dist = df['Peso'].value_counts().sort_index()
st.dataframe(peso_dist)

st.write("**Distribuição de Tier:**")
tier_dist = df['Tier'].value_counts()
st.dataframe(tier_dist)

st.write("**Cruzamento Tier × Peso:**")
tier_peso = df.groupby(['Tier', 'Peso']).size().reset_index(name='Count')
st.dataframe(tier_peso)

# Verificar se os pesos estão corretos
st.write("**Verificação de mapeamento:**")
amostra = df[['Tier', 'Peso']].drop_duplicates().sort_values('Tier')
st.dataframe(amostra)

# =============================================================================
# DIAGNÓSTICO 2: CÁLCULO NSS DETALHADO
# =============================================================================

st.header("2. Análise Detalhada do NSS")

# Filtrar orgânicos
df_org = df[df['Classificação'] != 'PUBLICIDADE'].copy()

st.write(f"**Total orgânico:** {len(df_org):,} linhas")
st.write(f"**Classificações únicas:** {df_org['Classificação'].unique().tolist()}")

# Pegar um mês exemplo
mes_exemplo = sorted(df_org['Ano_Mes'].unique())[0]
st.write(f"**Analisando mês exemplo:** {mes_exemplo}")

subset = df_org[df_org['Ano_Mes'] == mes_exemplo].copy()

st.write(f"Total de registros neste mês: {len(subset):,}")

# Contagens simples
pos_count = (subset['Classificação'] == 'POSITIVA').sum()
neg_count = (subset['Classificação'] == 'NEGATIVA').sum()
neu_count = (subset['Classificação'] == 'NEUTRA').sum()

st.write("**Contagens simples:**")
st.write(f"- POSITIVA: {pos_count:,}")
st.write(f"- NEGATIVA: {neg_count:,}")
st.write(f"- NEUTRA: {neu_count:,}")
st.write(f"- **TOTAL: {len(subset):,}**")

# NSS Simples
nss_simples = ((pos_count - neg_count) / len(subset) * 100) if len(subset) > 0 else 0
st.write(f"**NSS Simples:** {nss_simples:.2f}%")
st.code(f"({pos_count} - {neg_count}) / {len(subset)} × 100 = {nss_simples:.2f}%")

# Contagens ponderadas
st.write("**Contagens PONDERADAS:**")

pos_subset = subset[subset['Classificação'] == 'POSITIVA']
neg_subset = subset[subset['Classificação'] == 'NEGATIVA']

pos_pond = pos_subset['Peso'].sum()
neg_pond = neg_subset['Peso'].sum()
total_pond = subset['Peso'].sum()

st.write(f"- Soma pesos POSITIVA: {pos_pond:,.0f}")
st.write(f"- Soma pesos NEGATIVA: {neg_pond:,.0f}")
st.write(f"- Soma pesos TOTAL: {total_pond:,.0f}")

# Mostrar distribuição de pesos por classificação
st.write("**Distribuição de pesos por Classificação neste mês:**")
peso_por_class = subset.groupby('Classificação')['Peso'].agg(['sum', 'count', 'mean'])
st.dataframe(peso_por_class)

# NSS Ponderado
nss_pond = ((pos_pond - neg_pond) / total_pond * 100) if total_pond > 0 else 0
st.write(f"**NSS Ponderado:** {nss_pond:.2f}%")
st.code(f"({pos_pond:.0f} - {neg_pond:.0f}) / {total_pond:.0f} × 100 = {nss_pond:.2f}%")

# Comparação
st.write("---")
st.write("**COMPARAÇÃO:**")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("NSS Simples", f"{nss_simples:.2f}%")
with col2:
    st.metric("NSS Ponderado", f"{nss_pond:.2f}%")
with col3:
    diferenca = nss_pond - nss_simples
    st.metric("Diferença", f"{diferenca:.2f}%", delta=f"{diferenca:.2f}%")

if abs(diferenca) < 0.1:
    st.warning("⚠️ **PROBLEMA DETECTADO:** Os valores são praticamente idênticos! Isso indica que os pesos não estão sendo aplicados corretamente.")

# =============================================================================
# DIAGNÓSTICO 3: ANÁLISE DE UM REGISTRO
# =============================================================================

st.header("3. Análise de Registros Individuais")

st.write("**Primeiros 10 registros POSITIVOS do mês exemplo:**")
pos_sample = subset[subset['Classificação'] == 'POSITIVA'][['Tier', 'Peso', 'Classificação', 'Veículo_de_comunicacao']].head(10)
st.dataframe(pos_sample)

st.write("**Primeiros 10 registros NEGATIVOS do mês exemplo:**")
neg_sample = subset[subset['Classificação'] == 'NEGATIVA'][['Tier', 'Peso', 'Classificação', 'Veículo_de_comunicacao']].head(10)
st.dataframe(neg_sample)

# =============================================================================
# DIAGNÓSTICO 4: TESTE DE CÁLCULO MANUAL
# =============================================================================

st.header("4. Teste de Cálculo Manual")

st.write("**Vou refazer o cálculo passo a passo:**")

# Criar DataFrame de teste
st.code("""
# Exemplo hipotético:
# 10 POSITIVAS com peso 1 = 10 pontos
# 5 POSITIVAS com peso 8 = 40 pontos
# Total POSITIVA = 50 pontos
# 
# 3 NEGATIVAS com peso 1 = 3 pontos
# 2 NEGATIVAS com peso 8 = 16 pontos
# Total NEGATIVA = 19 pontos
#
# NSS Ponderado = (50 - 19) / (50 + 19) × 100 = 44.9%
# NSS Simples = (15 - 5) / 20 × 100 = 50%
""")

# Verificar se há variação de pesos dentro de cada classificação
st.write("**Variação de pesos DENTRO de cada classificação (mês exemplo):**")

for classif in ['POSITIVA', 'NEGATIVA', 'NEUTRA']:
    sub = subset[subset['Classificação'] == classif]
    if len(sub) > 0:
        pesos_unicos = sub['Peso'].unique()
        st.write(f"- {classif}: {len(pesos_unicos)} pesos diferentes → {sorted(pesos_unicos)}")
        
        # Distribuição detalhada
        dist = sub['Peso'].value_counts().sort_index()
        st.write(f"  Distribuição: {dict(dist)}")

# =============================================================================
# DIAGNÓSTICO 5: GRÁFICO DE TESTE
# =============================================================================

st.header("5. Gráfico de Teste - NSS ao Longo do Tempo")

# Calcular para todos os meses
resultados = []

for mes in sorted(df_org['Ano_Mes'].unique()):
    sub = df_org[df_org['Ano_Mes'] == mes]
    
    # Simples
    total = len(sub)
    pos = (sub['Classificação'] == 'POSITIVA').sum()
    neg = (sub['Classificação'] == 'NEGATIVA').sum()
    nss_s = ((pos - neg) / total * 100) if total > 0 else 0
    
    # Ponderado
    total_p = sub['Peso'].sum()
    pos_p = sub[sub['Classificação'] == 'POSITIVA']['Peso'].sum()
    neg_p = sub[sub['Classificação'] == 'NEGATIVA']['Peso'].sum()
    nss_p = ((pos_p - neg_p) / total_p * 100) if total_p > 0 else 0
    
    resultados.append({
        'Mes': mes,
        'NSS_Simples': round(nss_s, 2),
        'NSS_Ponderado': round(nss_p, 2),
        'Diferenca': round(nss_p - nss_s, 2),
        'Total': total,
        'Pos': pos,
        'Neg': neg,
        'Total_Pond': total_p,
        'Pos_Pond': pos_p,
        'Neg_Pond': neg_p
    })

df_resultado = pd.DataFrame(resultados)

st.write("**Tabela completa de resultados:**")
st.dataframe(df_resultado)

# Plotar
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=pd.to_datetime(df_resultado['Mes'] + '-01'),
    y=df_resultado['NSS_Simples'],
    mode='lines+markers',
    name='NSS Simples',
    line=dict(color='#2ecc71', width=2)
))

fig.add_trace(go.Scatter(
    x=pd.to_datetime(df_resultado['Mes'] + '-01'),
    y=df_resultado['NSS_Ponderado'],
    mode='lines+markers',
    name='NSS Ponderado',
    line=dict(color='#e74c3c', width=3, dash='dash')
))

fig.update_layout(
    title="NSS Simples vs Ponderado - Diagnóstico",
    template='plotly_white',
    height=500
)

st.plotly_chart(fig, use_container_width=True)

# Análise da diferença
st.write("**Análise da diferença:**")
st.write(f"- Diferença mínima: {df_resultado['Diferenca'].min():.2f}%")
st.write(f"- Diferença máxima: {df_resultado['Diferenca'].max():.2f}%")
st.write(f"- Diferença média: {df_resultado['Diferenca'].mean():.2f}%")

if df_resultado['Diferenca'].abs().max() < 0.5:
    st.error("🚨 **CONFIRMADO:** As diferenças são mínimas! O problema está no cálculo ou na aplicação dos pesos.")
    
    st.write("**Hipóteses:**")
    st.write("1. Todos os registros têm o mesmo peso (improvável, mas possível)")
    st.write("2. A distribuição de pesos é uniforme entre POSITIVA e NEGATIVA")
    st.write("3. Há um bug no mapeamento Tier → Peso")
    st.write("4. A coluna Tier não tem valores 'Muito Relevante' ou 'Relevante' suficientes")
else:
    st.success("✅ Os cálculos parecem corretos! As diferenças são significativas.")
