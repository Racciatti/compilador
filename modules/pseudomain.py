from utils import build_lexical, LAST_SET
from engine import RDP
from abstractions import AST

if __name__ == '__main__':

    lexical = build_lexical()
    
    lexical.load_source_code()

    ast = AST()

    parser = RDP(lexical, ast, LAST_SET)

    # parser.test_parse_program()

    successfully_parsed = parser.parse_program()

    print(successfully_parsed)



