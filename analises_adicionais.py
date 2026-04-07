# ============================================================================
# ANÁLISES ADICIONAIS: CLASSIFICAÇÃO TEMPORAL E TIER × CLASSIFICAÇÃO × TEMPO
# ============================================================================
# 
# Adicione este código ao seu notebook após a seção de Análise de Moderação
#
# OBJETIVO: Verificar se a mudança em setembro ocorreu igualmente em todos 
# os Tiers ou se foi concentrada em veículos menos relevantes
#
# ============================================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ============================================================================
# SEÇÃO 4.2: ANÁLISE TEMPORAL DETALHADA DE CADA CLASSIFICAÇÃO
# ============================================================================

print("="*80)
print("ANÁLISE TEMPORAL: EVOLUÇÃO DE CADA CLASSIFICAÇÃO")
print("="*80)

# Criar análise temporal por classificação
temporal_class = df_sentiment.groupby(['Ano_Mes', 'Classificação']).size().unstack(fill_value=0)
temporal_class = temporal_class.reset_index()
temporal_class['Data'] = temporal_class['Ano_Mes'].dt.to_timestamp()

# Calcular percentuais
temporal_class['Total'] = temporal_class[['POSITIVA', 'NEUTRA', 'NEGATIVA']].sum(axis=1)
temporal_class['Pct_POSITIVA'] = (temporal_class['POSITIVA'] / temporal_class['Total'] * 100)
temporal_class['Pct_NEUTRA'] = (temporal_class['NEUTRA'] / temporal_class['Total'] * 100)
temporal_class['Pct_NEGATIVA'] = (temporal_class['NEGATIVA'] / temporal_class['Total'] * 100)

print("\nÚltimos 12 meses:")
display(temporal_class.tail(12))

# ============================================================================
# VISUALIZAÇÃO 1: Evolução em Números Absolutos
# ============================================================================

fig, ax = plt.subplots(figsize=(16, 6))

ax.plot(temporal_class['Data'], temporal_class['POSITIVA'], 
        marker='o', linewidth=2, color='#2ecc71', label='POSITIVA')
ax.plot(temporal_class['Data'], temporal_class['NEUTRA'], 
        marker='s', linewidth=2, color='#95a5a6', label='NEUTRA')
ax.plot(temporal_class['Data'], temporal_class['NEGATIVA'], 
        marker='^', linewidth=2, color='#e74c3c', label='NEGATIVA')

# Destacar setembro
setembro_2025_ts = pd.Timestamp('2025-09-01')
if setembro_2025_ts in temporal_class['Data'].values:
    ax.axvline(setembro_2025_ts, color='gold', linestyle=':', 
               alpha=0.5, linewidth=3, label='Setembro/2025')

ax.set_title('Evolução Temporal: Classificações em Números Absolutos', 
             fontsize=14, fontweight='bold')
ax.set_xlabel('Mês', fontsize=12)
ax.set_ylabel('Número de Comentários', fontsize=12)
ax.legend(loc='best', fontsize=11)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

print("\n💡 INTERPRETAÇÃO:")
print("   Se POSITIVA cresceu MAIS que NEGATIVA → NSS subiu")
print("   Se NEGATIVA cresceu em termos absolutos → Comunicação está certa")

# ============================================================================
# VISUALIZAÇÃO 2: Evolução em Percentuais (Proporções)
# ============================================================================

fig, ax = plt.subplots(figsize=(16, 6))

ax.plot(temporal_class['Data'], temporal_class['Pct_POSITIVA'], 
        marker='o', linewidth=2, color='#2ecc71', label='% POSITIVA')
ax.plot(temporal_class['Data'], temporal_class['Pct_NEUTRA'], 
        marker='s', linewidth=2, color='#95a5a6', label='% NEUTRA')
ax.plot(temporal_class['Data'], temporal_class['Pct_NEGATIVA'], 
        marker='^', linewidth=2, color='#e74c3c', label='% NEGATIVA')

if setembro_2025_ts in temporal_class['Data'].values:
    ax.axvline(setembro_2025_ts, color='gold', linestyle=':', 
               alpha=0.5, linewidth=3, label='Setembro/2025')

ax.set_title('Evolução Temporal: Classificações em Percentuais', 
             fontsize=14, fontweight='bold')
ax.set_xlabel('Mês', fontsize=12)
ax.set_ylabel('Percentual (%)', fontsize=12)
ax.legend(loc='best', fontsize=11)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

