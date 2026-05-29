import streamlit as st
import yfinance as yf
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# CONFIGURAÇÕES DE SEGURANÇA
SENHA_CORRETA = "WIN2026"
DATA_EXPIRACAO = "2026-05-31"

st.set_page_config(page_title="Painel Macro WIN", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .main { background-color: #121212; color: #E0E0E0; }
    .stButton>button { background-color: #0D47A1; color: white; width: 100%; font-weight: bold; height: 3em; border-radius: 5px; border: none; }
    .stButton>button:hover { background-color: #1565C0; color: white; }
    .stTextInput>div>div>input { background-color: #1E1E1E; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 SCANNER AUTOMÁTICO @leandro9.1")
st.subheader("Painel de Direção Macro WIN - Versão Mobile/Web")

data_limite = datetime.strptime(DATA_EXPIRACAO, "%Y-%m-%d")
if datetime.now() > data_limite:
    st.error("❌ Esta cópia do aplicativo expirou.")
    st.stop()

senha_inserida = st.text_input("🔑 Chave de Acesso:", type="password")

if senha_inserida == SENHA_CORRETA:
    st.success("✅ Acesso Liberado!")
    
    # Atualização automática a cada 30 segundos de forma inteligente
    st_autorefresh(interval=30000, key="datarefresh")

    if st.button("🔄 ATUALIZAR DADOS AGORA"):
        st.rerun()

    st.info(f"⏱️ Última atualização: {datetime.now().strftime('%H:%M:%S')}")

    try:
        tickers_globais = {
            'VIX': '^VIX', 'BRENT': 'BZ=F', 'MINERIO': 'VALE',   
            'SP500': '^GSPC', 'DOW': '^DJI', 'NASDAQ': '^IXIC', 'DXY': 'DX-Y.NYB',
            'PETR4': 'PETR4.SA', 'VALE3': 'VALE3.SA', 'WDO': 'BRL=X'
        }
        
        var = {}
        for nome, ticker in tickers_globais.items():
            t_obj = yf.Ticker(ticker)
            df = t_obj.history(period="2d")
            if len(df) >= 2:
                ant = df['Close'].iloc[-2]
                atu = df['Close'].iloc[-1]
                var[nome] = ((atu - ant) / ant) * 100
            else:
                var[nome] = 0.0

        peso_alta = (var['SP500'] * 20) + (var['NASDAQ'] * 15) + (var['DOW'] * 10) + (var['MINERIO'] * 30) + (var['BRENT'] * 25)
        peso_baixa = (-var['VIX'] * 40) + (-var['DXY'] * 60)
        score_total = peso_alta + peso_baixa
        
        score_limitado = max(-200, min(score_total, 200))
        porcentagem_forca = abs(score_limitado) / 200 * 100
        if 0 < porcentagem_forca < 10: 
            porcentagem_forca = 12.5 
            
        total_blocos = 15  
        blocos_preenchidos = int((porcentagem_forca / 100) * total_blocos)
        grafico_barra = ("█" * blocos_preenchidos) + ("░" * (total_blocos - blocos_preenchidos))
        
        if score_total > 15:
            direcao = " COMPRA  ▲ "
            cor_card = "rgba(0, 230, 118, 0.2)"
            texto_cor = "#00E676"
            if porcentagem_forca <= 30:
                detalhe_cenario = f"Fluxo Comprador Fraco ({porcentagem_forca:.1f}%)."
            elif porcentagem_forca <= 65:
                detalhe_cenario = f"Fluxo Comprador Moderado ({porcentagem_forca:.1f}%)."
            else:
                detalhe_cenario = f"Fluxo COMPRADOR FORTE ({porcentagem_forca:.1f}%)."
        elif score_total < -15:
            direcao = " VENDA  ▼ "
            cor_card = "rgba(255, 23, 68, 0.2)"
            texto_cor = "#FF1744"
            if porcentagem_forca <= 30:
                detalhe_cenario = f"Fluxo Vendedor Fraco ({porcentagem_forca:.1f}%)."
            elif porcentagem_forca <= 65:
                detalhe_cenario = f"Fluxo Vendedor Moderado ({porcentagem_forca:.1f}%)."
            else:
                detalhe_cenario = f"Fluxo VENDEDOR FORTE ({porcentagem_forca:.1f}%)."
        else:
            direcao = " NEUTRO / LATERAL  ◄► "
            detalhe_cenario = "Mercado totalmente equilibrado e sem direção."
            porcentagem_forca = 0.0
            cor_card = "rgba(66, 66, 66, 0.2)"
            texto_cor = "#B0BEC5"
            grafico_barra = "░" * total_blocos

        score_novo = (var['SP500'] * 25) + (var['NASDAQ'] * 25) + (var['PETR4'] * 25) + (var['VALE3'] * 25) + (-var['WDO'] * 30)
        score_novo_limitado = max(-150, min(score_novo, 150))
        porcentagem_novo = abs(score_novo_limitado) / 150 * 100
        if 0 < porcentagem_novo < 10:
            porcentagem_novo = 12.5
            
        blocos_novos_preenchidos = int((porcentagem_novo / 100) * total_blocos)
        barra_novo_termometro = ("█" * blocos_novos_preenchidos) + ("░" * (total_blocos - blocos_novos_preenchidos))
        cor_texto_novo = "#00E676" if score_novo > 10 else "#FF1744" if score_novo < -10 else "#FFB300"

        st.markdown(f"""
            <div style="background-color: {cor_card}; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid {texto_cor}; margin-bottom: 20px;">
                <h2 style="color: {texto_cor}; margin: 0;">{direcao}</h2>
                <p style="margin: 10px 0 0 0; font-size: 1.1em;"><b>Cenário:</b> {detalhe_cenario}</p>
            </div>
            """, unsafe_allow_html=True)

        aba1, aba2 = st.tabs(["🌍 Mundo (Global)", "🇧🇷 Brasil (B3)"])

        with aba1:
            st.markdown(f"### 📊 Fluxo Global: **{porcentagem_forca:.1f}%**")
            st.code(f"[{grafico_barra}]")
            
            st.markdown(f"### ⚡ Pressão Co-relação: <span style='color:{cor_texto_novo}'>{porcentagem_novo:.1f}%</span>", unsafe_allow_html=True)
            st.code(f"[{barra_novo_termometro}]")
            
            st.markdown("---")
            st.markdown("#### 🇺🇸 Bolsas Americanas")
            st.write(f"• **S&P 500:** {var['SP500']:+.2f}%")
            st.write(f"• **Nasdaq:** {var['NASDAQ']:+.2f}%")
            st.write(f"• **Dow Jones:** {var['DOW']:+.2f}%")
            
            st.markdown("#### 📦 Commodities")
            st.write(f"• **Minério (VALE):** {var['MINERIO']:+.2f}%")
            st.write(f"• **Petróleo Brent:** {var['BRENT']:+.2f}%")
            
            st.markdown("#### ⚠️ Proteção e Risco")
            st.write(f"• **Dólar DXY:** {var['DXY']:+.2f}%")
            st.write(f"• **Índice VIX:** {var['VIX']:+.2f}%")

        with aba2:
            try:
                ind_obj = yf.Ticker("^BVSP")
                df_ind = ind_obj.history(period="2d")
                cot_ind = df_ind['Close'].iloc[-1]
                var_ind = ((df_ind['Close'].iloc[-1] - df_ind['Close'].iloc[-2]) / df_ind['Close'].iloc[-2]) * 100
                
                dol_obj = yf.Ticker("BRL=X")
                df_dol = dol_obj.history(period="2d")
                cot_dol = df_dol['Close'].iloc[-1]
                var_dol = ((df_dol['Close'].iloc[-1] - df_dol['Close'].iloc[-2]) / df_dol['Close'].iloc[-2]) * 100
            except:
                cot_ind, var_ind, cot_dol, var_dol = 0.0, 0.0, 0.0, 0.0

            st.markdown("### 📊 Ativos Futuros B3")
            st.write(f"• **Mini-Índice (WIN):** {int(cot_ind)} pts ({var_ind:+.2f}%)")
            st.write(f"• **Mini-Dólar (WDO):** R$ {cot_dol:.3f} ({var_dol:+.2f}%)")
            st.write(f"• **PETR4:** {var['PETR4']:+.2f}%")
            st.write(f"• **VALE3:** {var['VALE3']:+.2f}%")

    except Exception as e:
        st.error(f"Erro ao carregar dados do mercado.")
else:
    if senha_inserida != "":
        st.error("Chave de Acesso Incorreta!")