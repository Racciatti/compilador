from grammar import Alphabet
from utils import build_lexical
from lexical import LexicalAnalyzer, Token
from parser import RSP

if __name__ == '__main__':

    lexical = build_lexical()
    
    lexical.load_source_code()

    parser = RSP(lexical)

    # parser.test_parse_program()

    successfully_parsed = parser.parse_program()

    print(successfully_parsed)



