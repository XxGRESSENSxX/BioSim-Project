import streamlit as st
import google.generativeai as genai
import pandas as pd
import numpy as np
import time
import re

# --- 1. CONFIGURAÇÃO OCULTA ---
CHAVE_GEMINI = st.secrets.get("CHAVE_GEMINI", "")
if CHAVE_GEMINI:
    genai.configure(api_key=CHAVE_GEMINI)
    model = genai.GenerativeModel('gemini-2.0-flash') 
else:
    st.error("Erro de Sistema: Licença não encontrada.")
    st.stop()

st.set_page_config(page_title="BioSim Professional", layout="wide", initial_sidebar_state="expanded")

# --- 2. ESTADO DO SISTEMA ---
if 'sinais' not in st.session_state:
    st.session_state.sinais = {"fc": 75, "sp": 98, "resp": 16, "pam": 90}
if 'ultimo_laudo' not in st.session_state:
    st.session_state.ultimo_laudo = ""

# --- 3. DESIGN PROFISSIONAL (CSS) ---
st.markdown('''
    <style>
    .main { background-color: #05070A; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #0F172A; border-right: 1px solid #1E293B; }
    .biosim-title { font-size: 42px; font-weight: 800; color: #F8FAFC; font-family: sans-serif; }
    .monitor-panel { background-color: #000000; padding: 20px; border-radius: 10px; border: 1px solid #1E293B; }
    .metric-box { margin-bottom: 20px; text-align: right; }
    .metric-label { font-size: 12px; font-weight: bold; text-transform: uppercase; }
    .metric-value { font-size: 55px; font-weight: bold; font-family: 'Courier New', monospace; line-height: 1; }
    .report-box { background-color: #0B1120; padding: 25px; border: 1px solid #1E293B; border-radius: 8px; color: #CBD5E1; }
    .stButton>button { background-color: #2563EB; color: white; font-weight: bold; width: 100%; height: 3.5em; border: none; }
    </style>
''', unsafe_allow_html=True)

# --- 4. SIDEBAR COMPLETA ---
with st.sidebar:
    st.markdown('<div class="biosim-title">BioSim</div>', unsafe_allow_html=True)
    st.markdown('<p style="color: #64748B; margin-top: -10px;">Clinical Simulation Suite</p>', unsafe_allow_html=True)
    
    with st.expander("👤 PERFIL DO PACIENTE", expanded=True):
        sexo = st.selectbox("Sexo", ["Feminino", "Masculino"])
        idade = st.number_input("Idade", 1, 110, 24)
        c1, c2 = st.columns(2)
        peso = c1.number_input("Peso (kg)", 1.0, 300.0, 65.0)
        altura = c2.number_input("Altura (m)", 0.5, 2.5, 1.70)
        gordura = st.slider("Gordura (%)", 5, 50, 22)
        massa = st.slider("Massa Magra (%)", 10, 90, 40)
    
    st.divider()
    st.markdown("### 📋 HISTÓRICO E ESTILO")
    estilo = st.text_input("Estilo de Vida:", placeholder="Ex: Sedentário, Atleta...")
    patologias = st.text_input("Comorbidades:", placeholder="Ex: Diabetes, ICC...")

# --- 5. LAYOUT DO MONITOR ---
col_ondas, col_numeros = st.columns([2.5, 1])
with col_ondas:
    st.markdown("### Telemetria Multiparamétrica")
    plot_spot = st.empty() 
with col_numeros:
    metrics_spot = st.empty()

st.divider()

# --- 6. SIMULAÇÃO ---
st.subheader("🧪 Administração de Fármacos / Estímulos")
c_in, c_bt = st.columns([4, 1])
intervencao = c_in.text_input("Inserir Intervenção:", placeholder="Ex: Adrenalina 2mg IV")
btn_simular = c_bt.button("PROCESSAR SIMULAÇÃO")
laudo_area = st.empty()

# --- 7. MOTOR DE DADOS ---
def extrair_parametros(texto):
    padrao = r"\[FC:(\d+), RESP:(\d+), PAM:(\d+), SPO2:(\d+)\]"
    busca = re.search(padrao, texto)
    if busca:
        return {"fc": int(busca.group(1)), "resp": int(busca.group(2)), "pam": int(busca.group(3)), "sp": int(busca.group(4))}
    return None

def rodar_simulacao():
    t_base = 0
    while True:
        t_base += 0.05
        t = np.linspace(t_base, t_base + 5, 100)
        
        # Processamento da Resposta
        if btn_simular and intervencao:
            if "last_int" not in st.session_state or st.session_state.last_int != intervencao:
                with laudo_area:
                    with st.spinner("Analisando Resposta Hemodinâmica..."):
                        p = f"Simulação Clínica: {sexo}, {idade}a, {peso}kg, {altura}m. Estilo: {estilo}. Patologia: {patologias}. Intervenção: {intervencao}. Descreva a evolução do quadro e termine com: [FC:X, RESP:Y, PAM:Z, SPO2:W]"
                        res = model.generate_content(p)
                        st.session_state.ultimo_laudo = res.text
                        novos = extrair_parametros(res.text)
                        if novos: st.session_state.sinais.update(novos)
                        st.session_state.last_int = intervencao

        if st.session_state.ultimo_laudo:
            laudo_area.markdown(f'<div class="report-box">{st.session_state.ultimo_laudo}</div>', unsafe_allow_html=True)

        # Gerenciamento de Ondas
        fc = st.session_state.sinais['fc']
        if fc > 0:
            onda_ecg = np.sin(t * (fc/10)) + np.random.normal(0, 0.02, 100)
            onda_resp = np.sin(t * (st.session_state.sinais['resp']/20)) * 0.4 + 1
        else:
            onda_ecg = np.zeros(100) + np.random.normal(0, 0.005, 100)
            onda_resp = np.zeros(100) + 1

        df_ondas = pd.DataFrame({'ECG': onda_ecg, 'RESP': onda_resp}).set_index(t)
        plot_spot.line_chart(df_ondas, color=["#00FF00", "#FFFF00"], height=400)

        # Atualização do Painel Numérico
        metrics_spot.markdown(f'''
            <div class="monitor-panel">
                <div class="metric-box" style="color:#00FF00;"><div class="metric-label">FC (bpm)</div><div class="metric-value">{"--" if fc==0 else fc}</div></div>
                <div class="metric-box" style="color:#FFFF00;"><div class="metric-label">RESP (mpm)</div><div class="metric-value">{st.session_state.sinais['resp']}</div></div>
                <div class="metric-box" style="color:#FFFFFF;"><div class="metric-label">PAM (mmHg)</div><div class="metric-value" style="font-size:40px;">{st.session_state.sinais['pam']}</div></div>
                <div class="metric-box" style="color:#00FFFF;"><div class="metric-label">SpO2 (%)</div><div class="metric-value" style="font-size:40px;">{st.session_state.sinais['sp']}</div></div>
            </div>
        ''', unsafe_allow_html=True)
        time.sleep(0.3)

rodar_simulacao()
