# Do material:
# "A tabela de símbolos é utilizada para diferenciar palavaras e símbolos reservados 
# da linguagem de identificadores definidos pelo usuário"


class Element:

    def __init__(self, element_type:str, identifier:str, element_subtype:str=None, value = None):

        if element_type not in ['keyword', 'variable']:
            raise ValueError(f'"element_type" parameter must be one of ["keyword", "variable"], but "{element_type}" was received')
        
        self.type = element_type

        if self.type == 'variable':

            # if element_subtype not in ['boolean', 'int']:
            #     raise ValueError(f'INVALID VAR TYPE: {element_subtype}')
            
            self.subtype = element_subtype

        else:
            # if element_subtype not in ['constant', 'var_type', 'procedure']:
            #     raise ValueError(f'INVALID KEYWORD TYPE: {element_subtype}')

            self.subtype = element_subtype
        
        self.identifier = identifier
        self.value = value



class SymbolicTable:
    def __init__(self, elements:list):
        # Register the elements as a hash table with identifiers as keys
        self.elements = {element.identifier: element for element in elements}
    

    def add_element(self, identifier:str, value, type:str): 
        if identifier in (self.elements.keys()):
            return 'ERROR: Identifier already exists'
        
        self.elements[identifier] = Element(element_type='variable', element_subtype=type, identifier=identifier, value=value)
    
    def remove_element(self, identifier:str):

        if self.elements.pop(identifier) is None:
            raise Exception(f'ERROR: Identifier {identifier} tried to be removed but it does not exist')
    
    


if __name__ == '__main__':
    keyword_identifiers = ['program','procedure','begin','end','read','write','var','if','then','else','while','do','int','boolean','true','false','not','and','or',]

    elements = [Element(element_type='keyword', identifier=id) for id in keyword_identifiers]

    table = SymbolicTable(elements)


