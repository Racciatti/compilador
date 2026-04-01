import streamlit as st
import pandas as pd
import modules.utils as ut


st.set_page_config(
    "Analisador léxico", 
    layout="centered"
)

st.title("Analisador léxico")

st.markdown(
    """
        Interface para inspecionar tokens e erros gerados pelo analisador léxico atual.
        O código é interpretado conforme o alfabeto definido pela BNF, isto é:
        inclui-se dígitos, letras, `_`, operadores, separadores e comentários.
    """
)

st.caption("Comentários de linha usam `/...` até a quebra de linha e comentários de bloco usam `{...}`.")

# Entrada
selection = st.pills(
    label="Modo de entrada",
    options=["Inserir texto", "Enviar arquivo .txt"],
    label_visibility="hidden",
)

texto_bruto = None

if selection == "Inserir texto":
    texto_bruto = st.text_area(
        label="Digite o código-fonte, para números reais, escreva com ponto(.) e não vírgula (,)",
        placeholder="Ex:\nvar1 := 10\n{ comentario }\nwrite(var1)",
        height=180,
    )
elif selection == "Enviar arquivo .txt":
    arquivo = st.file_uploader("Enviar arquivo (APENAS .TXT)", type="txt")
    if arquivo is not None:
        texto_bruto = arquivo.read().decode("utf-8")

# Botão para analisar
analisar = st.button("Analisar", width="content")

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
        tokens, erros = ut.analyze_source(texto_bruto)

        total_tokens, total_erros = st.columns(2)
        total_tokens.metric("Tokens", len(tokens))
        total_erros.metric("Erros", len(erros))

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