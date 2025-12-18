import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from pypdf import PdfReader
import re

# Configurações iniciais
st.set_page_config(page_title="Painel do Administrador", layout="wide")
SENHA_ACESSO = "suasenha123" # Altere para a senha que desejar

# Conexão com Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def realizar_login():
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False
    
    if not st.session_state.autenticado:
        st.title("Acesso Restrito")
        senha = st.text_input("Digite a senha do painel:", type="password")
        if st.button("Entrar"):
            if senha == SENHA_ACESSO:
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Senha incorreta.")
        return False
    return True

def processar_extrato(pdf_file, df_membros):
    reader = PdfReader(pdf_file)
    texto = ""
    for page in reader.pages:
        texto += page.extract_text()

    # Procura por padrões de "PIX RECEBIDO" e o valor
    # Exemplo no seu PDF: "PIX RECEBIDO", "Nome", "Valor C"
    padrao = r"PIX RECEBIDO\n(.*?)\n.*?\n([\d\.,]+)\sC"
    matches = re.findall(padrao, texto)
    
    atualizacoes = []
    for nome_extrato, valor_str in matches:
        valor_cheio = float(valor_str.replace('.', '').replace(',', '.'))
        inteiro = int(valor_cheio)
        centavos = round((valor_cheio - inteiro) * 100)
        id_encontrado = str(centavos).zfill(2)
        
        atualizacoes.append({
            "Nome": nome_extrato.strip(),
            "Valor": inteiro,
            "ID_Identificado": id_encontrado
        })
    return atualizacoes

if realizar_login():
    st.title("📊 Painel do Administrador")
    
    # Carregar dados da planilha
    try:
        df_membros = conn.read(worksheet="Membros")
    except:
        st.error("Erro ao conectar com a planilha. Verifique os Secrets.")
        st.stop()

    # Cards de Resumo
    col1, col2 = st.columns(2)
    saldo_total = df_membros['Saldo'].sum()
    col1.metric("Saldo Acumulado dos Membros", f"R$ {saldo_total:.2f}")
    
    # Área de Upload
    st.divider()
    st.subheader("Atualizar Pagamentos via Extrato")
    arquivo_pdf = st.file_uploader("Arraste o PDF do extrato da CAIXA aqui", type="pdf")
    
    if arquivo_pdf:
        if st.button("Processar Extrato e Atualizar Saldos"):
            resultados = processar_extrato(arquivo_pdf, df_membros)
            if resultados:
                for item in resultados:
                    # Lógica para somar o valor ao saldo do ID correspondente
                    id_id = item['ID_Identificado']
                    valor_pago = item['Valor']
                    
                    if id_id in df_membros['ID'].values:
                        idx = df_membros.index[df_membros['ID'] == id_id][0]
                        df_membros.at[idx, 'Saldo'] += valor_pago
                        st.success(f"Confirmado: {item['Nome']} (ID {id_id}) pagou R$ {valor_pago:.2f}")
                
                # Salvar de volta na planilha
                conn.update(worksheet="Membros", data=df_membros)
                st.balloons()
            else:
                st.warning("Nenhum pagamento PIX novo identificado no padrão de centavos.")

    # Tabela de Visualização
    st.divider()
    st.subheader("Lista de Membros")
    st.dataframe(df_membros, use_container_width=True)
