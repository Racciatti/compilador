import pandas as pd

class Symbol:
    """
    A symbol is the atomic unit in a language. 
    Each symbol (character) has a name and certain properties. 
    """

    def __init__(self, symbol:str, name:str, is_separator:bool=False, is_digit:bool = False, is_character:bool=False):
        self.symbol = symbol
        self.name = name
        self.properties = {}
        self.properties['is_separator'] = is_separator
        self.properties['is_digit'] = is_digit
        self.properties['is_character'] = is_character
        
class Alphabet:
    """
    An alphabet is defined by a set of symbols.
    """
    def __init__(self, symbols:set):
        self.symbols = {symbol.symbol : symbol for symbol in symbols} # Dict structure with symbol.symbol as key and symbol object as value
        self.existing_symbols = list(self.symbols.keys())
            
    def contains_symbol(self, symbol:str)->bool:
        return symbol in self.existing_symbols
    
    def is_separator(self, symbol:str)->bool:
        return self.__get_symbol(symbol).properties['is_separator']

    def is_digit(self, symbol:str)->bool:
        return self.__get_symbol(symbol).properties['is_digit']
    
    def is_character(self, symbol:str)->bool:
        return self.__get_symbol(symbol).properties['is_character']
    
    def __get_symbol(self, symbol:str)->Symbol:
        if self.contains_symbol(symbol):
            return self.symbols[symbol]
        
        return None
    
    def __str__(self):
        ans = ""
        for symbol in self.symbols:
            ans += f"{symbol}:{self.symbols[symbol].name}\n"
        
        return ans

class Token:    
    """
    A token is formed by one or more symbols. 
    Valid tokens can be joined in order to form higher level abstractions. 
    """
    
    def __init__(self, name:str, value:str, col:int, lin:int):
        self.name = name
        self.value = value
        self.col = col
        self.lin = lin
    
    def __str__(self):

        return f"""
                token name: {self.name}
                token value:{self.value}
                token pos: {self.lin, self.col}
                """
        
