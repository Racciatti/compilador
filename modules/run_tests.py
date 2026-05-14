import os
import sys
import traceback
from utils import build_lexical, LAST_SET
from engine import RDP
from abstractions import AST, AST_Node, Token

def format_ast(node, indent=""):
    """
    Format output for the AST node and its children in a readable tree format.
    """
    lines = []
    if isinstance(node, AST_Node):
        status = node.status
        name = node.name
        lines.append(f"{indent}├── Node: {name} [Status: {status}]")
        for i, child in enumerate(node.children):
            is_last = (i == len(node.children) - 1)
            child_indent = indent + ("    " if is_last else "│   ")
            lines.extend(format_ast(child, child_indent))
    elif isinstance(node, Token):
        val = str(node.value).replace('\n', '\\n')
        lines.append(f"{indent}└── Token: <{node.name}> '{val}' (Ln: {node.lin}, Col: {node.col})")
    return lines

def main():
    test_dir = os.path.join('../source_code_tests', 'auto_tests')
    
    if not os.path.exists(test_dir):
        print(f"Diretório {test_dir} não encontrado!")
        return

    test_files = sorted([f for f in os.listdir(test_dir) if f.endswith('.txt')])
    
    for filename in test_files:
        filepath = os.path.join(test_dir, filename)
        
        print("\n\n" + "="*80)
        print(f"  RODANDO TESTE: {filename}")
        print("="*80)
        
        lexical = build_lexical()
        try:
            # We redirect stdout so we don't get flooded by prints from the engine/AST inside the loop
            old_stdout = sys.stdout
            with open(os.devnull, 'w') as f:
                sys.stdout = f
                lexical.load_source_code(filepath)
                ast = AST()
                parser = RDP(lexical, ast, LAST_SET)
                parser.parse_program()
            sys.stdout = old_stdout
            crash_free = True
            error_msg = ""
        except Exception as e:
            sys.stdout = old_stdout
            crash_free = False
            error_msg = traceback.format_exc()

        # a) Sem erros que crasharam o código
        if not crash_free:
            print(f"❌ STATUS DA EXECUÇÃO: CRASH!")
            print(f"Trackback:")
            print(error_msg)
            continue
        else:
            print(f"✅ STATUS DA EXECUÇÃO: Sucesso (sem exceptions não tratadas).")
            
        # b) Terminando no nó da AST "S" (Raiz)
        if ast.root is None:
            print("❌ VALIDAÇÃO DA AST: AST Vazia ou raiz não encontrada.")
            continue
            
        # Verifica se finalizou com a current_node apontando corretamente,
        # O parser deve terminar (na teoria) e voltar a current_node para o inicio
        # A raiz no código de vocês chama "PROGRAM" 
        root_name = ast.root.name
        
        # O nó raiz é o S (Start symbol), no nosso caso PROGRAM
        is_returning_to_s = (ast.current_node == ast.root or ast.current_node is None)
        
        print(f"✅ VALIDAÇÃO DA AST: Raiz encontrada: '{root_name}'.")
        print(f"{'✅' if is_returning_to_s else '⚠️'} Ponteiro final no nó raiz (Current: {ast.current_node.name if ast.current_node else 'None'})")

        # c) Estruturando a AST como um output compreensível
        print("\n📊 ESTRUTURA DA AST GERADA:")
        ast_output = format_ast(ast.root)
        print('\n'.join(ast_output))

        print("\n" + "-"*80)

if __name__ == '__main__':
    main()
