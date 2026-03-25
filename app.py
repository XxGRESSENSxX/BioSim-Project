import streamlit as st
import google.generativeai as genai
import pandas as pd
import numpy as np
import time

# Configurações iniciais
genai.configure(api_key="AIzaSyC9Sp2IitOOH5fxWFEQP6OYCC6pefv0EhY")
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="BioSim Pro", layout="wide", initial_sidebar_state="expanded")

# --- CSS para Estética de Monitor Real ---
st.markdown('''
    <style>
    .main { background-color: #05070A; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #0F172A; }
    
    .biosim-title { font-size: 48px; font-weight: 800; color: #F8FAFC; margin-bottom: 20px; }
    
    .monitor-panel { 
        background-color: #000000; 
        padding: 15px; 
        border-radius: 8px; 
        border: 1px solid #1E293B; 
        display: flex; 
        flex-direction: column; 
        justify-content: space-around;
        height: 450px;
    }
    .metric-group { text-align: right; line-height: 1; }
    .metric-label { font-size: 12px; font-weight: bold; }
    .metric-value { font-size: 60px; font-weight: bold; font-family: monospace; }
    </style>
''', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown('<div class="biosim-title">BioSim</div>', unsafe_allow_html=True)
    st.subheader("👤 Perfil do Paciente")
    sexo = st.selectbox("Sexo", ["Feminino", "Masculino"])
    idade = st.number_input("Idade", 18, 100, 24)
    peso = st.number_input("Massa (kg)", value=65.0)
    
    st.divider()
    intervencao = st.text_input("💉 Intervenção (Fármaco/Estímulo):")
    simular_btn = st.button("Simular Resposta")

# --- ÁREA DO MONITOR (ESTÁTICA) ---
col_grafico, col_numeros = st.columns([3, 1])

with col_grafico:
    st.markdown("### Telemetria Multiparamétrica")
    # Este é o segredo: um placeholder que será limpo e preenchido continuamente
    plot_spot = st.empty()

with col_numeros:
    # Placeholder para os números à direita
    metrics_spot = st.empty()

# Placeholder para o laudo lá embaixo
laudo_spot = st.empty()

# --- LÓGICA DE SIMULAÇÃO EM TEMPO REAL ---
def iniciar_monitor():
    t_base = 0
    impacto = 0
    
    # Se clicar no botão, aumenta o impacto visual temporariamente
    if simular_btn and intervencao:
        impacto = 0.5
        with laudo_spot:
            st.info(f"Analisando resposta biológica para: {intervencao}...")

    # Loop Infinito (O Monitor "Vivo")
    while True:
        t_base += 0.1
        t = np.linspace(t_base, t_base + 5, 100)
        
        # Gerando as curvas
        df = pd.DataFrame({
            'Tempo': t,
            'ECG': np.sin(t * 8) + np.random.normal(0, 0.05, 100),
            'PLET': np.sin(t * 2) * 0.5 + 2,
            'RESP': np.sin(t * 0.8) * 0.3 + 1,
            'PAM': np.sin(t * 8) * 0.2 + 4
        }).set_index('Tempo')

        # 1. Atualiza o Gráfico (sem criar um novo embaixo)
        plot_spot.line_chart(df, color=["#00FF00", "#00FFFF", "#FFFF00", "#FFFFFF"], height=400)

        # 2. Atualiza os Números à direita
        fc = int(75 + (impacto * 30) + np.random.randint(-2, 3))
        spo2 = int(98 - (impacto * 3))
        resp = int(18 + (impacto * 5))
        
        metrics_spot.markdown(f'''
            <div class="monitor-panel">
                <div class="metric-group" style="color: #00FF00;">
                    <div class="metric-label">ECG / FC</div>
                    <div class="metric-value">{fc}</div>
                </div>
                <div class="metric-group" style="color: #00FFFF;">
                    <div class="metric-label">SpO2 %</div>
                    <div class="metric-value">{spo2}</div>
                </div>
                <div class="metric-group" style="color: #FFFF00;">
                    <div class="metric-label">RESP</div>
                    <div class="metric-value">{resp}</div>
                </div>
                <div class="metric-group" style="color: #FFFFFF;">
                    <div class="metric-label">TEMP ºC</div>
                    <div class="metric-value" style="font-size: 35px;">37.2</div>
                </div>
            </div>
        ''', unsafe_allow_html=True)
        
        # Pequena pausa para simular a velocidade do monitor
        time.sleep(0.1)

# Inicia o loop
iniciar_monitor()
