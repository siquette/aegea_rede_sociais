# Relatório de Mídia — Quarto Dashboard & Observable Framework

Duas versões do mesmo relatório narrativo interativo.

## Quarto Dashboard

### Requisitos
```bash
# Instalar Quarto: https://quarto.org/docs/get-started/
# Instalar dependências Python:
pip install shiny shinywidgets pandas numpy plotly scipy
```

### Executar
```bash
quarto serve dashboard_quarto.qmd
```

O Quarto usa `server: shiny` para reatividade — cada filtro no sidebar atualiza todos os gráficos. O layout é `scrolling: true` para narrativa vertical (scrollytelling).

### Publicar
```bash
# Para Quarto Pub (gratuito):
quarto publish quarto-pub dashboard_quarto.qmd

# Para posit.cloud / shinyapps.io:
quarto publish connect dashboard_quarto.qmd
```

---

## Observable Framework

### Requisitos
```bash
# Node.js >= 18
npm install -g @observablehq/framework
```

### Setup
```bash
cd observable/

# Colocar os dados na pasta data/
mkdir -p src/data
# Baixar o CSV do Google Sheets e salvar como:
# src/data/clipping.csv

# OU criar um data loader que baixa automaticamente:
# src/data/clipping.csv.py (script Python que faz o download)
```

### Data Loader automático (opcional)
Crie `src/data/clipping.csv.py`:
```python
import pandas as pd
import sys

url = "https://docs.google.com/spreadsheets/d/1UVGM5g7A2pSmg4Nn5eTzjZhd25sAFFDbkBclRfyNgX8/export?format=csv"
df = pd.read_csv(url)
df.to_csv(sys.stdout, index=False)
```

### Executar
```bash
cd observable/
npm run dev
# ou
npx observable preview
```

### Publicar
```bash
npx observable deploy
```

---

## Diferenças conceituais

| Aspecto | Quarto Dashboard | Observable Framework |
|---------|-----------------|---------------------|
| Linguagem | Python (Shiny) | JavaScript (Observable) |
| Reatividade | Server-side (Shiny) | Client-side (browser) |
| Narrativa | Scrolling dashboard com seções | Scrollytelling nativo |
| Dados | Carrega do Google Sheets via Python | CSV local ou data loader |
| Filtros | Sidebar persistente | Inline no fluxo narrativo |
| Deploy | Quarto Pub, Posit Connect | Observable Cloud, Netlify |
| Performance | Depende do server Python | Roda 100% no browser (rápido) |
| Offline | Não (precisa server) | Sim (após build estático) |
| Melhor para | Equipe que já usa Python/Shiny | Publicação web pública, jornalismo de dados |

## Estrutura dos markdowns

Ambas as versões seguem o mesmo padrão narrativo:

1. **Título com metáfora** — "Efeito Megafone", "Radiografia dos Atores"
2. **O que o gráfico mostra** — sem jargão técnico
3. **Como ler** — instruções concretas (eixos, cores, onde olhar)
4. **O que NÃO está nos markdowns** — interpretação dos dados. O texto ensina a ler; o usuário tira suas próprias conclusões usando os filtros.
