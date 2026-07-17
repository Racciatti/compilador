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

    def __init__(self, op: str, arg=None):
        self.op = op
        self.arg = arg

    def __repr__(self):
        if self.arg is None:
            return self.op
        return f'{self.op} {self.arg}'


class CodeGenerator:
    """Gerador de código intermediário MEPA."""

    def __init__(self):
        self.C: list = []
        self._offset: int = 0

    def gerar(self, op: str, arg=None) -> int:
        """Adiciona instrução ao vetor C e retorna o índice (necessário para back-patch)."""
        instrucao = Instruction(op, arg)
        idx = len(self.C)
        self.C.append(instrucao)
        return idx

    def back_patch(self, pos: int, arg) -> None:
        """Preenche o argumento de C[pos] — usado para resolver endereços de desvio."""
        if pos < 0 or pos >= len(self.C):
            raise IndexError(
                f'[ERRO] back_patch: posição {pos} fora do intervalo válido (0..{len(self.C)-1})'
            )
        self.C[pos].arg = arg

    def proximo_indice(self) -> int:
        """Índice que a próxima instrução vai ocupar (alvo de desvio)."""
        return len(self.C)

    def novo_end_relativo(self) -> int:
        """Retorna o próximo end_relativo e incrementa o contador."""
        end = self._offset
        self._offset += 1
        return end

    def resetar_offset(self) -> None:
        self._offset = 0

    def __repr__(self):
        linhas = [f'{i}: {instr}' for i, instr in enumerate(self.C)]
        return 'CodeGenerator([\n  ' + '\n  '.join(linhas) + '\n])'
