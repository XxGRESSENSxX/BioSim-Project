import streamlit as st
import google.generativeai as genai
import pandas as pd
import numpy as np
import re

# --- 1. CONFIGURAÇÃO (FIXADO NA 2.5) ---
CHAVE_API = st.secrets.get("CHAVE_GEMINI", "")
if CHAVE_API:
    genai.configure(api_key=CHAVE_API)
    model = genai.GenerativeModel('gemini-2.5-flash') 
else:
    st.error("Erro de Licença: Chave não encontrada.")
    st.stop()

st.set_page_config(page_title="BioSim Professional", layout="wide")

# --- 2. ESTADO DO SISTEMA ---
if 'sinais' not in st.session_state:
    st.session_state.sinais = {"fc": 75, "sp": 98, "resp": 16, "pam": 90}
if 'ultimo_resultado' not in st.session_state:
    st.session_state.ultimo_resultado = ""

# --- 3. CSS ---
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
        font-size: 16px;
        line-height: 1.6;
    }
    </style>
''', unsafe_allow_html=True)

# --- 4. SIDEBAR (RESTAURADA COM MASSA MAGRA) ---
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
    estilo = st.text_input("Estilo de Vida:", placeholder="Ex: Atleta, fumante...")
    patologias = st.text_input("Comorbidades:", placeholder="Ex: ICC, Diabetes...")

# --- 5. PAINEL DE MONITORAMENTO ---
st.title("Monitor de Fisiologia Aplicada")

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Frequência Cardíaca", f"{st.session_state.sinais['fc']} BPM")
    st.progress(min(st.session_state.sinais['fc'] / 200, 1.0))
with m2:
    st.metric("Frequência Resp.", f"{st.session_state.sinais['resp']} MPM")
    st.progress(min(st.session_state.sinais['resp'] / 40, 1.0))
with m3:
    st.metric("Pressão Arterial (PAM)", f"{st.session_state.sinais['pam']} mmHg")
    st.progress(min(st.session_state.sinais['pam'] / 180, 1.0))
with m4:
    st.metric("Saturação O2", f"{st.session_state.sinais['sp']} %")
    st.progress(st.session_state.sinais['sp'] / 100)

# Gráfico de Referência
t = np.linspace(0, 2, 200)
ecg = np.sin(t * (st.session_state.sinais['fc']/10)) + np.random.normal(0, 0.02, 200)
st.line_chart(ecg, height=150)

st.divider()

# --- 6. INTERVENÇÃO E RESULTADO ---
st.subheader("🧪 Intervenção Terapêutica")
c_in, c_bt = st.columns([4, 1])
intervencao = c_in.text_input("Fármaco ou Estímulo:", placeholder="Ex: Adrenalina 2mg IV")
btn_simular = c_bt.button("EXECUTAR SIMULAÇÃO")

def extrair_dados(texto):
    padrao = r"\[FC:(\d+), RESP:(\d+), PAM:(\d+), SPO2:(\d+)\]"
    busca = re.search(padrao, texto)
    if busca:
        return {"fc": int(busca.group(1)), "resp": int(busca.group(2)), "pam": int(busca.group(3)), "sp": int(busca.group(4))}
    return None

if btn_simular and intervencao:
    with st.spinner("Analisando Resposta Bioquímica..."):
        prompt = (f"Paciente {sexo}, {idade}a, {peso}kg, {altura}m. Massa Magra: {massa_magra}%. "
                  f"Estilo: {estilo}. Patologia: {patologias}. Intervenção: {intervencao}. "
                  f"Explique a farmacodinâmica e termine com: [FC:X, RESP:Y, PAM:Z, SPO2:W]")
        try:
            res = model.generate_content(prompt)
            st.session_state.ultimo_resultado = res.text # SALVA O TEXTO
            novos = extrair_dados(res.text)
            if novos:
                st.session_state.sinais.update(novos)
            st.rerun()
        except:
            st.error("Erro na simulação.")

# EXIBIÇÃO DO RESULTADO (AQUI É ONDE APARECE O TEXTO)
if st.session_state.ultimo_resultado:
    st.markdown("### 📝 Resultado da Intervenção")
    st.markdown(f'<div class="resultado-clinico">{st.session_state.ultimo_resultado}</div>', unsafe_allow_html=True)
