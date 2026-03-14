import pandas as pd

class Symbol:
    """
    A symbol is the atomic unit in a language. 
    Each symbol (character) has a name and a type, which can be any of: "oprator", "separator", "digit", "character"
    """

    def __init__(self, symbol:str, name:str, symbol_type:str=None):
        self.symbol = symbol
        self.name = name
        if symbol_type not in 'digit character separator operator'.split() + [None]:
            raise ValueError(f'INVALID SYMBOL TYPE: {symbol_type}')
        self.type = symbol_type
        
class Alphabet:
    """
    An alphabet is defined by a set of symbols. 
    Additionally, it contains methods that validate the type of symbols and their existence in order to make the code less verbose 
    """
    def __init__(self, symbols:set):
        self.symbols = {symbol.symbol : symbol for symbol in symbols} # Dict structure with symbol.symbol as key and symbol object as value
        self.existing_symbols = list(self.symbols.keys())
            
    def contains_symbol(self, symbol:str)->bool:
        return symbol in self.existing_symbols
    
    def is_separator(self, symbol:str)->bool:
        return self.__get_symbol(symbol).type == 'separator'

    def is_digit(self, symbol:str)->bool:
        return self.__get_symbol(symbol).type == 'digit'
    
    def is_character(self, symbol:str)->bool:
        return self.__get_symbol(symbol).type == 'character'
    
    def is_operator(self, symbol:str)->bool:
        return self.__get_symbol(symbol).type == 'operator'
    
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
                token name: {self.name}
                token value:{self.value}
                token pos: {self.col, self.lin}
                """
        
class LexicalAnalyzer:
    """
    Documentation pending !!!
    """

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

        print('LEXICAL CALLED')

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
                    print('ignored multiple line comment')    
                    
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
                    print('ignored single line comment')    

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
                            print('ignored new_line')    
                            self.__cursor_new_line()
                    
                        else:
                            print('ignored space')    
                            self.__cursor_right()

                        if self.__get_current_symbol() == '$':
                            return None

        # If after the separators that must be ignored we still have a separator
        if self.__is_current_symbol_separator():

            print('branch relevant separator ')

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
                        return self.__return_token(token_key=self.source_code[self.pos-1:self.pos+1])
                    
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

if __name__ == '__main__':

    # Create the symbols of the language
    symbols = [
        
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

    # Define a hash table for associating symbols to token names easily
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
    '_':    'underline',
    '/':    'forward_slash',
    '<':    'smt',
    '>':    'get',
    '>=':   'geq',
    '<=':   'seq',
    '<>':   'diff',
    ':=':   'attr',
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
