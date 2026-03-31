BioSim v2.5 - Simulador Biomédico Multiespécie

O **BioSim v2.5** é um simulador *in silico* de alta fidelidade desenvolvido para a análise de interações farmacológicas em cenários clínicos humanos e veterinários. 

O sistema utiliza Inteligência Artificial Generativa integrada a uma interface de monitoramento multiparamétrico, permitindo a configuração de prontuários dinâmicos e a observação da resposta fisiológica imediata.

<p align="center">
  <video src="demo.mp4" width="100%" autoplay loop muted playsinline>
    Seu navegador não suporta este vídeo.
  </video>
</p>

## Diferenciais Técnicos
* **Biologia Comparada:** Suporte para humanos (Estatura) e animais (Porte: Mini a Gigante).
* **Sem IMC:** Substituição do Índice de Massa Corporal por parâmetros de Alometria e Geometria Corporal.
* **Monitor em Tempo Real:** Gráficos de ECG matematicamente sincronizados com a Frequência Cardíaca (FC).
* **Rigor Acadêmico:** Geração de laudos com referências bibliográficas nas normas ABNT.

## Arquitetura do Sistema
O software foi construído em **Python**, utilizando:
1. **Streamlit:** Interface de usuário e gerenciamento de estado volátil (`session_state`).
2. **NumPy:** Processamento matemático para geração de ondas fisiológicas.
3. **Regex:** Extração de dados estruturados para atualização do monitor.

Próximos Passos (v3.0)
* [ ] Implementação de banco de dados local (**SQLite**) para independência da nuvem.
* [ ] Motor de cálculo **100% Offline**.
* [ ] Encapsulamento para executável (** .exe**).

---
*Desenvolvido para fins de pesquisa e estudos de caso*
