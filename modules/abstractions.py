from formal_grammar import NonTerminal

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

class AST_Node:

    def __init__(self, name:str, father:AST_Node, status:str = 'invalid', children:list = []):
        
        self.name = name
        self.father = father

        self.status = status if status in {'invalid', 'valid', 'error'} else 'invalid'

        self.children = children

    def add_child(self, node:AST_Node):
        self.children.append(node)

    
    def validate(self):
        self.status = 'valid'
    
    def mark_error(self):
        self.status = 'error'
    


class AST():

    def __init__(self):
        self.root = None
        self.current_node = None
    

    def create_root(self, name:str):
        print(f'AST: Created root node "{name}"')
        if self.root is not None:
            raise Exception('Root has already been created')
        
        self.root = AST_Node(name, None)
        self.current_node = self.root # ! Pointer issue?

    def add_leaf(self, token:Token):
        print(f'AST: Adding leaf node {token.value}')
        self.current_node.add_child(token)

    def add_node(self, name:str):
        print(f'AST: Adding child node "{name}" and moving to the child')

        new_node = AST_Node(name, self.current_node)
        
        self.current_node.add_child(new_node)

        self.current_node = new_node
        

    def validate_current_node(self):

        print(f'AST: validating current node "{self.current_node.name}" and moving to father "{self.current_node.father.name}"')
        self.current_node.validate()
        
        self.current_node = self.current_node.father
