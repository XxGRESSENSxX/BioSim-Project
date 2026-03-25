import streamlit as st
import google.generativeai as genai
import pandas as pd
import numpy as np
import re

# --- 1. CONFIGURAÇÃO (FIXADO NA VERSÃO 2.5) ---
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
if 'historico_acoes' not in st.session_state:
    st.session_state.historico_acoes = []

# --- 3. CSS PARA INTERFACE MÉDICA LÚDICA ---
st.markdown('''
    <style>
    .main { background-color: #05070A; }
    .stMetric { background-color: #0F172A; padding: 15px; border-radius: 10px; border: 1px solid #1E293B; }
    .biosim-header { font-size: 42px; font-weight: 800; color: #F8FAFC; margin-bottom: 20px; }
    .status-card { border-left: 5px solid #2563EB; background: #0F172A; padding: 20px; border-radius: 5px; }
    </style>
''', unsafe_allow_html=True)

# --- 4. SIDEBAR (PERFIL COMPLETO) ---
with st.sidebar:
    st.markdown('<div style="font-size:30px; font-weight:bold;">BioSim Pro</div>', unsafe_allow_html=True)
    
    with st.expander("👤 PERFIL BIOLÓGICO", expanded=True):
        sexo = st.selectbox("Sexo", ["Feminino", "Masculino"])
        idade = st.number_input("Idade", 1, 110, 24)
        peso = st.number_input("Massa (kg)", 1.0, 300.0, 65.0)
        altura = st.number_input("Estatura (m)", 0.5, 2.5, 1.70)
        gordura = st.slider("Gordura (BF %)", 5, 50, 22)
    
    st.divider()
    st.subheader("📋 HISTÓRICO CLÍNICO")
    estilo = st.text_input("Estilo de Vida:", placeholder="Ex: Atleta, Sedentário...")
    patologias = st.text_input("Comorbidades:", placeholder="Ex: ICC, Diabetes...")

# --- 5. PAINEL DE SINAIS VITAIS (LÚDICO E LEVE) ---
st.markdown('<div class="biosim-header">Painel de Monitoramento Dinâmico</div>', unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)

# Renderização das métricas baseadas no estado atual
with m1:
    st.metric("Frequência Cardíaca", f"{st.session_state.sinais['fc']} BPM", delta=None, delta_color="normal")
    st.progress(min(st.session_state.sinais['fc'] / 200, 1.0)) # Barra visual

with m2:
    st.metric("Frequência Resp.", f"{st.session_state.sinais['resp']} MPM")
    st.progress(min(st.session_state.sinais['resp'] / 40, 1.0))

with m3:
    st.metric("Pressão Arterial (PAM)", f"{st.session_state.sinais['pam']} mmHg")
    st.progress(min(st.session_state.sinais['pam'] / 180, 1.0))

with m4:
    st.metric("Saturação O2", f"{st.session_state.sinais['sp']} %")
    st.progress(st.session_state.sinais['sp'] / 100)

# --- 6. GRÁFICO DE TENDÊNCIA (ESTÁTICO, NÃO PESA) ---
# Em vez de mover, ele mostra a "forma da onda" atual
t = np.linspace(0, 2, 200)
ecg_shape = np.sin(t * (st.session_state.sinais['fc']/10)) + np.random.normal(0, 0.05, 200)
st.line_chart(ecg_shape, height=150, use_container_width=True)
st.caption("Traçado Eletrocardiográfico de Referência")

st.divider()

# --- 7. SIMULAÇÃO E LÓGICA ---
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
    with st.spinner("Analisando Cascata Fisiológica..."):
        prompt = f"Paciente {sexo}, {idade}a, {peso}kg. Estilo: {estilo}. Patologia: {patologias}. Intervenção: {intervencao}. Descreva o efeito clínico e termine OBRIGATORIAMENTE com: [FC:X, RESP:Y, PAM:Z, SPO2:W]"
        try:
            res = model.generate_content(prompt)
            novos_sinais = extrair_dados(res.text)
            
            if novos_sinais:
                st.session_state.sinais.update(novos_sinais)
                st.session_state.historico_acoes.insert(0, res.text) # Guarda o laudo
                st.rerun() # Atualiza a tela com os novos números
        except:
            st.error("Falha na simulação. Tente novamente.")

# Exibição do histórico de laudos
if st.session_state.historico_acoes:
    st.markdown("### 📝 Relatório de Evolução")
    for laudo in st.session_state.historico_acoes:
        st.markdown(f'<div class="status-card">{laudo}</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
