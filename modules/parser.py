from lexical import LexicalAnalyzer
from symbolic_table import SymbolicTable

DEBUG = True

class RSP():

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
        if DEBUG:
            print('call parse expr')
        self.parse_simple_expr()
        self.parse_expr_1()
        self.__parsed('expr')
    
    def parse_expr_1(self):
        if DEBUG:
            print('call parse expr_1')
        
        self.__next_token()

        # REL non-terminal abstracted out
        if self.current_token.value in {'=', '<>', '<', '<=', '>=', '>'}:
            self.parse_simple_expr()
            return
        
        self.__cache_token()
    
    def parse_simple_expr(self):
        if DEBUG:
            print('call parse simple expr')

        self.__next_token()

        if self.current_token.value not in {'+', '-'}:

            self.__cache_token()
        
        self.parse_term()
        self.parse_simple_expr_1()

    def parse_simple_expr_1(self):
        if DEBUG:
            print('call parse simple expr 1')

        self.__next_token()

        if self.current_token.value in {'or', '+', '-'}:
            self.parse_term()
            return
        
        self.__cache_token()
    
    def parse_term(self):
        if DEBUG:
            print('call parse term')
        
        self.parse_factor()
        self.parse_term_1()
        self.__parsed('term')
    
    def parse_term_1(self):
        if DEBUG:
            print('call parse term 1')

        self.__next_token()

        if self.current_token.value in {'*', 'div', 'and'}:
            self.parse_factor()
            return
        
        self.__cache_token()
    
    def parse_factor(self):
        if DEBUG:
            print('call parse factor')

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

        if DEBUG: 
            print(f'Validating value "{value}" against the current_token.value "{self.current_token.value}"')

        if self.current_token.value != value:
            self.__handle_error()

    def __validate_current_token_name(self, name:str):
        print(f'Validating value "{name}" against the current_token.name "{self.current_token.name}"')
        if self.current_token.name != name:
            self.__handle_error()

    def __next_token(self):
        """
        Gets the next token from the lexical analyzer and updates the current token if the use_cached_token flag is False. 
        Otherwise, does not update the current token as it still needs to be consumed
        """
        if not self.use_cached_token:
            self.current_token = self.lexical.get_next_token()
            if DEBUG: 
                print('CURRENT TOKEN: ', self.current_token.__str__())
                print('SUCCESSFULLY PARSED: ', self.successfully_parsed)
            return
        
        self.use_cached_token = False




    def __handle_error(self):
        print("ERROR: ")



    def test_parse_program(self):

        while True:

            self.__next_token()

            if DEBUG:
                print(self.current_token.__str__())

            if self.current_token is None:
                return