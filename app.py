import tkinter as tk
from tkinter import messagebox, ttk
import yfinance as yf
from datetime import datetime, time
import requests  
import math

# =====================================================================
# 🔒 CONFIGURAÇÕES DE SEGURANÇA E PARÂMETROS DE TELEGRAM
# =====================================================================
SENHA_CORRETA = "WIN2026"
DATA_EXPIRACAO = "2026-12-30"

TELEGRAM_TOKEN = "7977057617:AAFC1HzeIZIt-WSl19OwcKY4iNjUx6l9Nic"
TELEGRAM_CHAT_ID = "1052417563"
# =====================================================================

class MacroQuantEngine:
    def __init__(self):
        self.PESOS_BASE_LOCAIS = {
            'VALE3.SA': 0.15, 'PETR4.SA': 0.065, 'PETR3.SA': 0.065,
            'ITUB4.SA': 0.07, 'BBDC4.SA': 0.05, 'BBAS3.SA': 0.05, 'SANB11.SA': 0.05
        }
        
        self.PESOS_BASE_GLOBAIS = {
            'SP_VISTA': 0.15, 'SP_FUTURO': 0.10, 'NASDAQ': 0.10,     
            'MINERIO': 0.08, 'BRENT': 0.07       
        }
        
        self.historico_scores = []
        self.alfa_ema = 0.35  
        
        self.ultimo_envio_telegram = 0
        self.ultimo_sinal_enviado = ""

    def enviar_alerta_telegram(self, mensagem: str):
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
            requests.post(url, json=payload, timeout=10)
        except Exception as e:
            print(f"Erro ao enviar Telegram: {e}")

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

        # 4. Solução Proxy Segura para Juros Futuros (DI) via FIXA11
        try:
            obj_di = yf.Ticker('FIXA11.SA')
            df_di = obj_di.history(period="5d").dropna(subset=['Close'])
            if len(df_di) >= 2:
                var_fixa = ((df_di['Close'].iloc[-1] - df_di['Close'].iloc[-2]) / df_di['Close'].iloc[-2]) * 100
                var_di = -var_fixa 
                dados_retorno['DI_var'] = 0.0 if (math.isnan(var_di) or math.isinf(var_di)) else var_di
            else:
                dados_retorno['DI_var'] = 0.0
        except:
            dados_retorno['DI_var'] = 0.0

        # 5. Filtro de Tendência & Volume via IBOV
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

    def calcular_regime_vix(self, dados: dict) -> tuple:
        vix_atual = dados.get('VIX_atual', 0.0)
        if vix_atual < 18.0:
            return "Normal", "✅ Fluxo normal para operações (Lote Cheio).", 1.0
        elif 18.0 <= vix_atual <= 22.0:
            return "Moderado", "⚠️ Volatilidade subindo. Alongue stops.", 0.85
        else:
            return "Estressado", "🚨 ALERTA: VIX Elevado! Reduzir lote!", 0.50

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

        var_dxy = dados.get('DXY_var', 0.0)
        var_wdo = dados.get('WDO_var', 0.0)
        score_dolar = (var_dxy * 0.40) + (var_wdo * 0.60)
        score_base += (-score_dolar * 0.25)

        var_di = dados.get('DI_var', 0.0)
        score_base += (-var_di * 0.30)

        ema9 = dados.get('WIN_EMA9', 0.0)
        ema21 = dados.get('WIN_EMA21', 0.0)
        reforco_tendencia = 0.0
        
        if ema9 > ema21 and ema21 > 0:
            sit_tendencia = "ALTA (EMA9 > EMA21)"
            reforco_tendencia = 0.15
        elif ema9 < ema21 and ema21 > 0:
            sit_tendencia = "BAIXA (EMA9 < EMA21)"
            reforco_tendencia = -0.15
        else:
            sit_tendencia = "LATERALIZADA"
            
        score_base += reforco_tendencia

        vol_atual = dados.get('WIN_vol_atual', 1.0)
        vol_medio = dados.get('WIN_vol_medio', 1.0)
        multiplicador_volume = 1.0
        
        if vol_atual > vol_medio and vol_medio > 1.0:
            sit_volume = "ACIMA DA MÉDIA (CONFIRMA)"
            multiplicador_volume = 1.20
        else:
            sit_volume = "ABAIXO DA MÉDIA (FRACO)"
            multiplicador_volume = 0.80

        score_base *= multiplicador_volume
        score_suavizado = self._aplicar_suavizacao_ema(score_base)

        regime_vix, alerta_vix, redutor_compra = self.calcular_regime_vix(dados)
        if score_suavizado > 0:
            score_suavizado *= redutor_compra
            
        if (score_suavizado > 0 and ema9 < ema21 and ema21 > 0) or (score_suavizado < 0 and ema9 > ema21 and ema21 > 0):
            score_suavizado *= 0.60

        direcoes = [
            var_vale > 0, var_petr > 0, var_ifnc > 0,
            dados.get('SP_FUTURO_var', 0.0) > 0, dados.get('NASDAQ_var', 0.0) > 0,
            dados.get('BRENT_var', 0.0) > 0, score_dolar < 0, var_di < 0
        ]
        total_comprados = sum(1 for x in direcoes if x)
        total_vendedores = 8 - total_comprados
        alinhamento_maximo = max(total_comprados, total_vendedores)
        taxa_alinhamento = (alinhamento_maximo / 8) * 100

        forca_norm = max(0.0, min(abs(score_suavizado) / 1.8, 1.0))
        nota_confianca = round(forca_norm * 7 + (taxa_alinhamento / 100) * 3)
        
        if score_suavizado > 0.10:
            prob_compra = round(forca_norm * 60 + (taxa_alinhamento * 0.4))
            prob_venda = round((100 - prob_compra) * 0.3)
            prob_neutro = 100 - prob_compra - prob_venda
        elif score_suavizado < -0.10:
            prob_venda = round(forca_norm * 60 + (taxa_alinhamento * 0.4))
            prob_compra = round((100 - prob_venda) * 0.3)
            prob_neutro = 100 - prob_venda - prob_compra
        else:
            prob_neutro = round(80 - (forca_norm * 40))
            prob_compra = round((100 - prob_neutro) / 2)
            prob_venda = 100 - prob_neutro - prob_compra

        if nota_confianca <= 3:
            conviccao_status = "BAIXA CONVICÇÃO ░"
        elif 4 <= nota_confianca <= 5:
            conviccao_status = "MÉDIA CONVICÇÃO ▒"
        elif 6 <= nota_confianca <= 7:
            conviccao_status = "ALTA CONVICÇÃO ▓"
        else:
            conviccao_status = "CONVICÇÃO EXTREMA 🔥"

        if score_suavizado > 0.12 and nota_confianca >= 7:
            indicacao = f" [ COMPRA FORTE: {nota_confianca}/10 ] "
            cor_fundo, cor_texto = "#00E676", "#000000"
        elif score_suavizado > 0.12:
            indicacao = f" [ COMPRA MODERADA: {nota_confianca}/10 ] "
            cor_fundo, cor_texto = "#AEEA00", "#000000"
        elif score_suavizado < -0.12 and nota_confianca >= 7:
            indicacao = f" [ VENDA FORTE: {nota_confianca}/10 ] "
            cor_fundo, cor_texto = "#FF1744", "#FFFFFF"
        elif score_suavizado < -0.12:
            indicacao = f" [ VENDA MODERADA: {nota_confianca}/10 ] "
            cor_fundo, cor_texto = "#FF9100", "#000000"
        else:
            indicacao = " [ AGUARDE / MERCADO LATERAL ] "
            cor_fundo, cor_texto = "#FFB300", "#000000"

        dict_probabilidades = {'compra': prob_compra, 'venda': prob_venda, 'neutro': prob_neutro, 'nota': nota_confianca, 'conviccao': conviccao_status}
        
        sit_dolar = "ALTA 🔺" if score_dolar > 0.1 else ("BAIXA 🔻" if score_dolar < -0.1 else "ESTÁVEL ⚖️")
        sit_juros = "ALTA 🔺" if var_di > 0.1 else ("BAIXA 🔻" if var_di < -0.1 else "ESTÁVEL ⚖️")
        
        texto_alinhamento = f"{taxa_alinhamento:.0f}% ({alinhamento_maximo}/8 ativos)"
        diagnostico_blocos = {
            'tendencia_win': sit_tendencia, 'volume_win': sit_volume,
            'situacao_dolar': sit_dolar, 'situacao_juros': sit_juros,
            'alinhamento': texto_alinhamento
        }

        self.processar_disparos_telegram(indicacao, score_suavizado, media_ponderada_local, media_ponderada_global, dados, regime_vix, dict_probabilidades, diagnostico_blocos)

        return {
            'indicacao': indicacao, 'score_final': score_suavizado,
            'local_ponderado': media_ponderada_local, 'global_ponderado': media_ponderada_global,
            'regime_vix': regime_vix, 'alerta_vix': alerta_vix,
            'cor_fundo': cor_fundo, 'cor_texto': cor_texto,
            'horario_ny_ativo': self.verificar_horario_sp500(),
            'probs': dict_probabilidades, 'diagnosticos': diagnostico_blocos
        }

    def _aplicar_suavizacao_ema(self, novo_score: float) -> float:
        if not self.historico_scores:
            self.historico_scores.append(novo_score)
            return novo_score
        nova_ema = (novo_score * self.alfa_ema) + (self.historico_scores[-1] * (1 - self.alfa_ema))
        self.historico_scores.append(nova_ema)
        if len(self.historico_scores) > 10: self.historico_scores.pop(0)
        return nova_ema

    def processar_disparos_telegram(self, indicacao: str, score: float, local_p: float, global_p: float, dados: dict, regime_vix: str, probs: dict, diag: dict):
        agora = datetime.now().timestamp()
        mudou_sinal = (indicacao != self.ultimo_sinal_enviado) and (self.ultimo_sinal_enviado != "")
        tempo_esgotado = (agora - self.ultimo_envio_telegram >= 300) or (self.ultimo_envio_telegram == 0)

        if mudou_sinal or tempo_esgotado:
            status_envio = "⚡ GATILHO SNIPER ATIVO" if mudou_sinal else "📊 ATUALIZAÇÃO CONTEXTUAL"
            
            mensagem = (
                f"*{status_envio} - *\n"
                f"⏱️ {datetime.now().strftime('%H:%M:%S')}\n\n"
                f"🎯 *SINAL:* `{indicacao.strip()}`\n"
                f"🔥 *CONVICÇÃO:* `{probs['conviccao']}`\n\n"
                f"📊 *PROBABILIDADES DO MODELO:*\n"
                f"🟢 Compra  : `{probs['compra']}%`\n"
                f"🔴 Venda   : `{probs['venda']}%`\n"
                f"🟡 Neutro  : `{probs['neutro']}%`\n"
                f"🏆 *Nota de Confiança:* `{probs['nota']}/10`\n\n"
                f"🛡️ *ANÁLISE DE ALINHAMENTO E FILTROS:*\n"
                f"• Alinhamento Operacional: `{diag['alinhamento']}`\n"
                f"• Tendência do Preço WIN: `{diag['tendencia_win']}`\n"
                f"• Pressão do Dólar (Cambial): `{diag['situacao_dolar']}`\n"
                f"• Curva de Juros Futuros DI: `{diag['situacao_juros']}`\n"
                f"• Volume Negociado WIN: `{diag['volume_win']}`\n\n"
                f"🔬 *Métricas Rápidas:* VIX: `{dados.get('VIX_atual', 0.0):.2f}` | Retorno B3: `{local_p:+.2f}%`"
            )
            self.enviar_alerta_telegram(mensagem)
            self.ultimo_envio_telegram = agora
            self.ultimo_sinal_enviado = indicacao


