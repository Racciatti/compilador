class Symbol:

    def __init__(self, symbol:str, name:str, symbol_type:str=None):
        self.symbol = symbol
        self.name = name
        if symbol_type not in 'digit character separator operator'.split() + [None]:
            raise ValueError(f'INVALID SYMBOL TYPE: {symbol_type}')
        self.type = symbol_type

class Alphabet:
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
        
        raise ValueError(f'Symbol "{symbol}" does not exist in the alphabet')
    
    def __str__(self):
        ans = ""
        for symbol in self.symbols:
            ans += f"{symbol}:{self.symbols[symbol].name}\n"
        
        return ans
    
class NonTerminal:

    def __init__(self):
        pass