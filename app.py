import streamlit as st
import yfinance as yf
from datetime import datetime, time
import requests
import math

# Configuração da página Web
st.set_page_config(page_title="Painel Macro WIN - Versão Web", page_icon="📊", layout="centered")

# =====================================================================
# 🔒 CONFIGURAÇÕES DE SEGURANÇA E PARÂMETROS DE TELEGRAM
# =====================================================================
SENHA_CORRETA = "WIN2026"
DATA_EXPIRACAO = "2026-12-30"

TELEGRAM_TOKEN = "7977057617:AAFC1HzeIZIt-WSl19OwcKY4iNjUx6l9Nic"
TELEGRAM_CHAT_ID = "1052417563"
# =====================================================================

class MacroQuantWebEngine:
    def __init__(self):
        self.PESOS_BASE_LOCAIS = {
            'VALE3.SA': 0.15, 'PETR4.SA': 0.065, 'PETR3.SA': 0.065,
            'ITUB4.SA': 0.07, 'BBDC4.SA': 0.05, 'BBAS3.SA': 0.05, 'SANB11.SA': 0.05
        }
        self.PESOS_BASE_GLOBAIS = {
            'SP_VISTA': 0.15, 'SP_FUTURO': 0.10, 'NASDAQ': 0.10,     
            'MINERIO': 0.08, 'BRENT': 0.07       
        }
        self.alfa_ema = 0.35  

    def verificar_horario_sp500(self) -> bool:
        agora = datetime.now().time()
        return time(10, 30, 0) <= agora <= time(17, 0, 0)

    def calcular_ema(self, precos, periodo):
        k = 2 / (periodo + 1)
        ema = precos[0]
        for preco in precos[1:]:
            ema = (preco * k) + (ema * (1 - k))
        return ema

    def obter_dados_mercado(self) -> dict:
        dados_retorno = {}
        
        # 1. Coleta do Bloco Local B3
        for ticker in self.PESOS_BASE_LOCAIS.keys():
            try:
                obj = yf.Ticker(ticker)
                df = obj.history(period="5d").dropna(subset=['Close'])
                if len(df) >= 2:
                    var = ((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
                    dados_retorno[ticker] = 0.0 if (math.isnan(var) or math.isinf(var)) else var
                else:
                    dados_retorno[ticker] = 0.0
            except:
                dados_retorno[ticker] = 0.0

        # 2. Coleta do Bloco Internacional e VIX
        tickers_globais = {
            'SP_VISTA': '^GSPC', 'SP_FUTURO': 'ES=F', 'NASDAQ': '^IXIC', 
            'MINERIO': 'VALE', 'BRENT': 'BZ=F', 'VIX': '^VIX'
        }
        for nome, ticker in tickers_globais.items():
            try:
                obj = yf.Ticker(ticker)
                df = obj.history(period="5d").dropna(subset=['Close'])
                if len(df) >= 2:
                    var = ((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
                    dados_retorno[f"{nome}_var"] = 0.0 if (math.isnan(var) or math.isinf(var)) else var
                    dados_retorno[f"{nome}_atual"] = df['Close'].iloc[-1]
                else:
                    dados_retorno[f"{nome}_var"] = 0.0
                    dados_retorno[f"{nome}_atual"] = 15.0 if nome == 'VIX' else 0.0
            except:
                dados_retorno[f"{nome}_var"] = 0.0
                dados_retorno[f"{nome}_atual"] = 15.0 if nome == 'VIX' else 0.0

        # 3. Coleta do Bloco Dólar
        tickers_dolar = {'DXY': 'DX-Y.NYB', 'WDO': 'BRL=X'}
        for nome, ticker in tickers_dolar.items():
            try:
                obj = yf.Ticker(ticker)
                df = obj.history(period="5d").dropna(subset=['Close'])
                if len(df) >= 2:
                    var = ((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
                    dados_retorno[f"{nome}_var"] = 0.0 if (math.isnan(var) or math.isinf(var)) else var
                else:
                    dados_retorno[f"{nome}_var"] = 0.0
            except:
                dados_retorno[f"{nome}_var"] = 0.0

        # 4. Juros DI sem 404 (DI1F29.SA)
        try:
            obj_di = yf.Ticker('DI1F29.SA')
            df_di = obj_di.history(period="5d").dropna(subset=['Close'])
            if len(df_di) >= 2:
                var_di = ((df_di['Close'].iloc[-1] - df_di['Close'].iloc[-2]) / df_di['Close'].iloc[-2]) * 100
                dados_retorno['DI_var'] = 0.0 if (math.isnan(var_di) or math.isinf(var_di)) else var_di
            else:
                dados_retorno['DI_var'] = 0.0
        except:
            dados_retorno['DI_var'] = 0.0

        # 5. IBOV / WIN
        try:
            obj_win = yf.Ticker('^BVSP')
            df_win = obj_win.history(period="35d").dropna(subset=['Close', 'Volume'])
            if len(df_win) >= 22:
                precos_fechamento = df_win['Close'].tolist()
                dados_retorno['WIN_EMA9'] = self.calcular_ema(precos_fechamento, 9)
                dados_retorno['WIN_EMA21'] = self.calcular_ema(precos_fechamento, 21)
                var_win = ((df_win['Close'].iloc[-1] - df_win['Close'].iloc[-2]) / df_win['Close'].iloc[-2]) * 100
                dados_retorno['WIN_var'] = 0.0 if math.isnan(var_win) else var_win
                dados_retorno['WIN_vol_atual'] = df_win['Volume'].iloc[-1]
                dados_retorno['WIN_vol_medio'] = df_win['Volume'].iloc[-21:-1].mean()
            else:
                dados_retorno['WIN_EMA9'] = 0.0
                dados_retorno['WIN_EMA21'] = 0.0
                dados_retorno['WIN_var'] = 0.0
                dados_retorno['WIN_vol_atual'] = 1.0
                dados_retorno['WIN_vol_medio'] = 1.0
        except:
            dados_retorno['WIN_EMA9'] = 0.0
            dados_retorno['WIN_EMA21'] = 0.0
            dados_retorno['WIN_var'] = 0.0
            dados_retorno['WIN_vol_atual'] = 1.0
            dados_retorno['WIN_vol_medio'] = 1.0
                
        return dados_retorno

    def calcular_direcao_ponderada(self, dados: dict) -> dict:
        var_vale = dados.get('VALE3.SA', 0.0)
        var_petr = (dados.get('PETR4.SA', 0.0) + dados.get('PETR3.SA', 0.0)) / 2
        var_ifnc = (dados.get('ITUB4.SA', 0.0) + dados.get('BBDC4.SA', 0.0) + 
                    dados.get('BBAS3.SA', 0.0) + dados.get('SANB11.SA', 0.0)) / 4
        
        forcas_locais = {'VALE': abs(var_vale), 'PETR': abs(var_petr), 'BANC': abs(var_ifnc)}
        lider_local = max(forcas_locais, key=forcas_locais.get) if any(forcas_locais.values()) else 'VALE'
        
        peso_vale = 0.22 if lider_local == 'VALE' else 0.15
        peso_petr = 0.18 if lider_local == 'PETR' else 0.13
        peso_ifnc = 0.28 if lider_local == 'BANC' else 0.22
        soma_pesos_locais = peso_vale + peso_petr + peso_ifnc
        
        media_ponderada_local = ((var_vale * peso_vale) + (var_petr * peso_petr) + (var_ifnc * peso_ifnc)) / soma_pesos_locais

        pesos_g = self.PESOS_BASE_GLOBAIS.copy()
        if not self.verificar_horario_sp500():
            pesos_g['SP_FUTURO'] += pesos_g['SP_VISTA']
            pesos_g['SP_VISTA'] = 0.0

        media_ponderada_global = (
            (dados.get('SP_VISTA_var', 0.0) * pesos_g['SP_VISTA']) +
            (dados.get('SP_FUTURO_var', 0.0) * pesos_g['SP_FUTURO']) +
            (dados.get('NASDAQ_var', 0.0) * pesos_g['NASDAQ']) +
            (dados.get('MINERIO_var', 0.0) * pesos_g['MINERIO']) +
            (dados.get('BRENT_var', 0.0) * pesos_g['BRENT'])
        ) / sum(pesos_g.values())

        score_base = (media_ponderada_local * 0.50) + (media_ponderada_global * 0.50)
        score_base += (-(dados.get('DXY_var', 0.0) * 0.40 + dados.get('WDO_var', 0.0) * 0.60) * 0.25)
        score_base += (-dados.get('DI_var', 0.0) * 0.30)

        ema9 = dados.get('WIN_EMA9', 0.0)
        ema21 = dados.get('WIN_EMA21', 0.0)
        if ema9 > ema21 and ema21 > 0:
            sit_tendencia, reforco = "ALTA (EMA9 > EMA21)", 0.15
        elif ema9 < ema21 and ema21 > 0:
            sit_tendencia, reforco = "BAIXA (EMA9 < EMA21)", -0.15
        else:
            sit_tendencia, reforco = "LATERALIZADA", 0.0
        score_base += reforco

        if dados.get('WIN_vol_atual', 1.0) > dados.get('WIN_vol_medio', 1.0):
            sit_volume, mult_vol = "ACIMA DA MÉDIA (CONFIRMA)", 1.20
        else:
            sit_volume, mult_vol = "ABAIXO DA MÉDIA (FRACO)", 0.80
        score_base *= mult_vol

        # Suavização simples para persistência Web Session State
        if 'last_score' not in st.session_state:
            st.session_state.last_score = score_base
        st.session_state.last_score = (score_base * self.alfa_ema) + (st.session_state.last_score * (1 - self.alfa_ema))
        score_suavizado = st.session_state.last_score

        vix_atual = dados.get('VIX_atual', 0.0)
        if vix_atual < 18.0:
            regime_vix, alerta_vix, redutor = "Normal", "✅ Fluxo normal para operações (Lote Cheio).", 1.0
        elif 18.0 <= vix_atual <= 22.0:
            regime_vix, alerta_vix, redutor = "Moderado", "⚠️ Volatilidade subindo. Alongue stops.", 0.85
        else:
            regime_vix, alerta_vix, redutor = "Estressado", "🚨 ALERTA: VIX Elevado! Reduzir lote!", 0.50

        if score_suavizado > 0: score_suavizado *= redutor
        if (score_suavizado > 0 and ema9 < ema21) or (score_suavizado < 0 and ema9 > ema21): score_suavizado *= 0.60

        direcoes = [var_vale > 0, var_petr > 0, var_ifnc > 0, dados.get('SP_FUTURO_var', 0.0) > 0, dados.get('NASDAQ_var', 0.0) > 0, dados.get('BRENT_var', 0.0) > 0, (dados.get('DXY_var', 0.0) * 0.40 + dados.get('WDO_var', 0.0) * 0.60) < 0, dados.get('DI_var', 0.0) < 0]
        alinhamento_maximo = max(sum(1 for x in direcoes if x), 8 - sum(1 for x in direcoes if x))
        taxa_alinhamento = (alinhamento_maximo / 8) * 100

        forca_norm = max(0.0, min(abs(score_suavizado) / 1.8, 1.0))
        nota_confianca = round(forca_norm * 7 + (taxa_alinhamento / 100) * 3)
        
        if score_suavizado > 0.10:
            prob_compra = round(forca_norm * 60 + (taxa_alinhamento * 0.4))
            prob_venda = round((100 - prob_compra) * 0.3)
        elif score_suavizado < -0.10:
            prob_venda = round(forca_norm * 60 + (taxa_alinhamento * 0.4))
            prob_compra = round((100 - prob_venda) * 0.3)
        else:
            prob_compra = prob_venda = round((100 - round(80 - (forca_norm * 40))) / 2)
        prob_neutro = 100 - prob_compra - prob_venda

        if score_suavizado > 0.12 and nota_confianca >= 7:
            indicacao, cor = "COMPRA FORTE 🔥", "#00E676"
        elif score_suavizado > 0.12:
            indicacao, cor = "COMPRA MODERADA 🟢", "#AEEA00"
        elif score_suavizado < -0.12 and nota_confianca >= 7:
            indicacao, cor = "VENDA FORTE 🚨", "#FF1744"
        elif score_suavizado < -0.12:
            indicacao, cor = "VENDA MODERADA 🟠", "#FF9100"
        else:
            indicacao, cor = "AGUARDE / MERCADO LATERAL ⚖️", "#FFB300"

        return {
            'indicacao': indicacao, 'cor': cor, 'nota': nota_confianca,
            'compra': prob_compra, 'venda': prob_venda, 'neutro': prob_neutro,
            'alinhamento': f"{taxa_alinhamento:.0f}% ({alinhamento_maximo}/8 ativos)",
            'tendencia_win': sit_tendencia, 'volume_win': sit_volume,
            'vix_atual': vix_atual, 'alerta_vix': alerta_vix,
            'local': media_ponderada_local, 'global': media_ponderada_global
        }

# --- INTERFACE STREAMLIT ---
st.title("🖥️ SCANNER AUTOMÁTICO")
st.subheader("@leandro9.1")
st.caption("Painel de Direção Macro WIN - Versão Mobile/Web")

if datetime.now() > datetime.strptime(DATA_EXPIRACAO, "%Y-%m-%d"):
    st.error("Esta cópia do aplicativo expirou.")
else:
    senha = st.text_input("🔑 Insira a Chave de Acesso:", type="password")
    if senha == SENHA_CORRETA:
        st.success("Acesso Liberado com sucesso!")
        
        engine = MacroQuantWebEngine()
        with st.spinner("Realizando varredura e calibração de pesos macro..."):
            try:
                dados = engine.obter_dados_mercado()
                res = engine.calcular_direcao_ponderada(dados)
                
                # Exibição do Alerta Principal
                st.markdown(f"<div style='background-color:{res['cor']}; padding:15px; border-radius:8px; text-align:center;'><h2 style='color:black; margin:0;'>{res['indicacao']}</h2><p style='color:black; margin:5px 0 0 0;'>Nota de Confiança: {res['nota']}/10</p></div>", unsafe_allow_html=True)
                
                # Métricas em Colunas
                st.write("")
                col1, col2, col3 = st.columns(3)
                col1.metric("🟢 Chance Compra", f"{res['compra']}%")
                col2.metric("🔴 Chance Venda", f"{res['venda']}%")
                col3.metric("🟡 Neutro", f"{res['neutro']}%")
                
                st.subheader("🛡️ Análise de Filtros Ponderados")
                st.text(f"• Alinhamento Operacional: {res['alinhamento']}")
                st.text(f"• Tendência WIN (Preço)   : {res['tendencia_win']}")
                st.text(f"• Volatilidade VIX        : {res['vix_atual']:.2f} ({res['alerta_vix']})")
                st.text(f"• Volume WIN              : {res['volume_win']}")
                
                st.subheader("📊 Médias Macrodirecionais")
                st.metric("Retorno Bloco Nacional (B3)", f"{res['local']:+.2f}%")
                st.metric("Retorno Bloco Global (EUA/Commodities)", f"{res['global']:+.2f}%")
                
                if st.button("🔄 Atualizar Dados"):
                    st.rerun()
            except Exception as e:
                st.error(f"Erro no processamento quântico: {e}")
    elif senha != "":
        st.error("Chave de acesso incorreta!")