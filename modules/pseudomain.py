import io
import sys
import os
from contextlib import redirect_stdout


def compilar_e_executar(codigo_fonte: str, entrada: list = None) -> dict:
    """
    Roda o pipeline completo: léxico → sintático → semântico → codegen → interpretação.
    Retorna dict com 'diagnostics', 'saida', 'codigo' e 'sucesso'.
    """
    _modules_dir = os.path.dirname(os.path.abspath(__file__))
    if _modules_dir not in sys.path:
        sys.path.insert(0, _modules_dir)

    from abstractions import AST
    from engine import LexicalAnalyzer, RDP
    from utils import build_alphabet, build_symbolic_table, TOKENS_DICT, LAST_SET
    from diagnostics import Diagnostics
    from codegen import CodeGenerator
    from interpreter import MEPA_VM

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

    # suprime prints de debug do parser; captura erros sintáticos impressos no stdout
    buf_ruido = io.StringIO()
    with redirect_stdout(buf_ruido):
        try:
            parser.parse_program()
        except Exception as exc:
            diag.add('sintatica', f'[ERRO SINTÁTICO] Exceção durante o parse: {exc}')

    saida_parser = buf_ruido.getvalue()
    for linha_ruido in saida_parser.splitlines():
        if '[ERRO SINTÁTICO]' in linha_ruido:
            diag.add('sintatica', linha_ruido.strip())

    fases_de_erro = {'lexica', 'sintatica', 'semantica'}
    tem_erro = any(e['fase'] in fases_de_erro for e in diag.errors)

    codigo_gerado = [str(instr) for instr in cg.C]

    if tem_erro:
        return {
            'diagnostics': list(diag.errors),
            'saida': '',
            'codigo': [],
            'sucesso': False,
        }

    if parser._tem_procedure:
        return {
            'diagnostics': list(diag.errors),
            'saida': '',
            'codigo': [],
            'sucesso': False,
        }

    if not cg.C:
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
