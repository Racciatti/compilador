# Alfabeto válido: [0-9], +, -, ., *, /
## Números e os operadores básicos + pontos
NUMS = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}
# NUMS = [0,1,2,3,4,5,6,7,8,9]

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

def read_text(text):
    linha = 1
    coluna = 1

    for caracter in text: 
        if caracter == "\n":
            linha += 1

        if caracter in OPERATORS:
            print(f"O caracter lido foi: {caracter} -> {OPERATORS[caracter]}")
            print(f"Caractere lido na coluna {coluna} - linha: {linha}\n")
        elif caracter in NUMS:
            numero = int(caracter)
            print(f"O digito lido foi: {numero} -> number")
            print(f"Caractere lido na coluna {coluna} - linha: {linha}\n")     
        else:
            print(f"CARACTERE INVÁLIDO")    

        coluna += 1


teste = input("Digite algo: ")
read_text(teste)


# Ler texto de fora (primeira ideia de usar open)
## Depois com a interface trocar o "lorem.txt" pelo o que o usuário colocar
# with open("lorem.txt", "r") as file: 
#     content = file.read()
#     read_text(content)