engine = MacroQuantEngine()

# =====================================================================
# INTERFACE GRÁFICA (TKINTER) - REVISADA E REDESENHADA PARA ESTABILIDADE
# =====================================================================

def verificar_seguranca():
    if datetime.now() > datetime.strptime(DATA_EXPIRACAO, "%Y-%m-%d"):
        messagebox.showerror("Licença Expirada", "Esta cópia expirou.")
        root.destroy()
        return False
    if entry_senha.get() != SENHA_CORRETA:
        messagebox.showerror("Acesso Negado", "Chave Incorreta!")
        return False
    return True

def rodar_monitoramento_global():
    if verificar_seguranca():
        engine.ultimo_envio_telegram = 0
        analisar_tudo()

def analisar_tudo():
    label_status.config(text="Executando varredura e calibração de pesos quânticos...", fg="#FFB300")
    root.update()
    
    try:
        dados = engine.obter_dados_mercado()
        res = engine.calcular_direcao_ponderada(dados)
        
        score_limitado = max(-2.0, min(res['score_final'], 2.0))
        porcentagem_forca = (abs(score_limitado) / 2.0) * 100
        
        total_blocos = 20
        blocos_pr = int((porcentagem_forca / 100) * total_blocos)
        grafico_barra = ("█" * blocos_pr) + ("░" * (total_blocos - blocos_pr))
        if "MERCADO LATERAL" in res['indicacao'] and porcentagem_forca < 10.0:
            grafico_barra = "░" * total_blocos
            porcentagem_forca = 0.0

        txt.delete(1.0, tk.END)
        txt.insert(tk.END, f"=========================================================\n")
        txt.insert(tk.END, f"       SCANNER DE TENDENCIA     \n")
        txt.insert(tk.END, f"=========================================================\n")
        txt.insert(tk.END, f" ÚLTIMA ATUALIZAÇÃO: {datetime.now().strftime('%H:%M:%S')}\n")
        txt.insert(tk.END, f" CONVICÇÃO DO MODELO: {res['probs']['conviccao']} (Nota: {res['probs']['nota']}/10)\n")
        txt.insert(tk.END, f" ALERTA DA VOLATILIDADE: {res['alerta_vix']}\n")
        txt.insert(tk.END, f"---------------------------------------------------------\n")
        txt.insert(tk.END, f" INDICAÇÃO ATUAL:  ")
        
        p_i_s = txt.index(tk.INSERT)
        txt.insert(tk.END, f"{res['indicacao']}")
        p_f_s = txt.index(tk.INSERT)
        
        txt.insert(tk.END, f"\n\n 📊 NOVA PROBABILIDADE E CLASSIFICAÇÃO QUANT:\n")
        txt.insert(tk.END, f"    🟢 Probabilidade Compra: {res['probs']['compra']}%\n")
        txt.insert(tk.END, f"    🔴 Probabilidade Venda : {res['probs']['venda']}%\n")
        txt.insert(tk.END, f"    🟡 Probabilidade Neutro: {res['probs']['neutro']}%\n")
        txt.insert(tk.END, f"    🎯 Alinhamento Ativos  : {res['diagnosticos']['alinhamento']}\n")
        
        txt.insert(tk.END, f"---------------------------------------------------------\n")
        txt.insert(tk.END, f" ⚡ TERMÔMETRO DE FORÇA INTEGRADA: [{grafico_barra}] {porcentagem_forca:.1f}%\n")
        txt.insert(tk.END, f"---------------------------------------------------------\n")
        txt.insert(tk.END, f" DIAGNÓSTICO DOS FILTROS OPERACIONAIS RECENTES:\n")
        txt.insert(tk.END, f"    • Tendência de Médias WIN : {res['diagnosticos']['tendencia_win']}\n")
        txt.insert(tk.END, f"    • Volume Financeiro WIN   : {res['diagnosticos']['volume_win']}\n")
        txt.insert(tk.END, f"    • Situação do Complexo USD: {res['diagnosticos']['situacao_dolar']}\n")
        txt.insert(tk.END, f"    • Curva Futura Juros (DI) : {res['diagnosticos']['situacao_juros']}\n")
        txt.insert(tk.END, f"---------------------------------------------------------\n")
        
        def inserir_ativo_colorido(tk_text, label, valor, eh_inverso=False):
            cor = ("#FF1744" if valor >= 0 else "#00E676") if eh_inverso else ("#00E676" if valor >= 0 else "#FF1744")
            tk_text.insert(tk_text.index(tk.INSERT), f"   • {label}: ")
            p_i = tk_text.index(tk.INSERT)
            tk_text.insert(tk_text.index(tk.INSERT), f"{valor:+.2f}%")
            p_f = tk_text.index(tk.INSERT)
            txt.insert(tk.END, f"\n")
            tag_n = f"cor_{label.split()[0]}"
            tk_text.tag_add(tag_n, p_i, p_f)
            tk_text.tag_config(tag_n, foreground=cor, font=("Courier New", 10, "bold"))

        txt.insert(tk.END, f"   MERCADOS CORE (BRASIL & GLOBAIS):\n")
        inserir_ativo_colorido(txt, "VALE3 (Ajuste Dinâmico)", dados.get('VALE3.SA', 0.0))
        inserir_ativo_colorido(txt, "PETR4 (Ajuste Dinâmico)", dados.get('PETR4.SA', 0.0))
        inserir_ativo_colorido(txt, "ITUB4 (Setor Bancário)", dados.get('ITUB4.SA', 0.0))
        inserir_ativo_colorido(txt, "S&P 500 Futuro", dados.get('SP_FUTURO_var', 0.0))
        inserir_ativo_colorido(txt, "Dólar Comercial (WDO)", dados.get('WDO_var', 0.0), eh_inverso=True)
        inserir_ativo_colorido(txt, "Juros Estruturados (DI)", dados.get('DI_var', 0.0), eh_inverso=True)
        
        # -----------------------------------------------------------------
        # MONITOR DE PROTEÇÃO DO VIX NO RODAPÉ - EXCLUSIVO VISUAL
        # -----------------------------------------------------------------
        txt.insert(tk.END, f"---------------------------------------------------------\n")
        txt.insert(tk.END, f" MONITOR DE PROTEÇÃO (Informativo):\n")
        
        vix_var = dados.get('VIX_var', 0.0)
        if vix_var >= 0:
            texto_vix = f"   • VIX (Índice do Medo): {vix_var:+.2f}% [ BOM PARA VENDA ÍNDICE ]"
            cor_vix = "#00E676"  # Verde se positivo
        else:
            texto_vix = f"   • VIX (Índice do Medo): {vix_var:+.2f}% [ BOM PARA COMPRA ÍNDICE ]"
            cor_vix = "#FF1744"  # Vermelho se negativo
            
        p_i_vix = txt.index(tk.INSERT)
        txt.insert(tk.END, texto_vix)
        p_f_vix = txt.index(tk.INSERT)
        txt.insert(tk.END, f"\n")
        
        txt.tag_add("vix_ativo", p_i_vix, p_f_vix)
        txt.tag_config("vix_ativo", foreground=cor_vix, font=("Courier New", 10, "bold"))
        # -----------------------------------------------------------------
        
        txt.insert(tk.END, f"=========================================================\n")
        
        txt.tag_add("sinal", p_i_s, p_f_s)
        txt.tag_config("sinal", background=res['cor_fundo'], foreground=res['cor_texto'], font=("Courier New", 11, "bold"))

        # ABA 2
        txt_b3.delete(1.0, tk.END)
        txt_b3.insert(tk.END, f"=========================================================\n")
        txt_b3.insert(tk.END, f"            RESUMO DE MÉDIAS DE BLOCOS QUANT V5         \n")
        txt_b3.insert(tk.END, f"=========================================================\n\n")
        
        cor_l = "#00E676" if res['local_ponderado'] >= 0 else "#FF1744"
        txt_b3.insert(tk.END, f" 📊 BLOCO NACIONAL PONDERADO AJUSTADO (B3):\n")
        p_il = txt_b3.index(tk.INSERT)
        txt_b3.insert(tk.END, f"    • Retorno Médio Dinâmico: {res['local_ponderado']:+.2f}%\n")
        p_fl = txt_b3.index(tk.INSERT)
        
        cor_g = "#00E676" if res['global_ponderado'] >= 0 else "#FF1744"
        txt_b3.insert(tk.END, f"\n 🌎 BLOCO EXTERNO PONDERADO (GLOBAL):\n")
        p_ig = txt_b3.index(tk.INSERT)
        txt_b3.insert(tk.END, f"    • Retorno Médio Global:   {res['global_ponderado']:+.2f}%\n")
        p_fg = txt_b3.index(tk.INSERT)
        txt_b3.insert(tk.END, f"\n=========================================================\n")
        
        txt_b3.tag_add("cor_l", p_il, p_fl)
        txt_b3.tag_config("cor_l", foreground=cor_l, font=("Courier New", 11, "bold"))
        txt_b3.tag_add("cor_g", p_ig, p_fg)
        txt_b3.tag_config("cor_g", foreground=cor_g, font=("Courier New", 11, "bold"))

        label_status.config(text="⏱️ Scanner monitorando em tempo real (30s)...", fg="#00E676")
    except Exception as e:
        label_status.config(text=f"Erro no processamento gráfico: {str(e)}", fg="#FF1744")
        
    root.after(30000, analisar_tudo)

