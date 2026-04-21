from utils import build_lexical
from engine import RSP
from abstractions import AST

if __name__ == '__main__':

    lexical = build_lexical()
    
    lexical.load_source_code()

    ast = AST()

    parser = RSP(lexical, ast)

    # parser.test_parse_program()

    successfully_parsed = parser.parse_program()

    print(successfully_parsed)



