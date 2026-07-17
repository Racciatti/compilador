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

        # The alphabet the lexical analyzer will be based upon
        self.alphabet = alphabet

        # Current cursor position
        self.pos = 0

        # The current line and column of the cursor
        self.col = 0
        self.lin = 0

        self.source_code = None

    def get_next_token(self):

        if self.source_code is None:
            raise Exception('Source code was not defined')

        # If we reached EOF, return None
        if self.__get_current_symbol() == '$':
            return None

        # If the current symbol doesn't belong to the alphabet
        if not self.__is_current_symbol_valid():

            # Return an error
            return self.__throw_error_for_current_symbol(f'ERROR: Symbol "{self.__get_current_symbol()}" not in alphabet')

        # If it is a symbol that must be ignored (comments or non-token separators)
        if self.__get_current_symbol() in ['\n', ' ', '/', '{']:

            # While we run into symbols that must be ignored
            while self.__get_current_symbol() in ['\n', ' ', '/', '{']:

                # If it is a multiple line comment, ignore everything until we find a closing bracket
                if self.__get_current_symbol() == '{':

                    self.__cursor_right()

                    while self.__get_current_symbol() != '}':

                        # If we reach the end of the file prior to reaching the end of the comment
                        if self.__get_current_symbol() == '$':
                            return self.__throw_error_for_current_symbol('UNEXPECTED EOF: Expected "}" ')

                        # Otherwise, keep moving the cursor
                        elif self.__get_current_symbol() == '\n':
                            self.__cursor_new_line()

                        else:
                            self.__cursor_right()

                    # Validate we found the closing brackets

                    assert self.__get_current_symbol() == '}'
                    self.__cursor_right()
                    if self.__get_current_symbol() == '$':
                        return None

                # If it is a single line comment, ignore everything until we find a newline character
                elif self.__get_current_symbol() == '/':


                    while self.__get_current_symbol() != '\n':

                        if self.__get_current_symbol() == '$':
                            return None

                        self.__cursor_right()

                    # Validate we found a new_line character
                    assert self.__get_current_symbol() == '\n'
                    self.__cursor_new_line()

                    if self.__get_current_symbol() == '$':
                        return None


                # If we have standard separators
                elif self.__get_current_symbol() in ['\n', ' ']:

                    # While we have separators, keep discarding them and moving the cursor
                    while self.__get_current_symbol() in ['\n', ' ']:

                        if self.__get_current_symbol() == '\n':
                            self.__cursor_new_line()

                        else:
                            self.__cursor_right()

                        if self.__get_current_symbol() == '$':
                            return None

        # If after the separators that must be ignored we still have a separator
        if self.__is_current_symbol_separator():

            # Then it is a one-symbol token that can be directly returned (',', ';')
            return self.__return_token()

        # If we have an operator
        if self.__is_current_symbol_operator():

            # If it can be a token that allows for more than one symbol in the operator
            if self.__get_current_symbol() in ['<', ':', '>']:

                # If the next symbol is also an operator
                self.__cursor_right()
                if self.__is_current_symbol_operator():

                    # Check if that is indeed a two-symbol operator
                    if self.source_code[self.pos-1:self.pos+1] in list(self.tokens_dict.keys()):

                        # If it is, return its token
                        return self.__return_token(token_key=self.source_code[self.pos-1:self.pos+1], token_value=self.source_code[self.pos-1:self.pos+1])

                else:
                    self.__cursor_left()

            # Otherwise, return the first symbol's token
            return self.__return_token()


        if self.__get_current_symbol() == '.':
            return self.__throw_error_for_current_symbol("ERROR: Unexpected '.'")

        # If it starts with a character, it has to be an identifier or keyword
        if self.__is_current_symbol_character():


            # Regardless of the token type, this has to be a sequence of characters and digits. Once we find a separator, we got the string
            initial_pos = self.pos
            initial_col = self.col

            # While we go through characters and digits, update the cursor position and the source_code index
            while True:
                self.__cursor_right()

                # Once we find a separator, stop incrementing
                if not (self.__is_current_symbol_digit() or self.__is_current_symbol_character()):
                    break

            self.__cursor_left()

            value = self.source_code[initial_pos:self.pos + 1]

            # Check RESERVED_WORDS directly; predeclared identifiers (int, boolean, true, false,
            # read, write) are classified as 'identifier', not 'keyword'.
            if value in RESERVED_WORDS:
                return self.__return_token(token_value=value, token_col=initial_col, token_key='key', token_lin=self.lin)

            # Otherwise, return an identifier token
            return self.__return_token(token_value=value, token_col=initial_col, token_key='id', token_lin=self.lin)

        # If it starts with a number, it has to be a real number or an integer
        if self.__is_current_symbol_digit():


            # Regardless of the token type, this has to be a sequence of digits
            initial_pos = self.pos
            initial_col = self.col

            # While we go through digits, update the cursor position and the source_code index
            while True:
                self.__cursor_right()

                # Once we find something that is not a digit, stop incrementing
                if not self.__is_current_symbol_digit():
                    break

            # If we have a separator or an operator, this is an integer
            if self.__is_current_symbol_separator() or self.__is_current_symbol_operator():

                self.__cursor_left()

                value = self.source_code[initial_pos:self.pos + 1]
                return self.__return_token(token_value=value, token_col=initial_col, token_key='int', token_lin=self.lin)

            # If we have a dot, this has to be a real number
            elif self.__get_current_symbol() == '.':

                # In order to validate the real number, we increment and check if we have a number after the dot

                self.__cursor_right()

                # If we do have at least one digit
                if self.__is_current_symbol_digit():

                    # all symbols after the initial digit must be a digit until we find a separator
                    while True:

                        self.__cursor_right()
                        if not self.__is_current_symbol_digit():
                            break

                    # If after the stream of numbers we do not have a separator
                    if not self.__is_current_symbol_separator():
                        return self.__throw_error_for_current_symbol(f'ERROR: real number "{self.source_code[initial_pos, self.pos+1]}" is malformed')

                    # Otherwise, this is a valid real number
                    else:
                        self.__cursor_left()
                        value = self.source_code[initial_pos:self.pos + 1]
                        return self.__return_token(token_value=value, token_col=initial_col, token_key='real', token_lin=self.lin)

            # If it is neither a separator nor a dot, this is a malformation (characters after a number)
            else:
                return self.__throw_error_for_current_symbol(f'ERROR: number {self.source_code[initial_pos, self.pos+1]} is malformed')

            # Get the string
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

    # Update cursor position
    def __cursor_new_line(self):
        self.col=0
        self.lin+=1
        self.pos+=1

    # Update cursor position
    def __cursor_right(self):
        self.pos+=1
        self.col+=1

    # Update cursor position
    def __cursor_left(self):
        self.pos-=1
        self.col-=1

    # Check symbol type
    def __is_current_symbol_digit(self)->bool:
        return self.alphabet.is_digit(self.__get_current_symbol())

    # Check symbol type
    def __is_current_symbol_separator(self)->bool:
        return self.alphabet.is_separator(self.__get_current_symbol())

    # Check symbol type
    def __is_current_symbol_character(self)->bool:
        return self.alphabet.is_character(self.__get_current_symbol())

    # Check symbol type
    def __is_current_symbol_operator(self)->bool:
        return self.alphabet.is_operator(self.__get_current_symbol())

    # Validate symbols' existence
    def __is_current_symbol_valid(self)->bool:
        return self.alphabet.contains_symbol(self.__get_current_symbol())

    # Return the symbol under the cursor
    def __get_current_symbol(self)->str:
        """
        Returns the symbol under the cursor
        """
        return self.source_code[self.pos]

    # We'll probably need something more elaborate here, so the method has already been created
    def __throw_error_for_current_symbol(self, error_str:str):
        return error_str

    def __return_token(self, token_value:str = None, token_col:int = None, token_lin:int = None, token_key:str = None):
        """
        Use the symbol under the cursor or passed arguments to create a token and return it,
        whilst also moving the cursor.
        """

        # If the token key is merely the symbol in which the cursor is on right now, set token attributes based on cursor position
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
    Recursive-descent parser for LALG.
    Etapa 2: integrates semantic actions (type checking, scope management, diagnostics).
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

        # Semantic analysis support (Etapa 2)
        self.symbolic_table = symbolic_table
        self.diagnostics = diagnostics
        self.nivel_atual = 0  # current scope level

        # Code generation support (Etapa 3)
        self.code_generator = code_generator
        self._tem_procedure = False  # set to True on first PROC_DEC; disables codegen

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def parse_program(self):
        """PROGRAM -> 'program' id ';' BLOCK '.'"""

        self.start_parsing('PROGRAM')

        self.__next_token()

        self.__validate_current_token_value('program', 'PROGRAM')

        self.__next_token()

        # Semantic: register program name in the symbolic table
        if self.current_token is not None and self.current_token.name == 'identifier':
            self.__semantic_inserir_nome_prog(self.current_token)

        self.__validate_current_token_name('identifier', 'PROGRAM')

        self.__next_token()

        self.__validate_current_token_value(';', 'PROGRAM')

        # Codegen: emit INPP before parsing the block (Seção 5 do plano)
        if self.code_generator is not None:
            self.code_generator.gerar('INPP')

        self.__parse_block()

        self.__next_token()

        self.__validate_current_token_value('.', 'PROGRAM')

        # Semantic: warn about unused variables at program level (nivel 0 user vars)
        # Predeclared identifiers at nivel 0 are excluded (categoria != 'var'/'param')
        self.__semantic_checar_nao_utilizadas(nivel=self.nivel_atual)

        # Codegen: emit PARA after consuming '.', or abort if program has procedures
        if self.code_generator is not None:
            if self._tem_procedure:
                # Abort generation: discard any partial code generated and record info
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

    # ------------------------------------------------------------------
    # Block structure
    # ------------------------------------------------------------------

    def __parse_block(self):
        """
        BLOCK -> VAR_DEC_SECTION SUBR_DEC_SECTION COMP_COMMAND
               | SUBR_DEC_SECTION COMP_COMMAND

        int/boolean are now predeclared identifiers (token.name == 'identifier'),
        so we check token.value directly instead of token.name == 'keyword'.
        """

        self.start_parsing('BLOCK')

        self.__next_token()

        if self.current_token.value in {'int', 'boolean'}:

            # Since we got a token but did not consume it, set the use_cached_token flag to true
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

        # Collect identifiers for semantic insertion
        id_tokens = self.__parse_id_list_collecting()

        # Semantic: insert each identifier into the symbolic table
        # Codegen: emit AMEM 1 per variable and assign end_relativo (Seção 5 do plano)
        if tipo is not None:
            for id_tok in id_tokens:
                self.__semantic_inserir_var(id_tok, tipo)
                if self.code_generator is not None and not self._tem_procedure:
                    end_rel = self.code_generator.novo_end_relativo()
                    self.code_generator.gerar('AMEM', 1)
                    # Grava end_relativo na entrada da tabela de símbolos
                    if self.symbolic_table is not None:
                        entry = self.symbolic_table.busca(id_tok.value)
                        if entry is not None:
                            entry.end_relativo = end_rel

        self.finish_parsing()

    def __parse_type(self) -> str:
        """TYPE -> 'int' | 'boolean' — returns semantic type string"""

        self.__next_token()

        if self.current_token.value not in {'boolean', 'int'}:
            self.__handle_error('TYPE')
            return None

        self.ast.add_leaf(self.current_token)

        # Map lexeme to semantic type
        return 'integer' if self.current_token.value == 'int' else 'boolean'

    def __parse_id_list(self):
        """ID_LIST -> id ID_LIST_1 (original, for backward compatibility)"""

        self.start_parsing('ID_LIST')

        self.__next_token()

        self.__validate_current_token_name('identifier', 'ID_LIST')

        self.__parse_id_list_1()

        self.finish_parsing()

    def __parse_id_list_collecting(self) -> list:
        """
        ID_LIST -> id ID_LIST_1
        Returns list of identifier tokens collected (for semantic insertion).
        Also builds the AST normally.
        """
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

        # If the peek token is not consumed, we need to use it again later on
        self.__cache_token()

    def __parse_id_list_1_collecting(self) -> list:
        """ID_LIST_1 -> ',' id ID_LIST_1 | ε — returns list of additional id tokens"""

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
        Grammar rule 6: SUBR_DEC_SECTION -> PROC_DEC; SUBR_DEC_SECTION | ε
        """

        self.start_parsing('SUBR_DEC_SECTION')

        self.__next_token()

        if self.current_token is not None and self.current_token.value == 'procedure':

            self.__cache_token()

            self.__parse_proc_dec()

            # Consume the ';' that separates procedures (SUBR_DEC_SECTION grammar rule)
            self.__next_token()
            self.__validate_current_token_value(';', 'SUBR_DEC_SECTION')

            # Recurse for additional procedure declarations
            self.__parse_subr_dec_section()

            self.finish_parsing()
            return

        self.__cache_token()

        self.finish_parsing()

    def __parse_proc_dec(self):
        """
        PROC_DEC -> 'procedure' id PROC_DEC_1 ';' BLOCK
        Semantic: insert proc name in current level; then increment level for body.
        On exit: check unused vars in the closing level; remover_nivel; decrement level.
        Codegen: sets _tem_procedure = True; generation is aborted in parse_program.
        """

        # Codegen: flag that this program contains a procedure (Seção 5 / Decisão 2)
        self._tem_procedure = True

        self.start_parsing('PROC_DEC')

        self.__next_token()

        self.__validate_current_token_value('procedure', 'PROC_DEC')

        self.__next_token()

        proc_name_token = self.current_token

        self.__validate_current_token_name('identifier', 'PROC_DEC')

        # Semantic: insert procedure name at current level before incrementing
        proc_entry = None
        if proc_name_token is not None and proc_name_token.name == 'identifier':
            proc_entry = self.__semantic_inserir_proc(proc_name_token)

        # Increment level to parse parameters and body
        self.nivel_atual += 1

        # Parse optional formal parameters (collects param info for proc_entry)
        param_tokens, param_types = self.__parse_proc_dec_1_semantic()

        # Update proc entry with param info
        if proc_entry is not None:
            proc_entry.num_params = len(param_tokens)
            proc_entry.tipos_params = param_types

        # Insert formal params into the symbolic table at the new (incremented) level
        for i, p_tok in enumerate(param_tokens):
            self.__semantic_inserir_param(p_tok, param_types[i])

        self.__next_token()

        self.__validate_current_token_value(';', 'PROC_DEC')

        self.__parse_block()

        # Semantic: check unused variables declared in this scope before closing it
        self.__semantic_checar_nao_utilizadas(nivel=self.nivel_atual)

        # Semantic: close scope
        if self.symbolic_table is not None:
            self.symbolic_table.remover_nivel(self.nivel_atual)
        self.nivel_atual -= 1

        self.finish_parsing()

    def __parse_proc_dec_1(self):
        """PROC_DEC_1 -> FORMAL_PARAMS | ε"""

        self.__next_token()

        # Check if there are formal params in the procedure declaration
        if self.current_token.value == '(':
            self.__cache_token()
            self.__parse_formal_params()
            return

        self.__cache_token()

    def __parse_proc_dec_1_semantic(self) -> tuple:
        """
        PROC_DEC_1 -> FORMAL_PARAMS | ε
        Returns (param_tokens, param_types) for semantic insertion.
        """
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
        """
        FORMAL_PARAMS -> '(' FORMAL_PARAMS_SECTION FORMAL_PARAMS_1 ')'
        Returns (all_param_tokens, all_param_types).
        """
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
        """FORMAL_PARAMS_1 semantic variant — returns (tokens, types)"""

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
        """
        FORMAL_PARAMS_SECTION -> ['var'] ID_LIST ':' id
        Returns (param_tokens, param_types).
        Note: params are inserted by __parse_proc_dec after this returns,
        so we only collect here.
        """
        self.start_parsing('FORMAL_PARAMS_SECTION')

        self.__next_token()

        if not self.current_token.value == 'var':
            self.__cache_token()
        else:
            self.ast.add_leaf(self.current_token)

        # Collect param identifiers
        param_tokens = self.__parse_id_list_collecting()

        self.__next_token()

        self.__validate_current_token_value(':', 'FORMAL_PARAMS_SECTION')

        self.__next_token()

        # The type identifier (must be 'int' or 'boolean' — predeclared)
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

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

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

        # Cache the token immediately since we won't consume it here
        self.__cache_token()

        if self.current_token.value in {'[', ':='}:
            self.__parse_attr_tail(id_token)
            return

        self.__parse_proc_call_tail(id_token)

    def __parse_attr_tail(self, id_token=None):
        """
        ATTR_TAIL -> '[' EXPR ']' ':=' EXPR | ':=' EXPR
        Semantic (rule 5): var type must match expr type.
        Semantic (rule 11): vector indexing not supported.
        """

        self.start_parsing('ATTR')

        self.__next_token()

        if self.current_token.value == '[':

            self.ast.add_leaf(self.current_token)

            # Semantic rule 11: vector indexing not supported
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

            # Semantic: look up the variable's declared type
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

            # Semantic rule 5: assignment type check
            if var_tipo is not None and expr_tipo is not None and var_tipo != expr_tipo:
                self.__semantic_erro(
                    f'[ERRO SEMÂNTICO] Atribuição com tipos incompatíveis: '
                    f'variável "{id_token.value}" é "{var_tipo}", '
                    f'mas a expressão é "{expr_tipo}"',
                    id_token.lin if id_token else None,
                    id_token.col if id_token else None
                )

            # Codegen: ARMZ <end_relativo> após gerar código da EXPR (Seção 5 do plano)
            if self.code_generator is not None and var_end_relativo is not None:
                self.code_generator.gerar('ARMZ', var_end_relativo)

            self.finish_parsing()
            return

        self.__handle_error('ATTR_TAIL')

    # ------------------------------------------------------------------
    # Expression parsers — all return the computed type ('integer'|'boolean'|None)
    # ------------------------------------------------------------------

    def __parse_expr(self) -> str:
        """
        EXPR -> SIMPLE_EXPR EXPR_1
        Returns computed type.
        Semantic rule 6: relational operators type-check their operands.
        """
        self.start_parsing('EXPR')

        left_tipo = self.__parse_simple_expr()

        result_tipo = self.__parse_expr_1(left_tipo)

        self.finish_parsing()
        return result_tipo if result_tipo is not None else left_tipo

    def __parse_expr_1(self, left_tipo: str = None) -> str:
        """
        EXPR_1 -> REL SIMPLE_EXPR | ε
        REL -> '=' | '<>' | '<' | '<=' | '>=' | '>'
        Returns 'boolean' if a relational operator was found, else None.
        Semantic rule 6: operand types must be compatible.
        """

        self.__next_token()

        # REL non-terminal abstracted out
        if self.current_token.value in {'=', '<>', '<', '<=', '>=', '>'}:
            rel_op = self.current_token.value
            rel_token = self.current_token
            self.ast.add_leaf(self.current_token)

            right_tipo = self.__parse_simple_expr()

            # Semantic rule 6 / plan section 9:
            # '=' and '<>' accept integer×integer or boolean×boolean
            # '<', '<=', '>', '>=' require integer×integer
            if left_tipo is not None and right_tipo is not None:
                if rel_op in {'=', '<>'}:
                    if left_tipo != right_tipo:
                        self.__semantic_erro(
                            f'[ERRO SEMÂNTICO] Operador "{rel_op}" requer operandos do mesmo tipo '
                            f'(recebeu "{left_tipo}" e "{right_tipo}")',
                            rel_token.lin, rel_token.col
                        )
                else:  # '<', '<=', '>', '>='
                    if left_tipo != 'integer' or right_tipo != 'integer':
                        self.__semantic_erro(
                            f'[ERRO SEMÂNTICO] Operador "{rel_op}" requer operandos do tipo "integer" '
                            f'(recebeu "{left_tipo}" e "{right_tipo}")',
                            rel_token.lin, rel_token.col
                        )

            # Codegen: instrução de comparação após os dois operandos (Seção 5 do plano)
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
        Returns computed type.
        Semantic: unary '-' requires 'integer'.
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

        # Semantic: unary minus requires integer
        if unary_op == '-' and term_tipo is not None and term_tipo != 'integer':
            self.__semantic_erro(
                '[ERRO SEMÂNTICO] Operador unário "-" requer operando do tipo "integer"',
                unary_token.lin if unary_token else None,
                unary_token.col if unary_token else None
            )

        # Codegen: INVR após o código do termo se houver menos unário (Seção 5 do plano)
        if unary_op == '-' and self.code_generator is not None:
            self.code_generator.gerar('INVR')

        result_tipo = self.__parse_simple_expr_1(term_tipo)

        self.finish_parsing()
        return result_tipo if result_tipo is not None else term_tipo

    def __parse_simple_expr_1(self, left_tipo: str = None) -> str:
        """
        SIMPLE_EXPR_1 -> ('+' | '-' | 'or') TERM | ε
        Returns type if an operator was applied, else None.
        Semantic rule 6: '+'/'-' require 'integer'; 'or' requires 'boolean'.
        """

        self.__next_token()

        if self.current_token.value in {'or', '+', '-'}:
            op = self.current_token.value
            op_token = self.current_token
            self.ast.add_leaf(self.current_token)

            right_tipo = self.__parse_term()

            # Semantic rule 6
            if op in {'+', '-'}:
                expected = 'integer'
            else:  # 'or'
                expected = 'boolean'

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

            # Codegen: SOMA / SUBT / DISJ após gerar código do termo direito (Seção 5 do plano)
            if self.code_generator is not None:
                _op_mepa = {'+': 'SOMA', '-': 'SUBT', 'or': 'DISJ'}
                self.code_generator.gerar(_op_mepa[op])

            return expected

        self.__cache_token()
        return None

    def __parse_term(self) -> str:
        """
        TERM -> FACTOR TERM_1
        Returns computed type.
        """
        self.start_parsing('TERM')

        factor_tipo = self.__parse_factor()

        result_tipo = self.__parse_term_1(factor_tipo)

        self.finish_parsing()
        return result_tipo if result_tipo is not None else factor_tipo

    def __parse_term_1(self, left_tipo: str = None) -> str:
        """
        TERM_1 -> ('*' | 'div' | 'and') FACTOR | ε
        Returns type if an operator was applied, else None.
        Semantic rule 6: '*'/'div' require 'integer'; 'and' requires 'boolean'.
        """

        self.__next_token()

        if self.current_token.value in {'*', 'div', 'and'}:
            op = self.current_token.value
            op_token = self.current_token
            self.ast.add_leaf(self.current_token)

            right_tipo = self.__parse_factor()

            # Semantic rule 6
            if op in {'*', 'div'}:
                expected = 'integer'
            else:  # 'and'
                expected = 'boolean'

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

            # Codegen: MULT / DIVI / CONJ após gerar código do fator direito (Seção 5 do plano)
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
                | real_literal  (semantic error: not supported)
        Returns computed type ('integer' | 'boolean' | None).
        """

        self.start_parsing('FACTOR')

        self.__next_token()

        # 'true' / 'false' → boolean (Semantic: mark as used)
        # Codegen: CRCT 1 / CRCT 0 (Seção 5 do plano)
        if self.current_token.value in {'true', 'false'}:
            self.ast.add_leaf(self.current_token)
            if self.symbolic_table is not None:
                self.symbolic_table.marcar_utilizada(self.current_token.value)
            if self.code_generator is not None:
                valor_bool = 1 if self.current_token.value == 'true' else 0
                self.code_generator.gerar('CRCT', valor_bool)
            self.finish_parsing()
            return 'boolean'

        # identifier → look up type in table
        # Codegen: CRVL <end_relativo> (Seção 5 do plano)
        if self.current_token.name == 'identifier':
            id_token = self.current_token
            self.__cache_token()
            self.__parse_var()
            # Semantic: lookup
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

        # '(' EXPR ')' → type of EXPR (codegen delegated to __parse_expr)
        if self.current_token.value == '(':
            self.ast.add_leaf(self.current_token)
            inner_tipo = self.__parse_expr()
            self.__next_token()
            self.__validate_current_token_value(')', 'FACTOR')
            self.finish_parsing()
            return inner_tipo

        # 'not' FACTOR → boolean (Semantic rule 6: factor must be boolean)
        # Codegen: (código do fator já gerado recursivamente) + NEGA (Seção 5 do plano)
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

        # real number literal → semantic error (rule 12)
        if self.current_token.name == 'real_number':
            self.__semantic_erro(
                '[ERRO SEMÂNTICO] Números reais não são suportados pela LALG',
                self.current_token.lin, self.current_token.col
            )
            self.ast.add_leaf(self.current_token)
            self.finish_parsing()
            return None

        # integer literal
        # Codegen: CRCT <valor> (Seção 5 do plano)
        lit_token = self.current_token
        self.__validate_current_token_name('integer', 'FACTOR')
        if self.code_generator is not None and lit_token is not None:
            self.code_generator.gerar('CRCT', int(lit_token.value))

        self.finish_parsing()
        return 'integer'

    # ------------------------------------------------------------------
    # Procedure call
    # ------------------------------------------------------------------

    def __parse_proc_call_tail(self, id_token=None):
        """
        PROC_CALL_TAIL -> '(' EXPR_LIST ')' | ε
        Semantic rules 3, 8, 9: validate proc args.
        Codegen (Seção 5 do plano):
          - read(v1,...,vn): por variável → LEIT + ARMZ <end_relativo>
          - write(e1,...,en): por expressão → gera código + IMPR; ao final → IMPE
        """

        self.start_parsing('PROC_CALL')

        self.__next_token()

        if self.current_token.value == '(':

            self.ast.add_leaf(self.current_token)

            proc_name = id_token.value if id_token is not None else None

            # Codegen especial para read/write: intercala instrução após cada expressão
            if self.code_generator is not None and proc_name in {'read', 'write'}:
                arg_exprs = self.__parse_expr_list_collecting_com_codegen(proc_name)
                # IMPE ao final do write
                if proc_name == 'write':
                    self.code_generator.gerar('IMPE')
            else:
                # Caso geral: coleta tipos sem codegen especial por argumento
                arg_exprs = self.__parse_expr_list_collecting()

            self.__next_token()

            self.__validate_current_token_value(')', 'PROC_CALL_TAIL')

            # Semantic: validate call
            if id_token is not None and self.symbolic_table is not None:
                self.__semantic_validar_chamada_proc(id_token, arg_exprs)

            self.finish_parsing()

            return

        self.__cache_token()

        # proc call with no parens: still validate if it's a proc
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

    # ------------------------------------------------------------------
    # Conditional and iterative commands
    # ------------------------------------------------------------------

    def __parse_cond_command(self):
        """
        COND_COMMAND -> 'if' EXPR 'then' COMMAND COND_COMMAND_1
        Semantic rule 7: condition must be 'boolean'.
        Codegen:
          sem else: gera E; DSVF p (reservado); gera C1; back-patch p → próximo índice
          com else: gera E; DSVF p1; gera C1; DSVS p2; back-patch p1; gera C2; back-patch p2
          (Seção 5 do plano)
        """

        self.start_parsing('COND_COMMAND')

        self.__next_token()

        self.__validate_current_token_value('if', 'COND_COMMAND')

        if_token = self.current_token  # already consumed above but holds position
        cond_tipo = self.__parse_expr()

        # Semantic rule 7
        if cond_tipo is not None and cond_tipo != 'boolean':
            self.__semantic_erro(
                f'[ERRO SEMÂNTICO] Condição do "if" deve ser do tipo "boolean" '
                f'(recebeu "{cond_tipo}")',
                self.lexical.lin, self.lexical.col
            )

        # Codegen: reservar DSVF após a condição (Seção 5 do plano)
        pos_dsvf = None
        if self.code_generator is not None:
            pos_dsvf = self.code_generator.gerar('DSVF', None)

        self.__next_token()

        self.__validate_current_token_value('then', 'COND_COMMAND')

        self.__parse_command()

        # Codegen: gerar DSVS reservado e fazer back-patch do DSVF, se houver else
        # (delegado ao __parse_cond_command_1 via parâmetro)
        self.__parse_cond_command_1(pos_dsvf)

        self.finish_parsing()

    def __parse_cond_command_1(self, pos_dsvf=None):
        """
        COND_COMMAND_1 -> 'else' COMMAND | ε
        Codegen:
          - se houver 'else': emite DSVS reservado; back-patch do DSVF para início do else;
            gera C2; back-patch do DSVS para após o else
          - se não houver 'else': back-patch do DSVF para próximo índice
        """

        self.__next_token()

        if self.current_token.value == 'else':

            self.ast.add_leaf(self.current_token)

            # Codegen: DSVS reservado (pula o else ao sair do then), back-patch DSVF para aqui
            pos_dsvs = None
            if self.code_generator is not None:
                pos_dsvs = self.code_generator.gerar('DSVS', None)
                if pos_dsvf is not None:
                    self.code_generator.back_patch(pos_dsvf, self.code_generator.proximo_indice())

            self.__parse_command()

            # Codegen: back-patch DSVS para após o bloco else
            if self.code_generator is not None and pos_dsvs is not None:
                self.code_generator.back_patch(pos_dsvs, self.code_generator.proximo_indice())

            self.__cache_token()
            return

        # Codegen: sem else — back-patch DSVF para o próximo índice (após C1)
        if self.code_generator is not None and pos_dsvf is not None:
            self.code_generator.back_patch(pos_dsvf, self.code_generator.proximo_indice())

        self.__cache_token()

    def __parse_iter_command(self):
        """
        ITER_COMMAND -> 'while' EXPR 'do' COMMAND
        Semantic rule 7: condition must be 'boolean'.
        Codegen: marca inicio; gera E; DSVF p (reservado); gera C; DSVS inicio;
                 back-patch p → próximo índice (Seção 5 do plano)
        """

        self.start_parsing('ITER_COMMAND')

        self.__next_token()

        self.__validate_current_token_value('while', 'ITER_COMMAND')

        # Codegen: marca posição do início da condição (alvo do DSVS final)
        inicio = None
        if self.code_generator is not None:
            inicio = self.code_generator.proximo_indice()

        cond_tipo = self.__parse_expr()

        # Semantic rule 7
        if cond_tipo is not None and cond_tipo != 'boolean':
            self.__semantic_erro(
                f'[ERRO SEMÂNTICO] Condição do "while" deve ser do tipo "boolean" '
                f'(recebeu "{cond_tipo}")',
                self.lexical.lin, self.lexical.col
            )

        # Codegen: DSVF reservado (pula o corpo quando condição falsa)
        pos_dsvf = None
        if self.code_generator is not None:
            pos_dsvf = self.code_generator.gerar('DSVF', None)

        self.__next_token()

        self.__validate_current_token_value('do', 'ITER_COMMAND')

        self.__parse_command()

        # Codegen: DSVS de volta ao início da condição; back-patch DSVF para após DSVS
        if self.code_generator is not None:
            self.code_generator.gerar('DSVS', inicio)
            if pos_dsvf is not None:
                self.code_generator.back_patch(pos_dsvf, self.code_generator.proximo_indice())

        self.finish_parsing()

    # ------------------------------------------------------------------
    # Variable / expression list helpers
    # ------------------------------------------------------------------

    def __parse_var(self):
        """
        VAR -> id VAR_TAIL
        Semantic rule 11: vector indexing not supported (handled in VAR_TAIL).
        """

        self.start_parsing('VAR')

        self.__next_token()

        self.__validate_current_token_name('identifier', 'VAR')

        self.__parse_var_tail()

        self.finish_parsing()

    def __parse_var_tail(self):
        """
        VAR_TAIL -> '[' EXPR ']' | ε
        Semantic rule 11: vector indexing not supported.
        """

        self.__next_token()

        if self.current_token.value == '[':

            self.ast.add_leaf(self.current_token)

            # Semantic rule 11 — error already emitted in __parse_attr_tail if this is LHS;
            # for RHS occurrences, emit here.
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
        """
        EXPR_LIST -> EXPR EXPR_LIST_1
        Returns list of (tipo, token_position) tuples for semantic validation.
        Each element is a dict: {'tipo': str, 'lin': int, 'col': int}
        """
        self.start_parsing('EXPR_LIST')

        # Capture current position before parsing expr (approximate)
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
        """EXPR_LIST_1 semantic variant — returns list of tipo dicts"""

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
        EXPR_LIST -> EXPR EXPR_LIST_1
        Variante para read/write: intercala geração de código após cada expressão.
          - read: LEIT + ARMZ <end_relativo> por variável (a expressão deve ser um identifier)
          - write: IMPR por expressão (IMPE é emitido pelo chamador após o loop)
        Retorna lista de dicts {'tipo', 'lin', 'col'} para validação semântica.
        (Seção 5 do plano)
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
        """
        EXPR_LIST_1 -> ',' EXPR EXPR_LIST_1 | ε
        Variante com codegen intercalado para read/write.
        """
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
        Emite instrução MEPA após cada argumento de read/write.
          - read: a expressão gerou CRVL/CRCT mas read precisa de LEIT + ARMZ.
            Porém, a expressão (identifier) já foi gerada como CRVL — para read,
            precisamos do end_relativo da variável. O código da expressão (CRVL) foi
            gerado desnecessariamente; precisamos desfazê-lo e substituir por LEIT+ARMZ.
            Estratégia: remover a última instrução gerada (que deve ser CRVL <n>),
            emitir LEIT, emitir ARMZ <n>.
          - write: a expressão já está gerada na pilha; emitir IMPR.
        (Seção 5 do plano)
        """
        if self.code_generator is None:
            return

        if proc_name == 'write':
            self.code_generator.gerar('IMPR')

        elif proc_name == 'read':
            # A última instrução gerada pela expressão (identificador) é CRVL <end_rel>
            # Substituímos por LEIT + ARMZ <end_rel>
            if self.code_generator.C:
                ultima = self.code_generator.C[-1]
                if ultima.op == 'CRVL' and ultima.arg is not None:
                    end_rel = ultima.arg
                    # Remover o CRVL desnecessário
                    self.code_generator.C.pop()
                    # Emitir LEIT + ARMZ
                    self.code_generator.gerar('LEIT')
                    self.code_generator.gerar('ARMZ', end_rel)

    # ------------------------------------------------------------------
    # Semantic helpers
    # ------------------------------------------------------------------

    def __semantic_erro(self, mensagem: str, linha: int = None, coluna: int = None):
        """Records a semantic error in the Diagnostics collector (does not stop parsing)."""
        if self.diagnostics is not None:
            self.diagnostics.add('semantica', mensagem, linha, coluna)
        else:
            print(mensagem)

    def __semantic_inserir_nome_prog(self, token: Token):
        """Inserts the program name into the symbolic table."""
        if self.symbolic_table is None:
            return
        self.symbolic_table.inserir(Element(
            identificador=token.value,
            categoria='nome_prog',
            nivel=self.nivel_atual,
        ))

    def __semantic_inserir_var(self, token: Token, tipo: str):
        """
        Inserts a variable declaration into the symbolic table.
        Semantic rule 2: error if already declared at the same level.
        """
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

    def __semantic_inserir_proc(self, token: Token) -> 'Element | None':
        """
        Inserts a procedure declaration into the symbolic table.
        Semantic rule 2: error if already declared at the same level.
        Returns the inserted Element (so caller can fill num_params/tipos_params).
        """
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
        """
        Inserts a formal parameter at the current (incremented) level.
        Semantic rule 2: error if already declared at the same level.
        """
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
        """
        Semantic rule 10: warn about variables/params declared but never used
        at the given scope level.
        Predeclared identifiers (nivel 0, non-var/param) are excluded.
        """
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
        Validates a procedure call:
        - Rule 1: proc must be declared
        - Rule 3: arg count and types must match (for non-builtins)
        - Rule 8: read() args must be integer variables
        - Rule 9: write() args must be integer expressions
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

        # Special builtins: read and write
        if id_token.value == 'read':
            # Rule 8: each arg must be an integer variable
            # We only have type info here; the full check (must be a var, not an expr)
            # is done as best-effort from the collected arg types.
            for arg in arg_exprs:
                if arg['tipo'] is not None and arg['tipo'] != 'integer':
                    self.__semantic_erro(
                        f'[ERRO SEMÂNTICO] Argumento de "read" deve ser uma variável inteira '
                        f'(recebeu tipo "{arg["tipo"]}")',
                        arg['lin'], arg['col']
                    )
            return

        if id_token.value == 'write':
            # Rule 9: each arg must be an integer expression
            for arg in arg_exprs:
                if arg['tipo'] is not None and arg['tipo'] != 'integer':
                    self.__semantic_erro(
                        f'[ERRO SEMÂNTICO] Argumento de "write" deve ser uma expressão inteira '
                        f'(recebeu tipo "{arg["tipo"]}")',
                        arg['lin'], arg['col']
                    )
            return

        # Non-builtin procedure: rule 3
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

    # ------------------------------------------------------------------
    # Parser infrastructure
    # ------------------------------------------------------------------

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
        Gets the next token from the lexical analyzer and updates the current token if the use_cached_token flag is False.
        Otherwise, does not update the current token as it still needs to be consumed
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
