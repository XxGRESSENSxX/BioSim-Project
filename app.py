import streamlit as st
import google.generativeai as genai
# ... outros imports ...

# --- 1. CONFIGURAÇÕES SEGURAS ---
# Tenta pegar a chave dos Secrets do Streamlit, se não achar, usa uma string vazia
CHAVE_GEMINI = st.secrets.get("CHAVE_GEMINI", "")

if CHAVE_GEMINI:
    genai.configure(api_key=CHAVE_GEMINI)
    model = genai.GenerativeModel('models/gemini-2.5-flash')
else:
    st.error("Erro: Chave API não configurada nos Secrets do Streamlit.")

# --- 2. DESIGN (CSS) ---
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

# --- 3. SIDEBAR ---
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
    estilo = st.multiselect("Fatores de Estilo de Vida", ["Sedentário", "Ativo", "Atleta Elite", "Tabagista", "Alcoolista"])
    condicao = st.selectbox("Patologia Preexistente", ["Nenhuma", "Diabetes Tipo 1", "Diabetes Tipo 2", "HAS Estágio II", "Hipertiroidismo", "Hipotiroidismo"])

# --- 4. LAYOUT DO MONITOR ---
col_ondas, col_numeros = st.columns([2.5, 1])

with col_ondas:
    st.markdown("### Telemetria Multiparamétrica")
    plot_spot = st.empty() 

with col_numeros:
    metrics_spot = st.empty()

st.divider()

# --- 5. INTERVENÇÃO ---
st.subheader("🧪 Simulador de Fisiologia Aplicada")
c_in, c_bt = st.columns([4, 1])
intervencao = c_in.text_input("Inserir Fármaco ou Estímulo:", placeholder="Ex: Adrenalina 1mg IV")
btn_simular = c_bt.button("Simular Resposta")

laudo_area = st.empty()

# --- 6. FUNÇÃO DO MONITOR (COM TEMPO AMPLIADO) ---
def rodar_monitor():
    t_base = 0
    fc_atual = 75 
    
    while True:
        t_base += 0.05 # Reduzi o passo do tempo para a curva ser mais suave
        t = np.linspace(t_base, t_base + 5, 100)
        
        # Logica do Gemini
        if btn_simular and intervencao:
            if "key" not in st.session_state or st.session_state.key != intervencao:
                with laudo_area:
                    with st.spinner("Analisando farmacodinâmica..."):
                        p = f"Paciente {sexo}, {idade}a, {peso}kg. Condição: {condicao}. Fatores: {estilo}. Droga: {intervencao}. Laudo técnico:"
                        res = model.generate_content(p)
                        st.markdown(f'<div class="report-box">{res.text}</div>', unsafe_allow_html=True)
                        st.session_state.key = intervencao

        # Atualiza Gráfico - Ruído reduzido para ondas mais limpas
        df = pd.DataFrame({
            'Tempo': t,
            'ECG': np.sin(t * 8) + np.random.normal(0, 0.02, 100),
            'PLET': np.sin(t * 2.0) * 0.5 + 2,
            'RESP': np.sin(t * 0.6) * 0.3 + 1,
            'PAM': np.sin(t * 8) * 0.15 + 4
        }).set_index('Tempo')
        
        plot_spot.line_chart(df, color=["#00FF00", "#00FFFF", "#FFFF00", "#FFFFFF"], height=400)

        # Atualiza Números de forma bem mais lenta
        # Só tem 5% de chance de mudar a FC a cada ciclo de 0.3s
        if np.random.random() > 0.95: 
            fc_atual += np.random.choice([-1, 0, 1])
            fc_atual = max(60, min(100, fc_atual)) 

        metrics_spot.markdown(f'''
            <div class="monitor-panel">
                <div class="metric-group" style="color: #00FF00;"><div class="metric-label">ECG / FC</div><div class="metric-value">{fc_atual}</div></div>
                <div class="metric-group" style="color: #00FFFF;"><div class="metric-label">SpO2 %</div><div class="metric-value">98</div></div>
                <div class="metric-group" style="color: #FFFF00;"><div class="metric-label">RESP</div><div class="metric-value">16</div></div>
                <div class="metric-group" style="color: #FFFFFF;"><div class="metric-label">TEMP ºC</div><div class="metric-value" style="font-size: 35px;">36.8</div></div>
            </div>
        ''', unsafe_allow_html=True)
        
        # ESPAÇO DE TEMPO AUMENTADO AQUI (de 0.15 para 0.30)
        time.sleep(0.3) 

# --- 7. EXECUÇÃO ---
rodar_monitor()
