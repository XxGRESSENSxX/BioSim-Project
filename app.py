import streamlit as st
import google.generativeai as genai
import pandas as pd
import numpy as np
import re

# --- 1. CONFIGURAÇÃO (FIXADO NA VERSÃO 2.5) ---
CHAVE_API = st.secrets.get("CHAVE_GEMINI", "")
if CHAVE_API:
    genai.configure(api_key=CHAVE_API)
    # Mantendo a 2.5 que você validou
    model = genai.GenerativeModel('gemini-2.5-flash') 
else:
    st.error("Erro: Chave API não configurada.")
    st.stop()

st.set_page_config(page_title="BioSim Professional", layout="wide")

# --- 2. ESTADO DO SISTEMA ---
if 'sinais' not in st.session_state:
    st.session_state.sinais = {"fc": 75, "sp": 98, "resp": 16, "pam": 90}
if 'ultimo_resultado' not in st.session_state:
    st.session_state.ultimo_resultado = ""

# --- 3. ESTILO VISUAL ---
st.markdown('''
    <style>
    .main { background-color: #05070A; }
    .stMetric { background-color: #0F172A; padding: 15px; border-radius: 10px; border: 1px solid #1E293B; }
    .resultado-clinico { 
        background-color: #0B1120; 
        padding: 25px; 
        border-left: 5px solid #2563EB; 
        border-radius: 8px; 
        color: #F8FAFC; 
        margin-top: 20px;
    }
    </style>
''', unsafe_allow_html=True)

# --- 4. SIDEBAR (PERFIL COMPLETO RESTAURADO) ---
with st.sidebar:
    st.markdown('## BioSim Pro')
    with st.expander("👤 PERFIL BIOLÓGICO", expanded=True):
        sexo = st.selectbox("Sexo", ["Feminino", "Masculino"])
        idade = st.number_input("Idade", 1, 110, 24)
        peso = st.number_input("Massa (kg)", 1.0, 300.0, 65.0)
        altura = st.number_input("Estatura (m)", 0.5, 2.5, 1.70)
        gordura = st.slider("Gordura (BF %)", 5, 50, 22)
        massa_magra = st.slider("Massa Magra (%)", 10, 90, 40) # RESTAURADO
    
    st.divider()
    st.subheader("📋 HISTÓRICO CLÍNICO")
    estilo = st.text_input("Estilo de Vida:", placeholder="Ex: Atleta, Sedentário...")
    patologias = st.text_input("Comorbidades:", placeholder="Ex: ICC, Diabetes...")

# --- 5. MONITOR DINÂMICO ---
st.title("Painel de Monitoramento Fisiológico")

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("FC (BPM)", st.session_state.sinais['fc'])
    st.progress(min(st.session_state.sinais['fc'] / 220, 1.0))
with m2:
    st.metric("RESP (MPM)", st.session_state.sinais['resp'])
    st.progress(min(st.session_state.sinais['resp'] / 40, 1.0))
with m3:
    st.metric("PAM (mmHg)", st.session_state.sinais['pam'])
    st.progress(min(st.session_state.sinais['pam'] / 180, 1.0))
with m4:
    st.metric("SpO2 (%)", st.session_state.sinais['sp'])
    st.progress(st.session_state.sinais['sp'] / 100)

# Gráfico atualizado conforme logs (stretch)
t = np.linspace(0, 2, 200)
onda = np.sin(t * (st.session_state.sinais['fc']/10)) + np.random.normal(0, 0.02, 200)
st.line_chart(onda, height=150, width='stretch')

st.divider()

# --- 6. SIMULAÇÃO ---
st.subheader("🧪 Intervenção Terapêutica")
c_in, c_bt = st.columns([4, 1])
intervencao = c_in.text_input("Fármaco/Estímulo:", key="sim_input")
btn_simular = c_bt.button("EXECUTAR SIMULAÇÃO")

def extrair_dados(texto):
    padrao = r"\[FC:(\d+), RESP:(\d+), PAM:(\d+), SPO2:(\d+)\]"
    busca = re.search(padrao, texto)
    if busca:
        return {"fc": int(busca.group(1)), "resp": int(busca.group(2)), "pam": int(busca.group(3)), "sp": int(busca.group(4))}
    return None

if btn_simular and intervencao:
    with st.spinner("Simulando Cascata Farmacológica..."):
        p = (f"Paciente {sexo}, {idade}a, {peso}kg, {altura}m, {massa_magra}% Massa Magra. "
             f"Estilo: {estilo}. Patologia: {patologias}. Intervenção: {intervencao}. "
             f"Explique os efeitos e finalize com: [FC:X, RESP:Y, PAM:Z, SPO2:W]")
        try:
            res = model.generate_content(p)
            st.session_state.ultimo_resultado = res.text
            dados = extrair_dados(res.text)
            if dados:
                st.session_state.sinais.update(dados)
            st.rerun()
        except Exception as e:
            st.error("Limite de cota excedido. Aguarde 1 minuto para a próxima requisição.")

if st.session_state.ultimo_resultado:
    st.markdown("### 📝 Resultado da Intervenção")
    st.markdown(f'<div class="resultado-clinico">{st.session_state.ultimo_resultado}</div>', unsafe_allow_html=True)
