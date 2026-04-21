from abstractions import Token, AST
from formal_grammar import Alphabet, Token 
from registry import SymbolicTable

class LexicalAnalyzer:

    def __init__(self, alphabet:Alphabet, tokens_dict:dict, symbolic_table:SymbolicTable):
        
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

            # Now that we have the string value, we check whether it is a reserved keyword or an identifier

            # If keyword, return the token
            if self.symbolic_table.is_keyword(value):
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

class RSP:

    def __init__(self, lexical:LexicalAnalyzer):
        
        self.lexical = lexical
        self.current_token = None
        self.use_cached_token = False

        self.successfully_parsed = []

    def parse_program(self):

        self.__next_token()

        self.__validate_current_token_value('program')

        self.__next_token()

        self.__validate_current_token_name('identifier')

        self.__next_token()

        self.__validate_current_token_value(';')
        
        self.parse_block()

        self.__next_token()

        self.__validate_current_token_value('.')

        self.__parsed('program')

        return self.successfully_parsed
    
    def parse_block(self):

        self.__next_token()

        # A block needs to start with a reserved keyword. 
        self.__validate_current_token_name('keyword')
        
        # Check the next production is towards var_dec_section
        if self.current_token.value in {'int', 'boolean'}: 

            # Since we got a token but did not consume it, set the use_cached_token flag to true
            self.__cache_token()

            self.parse_var_dec_section()

            self.parse_subr_dec_section()

            self.parse_comp_command()
            
            self.__parsed('block')
            return

        elif self.current_token.value in {'procedure', 'begin'}:
            self.__cache_token()

            self.parse_subr_dec_section()

            self.parse_comp_command()

            self.__parsed('block')

            return
        
        self.__handle_error()

    def parse_var_dec_section(self):
        
        self.parse_var_dec()

        self.__next_token()

        self.__validate_current_token_value(';')

        self.parse_var_dec_section_1()

        self.__parsed('vardecsec')

    def parse_var_dec_section_1(self):

        self.__next_token()

        if self.current_token.value in {'boolean', 'int'}:

            self.__cache_token()

            self.parse_var_dec()

            self.__next_token()

            self.__validate_current_token_value(';')

            self.parse_var_dec_section_1()

            return
        
        self.__cache_token()

    def parse_var_dec(self):
        
        self.parse_type()

        self.parse_id_list()

        self.__parsed('vardec')

    def parse_type(self):

        self.__next_token()
        
        if self.current_token.value not in {'boolean', 'int'}:
            self.__handle_error()
        
    def parse_id_list(self):

        self.__next_token()

        self.__validate_current_token_name('identifier')

        self.parse_id_list_1()
    
    def parse_id_list_1(self):

        self.__next_token()

        if self.current_token.value == ',':

            self.__next_token()

            self.__validate_current_token_name('identifier')

            self.parse_id_list_1()

            return
        
        # If the peek token is not consumed, we need to use it again later on
        self.__cache_token()
        
    def parse_subr_dec_section(self):
        
        self.__next_token()

        if self.current_token.value == 'procedure':
            self.__cache_token()
            self.parse_proc_dec()
            return
        
        self.__cache_token()

    def parse_proc_dec(self):
        self.__next_token()

        self.__validate_current_token_value('procedure')

        self.__next_token()

        self.__validate_current_token_name('identifier')

        self.parse_proc_dec_1()

        self.__next_token()

        self.__validate_current_token_value(';')

        self.parse_block()

    def parse_proc_dec_1(self):

        self.__next_token()

        # Check if there are formal params in the procedure declaration
        if self.current_token.value == '(':
            self.__cache_token()
            self.parse_formal_params()
            return
        
        self.__cache_token()
    
    def parse_formal_params(self):

        self.__next_token()

        self.__validate_current_token_value('(')

        self.parse_formal_params_section()

        self.parse_formal_params_1()

        self.__next_token()

        self.__validate_current_token_value(')')
    
    def parse_formal_params_1(self):

        self.__next_token()

        if self.current_token.value == ';':

            self.parse_formal_params_section()

            self.parse_formal_params_1()

            return
        
        self.__cache_token()

    def parse_formal_params_section(self):

        self.__next_token()
        
        if not self.current_token.value == 'var': # ! We may need to distinguish between the derivations when building the AST
            self.__cache_token()
        
        self.parse_id_list()

        self.__next_token()

        self.__validate_current_token_value(':')

        self.__next_token()

        self.__validate_current_token_name('identifier')

    def parse_comp_command(self):
        
        self.__next_token()

        self.__validate_current_token_value('begin')

        self.parse_command()
        
        self.parse_comp_command_1()

        self.__next_token()

        self.__validate_current_token_value('end')

        self.__parsed('comp_command')

    def parse_comp_command_1(self):
        
        self.__next_token()

        if self.current_token.value == ';':
            self.parse_command()
            self.parse_comp_command_1()
            return

        self.__cache_token()

    def parse_command(self):

        self.__next_token()

        if self.current_token.name == 'identifier':
            self.parse_cmd_attr_tail()
            self.__parsed('command')
            return
        
        self.__cache_token()

        if self.current_token.value == 'if':
            self.parse_cond_command()
            self.__parsed('command')
            return
        
        if self.current_token.value == 'while':
            self.parse_iter_command()
            self.__parsed('command')
            return
        
        if self.current_token.value == 'begin':
            self.parse_comp_command()
            self.__parsed('command')
            return

        self.__handle_error()

    def parse_cmd_attr_tail(self):
        
        self.__next_token()

        # Cache the token immediately since we won't consume it here
        self.__cache_token()

        if self.current_token.value in {'[', ':='}:
            self.parse_attr_tail()
            return
        
        self.parse_proc_call_tail()

    def parse_attr_tail(self):
        
        self.__next_token()

        if self.current_token.value == '[':
            
            self.parse_expr()

            self.__next_token()

            self.__validate_current_token_value(']')
            
            self.__next_token()

            self.__validate_current_token_value(':=')

            self.parse_expr()

            self.__parsed('attr')

            return

        if self.current_token.value == ':=':
            
            self.parse_expr()

            self.__parsed('attr')
            
            return
        
        self.__handle_error()

    def parse_expr(self):
        self.parse_simple_expr()
        self.parse_expr_1()
        self.__parsed('expr')
    
    def parse_expr_1(self):
        
        self.__next_token()

        # REL non-terminal abstracted out
        if self.current_token.value in {'=', '<>', '<', '<=', '>=', '>'}:
            self.parse_simple_expr()
            return
        
        self.__cache_token()
    
    def parse_simple_expr(self):

        self.__next_token()

        if self.current_token.value not in {'+', '-'}:

            self.__cache_token()
        
        self.parse_term()
        self.parse_simple_expr_1()

    def parse_simple_expr_1(self):

        self.__next_token()

        if self.current_token.value in {'or', '+', '-'}:
            self.parse_term()
            return
        
        self.__cache_token()
    
    def parse_term(self):
        
        self.parse_factor()
        self.parse_term_1()
        self.__parsed('term')
    
    def parse_term_1(self):

        self.__next_token()

        if self.current_token.value in {'*', 'div', 'and'}:
            self.parse_factor()
            return
        
        self.__cache_token()
    
    def parse_factor(self):

        self.__next_token()

        if self.current_token.value in {'true', 'false'}:

            return
        

        if self.current_token.name == 'identifier':
            
            self.__cache_token()
            
            self.parse_var()
            
            return

        if self.current_token.value == '(':

            self.parse_expr()

            self.__next_token()

            self.__validate_current_token_value(')')

            return
        
        if self.current_token.value == 'not':

            self.parse_factor()

            return
        

        self.__validate_current_token_name('integer')

    def parse_proc_call_tail(self):
        
        self.__next_token()

        if self.current_token.value == '(':

            self.parse_expr_list()

            self.__next_token()

            self.__validate_current_token_value(')')

            return
        
        self.__cache_token()

    def parse_cond_command(self):
        
        self.__next_token()

        self.__validate_current_token_value('if')

        self.parse_expr()

        self.__next_token()

        self.__validate_current_token_value('then')

        self.parse_command()

        self.parse_cond_command_1()
        self.__parsed('cond_command')
    
    def parse_cond_command_1(self):

        self.__next_token()

        if self.current_token.value == 'else':

            self.parse_command()
        
        self.__cache_token()
    
    def parse_iter_command(self):
        
        self.__next_token()

        self.__validate_current_token_value('while')

        self.parse_expr()

        self.__next_token()

        self.__validate_current_token_value('do') 

        self.parse_command()
        self.__parsed('iter_command')

    def parse_var(self):

        self.__next_token()

        self.__validate_current_token_name('identifier')

        self.parse_var_tail()
    
    def parse_var_tail(self):

        self.__next_token()

        if self.current_token.value == '[':

            self.parse_expr()

            self.__next_token()

            self.__validate_current_token_value(']')

            return

        self.__cache_token()

    def parse_expr_list(self):

        self.parse_expr()
        self.parse_expr_list_1()

    def parse_expr_list_1(self):

        self.__next_token()

        if self.current_token.value == ',':
            self.parse_expr()
            self.parse_expr_list_1()
            return

        self.__cache_token()


    def __parsed(self, parsed_element:str):
        self.successfully_parsed.append(parsed_element)

    def __cache_token(self):
        # Method created merely for interpretability
        self.use_cached_token = True

    def __validate_current_token_value(self, value:str):

        if self.current_token.value != value:
            self.__handle_error()

    def __validate_current_token_name(self, name:str):
        if self.current_token.name != name:
            self.__handle_error()

    def __next_token(self):
        """
        Gets the next token from the lexical analyzer and updates the current token if the use_cached_token flag is False. 
        Otherwise, does not update the current token as it still needs to be consumed
        """
        if not self.use_cached_token:
            self.current_token = self.lexical.get_next_token()
            return
        
        self.use_cached_token = False




    def __handle_error(self):
        # !!!
        pass



    def test_parse_program(self):

        while True:

            self.__next_token()

            print(self.current_token.__str__())

            if self.current_token is None:
                return