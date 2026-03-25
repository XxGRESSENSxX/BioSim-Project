import streamlit as st
import google.generativeai as genai
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

# Listas que vão armazenar as tags que você criar na hora
if 'opcoes_estilo' not in st.session_state:
    st.session_state.opcoes_estilo = []
if 'opcoes_pato' not in st.session_state:
    st.session_state.opcoes_pato = []

# --- 3. FÁBRICA DE TAGS (CALLBACKS) ---
def add_estilo():
    tag = st.session_state.input_estilo.strip()
    if tag and tag not in st.session_state.opcoes_estilo:
        st.session_state.opcoes_estilo.append(tag)
    st.session_state.input_estilo = "" # Limpa o campo após o Enter

def add_pato():
    tag = st.session_state.input_pato.strip()
    if tag and tag not in st.session_state.opcoes_pato:
        st.session_state.opcoes_pato.append(tag)
    st.session_state.input_pato = ""

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("🧬 Perfil do Paciente")
    sexo = st.selectbox("Sexo", ["Feminino", "Masculino"])
    idade = st.number_input("Idade", 1, 110, 24)
    peso = st.number_input("Peso (kg)", 1.0, 300.0, 65.0)
    altura = st.number_input("Estatura (m)", 0.5, 2.5, 1.70)
    
    gordura = st.slider("Gordura Corporal (BF %)", 5, 50, 22)
    massa_magra = st.slider("Massa Magra (%)", 10, 90, 40)
    
    st.divider()
    st.subheader("📋 Histórico Clínico")
    
    # CRIADOR DE TAGS: ESTILO DE VIDA
    st.text_input("➕ Digite o Estilo de Vida e dê Enter:", key="input_estilo", on_change=add_estilo)
    tags_estilo = st.multiselect("Tags de Estilo ativas:", options=st.session_state.opcoes_estilo, default=st.session_state.opcoes_estilo)
    
    # CRIADOR DE TAGS: PATOLOGIAS
    st.text_input("➕ Digite a Patologia e dê Enter:", key="input_pato", on_change=add_pato)
    tags_pato = st.multiselect("Tags de Patologia ativas:", options=st.session_state.opcoes_pato, default=st.session_state.opcoes_pato)

# --- 5. PAINEL DE TELEMETRIA REATIVO ---
st.title("Painel de Telemetria BioSim")

m1, m2, m3, m4 = st.columns(4)
m1.metric("FC (BPM)", st.session_state.sinais['fc'])
m2.metric("RESP (MPM)", st.session_state.sinais['resp'])
m3.metric("PAM (mmHg)", st.session_state.sinais['pam'])
m4.metric("SpO2 (%)", f"{st.session_state.sinais['sp']}%")

t = np.linspace(0, 2, 200)
onda = np.sin(t * (st.session_state.sinais['fc']/10)) + np.random.normal(0, 0.02, 200)
st.line_chart(onda, height=150)

st.divider()

# --- 6. INTERVENÇÃO ---
st.subheader("🧪 Intervenção Terapêutica")
c_in, c_bt = st.columns([4, 1])
droga = c_in.text_input("Inserir Fármaco ou Estímulo:", placeholder="Ex: Adrenalina 2mg IV")

if c_bt.button("EXECUTAR SIMULAÇÃO") and droga:
    with st.spinner("Analisando cascata bioquímica..."):
        # As tags selecionadas são injetadas direto no raciocínio da IA
        prompt = (f"Paciente {sexo}, {idade}a, {peso}kg, {altura}m. "
                  f"Gordura: {gordura}%, Massa Magra: {massa_magra}%. "
                  f"Estilo de Vida: {', '.join(tags_estilo)}. Patologias: {', '.join(tags_pato)}. "
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
                st.rerun() 
        except Exception as e:
            st.error("Erro de cota ou conexão. Aguarde alguns segundos.")

# --- 7. RESULTADO ---
if st.session_state.ultimo_laudo:
    st.markdown("### 📝 Resultado da Intervenção")
    st.info(st.session_state.ultimo_laudo)
