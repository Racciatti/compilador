from grammar import Alphabet, Symbol
from symbolic_table import SymbolicTable

class Token:    
    """
    A token can be formed by one or more symbols, it is the atomic unit extracted from the source code,
    from a lexical perspective.

    Each token has a name, value, and the position in which it was found in the source code (col, lin)  
    """
    
    def __init__(self, name:str, value:str, col:int, lin:int):
        self.name = name
        self.value = value
        self.col = col
        self.lin = lin
    
    def __str__(self):

        return f"""
                token name:{self.name}
                token value:{self.value}
                token pos:{self.col, self.lin}
                """
        
class LexicalAnalyzer:
    """
    Documentation pending !!!
    """

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