print("\n💡 INTERPRETAÇÃO:")
print("   Percentuais mostram a PROPORÇÃO (como a pesquisa vê)")
print("   Se % NEGATIVA caiu → Satisfação relativa melhorou")

# ============================================================================
# VISUALIZAÇÃO 3: Gráfico de Área Empilhada (Composição)
# ============================================================================

fig, ax = plt.subplots(figsize=(16, 6))

ax.stackplot(temporal_class['Data'], 
             temporal_class['Pct_POSITIVA'],
             temporal_class['Pct_NEUTRA'],
             temporal_class['Pct_NEGATIVA'],
             labels=['POSITIVA', 'NEUTRA', 'NEGATIVA'],
             colors=['#2ecc71', '#95a5a6', '#e74c3c'],
             alpha=0.7)

if setembro_2025_ts in temporal_class['Data'].values:
    ax.axvline(setembro_2025_ts, color='gold', linestyle=':', 
               alpha=0.8, linewidth=3, label='Setembro/2025')

ax.set_title('Composição de Classificações ao Longo do Tempo (% Empilhadas)', 
             fontsize=14, fontweight='bold')
ax.set_xlabel('Mês', fontsize=12)
ax.set_ylabel('Percentual (%)', fontsize=12)
ax.legend(loc='upper right', fontsize=11)
ax.set_ylim(0, 100)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

print("\n💡 INTERPRETAÇÃO:")
print("   Se a área VERDE (POSITIVA) aumentou → Satisfação melhorou")
print("   Se a área VERMELHA (NEGATIVA) diminuiu → Menos reclamações proporcionalmente")

# ============================================================================
# SEÇÃO 4.3: ANÁLISE CRÍTICA - TIER × CLASSIFICAÇÃO × TEMPO
# ============================================================================

print("\n" + "="*80)
print("ANÁLISE CRÍTICA: A MUDANÇA FOI IGUAL EM TODOS OS TIERS?")
print("="*80)

print("\n🎯 QUESTÃO CHAVE:")
print("   Se NSS melhorou, foi porque:")
print("   A) Veículos GRANDES (Muito Relevante) melhoraram? → Impacto real")
print("   B) Veículos PEQUENOS (Menos Relevante) melhoraram? → Ilusão estatística")

# ============================================================================
# Criar análise Tier × Classificação × Tempo
# ============================================================================

tier_class_tempo = []

for mes in df_sentiment['Ano_Mes'].dropna().unique():
    for tier in df_sentiment['Tier'].dropna().unique():
        df_subset = df_sentiment[(df_sentiment['Ano_Mes'] == mes) & 
                                 (df_sentiment['Tier'] == tier)]
        
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
                'Pct_NEUTRA': (neu / total * 100) if total > 0 else 0,
                'Pct_NEGATIVA': (neg / total * 100) if total > 0 else 0,
                'NSS': ((pos - neg) / total * 100) if total > 0 else 0
            })

tier_class_tempo_df = pd.DataFrame(tier_class_tempo)
tier_class_tempo_df['Data'] = tier_class_tempo_df['Ano_Mes'].dt.to_timestamp()
tier_class_tempo_df = tier_class_tempo_df.sort_values('Data')

print("\n📊 Dados preparados: Tier × Classificação × Tempo")

# ============================================================================
# VISUALIZAÇÃO 4: POSITIVA por Tier ao longo do tempo
# ============================================================================

fig, axes = plt.subplots(3, 1, figsize=(16, 14), sharex=True)

# Gráfico 1: POSITIVA por Tier
for tier in tier_class_tempo_df['Tier'].unique():
    df_tier = tier_class_tempo_df[tier_class_tempo_df['Tier'] == tier]
    axes[0].plot(df_tier['Data'], df_tier['Pct_POSITIVA'], 
                 marker='o', linewidth=2, label=tier)

if setembro_2025_ts in tier_class_tempo_df['Data'].values:
    axes[0].axvline(setembro_2025_ts, color='gold', linestyle=':', 
                    alpha=0.5, linewidth=2)

axes[0].set_title('% POSITIVA por Tier ao Longo do Tempo', 
                  fontsize=13, fontweight='bold')
axes[0].set_ylabel('% POSITIVA', fontsize=11)
axes[0].legend(title='Tier', loc='best')
axes[0].grid(True, alpha=0.3)

# Gráfico 2: NEGATIVA por Tier
for tier in tier_class_tempo_df['Tier'].unique():
    df_tier = tier_class_tempo_df[tier_class_tempo_df['Tier'] == tier]
    axes[1].plot(df_tier['Data'], df_tier['Pct_NEGATIVA'], 
                 marker='s', linewidth=2, label=tier)

