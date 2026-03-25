import streamlit as st
import google.generativeai as genai
import pandas as pd
import numpy as np  # <--- O ERRO ESTAVA AQUI, ESSA LINHA É VITAL
import time

# --- 1. CONFIGURAÇÕES SEGURAS (SECRETS) ---
try:
    # Ele busca no "cofre" que você acabou de configurar
    if "CHAVE_GEMINI" in st.secrets:
        CHAVE_GEMINI = st.secrets["CHAVE_GEMINI"]
        genai.configure(api_key=CHAVE_GEMINI)
        model = genai.GenerativeModel('models/gemini-1.5-flash')
    else:
        st.error("Chave não encontrada no painel de Secrets.")
        st.stop()
except Exception as e:
    st.error(f"Erro ao carregar a chave: {e}")
    st.stop()

# --- 2. DESIGN (CSS) ---
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

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown('<div class="biosim-title">BioSim</div>', unsafe_allow_html=True)
    st.markdown('<p style="color: #64748B; margin-bottom: 30px;">Physiological Simulator v3.4</p>', unsafe_allow_html=True)
    
    st.subheader("👤 Perfil do Paciente")
    sexo = st.selectbox("Sexo", ["Feminino", "Masculino"])
    idade = st.number_input("Idade", 18, 100, 24)
    
    c1, c2 = st.columns(2)
    peso = c1.number_input("Massa (kg)", value=65.0)
    altura = c2.number_input("Estatura (m)", value=1.70)
    
    st.divider()
    estilo = st.multiselect("Estilo de Vida", ["Sedentário", "Ativo", "Atleta", "Tabagista"])
    condicao = st.selectbox("Patologia", ["Nenhuma", "Diabetes", "HAS Estágio II", "Tiroide"])

# --- 4. LAYOUT DO MONITOR ---
col_ondas, col_numeros = st.columns([2.5, 1])
with col_ondas:
    st.markdown("### Telemetria Multiparamétrica")
    plot_spot = st.empty() 
with col_numeros:
    metrics_spot = st.empty()
st.divider()

# --- 5. INTERVENÇÃO ---
st.subheader("🧪 Simulador de Fisiologia Aplicada")
c_in, c_bt = st.columns([4, 1])
intervencao = c_in.text_input("Inserir Fármaco ou Estímulo:", placeholder="Ex: Adrenalina 2mg IV")
btn_simular = c_bt.button("Simular Resposta")
laudo_area = st.empty()

# --- 6. FUNÇÃO DO MONITOR ---
def rodar_monitor():
    t_base = 0
    fc_atual = 75 
    
    while True:
        t_base += 0.05
        t = np.linspace(t_base, t_base + 5, 100)
        
        # Logica da IA
        if btn_simular and intervencao:
            if "key" not in st.session_state or st.session_state.key != intervencao:
                with laudo_area:
                    with st.spinner("Analisando bioquímica..."):
                        p = f"Simulação: Paciente {sexo}, {idade} anos. Droga: {intervencao}. Explique a cascata fisiológica."
                        try:
                            res = model.generate_content(p)
                            st.markdown(f'<div class="report-box">{res.text}</div>', unsafe_allow_html=True)
                            st.session_state.key = intervencao
                        except:
                            st.error("Erro na comunicação com o Gemini.")

        # Ondas do monitor
        df = pd.DataFrame({
            'Tempo': t,
            'ECG': np.sin(t * 8) + np.random.normal(0, 0.02, 100),
            'PLET': np.sin(t * 2.0) * 0.5 + 2,
            'RESP': np.sin(t * 0.6) * 0.3 + 1
        }).set_index('Tempo')
        plot_spot.line_chart(df, color=["#00FF00", "#00FFFF", "#FFFF00"], height=400)

        # Números estáveis
        if np.random.random() > 0.95: 
            fc_atual += np.random.choice([-1, 0, 1])

        metrics_spot.markdown(f'''
            <div class="monitor-panel">
                <div class="metric-group" style="color: #00FF00;"><div class="metric-label">ECG / FC</div><div class="metric-value">{fc_atual}</div></div>
                <div class="metric-group" style="color: #00FFFF;"><div class="metric-label">SpO2 %</div><div class="metric-value">98</div></div>
                <div class="metric-group" style="color: #FFFF00;"><div class="metric-label">RESP</div><div class="metric-value">16</div></div>
                <div class="metric-group" style="color: #FFFFFF;"><div class="metric-label">TEMP ºC</div><div class="metric-value" style="font-size: 35px;">36.8</div></div>
            </div>
        ''', unsafe_allow_html=True)
        time.sleep(0.3)

# --- 7. EXECUÇÃO ---
rodar_monitor()
