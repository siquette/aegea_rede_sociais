# Dashboard de Satisfação v2

Duas versões do mesmo dashboard para comparação.

## Execução

### Streamlit
```bash
pip install streamlit pandas numpy plotly scipy openpyxl
streamlit run dashboard_streamlit.py
```

### Shiny for Python
```bash
pip install shiny shinywidgets pandas numpy plotly scipy openpyxl
shiny run dashboard_shiny.py
```

## O que mudou em relação à v1

### Novos filtros
- Busca textual por Veículo e Programa (3.773 veículos — multiselect inviável)

### Tab Tier × Classificação (expandida)
- **Heatmap NSS Categoria × Tier** — mostra a mesma categoria com sentimentos opostos entre Tiers
- **Treemap Tier > Categoria** — visualização hierárquica com cor = NSS
- Tabela de divergência MR → LR

### Tab Categorias (melhorada)
- Toggle "Segmentar por Tier" — alterna entre bar chart flat e heatmap por Tier

### Tab Veículos & Programas (nova)
- **Veículos**: Top 20 por Tier selecionado, com NSS divergente
- **Programas**: Pirâmide de sentimento (10 mais negativos + 10 mais positivos)
  - %Neg à esquerda, %Neutra no meio, %Pos à direita
  - Emoji de Tier no label + volume (N)

### Alertas
- Banner automático quando Tier Null > 20% dos dados

## Diferenças entre Streamlit e Shiny

| Aspecto | Streamlit | Shiny |
|---------|-----------|-------|
| Reatividade | Re-executa script inteiro | Granular (só recalcula dependências) |
| CSS/Tema | Customizável via `st.markdown` | Bootstrap nativo via themes |
| Deploy | Streamlit Cloud (gratuito) | ShinyApps.io, Posit Connect |
| Plotly | Nativo com `st.plotly_chart` | Via `shinywidgets` + `render_plotly` |
| Estado | Stateless (reruns) | Stateful (sessão server-side) |
| Curva | Mais simples para começar | Mais poderoso para apps complexos |
