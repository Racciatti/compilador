"""
Módulo interpretador MEPA para o compilador LALG.

Implementa a classe MEPA_VM que executa o vetor de código C gerado pelo CodeGenerator.

Instruções suportadas (Seção 6 do plano):
  INPP, AMEM, DMEM, PARA, CRCT, CRVL, ARMZ,
  SOMA, SUBT, MULT, DIVI, MODI, INVR,
  CONJ, DISJ, NEGA,
  CMME, CMMA, CMIG, CMDG, CMAG, CMEG,
  DSVS, DSVF, NADA,
  LEIT, LECH (não suportado), IMPR, IMPC (não suportado), IMPE

Convenções (plano Seção 8):
  - AMEM: inicializa posições alocadas com 0 (torna testes determinísticos).
  - IMPR/IMPE: IMPR acumula valor no buffer da linha atual; IMPE descarrega o buffer
    como "v1 v2 ... vn\\n" (valores separados por espaço + quebra de linha).
  - LEIT: consome de lista `entrada` (para testes) ou lê de stdin.
"""


class MEPA_VM:
    """
    Máquina virtual para execução do código intermediário MEPA.

    Estado (Seção 6 do plano):
      D: pilha de dados (cresce dinamicamente)
      s: índice do topo da pilha (-1 = vazia)
      i: contador de programa
      saida: saída acumulada (usada em testes para verificar resultado sem capturar stdout)
    """

    def __init__(self):
        self.D: list = []
        self.s: int = -1
        self.i: int = 0
        self.saida: list = []     # lista de strings (uma por linha escrita)

    # ------------------------------------------------------------------
    # Ponto de entrada
    # ------------------------------------------------------------------

    def executar(self, C: list, entrada: list = None) -> str:
        """
        Executa o vetor de código C.

        Parâmetros:
          C: lista de Instruction (objetos com .op e .arg)
          entrada: lista de inteiros para LEIT (se None, lê de stdin interativo)

        Retorna a saída total produzida como string (concatenação de todas as linhas).
        Levanta RuntimeError com mensagem em português em caso de erro de execução.
        """
        # Reinicia estado a cada execução
        self.D = []
        self.s = -1
        self.i = 0
        self.saida = []
        self._impr_buffer: list = []

        _entrada = list(entrada) if entrada is not None else None

        # Tabela de despacho: opcode → método handler
        _dispatch = {
            'INPP': self.__op_inpp,
            'AMEM': self.__op_amem,
            'DMEM': self.__op_dmem,
            'PARA': None,          # sinal de parada — tratado no laço
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

            # DSVS/DSVF retornam o novo valor de i quando desviam
            if resultado is not None:
                self.i = resultado
            else:
                self.i += 1

        return ''.join(self.saida)

    # ------------------------------------------------------------------
    # Utilitários internos de pilha
    # ------------------------------------------------------------------

    def __push(self, valor: int):
        """Empilha um valor. Expande D se necessário."""
        self.s += 1
        if self.s < len(self.D):
            self.D[self.s] = valor
        else:
            self.D.append(valor)

    def __pop(self) -> int:
        """Desempilha e retorna o valor do topo."""
        if self.s < 0:
            raise RuntimeError(
                '[ERRO VM] Pilha vazia: tentativa de leitura com s < 0'
            )
        valor = self.D[self.s]
        self.s -= 1
        return valor

    def __topo(self) -> int:
        """Retorna o valor do topo sem desempilhar."""
        if self.s < 0:
            raise RuntimeError(
                '[ERRO VM] Pilha vazia: tentativa de leitura do topo com s < 0'
            )
        return self.D[self.s]

    def __set_topo(self, valor: int):
        """Substitui o valor do topo sem alterar s."""
        if self.s < 0:
            raise RuntimeError(
                '[ERRO VM] Pilha vazia: tentativa de escrita no topo com s < 0'
            )
        self.D[self.s] = valor

    def __acessa(self, n: int) -> int:
        """Lê D[n] com verificação de limites."""
        if n < 0 or n >= len(self.D):
            raise RuntimeError(
                f'[ERRO VM] Acesso inválido à pilha: índice {n} fora do intervalo '
                f'[0, {len(self.D) - 1}]'
            )
        return self.D[n]

    def __escreve(self, n: int, valor: int):
        """Escreve D[n] com verificação de limites."""
        if n < 0 or n >= len(self.D):
            raise RuntimeError(
                f'[ERRO VM] Acesso inválido à pilha: índice {n} fora do intervalo '
                f'[0, {len(self.D) - 1}]'
            )
        self.D[n] = valor

    # ------------------------------------------------------------------
    # Handlers de instrução
    # Retornam None para incremento normal de i, ou int (novo i) para desvios.
    # ------------------------------------------------------------------

    def __op_inpp(self, arg, entrada):
        """INPP: inicializa pilha (s = -1). Já feito no início de executar."""
        # s já foi resetado para -1; nada a fazer.
        return None

    def __op_amem(self, arg, entrada):
        """AMEM m: aloca m posições inicializadas com 0; s += m."""
        m = arg if arg is not None else 1
        for _ in range(m):
            self.D.append(0)
            self.s += 1
        return None

    def __op_dmem(self, arg, entrada):
        """DMEM m: desaloca m posições; s -= m."""
        m = arg if arg is not None else 1
        if self.s - m < -1:
            raise RuntimeError(
                f'[ERRO VM] DMEM {m}: pilha insuficiente (s={self.s})'
            )
        for _ in range(m):
            self.D.pop()
            self.s -= 1
        return None

    def __op_crct(self, arg, entrada):
        """CRCT c: s += 1; D[s] = c."""
        self.__push(arg)
        return None

    def __op_crvl(self, arg, entrada):
        """CRVL n: s += 1; D[s] = D[n]."""
        valor = self.__acessa(arg)
        self.__push(valor)
        return None

    def __op_armz(self, arg, entrada):
        """ARMZ n: D[n] = D[s]; s -= 1."""
        valor = self.__pop()
        self.__escreve(arg, valor)
        return None

    def __op_soma(self, arg, entrada):
        """SOMA: D[s-1] += D[s]; s -= 1."""
        b = self.__pop()
        a = self.__topo()
        self.__set_topo(a + b)
        return None

    def __op_subt(self, arg, entrada):
        """SUBT: D[s-1] -= D[s]; s -= 1."""
        b = self.__pop()
        a = self.__topo()
        self.__set_topo(a - b)
        return None

    def __op_mult(self, arg, entrada):
        """MULT: D[s-1] *= D[s]; s -= 1."""
        b = self.__pop()
        a = self.__topo()
        self.__set_topo(a * b)
        return None

    def __op_divi(self, arg, entrada):
        """DIVI: D[s-1] = D[s-1] // D[s]; s -= 1. Divisão inteira."""
        b = self.__pop()
        if b == 0:
            raise RuntimeError('[ERRO VM] Divisão por zero')
        a = self.__topo()
        self.__set_topo(a // b)
        return None

    def __op_modi(self, arg, entrada):
        """MODI: D[s-1] = D[s-1] % D[s]; s -= 1."""
        b = self.__pop()
        if b == 0:
            raise RuntimeError('[ERRO VM] Módulo por zero')
        a = self.__topo()
        self.__set_topo(a % b)
        return None

    def __op_invr(self, arg, entrada):
        """INVR: D[s] = -D[s]."""
        self.__set_topo(-self.__topo())
        return None

    def __op_conj(self, arg, entrada):
        """CONJ: D[s-1] = int(bool(D[s-1]) and bool(D[s])); s -= 1."""
        b = self.__pop()
        a = self.__topo()
        self.__set_topo(int(bool(a) and bool(b)))
        return None

    def __op_disj(self, arg, entrada):
        """DISJ: D[s-1] = int(bool(D[s-1]) or bool(D[s])); s -= 1."""
        b = self.__pop()
        a = self.__topo()
        self.__set_topo(int(bool(a) or bool(b)))
        return None

    def __op_nega(self, arg, entrada):
        """NEGA: D[s] = int(not bool(D[s]))."""
        self.__set_topo(int(not bool(self.__topo())))
        return None

    def __op_cmme(self, arg, entrada):
        """CMME: D[s-1] = int(D[s-1] < D[s]); s -= 1."""
        b = self.__pop()
        a = self.__topo()
        self.__set_topo(int(a < b))
        return None

    def __op_cmma(self, arg, entrada):
        """CMMA: D[s-1] = int(D[s-1] > D[s]); s -= 1."""
        b = self.__pop()
        a = self.__topo()
        self.__set_topo(int(a > b))
        return None

    def __op_cmig(self, arg, entrada):
        """CMIG: D[s-1] = int(D[s-1] == D[s]); s -= 1."""
        b = self.__pop()
        a = self.__topo()
        self.__set_topo(int(a == b))
        return None

    def __op_cmdg(self, arg, entrada):
        """CMDG: D[s-1] = int(D[s-1] != D[s]); s -= 1."""
        b = self.__pop()
        a = self.__topo()
        self.__set_topo(int(a != b))
        return None

    def __op_cmag(self, arg, entrada):
        """CMAG: D[s-1] = int(D[s-1] >= D[s]); s -= 1."""
        b = self.__pop()
        a = self.__topo()
        self.__set_topo(int(a >= b))
        return None

    def __op_cmeg(self, arg, entrada):
        """CMEG: D[s-1] = int(D[s-1] <= D[s]); s -= 1."""
        b = self.__pop()
        a = self.__topo()
        self.__set_topo(int(a <= b))
        return None

    def __op_dsvs(self, arg, entrada):
        """DSVS p: i = p (desvio incondicional). Retorna p para que o laço salte para lá."""
        if arg is None:
            raise RuntimeError(
                f'[ERRO VM] DSVS na posição {self.i}: argumento de desvio não resolvido (None)'
            )
        # Retornamos arg diretamente: o laço principal vai usar esse valor como próximo i.
        # Como o laço faz self.i = resultado (sem incrementar depois), chegamos em arg.
        return arg

    def __op_dsvf(self, arg, entrada):
        """DSVF p: se D[s] == 0 então i = p; s -= 1. Senão s -= 1."""
        if arg is None:
            raise RuntimeError(
                f'[ERRO VM] DSVF na posição {self.i}: argumento de desvio não resolvido (None)'
            )
        cond = self.__pop()
        if not cond:
            # Desvio: retornamos arg para que o laço principal salte para lá.
            return arg
        # Sem desvio: incremento normal
        return None

    def __op_nada(self, arg, entrada):
        """NADA: nenhuma operação."""
        return None

    def __op_leit(self, arg, _entrada):
        """LEIT: lê inteiro de entrada (lista) ou stdin; s += 1; D[s] = valor."""
        if _entrada is not None:
            if not _entrada:
                raise RuntimeError(
                    '[ERRO VM] Lista de entrada esgotada antes do LEIT'
                )
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
        """LECH: leitura de caractere — não gerada pelo compilador LALG."""
        raise NotImplementedError(
            '[ERRO VM] Instrução LECH não é gerada pelo compilador LALG '
            '(leitura de caractere não suportada)'
        )

    def __op_impr(self, arg, entrada):
        """IMPR: acumula D[s] no buffer da linha atual; s -= 1."""
        valor = self.__pop()
        self._impr_buffer.append(str(valor))
        return None

    def __op_impc(self, arg, entrada):
        """IMPC: impressão de caractere — não gerada pelo compilador LALG."""
        raise NotImplementedError(
            '[ERRO VM] Instrução IMPC não é gerada pelo compilador LALG '
            '(impressão de caractere não suportada)'
        )

    def __op_impe(self, arg, entrada):
        """
        IMPE: finaliza a linha atual.
        Descarrega o buffer como "v1 v2 ... vn\\n" e esvazia o buffer.
        Acumula em self.saida (para testes) e imprime em stdout.
        """
        linha = ' '.join(self._impr_buffer) + '\n'
        self.saida.append(linha)
        print(linha, end='')
        self._impr_buffer = []
        return None
