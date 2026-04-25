#!/bin/bash
# Script de reorganização do projeto opniao_aegea
# Autor: Claude + Rodrigo Siquette
# Data: 2026-04-23

set -e  # Para em caso de erro

echo "🔄 Iniciando reorganização do projeto..."

# Backup
echo "📦 Criando backup..."
tar -czf backup_$(date +%Y%m%d_%H%M%S).tar.gz \
    --exclude='dados' \
    --exclude='*.lock' \
    --exclude='.pixi' \
    .
echo "✅ Backup criado"

# Criar estrutura
echo "📁 Criando nova estrutura de pastas..."
mkdir -p notebooks/{exploratorias,producao,archive}
mkdir -p dashboards/streamlit/{pages,utils}
mkdir -p dashboards/shiny
mkdir -p scripts
mkdir -p docs/relatorios

# Mover notebooks
echo "📓 Organizando notebooks..."
[ -f analise_satisfacao_comentada_v3_improved.ipynb ] && \
    mv analise_satisfacao_comentada_v3_improved.ipynb notebooks/producao/

[ -f analise_temporal_multiplas_perspectivas.ipynb ] && \
    mv analise_temporal_*.ipynb notebooks/exploratorias/ 2>/dev/null || true

[ -f analise_satisfacao1.ipynb ] && \
    mv analise_satisfacao*.ipynb notebooks/archive/ 2>/dev/null || true

[ -f secao_3_5.ipynb ] && \
    mv secao_3_5.ipynb notebooks/exploratorias/

# Mover scripts
echo "🐍 Organizando scripts..."
[ -f analises_adicionais.py ] && mv analises_adicionais.py scripts/
[ -f relatorio_midia.py ] && mv relatorio_midia.py scripts/

# Mover documentação
echo "📄 Organizando documentação..."
[ -f README_dashboards.md ] && mv README_dashboards.md docs/
[ -f analise_satisfacao_comentada.html ] && mv analise_satisfacao_comentada.html docs/relatorios/
[ -f relatorio_h2r.qmd ] && mv relatorio_h2r.qmd docs/relatorios/
[ -f index.html ] && mv *.html docs/relatorios/ 2>/dev/null || true

# Reorganizar Streamlit
echo "📱 Reorganizando Streamlit..."
if [ -d stramilit ]; then
    # Mover conteúdo
    mv stramilit/files/* dashboards/streamlit/ 2>/dev/null || true
    rm -rf stramilit
    
    # Limpar arquivo estranho
    [ -f dashboards/streamlit/=5.18.0 ] && rm dashboards/streamlit/=5.18.0
    
    # Renomear dashboard principal
    [ -f dashboards/streamlit/dashboard_final.py ] && \
        mv dashboards/streamlit/dashboard_final.py dashboards/streamlit/app.py
fi

# Limpar root
echo "🧹 Limpando arquivos duplicados no root..."
rm -f dashboard_satisfacao*.py 2>/dev/null || true
rm -f dashboard_streamlit.py 2>/dev/null || true
rm -f dashboard_shiny.py 2>/dev/null || true

# Mover Shiny se existir
[ -f dashboard_shiny.py ] && mv dashboard_shiny.py dashboards/shiny/app.py 2>/dev/null || true

echo ""
echo "✅ Reorganização concluída!"
echo ""
echo "📂 Nova estrutura:"
tree -L 2 -d

echo ""
echo "🎯 Próximos passos:"
echo "1. Revisar a nova estrutura: tree"
echo "2. Testar dashboard: pixi run dashboard"
echo "3. Abrir notebooks: pixi run notebook"
echo ""
echo "💾 Backup salvo em: backup_$(date +%Y%m%d)*.tar.gz"
