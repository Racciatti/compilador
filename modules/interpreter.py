class MEPA_VM:
    """Máquina virtual para execução do código intermediário MEPA."""

    def __init__(self):
        self.D: list = []
        self.s: int = -1
        self.i: int = 0
        self.saida: list = []

    def executar(self, C: list, entrada: list = None) -> str:
        """
        Executa o vetor de código C.
        entrada: lista de inteiros para LEIT (se None, lê de stdin).
        Retorna a saída total como string.
        """
        self.D = []
        self.s = -1
        self.i = 0
        self.saida = []
        self._impr_buffer: list = []

        _entrada = list(entrada) if entrada is not None else None

        _dispatch = {
            'INPP': self.__op_inpp,
            'AMEM': self.__op_amem,
            'DMEM': self.__op_dmem,
            'PARA': None,
            'CRCT': self.__op_crct,
            'CRVL': self.__op_crvl,
            'ARMZ': self.__op_armz,
            'SOMA': self.__op_soma,
            'SUBT': self.__op_subt,
            'MULT': self.__op_mult,
            'DIVI': self.__op_divi,
            'MODI': self.__op_modi,
            'INVR': self.__op_invr,
            'CONJ': self.__op_conj,
            'DISJ': self.__op_disj,
            'NEGA': self.__op_nega,
            'CMME': self.__op_cmme,
            'CMMA': self.__op_cmma,
            'CMIG': self.__op_cmig,
            'CMDG': self.__op_cmdg,
            'CMAG': self.__op_cmag,
            'CMEG': self.__op_cmeg,
            'DSVS': self.__op_dsvs,
            'DSVF': self.__op_dsvf,
            'NADA': self.__op_nada,
            'LEIT': self.__op_leit,
            'LECH': self.__op_lech,
            'IMPR': self.__op_impr,
            'IMPC': self.__op_impc,
            'IMPE': self.__op_impe,
        }

        while self.i < len(C):
            instr = C[self.i]
            op = instr.op

            if op == 'PARA':
                break

            if op not in _dispatch:
                raise RuntimeError(
                    f'[ERRO VM] Instrução desconhecida: "{op}" na posição {self.i}'
                )

            handler = _dispatch[op]
            resultado = handler(instr.arg, _entrada)

            # DSVS/DSVF retornam o novo i quando desviam
            if resultado is not None:
                self.i = resultado
            else:
                self.i += 1

        return ''.join(self.saida)

    def __push(self, valor: int):
        self.s += 1
        if self.s < len(self.D):
            self.D[self.s] = valor
        else:
            self.D.append(valor)

    def __pop(self) -> int:
        if self.s < 0:
            raise RuntimeError('[ERRO VM] Pilha vazia: tentativa de leitura com s < 0')
        valor = self.D[self.s]
        self.s -= 1
        return valor

    def __topo(self) -> int:
        if self.s < 0:
            raise RuntimeError('[ERRO VM] Pilha vazia: tentativa de leitura do topo com s < 0')
        return self.D[self.s]

    def __set_topo(self, valor: int):
        if self.s < 0:
            raise RuntimeError('[ERRO VM] Pilha vazia: tentativa de escrita no topo com s < 0')
        self.D[self.s] = valor

    def __acessa(self, n: int) -> int:
        if n < 0 or n >= len(self.D):
            raise RuntimeError(
                f'[ERRO VM] Acesso inválido à pilha: índice {n} fora do intervalo '
                f'[0, {len(self.D) - 1}]'
            )
        return self.D[n]

    def __escreve(self, n: int, valor: int):
        if n < 0 or n >= len(self.D):
            raise RuntimeError(
                f'[ERRO VM] Acesso inválido à pilha: índice {n} fora do intervalo '
                f'[0, {len(self.D) - 1}]'
            )
        self.D[n] = valor

    def __op_inpp(self, arg, entrada):
        # s já foi resetado no início de executar
        return None

    def __op_amem(self, arg, entrada):
        m = arg if arg is not None else 1
        for _ in range(m):
            self.D.append(0)
            self.s += 1
        return None

    def __op_dmem(self, arg, entrada):
        m = arg if arg is not None else 1
        if self.s - m < -1:
            raise RuntimeError(f'[ERRO VM] DMEM {m}: pilha insuficiente (s={self.s})')
        for _ in range(m):
            self.D.pop()
            self.s -= 1
        return None

    def __op_crct(self, arg, entrada):
        self.__push(arg)
        return None

    def __op_crvl(self, arg, entrada):
        valor = self.__acessa(arg)
        self.__push(valor)
        return None

    def __op_armz(self, arg, entrada):
        valor = self.__pop()
        self.__escreve(arg, valor)
        return None

    def __op_soma(self, arg, entrada):
        b = self.__pop()
        a = self.__topo()
        self.__set_topo(a + b)
        return None

    def __op_subt(self, arg, entrada):
        b = self.__pop()
        a = self.__topo()
        self.__set_topo(a - b)
        return None

    def __op_mult(self, arg, entrada):
        b = self.__pop()
        a = self.__topo()
        self.__set_topo(a * b)
        return None

    def __op_divi(self, arg, entrada):
        b = self.__pop()
        if b == 0:
            raise RuntimeError('[ERRO VM] Divisão por zero')
        a = self.__topo()
        self.__set_topo(a // b)
        return None

    def __op_modi(self, arg, entrada):
        b = self.__pop()
        if b == 0:
            raise RuntimeError('[ERRO VM] Módulo por zero')
        a = self.__topo()
        self.__set_topo(a % b)
        return None

    def __op_invr(self, arg, entrada):
        self.__set_topo(-self.__topo())
        return None

    def __op_conj(self, arg, entrada):
        b = self.__pop()
        a = self.__topo()
        self.__set_topo(int(bool(a) and bool(b)))
        return None

    def __op_disj(self, arg, entrada):
        b = self.__pop()
        a = self.__topo()
        self.__set_topo(int(bool(a) or bool(b)))
        return None

    def __op_nega(self, arg, entrada):
        self.__set_topo(int(not bool(self.__topo())))
        return None

    def __op_cmme(self, arg, entrada):
        b = self.__pop()
        a = self.__topo()
        self.__set_topo(int(a < b))
        return None

    def __op_cmma(self, arg, entrada):
        b = self.__pop()
        a = self.__topo()
        self.__set_topo(int(a > b))
        return None

    def __op_cmig(self, arg, entrada):
        b = self.__pop()
        a = self.__topo()
        self.__set_topo(int(a == b))
        return None

    def __op_cmdg(self, arg, entrada):
        b = self.__pop()
        a = self.__topo()
        self.__set_topo(int(a != b))
        return None

    def __op_cmag(self, arg, entrada):
        b = self.__pop()
        a = self.__topo()
        self.__set_topo(int(a >= b))
        return None

    def __op_cmeg(self, arg, entrada):
        b = self.__pop()
        a = self.__topo()
        self.__set_topo(int(a <= b))
        return None

    def __op_dsvs(self, arg, entrada):
        if arg is None:
            raise RuntimeError(
                f'[ERRO VM] DSVS na posição {self.i}: argumento de desvio não resolvido (None)'
            )
        return arg

    def __op_dsvf(self, arg, entrada):
        if arg is None:
            raise RuntimeError(
                f'[ERRO VM] DSVF na posição {self.i}: argumento de desvio não resolvido (None)'
            )
        cond = self.__pop()
        if not cond:
            return arg
        return None

    def __op_nada(self, arg, entrada):
        return None

    def __op_leit(self, arg, _entrada):
        if _entrada is not None:
            if not _entrada:
                raise RuntimeError('[ERRO VM] Lista de entrada esgotada antes do LEIT')
            valor = _entrada.pop(0)
        else:
            try:
                valor = int(input())
            except (ValueError, EOFError) as exc:
                raise RuntimeError(
                    f'[ERRO VM] LEIT: falha ao ler inteiro da entrada padrão: {exc}'
                ) from exc
        self.__push(valor)
        return None

    def __op_lech(self, arg, entrada):
        raise NotImplementedError(
            '[ERRO VM] Instrução LECH não é gerada pelo compilador LALG '
            '(leitura de caractere não suportada)'
        )

    def __op_impr(self, arg, entrada):
        valor = self.__pop()
        self._impr_buffer.append(str(valor))
        return None

    def __op_impc(self, arg, entrada):
        raise NotImplementedError(
            '[ERRO VM] Instrução IMPC não é gerada pelo compilador LALG '
            '(impressão de caractere não suportada)'
        )

    def __op_impe(self, arg, entrada):
        linha = ' '.join(self._impr_buffer) + '\n'
        self.saida.append(linha)
        print(linha, end='')
        self._impr_buffer = []
        return None
