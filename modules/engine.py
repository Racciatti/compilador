from abstractions import Token, AST
from formal_grammar import Alphabet
from registry import SymbolicTable, Element

RESERVED_WORDS = {
    'program', 'procedure', 'begin', 'end', 'var',
    'if', 'then', 'else', 'while', 'do',
    'div', 'and', 'or', 'not'
}

class LexicalAnalyzer:

    def __init__(self, alphabet:Alphabet, tokens_dict:dict, symbolic_table:SymbolicTable = None):

        self.symbolic_table = symbolic_table

        # Store tokens as a dict for quick comparison and access.
        self.tokens_dict = tokens_dict

        # Check if required tokens were passed
        required_token_keys = 'int real id'.split()
        for token_key in required_token_keys:
            if token_key not in self.tokens_dict:
                raise ValueError(f'The token {token_key} is required and was not provided')

        self.alphabet = alphabet

        self.pos = 0
        self.col = 0
        self.lin = 0

        self.source_code = None

    def get_next_token(self):

        if self.source_code is None:
            raise Exception('Source code was not defined')

        if self.__get_current_symbol() == '$':
            return None

        if not self.__is_current_symbol_valid():
            return self.__throw_error_for_current_symbol(f'ERROR: Symbol "{self.__get_current_symbol()}" not in alphabet')

        if self.__get_current_symbol() in ['\n', ' ', '/', '{']:

            while self.__get_current_symbol() in ['\n', ' ', '/', '{']:

                if self.__get_current_symbol() == '{':

                    self.__cursor_right()

                    while self.__get_current_symbol() != '}':

                        if self.__get_current_symbol() == '$':
                            return self.__throw_error_for_current_symbol('UNEXPECTED EOF: Expected "}" ')

                        elif self.__get_current_symbol() == '\n':
                            self.__cursor_new_line()

                        else:
                            self.__cursor_right()

                    assert self.__get_current_symbol() == '}'
                    self.__cursor_right()
                    if self.__get_current_symbol() == '$':
                        return None

                elif self.__get_current_symbol() == '/':

                    while self.__get_current_symbol() != '\n':

                        if self.__get_current_symbol() == '$':
                            return None

                        self.__cursor_right()

                    assert self.__get_current_symbol() == '\n'
                    self.__cursor_new_line()

                    if self.__get_current_symbol() == '$':
                        return None

                elif self.__get_current_symbol() in ['\n', ' ']:

                    while self.__get_current_symbol() in ['\n', ' ']:

                        if self.__get_current_symbol() == '\n':
                            self.__cursor_new_line()

                        else:
                            self.__cursor_right()

                        if self.__get_current_symbol() == '$':
                            return None

        if self.__is_current_symbol_separator():
            return self.__return_token()

        if self.__is_current_symbol_operator():

            if self.__get_current_symbol() in ['<', ':', '>']:

                self.__cursor_right()
                if self.__is_current_symbol_operator():

                    if self.source_code[self.pos-1:self.pos+1] in list(self.tokens_dict.keys()):
                        return self.__return_token(token_key=self.source_code[self.pos-1:self.pos+1], token_value=self.source_code[self.pos-1:self.pos+1])

                else:
                    self.__cursor_left()

            return self.__return_token()


        if self.__get_current_symbol() == '.':
            return self.__throw_error_for_current_symbol("ERROR: Unexpected '.'")

        if self.__is_current_symbol_character():

            initial_pos = self.pos
            initial_col = self.col

            while True:
                self.__cursor_right()

                if not (self.__is_current_symbol_digit() or self.__is_current_symbol_character()):
                    break

            self.__cursor_left()

            value = self.source_code[initial_pos:self.pos + 1]

            # Check RESERVED_WORDS directly; predeclared identifiers (int, boolean, true, false,
            # read, write) are classified as 'identifier', not 'keyword'.
            if value in RESERVED_WORDS:
                return self.__return_token(token_value=value, token_col=initial_col, token_key='key', token_lin=self.lin)

            return self.__return_token(token_value=value, token_col=initial_col, token_key='id', token_lin=self.lin)

        if self.__is_current_symbol_digit():

            initial_pos = self.pos
            initial_col = self.col

            while True:
                self.__cursor_right()

                if not self.__is_current_symbol_digit():
                    break

            if self.__is_current_symbol_separator() or self.__is_current_symbol_operator():

                self.__cursor_left()

                value = self.source_code[initial_pos:self.pos + 1]
                return self.__return_token(token_value=value, token_col=initial_col, token_key='int', token_lin=self.lin)

            elif self.__get_current_symbol() == '.':

                self.__cursor_right()

                if self.__is_current_symbol_digit():

                    while True:

                        self.__cursor_right()
                        if not self.__is_current_symbol_digit():
                            break

                    if not self.__is_current_symbol_separator():
                        return self.__throw_error_for_current_symbol(f'ERROR: real number "{self.source_code[initial_pos, self.pos+1]}" is malformed')

                    else:
                        self.__cursor_left()
                        value = self.source_code[initial_pos:self.pos + 1]
                        return self.__return_token(token_value=value, token_col=initial_col, token_key='real', token_lin=self.lin)

            else:
                return self.__throw_error_for_current_symbol(f'ERROR: number {self.source_code[initial_pos, self.pos+1]} is malformed')

            string = self.source_code[initial_pos, self.pos]

    def load_source_code(self, file_path:str = '../source_code.txt'):

        with open(file_path, 'r') as file:
            self.source_code = file.read()

        file.close()

        self.source_code = self.source_code + '$'
        self.max_pos = len(self.source_code) - 1

        print('loaded source: ')
        print('=' * 80)
        print(self.source_code)
        print('=' * 80)

    def set_source_code(self, source_code:str):
        self.source_code = source_code + '$'
        self.max_pos = len(self.source_code) - 1

    def __cursor_new_line(self):
        self.col=0
        self.lin+=1
        self.pos+=1

    def __cursor_right(self):
        self.pos+=1
        self.col+=1

    def __cursor_left(self):
        self.pos-=1
        self.col-=1

    def __is_current_symbol_digit(self)->bool:
        return self.alphabet.is_digit(self.__get_current_symbol())

    def __is_current_symbol_separator(self)->bool:
        return self.alphabet.is_separator(self.__get_current_symbol())

    def __is_current_symbol_character(self)->bool:
        return self.alphabet.is_character(self.__get_current_symbol())

    def __is_current_symbol_operator(self)->bool:
        return self.alphabet.is_operator(self.__get_current_symbol())

    def __is_current_symbol_valid(self)->bool:
        return self.alphabet.contains_symbol(self.__get_current_symbol())

    def __get_current_symbol(self)->str:
        return self.source_code[self.pos]

    def __throw_error_for_current_symbol(self, error_str:str):
        return error_str

    def __return_token(self, token_value:str = None, token_col:int = None, token_lin:int = None, token_key:str = None):
        """
        Cria e retorna o token a partir do símbolo atual ou dos argumentos passados,
        avançando o cursor.
        """

        if token_key is None:
            current_symbol = self.__get_current_symbol()
            token_name = self.tokens_dict[current_symbol]
            token_value = current_symbol
            token_col = self.col
            token_lin = self.lin
            token = Token(name=token_name, value=token_value, col=token_col, lin=token_lin)

        else:
            token_name = self.tokens_dict[token_key]
            col = self.col if token_col is None else token_col
            lin = self.lin if token_lin is None else token_lin
            value = self.tokens_dict[token_key] if token_value is None else token_value

            token = Token(name=token_name, value=value, col=col, lin=lin)


        self.__cursor_right()

        return token


