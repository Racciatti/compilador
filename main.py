import sys
import os
import io
import pandas as pd
import streamlit as st
from contextlib import redirect_stdout

# Garantir que a pasta 'modules' está no sys.path
_current_dir = os.path.dirname(os.path.abspath(__file__))
_modules_dir = os.path.join(_current_dir, "modules")
if _modules_dir not in sys.path:
    sys.path.insert(0, _modules_dir)

import modules.utils as ut
from modules.abstractions import AST, AST_Node, Token
from modules.engine import LexicalAnalyzer, RDP
from modules.utils import build_alphabet, build_symbolic_table, TOKENS_DICT, LAST_SET
from modules.diagnostics import Diagnostics
from modules.codegen import CodeGenerator
from modules.pseudomain import compilar_e_executar

# Configuração da página
st.set_page_config(
    page_title="Analisador Léxico, Sintático & Semântico - LALG",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.title("Analisador e Compilador LALG")

st.markdown(
    """
        Interface para inspecionar tokens, erros, árvore sintática e execução do compilador.
        O código é interpretado conforme o alfabeto definido pela BNF, isto é:
        inclui-se dígitos, letras, `_`, operadores, separadores e comentários.
    """
    # Talvez seja interessante colocar um botão para adicionar o 
)

st.caption("Comentários de linha usam `/...` até a quebra de linha e comentários de bloco usam `{...}`.")

# Exemplos de teste rápidos para enriquecer a experiência do usuário
EXEMPLOS_CODIGO = {
    "-- Selecionar Exemplo Próprio --": "",
    "1. Atribuição e Saída (Válido)": """program Exemplo1;
int x, y;
begin
    x := 15;
    y := x + 25;
    write(y)
end.
""",
    "2. Tipos e Atribuições Múltiplas": """program Exemplo2;
boolean b;
int n;
begin
    b := true;
    n := 42
end.
""",
    "3. Expressão Aritmética Completa": """program Exemplo3;
int a, b, res;
begin
    a := 10;
    b := 20;
    res := (a + b) * 2;
    write(res)
end.
""",
    "4. Erro Sintático Demonstrativo": """program ErroSintaxe;
begin
    x := 10 +
end.
""",
    "5. Erro Semântico (Variável não declarada)": """program ErroSemantico;
begin
    varNaoDeclarada := 100
end.
""",
}

# Entrada
selection = st.pills(
    label="Modo de entrada",
    options=["Inserir texto", "Enviar arquivo .txt"],
    label_visibility="hidden",
)

texto_bruto = None

if selection == "Inserir texto":
    col_ex, col_pad = st.columns([2, 3])
    with col_ex:
        ex_selecionado = st.selectbox(
            "Exemplos de código pré-carregados:",
            options=list(EXEMPLOS_CODIGO.keys()),
        )
    
    valor_inicial = EXEMPLOS_CODIGO[ex_selecionado]     if ex_selecionado != "-- Selecionar Exemplo Próprio --" else ""

    texto_bruto = st.text_area(
        label="Digite o código-fonte, para números reais, escreva com ponto(.) e não vírgula (,)",
        value=valor_inicial,
        placeholder="Ex:\nprogram Exemplo;\nint var1;\nbegin\nvar1 := 10;\n{ comentario }\nwrite(var1)\nend.",
        height=190,
    )
elif selection == "Enviar arquivo .txt":
    arquivo = st.file_uploader("Enviar arquivo (APENAS .TXT)", type="txt")
    if arquivo is not None:
        texto_bruto = arquivo.read().decode("utf-8")

# Botão para analisar
analisar = st.button("Analisar", width="content")


# Funções de suporte para Árvore Sintática e Tabela de Símbolos
def generate_ast_dot(ast_root):
    """Gera string DOT para visualização com Graphviz da AST."""
    if ast_root is None:
        return ""

    lines = [
        'digraph SyntaxTree {',
        '  graph [rankdir=TB, fontname="Inter, Helvetica, Arial, sans-serif", bgcolor="transparent", pad="0.3", nodesep="0.3", ranksep="0.4"];',
        '  node [fontname="Inter, Helvetica, Arial, sans-serif", fontsize=10, style="filled,rounded", shape=box, height=0.3, margin="0.1,0.05"];',
        '  edge [fontname="Inter, Helvetica, Arial, sans-serif", fontsize=9, color="#64748B", arrowsize=0.7, penwidth=1.2];',
    ]

    counter = [0]

    def traverse(node, parent_id=None):
        current_id = f"node_{counter[0]}"
        counter[0] += 1

        if isinstance(node, AST_Node):
            if node.status == "valid":
                fillcolor = "#E0F2FE"
                color = "#0284C7"
                fontcolor = "#0369A1"
            elif node.status == "error":
                fillcolor = "#FEE2E2"
                color = "#DC2626"
                fontcolor = "#991B1B"
            else:
                fillcolor = "#FEF3C7"
                color = "#D97706"
                fontcolor = "#92400E"

            label = str(node.name).replace('"', '\\"')
            lines.append(
                f'  {current_id} [label="<{label}>", fillcolor="{fillcolor}", color="{color}", fontcolor="{fontcolor}"];'
            )

            if parent_id:
                lines.append(f'  {parent_id} -> {current_id};')

            for child in node.children:
                traverse(child, current_id)

        elif isinstance(node, Token):
            fillcolor = "#DCFCE7"
            color = "#16A34A"
            fontcolor = "#15803D"
            val = (
                str(node.value)
                .replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("\n", "\\n")
            )
            label = f"{node.name}\\n\"{val}\""
            lines.append(
                f'  {current_id} [label="{label}", shape=ellipse, fillcolor="{fillcolor}", color="{color}", fontcolor="{fontcolor}"];'
            )

            if parent_id:
                lines.append(f'  {parent_id} -> {current_id};')

    traverse(ast_root)
    lines.append('}')
    return '\n'.join(lines)


def render_text_tree(node, indent="", is_last=True):
    """Gera visualização em texto ASCII hierárquico para a AST."""
    lines = []
    marker = "└── " if is_last else "├── "
    if isinstance(node, AST_Node):
        lines.append(f"{indent}{marker}<{node.name}> [{node.status}]")
        new_indent = indent + ("    " if is_last else "│   ")
        count = len(node.children)
        for i, child in enumerate(node.children):
            last_child = i == count - 1
            lines.extend(render_text_tree(child, new_indent, last_child))
    elif isinstance(node, Token):
        lines.append(
            f"{indent}{marker}Token({node.name}, '{node.value}') [L{node.lin + 1}:C{node.col + 1}]"
        )
    return lines


def render_expander_tree(node):
    """Renderiza a árvore sintática usando expansores aninhados no Streamlit."""
    if isinstance(node, AST_Node):
        expand_by_default = node.name in ["S", "PROGRAM", "BLOCK"]
        with st.expander(
            f"<{node.name}> — status: `{node.status}` ({len(node.children)} filhos)",
            expanded=expand_by_default,
        ):
            for child in node.children:
                render_expander_tree(child)
    elif isinstance(node, Token):
        st.write(
            f"🍃 **Token**: `{node.name}` | **Lexema**: `{node.value}` | *(Linha: {node.lin + 1}, Coluna: {node.col + 1})*"
        )


def serialize_symbol_table(symtable):
    """Converte entradas da SymbolicTable para DataFrame do pandas."""
    if not symtable or not hasattr(symtable, "_entries"):
        return []
    return [
        {
            "Identificador": e.identificador,
            "Categoria": e.categoria,
            "Tipo": e.tipo if e.tipo else "-",
            "Nível Escopo": e.nivel,
            "End. Relativo": e.end_relativo if e.end_relativo is not None else "-",
            "Valor": e.valor if e.valor is not None else "-",
            "Utilizada": "Sim" if e.utilizada else "Não",
            "Nº Params": e.num_params if e.num_params else "-",
        }
        for e in symtable._entries
    ]


# Renderização dos resultados quando o botão Analisar for acionado
if analisar:
    if not texto_bruto or not texto_bruto.strip():
        st.warning("Insira um texto ou envie um arquivo antes de analisar.")
    else:
        # 1 - Análise Léxica
        tokens, erros = ut.analyze_source(texto_bruto)

        # 2 - Análise Sintática & Construção da AST
        diag = Diagnostics()
        symtable = build_symbolic_table()
        cg = CodeGenerator()
        lexer = LexicalAnalyzer(build_alphabet(), TOKENS_DICT, symtable)
        lexer.set_source_code(texto_bruto)
        ast = AST()
        parser = RDP(lexer, ast, LAST_SET, symtable, diag, cg)

        buf_parse = io.StringIO()
        with redirect_stdout(buf_parse):
            try:
                parser.parse_program()
            except Exception as exc:
                diag.add("sintatica", f"[ERRO SINTÁTICO] Exceção durante o parse: {exc}")

        # 3 - Análise Semântica e Execução Completa via Pseudomain
        resultado_compilacao = compilar_e_executar(texto_bruto)

        # Interface em Abas
        tab_lexico, tab_sintatico, tab_semantico, tab_simbolos = st.tabs(
            [
                "🔤 Análise Léxica",
                "🌳 Árvore Sintática",
                "⚙️ Semântica & Execução MEPA",
                "📋 Tabela de Símbolos",
            ]
        )

        # ABA 1: ANÁLISE LÉXICA
        with tab_lexico:
            total_tokens, total_erros = st.columns(2)
            total_tokens.metric("Tokens", len(tokens))
            total_erros.metric("Erros", len(erros))

            col_analise, col_erros = st.columns(2)

            with col_analise:
                st.badge("Análise léxica", color="green")
                if tokens:
                    df_tokens = pd.DataFrame(tokens)
                    st.dataframe(df_tokens, use_container_width=True, hide_index=True)
                else:
                    st.info("Nenhum token válido encontrado.")

            with col_erros:
                st.badge("Erros", color="red")
                if erros:
                    df_erros = pd.DataFrame(erros)
                    st.dataframe(df_erros, use_container_width=True, hide_index=True)
                else:
                    st.write("Nenhum erro encontrado")

        # ABA 2: ÁRVORE SINTÁTICA
        with tab_sintatico:
            st.subheader("🌲 Árvore Sintática (AST)")

            erros_sintaticos = [
                d for d in diag.errors if d.get("fase") == "sintatica"
            ]

            if erros_sintaticos:
                st.error("Foram identificados erros sintáticos na análise:")
                for err in erros_sintaticos:
                    st.markdown(f"- **{err['mensagem']}**")
            else:
                st.success("✅ Código analisado sem erros de sintaxe!")

            if ast.root:
                viz_mode = st.radio(
                    "Modo de Visualização da Árvore:",
                    options=[
                        "🎨 Gráfico Visual (Graphviz)",
                        "🌳 Árvore Interativa (Expansores)",
                        "📄 Estrutura Textual (ASCII Tree)",
                    ],
                    horizontal=True,
                )

                if viz_mode == "🎨 Gráfico Visual (Graphviz)":
                    dot_str = generate_ast_dot(ast.root)
                    st.graphviz_chart(dot_str, use_container_width=True)
                    st.caption(
                        "Legenda: Azul = Nós Sintáticos Válidos | Verde = Tokens (Folhas) | Amarelo/Vermelho = Nós com Erros/Pendências"
                    )

                # VERIFICAR PORQUE NÃO ESTÁ FUNCIONANDO
                elif viz_mode == "🌳 Árvore Interativa (Expansores)": 
                    render_expander_tree(ast.root)

                # VERIFICAR PORQUE NÃO ESTÁ FUNCIONANDO
                elif viz_mode == "📄 Estrutura Textual (ASCII Tree)":
                    text_lines = render_text_tree(ast.root)
                    st.code("\n".join(text_lines), language="text")
            else:
                st.warning("Árvore sintática não foi gerada.")

        # ABA 3: SEMÂNTICA E EXECUÇÃO MEPA
        with tab_semantico:
            st.subheader("⚙️ Análise Semântica e Máquina Virtual MEPA")

            col_diag, col_mepa = st.columns([1, 1])

            with col_diag:
                st.markdown("##### 🔍 Diagnósticos de Compilação")
                diagnostics_list = resultado_compilacao.get("diagnostics", [])
                if diagnostics_list:
                    df_diag = pd.DataFrame(diagnostics_list)
                    st.dataframe(df_diag, use_container_width=True, hide_index=True)
                else:
                    st.success("Nenhum erro semântico ou sintático reportado.")

            with col_mepa:
                st.markdown("##### 📜 Bytecode MEPA Gerado")
                codigo_mepa = resultado_compilacao.get("codigo", [])
                if codigo_mepa:
                    df_mepa = pd.DataFrame(
                        {
                            "Linha": range(len(codigo_mepa)),
                            "Instrução MEPA": codigo_mepa,
                        }
                    )
                    st.dataframe(df_mepa, use_container_width=True, hide_index=True)
                else:
                    st.info("Nenhum código MEPA gerado.")

            st.markdown("---")
            st.markdown("##### 🚀 Saída de Execução (MEPA VM)")
            saida_vm = resultado_compilacao.get("saida", "")
            if resultado_compilacao.get("sucesso"):
                st.success("Execução finalizada com sucesso!")
                st.code(saida_vm if saida_vm else "(Execução sem saída de texto)", language="text")
            else:
                st.error("Execução interrompida devido a erros ou falta de código.")
                if saida_vm:
                    st.code(saida_vm, language="text")

        # ABA 4: TABELA DE SÍMBOLOS
        with tab_simbolos:
            st.subheader("📋 Tabela de Símbolos")
            st.markdown(
                "Visão detalhada dos identificadores, categorias, tipos e escopos mapeados pela tabela de símbolos do compilador."
            )

            simbolos_dados = serialize_symbol_table(symtable)
            if simbolos_dados:
                df_simbolos = pd.DataFrame(simbolos_dados)
                st.dataframe(df_simbolos, use_container_width=True, hide_index=True)
            else:
                st.info("Tabela de símbolos vazia.")