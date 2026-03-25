import streamlit as st
import google.generativeai as genai
import pandas as pd
import numpy as np
import re

# --- 1. CONFIGURAÇÃO ---
CHAVE_API = st.secrets.get("CHAVE_GEMINI", "")
if CHAVE_API:
    genai.configure(api_key=CHAVE_API)
    model = genai.GenerativeModel('gemini-1.5-flash') 
else:
    st.error("Chave API não configurada.")
    st.stop()

st.set_page_config(page_title="BioSim Pro", layout="wide")

# --- 2. ESTADO DA SESSÃO ---
if 'sinais' not in st.session_state:
    st.session_state.sinais = {"fc": 75, "sp": 98, "resp": 16, "pam": 90}
if 'ultimo_laudo' not in st.session_state:
    st.session_state.ultimo_laudo = ""

# --- 3. SIDEBAR (CAMPOS MANUAIS E SEPARADOS) ---
with st.sidebar:
    st.header("🧬 Perfil do Paciente")
    sexo = st.selectbox("Sexo", ["Feminino", "Masculino"])
    idade = st.number_input("Idade", 1, 110, 24)
    peso = st.number_input("Peso (kg)", 1.0, 300.0, 65.0)
    altura = st.number_input("Estatura (m)", 0.5, 2.5, 1.70)
    
    # Sliders separados mantidos
    gordura = st.slider("Gordura Corporal (BF %)", 5, 50, 22)
    massa_magra = st.slider("Massa Magra (%)", 10, 90, 40)
    
    st.divider()
    st.subheader("📋 Histórico Clínico")
    
    # Estilo de Vida: Texto livre
    estilo_vida = st.text_input("Estilo de Vida:", placeholder="Ex: Maratonista, fumante...")
    
    # Patologias: ENTRADA MANUAL (estilo LinkedIn)
    # O st.multiselect com 'options' vazias e 'default' permite que você digite e crie novas tags
    patologias = st.multiselect(
        "Patologias / Comorbidades Prévias (digite e dê enter):",
        options=[], 
        default=[],
        placeholder="Escreva e aperte Enter",
        help="Digite qualquer termo e pressione Enter para adicionar como tag.",
        key="patologias_tags"
    )

# --- 4. PAINEL DE TELEMETRIA REATIVO ---
st.title("Painel de Telemetria BioSim")

m1, m2, m3, m4 = st.columns(4)
m1.metric("FC (BPM)", st.session_state.sinais['fc'])
m2.metric("RESP (MPM)", st.session_state.sinais['resp'])
m3.metric("PAM (mmHg)", st.session_state.sinais['pam'])
m4.metric("SpO2 (%)", f"{st.session_state.sinais['sp']}%")

# Gráfico dinâmico conforme a FC
t = np.linspace(0, 2, 200)
onda = np.sin(t * (st.session_state.sinais['fc']/10)) + np.random.normal(0, 0.02, 200)
st.line_chart(onda, height=150)

st.divider()

# --- 5. INTERVENÇÃO ---
st.subheader("🧪 Intervenção Terapêutica")
c_in, c_bt = st.columns([4, 1])
droga = c_in.text_input("Inserir Fármaco ou Estímulo:", placeholder="Ex: Adrenalina 2mg IV")

if c_bt.button("EXECUTAR SIMULAÇÃO") and droga:
    with st.spinner("Analisando resposta..."):
        prompt = (f"Paciente {sexo}, {idade}a, {peso}kg, {altura}m. "
                  f"Gordura: {gordura}%, Massa Magra: {massa_magra}%. "
                  f"Estilo de Vida: {estilo_vida}. Patologias: {', '.join(patologias)}. "
                  f"Intervenção: {droga}. "
                  f"Explique a farmacodinâmica e termine com: [FC:X, RESP:Y, PAM:Z, SPO2:W]")
        
        try:
            res = model.generate_content(prompt)
            texto_bruto = res.text
            
            regex = r"\[FC:(\d+), RESP:(\d+), PAM:(\d+), SPO2:(\d+)\]"
            match = re.search(regex, texto_bruto)
            
            if match:
                st.session_state.sinais = {
                    "fc": int(match.group(1)),
                    "resp": int(match.group(2)),
                    "pam": int(match.group(3)),
                    "sp": int(match.group(4))
                }
                st.session_state.ultimo_laudo = re.sub(regex, "", texto_bruto)
                st.rerun() # Atualiza os números no topo
        except Exception as e:
            st.error("Erro de cota. Aguarde 60 segundos.")

# --- 6. RESULTADO ---
if st.session_state.ultimo_laudo:
    st.markdown("### 📝 Resultado da Intervenção")
    st.info(st.session_state.ultimo_laudo)
