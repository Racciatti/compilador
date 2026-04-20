from modules.grammar import Alphabet
from modules.utils import build_lexical
from modules.lexical import LexicalAnalyzer, Token
from modules.parser import RSP

if __name__ == '__main__':

    lexical = build_lexical()
    
    lexical.load_source_code()

    parser = RSP(lexical)

    parser.test_parse_program()



