from lexical import LexicalAnalyzer
from symbolic_table import SymbolicTable

class RSP():

    def __init__(self, lexical:LexicalAnalyzer):
        
        self.lexical = lexical
        self.current_token = None
        self.use_cached_token = False

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
    
    def parse_block(self):

        self.__next_token()

        # A block needs to start with a reserved keyword. 
        self.__validate_current_token_name('keyword')
        
        # Check the next production is towards var_dec_section
        if self.current_token.value in {'int', 'bool'}: 

            # Since we got a token but did not consume it, set the use_cached_token flag to true
            self.use_cached_token = True

            self.parse_var_dec_section()

            self.parse_subr_dec_section()

            self.parse_comp_command()

            return

        elif self.current_token.value in {'procedure', 'begin'}:
            self.use_cached_token = True

            self.parse_subr_dec_section()

            self.parse_comp_command()

            return
        
        self.__handle_error()

    def parse_var_dec_section(self):
        
        self.parse_var_dec()

        self.__next_token()

        self.__validate_current_token_value(';')

        self.parse_var_dec_section_1()

    def parse_var_dec_section_1(self):

        self.__next_token()

        if self.current_token.value in {'boolean', 'int'}:

            self.use_cached_token = True

            self.parse_var_dec()

            self.__next_token()

            self.__validate_current_token_value(';')

            self.parse_var_dec_section_1()

            return
        
        self.use_cached_token = True

    def parse_var_dec(self):
        
        self.parse_type()

        self.parse_id_list()

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
        self.use_cached_token = True
        
    def parse_subr_dec_section(self):
        
        self.__next_token()

        if self.current_token.value == 'procedure':
            self.use_cached_token = True
            self.parse_proc_dec()
            return
        
        self.use_cached_token = True

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
            self.use_cached_token = True
            self.parse_formal_params()
            return
        
        self.use_cached_token = True
    
    def parse_formal_params(self):

        self.__next_token()

        self.__validate_current_token_value('(')

        self.parse_formal_params_section()

        self.parse_formal_params_1()

        self.__next_token()

        self.__validate_current_token_value(')')
    
    def parse_formal_params_1(self):

        self.__next_token()

        if self.current_token == ';':

            self.parse_formal_params_section()

            self.parse_formal_params_1()

            return
        
        self.use_cached_token = True

    def parse_formal_params_section(self):

        self.__next_token()

        if self.current_token.value == 'var': # ! We may need to distinguish between the derivations when building the AST
            self.__next_token()
        
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

    def parse_comp_command_1(self):
        
        self.__next_token()

        if self.current_token.value == ';':
            self.parse_command()
            self.parse_comp_command_1()
            return

        self.use_cached_token = True

    def parse_command(self):
        
    
        pass



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
        pass # !!!

















    def test_parse_program(self):

        while True:

            self.current_token = self.lexical.get_next_token()

            print(self.current_token.__str__())

            if self.current_token is None:
                return