# =====================================================================
# LAYOUT DE INTERFACE GRÁFICA DARK MODE
# =====================================================================
COR_FUNDO_JANELA, COR_FUNDO_CAIXA, COR_TEXTO_PADRAO = "#121212", "#1E1E1E", "#E0E0E0"

root = tk.Tk()
root.title("Painel Master WIN - Engine Quant V5")
root.geometry("600x870") # Redimensionado estrategicamente para evitar rolagem
root.configure(bg=COR_FUNDO_JANELA)

estilo = ttk.Style()
estilo.theme_use('default')
estilo.configure('TNotebook', background=COR_FUNDO_JANELA, borderwidth=0)
estilo.configure('TNotebook.Tab', background="#2C2C2C", foreground="white", font=("Arial", 9, "bold"), padding=[10, 4])
estilo.map('TNotebook.Tab', background=[('selected', COR_FUNDO_CAIXA)], foreground=[('selected', "#00B0FF")])

tk.Label(root, text="SCANNER DE TENDENCIA @leandro9.1", font=("Arial", 11, "bold"), fg="#00B0FF", bg=COR_FUNDO_JANELA).pack(pady=5)

f_senha = tk.Frame(root, bg=COR_FUNDO_JANELA)
f_senha.pack(pady=5)
tk.Label(f_senha, text="🔑 Chave de Acesso:", font=("Arial", 9, "bold"), fg=COR_TEXTO_PADRAO, bg=COR_FUNDO_JANELA).pack(side=tk.LEFT, padx=5)
entry_senha = tk.Entry(f_senha, font=("Arial", 9), width=15, show="*", bg=COR_FUNDO_CAIXA, fg="white", insertbackground="white")
entry_senha.pack(side=tk.LEFT, padx=5)

