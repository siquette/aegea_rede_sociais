# 📊 Streamlit Scrollytelling - Análise de Sentimento de Mídia

## 🚀 Como Executar

### 1. Instalar Dependências

```bash
pip install streamlit pandas numpy plotly openpyxl
```

### 2. Rodar a Aplicação

```bash
streamlit run streamlit_scrollytelling.py
```

A aplicação abrirá automaticamente no navegador em `http://localhost:8501`

---

## 📁 Estrutura do Projeto

```
projeto/
├── streamlit_scrollytelling.py    # Aplicação principal (arquivo único)
└── README_STREAMLIT.md            # Este arquivo
```

---

## 🎨 Funcionalidades

### **Filtros Globais (Sidebar)**
- 🏢 **Grupo**: Filtrar por grupo empresarial
- 🏭 **Empresa**: Filtrar por empresa específica
- 📅 **Período**: Data início e fim

### **Seções Narrativas (Scrollytelling)**

1. **Conceito e Panorama**
   - Explicação do NSS
   - Distribuição de sentimentos (pizza + barras)
   - Métricas resumo

2. **Agenda da Mídia**
   - Top N categorias
   - Filtro: sentimento (Positiva/Neutra/Negativa)
   - Slider: número de categorias (5-20)

3. **Evolução Temporal**
   - Volume de menções ao longo do tempo
   - Filtro: agregação (Dia/Semana/Mês)
   - Distribuição semanal

4. **Tier × Sentimento**
   - Heatmap Tier × Classificação
   - Filtro: categoria (drill-down)
   - Explicação do NSS ponderado

5. **Evolução do NSS**
   - Linha temporal do NSS
   - Filtros: categoria, modo (simples/ponderado)

6. **Heatmap Temporal**
   - NSS por Categoria × Mês
   - Filtro: mínimo de menções mensais

7. **Hierarquia de Mídia**
   - Treemap interativo (Mídia → Veículo → Sentimento → Tema)
   - Filtros: top N veículos, mínimo de menções

8. **Conclusões**
   - NSS por Tier
   - Recomendações de próximos passos

---

## 🎯 Navegação

### **Scroll Natural**
- Role a página normalmente
- Cada seção revela gradualmente os insights
- Gráficos são interativos (zoom, hover, filtros)

### **Filtros**
- **Globais** (sidebar): aplicam a TODAS as visualizações
- **Específicos** (inline): aplicam apenas ao gráfico local
- Mudanças nos filtros atualizam automaticamente

### **Interatividade Plotly**
- 🖱️ **Hover**: detalhes sobre cada ponto/barra
- 🔍 **Zoom**: clique e arraste para dar zoom
- 📷 **Download**: ícone de câmera para salvar imagem
- ↩️ **Reset**: duplo clique para resetar zoom

---

## 📊 Dados

A aplicação carrega dados diretamente do Google Sheets:
```
URL: https://docs.google.com/spreadsheets/d/1UVGM5g7A2pSmg4Nn5eTzjZhd25sAFFDbkBclRfyNgX8
```

**Cache**: Dados ficam em cache por 1 hora (3600s) para performance.

Para usar dados locais (CSV), modifique a função `carregar_dados()`:
```python
def carregar_dados():
    df = pd.read_csv("seu_arquivo.csv")
    # ... resto do código
```

---

## 🎨 Personalização

### **Cores do Tema**
Edite o dicionário `COLORS_SENTIMENT`:
```python
COLORS_SENTIMENT = {
    'POSITIVA': '#2ecc71',   # Verde
    'NEUTRA': '#95a5a6',     # Cinza
    'NEGATIVA': '#e74c3c',   # Vermelho
    'PUBLICIDADE': '#3498db' # Azul
}
```

### **CSS Customizado**
Todo o CSS está no bloco `st.markdown()` no início do código.
Procure por `<style>` e modifique conforme necessário.

### **Título e Metadados**
```python
st.set_page_config(
    page_title="Seu Título",
    page_icon="📊",
    layout="wide"
)
```

---

## 🐛 Troubleshooting

### **Erro: ModuleNotFoundError**
```bash
pip install streamlit pandas numpy plotly openpyxl
```

### **Gráficos não aparecem**
- Certifique-se de que há dados no período filtrado
- Tente resetar os filtros (botão na sidebar)

### **Performance lenta**
- Reduza o período de análise
- O cache está ativado (dados carregam 1x por hora)

### **Porta já em uso**
```bash
streamlit run streamlit_scrollytelling.py --server.port 8502
```

---

## 📤 Deploy (Streamlit Cloud)

### **1. Criar repositório GitHub**
```bash
git init
git add streamlit_scrollytelling.py
git commit -m "Initial commit"
git remote add origin https://github.com/seu-usuario/seu-repo.git
git push -u origin main
```

### **2. Criar requirements.txt**
```
streamlit
pandas
numpy
plotly
openpyxl
```

### **3. Deploy no Streamlit Cloud**
1. Acesse https://streamlit.io/cloud
2. Conecte sua conta GitHub
3. Selecione o repositório
4. Deploy!

URL pública estará disponível em: `https://seu-app.streamlit.app`

---

## 📝 Notas Técnicas

### **Estrutura de Código**
- ✅ Arquivo único (fácil de distribuir)
- ✅ Funções bem documentadas
- ✅ Cache para performance
- ✅ Responsivo (funciona em mobile)

### **Frameworks Utilizados**
- **Streamlit**: Interface web
- **Plotly**: Gráficos interativos
- **Pandas**: Manipulação de dados
- **NumPy**: Operações numéricas

### **Behavioral Data Science**
A análise segue os conceitos de Florent Buisson:
- **Declared Data**: Surveys (não usado aqui)
- **Revealed Data**: Comportamento observado (clipping de mídia)
- **Tier Weighting**: Pondera pelo impacto real

---

## 🔄 Próximos Passos

Após validar o Streamlit, criaremos:
- **Quarto RevealJS**: Slides interativos
- **Shiny for Python**: Versão mais polida
- **Quarto Dashboard**: Comparação com layout tradicional

---

## 📧 Suporte

Para dúvidas ou sugestões, revise:
1. Este README
2. Comentários no código
3. Documentação Streamlit: https://docs.streamlit.io

---

**Desenvolvido com** ❤️ **usando Streamlit + Plotly**
