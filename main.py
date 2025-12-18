import streamlit as st
import pandas as pd
from pypdf import PdfReader
import re
import os

st.set_page_config(page_title="Penaareia - Admin", layout="wide")

# --- BANCO DE DADOS LOCAL ---
ARQUIVO_DADOS = "dados_membros.csv"

def inicializar_dados():
    if not os.path.exists(ARQUIVO_DADOS):
        # Criando a lista baseada no seu print inicial
        dados = {
            'ID': ['00', '06', '02', '12', '01', '11', '04'],
            'Nome': ['Alemão e Pri', 'Alexandre e Vanessa', 'André e Denise', 'Cabeção', 'Cacá e Karina', 'Campana', 'Caxias e Van'],
            'Saldo': [-120.0, -120.0, -180.0, 90.0, -180.0, -190.0, -240.0],
            'Taxa': [60.0, 60.0, 60.0, 30.0, 60.0, 30.0, 60.0]
        }
        pd.DataFrame(dados).to_csv(ARQUIVO_DADOS, index=False)

inicializar_dados()
df_membros = pd.read_csv(ARQUIVO_DADOS, dtype={'ID': str})

# --- LOGIN ---
if 'logado' not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    senha = st.text_input("Senha de Administrador", type="password")
    if st.button("Acessar"):
        if senha == "admin123": # Mude sua senha aqui
            st.session_state.logado = True
            st.rerun()
    st.stop()

# --- INTERFACE ---
st.title("Painel do Administrador")

# Upload e Processamento
with st.expander("⬆️ Upload de Extrato PDF", expanded=True):
    arquivo = st.file_uploader("Arraste o extrato da Caixa aqui", type="pdf")
    if arquivo and st.button("Processar Pagamentos"):
        reader = PdfReader(arquivo)
        texto_completo = ""
        for page in reader.pages:
            texto_completo += page.extract_text()
        
        # Lógica de leitura ajustada para o seu PDF 
        # Procura por PIX RECEBIDO, Nome e Valor com centavos
        padrao = r"PIX RECEBIDO\n(.*?)\n.*?\n([\d\.,]+)\sC"
        matches = re.findall(padrao, texto_completo)
        
        if matches:
            count = 0
            for nome_pdf, valor_str in matches:
                # Converte "60,06" em 60.06
                valor_f = float(valor_str.replace('.', '').replace(',', '.'))
                # Extrai centavos para o ID (ex: 0.06 -> "06") 
                centavos = int(round((valor_f - int(valor_f)) * 100))
                id_pix = str(centavos).zfill(2)
                
                if id_pix in df_membros['ID'].values:
                    idx = df_membros.index[df_membros['ID'] == id_pix][0]
                    # Soma apenas o valor inteiro (R$ 60,00) conforme sua regra
                    df_membros.at[idx, 'Saldo'] += int(valor_f)
                    st.success(f"✅ Identificado: {nome_pdf} (ID {id_pix}) - R$ {int(valor_f)}")
                    count += 1
            
            if count > 0:
                df_membros.to_csv(ARQUIVO_DADOS, index=False)
                st.info(f"{count} pagamentos processados com sucesso!")
        else:
            st.warning("Nenhum PIX RECEBIDO encontrado com o padrão de centavos.")

# Exibição da Tabela
st.subheader("Lista de Membros")
df_final = st.data_editor(df_membros, use_container_width=True, num_rows="dynamic")

if st.button("Salvar Alterações Manuais"):
    df_final.to_csv(ARQUIVO_DADOS, index=False)
    st.success("Dados salvos!")
