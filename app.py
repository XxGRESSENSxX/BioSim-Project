import streamlit as st
import google.generativeai as genai
import pandas as pd
import numpy as np
import time

# --- CONFIGURAÇÕES ---
CHAVE_GEMINI = "AIzaSyC9Sp2IitOOH5fxWFEQP6OYCC6pefv0EhY"
genai.configure(api_key=CHAVE_GEMINI)

# ATUALIZADO PARA 2.5-FLASH
model = genai.GenerativeModel('models/gemini-2.5-flash')

st.set_page_config(page_title="BioSim Pro", layout="wide", initial_sidebar_state="expanded")

# --- SEU DESIGN ORIGINAL (CSS) ---
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

# --- 1. SIDEBAR (RESTAURADA) ---
with st.sidebar:
    st.markdown('<div class="biosim-title">BioSim</div>', unsafe_allow_html=True)
    st.markdown('<p style="color: #64748B; margin-bottom: 30px;">Physiological Simulator v3.2</p>', unsafe_allow_html=True)
    
    st.subheader("👤 Perfil Biológico")
    sexo = st.selectbox("Sexo", ["Feminino", "Masculino"])
    idade = st.number_input("Idade", 18, 100, 24)
    
    c1, c2 = st.columns(2)
    peso = c1.number_input("Massa (kg)", value=65.0)
    altura = c2.number_input("Estatura (m)", value=1.70)
    
    fat = st.slider("Gordura (BF %)", 5, 50, 22)
    musculo = st.slider("Massa Magra (%)", 20, 70, 40)
    
    st.divider()
    st.subheader("📋 Histórico e Estilo")
    estilo = st.multiselect("Fatores", ["Sedentário", "Ativo", "Atleta Elite", "Tabagista", "Alcoolista"])
    condicao = st.selectbox("Patologia Preexistente", ["Nenhuma", "Diabetes Tipo 1", "Diabetes Tipo 2", "HAS Estágio II", "Hipertiroidismo", "Hipotiroidismo"])

# --- 2. ÁREA DO MONITOR ---
col_ondas, col_numeros = st.columns([2.5, 1])

with col_ondas:
    st.markdown("### Telemetria Multiparamétrica")
    plot_spot = st.empty() 

with col_numeros:
    metrics_spot = st.empty()

st.divider()

# --- 3. INTERVENÇÃO ---
st.subheader("🧪 Simulador de Fisiologia Aplicada")
c_in, c_bt = st.columns([4, 1])
intervencao = c_in.text_input("Inserir Fármaco ou Estímulo:", placeholder="Ex: Adrenalina 1mg IV")
