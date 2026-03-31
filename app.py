# Projeto: BioSim v2.5
# Desenvolvido por: Gabriela Paula Brizola Gressens Brandão
# Objetivo: Simulação Biomédica Comparada (Humano/Vet)

import streamlit as st
import google.generativeai as genai
import numpy as np
import re

# --- 1. CONFIGURAÇÃO DE SEGURANÇA ---
try:
    CHAVE_API = st.secrets["GOOGLE_API_KEY"]
except:
    CHAVE_API = "SUA_CHAVE_AQUI"

genai.configure(api_key=CHAVE_API)
model = genai.GenerativeModel('gemini-2.5-flash')

st.set_page_config(page_title="BioSim v2.5 pro", layout="wide")

# --- 2. DICIONÁRIO DE ESPÉCIES ---
ESPECIES = {
    "Humano": {"fc": 75, "resp": 16, "pam": 90, "sp": 98},
    "Cão": {"fc": 100, "resp": 24, "pam": 100, "sp": 97},
    "Gato": {"fc": 140, "resp": 30, "pam": 110, "sp": 97},
    "Equino": {"fc": 36, "resp": 12, "pam": 95, "sp": 96}
}

# --- 3. ESTADO DA SESSÃO ---
if 'sinais' not in st.session_state:
    st.session_state.sinais = ESPECIES["Humano"].copy()
if 'ultimo_laudo' not in st.session_state:
    st.session_state.ultimo_laudo = ""
if 'referencias' not in st.session_state:
    st.session_state.referencias = "As referências aparecerão aqui."
if 'opcoes_estilo' not in st.session_state:
    st.session_state.opcoes_estilo = []
if 'opcoes_pato' not in st.session_state:
    st.session_state.opcoes_pato = []

# --- 4. FUNÇÕES ---
def reset_estudo():
    st.session_state.sinais = ESPECIES["Humano"].copy()
    st.session_state.ultimo_laudo = ""
    st.session_state.referencias = "As referências aparecerão aqui."
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

# --- 5. SIDEBAR ---
with st.sidebar:
    st.header("Parâmetros do Estudo")
    especie_selecionada = st.selectbox("Espécie", list(ESPECIES.keys()))
    if st.button(f"Aplicar Padrão: {especie_selecionada}", use_container_width=True):
        st.session_state.sinais = ESPECIES[especie_selecionada].copy()
        st.rerun()

    st.divider()
    st.subheader("Sinais Vitais Iniciais")
    st.session_state.sinais['fc'] = st.number_input("FC (BPM)", 10, 300, st.session_state.sinais['fc'])
    st.session_state.sinais['pam'] = st.number_input("PAM (mmHg)", 20, 250, st.session_state.sinais['pam'])
    st.session_state.sinais['resp'] = st.number_input("RESP (MPM)", 2, 100, st.session_state.sinais['resp'])
    st.session_state.sinais['sp'] = st.number_input("SpO₂ (%)", 40, 100, st.session_state.sinais['sp'])

    st.divider()
    st.subheader("Perfil e Composição")
    sexo = st.selectbox("Sexo", ["Feminino", "Masculino"])
    idade = st.number_input("Idade", 1, 110, 24)
    peso = st.number_input("Peso (kg)", 0.1, 1000.0, 65.0)
    
    col1, col2 = st.columns(2)
    massa_magra = col1.number_input("Massa Magra (%)", 0.0, 100.0, 75.0)
    gordura = col2.number_input("Gordura (%)", 0.0, 100.0, 25.0)

    if especie_selecionada == "Humano":
        altura_valor = st.number_input("Estatura (m)", 0.50, 2.50, 1.70)
        parametro_fisico = f"Estatura: {altura_valor}m"
    else:
        porte_valor = st.selectbox("Porte", ["Mini", "Pequeno", "Médio", "Grande", "Gigante"])
        parametro_fisico = f"Porte: {porte_valor}"

    st.divider()
    st.text_input("Adicionar Estilo de Vida:", key="in_estilo", on_change=add_tag, args=("in_estilo", "opcoes_estilo"))
    tags_estilo = st.multiselect("Tags Estilo:", options=st.session_state.opcoes_estilo, default=st.session_state.opcoes_estilo)
    st.text_input("Adicionar Patologia:", key="in_pato", on_change=add_tag, args=("in_pato", "opcoes_pato"))
    tags_pato = st.multiselect("Tags Patologia:", options=st.session_state.opcoes_pato, default=st.session_state.opcoes_pato)

    if st.button("RESETAR ESTUDO", use_container_width=True, on_click=reset_estudo):
        st.rerun()

