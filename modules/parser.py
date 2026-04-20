from lexical import LexicalAnalyzer
from symbolic_table import SymbolicTable

class RSP():

    def __init__(self, lexical:LexicalAnalyzer):
        
        self.lexical = lexical
        self.current_token = None
        self.use_cached_token = False


    def test_parse_program(self):

        while self.current_token is not None:

            self.current_token = self.lexical.get_next_token()

            print(self.current_token.__str__)

    def parse_program(self):

        token = self.lexical.get_next_token()

        if token.value is not 'program':
            # RAISE OR RETURN ERROR
            pass

        token = self.lexical.get_next_token()

        if token is not ID:
            # RAISE OR RETURN ERROR
            pass
        
        token = self.lexical.get_next_token()

        if token.value != ';':
            # RAISE OR RETURN ERROR
            pass

        self.parse_block() # VALIDATE ALL WENT WELL ------------------------ SLEF>USE_CACHED_TOKEN. AST? PANIC? 

        token = self.lexical.get_next_token()

        if token.value != '.':
            # RAISE OR RETURN ERROR
            pass
    
        return True
        
        

    def parse_block(self):

        token = self.lexical.get_next_token()

        if token.value == 'procedure':
            self.parse_subroutine_declaration()


    
    def parse_subr_dec(self):

        self.parse_proc_dec(self)


    def parse_proc_dec(self):

        # PRESUMED TO HAVE CONSUMED 'procedure'

        token = self.lexical.get_next_token()

        if self.token is not ID:
            pass

        self.parse_proc_dec_1()
        




