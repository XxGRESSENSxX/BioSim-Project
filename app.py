import streamlit as st
import google.generativeai as genai
import numpy as np
import re

# --- 1. CONFIGURAÇÃO DA API (ONLINE) ---
CHAVE_API = st.secrets.get("CHAVE_GEMINI", "")
if CHAVE_API:
    genai.configure(api_key=CHAVE_API)
    model = genai.GenerativeModel('gemini-2.5-flash') 
else:
    st.error("Erro: API Key não encontrada no Secrets do Streamlit.")
    st.stop()

st.set_page_config(page_title="BioSim v5.1", layout="wide")

# --- 2. ESTADO DA SESSÃO ---
if 'sinais' not in st.session_state:
    st.session_state.sinais = {"fc": 75, "sp": 98, "resp": 16, "pam": 90}
if 'ultimo_laudo' not in st.session_state:
    st.session_state.ultimo_laudo = ""
if 'opcoes_estilo' not in st.session_state:
    st.session_state.opcoes_estilo = []
if 'opcoes_pato' not in st.session_state:
    st.session_state.opcoes_pato = []

# --- 3. LÓGICA DE TAGS MANUAIS ---
def add_tag(key_input, key_lista):
    tag = st.session_state[key_input].strip()
    if tag and tag not in st.session_state[key_lista]:
        st.session_state[key_lista].append(tag)
    st.session_state[key_input] = "" # Limpa o campo após o Enter

# --- 4. MONITOR ECG (COMPLEXO QRS) ---
def gerar_onda_ecg(fc):
    pontos = 400
    t = np.linspace(0, 2, pontos)
    def beat(x):
        x = x % 1.0
        p = 0.15 * np.exp(-((x - 0.2)**2) / 0.001) # Onda P
        qrs = 1.0 * np.exp(-((x - 0.4)**2) / 0.0001) - 0.1 * np.exp(-((x - 0.38)**2) / 0.0001) # QRS
        t_wave = 0.25 * np.exp(-((x - 0.7)**2) / 0.005) # Onda T
        return p + qrs + t_wave
    
    frequencia_ajustada = (fc / 60)
    onda = [beat(ti * frequencia_ajustada) for ti in t]
    onda += np.random.normal(0, 0.02, pontos) # Ruído clínico
    return onda

# --- 5. SIDEBAR ---
with st.sidebar:
    st.header("Perfil do Paciente")
    sexo = st.selectbox("Sexo", ["Feminino", "Masculino"])
    idade = st.number_input("Idade", 1, 110, 24)
    peso = st.number_input("Peso (kg)", 1.0, 300.0, 65.0)
    altura = st.number_input("Estatura (m)", 0.5, 2.5, 1.70)
    
    # Sliders restaurados e independentes
    gordura = st.slider("Gordura Corporal (BF %)", 5, 50, 22)
    massa_magra = st.slider("Massa Magra (%)", 10, 90, 40)
    
    st.divider()
    st.subheader("Histórico Clínico")
    
    # Estilo de Vida (Tags Manuais)
    st.text_input("➕ Adicionar Estilo de Vida (Enter):", key="in_estilo", on_change=add_tag, args=("in_estilo", "opcoes_estilo"))
    tags_estilo = st.multiselect("Estilo de Vida Ativo:", options=st.session_state.opcoes_estilo, default=st.session_state.opcoes_estilo)
    
    # Patologias (Tags Manuais)
    st.text_input("➕ Adicionar Patologia (Enter):", key="in_pato", on_change=add_tag, args=("in_pato", "opcoes_pato"))
    tags_pato = st.multiselect("Patologias Ativas:", options=st.session_state.opcoes_pato, default=st.session_state.opcoes_pato)

# --- 6. PAINEL DE TELEMETRIA ---
st.title("Monitor Multiparamétrico BioSim (Online)")

m1, m2, m3, m4 = st.columns(4)
m1.metric("FC (BPM)", st.session_state.sinais['fc'])
m2.metric("RESP (MPM)", st.session_state.sinais['resp'])
m3.metric("PAM (mmHg)", st.session_state.sinais['pam'])
m4.metric("SpO2 (%)", f"{st.session_state.sinais['sp']}%")

st.write("**Traçado Eletrocardiográfico (ECG)**")
onda_qrs = gerar_onda_ecg(st.session_state.sinais['fc'])
st.line_chart(onda_qrs, height=200)

st.divider()

# --- 7. INTERVENÇÃO ---
st.subheader("Intervenção")
c_in, c_bt = st.columns([4, 1])
droga = c_in.text_input("Inserir Fármaco ou Estímulo:", placeholder="Ex: Adrenalina 2mg IV")

if c_bt.button("EXECUTAR SIMULAÇÃO") and droga:
    with st.spinner("IA analisando farmacodinâmica..."):
        prompt = (f"Paciente {sexo}, {idade}a, {peso}kg, {altura}m. Gordura: {gordura}%, Massa Magra: {massa_magra}%. "
                  f"Estilo: {', '.join(tags_estilo)}. Patologias: {', '.join(tags_pato)}. "
                  f"Intervenção: {droga}. Explique a resposta e termine com: [FC:X, RESP:Y, PAM:Z, SPO2:W]")
        
        try:
            res = model.generate_content(prompt)
            texto_bruto = res.text
            regex = r"\[FC:(\d+), RESP:(\d+), PAM:(\d+), SPO2:(\d+)\]"
            match = re.search(regex, texto_bruto)
            
            if match:
                st.session_state.sinais = {
                    "fc": int(match.group(1)), "resp": int(match.group(2)),
                    "pam": int(match.group(3)), "sp": int(match.group(4))
                }
                st.session_state.ultimo_laudo = re.sub(regex, "", texto_bruto)
                st.rerun()
        except Exception as e:
            st.error("Erro na comunicação. Verifique sua cota da API.")

# --- 8. RESULTADO ---
if st.session_state.ultimo_laudo:
    st.markdown("### Laudo de Resposta")
    st.info(st.session_state.ultimo_laudo)
