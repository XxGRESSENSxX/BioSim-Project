import streamlit as st
import google.generativeai as genai
import pandas as pd
import numpy as np
import re

# --- 1. CONFIGURAÇÃO (API GEMINI) ---
CHAVE_API = st.secrets.get("CHAVE_GEMINI", "")
if CHAVE_API:
    genai.configure(api_key=CHAVE_API)
    model = genai.GenerativeModel('gemini-1.5-flash') 
else:
    st.error("Erro: API Key não configurada no Streamlit Secrets.")
    st.stop()

st.set_page_config(page_title="BioSim Pro", layout="wide")

# --- 2. ESTADO DA SESSÃO ---
if 'sinais' not in st.session_state:
    st.session_state.sinais = {"fc": 75, "sp": 98, "resp": 16, "pam": 90}
if 'ultimo_laudo' not in st.session_state:
    st.session_state.ultimo_laudo = ""

# --- 3. DESIGN ---
st.markdown('''
    <style>
    .main { background-color: #05070A; }
    .stMetric { background-color: #0F172A; padding: 15px; border-radius: 10px; border: 1px solid #1E293B; }
    .laudo-container { 
        background-color: #0B1120; 
        padding: 20px; 
        border-left: 5px solid #2563EB; 
        border-radius: 8px; 
        color: #F8FAFC; 
    }
    </style>
''', unsafe_allow_html=True)

# --- 4. SIDEBAR (PERFIL COMPLETO) ---
with st.sidebar:
    st.header("🧬 Perfil do Paciente")
    sexo = st.selectbox("Sexo", ["Feminino", "Masculino"])
    idade = st.number_input("Idade", 1, 110, 24)
    peso = st.number_input("Peso (kg)", 1.0, 300.0, 65.0)
    altura = st.number_input("Estatura (m)", 0.5, 2.5, 1.70)
    massa_magra = st.slider("Massa Magra (%)", 10, 90, 40)
    
    st.divider()
    # Multiselect para Histórico Clínico (Incorpora direto no raciocínio da IA)
    historico = st.multiselect(
        "Histórico e Comorbidades:",
        ["Atleta", "Sedentário", "Tabagista", "Diabetes", "ICC", "Hipertensão", "DPOC"],
        default=["Atleta"]
    )

# --- 5. PAINEL DE MONITORAMENTO REATIVO ---
st.title("Painel de Telemetria BioSim")

# As métricas agora usam o st.session_state que é atualizado pela simulação
m1, m2, m3, m4 = st.columns(4)
m1.metric("FC (BPM)", st.session_state.sinais['fc'])
m2.metric("RESP (MPM)", st.session_state.sinais['resp'])
m3.metric("PAM (mmHg)", st.session_state.sinais['pam'])
m4.metric("SpO2 (%)", f"{st.session_state.sinais['sp']}%")

# Gráfico que muda visualmente conforme a FC aumenta/diminui
t = np.linspace(0, 2, 200)
onda = np.sin(t * (st.session_state.sinais['fc']/10)) + np.random.normal(0, 0.02, 200)
st.line_chart(onda, height=150)

st.divider()

# --- 6. INTERVENÇÃO ---
st.subheader("🧪 Administração de Fármacos / Estímulos")
c_in, c_bt = st.columns([4, 1])
droga = c_in.text_input("Inserir Intervenção:", placeholder="Ex: Adrenalina 2mg IV")

if c_bt.button("EXECUTAR SIMULAÇÃO") and droga:
    with st.spinner("Analisando resposta..."):
        # O Prompt envia todos os dados da sidebar para a IA
        prompt = (f"Paciente {sexo}, {idade}a, {peso}kg, {altura}m. Massa Magra: {massa_magra}%. "
                  f"Histórico: {', '.join(historico)}. Intervenção: {droga}. "
                  f"Explique a farmacodinâmica e termine com: [FC:X, RESP:Y, PAM:Z, SPO2:W]")
        
        try:
            res = model.generate_content(prompt)
            texto_bruto = res.text
            
            # Extração dos dados para o painel
            regex = r"\[FC:(\d+), RESP:(\d+), PAM:(\d+), SPO2:(\d+)\]"
            match = re.search(regex, texto_bruto)
            
            if match:
                st.session_state.sinais = {
                    "fc": int(match.group(1)),
                    "resp": int(match.group(2)),
                    "pam": int(match.group(3)),
                    "sp": int(match.group(4))
                }
                # Limpa o texto para o laudo ficar bonito
                st.session_state.ultimo_laudo = re.sub(regex, "", texto_bruto)
                st.rerun() # FORÇA a atualização dos cards de métrica
        except Exception as e:
            st.error("Erro na comunicação com a IA. Tente novamente em alguns segundos.")

# --- 7. EXIBIÇÃO DO LAUDO ---
if st.session_state.ultimo_laudo:
    st.markdown("### 📝 Resultado da Intervenção")
    st.markdown(f'<div class="laudo-container">{st.session_state.ultimo_laudo}</div>', unsafe_allow_html=True)
