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

    def __init__(self, alphabet:Alphabet, source_code:str, tokens_dict:dict):
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
        
        # Add SOF and EOF symbols to the source code
        self.source_code = source_code + '$'

        # Max cursor position before EOF
        self.max_pos = len(source_code) - 1


    def get_next_token(self):
        
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

        print('called return token with', token_value, token_col, token_lin, token_key)

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


def load_symbols(symbols_data_path:str='../symbols.csv')->set:

    symbols_df = pd.read_csv(symbols_data_path)
    
    symbols_list = [
        Symbol(
            symbol=element[1]['symbol'], 
            name=element[1]['name'], 
            is_separator=element[1]['is_sep'], 
            is_digit=element[1]['is_digit'], 
            is_character=element[1]['is_char'])
            
            for element in symbols_df.iterrows()
    ]

    return set(symbols_list)


if __name__ == '__main__':

    tokens_dict ={
    '+':    'op_sum',
    '-':    'op_sub', 
    '*':    'op_mul',
    '/':    'op_div',
    'real': 'real_number',
    'int':  'integer',
    'key':  'keyword',
    'id':   'identifier',
    ' ':    'space',
    '(':    'open_p',
    ')':    'close_p',
    ':':    'colon',

    }

    # Loading and creating symbols
    symbols = load_symbols()

    # Creating alphabet from symbols
    alphabet = Alphabet(symbols)   

    # User input for testing
    input_str = input()
    
    # Create lexical analyzer
    lexical = LexicalAnalyzer(alphabet, source_code=input_str, tokens_dict=tokens_dict)

    # Add start of file token to start the mainloop
    current_token = Token('SOF', 'SOF', -1, -1)

    while current_token is not None:
        current_token = lexical.get_next_token()
        print(current_token.__str__())

    

# PENDENTE:
# Eliminação de espaços
# Adição de operadores e separadores remanescentes
# Testes de erros encontrados pelo léxico
# Criação de tabela de memória auxiliar para identificadores e palavras reservadas
# Carregamento de símbolos e tokens ao invés de criação no código