import streamlit as st
import google.generativeai as genai
import pandas as pd
import numpy as np
import time
import re

# --- 1. CONFIGURAÇÃO IA ---
CHAVE_GEMINI = st.secrets.get("CHAVE_GEMINI", "")
if CHAVE_GEMINI:
    genai.configure(api_key=CHAVE_GEMINI)
    model = genai.GenerativeModel('models/gemini-2.5-flash')
else:
    st.error("Chave API não configurada nos Secrets.")
    st.stop()

st.set_page_config(page_title="BioSim Pro", layout="wide", initial_sidebar_state="expanded")

# --- 2. INICIALIZAÇÃO DE ESTADO ---
if 'sinais' not in st.session_state:
    st.session_state.sinais = {"fc": 75, "sp": 98, "resp": 16, "pam": 90}
if 'ultimo_laudo' not in st.session_state:
    st.session_state.ultimo_laudo = ""

# --- 3. DESIGN (CSS RESTAURADO) ---
st.markdown('''
    <style>
    .main { background-color: #05070A; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #0F172A; border-right: 1px solid #1E293B; }
    .biosim-title { font-size: 48px; font-weight: 800; color: #F8FAFC; margin-bottom: -10px; font-family: sans-serif; }
    .monitor-panel { background-color: #000000; padding: 20px; border-radius: 8px; border: 1px solid #1E293B; height: 100%; display: flex; flex-direction: column; justify-content: space-around; }
    .metric-group { text-align: right; }
    .metric-label { font-size: 14px; font-weight: bold; }
    .metric-value { font-size: 65px; font-weight: bold; font-family: 'Courier New', monospace; line-height: 1; }
    .report-box { background-color: #0B1120; padding: 25px; border: 1px solid #1E293B; border-radius: 6px; color: #CBD5E1; font-family: sans-serif; margin-top: 20px; }
    .stButton>button { background-color: #2563EB; color: white; font-weight: bold; height: 3.5em; width: 100%; }
    </style>
''', unsafe_allow_html=True)

# --- 4. SIDEBAR (TODOS OS CAMPOS RESTAURADOS) ---
with st.sidebar:
    st.markdown('<div class="biosim-title">BioSim</div>', unsafe_allow_html=True)
    st.markdown('<p style="color: #64748B; margin-bottom: 30px;">Physiological Simulator v3.8</p>', unsafe_allow_html=True)
    
    st.subheader("👤 Perfil Biológico")
    sexo = st.selectbox("Sexo", ["Feminino", "Masculino"])
    idade = st.number_input("Idade", 1, 110, 24)
    
    c1, c2 = st.columns(2)
    peso = c1.number_input("Massa (kg)", 1.0, 300.0, 65.0)
    altura = c2.number_input("Estatura (m)", 0.5, 2.5, 1.70)
    
    # Sliders restaurados
    gordura = st.slider("Gordura (BF %)", 5, 50, 22)
    massa_magra = st.slider("Massa Magra (%)", 10, 90, 40)
    
    st.divider()
    st.subheader("📋 Histórico Clínico")
    # Campos digitáveis mantidos
    estilo_vida = st.text_input("Estilo de Vida:", placeholder="Ex: Maratonista, fumante...")
    patologias = st.text_input("Patologias / Comorbidades:", placeholder="Ex: ICC, Diabetes...")

# --- 5. LAYOUT DO MONITOR ---
col_ondas, col_numeros = st.columns([2.5, 1])
with col_ondas:
    st.markdown("### Telemetria Multiparamétrica")
    plot_spot = st.empty() 
with col_numeros:
    metrics_spot = st.empty()

st.divider()

# --- 6. INTERVENÇÃO ---
st.subheader("🧪 Simulador de Fisiologia Aplicada")
c_in, c_bt = st.columns([4, 1])
intervencao = c_in.text_input("Dose e Via:", placeholder="Ex: Adrenalina 8mg IV")
btn_simular = c_bt.button("Simular Resposta")
laudo_area = st.empty()

# --- 7. PARSER DE DADOS (IA COMANDA MONITOR) ---
def extrair_sinais(texto):
    padrao = r"\[FC:(\d+), RESP:(\d+), PAM:(\d+), SPO2:(\d+)\]"
    busca = re.search(padrao, texto)
    if busca:
        return {
            "fc": int(busca.group(1)),
            "resp": int(busca.group(2)),
            "pam": int(busca.group(3)),
            "sp": int(busca.group(4))
        }
    return None

# --- 8. LOOP DINÂMICO ---
def rodar_monitor():
    t_base = 0
    while True:
        t_base += 0.05
        t = np.linspace(t_base, t_base + 5, 100)
        
        # LOGICA DA IA
        if btn_simular and intervencao:
            if "last_int" not in st.session_state or st.session_state.last_int != intervencao:
                with laudo_area:
                    with st.spinner("Gemini analisando farmacodinâmica..."):
                        prompt = f"""
                        Paciente {sexo}, {idade} anos, {peso}kg, {altura}m.
                        Gordura: {gordura}%, Massa Magra: {massa_magra}%.
                        Estilo de Vida: {estilo_vida}.
                        Patologias: {patologias}.
                        Intervenção: {intervencao}.
                        
                        1. Descreva os efeitos bioquímicos e hemodinâmicos.
                        2. OBRIGATÓRIO: Termine a resposta com os novos parâmetros:
                        [FC:valor, RESP:valor, PAM:valor, SPO2:valor]
                        """
                        res = model.generate_content(prompt)
                        st.session_state.ultimo_laudo = res.text
                        
                        novos = extrair_sinais(res.text)
                        if novos:
                            st.session_state.sinais.update(novos)
                        st.session_state.last_int = intervencao

        # Exibe o laudo se existir
        if st.session_state.ultimo_laudo:
            laudo_area.markdown(f'<div class="report-box">{st.session_state.ultimo_laudo}</div>', unsafe_allow_html=True)

        # RENDERIZAÇÃO DAS ONDAS
        fc = st.session_state.sinais['fc']
        if fc > 0:
            ecg = np.sin(t * (fc/10)) + np.random.normal(0, 0.02, 100)
            resp_onda = np.sin(t * (st.session_state.sinais['resp']/20)) * 0.4 + 1
        else:
            # ASSISTOLIA
            ecg = np.zeros(100) + np.random.normal(0, 0.005, 100)
            resp_onda = np.zeros(100) + 1

        df = pd.DataFrame({'ECG': ecg, 'RESP': resp_onda}).set_index(t)
        plot_spot.line_chart(df, color=["#00FF00", "#FFFF00"], height=400)

        # MONITOR NUMÉRICO
        metrics_spot.markdown(f'''
            <div class="monitor-panel">
                <div class="metric-group" style="color: #00FF00;"><div class="metric-label">FC (bpm)</div><div class="metric-value">{"00" if fc==0 else fc}</div></div>
                <div class="metric-group" style="color: #FFFF00;"><div class="metric-label">RESP (mpm)</div><div class="metric-value">{st.session_state.sinais['resp']}</div></div>
                <div class="metric-group" style="color: #FFFFFF;"><div class="metric-label">PAM (mmHg)</div><div class="metric-value" style="font-size: 35px;">{st.session_state.sinais['pam']}</div></div>
                <div class="metric-group" style="color: #00FFFF;"><div class="metric-label">SpO2 %</div><div class="metric-value" style="font-size: 35px;">{st.session_state.sinais['sp']}</div></div>
            </div>
        ''', unsafe_allow_html=True)
        
        time.sleep(0.3)

rodar_monitor()