if setembro_2025_ts in tier_class_tempo_df['Data'].values:
    axes[1].axvline(setembro_2025_ts, color='gold', linestyle=':', 
                    alpha=0.5, linewidth=2)

axes[1].set_title('% NEGATIVA por Tier ao Longo do Tempo', 
                  fontsize=13, fontweight='bold')
axes[1].set_ylabel('% NEGATIVA', fontsize=11)
axes[1].legend(title='Tier', loc='best')
axes[1].grid(True, alpha=0.3)

# Gráfico 3: NSS por Tier
for tier in tier_class_tempo_df['Tier'].unique():
    df_tier = tier_class_tempo_df[tier_class_tempo_df['Tier'] == tier]
    axes[2].plot(df_tier['Data'], df_tier['NSS'], 
                 marker='^', linewidth=2, label=tier)

if setembro_2025_ts in tier_class_tempo_df['Data'].values:
    axes[2].axvline(setembro_2025_ts, color='gold', linestyle=':', 
                    alpha=0.5, linewidth=2, label='Setembro/2025')

axes[2].axhline(0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
axes[2].set_title('NSS por Tier ao Longo do Tempo', 
                  fontsize=13, fontweight='bold')
axes[2].set_xlabel('Mês', fontsize=11)
axes[2].set_ylabel('NSS', fontsize=11)
axes[2].legend(title='Tier', loc='best')
axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

print("\n💡 INTERPRETAÇÃO CRÍTICA:")
print("   Se todas as linhas subiram em setembro → Melhoria GENERALIZADA")
print("   Se apenas 'Menos Relevante' subiu → Melhoria em veículos PEQUENOS")
print("   Se 'Muito Relevante' caiu → Veículos GRANDES pioraram (PREOCUPANTE!)")

# ============================================================================
# ANÁLISE NUMÉRICA: Delta por Tier em Setembro
# ============================================================================

print("\n" + "="*80)
print("ANÁLISE NUMÉRICA: MUDANÇA EM SETEMBRO POR TIER")
print("="*80)

delta_tier = []

for tier in df_sentiment['Tier'].dropna().unique():
    # Antes de setembro
    df_antes = df_sentiment[(df_sentiment['Tier'] == tier) & 
                            (df_sentiment['Periodo'] == 'Antes')]
    
    # Setembro
    df_set = df_sentiment[(df_sentiment['Tier'] == tier) & 
                          (df_sentiment['Periodo'] == 'Setembro')]
    
    if len(df_antes) > 0 and len(df_set) > 0:
        # Calcular métricas
        total_antes = len(df_antes)
        pos_antes = len(df_antes[df_antes['Classificação'] == 'POSITIVA'])
        neg_antes = len(df_antes[df_antes['Classificação'] == 'NEGATIVA'])
        nss_antes = ((pos_antes - neg_antes) / total_antes * 100)
        pct_pos_antes = (pos_antes / total_antes * 100)
        pct_neg_antes = (neg_antes / total_antes * 100)
        
        total_set = len(df_set)
        pos_set = len(df_set[df_set['Classificação'] == 'POSITIVA'])
        neg_set = len(df_set[df_set['Classificação'] == 'NEGATIVA'])
        nss_set = ((pos_set - neg_set) / total_set * 100)
        pct_pos_set = (pos_set / total_set * 100)
        pct_neg_set = (neg_set / total_set * 100)
        
        delta_tier.append({
            'Tier': tier,
            'NSS_Antes': nss_antes,
            'NSS_Setembro': nss_set,
            'Delta_NSS': nss_set - nss_antes,
            'Pct_POS_Antes': pct_pos_antes,
            'Pct_POS_Setembro': pct_pos_set,
            'Delta_POS': pct_pos_set - pct_pos_antes,
            'Pct_NEG_Antes': pct_neg_antes,
            'Pct_NEG_Setembro': pct_neg_set,
            'Delta_NEG': pct_neg_set - pct_neg_antes
        })

delta_tier_df = pd.DataFrame(delta_tier)

print("\n📊 MUDANÇAS POR TIER (Setembro vs Antes):")
print("="*80)
display(delta_tier_df)
print("="*80)

# ============================================================================
# VISUALIZAÇÃO 5: Delta por Tier (Barras)
# ============================================================================

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Delta NSS
colors_nss = ['#2ecc71' if x > 0 else '#e74c3c' for x in delta_tier_df['Delta_NSS']]
delta_tier_df.plot(x='Tier', y='Delta_NSS', kind='bar', 
                   ax=axes[0], color=colors_nss, legend=False)
axes[0].set_title('Delta NSS (Setembro - Antes)', fontsize=13, fontweight='bold')
axes[0].set_ylabel('Pontos de NSS', fontsize=11)
axes[0].set_xlabel('Tier', fontsize=11)
axes[0].axhline(0, color='black', linewidth=1)
axes[0].grid(axis='y', alpha=0.3)
axes[0].tick_params(axis='x', rotation=45)

# Delta % POSITIVA
colors_pos = ['#2ecc71' if x > 0 else '#e74c3c' for x in delta_tier_df['Delta_POS']]
delta_tier_df.plot(x='Tier', y='Delta_POS', kind='bar', 
                   ax=axes[1], color=colors_pos, legend=False)
axes[1].set_title('Delta % POSITIVA (Setembro - Antes)', fontsize=13, fontweight='bold')
axes[1].set_ylabel('Pontos Percentuais', fontsize=11)
axes[1].set_xlabel('Tier', fontsize=11)
axes[1].axhline(0, color='black', linewidth=1)
axes[1].grid(axis='y', alpha=0.3)
axes[1].tick_params(axis='x', rotation=45)

# Delta % NEGATIVA
colors_neg = ['#e74c3c' if x > 0 else '#2ecc71' for x in delta_tier_df['Delta_NEG']]
delta_tier_df.plot(x='Tier', y='Delta_NEG', kind='bar', 
                   ax=axes[2], color=colors_neg, legend=False)
axes[2].set_title('Delta % NEGATIVA (Setembro - Antes)', fontsize=13, fontweight='bold')
axes[2].set_ylabel('Pontos Percentuais', fontsize=11)
axes[2].set_xlabel('Tier', fontsize=11)
axes[2].axhline(0, color='black', linewidth=1)
axes[2].grid(axis='y', alpha=0.3)
axes[2].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.show()

# ============================================================================
# CONCLUSÃO: Onde ocorreu a mudança?
# ============================================================================

print("\n" + "="*80)
print("🎯 CONCLUSÃO: ONDE OCORREU A MUDANÇA?")
print("="*80)

# Identificar qual Tier teve maior mudança
tier_maior_delta = delta_tier_df.loc[delta_tier_df['Delta_NSS'].idxmax(), 'Tier']
delta_max = delta_tier_df['Delta_NSS'].max()

print(f"\n📊 Tier com MAIOR aumento de NSS: {tier_maior_delta} (+{delta_max:.2f} pontos)")

# Verificar se a mudança foi concentrada ou generalizada
if delta_tier_df['Delta_NSS'].std() > 10:  # Alta variabilidade
    print("\n⚠️ ALERTA: Mudança CONCENTRADA em alguns Tiers")
    print("   → A melhoria não foi generalizada")
    print("   → Investigar por que alguns Tiers não melhoraram")
else:
    print("\n✅ Mudança GENERALIZADA em todos os Tiers")
    print("   → Melhoria consistente independente do Tier")

# Verificar se "Muito Relevante" melhorou
muito_rel = delta_tier_df[delta_tier_df['Tier'] == 'Muito Relevante']
if len(muito_rel) > 0:
    delta_muito_rel = muito_rel['Delta_NSS'].values[0]
    
    print(f"\n📢 Veículos 'Muito Relevante' (MAIOR IMPACTO):")
    if delta_muito_rel > 0:
        print(f"   ✅ NSS melhorou {delta_muito_rel:+.2f} pontos")
        print("   → Impacto REAL na percepção pública (veículos grandes alcançam mais pessoas)")
    else:
        print(f"   ❌ NSS piorou {delta_muito_rel:.2f} pontos")
        print("   → CUIDADO: Veículos grandes pioraram, mesmo que NSS geral tenha subido")
        print("   → Pesquisa pode estar certa em média, mas percepção pública pode ter piorado")

print("\n" + "="*80)

# ============================================================================
# EXPORTAR RESULTADOS
# ============================================================================

# Exportar análises
tier_class_tempo_df.to_csv('tier_classificacao_tempo.csv', index=False)
delta_tier_df.to_csv('delta_tier_setembro.csv', index=False)
temporal_class.to_csv('evolucao_classificacoes.csv', index=False)

print("\n✅ Arquivos adicionais exportados:")
print("   - tier_classificacao_tempo.csv")
print("   - delta_tier_setembro.csv")
print("   - evolucao_classificacoes.csv")
