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

st.set_page_config(page_title="BioSim Pro v3.8", layout="wide")

# --- 2. INICIALIZAÇÃO DE ESTADO ---
if 'sinais' not in st.session_state:
    st.session_state.sinais = {"fc": 75, "sp": 98, "resp": 16, "pam": 90}
if 'ultimo_laudo' not in st.session_state:
    st.session_state.ultimo_laudo = ""

# --- 3. SIDEBAR (CAMPOS DIGITÁVEIS AGORA) ---
with st.sidebar:
    st.markdown("### 🧬 Perfil Bio")
    sexo = st.selectbox("Sexo", ["Feminino", "Masculino"])
    idade = st.number_input("Idade", 1, 110, 24)
    peso = st.number_input("Peso (kg)", 1.0, 300.0, 65.0)
    
    st.divider()
    st.markdown("### 📋 Histórico Clínico")
    # MUDANÇA: Agora são campos de texto livre
    estilo_vida = st.text_input("Estilo de Vida:", placeholder="Ex: Sedentário, maratonista, tabagista...")
    patologias = st.text_input("Patologias / Comorbidades:", placeholder="Ex: ICC, DPOC, Diabetes Tipo 2...")

# --- 4. LAYOUT DO MONITOR ---
col_ondas, col_numeros = st.columns([2.5, 1])
with col_ondas:
    plot_spot = st.empty() 
with col_numeros:
    metrics_spot = st.empty()

st.divider()

# --- 5. INTERVENÇÃO ---
st.subheader("🧪 Simulador de Fisiologia Aplicada")
c_in, c_bt = st.columns([4, 1])
intervencao = c_in.text_input("Dose e Via:", placeholder="Ex: Adrenalina 8mg IV")
btn_simular = c_bt.button("Simular Resposta")
laudo_area = st.empty()

# --- 6. PARSER DE DADOS (EXTRAÇÃO) ---
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

# --- 7. LOOP DINÂMICO ---
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
                        Paciente {sexo}, {idade} anos, {peso}kg.
                        Estilo de Vida: {estilo_vida}.
                        Patologias: {patologias}.
                        Intervenção: {intervencao}.
                        
                        1. Descreva os efeitos bioquímicos e hemodinâmicos.
                        2. Se a dose for incompatível com a vida ou causar colapso, detalhe.
                        3. OBRIGATÓRIO (para o monitor): Termine a resposta com os novos parâmetros:
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
            laudo_area.markdown(f'<div style="background:#0B1120;padding:25px;border-radius:10px;border:1px solid #1E293B;color:#CBD5E1">{st.session_state.ultimo_laudo}</div>', unsafe_allow_html=True)

        # RENDERIZAÇÃO DAS ONDAS
        fc = st.session_state.sinais['fc']
        if fc > 0:
            fator_velocidade = fc / 10
            ecg = np.sin(t * fator_velocidade) + np.random.normal(0, 0.02, 100)
            resp = np.sin(t * (st.session_state.sinais['resp']/20)) * 0.4 + 1
        else:
            # ASSISTOLIA (Linha reta com ruído mínimo)
            ecg = np.zeros(100) + np.random.normal(0, 0.005, 100)
            resp = np.zeros(100) + 1

        df = pd.DataFrame({'ECG': ecg, 'RESP': resp}).set_index(t)
        plot_spot.line_chart(df, color=["#00FF00", "#FFFF00"], height=400)

        # MONITOR NUMÉRICO
        metrics_spot.markdown(f'''
            <div style="background:black;padding:20px;border-radius:10px;border:2px solid #1E293B">
                <p style="color:#00FF00;margin:0">FC (bpm)</p>
                <h1 style="color:#00FF00;font-size:60px;margin:-10px 0">{"00" if fc==0 else fc}</h1>
                <p style="color:#FFFF00;margin:0">RESP (mpm)</p>
                <h1 style="color:#FFFF00;font-size:45px;margin:-10px 0">{st.session_state.sinais['resp']}</h1>
                <p style="color:#FFFFFF;margin:0">PAM (mmHg)</p>
                <h1 style="color:#FFFFFF;font-size:45px;margin:-10px 0">{st.session_state.sinais['pam']}</h1>
                <p style="color:#00FFFF;margin:0">SpO2 %</p>
                <h1 style="color:#00FFFF;font-size:45px;margin:-10px 0">{st.session_state.sinais['sp']}</h1>
            </div>
        ''', unsafe_allow_html=True)
        
        time.sleep(0.3)

rodar_monitor()
