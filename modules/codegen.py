"""
Módulo de geração de código intermediário MEPA para o compilador LALG.

Implementa a classe CodeGenerator que mantém o vetor de código C e fornece
suporte a back-patching de desvios condicionais/incondicionais.

Instruções suportadas (conjunto fechado, Seção 5 do plano):
  INPP, AMEM, DMEM, PARA, CRCT, CRVL, ARMZ,
  SOMA, SUBT, MULT, DIVI, MODI, INVR,
  CONJ, DISJ, NEGA,
  CMME, CMMA, CMIG, CMDG, CMAG, CMEG,
  DSVS, DSVF, NADA,
  LEIT, LECH, IMPR, IMPC, IMPE
"""

INSTRUCOES_VALIDAS = {
    'INPP', 'AMEM', 'DMEM', 'PARA',
    'CRCT', 'CRVL', 'ARMZ',
    'SOMA', 'SUBT', 'MULT', 'DIVI', 'MODI', 'INVR',
    'CONJ', 'DISJ', 'NEGA',
    'CMME', 'CMMA', 'CMIG', 'CMDG', 'CMAG', 'CMEG',
    'DSVS', 'DSVF', 'NADA',
    'LEIT', 'LECH', 'IMPR', 'IMPC', 'IMPE',
}


class Instruction:
    """Representa uma instrução do código MEPA gerado."""

    def __init__(self, op: str, arg=None):
        self.op = op
        self.arg = arg

    def __repr__(self):
        if self.arg is None:
            return self.op
        return f'{self.op} {self.arg}'


class CodeGenerator:
    """
    Gerador de código intermediário MEPA.
    Mantém o vetor de código C e o contador de deslocamento de variáveis.

    Uso típico:
        cg = CodeGenerator()
        cg.gerar('INPP')
        pos = cg.gerar('DSVF', None)   # reservado para back-patch
        cg.back_patch(pos, cg.proximo_indice())
        cg.gerar('PARA')
    """

    def __init__(self):
        # Vetor de código — lista de Instruction
        self.C: list = []

        # Contador de deslocamento relativo para variáveis (end_relativo)
        self._offset: int = 0

    def gerar(self, op: str, arg=None) -> int:
        """
        Adiciona uma instrução ao vetor de código.
        Retorna o índice da instrução adicionada (necessário para back-patching).
        """
        instrucao = Instruction(op, arg)
        idx = len(self.C)
        self.C.append(instrucao)
        return idx

    def back_patch(self, pos: int, arg) -> None:
        """
        Preenche o argumento de C[pos] com arg.
        Usado para resolver endereços de desvio reservados antecipadamente.
        """
        if pos < 0 or pos >= len(self.C):
            raise IndexError(
                f'[ERRO] back_patch: posição {pos} fora do intervalo válido (0..{len(self.C)-1})'
            )
        self.C[pos].arg = arg

    def proximo_indice(self) -> int:
        """Retorna o índice que a próxima instrução vai ocupar (alvo de desvio)."""
        return len(self.C)

    def novo_end_relativo(self) -> int:
        """
        Retorna o próximo endereço relativo de variável e incrementa o contador.
        Deve ser chamado a cada VAR_DEC para alocar espaço consecutivo em D.
        """
        end = self._offset
        self._offset += 1
        return end

    def resetar_offset(self) -> None:
        """
        Reseta o contador de offset de variáveis.
        Chamado ao início do parse (escopo global — programas sem procedure).
        """
        self._offset = 0

    def __repr__(self):
        linhas = [f'{i}: {instr}' for i, instr in enumerate(self.C)]
        return 'CodeGenerator([\n  ' + '\n  '.join(linhas) + '\n])'