class RDP:
    """
    Parser recursivo-descendente para LALG.
    Etapa 2: integra ações semânticas (verificação de tipos, escopos, diagnósticos).
    """

    def __init__(self, lexical: LexicalAnalyzer, abstract_syntax_tree: AST,
                 sync_table: dict, symbolic_table: SymbolicTable = None,
                 diagnostics=None, code_generator=None):

        self.lexical = lexical
        self.current_token = None
        self.use_cached_token = False
        self.ast = abstract_syntax_tree

        self.ast.create_root('S')

        self.sync_table = sync_table

        self.symbolic_table = symbolic_table
        self.diagnostics = diagnostics
        self.nivel_atual = 0

        self.code_generator = code_generator
        self._tem_procedure = False

    def parse_program(self):
        """PROGRAM -> 'program' id ';' BLOCK '.'"""

        self.start_parsing('PROGRAM')

        self.__next_token()

        self.__validate_current_token_value('program', 'PROGRAM')

        self.__next_token()

        if self.current_token is not None and self.current_token.name == 'identifier':
            self.__semantic_inserir_nome_prog(self.current_token)

        self.__validate_current_token_name('identifier', 'PROGRAM')

        self.__next_token()

        self.__validate_current_token_value(';', 'PROGRAM')

        if self.code_generator is not None:
            self.code_generator.gerar('INPP')

        self.__parse_block()

        self.__next_token()

        self.__validate_current_token_value('.', 'PROGRAM')

        self.__semantic_checar_nao_utilizadas(nivel=self.nivel_atual)

        if self.code_generator is not None:
            if self._tem_procedure:
                self.code_generator.C = []
                if self.diagnostics is not None:
                    self.diagnostics.add(
                        'info',
                        '[INFO] Geração de código não suportada para programas com '
                        'procedimentos. Análise semântica concluída com sucesso.'
                    )
            else:
                self.code_generator.gerar('PARA')

        self.finish_parsing()

    def __parse_block(self):
        """
        BLOCK -> VAR_DEC_SECTION SUBR_DEC_SECTION COMP_COMMAND
               | SUBR_DEC_SECTION COMP_COMMAND

        int/boolean são predeclared identifiers (token.name == 'identifier'),
        então checamos token.value diretamente.
        """

        self.start_parsing('BLOCK')

        self.__next_token()

        if self.current_token.value in {'int', 'boolean'}:

            self.__cache_token()

            self.__parse_var_dec_section()

            self.__parse_subr_dec_section()

            self.__parse_comp_command()

            self.finish_parsing()
            return

        if self.current_token.value in {'procedure', 'begin'}:
            self.__cache_token()

            self.__parse_subr_dec_section()

            self.__parse_comp_command()

            self.finish_parsing()
            return

        self.__handle_error('BLOCK')

    def __parse_var_dec_section(self):
        """VAR_DEC_SECTION -> VAR_DEC ';' VAR_DEC_SECTION_1"""

        self.start_parsing('VAR_DEC_SECTION')

        self.__parse_var_dec()

        self.__next_token()

        self.__validate_current_token_value(';', 'VAR_DEC_SECTION')

        self.__parse_var_dec_section_1()

        self.finish_parsing()

    def __parse_var_dec_section_1(self):
        """VAR_DEC_SECTION_1 -> VAR_DEC ';' VAR_DEC_SECTION_1 | ε"""

        self.__next_token()

        if self.current_token.value in {'boolean', 'int'}:

            self.__cache_token()

            self.__parse_var_dec()

            self.__next_token()

            self.__validate_current_token_value(';', 'VAR_DEC_SECTION_1')

            self.__parse_var_dec_section_1()

            return

        self.__cache_token()

    def __parse_var_dec(self):
        """VAR_DEC -> TYPE ID_LIST"""

        self.start_parsing('VAR_DEC')

        tipo = self.__parse_type()

        id_tokens = self.__parse_id_list_collecting()

        # Seção 5 do plano: AMEM 1 por variável, atribui end_relativo
        if tipo is not None:
            for id_tok in id_tokens:
                self.__semantic_inserir_var(id_tok, tipo)
                if self.code_generator is not None and not self._tem_procedure:
                    end_rel = self.code_generator.novo_end_relativo()
                    self.code_generator.gerar('AMEM', 1)
                    if self.symbolic_table is not None:
                        entry = self.symbolic_table.busca(id_tok.value)
                        if entry is not None:
                            entry.end_relativo = end_rel

        self.finish_parsing()

    def __parse_type(self) -> str:
        """TYPE -> 'int' | 'boolean' — retorna o tipo semântico"""

        self.__next_token()

        if self.current_token.value not in {'boolean', 'int'}:
            self.__handle_error('TYPE')
            return None

        self.ast.add_leaf(self.current_token)

        return 'integer' if self.current_token.value == 'int' else 'boolean'

    def __parse_id_list(self):
        """ID_LIST -> id ID_LIST_1"""

        self.start_parsing('ID_LIST')

        self.__next_token()

        self.__validate_current_token_name('identifier', 'ID_LIST')

        self.__parse_id_list_1()

        self.finish_parsing()

    def __parse_id_list_collecting(self) -> list:
        """ID_LIST -> id ID_LIST_1 — retorna lista de tokens coletados"""
        self.start_parsing('ID_LIST')

        self.__next_token()

        self.__validate_current_token_name('identifier', 'ID_LIST')

        collected = [self.current_token]

        more = self.__parse_id_list_1_collecting()
        collected.extend(more)

        self.finish_parsing()
        return collected

    def __parse_id_list_1(self):
        """ID_LIST_1 -> ',' id ID_LIST_1 | ε"""

        self.__next_token()

        if self.current_token.value == ',':

            self.ast.add_leaf(self.current_token)

            self.__next_token()

            self.__validate_current_token_name('identifier', 'ID_LIST_1')

            self.__parse_id_list_1()

            return

        self.__cache_token()

    def __parse_id_list_1_collecting(self) -> list:
        """ID_LIST_1 -> ',' id ID_LIST_1 | ε — retorna tokens adicionais"""

        self.__next_token()

        if self.current_token.value == ',':

            self.ast.add_leaf(self.current_token)

            self.__next_token()

            self.__validate_current_token_name('identifier', 'ID_LIST_1')

            collected = [self.current_token]
            more = self.__parse_id_list_1_collecting()
            collected.extend(more)
            return collected

        self.__cache_token()
        return []

    def __parse_subr_dec_section(self):
        """
        SUBR_DEC_SECTION -> PROC_DEC ';' SUBR_DEC_SECTION | ε
        Regra 6 da gramática.
        """

        self.start_parsing('SUBR_DEC_SECTION')

        self.__next_token()

        if self.current_token is not None and self.current_token.value == 'procedure':

            self.__cache_token()

            self.__parse_proc_dec()

            self.__next_token()
            self.__validate_current_token_value(';', 'SUBR_DEC_SECTION')

            self.__parse_subr_dec_section()

            self.finish_parsing()
            return

        self.__cache_token()

        self.finish_parsing()

    def __parse_proc_dec(self):
        """
        PROC_DEC -> 'procedure' id PROC_DEC_1 ';' BLOCK
        Semântica: insere nome do proc no nível atual; incrementa nível para o corpo.
        Ao sair: verifica não-utilizadas; remover_nivel; decrementa nível.
        """

        self._tem_procedure = True

        self.start_parsing('PROC_DEC')

        self.__next_token()

        self.__validate_current_token_value('procedure', 'PROC_DEC')

        self.__next_token()

        proc_name_token = self.current_token

        self.__validate_current_token_name('identifier', 'PROC_DEC')

        proc_entry = None
        if proc_name_token is not None and proc_name_token.name == 'identifier':
            proc_entry = self.__semantic_inserir_proc(proc_name_token)

        self.nivel_atual += 1

        param_tokens, param_types = self.__parse_proc_dec_1_semantic()

        if proc_entry is not None:
            proc_entry.num_params = len(param_tokens)
            proc_entry.tipos_params = param_types

        for i, p_tok in enumerate(param_tokens):
            self.__semantic_inserir_param(p_tok, param_types[i])

        self.__next_token()

        self.__validate_current_token_value(';', 'PROC_DEC')

        self.__parse_block()

        self.__semantic_checar_nao_utilizadas(nivel=self.nivel_atual)

        if self.symbolic_table is not None:
            self.symbolic_table.remover_nivel(self.nivel_atual)
        self.nivel_atual -= 1

        self.finish_parsing()

    def __parse_proc_dec_1(self):
        """PROC_DEC_1 -> FORMAL_PARAMS | ε"""

        self.__next_token()

        if self.current_token.value == '(':
            self.__cache_token()
            self.__parse_formal_params()
            return

        self.__cache_token()

    def __parse_proc_dec_1_semantic(self) -> tuple:
        """PROC_DEC_1 -> FORMAL_PARAMS | ε — retorna (param_tokens, param_types)"""
        self.__next_token()

        if self.current_token.value == '(':
            self.__cache_token()
            return self.__parse_formal_params_semantic()

        self.__cache_token()
        return [], []

    def __parse_formal_params(self):
        """FORMAL_PARAMS -> '(' FORMAL_PARAMS_SECTION FORMAL_PARAMS_1 ')'"""

        self.start_parsing('FORMAL_PARAMS')

        self.__next_token()

        self.__validate_current_token_value('(', 'FORMAL_PARAMS')

        self.__parse_formal_params_section()

        self.__parse_formal_params_1()

        self.__next_token()

        self.__validate_current_token_value(')', 'FORMAL_PARAMS')

        self.finish_parsing()

    def __parse_formal_params_semantic(self) -> tuple:
        """FORMAL_PARAMS -> '(' FORMAL_PARAMS_SECTION FORMAL_PARAMS_1 ')' — retorna (tokens, tipos)"""
        self.start_parsing('FORMAL_PARAMS')

        self.__next_token()

        self.__validate_current_token_value('(', 'FORMAL_PARAMS')

        tokens, types = self.__parse_formal_params_section_semantic()

        more_tokens, more_types = self.__parse_formal_params_1_semantic()
        tokens.extend(more_tokens)
        types.extend(more_types)

        self.__next_token()

        self.__validate_current_token_value(')', 'FORMAL_PARAMS')

        self.finish_parsing()
        return tokens, types

    def __parse_formal_params_1(self):
        """FORMAL_PARAMS_1 -> ';' FORMAL_PARAMS_SECTION FORMAL_PARAMS_1 | ε"""

        self.__next_token()

        if self.current_token.value == ';':

            self.ast.add_leaf(self.current_token)

            self.__parse_formal_params_section()

            self.__parse_formal_params_1()

            return

        self.__cache_token()

    def __parse_formal_params_1_semantic(self) -> tuple:
        """FORMAL_PARAMS_1 semântico — retorna (tokens, tipos)"""

        self.__next_token()

        if self.current_token.value == ';':

            self.ast.add_leaf(self.current_token)

            tokens, types = self.__parse_formal_params_section_semantic()

            more_tokens, more_types = self.__parse_formal_params_1_semantic()
            tokens.extend(more_tokens)
            types.extend(more_types)
            return tokens, types

        self.__cache_token()
        return [], []

    def __parse_formal_params_section(self):
        """FORMAL_PARAMS_SECTION -> ['var'] ID_LIST ':' id"""

        self.start_parsing('FORMAL_PARAMS_SECTION')

        self.__next_token()

        if not self.current_token.value == 'var':
            self.__cache_token()

        else:
            self.ast.add_leaf(self.current_token)

        self.__parse_id_list()

        self.__next_token()

        self.__validate_current_token_value(':', 'FORMAL_PARAMS_SECTION')

        self.__next_token()

        self.__validate_current_token_name('identifier', 'FORMAL_PARAMS_SECTION')

        self.finish_parsing()

    def __parse_formal_params_section_semantic(self) -> tuple:
        """FORMAL_PARAMS_SECTION -> ['var'] ID_LIST ':' id — retorna (param_tokens, param_types)"""
        self.start_parsing('FORMAL_PARAMS_SECTION')

        self.__next_token()

        if not self.current_token.value == 'var':
            self.__cache_token()
        else:
            self.ast.add_leaf(self.current_token)

        param_tokens = self.__parse_id_list_collecting()

        self.__next_token()

        self.__validate_current_token_value(':', 'FORMAL_PARAMS_SECTION')

        self.__next_token()

        type_name_tok = self.current_token
        self.__validate_current_token_name('identifier', 'FORMAL_PARAMS_SECTION')

        param_tipo = None
        if type_name_tok is not None:
            if type_name_tok.value == 'int':
                param_tipo = 'integer'
            elif type_name_tok.value == 'boolean':
                param_tipo = 'boolean'
            else:
                self.__semantic_erro(
                    f'[ERRO SEMÂNTICO] Tipo desconhecido "{type_name_tok.value}" em declaração de parâmetros',
                    type_name_tok.lin, type_name_tok.col
                )

        param_types = [param_tipo] * len(param_tokens)

        self.finish_parsing()
        return param_tokens, param_types

    def __parse_comp_command(self):
        """COMP_COMMAND -> 'begin' COMMAND COMP_COMMAND_1 'end'"""

        self.start_parsing('COMP_COMMAND')

        self.__next_token()

        self.__validate_current_token_value('begin', 'COMP_COMMAND')

        self.__parse_command()

        self.__parse_comp_command_1()

        self.__next_token()

        self.__validate_current_token_value('end', 'COMP_COMMAND')

        self.finish_parsing()

    def __parse_comp_command_1(self):
        """COMP_COMMAND_1 -> ';' COMMAND COMP_COMMAND_1 | ε"""

        self.__next_token()

        if self.current_token is not None and self.current_token.value == ';':
            self.ast.add_leaf(self.current_token)
            self.__parse_command()
            self.__parse_comp_command_1()
            return

        self.__cache_token()

    def __parse_command(self):
        """
        COMMAND -> id CMD_ATTR_TAIL
                 | COND_COMMAND
                 | ITER_COMMAND
                 | COMP_COMMAND
        """

        self.start_parsing('COMMAND')

        self.__next_token()

        if self.current_token.name == 'identifier':
            id_token = self.current_token
            self.ast.add_leaf(self.current_token)
            self.__parse_cmd_attr_tail(id_token)
            self.finish_parsing()
            return

        self.__cache_token()

        if self.current_token.value == 'if':
            self.__parse_cond_command()
            self.finish_parsing()
            return

        if self.current_token.value == 'while':
            self.__parse_iter_command()
            self.finish_parsing()
            return

        if self.current_token.value == 'begin':
            self.__parse_comp_command()
            self.finish_parsing()
            return

        self.__handle_error('COMMAND')

    def __parse_cmd_attr_tail(self, id_token=None):
        """CMD_ATTR_TAIL -> ATTR_TAIL | PROC_CALL_TAIL"""

        self.__next_token()

        self.__cache_token()

        if self.current_token.value in {'[', ':='}:
            self.__parse_attr_tail(id_token)
            return

        self.__parse_proc_call_tail(id_token)

    def __parse_attr_tail(self, id_token=None):
        """
        ATTR_TAIL -> '[' EXPR ']' ':=' EXPR | ':=' EXPR
        Regra 5: tipo da var deve bater com o da expr.
        Regra 11: indexação de vetor não suportada.
        """

        self.start_parsing('ATTR')

        self.__next_token()

        if self.current_token.value == '[':

            self.ast.add_leaf(self.current_token)

            if id_token is not None:
                self.__semantic_erro(
                    '[ERRO SEMÂNTICO] Vetores não são suportados pela LALG',
                    id_token.lin, id_token.col
                )

            self.__parse_expr()

            self.__next_token()

            self.__validate_current_token_value(']', 'ATTR_TAIL')

            self.__next_token()

            self.__validate_current_token_value(':=', 'ATTR_TAIL')

            self.__parse_expr()

            self.finish_parsing()

            return

        if self.current_token.value == ':=':

            self.ast.add_leaf(self.current_token)

            var_tipo = None
            var_end_relativo = None
            if id_token is not None and self.symbolic_table is not None:
                entry = self.symbolic_table.busca(id_token.value)
                if entry is None:
                    self.__semantic_erro(
                        f'[ERRO SEMÂNTICO] Identificador não declarado: "{id_token.value}"',
                        id_token.lin, id_token.col
                    )
                else:
                    var_tipo = entry.tipo
                    var_end_relativo = entry.end_relativo
                    self.symbolic_table.marcar_utilizada(id_token.value)

            expr_tipo = self.__parse_expr()

            # Regra 5: verificação de tipo na atribuição
            if var_tipo is not None and expr_tipo is not None and var_tipo != expr_tipo:
                self.__semantic_erro(
                    f'[ERRO SEMÂNTICO] Atribuição com tipos incompatíveis: '
                    f'variável "{id_token.value}" é "{var_tipo}", '
                    f'mas a expressão é "{expr_tipo}"',
                    id_token.lin if id_token else None,
                    id_token.col if id_token else None
                )

            # Seção 5 do plano: ARMZ <end_relativo> após gerar código da EXPR
            if self.code_generator is not None and var_end_relativo is not None:
                self.code_generator.gerar('ARMZ', var_end_relativo)

            self.finish_parsing()
            return

        self.__handle_error('ATTR_TAIL')

    def __parse_expr(self) -> str:
        """EXPR -> SIMPLE_EXPR EXPR_1 — retorna o tipo computado"""
        self.start_parsing('EXPR')

        left_tipo = self.__parse_simple_expr()

        result_tipo = self.__parse_expr_1(left_tipo)

        self.finish_parsing()
        return result_tipo if result_tipo is not None else left_tipo

    def __parse_expr_1(self, left_tipo: str = None) -> str:
        """
        EXPR_1 -> REL SIMPLE_EXPR | ε
        REL -> '=' | '<>' | '<' | '<=' | '>=' | '>'
        Regra 6: tipos dos operandos devem ser compatíveis.
        """

        self.__next_token()

        if self.current_token.value in {'=', '<>', '<', '<=', '>=', '>'}:
            rel_op = self.current_token.value
            rel_token = self.current_token
            self.ast.add_leaf(self.current_token)

            right_tipo = self.__parse_simple_expr()

            # '=' e '<>' aceitam integer×integer ou boolean×boolean
            # '<', '<=', '>', '>=' exigem integer×integer
            if left_tipo is not None and right_tipo is not None:
                if rel_op in {'=', '<>'}:
                    if left_tipo != right_tipo:
                        self.__semantic_erro(
                            f'[ERRO SEMÂNTICO] Operador "{rel_op}" requer operandos do mesmo tipo '
                            f'(recebeu "{left_tipo}" e "{right_tipo}")',
                            rel_token.lin, rel_token.col
                        )
                else:
                    if left_tipo != 'integer' or right_tipo != 'integer':
                        self.__semantic_erro(
                            f'[ERRO SEMÂNTICO] Operador "{rel_op}" requer operandos do tipo "integer" '
                            f'(recebeu "{left_tipo}" e "{right_tipo}")',
                            rel_token.lin, rel_token.col
                        )

            # Seção 5 do plano: instrução de comparação
            if self.code_generator is not None:
                _rel_mepa = {
                    '=':  'CMIG',
                    '<>': 'CMDG',
                    '<':  'CMME',
                    '<=': 'CMEG',
                    '>':  'CMMA',
                    '>=': 'CMAG',
                }
                self.code_generator.gerar(_rel_mepa[rel_op])

            return 'boolean'

        self.__cache_token()
        return None

    def __parse_simple_expr(self) -> str:
        """
        SIMPLE_EXPR -> ['+' | '-'] TERM SIMPLE_EXPR_1
        Semântica: '-' unário exige 'integer'.
        """

        self.start_parsing('SIMPLE_EXPR')

        unary_op = None
        unary_token = None

        self.__next_token()

        if self.current_token.value in {'+', '-'}:
            unary_op = self.current_token.value
            unary_token = self.current_token
            self.ast.add_leaf(self.current_token)
        else:
            self.__cache_token()

        term_tipo = self.__parse_term()

        if unary_op == '-' and term_tipo is not None and term_tipo != 'integer':
            self.__semantic_erro(
                '[ERRO SEMÂNTICO] Operador unário "-" requer operando do tipo "integer"',
                unary_token.lin if unary_token else None,
                unary_token.col if unary_token else None
            )

        # Seção 5 do plano: INVR após o termo se houver menos unário
        if unary_op == '-' and self.code_generator is not None:
            self.code_generator.gerar('INVR')

        result_tipo = self.__parse_simple_expr_1(term_tipo)

        self.finish_parsing()
        return result_tipo if result_tipo is not None else term_tipo

    def __parse_simple_expr_1(self, left_tipo: str = None) -> str:
        """
        SIMPLE_EXPR_1 -> ('+' | '-' | 'or') TERM | ε
        Regra 6: '+'/'-' exigem 'integer'; 'or' exige 'boolean'.
        """

        self.__next_token()

        if self.current_token.value in {'or', '+', '-'}:
            op = self.current_token.value
            op_token = self.current_token
            self.ast.add_leaf(self.current_token)

            right_tipo = self.__parse_term()

            expected = 'integer' if op in {'+', '-'} else 'boolean'

            if left_tipo is not None and left_tipo != expected:
                self.__semantic_erro(
                    f'[ERRO SEMÂNTICO] Operador "{op}" requer operandos do tipo "{expected}" '
                    f'(recebeu "{left_tipo}")',
                    op_token.lin, op_token.col
                )
            if right_tipo is not None and right_tipo != expected:
                self.__semantic_erro(
                    f'[ERRO SEMÂNTICO] Operador "{op}" requer operandos do tipo "{expected}" '
                    f'(recebeu "{right_tipo}")',
                    op_token.lin, op_token.col
                )

            # Seção 5 do plano
            if self.code_generator is not None:
                _op_mepa = {'+': 'SOMA', '-': 'SUBT', 'or': 'DISJ'}
                self.code_generator.gerar(_op_mepa[op])

            return expected

        self.__cache_token()
        return None

    def __parse_term(self) -> str:
        """TERM -> FACTOR TERM_1"""
        self.start_parsing('TERM')

        factor_tipo = self.__parse_factor()

        result_tipo = self.__parse_term_1(factor_tipo)

        self.finish_parsing()
        return result_tipo if result_tipo is not None else factor_tipo

    def __parse_term_1(self, left_tipo: str = None) -> str:
        """
        TERM_1 -> ('*' | 'div' | 'and') FACTOR | ε
        Regra 6: '*'/'div' exigem 'integer'; 'and' exige 'boolean'.
        """

        self.__next_token()

        if self.current_token.value in {'*', 'div', 'and'}:
            op = self.current_token.value
            op_token = self.current_token
            self.ast.add_leaf(self.current_token)

            right_tipo = self.__parse_factor()

            expected = 'integer' if op in {'*', 'div'} else 'boolean'

            if left_tipo is not None and left_tipo != expected:
                self.__semantic_erro(
                    f'[ERRO SEMÂNTICO] Operador "{op}" requer operandos do tipo "{expected}" '
                    f'(recebeu "{left_tipo}")',
                    op_token.lin, op_token.col
                )
            if right_tipo is not None and right_tipo != expected:
                self.__semantic_erro(
                    f'[ERRO SEMÂNTICO] Operador "{op}" requer operandos do tipo "{expected}" '
                    f'(recebeu "{right_tipo}")',
                    op_token.lin, op_token.col
                )

            # Seção 5 do plano
            if self.code_generator is not None:
                _op_mepa = {'*': 'MULT', 'div': 'DIVI', 'and': 'CONJ'}
                self.code_generator.gerar(_op_mepa[op])

            return expected

        self.__cache_token()
        return None

    def __parse_factor(self) -> str:
        """
        FACTOR -> 'true' | 'false'
                | id VAR_TAIL
                | '(' EXPR ')'
                | 'not' FACTOR
                | integer_literal
                | real_literal  (erro semântico: não suportado)
        """

        self.start_parsing('FACTOR')

        self.__next_token()

        # Seção 5 do plano: CRCT 1 / CRCT 0
        if self.current_token.value in {'true', 'false'}:
            self.ast.add_leaf(self.current_token)
            if self.symbolic_table is not None:
                self.symbolic_table.marcar_utilizada(self.current_token.value)
            if self.code_generator is not None:
                valor_bool = 1 if self.current_token.value == 'true' else 0
                self.code_generator.gerar('CRCT', valor_bool)
            self.finish_parsing()
            return 'boolean'

        # Seção 5 do plano: CRVL <end_relativo>
        if self.current_token.name == 'identifier':
            id_token = self.current_token
            self.__cache_token()
            self.__parse_var()
            tipo = None
            end_relativo = None
            if self.symbolic_table is not None:
                entry = self.symbolic_table.busca(id_token.value)
                if entry is None:
                    self.__semantic_erro(
                        f'[ERRO SEMÂNTICO] Identificador não declarado: "{id_token.value}"',
                        id_token.lin, id_token.col
                    )
                else:
                    tipo = entry.tipo
                    end_relativo = entry.end_relativo
                    self.symbolic_table.marcar_utilizada(id_token.value)
            if self.code_generator is not None and end_relativo is not None:
                self.code_generator.gerar('CRVL', end_relativo)
            self.finish_parsing()
            return tipo

        if self.current_token.value == '(':
            self.ast.add_leaf(self.current_token)
            inner_tipo = self.__parse_expr()
            self.__next_token()
            self.__validate_current_token_value(')', 'FACTOR')
            self.finish_parsing()
            return inner_tipo

        # Seção 5 do plano: NEGA após o fator recursivo
        if self.current_token.value == 'not':
            not_token = self.current_token
            self.ast.add_leaf(self.current_token)
            factor_tipo = self.__parse_factor()
            if factor_tipo is not None and factor_tipo != 'boolean':
                self.__semantic_erro(
                    '[ERRO SEMÂNTICO] Operador "not" requer operando do tipo "boolean" '
                    f'(recebeu "{factor_tipo}")',
                    not_token.lin, not_token.col
                )
            if self.code_generator is not None:
                self.code_generator.gerar('NEGA')
            self.finish_parsing()
            return 'boolean'

        # Regra 12: reais não suportados
        if self.current_token.name == 'real_number':
            self.__semantic_erro(
                '[ERRO SEMÂNTICO] Números reais não são suportados pela LALG',
                self.current_token.lin, self.current_token.col
            )
            self.ast.add_leaf(self.current_token)
            self.finish_parsing()
            return None

        # Seção 5 do plano: CRCT <valor>
        lit_token = self.current_token
        self.__validate_current_token_name('integer', 'FACTOR')
        if self.code_generator is not None and lit_token is not None:
            self.code_generator.gerar('CRCT', int(lit_token.value))

        self.finish_parsing()
        return 'integer'

    def __parse_proc_call_tail(self, id_token=None):
        """
        PROC_CALL_TAIL -> '(' EXPR_LIST ')' | ε
        Regras 3, 8, 9: valida argumentos do proc.
        Seção 5 do plano:
          - read: LEIT + ARMZ por variável
          - write: IMPR por expressão; IMPE ao final
        """

        self.start_parsing('PROC_CALL')

        self.__next_token()

        if self.current_token.value == '(':

            self.ast.add_leaf(self.current_token)

            proc_name = id_token.value if id_token is not None else None

            if self.code_generator is not None and proc_name in {'read', 'write'}:
                arg_exprs = self.__parse_expr_list_collecting_com_codegen(proc_name)
                if proc_name == 'write':
                    self.code_generator.gerar('IMPE')
            else:
                arg_exprs = self.__parse_expr_list_collecting()

            self.__next_token()

            self.__validate_current_token_value(')', 'PROC_CALL_TAIL')

            if id_token is not None and self.symbolic_table is not None:
                self.__semantic_validar_chamada_proc(id_token, arg_exprs)

            self.finish_parsing()

            return

        self.__cache_token()

        if id_token is not None and self.symbolic_table is not None:
            entry = self.symbolic_table.busca(id_token.value)
            if entry is None:
                self.__semantic_erro(
                    f'[ERRO SEMÂNTICO] Identificador não declarado: "{id_token.value}"',
                    id_token.lin, id_token.col
                )
            elif entry.categoria == 'proc':
                self.symbolic_table.marcar_utilizada(id_token.value)

        self.finish_parsing()

    def __parse_cond_command(self):
        """
        COND_COMMAND -> 'if' EXPR 'then' COMMAND COND_COMMAND_1
        Regra 7: condição deve ser 'boolean'.
        Seção 5 do plano:
          sem else: DSVF p reservado; gera C1; back-patch p → próximo índice
          com else: DSVF p1; gera C1; DSVS p2; back-patch p1; gera C2; back-patch p2
        """

        self.start_parsing('COND_COMMAND')

        self.__next_token()

        self.__validate_current_token_value('if', 'COND_COMMAND')

        cond_tipo = self.__parse_expr()

        if cond_tipo is not None and cond_tipo != 'boolean':
            self.__semantic_erro(
                f'[ERRO SEMÂNTICO] Condição do "if" deve ser do tipo "boolean" '
                f'(recebeu "{cond_tipo}")',
                self.lexical.lin, self.lexical.col
            )

        pos_dsvf = None
        if self.code_generator is not None:
            pos_dsvf = self.code_generator.gerar('DSVF', None)

        self.__next_token()

        self.__validate_current_token_value('then', 'COND_COMMAND')

        self.__parse_command()

        self.__parse_cond_command_1(pos_dsvf)

        self.finish_parsing()

    def __parse_cond_command_1(self, pos_dsvf=None):
        """
        COND_COMMAND_1 -> 'else' COMMAND | ε
        Seção 5 do plano: back-patch dos desvios do if/else.
        """

        self.__next_token()

        if self.current_token.value == 'else':

            self.ast.add_leaf(self.current_token)

            pos_dsvs = None
            if self.code_generator is not None:
                pos_dsvs = self.code_generator.gerar('DSVS', None)
                if pos_dsvf is not None:
                    self.code_generator.back_patch(pos_dsvf, self.code_generator.proximo_indice())

            self.__parse_command()

            if self.code_generator is not None and pos_dsvs is not None:
                self.code_generator.back_patch(pos_dsvs, self.code_generator.proximo_indice())

            self.__cache_token()
            return

        if self.code_generator is not None and pos_dsvf is not None:
            self.code_generator.back_patch(pos_dsvf, self.code_generator.proximo_indice())

        self.__cache_token()

    def __parse_iter_command(self):
        """
        ITER_COMMAND -> 'while' EXPR 'do' COMMAND
        Regra 7: condição deve ser 'boolean'.
        Seção 5 do plano: marca inicio; DSVF p reservado; gera C; DSVS inicio; back-patch p
        """

        self.start_parsing('ITER_COMMAND')

        self.__next_token()

        self.__validate_current_token_value('while', 'ITER_COMMAND')

        inicio = None
        if self.code_generator is not None:
            inicio = self.code_generator.proximo_indice()

        cond_tipo = self.__parse_expr()

        if cond_tipo is not None and cond_tipo != 'boolean':
            self.__semantic_erro(
                f'[ERRO SEMÂNTICO] Condição do "while" deve ser do tipo "boolean" '
                f'(recebeu "{cond_tipo}")',
                self.lexical.lin, self.lexical.col
            )

        pos_dsvf = None
        if self.code_generator is not None:
            pos_dsvf = self.code_generator.gerar('DSVF', None)

        self.__next_token()

        self.__validate_current_token_value('do', 'ITER_COMMAND')

        self.__parse_command()

        if self.code_generator is not None:
            self.code_generator.gerar('DSVS', inicio)
            if pos_dsvf is not None:
                self.code_generator.back_patch(pos_dsvf, self.code_generator.proximo_indice())

        self.finish_parsing()

    def __parse_var(self):
        """VAR -> id VAR_TAIL"""

        self.start_parsing('VAR')

        self.__next_token()

        self.__validate_current_token_name('identifier', 'VAR')

        self.__parse_var_tail()

        self.finish_parsing()

    def __parse_var_tail(self):
        """VAR_TAIL -> '[' EXPR ']' | ε — regra 11: vetores não suportados"""

        self.__next_token()

        if self.current_token.value == '[':

            self.ast.add_leaf(self.current_token)

            self.__semantic_erro(
                '[ERRO SEMÂNTICO] Vetores não são suportados pela LALG',
                self.current_token.lin, self.current_token.col
            )

            self.__parse_expr()

            self.__next_token()

            self.__validate_current_token_value(']', 'VAR_TAIL')

            return

        self.__cache_token()

    def __parse_expr_list(self):
        """EXPR_LIST -> EXPR EXPR_LIST_1"""

        self.start_parsing('EXPR_LIST')

        self.__parse_expr()

        self.__parse_expr_list_1()

        self.finish_parsing()

    def __parse_expr_list_collecting(self) -> list:
        """EXPR_LIST -> EXPR EXPR_LIST_1 — retorna lista de dicts {tipo, lin, col}"""
        self.start_parsing('EXPR_LIST')

        lin = self.lexical.lin
        col = self.lexical.col
        tipo = self.__parse_expr()
        results = [{'tipo': tipo, 'lin': lin, 'col': col}]

        more = self.__parse_expr_list_1_collecting()
        results.extend(more)

        self.finish_parsing()
        return results

    def __parse_expr_list_1(self):
        """EXPR_LIST_1 -> ',' EXPR EXPR_LIST_1 | ε"""

        self.__next_token()

        if self.current_token.value == ',':

            self.ast.add_leaf(self.current_token)

            self.__parse_expr()

            self.__parse_expr_list_1()

            return

        self.__cache_token()

    def __parse_expr_list_1_collecting(self) -> list:
        """EXPR_LIST_1 semântico — retorna lista de dicts {tipo, lin, col}"""

        self.__next_token()

        if self.current_token.value == ',':

            self.ast.add_leaf(self.current_token)

            lin = self.lexical.lin
            col = self.lexical.col
            tipo = self.__parse_expr()
            results = [{'tipo': tipo, 'lin': lin, 'col': col}]

            more = self.__parse_expr_list_1_collecting()
            results.extend(more)
            return results

        self.__cache_token()
        return []

    def __parse_expr_list_collecting_com_codegen(self, proc_name: str) -> list:
        """
        EXPR_LIST -> EXPR EXPR_LIST_1 — variante para read/write.
        Intercala instrução MEPA após cada expressão (Seção 5 do plano).
        """
        self.start_parsing('EXPR_LIST')

        lin = self.lexical.lin
        col = self.lexical.col
        tipo = self.__parse_expr()
        self.__codegen_pos_arg_builtin(proc_name, tipo)
        results = [{'tipo': tipo, 'lin': lin, 'col': col}]

        more = self.__parse_expr_list_1_collecting_com_codegen(proc_name)
        results.extend(more)

        self.finish_parsing()
        return results

    def __parse_expr_list_1_collecting_com_codegen(self, proc_name: str) -> list:
        """EXPR_LIST_1 -> ',' EXPR EXPR_LIST_1 | ε — variante com codegen para read/write"""
        self.__next_token()

        if self.current_token.value == ',':

            self.ast.add_leaf(self.current_token)

            lin = self.lexical.lin
            col = self.lexical.col
            tipo = self.__parse_expr()
            self.__codegen_pos_arg_builtin(proc_name, tipo)
            results = [{'tipo': tipo, 'lin': lin, 'col': col}]

            more = self.__parse_expr_list_1_collecting_com_codegen(proc_name)
            results.extend(more)
            return results

        self.__cache_token()
        return []

    def __codegen_pos_arg_builtin(self, proc_name: str, tipo: str):
        """
        Emite instrução MEPA após cada argumento de read/write (Seção 5 do plano).
        - write: IMPR por expressão.
        - read: remove o CRVL gerado pela expressão, emite LEIT + ARMZ.
        """
        if self.code_generator is None:
            return

        if proc_name == 'write':
            self.code_generator.gerar('IMPR')

        elif proc_name == 'read':
            # a expressão (identificador) gerou CRVL <end_rel> — substituímos por LEIT + ARMZ
            if self.code_generator.C:
                ultima = self.code_generator.C[-1]
                if ultima.op == 'CRVL' and ultima.arg is not None:
                    end_rel = ultima.arg
                    self.code_generator.C.pop()
                    self.code_generator.gerar('LEIT')
                    self.code_generator.gerar('ARMZ', end_rel)

    def __semantic_erro(self, mensagem: str, linha: int = None, coluna: int = None):
        if self.diagnostics is not None:
            self.diagnostics.add('semantica', mensagem, linha, coluna)
        else:
            print(mensagem)

    def __semantic_inserir_nome_prog(self, token: Token):
        if self.symbolic_table is None:
            return
        self.symbolic_table.inserir(Element(
            identificador=token.value,
            categoria='nome_prog',
            nivel=self.nivel_atual,
        ))

    def __semantic_inserir_var(self, token: Token, tipo: str):
        """Regra 2: erro se já declarado no mesmo nível."""
        if self.symbolic_table is None:
            return
        existing = self.symbolic_table.busca_nivel_atual(token.value, self.nivel_atual)
        if existing is not None:
            self.__semantic_erro(
                f'[ERRO SEMÂNTICO] Identificador já declarado no escopo atual: "{token.value}"',
                token.lin, token.col
            )
            return
        self.symbolic_table.inserir(Element(
            identificador=token.value,
            categoria='var',
            tipo=tipo,
            nivel=self.nivel_atual,
        ))

    def __semantic_inserir_proc(self, token: Token):
        """Regra 2: erro se já declarado no mesmo nível. Retorna o Element inserido."""
        if self.symbolic_table is None:
            return None
        existing = self.symbolic_table.busca_nivel_atual(token.value, self.nivel_atual)
        if existing is not None:
            self.__semantic_erro(
                f'[ERRO SEMÂNTICO] Identificador já declarado no escopo atual: "{token.value}"',
                token.lin, token.col
            )
            return None
        entry = Element(
            identificador=token.value,
            categoria='proc',
            nivel=self.nivel_atual,
        )
        self.symbolic_table.inserir(entry)
        return entry

    def __semantic_inserir_param(self, token: Token, tipo: str):
        """Regra 2: erro se já declarado no mesmo nível."""
        if self.symbolic_table is None:
            return
        existing = self.symbolic_table.busca_nivel_atual(token.value, self.nivel_atual)
        if existing is not None:
            self.__semantic_erro(
                f'[ERRO SEMÂNTICO] Identificador já declarado no escopo atual: "{token.value}"',
                token.lin, token.col
            )
            return
        self.symbolic_table.inserir(Element(
            identificador=token.value,
            categoria='param',
            tipo=tipo,
            nivel=self.nivel_atual,
        ))

    def __semantic_checar_nao_utilizadas(self, nivel: int):
        """Regra 10: avisa sobre vars/params declarados e nunca usados no nível dado."""
        if self.symbolic_table is None:
            return
        for entry in self.symbolic_table._entries:
            if entry.nivel != nivel:
                continue
            if entry.categoria not in {'var', 'param'}:
                continue
            if not entry.utilizada:
                msg = (
                    f'[AVISO SEMÂNTICO] Variável "{entry.identificador}" '
                    f'declarada e nunca utilizada'
                )
                if self.diagnostics is not None:
                    self.diagnostics.add('semantica_aviso', msg)
                else:
                    print(msg)

    def __semantic_validar_chamada_proc(self, id_token: Token, arg_exprs: list):
        """
        Valida chamada de procedimento.
        Regra 1: proc deve estar declarado.
        Regra 3: número e tipos dos argumentos devem bater (não-builtins).
        Regra 8: args de read() devem ser variáveis inteiras.
        Regra 9: args de write() devem ser expressões inteiras.
        """
        if self.symbolic_table is None:
            return

        entry = self.symbolic_table.busca(id_token.value)
        if entry is None:
            self.__semantic_erro(
                f'[ERRO SEMÂNTICO] Identificador não declarado: "{id_token.value}"',
                id_token.lin, id_token.col
            )
            return

        if entry.categoria != 'proc':
            self.__semantic_erro(
                f'[ERRO SEMÂNTICO] "{id_token.value}" não é um procedimento',
                id_token.lin, id_token.col
            )
            return

        self.symbolic_table.marcar_utilizada(id_token.value)

        if id_token.value == 'read':
            for arg in arg_exprs:
                if arg['tipo'] is not None and arg['tipo'] != 'integer':
                    self.__semantic_erro(
                        f'[ERRO SEMÂNTICO] Argumento de "read" deve ser uma variável inteira '
                        f'(recebeu tipo "{arg["tipo"]}")',
                        arg['lin'], arg['col']
                    )
            return

        if id_token.value == 'write':
            for arg in arg_exprs:
                if arg['tipo'] is not None and arg['tipo'] != 'integer':
                    self.__semantic_erro(
                        f'[ERRO SEMÂNTICO] Argumento de "write" deve ser uma expressão inteira '
                        f'(recebeu tipo "{arg["tipo"]}")',
                        arg['lin'], arg['col']
                    )
            return

        # proc não-builtin: regra 3
        num_args = len(arg_exprs)
        if num_args != entry.num_params:
            self.__semantic_erro(
                f'[ERRO SEMÂNTICO] Chamada a "{id_token.value}" com número incorreto de argumentos: '
                f'esperado {entry.num_params}, recebeu {num_args}',
                id_token.lin, id_token.col
            )
            return

        for i, arg in enumerate(arg_exprs):
            expected_tipo = entry.tipos_params[i] if i < len(entry.tipos_params) else None
            if expected_tipo is not None and arg['tipo'] is not None and arg['tipo'] != expected_tipo:
                self.__semantic_erro(
                    f'[ERRO SEMÂNTICO] Argumento {i+1} de "{id_token.value}" tem tipo incorreto: '
                    f'esperado "{expected_tipo}", recebeu "{arg["tipo"]}"',
                    arg['lin'], arg['col']
                )

    def __cache_token(self):
        # Method created merely for interpretability
        self.use_cached_token = True

    def __validate_current_token_value(self, value:str, non_terminal:str):

        if self.current_token is None or self.current_token.value != value:
            self.__handle_error(non_terminal)
            return

        self.ast.add_leaf(self.current_token)

    def __validate_current_token_name(self, name:str, non_terminal:str):
        if self.current_token is None or self.current_token.name != name:
            self.__handle_error(non_terminal)
            return

        self.ast.add_leaf(self.current_token)

    def __next_token(self):
        """
        Pega o próximo token do analisador léxico.
        Se use_cached_token for True, reutiliza o token atual.
        """
        if not self.use_cached_token:
            self.current_token = self.lexical.get_next_token()
            print(self.current_token.__str__())
            return

        self.use_cached_token = False


    # AST methods
    def start_parsing(self, name:str):
        self.ast.add_node(name)

    def finish_parsing(self):
        self.ast.validate_current_node()

    def validate_token(self, token:Token):
        self.ast.add_leaf(token)


    def __handle_error(self, non_terminal:str):

        sync_tokens = self.sync_table.get(non_terminal) or set()

        token_value = self.current_token.value if self.current_token is not None else 'EOF'

        print(
            "[ERRO SINTÁTICO]"
            f"Localização: ({self.lexical.lin},{self.lexical.col})"
            f"Token inesperado '{token_value}' em <{non_terminal}>. "
            f"Tokens de sincronização: {sync_tokens}"
        )

        while self.current_token is not None:
            if self.current_token.value in sync_tokens:
                break
            self.current_token = self.lexical.get_next_token()


    def test___parse_program(self):

        while True:

            self.__next_token()

            print(self.current_token.__str__())

            if self.current_token is None:
                return
