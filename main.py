import streamlit as st
import pandas as pd
from modules.lexical_analysis import analyze_text

st.set_page_config("Calculadora", layout="centered")

st.title("Calculadora para análise léxica")

st.markdown(
    """
    Essa é uma aplicação para análise léxica de uma calculadora simples.
    Ela não é feita para solucionar contas matemáticas, mas sim para averiguar
    a estrutura de um programa, como o alfabeto utilizado e os erros encontrados.

    **Alfabeto válido:** dígitos `0–9` e os operadores `+ - * / . ( ) espaço`
    """
)

# Entrada 
selection = st.pills(
    label="Modo de entrada",
    options=["Inserir texto", "Enviar arquivo .txt"],
    label_visibility="hidden",
)

texto_bruto: str | None = None

if selection == "Inserir texto":
    texto_bruto = st.text_area(
        label="Digite sua expressão",
        placeholder="Ex: (12 + 3.5) * 2\nPara enviar aperte CTRL+ENTER",
        height=120,
    )
elif selection == "Enviar arquivo .txt":
    arquivo = st.file_uploader("Enviar arquivo (APENAS .TXT)", type="txt")
    if arquivo is not None:
        texto_bruto = arquivo.read().decode("utf-8")

# Botão para analisar
analisar = st.button("Analisar", use_container_width=True)

# Resultado 
col_analise, col_erros = st.columns(2)

with col_analise:
    st.badge("Análise léxica", color="green")

with col_erros:
    st.badge("Erros", color="red")

if analisar:
    if not texto_bruto or not texto_bruto.strip():
        st.warning("Insira um texto ou envie um arquivo antes de analisar.")
    else:
        tokens, erros = analyze_text(texto_bruto)

        with col_analise:
            if tokens:
                df_tokens = pd.DataFrame(tokens)
                st.dataframe(df_tokens, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum token válido encontrado.")

        with col_erros:
            if erros:
                df_erros = pd.DataFrame(erros)
                st.dataframe(df_erros, use_container_width=True, hide_index=True)
            else:
                st.write("Nenhum erro encontrado")