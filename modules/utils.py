from lexical import Alphabet, LexicalAnalyzer, Symbol, Token

TOKENS_DICT = {
    '+':    'op_sum',
    '-':    'op_sub', 
    '*':    'op_mul',
    '/':    'op_div',
    '=':    'op_eq',
    'real': 'real_number',
    'int':  'integer',
    'key':  'keyword',
    'id':   'identifier',
    ' ':    'space',
    '(':    'open_p',
    ')':    'close_p',
    ':':    'colon',
    '\n':   'new_line',
    ',':    'comma',
    ';':    'semicolon',
    '_':    'underline',
    '/':    'forward_slash',
    '<':    'smt',
    '>':    'get',
    '>=':   'geq',
    '<=':   'seq',
    '<>':   'diff',
    ':=':   'attr',
    }

ALPHABET_SYMBOLS = [
        
        # Digits
        Symbol('0', 'digit_0',      'digit'),
        Symbol('1', 'digit_1',      'digit'),
        Symbol('2', 'digit_2',      'digit'),
        Symbol('3', 'digit_3',      'digit'),
        Symbol('4', 'digit_4',      'digit'),
        Symbol('5', 'digit_5',      'digit'),
        Symbol('6', 'digit_6',      'digit'),
        Symbol('7', 'digit_7',      'digit'),
        Symbol('8', 'digit_8',      'digit'),
        Symbol('9', 'digit_9',      'digit'),

        # Characters
        Symbol("a", 'character_a',  'character'),
        Symbol("b", 'character_b',  'character'),
        Symbol("c", 'character_c',  'character'),
        Symbol("d", 'character_d',  'character'),
        Symbol("e", 'character_e',  'character'),
        Symbol("f", 'character_f',  'character'),
        Symbol("g", 'character_g',  'character'),
        Symbol("h", 'character_h',  'character'),
        Symbol("i", 'character_i',  'character'),
        Symbol("j", 'character_j',  'character'),
        Symbol("k", 'character_k',  'character'),
        Symbol("l", 'character_l',  'character'),
        Symbol("m", 'character_m',  'character'),
        Symbol("n", 'character_n',  'character'),
        Symbol("o", 'character_o',  'character'),
        Symbol("p", 'character_p',  'character'),
        Symbol("q", 'character_q',  'character'),
        Symbol("r", 'character_r',  'character'),
        Symbol("s", 'character_s',  'character'),
        Symbol("t", 'character_t',  'character'),
        Symbol("u", 'character_u',  'character'),
        Symbol("v", 'character_v',  'character'),
        Symbol("w", 'character_w',  'character'),
        Symbol("x", 'character_x',  'character'),
        Symbol("y", 'character_y',  'character'),
        Symbol("z", 'character_z',  'character'),
        Symbol("A", 'character_A',  'character'),
        Symbol("B", 'character_B',  'character'),
        Symbol("C", 'character_C',  'character'),
        Symbol("D", 'character_D',  'character'),
        Symbol("E", 'character_E',  'character'),
        Symbol("F", 'character_F',  'character'),
        Symbol("G", 'character_G',  'character'),
        Symbol("H", 'character_H',  'character'),
        Symbol("I", 'character_I',  'character'),
        Symbol("J", 'character_J',  'character'),
        Symbol("K", 'character_K',  'character'),
        Symbol("L", 'character_L',  'character'),
        Symbol("M", 'character_M',  'character'),
        Symbol("N", 'character_N',  'character'),
        Symbol("O", 'character_O',  'character'),
        Symbol("P", 'character_P',  'character'),
        Symbol("Q", 'character_Q',  'character'),
        Symbol("R", 'character_R',  'character'),
        Symbol("S", 'character_S',  'character'),
        Symbol("T", 'character_T',  'character'),
        Symbol("U", 'character_U',  'character'),
        Symbol("V", 'character_V',  'character'),
        Symbol("W", 'character_W',  'character'),
        Symbol("X", 'character_X',  'character'),
        Symbol("Y", 'character_Y',  'character'),
        Symbol("Z", 'character_Z',  'character'),
        Symbol("_", 'underline',    'character'),

        # OPERATORS
        # Arithmetic
        Symbol("+", "plus",         'operator'),
        Symbol("-", "minus",        'operator'),
        Symbol("*", "multiplier",   'operator'),

        # Relational
        Symbol('=', "equals",       'operator'),
        Symbol('<', "left_arrow",   'operator'),
        Symbol('>', "right_arrow",  'operator'),
        Symbol('(', "open_p",       'operator'),
        Symbol(')', "close_p",      'operator'),
        Symbol(':', "colon",        'operator'),
        
        # SEPARATORS
        # Ignored
        Symbol('\n',"new_line",     'separator'),
        Symbol(' ', "space",        'separator'),
        Symbol('/', "forward_slash",'separator'),
        Symbol('{', "open_b",       'separator'),
        Symbol('}', "close_b",      'separator'),

        # Tokenizeable
        Symbol(',', "comma",        'separator'),
        Symbol(';', "semicolon",    'separator'),
        Symbol('$', "eof",          'separator'),

        # MISC
        Symbol('.', "dot")

        # Eliminated
        # Symbol("/", "divider",      'operator'),
]

DISPLAY_LEXEMES = {value: key for key, value in TOKENS_DICT.items() if len(key) > 1}


def build_alphabet():
    """
        All the valid characters and thers respective tokens
    """
    symbols = [
        *(Symbol(str(number), f"digit_{number}", "digit") for number in range(10)), # o * é um empacotador (pra diminuir o tamanho do código)
        *(Symbol(letter, f"character_{letter}", "character") for letter in "abcdefghijklmnopqrstuvwxyz"),
        *(Symbol(letter, f"character_{letter}", "character") for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
        Symbol("_", "underline", "character"),
        Symbol("+", "plus", "operator"),
        Symbol("-", "minus", "operator"),
        Symbol("*", "multiplier", "operator"),
        Symbol("=", "equals", "operator"),
        Symbol("<", "left_arrow", "operator"),
        Symbol(">", "right_arrow", "operator"),
        Symbol("(", "open_p", "operator"),
        Symbol(")", "close_p", "operator"),
        Symbol(":", "colon", "operator"),
        Symbol("\n", "new_line", "separator"),
        Symbol(" ", "space", "separator"),
        Symbol("/", "forward_slash", "separator"),
        Symbol("{", "open_b", "separator"),
        ## excluir vírgula
        Symbol("}", "close_b", "separator"),
        Symbol(";", "semicolon", "separator"),
        Symbol("$", "eof", "separator"),
        Symbol(".", "dot"),
    ]
    return Alphabet(symbols)


def serialize_token(token: Token):
    """
        
    """
    lexeme = DISPLAY_LEXEMES.get(token.value, token.value)
    return {
        "token": token.name,
        "lexema": lexeme,
        "linha": token.lin + 1,
        "coluna": token.col + 1,
    }


def serialize_error(message: str):
    """
    """
    return {
        "erro": message,
        "linha": None,
        "coluna": None,
    }


def analyze_source(source_code: str):
    """
    
    (FUNCTION TO CONnECT)
    """
    analyzer = LexicalAnalyzer(build_alphabet(), tokens_dict=TOKENS_DICT)
    analyzer.set_source_code(source_code)

    tokens = []
    errors = []

    while True:
        try:
            item = analyzer.get_next_token()
        except Exception as exc:
            errors.append(serialize_error(str(exc)))
            break

        if item is None:
            break

        if isinstance(item, Token):
            tokens.append(serialize_token(item))
            continue

        errors.append(serialize_error(str(item)))
        break

    return tokens, errors