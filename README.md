# 📊 Análise de Opinião Pública - Aegea

Análise de sentimento de mídia para empresas do grupo Aegea.

## 🗂️ Estrutura do Projeto

```
opniao_aegea/
├── 📊 dados/              # Arquivos Excel com clipping mensal
├── 📓 notebooks/          # Análises Jupyter
│   ├── producao/          # Notebook principal (v3_improved)
│   ├── exploratorias/     # Análises ad-hoc
│   └── archive/           # Versões antigas
├── 📱 dashboards/         # Dashboards interativos
│   ├── streamlit/         # Dashboard Streamlit (principal)
│   └── quarto/            # Dashboard Quarto (alternativo)
├── 🐍 scripts/            # Scripts Python auxiliares
└── 📄 docs/               # Documentação e relatórios
```

## 🚀 Quick Start

### Instalar ambiente

```bash
pixi install
```

### Rodar Dashboard

```bash
pixi run dashboard
# Abre em http://localhost:8501
```

### Rodar Notebooks

```bash
pixi run notebook
```

## 📊 Dashboards Disponíveis

### Streamlit (Recomendado)
- **Localização:** `dashboards/streamlit/app.py`
- **Rodar:** `pixi run dashboard`
- **Features:** 10 visualizações interativas, filtros globais

### Quarto
- **Localização:** `dashboards/quarto/files/`
- **Rodar:** `pixi run serve-quarto`

## 📓 Notebook Principal

**Arquivo:** `notebooks/producao/analise_satisfacao_comentada_v3_improved.ipynb`

**Contém:**
- Cálculo NSS (Simples e Ponderado por Tier)
- Análise temporal
- Visualizações completas
- Interpretações e insights

## 📦 Dependências

- Python 3.11
- Streamlit 1.39+
- Plotly 6.6+
- Pandas 2.3+

Ver `pixi.toml` para lista completa.

## 🔄 Fluxo de Trabalho

1. **Dados novos** → Adicionar em `dados/`
2. **Análise** → Usar notebook em `notebooks/producao/`
3. **Dashboard** → Atualiza automaticamente (Google Sheets)
4. **Relatórios** → Exportar de `docs/relatorios/`

## 📈 Metodologia

### NSS (Net Sentiment Score)

```
NSS = (Positivas - Negativas) / Total × 100
```

### Ponderação por Tier

```
Muito Relevante: peso 8
Relevante:       peso 4
Menos Relevante: peso 1
```

### Fonte de Dados

Google Sheets (atualização automática):
`https://docs.google.com/spreadsheets/.../export?format=csv`

## 👤 Autor

Rodrigo Siquette (rodrigosiquette@gmail.com)

## 📝 Licença

Uso interno Aegea