class LexicalAnalyzer:

    def __init__(self, alphabet:Alphabet, tokens_dict:dict):
        
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

        # If it doesn't belong to the alphabet
        if not self.__is_current_symbol_valid():

            # Return an error
            return self.__throw_error_for_current_symbol(f'ERROR: Symbol "{self.__get_current_symbol()}" not in alphabet')
        
        # If it is a separator (!NOTE "is_separator" is being used as what should be "is_unitary". They match for this alphabet, but that is not a gurantee)
        if self.__is_current_symbol_separator():

            # Check if the current character is indeed a registered token
            if self.__get_current_symbol() not in list(self.tokens_dict.keys()):
                raise Exception('Symbol is separator and is in the alphabet, but it is not a key associated to a token')

            return self.__return_token()
            
        # If it's not a separator, it's either a digit, a character or a dot
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
            
            # If we have a separator, this is an integer
            if self.__is_current_symbol_separator():
                
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

    def __is_current_symbol_digit(self)->bool:
        return self.alphabet.is_digit(self.__get_current_symbol())
        
    def __is_current_symbol_separator(self)->bool:
        return self.alphabet.is_separator(self.__get_current_symbol())

    def __is_current_symbol_character(self)->bool:
        return self.alphabet.is_character(self.__get_current_symbol())

    def __is_current_symbol_valid(self)->bool:
        return self.alphabet.contains_symbol(self.__get_current_symbol())

    def __get_current_symbol(self)->str:
        return self.source_code[self.pos]

    # We'll probably need something more elaborate here, so the method has already been created
    def __throw_error_for_current_symbol(self, error_str:str):
        return error_str

    def __return_token(self, token_value:str = None, token_col:int = None, token_lin:int = None, token_key:str = None):
        """
        Use the symbol under the cursor or passed arguments to create a token and return it, whilst also moving the cursor.
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
            token = Token(name=token_name, value=token_value, col=token_col, lin=token_lin)
            
        if token_value == '\n':
            self.__cursor_new_line()
        else:
            self.__cursor_right()

        return token

if __name__ == '__main__':

    symbols = [
        
        # Digits
        Symbol('0', 'digit_0',      is_digit=True),
        Symbol('1', 'digit_1',      is_digit=True),
        Symbol('2', 'digit_2',      is_digit=True),
        Symbol('3', 'digit_3',      is_digit=True),
        Symbol('4', 'digit_4',      is_digit=True),
        Symbol('5', 'digit_5',      is_digit=True),
        Symbol('6', 'digit_6',      is_digit=True),
        Symbol('7', 'digit_7',      is_digit=True),
        Symbol('8', 'digit_8',      is_digit=True),
        Symbol('9', 'digit_9',      is_digit=True),

        # Characters
        Symbol("a", 'character_a',  is_character=True),
        Symbol("b", 'character_b',  is_character=True),
        Symbol("c", 'character_c',  is_character=True),
        Symbol("d", 'character_d',  is_character=True),
        Symbol("e", 'character_e',  is_character=True),
        Symbol("f", 'character_f',  is_character=True),
        Symbol("g", 'character_g',  is_character=True),
        Symbol("h", 'character_h',  is_character=True),
        Symbol("i", 'character_i',  is_character=True),
        Symbol("j", 'character_j',  is_character=True),
        Symbol("k", 'character_k',  is_character=True),
        Symbol("l", 'character_l',  is_character=True),
        Symbol("m", 'character_m',  is_character=True),
        Symbol("n", 'character_n',  is_character=True),
        Symbol("o", 'character_o',  is_character=True),
        Symbol("p", 'character_p',  is_character=True),
        Symbol("q", 'character_q',  is_character=True),
        Symbol("r", 'character_r',  is_character=True),
        Symbol("s", 'character_s',  is_character=True),
        Symbol("t", 'character_t',  is_character=True),
        Symbol("u", 'character_u',  is_character=True),
        Symbol("v", 'character_v',  is_character=True),
        Symbol("w", 'character_w',  is_character=True),
        Symbol("x", 'character_x',  is_character=True),
        Symbol("y", 'character_y',  is_character=True),
        Symbol("z", 'character_z',  is_character=True),
        Symbol("A", 'character_A',  is_character=True),
        Symbol("B", 'character_B',  is_character=True),
        Symbol("C", 'character_C',  is_character=True),
        Symbol("D", 'character_D',  is_character=True),
        Symbol("E", 'character_E',  is_character=True),
        Symbol("F", 'character_F',  is_character=True),
        Symbol("G", 'character_G',  is_character=True),
        Symbol("H", 'character_H',  is_character=True),
        Symbol("I", 'character_I',  is_character=True),
        Symbol("J", 'character_J',  is_character=True),
        Symbol("K", 'character_K',  is_character=True),
        Symbol("L", 'character_L',  is_character=True),
        Symbol("M", 'character_M',  is_character=True),
        Symbol("N", 'character_N',  is_character=True),
        Symbol("O", 'character_O',  is_character=True),
        Symbol("P", 'character_P',  is_character=True),
        Symbol("Q", 'character_Q',  is_character=True),
        Symbol("R", 'character_R',  is_character=True),
        Symbol("S", 'character_S',  is_character=True),
        Symbol("T", 'character_T',  is_character=True),
        Symbol("U", 'character_U',  is_character=True),
        Symbol("V", 'character_V',  is_character=True),
        Symbol("W", 'character_W',  is_character=True),
        Symbol("X", 'character_X',  is_character=True),
        Symbol("Y", 'character_Y',  is_character=True),
        Symbol("Z", 'character_Z',  is_character=True),

        # OPERATORS
        Symbol("+", "plus",         is_separator=True),
        Symbol("-", "minus",        is_separator=True),
        Symbol("*", "multiplier",   is_separator=True),
        Symbol("/", "divider",      is_separator=True),
        Symbol('(', "open_p",       is_separator=True),
        Symbol(')', "close_p",      is_separator=True),
        
        # MISC
        Symbol('\n',"new_line",     is_separator=True),
        Symbol(' ', "space",        is_separator=True),
        Symbol(',', "comma",        is_separator=True),
        Symbol(':', "colon",        is_separator=True),
        Symbol(';', "semicolon",    is_separator=True),
        Symbol('=', "equals",       is_separator=True),
        Symbol('$', "eof",          is_separator=True),
        Symbol('.', "dot")
    ]

    tokens_dict ={
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

    }

    # Creating alphabet from symbols
    alphabet = Alphabet(symbols)   

    # Create lexical analyzer
    lexical = LexicalAnalyzer(alphabet, tokens_dict=tokens_dict)
    
    # User input for testing
    # input_str = input()
    # lexical.set_source_code(input_str)

    # Load file contents for testing
    lexical.load_source_code()

    # Add start of file token to start the mainloop
    current_token = Token('SOF', 'SOF', -1, -1)

    while current_token is not None:
        current_token = lexical.get_next_token()
        print(current_token.__str__())
