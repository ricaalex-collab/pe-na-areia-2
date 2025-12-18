import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from pypdf import PdfReader
import re

# Configuração da página
st.set_page_config(page_title="Painel do Administrador", layout="wide")

# LOGIN SIMPLES
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    senha = st.text_input("Digite a senha do painel:", type="password")
    if st.button("Entrar"):
        if senha == "SUA_SENHA_AQUI": # Defina sua senha aqui
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Senha incorreta.")
    st.stop()

# CONEXÃO COM GOOGLE SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)

def processar_pdf_caixa(file):
    reader = PdfReader(file)
    texto = ""
    for page in reader.pages:
        texto += page.extract_text()
    
    # Busca padrão: Nome do Favorecido seguido de Valor com "C" (Crédito)
    # Ex: Alexandre Leoni Gu ... 60,06 C
    padrao = r"(.*?)\n[\d\.\*]*\n\n\n([\d\.,]+)\sC"
    matches = re.findall(padrao, texto)
    
    resultados = []
    for nome, valor_str in matches:
        if "PIX RECEBIDO" in texto: # Garante que estamos pegando entradas
            valor_limpo = valor_str.replace('.', '').replace(',', '.')
            valor_float = float(valor_limpo)
            
            # Pega apenas os centavos como ID
            centavos = int(round((valor_float - int(valor_float)) * 100))
            id_id = str(centavos).zfill(2)
            
            resultados.append({
                "Nome": nome.strip(),
                "Valor_Total": valor_float,
                "Valor_Base": int(valor_float),
                "ID_Identificado": id_id
            })
    return resultados

# INTERFACE
st.title("📊 Gestão de Pagamentos - Penaareia")

# Lendo dados da aba "Membros"
df_membros = conn.read(worksheet="Membros")

# Exibição do Saldo Total
saldo_total = df_membros['Saldo'].sum()
st.metric("Saldo Total em Conta", f"R$ {saldo_total:,.2f}")

# UPLOAD E PROCESSAMENTO
st.subheader("Upload de Extrato (PDF CAIXA)")
arquivo = st.file_uploader("Selecione o arquivo", type="pdf")

if arquivo and st.button("Processar Pagamentos"):
    pagamentos = processar_pdf_caixa(arquivo)
    
    for p in pagamentos:
        id_pg = p['ID_Identificado']
        if id_pg in df_membros['ID'].astype(str).values:
            idx = df_membros.index[df_membros['ID'].astype(str) == id_pg][0]
            nome_membro = df_membros.at[idx, 'Nome']
            
            # Atualiza Saldo
            df_membros.at[idx, 'Saldo'] += p['Valor_Base']
            st.success(f"✅ Pagamento identificado: {nome_membro} (ID {id_pg}) - R$ {p['Valor_Base']}")
        else:
            st.warning(f"⚠️ ID {id_pg} encontrado no extrato mas não cadastrado na planilha.")

    # SALVAR NA PLANILHA
    conn.update(worksheet="Membros", data=df_membros)
    st.info("Planilha atualizada com sucesso!")

st.divider()
st.subheader("Lista de Membros")
st.dataframe(df_membros, use_container_width=True)