btn = tk.Button(root, text="📥 INICIAR MONITORAMENTO ", font=("Arial", 10, "bold"), bg="#0D47A1", fg="white", command=rodar_monitoramento_global, height=2, width=35, bd=0, cursor="hand2")
btn.pack(pady=5)

label_status = tk.Label(root, text="Insira a chave para liberar o sistema...", font=("Arial", 9, "italic"), fg="#9E9E9E", bg=COR_FUNDO_JANELA)
label_status.pack(pady=2)

notebook = ttk.Notebook(root)
notebook.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)

aba_global = tk.Frame(notebook, bg=COR_FUNDO_JANELA)
notebook.add(aba_global, text="  Mundo (Macro Global V5)  ")
txt = tk.Text(aba_global, font=("Courier New", 10), width=70, height=32, bg=COR_FUNDO_CAIXA, fg=COR_TEXTO_PADRAO, bd=0, relief=tk.FLAT)
txt.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

aba_b3 = tk.Frame(notebook, bg=COR_FUNDO_JANELA)
notebook.add(aba_b3, text="  Resumo de Pesos Dinâmicos  ")
txt_b3 = tk.Text(aba_b3, font=("Courier New", 10), width=70, height=32, bg=COR_FUNDO_CAIXA, fg=COR_TEXTO_PADRAO, bd=0, relief=tk.FLAT)
txt_b3.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

root.mainloop()