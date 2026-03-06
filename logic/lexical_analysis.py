# Alfabeto válido: [0-9], +, -, ., *, /
## Números e os operadores básicos + pontos
NUMS = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}

OPERATORS = {
    "+": "plus",
    "-": "minus",
    "*": "multiplier",
    "/": "divider", 
    ".": "dot",
    "(": "open_par",
    ")": "close_par",
    " ": "space"
}


def analyze_text(text):
    """
    Analisa o texto e retorna dois dicionários de listas:
      - tokens: caracteres válidos do alfabeto
      - erros: caracteres fora do alfabeto
    """
    tokens = []
    erros = []

    linha = 1
    coluna = 1

    for caracter in text:
        if caracter in ("\n", "\r"):
            if caracter == "\n":
                linha += 1
                coluna = 1
            continue

        if caracter in OPERATORS:
            tokens.append({
                "Caractere": caracter,
                "Tipo": OPERATORS[caracter],
                "Coluna": coluna,
                "Linha": linha,
            })
        elif caracter in NUMS:
            tokens.append({
                "Caractere": caracter,
                "Tipo": "inteiro",
                "Coluna": coluna,
                "Linha": linha,
            })
        else:
            erros.append({
                "Caractere": caracter,
                "Mensagem": "Fora do alfabeto",
                "Coluna": coluna,
                "Linha": linha,
            })

        coluna += 1

    return tokens, erros