import streamlit as st
import pandas as pd
from pypdf import PdfReader
import re
import os

# Configuração que ajuda o carregamento a ser mais leve
st.set_page_config(page_title="Penaareia Admin", layout="wide")

ARQUIVO = "membros.csv"

# Carregamento seguro dos dados
def carregar_dados():
    if not os.path.exists(ARQUIVO):
        # Baseado no seu print
        df = pd.DataFrame({
            'ID': ['00', '06', '02', '12', '01', '11', '04'],
            'Nome': ['Alemão e Pri', 'Alexandre e Vanessa', 'André e Denise', 'Cabeção', 'Cacá e Karina', 'Campana', 'Caxias e Van'],
            'Saldo': [-120.0, -120.0, -180.0, 90.0, -180.0, -190.0, -240.0],
            'Mensalidade': [60.0, 60.0, 60.0, 30.0, 60.0, 30.0, 60.0]
        })
        df.to_csv(ARQUIVO, index=False)
    return pd.read_csv(ARQUIVO, dtype={'ID': str})

# Login
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    senha = st.text_input("Senha de Acesso:", type="password")
    if st.button("Entrar"):
        if senha == "123": # Mude sua senha aqui
            st.session_state.auth = True
            st.rerun()
    st.stop()

df = carregar_dados()
st.title("Painel Administrativo")

# Processamento do PDF otimizado para o padrão da CAIXA 
with st.expander("Processar Extrato Mensal"):
    pdf_file = st.file_uploader("Arraste o extrato aqui", type="pdf")
    if pdf_file and st.button("Confirmar Leitura"):
        reader = PdfReader(pdf_file)
        texto = ""
        for page in reader.pages:
            texto += page.extract_text()
        
        # Regex flexível para o padrão: PIX RECEBIDO -> Nome -> Valor C 
        # Ex: Alexandre Leoni Gu (ID 06) pagando 60,06 C [cite: 5]
        pattern = r"PIX RECEBIDO\s*\n(.*?)\n[\s\S]*?([\d\.,]+)\s*C"
        matches = re.findall(pattern, texto)
        
        if matches:
            for nome_fav, valor_str in matches:
                v_total = float(valor_str.replace('.', '').replace(',', '.'))
                # Extração do ID via centavos
                centavos = int(round((v_total - int(v_total)) * 100))
                id_str = str(centavos).zfill(2)
                
                if id_str in df['ID'].values:
                    idx = df.index[df['ID'] == id_str][0]
                    df.at[idx, 'Saldo'] += int(v_total)
                    st.success(f"Crédito de R$ {int(v_total)} para {df.at[idx, 'Nome']} [ID {id_str}]")
            
            df.to_csv(ARQUIVO, index=False)
            st.info("Planilha atualizada!")
        else:
            st.warning("Nenhum PIX identificado no padrão de centavos.")

# Tabela Interativa
st.subheader("Lista de Membros")
df_edit = st.data_editor(df, use_container_width=True, num_rows="dynamic")

if st.button("Salvar Alterações Manuais"):
    df_edit.to_csv(ARQUIVO, index=False)
    st.success("Dados salvos com sucesso!")
