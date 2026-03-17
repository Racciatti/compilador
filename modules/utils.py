from modules.lexical_analysis import Alphabet, LexicalAnalyzer, Symbol, Token

TOKENS_DICT = {
    "+": "op_sum",
    "-": "op_sub",
    "*": "op_mul",
    "/": "op_div",
    "=": "op_eq",
    "real": "real_number",
    "int": "integer",
    "key": "keyword",
    "id": "identifier",
    " ": "space",
    "(": "open_p",
    ")": "close_p",
    ":": "colon",
    "\n": "new_line",
    ",": "comma",
    ";": "semicolon",
    "_": "underline",
    "<": "smt",
    ">": "get",
    ">=": "geq",
    "<=": "seq",
    "<>": "diff",
    ":=": "attr",
}

DISPLAY_LEXEMES = {value: key for key, value in TOKENS_DICT.items() if len(key) > 1}


def build_alphabet():
    """
    
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
        Symbol("}", "close_b", "separator"),
        Symbol(",", "comma", "separator"),
        Symbol(";", "semicolon", "separator"),
        Symbol("$", "eof", "separator"),
        Symbol(".", "dot"),
    ]
    return Alphabet(symbols)


def serialize_token(token: Token):
    """"
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
    FUNCTION TO CONnECT
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