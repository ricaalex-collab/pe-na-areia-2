import streamlit as st
import pandas as pd
from pypdf import PdfReader
import re
import os

# Configuração da página
st.set_page_config(page_title="Penaareia Admin", layout="wide")

# Gerenciamento de Dados local (Arquivo CSV no GitHub)
ARQUIVO = "membros.csv"

def carregar_dados():
    if not os.path.exists(ARQUIVO):
        # Dados iniciais baseados no seu print
        df = pd.DataFrame({
            'ID': ['00', '06', '02', '12', '01', '11', '04'],
            'Nome': ['Alemão e Pri', 'Alexandre e Vanessa', 'André e Denise', 'Cabeção', 'Cacá e Karina', 'Campana', 'Caxias e Van'],
            'Saldo': [-120.0, -120.0, -180.0, 90.0, -180.0, -190.0, -240.0],
            'Mensalidade': [60.0, 60.0, 60.0, 30.0, 60.0, 30.0, 60.0]
        })
        df.to_csv(ARQUIVO, index=False)
    return pd.read_csv(ARQUIVO, dtype={'ID': str})

# Login simplificado
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    senha = st.text_input("Senha:", type="password")
    if st.button("Entrar"):
        if senha == "123": # Mude sua senha aqui
            st.session_state.auth = True
            st.rerun()
    st.stop()

df = carregar_dados()

st.title("Painel do Administrador")

# --- LÓGICA DE UPLOAD ---
with st.expander("Subir Extrato PDF"):
    pdf = st.file_uploader("Arraste aqui", type="pdf")
    if pdf and st.button("Processar"):
        reader = PdfReader(pdf)
        texto = ""
        for page in reader.pages:
            texto += page.extract_text()
        
        # Expressão regular para capturar PIX RECEBIDO 
        # Ela procura o texto, pula o nome e o CPF até achar o valor "XX,XX C"
        pattern = r"PIX RECEBIDO\n(.*?)\n.*?\n\n\n([\d\.,]+)\sC"
        matches = re.findall(pattern, texto)
        
        if matches:
            for nome_extrato, valor_str in matches:
                # Converte "60,06" em 60.06
                v_total = float(valor_str.replace('.', '').replace(',', '.'))
                # Extrai os centavos como ID
                centavos = int(round((v_total - int(v_total)) * 100))
                id_id = str(centavos).zfill(2)
                
                if id_id in df['ID'].values:
                    idx = df.index[df['ID'] == id_id][0]
                    df.at[idx, 'Saldo'] += int(v_total)
                    st.success(f"Creditado R$ {int(v_total)} para {df.at[idx, 'Nome']} (ID {id_id})")
            
            df.to_csv(ARQUIVO, index=False)
            st.rerun()
        else:
            st.warning("Nenhum pagamento identificado. Verifique se o PDF é o extrato correto da CAIXA.")

# --- TABELA DE MEMBROS ---
st.subheader("Lista de Membros")
df_edit = st.data_editor(df, use_container_width=True, num_rows="dynamic")

if st.button("Salvar Alterações"):
    df_edit.to_csv(ARQUIVO, index=False)
    st.success("Dados salvos!")
