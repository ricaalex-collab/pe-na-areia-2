import streamlit as st
import pandas as pd
from pypdf import PdfReader
import re
import os

# Configurações de exibição
st.set_page_config(page_title="Painel Penaareia", layout="wide")

# 1. GERENCIAMENTO DE ARQUIVO DE DADOS
ARQUIVO_DADOS = "membros_v1.csv"

def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        return pd.read_csv(ARQUIVO_DADOS, dtype={'ID': str})
    else:
        # Criar dados iniciais baseados no seu print
        data = {
            'Nome': ['Alemão e Pri', 'Alexandre e Vanessa', 'André e Denise', 'Cabeção', 'Cacá e Karina', 'Campana', 'Caxias e Van'],
            'ID': ['00', '06', '02', '12', '01', '11', '04'],
            'Saldo': [-120.0, -120.0, -180.0, 90.0, -180.0, -190.0, -240.0],
            'Taxa Mensal': [60.0, 60.0, 60.0, 30.0, 60.0, 30.0, 60.0]
        }
        df = pd.DataFrame(data)
        df.to_csv(ARQUIVO_DADOS, index=False)
        return df

def salvar_dados(df):
    df.to_csv(ARQUIVO_DADOS, index=False)

# 2. SISTEMA DE LOGIN
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("Acesso ao Painel")
    senha = st.text_input("Palavra-passe:", type="password")
    if st.button("Entrar"):
        if senha == "12345": # Altere aqui sua senha
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Senha incorreta")
    st.stop()

# 3. INTERFACE PRINCIPAL
st.title("Painel do Administrador - Grupo")
df_membros = carregar_dados()

# Cards Superiores
col1, col2 = st.columns(2)
col1.metric("Saldo Total do Grupo", f"R$ {df_membros['Saldo'].sum():.2f}")
col2.metric("Membros Ativos", len(df_membros))

# 4. PROCESSAMENTO DO PDF (Lógica baseada no seu extrato da CAIXA)
st.divider()
st.subheader("Atualizar via Extrato PDF")
arquivo_pdf = st.file_uploader("Upload do extrato CAIXA", type="pdf")

if arquivo_pdf:
    if st.button("Processar e Salvar"):
        reader = PdfReader(arquivo_pdf)
        texto = ""
        for page in reader.pages:
            texto += page.extract_text()
        
        # Procura por "PIX RECEBIDO", o nome do favorecido e o valor
        # O padrão abaixo identifica o valor e os centavos (ID)
        padrao_pix = r"PIX RECEBIDO\n(.*?)\n.*?\n([\d\.,]+)\sC"
        matches = re.findall(padrao_pix, texto)
        
        if matches:
            sucessos = 0
            for nome_pix, valor_str in matches:
                valor_float = float(valor_str.replace('.', '').replace(',', '.'))
                # Identifica ID pelos centavos (ex: 60,06 -> ID 06)
                centavos = int(round((valor_float - int(valor_float)) * 100))
                id_encontrado = str(centavos).zfill(2)
                
                # Atualiza no DataFrame
                if id_encontrado in df_membros['ID'].values:
                    idx = df_membros.index[df_membros['ID'] == id_encontrado][0]
                    valor_principal = int(valor_float)
                    df_membros.at[idx, 'Saldo'] += valor_principal
                    st.success(f"Pagamento de R$ {valor_principal} creditado para: {df_membros.at[idx, 'Nome']}")
                    sucessos += 1
            
            if sucessos > 0:
                salvar_dados(df_membros)
                st.info("Todos os saldos foram atualizados e salvos!")
        else:
            st.warning("Nenhum pagamento PIX com o padrão de centavos/ID foi encontrado no PDF.")

# 5. TABELA DE MEMBROS
st.divider()
st.subheader("Lista de Membros")
# Permite edição manual direto na tabela se necessário
df_editado = st.data_editor(df_membros, num_rows="dynamic", use_container_width=True)

if st.button("Salvar Alterações Manuais"):
    salvar_dados(df_editado)
    st.success("Dados salvos com sucesso!")
