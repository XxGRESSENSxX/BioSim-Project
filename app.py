import streamlit as st
import google.generativeai as genai
import numpy as np
import re
try:
    CHAVE_API = st.secrets["GOOGLE_API_KEY"]
except:
    CHAVE_API = ""

genai.configure(api_key=CHAVE_API)
model = genai.GenerativeModel('gemini-2.5-flash')

st.set_page_config(page_title="BioSim v2.5 - Pro", layout="wide")

if 'sinais' not in st.session_state:
    st.session_state.sinais = {"fc": 75, "sp": 98, "resp": 16, "pam": 90}
if 'ultimo_laudo' not in st.session_state:
    st.session_state.ultimo_laudo = ""
if 'referencias' not in st.session_state:
    st.session_state.referencias = "As referências aparecerão aqui após a simulação."
if 'opcoes_estilo' not in st.session_state:
    st.session_state.opcoes_estilo = []
if 'opcoes_pato' not in st.session_state:
    st.session_state.opcoes_pato = []

def reset_estudo():
    st.session_state.sinais = {"fc": 75, "sp": 98, "resp": 16, "pam": 90}
    st.session_state.ultimo_laudo = ""
    st.session_state.referencias = "As referências aparecerão aqui após a simulação."
    st.session_state.opcoes_estilo = []
    st.session_state.opcoes_pato = []

def add_tag(key_input, key_lista):
    tag = st.session_state[key_input].strip()
    if tag and tag not in st.session_state[key_lista]:
        st.session_state[key_lista].append(tag)
    st.session_state[key_input] = "" 

def gerar_onda_ecg(fc):
    pontos = 400
    t = np.linspace(0, 2, pontos)
    def beat(x):
        x = x % 1.0
        p = 0.1 * np.exp(-((x - 0.2)**2) / 0.001) 
        qrs = 1.2 * np.exp(-((x - 0.4)**2) / 0.0001) - 0.15 * np.exp(-((x - 0.38)**2) / 0.0001)
        t_wave = 0.2 * np.exp(-((x - 0.7)**2) / 0.005)
        return p + qrs + t_wave
    return [beat(ti * (fc / 60)) for ti in t] + np.random.normal(0, 0.012, pontos)

with st.sidebar:
    st.header("Perfil do Paciente")
    sexo = st.selectbox("Sexo", ["Feminino", "Masculino"])
    idade = st.number_input("Idade", 1, 110, 24)
    peso = st.number_input("Peso (kg)", 1.0, 300.0, 65.0)
    altura = st.number_input("Estatura (m)", 0.50, 2.50, 1.70)
    
    gordura = st.slider("Gordura Corporal (BF %)", 5, 50, 22)
    massa_magra = st.slider("Massa Magra (%)", 10, 90, 40)
    
    st.divider()
    st.subheader("Histórico Clínico")
    st.text_input("➕ Estilo de Vida:", key="in_estilo", on_change=add_tag, args=("in_estilo", "opcoes_estilo"))
    tags_estilo = st.multiselect("Tags Estilo:", options=st.session_state.opcoes_estilo, default=st.session_state.opcoes_estilo)
    
    st.text_input("➕ Patologia:", key="in_pato", on_change=add_tag, args=("in_pato", "opcoes_pato"))
    tags_pato = st.multiselect("Tags Patologia:", options=st.session_state.opcoes_pato, default=st.session_state.opcoes_pato)
    
    st.divider()
    if st.button("RESETAR ESTUDO", use_container_width=True, on_click=reset_estudo):
        st.rerun()

st.title("Monitor Multiparamétrico BioSim")
m1, m2, m3, m4 = st.columns(4)
m1.metric("FC (BPM)", st.session_state.sinais['fc'])
m2.metric("RESP (MPM)", st.session_state.sinais['resp'])
m3.metric("PAM (mmHg)", st.session_state.sinais['pam'])
m4.metric("SpO2 (%)", f"{st.session_state.sinais['sp']}%")

st.line_chart(gerar_onda_ecg(st.session_state.sinais['fc']), height=200)

st.divider()

aba_simulacao, aba_referencias = st.tabs(["Intervenção", "Referências Teóricas (ABNT)"])

with aba_simulacao:
    c_in, c_bt = st.columns([4, 1])
    droga = c_in.text_input("Inserir Fármaco (Ex: Adrenalina 1mg IV):")

    if c_bt.button("EXECUTAR SIMULAÇÃO") and droga:
        with st.spinner("Analisando cascata molecular e buscando literatura via Gemini Pro..."):
            prompt = (f"Simulador Farmacológico. Paciente {sexo}, {idade}a, {peso}kg, {altura}m.\n"
                      f"Composição: {gordura}% BF, {massa_magra}% MM.\n"
                      f"Histórico: {tags_estilo} | {tags_pato}.\n"
                      f"Sinais Atuais: FC={st.session_state.sinais['fc']}, PAM={st.session_state.sinais['pam']}.\n"
                      f"Intervenção: {droga}.\n"
                      f"Tarefa: Explique a farmacodinâmica e os novos sinais vitais.\n"
                      f"MANDATÓRIO: Forneça a resposta em DUAS partes separadas pela tag [REF].\n"
                      f"Parte 1: A explicação clínica.\n"
                      f"Parte 2: Pelo menos 2 referências bibliográficas reais (livros texto ou artigos clássicos) em formato ABNT que embasam sua resposta.\n"
                      f"Termine a Parte 1 EXATAMENTE com: [FC:X, RESP:Y, PAM:Z, SPO2:W]")
            
            try:
                response = model.generate_content(prompt)
                texto = response.text
                
                # Divisão do texto usando a tag [REF]
                if "[REF]" in texto:
                    partes = texto.split("[REF]")
                    laudo_bruto = partes[0]
                    referencias_abnt = partes[1].strip()
                else:
                    laudo_bruto = texto
                    referencias_abnt = "Não foi possível extrair as referências em ABNT nesta rodada."

                # Extração dos sinais vitais
                match = re.search(r"\[FC:(\d+), RESP:(\d+), PAM:(\d+), SPO2:(.+)\]", laudo_bruto)
                
                if match:
                    # Tenta converter SpO2 para int, caso a IA envie com '%'
                    spo2_val = match.group(4).replace('%', '').strip()
                    
                    st.session_state.sinais = {
                        "fc": int(match.group(1)), "resp": int(match.group(2)),
                        "pam": int(match.group(3)), "sp": spo2_val
                    }
                    st.session_state.ultimo_laudo = re.sub(r"\[.*\]", "", laudo_bruto).strip()
                    st.session_state.referencias = referencias_abnt
                    st.rerun()
                else:
                    st.session_state.ultimo_laudo = laudo_bruto
            except Exception as e:
                st.error(f"Erro na simulação: {e}")

    if st.session_state.ultimo_laudo:
        st.info(st.session_state.ultimo_laudo)

with aba_referencias:
    st.markdown("### Base Bibliográfica da Última Simulação")
    st.write(st.session_state.referencias)
