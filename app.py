import streamlit as st
import yfinance as yf
from datetime import datetime, time
import requests  
import math

# =====================================================================
# 🔒 CONFIGURAÇÃO DE SEGURANÇA E PARÂMETROS DO SITE (WEB)
# =====================================================================
DATA_EXPIRACAO = "2026-12-30"

TELEGRAM_TOKEN = "7977057617:AAFC1HzeIZIt-WSl19OwcKY4iNjUx6l9Nic"
TELEGRAM_CHAT_ID = "1052417563"
# =====================================================================

st.set_page_config(page_title="Painel Macro WIN", page_icon="📊", layout="centered")

# Cabeçalho do Site
st.markdown("<h1 style='text-align: center;'>📊 SCANNER AUTOMÁTICO</h1>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center; color: #555555;'>@leandro9.1</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-weight: bold;'>Painel de Direção Macro WIN - Versão Mobile/Web</p>", unsafe_allow_html=True)

st.write("---")

# Verificação de Validade no Servidor
data_atual = datetime.now()
data_limite = datetime.strptime(DATA_EXPIRACAO, "%Y-%m-%d")

if data_atual > data_limite:
    st.error("❌ Esta cópia do aplicativo expirou. Entre em contato com o administrador para obter a nova versão.")
else:
    st.success("✅ Sistema operacional da Web validado com sucesso!")
    
    st.markdown("### 📥 Download do Painel Desktop")
    st.write("Clique no botão abaixo para baixar a versão mais recente do painel executável para Windows:")
    
    # Botão de Download do Executável
    try:
        with open("Calculadora_Macro_WIN.exe", "rb") as file:
            btn = st.download_button(
                label="🚀 BAIXAR PAINEL MASTER (.EXE)",
                data=file,
                file_name="Calculadora_Macro_WIN.exe",
                mime="application/octet-stream"
            )
    except FileNotFoundError:
        st.warning("⚠️ O arquivo executável 'Calculadora_Macro_WIN.exe' não foi encontrado no repositório. Por favor, faça o upload dele no GitHub junto com este arquivo.")