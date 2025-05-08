import streamlit as st
st.logo('./assets/logo_horiz.png',
         size="large")

#icon_image()

st.image('./assets/head_home.png', use_container_width=True)


st.title(
    """
    Dashboard de Monitoramento do Coral Sol - PACS REBIO Arvoredo
"""
)


st.markdown(
    """
    Este painel de dados foi desenvolvido no âmbito do projeto PACS Arvoredo 
    (Plano de Ação para Prevenção e Controle do Coral Sol na REBIO Arvoredo e Entorno). Esta iniciativa 
    é uma condicionante da Licença de Operação nº 1587/2020 emitida pelo IBAMA em 07/08/2020 referente 
    ao Sistema de Desenvolvimento da Produção de Petróleo do Campo de Baúna, sob concessão da Karoon Energy, 
    e tem como objetivo gerar conhecimento científico sobre a espécie Tubastraea coccinea/coral-sol e desenvolver
    ferramentas e técnicas para a prevenção e o controle dessa espécie na REBIO Arvoredo e Entorno.

"""
)