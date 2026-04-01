"""
Analisador Sintático para Declaração de Variáveis

Gramática suportada:
    declaracoes_var -> 'var' decl_linha {decl_linha}
    decl_linha -> id {',' id} ':' tipo ';'(declaração de tipo)
                + id ':=' inteiro ';' (atribuição de valor inteiro)
    tipos_aceitos -> 'int' | 'boolean'

Tokens relevantes (name -> value):
    identifier : qualquer id ou palavra-reservada
    colon:   ':'
    attr : ':='
    semicolon : ';' (delimitador)
    integer : literal inteiro (ex: 10, 42)
"""

# Para o futuro
KEYWORDS = {
    "program", "procedure", "begin", "end",
    "read", "write", "var",
    "if", "then", "else",
    "while", "do",
    "int", "boolean",
    "true", "false",
    "not", "and", "or",
}

VALID_TYPES = {"int", "boolean"}


class SyntaxError_:
    """
    Representa um erro sintático 
    Não pode ser 'exception' porque não pode interromper o fluxo
    """
    def __init__(self, message: str, lin: int = None, col: int = None):
        self.message = message
        self.lin = lin
        self.col = col

    def __str__(self):
        if self.lin is not None:
            return f"{self.message} (linha {self.lin}, coluna {self.col})"
        return self.message


class VarDeclarationParser:
    """
    Parser de declarações de variáveis:
    recebe a lista de objetos Token do analisador léxico e verifica se
    o bloco de declaração de variáveis está sintaticamente correto

    Gramática:
        var id {, id} : tipo (declaração de tipo)
            id ':=' inteiro  (atribuição de valor inteiro)
    """

    def __init__(self, tokens: list):
        # Remove tokens sem relevância sintática, como espaço
        self._tokens = [
            t for t in tokens
            if t.name not in {"space", "new_line"}
        ]
        self._pos = 0

    # acesso ao token atual 

    @property
    def _current(self):
        return self._tokens[self._pos] if self._pos < len(self._tokens) else None

    def _advance(self):
        t = self._current
        self._pos += 1
        return t

    def _is_keyword(self, word: str) -> bool:
        t = self._current
        return t is not None and t.name == "identifier" and t.value == word

    # ponto de entrada 

    def parse(self) -> list:
        """
        Retorna lista de erros sintáticos encontrados
        OBS: Lista vazia significa código correto
        """
        errors = []

        if self._current is None:
            errors.append(SyntaxError_("Entrada vazia."))
            return errors

        # Espera 'var'
        if not self._is_keyword("var"):
            t = self._current
            errors.append(SyntaxError_(
                f'Esperado "var", encontrado "{t.value}".',
                t.lin + 1, t.col + 1,
            ))
            return errors

        self._advance()  # consome 'var'

        # deve existir ao menos uma linha de declaração
        if self._current is None or (
            self._current.name == "identifier"
            and self._current.value in KEYWORDS
            and self._current.value not in VALID_TYPES
        ):
            errors.append(SyntaxError_("Esperado ao menos uma declaração após 'var'."))
            return errors

        # lê todas as linhas de declaração
        while self._current is not None:
            line_errors = self._parse_decl_line()
            errors.extend(line_errors)

            # se houve erro, tenta recuperar avançando até o próximo ';'
            if line_errors:
                while self._current is not None and self._current.name != "semicolon":
                    self._advance()
                if self._current is not None:
                    self._advance()  # consome ';' de recuperação

            # para se o próximo token não parece início de nova declaração
            if self._current is None:
                break
            if self._current.name != "identifier":
                break
            if self._current.value in KEYWORDS and self._current.value not in VALID_TYPES:
                break

        return errors

    # regra: decl_linha (foi exposta no começo)

    def _parse_decl_line(self) -> list:
        """
        Analisa uma linha, que pode ser:
          - Declaração de tipo: id {, id} : tipo ;
          - Atribuição de valor: id := inteiro ;
        """
        errors = []

        # identifier - id 
        err = self._expect_id()
        if err:
            errors.append(err)
            return errors

        if self._current is None:
            errors.append(SyntaxError_('Esperado ":" ou ":=" após identificador, mas a entrada terminou.'))
            return errors

        # Bifurcação: atribuição (':=') ou declaração de tipo (':') 

        if self._current.name == "attr":
            ## 1° opção: id := inteiro ;
            self._advance()  # consome ':='

            err = self._expect_integer()
            if err:
                errors.append(err)
                return errors

        else:
            ## 2° opção: id {, id} : tipo ;
            # {, id} 
            while self._current is not None and self._current.value == ",":
                self._advance()  # consome ','
                err = self._expect_id()
                if err:
                    errors.append(err)
                    return errors

            # ':' -> declaração
            if self._current is None:
                errors.append(SyntaxError_('Esperado ":" após lista de identificadores, mas a entrada terminou.'))
                return errors

            if self._current.name != "colon":
                t = self._current
                errors.append(SyntaxError_(
                    f'Esperado ":" ou ":=", encontrado "{t.value}".',
                    t.lin + 1, t.col + 1,
                ))
                return errors

            self._advance()  # consome ':'

            # tipo 
            err = self._expect_type()
            if err:
                errors.append(err)
                return errors

        # ';' (comum aos dois caminhos já que é delimitador) 
        if self._current is None:
            errors.append(SyntaxError_('Esperado ";" ao final da declaração, mas a entrada terminou.'))
            return errors

        if self._current.name != "semicolon":
            t = self._current
            errors.append(SyntaxError_(
                f'Esperado ";" ao final da declaração, encontrado "{t.value}".',
                t.lin + 1, t.col + 1,
            ))
            return errors

        self._advance()  # consome ';'
        return errors

    # funções auxiliares 

    def _expect_id(self):
        """
        Consome um identificador comum, retornando erro se falhar
        """
        t = self._current
        if t is None:
            return SyntaxError_("Esperado identificador, mas a entrada terminou.")
        if t.name != "identifier":
            return SyntaxError_(
                f'Esperado identificador, encontrado "{t.value}" ({t.name}).',
                t.lin + 1, t.col + 1,
            )
        if t.value in KEYWORDS and t.value not in VALID_TYPES:
            return SyntaxError_(
                f'"{t.value}" é palavra reservada e não pode ser usada como identificador.',
                t.lin + 1, t.col + 1,
            )
        self._advance()
        return None

    def _expect_type(self):
        """
        Consome 'int' ou 'boolean'
        """
        t = self._current
        if t is None:
            return SyntaxError_('Esperado tipo ("int" ou "boolean"), mas a entrada terminou.')
        if t.name != "identifier" or t.value not in VALID_TYPES:
            return SyntaxError_(
                f'Tipo inválido: "{t.value}". Use "int" ou "boolean".',
                t.lin + 1, t.col + 1,
            )
        self._advance()
        return None

    def _expect_integer(self):
        """
        Consome um literal inteiro
        """

        t = self._current
        if t is None:
            return SyntaxError_('Esperado valor inteiro após ":=", mas a entrada terminou.')
        if t.name != "integer":
            return SyntaxError_(
                f'Esperado valor inteiro após ":=", encontrado "{t.value}".'
                + (' (números reais não são suportados na atribuição)' if t.name == 'real_number' else ''),
                t.lin + 1, t.col + 1,
            )
        self._advance()
        return None


# função de análise em si

def analyze_var_declarations(tokens: list) -> list:
    """
    Ponto de entrada: recebe a lista de Token e retorna lista de SyntaxError_.
    """
    parser = VarDeclarationParser(tokens)
    return parser.parse()