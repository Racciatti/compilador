"""
Pipeline principal do compilador LALG.

Ponto de entrada CLI:
  python3 modules/pseudomain.py arquivo.lalg

Função de pipeline para uso programático (testes end-to-end):
  compilar_e_executar(codigo_fonte: str, entrada: list[int] = None) -> dict

Pipeline (Seção 7 do plano):
  1. Construir léxico + tabela de símbolos pré-carregada + Diagnostics + CodeGenerator
  2. Rodar RDP.parse_program() (semântica + codegen embutidos)
  3. Se diagnostics.has_errors(): retornar com erros, sem executar
  4. Se não há erros E _tem_procedure == False: instanciar MEPA_VM e executar
  5. Se não há erros E _tem_procedure == True: retornar diagnóstico info, sem executar

Retorno de compilar_e_executar:
  {
    'diagnostics': lista de dicts {fase, mensagem, linha, coluna},
    'saida': string com a saída produzida (vazia se não executou),
    'codigo': lista de strings representando o bytecode gerado ([] se não gerado),
    'sucesso': bool (True se compilação e execução OK),
  }
"""

import io
import sys
import os
from contextlib import redirect_stdout


def compilar_e_executar(codigo_fonte: str, entrada: list = None) -> dict:
    """
    Roda o pipeline completo: léxico → sintático → semântico → codegen → interpretação.

    Parâmetros:
      codigo_fonte: código-fonte LALG como string.
      entrada: lista de inteiros para LEIT/read() (se None, lê de stdin).

    Retorna dict com:
      'diagnostics': lista de dicts {fase, mensagem, linha, coluna}
      'saida': string com a saída produzida (vazia se não executou)
      'codigo': lista de strings representando o bytecode gerado ([] se não gerado)
      'sucesso': bool (True se compilação e execução OK)
    """
    # Garante que modules/ está no sys.path quando este módulo é importado de fora
    _modules_dir = os.path.dirname(os.path.abspath(__file__))
    if _modules_dir not in sys.path:
        sys.path.insert(0, _modules_dir)

    from abstractions import AST
    from engine import LexicalAnalyzer, RDP
    from utils import build_alphabet, build_symbolic_table, TOKENS_DICT, LAST_SET
    from diagnostics import Diagnostics
    from codegen import CodeGenerator
    from interpreter import MEPA_VM

    # ------------------------------------------------------------------
    # Etapa 1: construir componentes
    # ------------------------------------------------------------------
    diag = Diagnostics()
    symtable = build_symbolic_table()
    cg = CodeGenerator()

    lexer = LexicalAnalyzer(
        alphabet=build_alphabet(),
        tokens_dict=TOKENS_DICT,
        symbolic_table=symtable,
    )
    lexer.set_source_code(codigo_fonte)

    ast = AST()
    parser = RDP(
        lexical=lexer,
        abstract_syntax_tree=ast,
        sync_table=LAST_SET,
        symbolic_table=symtable,
        diagnostics=diag,
        code_generator=cg,
    )

    # ------------------------------------------------------------------
    # Etapa 2: parse (léxico + sintático + semântico + codegen)
    # Suprime o print de debug do token que existe em engine.py (__next_token).
    # Captura stdout para detectar erros sintáticos que o RDP imprime (não registra
    # em Diagnostics) — "[ERRO SINTÁTICO]" na saída é convertido em diagnóstico.
    # ------------------------------------------------------------------
    buf_ruido = io.StringIO()
    with redirect_stdout(buf_ruido):
        try:
            parser.parse_program()
        except Exception as exc:
            # Erros de parser não tratados internamente chegam aqui como fallback.
            diag.add('sintatica', f'[ERRO SINTÁTICO] Exceção durante o parse: {exc}')

    # Converte mensagens sintáticas do stdout para entradas de diagnóstico
    saida_parser = buf_ruido.getvalue()
    for linha_ruido in saida_parser.splitlines():
        if '[ERRO SINTÁTICO]' in linha_ruido:
            diag.add('sintatica', linha_ruido.strip())

    # ------------------------------------------------------------------
    # Etapa 3: verificar diagnósticos — qualquer erro impede execução
    # ------------------------------------------------------------------
    # Erros reais são de fase 'lexica', 'sintatica' ou 'semantica'.
    # Fase 'info' e 'semantica_aviso' não bloqueiam, mas procedure bloqueia execução
    # (a flag _tem_procedure já cuidou disso na codegen — C estará vazio).
    fases_de_erro = {'lexica', 'sintatica', 'semantica'}
    tem_erro = any(e['fase'] in fases_de_erro for e in diag.errors)

    # Bytecode disponível apenas se não houve erros e não tem procedure
    codigo_gerado = [str(instr) for instr in cg.C]

    if tem_erro:
        return {
            'diagnostics': list(diag.errors),
            'saida': '',
            'codigo': [],
            'sucesso': False,
        }

    # ------------------------------------------------------------------
    # Etapa 4a: programa com procedure — informa mas não executa
    # ------------------------------------------------------------------
    if parser._tem_procedure:
        # Diagnóstico 'info' já foi adicionado pelo RDP.parse_program().
        return {
            'diagnostics': list(diag.errors),
            'saida': '',
            'codigo': [],
            'sucesso': False,
        }

    # ------------------------------------------------------------------
    # Etapa 4b: executar bytecode na MEPA_VM
    # ------------------------------------------------------------------
    if not cg.C:
        # Código vazio sem erro e sem procedure: situação inesperada; retornar sem executar.
        return {
            'diagnostics': list(diag.errors),
            'saida': '',
            'codigo': [],
            'sucesso': False,
        }

    vm = MEPA_VM()
    saida_vm = ''
    buf_stdout = io.StringIO()
    try:
        with redirect_stdout(buf_stdout):
            saida_vm = vm.executar(cg.C, entrada=entrada)
    except Exception as exc:
        diag.add('execucao', f'[ERRO DE EXECUÇÃO] {exc}')
        return {
            'diagnostics': list(diag.errors),
            'saida': '',
            'codigo': codigo_gerado,
            'sucesso': False,
        }

    return {
        'diagnostics': list(diag.errors),
        'saida': saida_vm,
        'codigo': codigo_gerado,
        'sucesso': True,
    }


# ------------------------------------------------------------------
# CLI: python3 modules/pseudomain.py arquivo.lalg
# ------------------------------------------------------------------

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Uso: python3 pseudomain.py <arquivo.lalg>')
        sys.exit(1)

    caminho = sys.argv[1]
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            fonte = f.read()
    except FileNotFoundError:
        print(f'[ERRO] Arquivo não encontrado: {caminho}')
        sys.exit(1)
    except IOError as exc:
        print(f'[ERRO] Falha ao ler o arquivo: {exc}')
        sys.exit(1)

    resultado = compilar_e_executar(fonte)

    if resultado['diagnostics']:
        print('--- Diagnósticos ---')
        for d in resultado['diagnostics']:
            linha_info = f' (linha {d["linha"]})' if d.get('linha') is not None else ''
            coluna_info = f' (coluna {d["coluna"]})' if d.get('coluna') is not None else ''
            print(f'{d["mensagem"]}{linha_info}{coluna_info}')

    if resultado['codigo']:
        print('--- Bytecode gerado ---')
        for linha in resultado['codigo']:
            print(linha)

    if resultado['saida']:
        print('--- Saída do programa ---')
        print(resultado['saida'], end='')

    if not resultado['sucesso']:
        sys.exit(1)
