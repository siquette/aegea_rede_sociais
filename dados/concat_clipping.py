import pandas as pd
from pathlib import Path
import logging
from typing import List

# Configuração simples de log para acompanharmos o progresso no terminal
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def consolidar_clipping(diretorio_alvo: str, nome_arquivo_saida: str) -> None:
    """
    Lê múltiplos arquivos Excel de um diretório, adiciona uma coluna de rastreabilidade
    e realiza a concatenação vertical (empilhamento por linha).
    """
    caminho_base = Path(diretorio_alvo)
    
    # Busca especificamente os arquivos que seguem o padrão de nomeação da Aegea
    # Isso evita ler o próprio arquivo de saída se rodarmos o script duas vezes
    arquivos_excel = sorted(caminho_base.glob("??.2025 - Clipping Geral*.xlsx"))
    
    if not arquivos_excel:
        logging.warning("Nenhum arquivo correspondente encontrado no diretório.")
        return

    lista_dfs: List[pd.DataFrame] = []

    for arquivo in arquivos_excel:
        try:
            logging.info(f"Processando: {arquivo.name}")
            
            # Lendo a planilha (se o Excel tiver múltiplas abas, você pode precisar do sheet_name=...)
            df_temp = pd.read_excel(arquivo)
            
            # BOA PRÁTICA: Criar uma variável que guarde a origem temporal daquele dado.
            # Como o nome do arquivo começa com "MM", pegamos os 2 primeiros caracteres.
            mes_ref = arquivo.name[:2]
            df_temp['mes_referencia'] = mes_ref
            
            # Adicionando o nome do arquivo inteiro caso queira auditar depois
            df_temp['arquivo_origem'] = arquivo.name 
            
            lista_dfs.append(df_temp)
            
        except Exception as e:
            logging.error(f"Erro ao tentar ler o arquivo {arquivo.name}. Detalhe: {e}")

    if lista_dfs:
        logging.info("Iniciando a concatenação vertical...")
        
        # O axis=0 empilha por linha. 
        # O ignore_index=True reseta o índice, criando um index sequencial limpo do 0 até N.
        df_consolidado = pd.concat(lista_dfs, axis=0, ignore_index=True)
        
        logging.info(f"Concatenação concluída. Shape final: {df_consolidado.shape}")
        
        # Exportando o resultado
        caminho_saida = caminho_base / nome_arquivo_saida
        df_consolidado.to_excel(caminho_saida, index=False)
        
        logging.info(f"Arquivo final salvo com sucesso em: {caminho_saida}")

if __name__ == "__main__":
    # "." significa o diretório atual onde você vai rodar o script
    DIR_ATUAL = "."
    ARQUIVO_FINAL = "Clipping_Consolidado_Aegea_2025.xlsx"
    
    consolidar_clipping(DIR_ATUAL, ARQUIVO_FINAL)