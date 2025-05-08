import streamlit as st

st.set_page_config(page_title="Sobre", page_icon="📃")
st.logo('./assets/logo_horiz.png', size="large")

st.image('./assets/head_sobre.png', use_container_width=True)


st.markdown(

"""    
## Visão Geral
Um dashboard é uma ferramenta incrivelmente valiosa que permite aos usuários visualizar e compreender dados complexos 
de forma simples. Ao atuar como uma centralização de dados processados, ele apresenta uma riqueza de métricas essenciais, 
tendências em um formato visualmente atraente e intuitivo. Isso o torna uma solução ideal para agências ambientais que 
buscam adquirir recursos valiosos para a Detecção Precoce - Resposta Rápida (EDRR) de espécies invasoras. Nesta documentação, 
exploraremos os componentes fundamentais da interpretação de dados no Dashboard de Monitoramento 
do Coral-Sol - PACS REBIO Arvoredo. 

## Protocolo de Monitoramento

### Aquisição das informações em campo
Os dados de monitoramento são obtidos em localidades, onde é definido um segmento, e na extensão de um segmento são coletadas informações 
relacionadas a transectos a cada minuto.

"""
)

st.image('./assets/local_segmento_dash.png', caption='Esquema de monitoramento de localidades', use_container_width=True)




st.markdown(
"""    
### Busca ativa

**Snorkeling** 

Na faixa de profundidade de zero a 2 metros do segmento de amostragem, o monitoramento será 
realizado por um mergulhador de snorkeling. O mergulhador buscará dentro dessa faixa de profundidade, cobrindo o 
segmento de amostragem e procurando possíveis ocorrências de coral-sol.

**Mergulho Autônomo (SCUBA)**  

As amostras de mergulho autônomo serão conduzidas por dois pares de mergulhadores. A área operacional para cada par será 
determinada por faixas de profundidade (por exemplo, de 0 a 8m e de 9 a 15m) ao longo da costa rochosa, visando cobrir a
maior extensão vertical possível. A divisão das profundidades de varredura entre os pares pode variar dependendo das 
características batimétricas de cada segmento de amostragem.

"""
)

st.image('./assets/monitora_dash.png', caption='Esquema operacional da busca ativa', use_container_width=True)


st.markdown(
"""
### DAFOR
Para classificar os níveis de invasão nos segmentos amostrados, utilizamos uma escala semi-quantitativa de abundância conhecida como escala DAFOR (Sutherland, 2006), especificamente adaptada para avaliar a abundância de coral-sol (Creed & Fleury, 2009). A escala atribui valores a cada classe de abundância relativa, que são descritas da seguinte forma:

**Dominante:** Esta categoria representa populações altamente evidentes que formam predominantemente manchas monoespecíficas de pelo menos 1m². Essas manchas contêm numerosas colônias isoladas e/ou manchas menores espalhadas pelo substrato.

**Abundante:** Os agrupamentos nesta categoria formam manchas essencialmente monoespecíficas variando de 50 a 100 cm de diâmetro. Semelhante à categoria dominante, colônias isoladas e/ou pequenas manchas espalhadas podem ser observadas ao longo do substrato.

**Frequente:** Esta classe inclui colônias isoladas e/ou pequenas manchas variando de 10 a 50 cm de diâmetro, espalhadas pelo substrato.

**Ocasional:** Aqui, temos menos de 10 colônias ou pequenas manchas menores que 10 cm de diâmetro, mas com mais de 5 colônias espalhadas pelo substrato.

**Raro:** Esta categoria abrange casos em que entre 1 e 5 colônias estão dispersas pelo substrato.

**Ausente:** Nesta classe, não são encontrados registros de ocorrências de coral-sol.
Durante o processo de avaliação, os mergulhadores se deslocam ao longo de transectos delimitados por 1 minuto de amostragem. As observações feitas na escala DAFOR são então convertidas para um índice de abundância relativa (RAI) usando a seguinte classificação: 10 - dominante, 8 - abundante, 6 - frequente, 4 - ocasional, 2 - raro; zero - ausente.
"""
)

st.image('./assets/dafor_eng.png', caption='Escala DAFOR para cálculo de IAR (Creed et al. 2025 - in press)', use_container_width=True)



st.markdown(
"""
### Indicadores
em contrução
"""
)
    
st.markdown(

"""
### Camadas
em contrução

"""
)



st.markdown(
"""
### Referências e links úteis

CREED, et al.2025. A bioinvasão do Coral-Sol. in press

CREED, J.C.; FLEURY, B.G. 2009. Monitoramento extensivo de coral-sol (Tubastraea coccinea e T. tagusensis): protocolo de semi-quantificação. Projeto Coral-Sol, Instituto Biodiversidade Marinha, Rio de Janeiro. p 1.

CREED JC; JUNQUEIRA ADOR, FLEURY BG, MANTELLATO MC, OIGMAN-PSZCZOL SS. 2017. The Sun-Coral Project: the first social-environmental initiative to manage the biological invasion of Tubastraea spp. in Brazil. Management of Biological Invasions 8(2): 181.

CREED JC, FENNER D, SAMMARCO P, CAIRNS S, CAPEL K., JUNQUEIRA AO, CRUZ I, MIRANDA RJ, CARLOS-JUNIORL, MANTELLATO MC, OIGMAN-PSZCZOL, S. 2017. The invasion of the azooxanthellate coral Tubastraea (Scleractinia: Dendrophylliidae) throughout the world: history, pathways and vectors. Biological Invasions 19: 283-305.

CRISP, DJ; SOUTHWARD, AJ. 1958. The distribution of intertidal organisms along the coasts of the English Channel. Journal of the Marine Biological Association UK 37: 157-208.

GRAINGER, S.; MAO, F.; BUYTAERT, W. 2016. Environmental data visualisation for non-scientific contexts: Literature review and design framework. Environmental Modelling & Software, 85, 299-318.

SILVEIRA, T.C.L.; CARVALHAL, A.; SEGAL, B. 2023. Protocolo Técnico de monitoramento de coral-sol na REBIO Arvoredo e entorno. In: Protocolos Técnicos de Campo. PACS Arvoredo. Projeto PACS Arvoredo. Florianópolis, 56 p.

SUTHERLAND, W. J. (Ed.). 2006. Ecological census techniques: a handbook. Cambridge university press.
"""
)