# --- 6. MONITOR ---
st.title("Monitor Multiparamétrico BioSim")
m1, m2, m3, m4 = st.columns(4)
m1.metric("FC (BPM)", st.session_state.sinais['fc'])
m2.metric("RESP (MPM)", st.session_state.sinais['resp'])
m3.metric("PAM (mmHg)", st.session_state.sinais['pam'])
m4.metric("SpO₂ (%)", f"{st.session_state.sinais['sp']}%")
st.line_chart(gerar_onda_ecg(st.session_state.sinais['fc']), height=200)

st.divider()

# --- 7. MOTOR DE SIMULAÇÃO ---
aba_simulacao, aba_referencias = st.tabs(["Intervenção", "Referências Teóricas (ABNT)"])

with aba_simulacao:
    c_in, c_bt = st.columns([4, 1])
    droga = c_in.text_input("Inserir Ação (Ex: Atropina 0.04mg/kg IV):")

    if c_bt.button("EXECUTAR SIMULAÇÃO") and droga:
        with st.spinner("Processando Simulação..."):
            
            prompt = f"""
            Atue como um Especialista Sênior em Farmacologia e Fisiologia.
            
            Dados do Paciente:
            Espécie: {especie_selecionada} | Sexo: {sexo} | Idade: {idade} anos
            Peso: {peso}kg | Massa Magra: {massa_magra}% | Gordura Corporal: {gordura}%
            Físico: {parametro_fisico}
            Estilo de Vida: {', '.join(tags_estilo) if tags_estilo else 'Nenhum'}
            Patologias: {', '.join(tags_pato) if tags_pato else 'Nenhuma'}
            
            Sinais Vitais Iniciais:
            FC: {st.session_state.sinais['fc']} | PAM: {st.session_state.sinais['pam']} | RESP: {st.session_state.sinais['resp']} | SpO2: {st.session_state.sinais['sp']}%
            
            Intervenção: {droga}
            
            Tarefa:
            Forneça uma explicação clínica detalhada, fluida e aprofundada (nível de doutorado). Vá direto ao ponto técnico, sem saudações genéricas.
            1. Descreva a farmacocinética da droga, explicando como o volume de distribuição e a lipossolubilidade são afetados pelos exatos {gordura}% de gordura e {massa_magra}% de massa magra do paciente.
            2. Detalhe a farmacodinâmica, a cascata bioquímica e a afinidade pelos receptores.
            3. Explique as alterações fisiológicas que justificam a mudança nos sinais vitais.
            
            Após sua explicação, adicione a tag [REF] seguida de 3 referências bibliográficas reais e formatadas em ABNT.
            
            Por fim, na última linha, você DEVE retornar as novas projeções de sinais vitais OBRIGATORIAMENTE no formato exato abaixo (substituindo as letras por números inteiros):
            [FC:X, RESP:Y, PAM:Z, SPO2:W]
            """
            
            try:
                response = model.generate_content(prompt)
                texto_completo = response.text
                
                # 1. Puxa os sinais vitais de QUALQUER LUGAR do texto
                match = re.search(r"\[\s*FC:\s*(\d+).*?RESP:\s*(\d+).*?PAM:\s*(\d+).*?SPO2:\s*(\d+)\s*\]", texto_completo, re.IGNORECASE | re.DOTALL)
                
                if match:
                    st.session_state.sinais = {
                        "fc": int(match.group(1)), "resp": int(match.group(2)),
                        "pam": int(match.group(3)), "sp": int(match.group(4))
                    }
                    # Remove a tag de sinais vitais para limpar o texto final
                    texto_limpo = re.sub(r"\[\s*FC:.*?\]", "", texto_completo, flags=re.IGNORECASE | re.DOTALL).strip()
                else:
                    texto_limpo = texto_completo

                # 2. Agora sim, divide o texto entre Laudo e Referências
                if "[REF]" in texto_limpo:
                    partes = texto_limpo.split("[REF]")
                    st.session_state.ultimo_laudo = partes[0].strip()
                    st.session_state.referencias = partes[1].strip()
                else:
                    st.session_state.ultimo_laudo = texto_limpo
                    st.session_state.referencias = "Nenhuma referência ABNT gerada."

                if match:
                    st.rerun()

            except Exception as e:
                st.error(f"Erro na simulação: {e}")

    if st.session_state.ultimo_laudo:
        st.info(st.session_state.ultimo_laudo)

with aba_referencias:
    st.write(st.session_state.referencias)
