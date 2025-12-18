import streamlit as st
import pandas as pd
from pypdf import PdfReader # Necessário instalar: pip install pypdf

# Configuração simples de senha
SENHA_ADMIN = "12345" 

def main():
    st.set_page_config(page_title="Painel do Administrador", layout="wide")
    
    # --- SISTEMA DE LOGIN ---
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        senha = st.text_input("Digite a senha de acesso:", type="password")
        if st.button("Entrar"):
            if senha == SENHA_ADMIN:
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Senha incorreta")
        return

    # --- INTERFACE PRINCIPAL ---
    st.title("Painel do Administrador")

    # Exemplo de dados (Na versão final, conectaremos ao Google Sheets)
    if 'df_membros' not in st.session_state:
        data = {
            'Nome': ['Alemão e Pri', 'Alexandre e Vanessa', 'André e Denise'],
            'ID': ['00', '06', '02'],
            'Saldo': [-120.00, -120.00, -180.00],
            'Taxa Mensal': [60.00, 60.00, 60.00]
        }
        st.session_state.df_membros = pd.DataFrame(data)

    # Cards Superiores
    col1, col2 = st.columns(2)
    col1.metric("Saldo da Conta", "R$ 1675.20")
    col2.metric("Última Atualização", "13/09/2025")

    # Botões de Ação
    c1, c2, c3 = st.columns(3)
    if c2.button("Atualizar Taxas (Upload PDF)"):
        fazer_upload_pdf()

    # Tabela de Membros
    st.subheader("Lista de Membros")
    st.table(st.session_state.df_membros)

def fazer_upload_pdf():
    arquivo = st.file_uploader("Selecione o extrato em PDF", type="pdf")
    if arquivo:
        # Lógica de leitura de PDF
        reader = PdfReader(arquivo)
        texto_completo = ""
        for page in reader.pages:
            texto_completo += page.extract_text()
        
        st.success("Extrato lido com sucesso! Processando centavos...")
        # Aqui entraria a lógica de Regex para encontrar valores e IDs
        # Ex: "Transferência Recebida ... 60,06" -> ID 06 pagou.

if __name__ == "__main__":
    main()
