class Element:
    """Entrada na tabela de símbolos."""

    def __init__(
        self,
        identificador: str,
        categoria: str,
        tipo: str = None,
        valor=None,
        nivel: int = 0,
        utilizada: bool = False,
        end_relativo: int = None,
        num_params: int = 0,
        tipos_params: list = None,
    ):
        self.identificador = identificador
        self.categoria = categoria
        self.tipo = tipo
        self.valor = valor
        self.nivel = nivel
        self.utilizada = utilizada
        self.end_relativo = end_relativo
        self.num_params = num_params
        self.tipos_params = tipos_params if tipos_params is not None else []

    def __repr__(self):
        return (
            f'Element(id={self.identificador!r}, categoria={self.categoria!r}, '
            f'tipo={self.tipo!r}, nivel={self.nivel})'
        )


class SymbolicTable:
    """
    Tabela de símbolos global com nível de escopo por entrada (Decisão 3 do plano).
    Entradas em ordem de inserção; busca percorre de trás pra frente (nível mais alto primeiro).
    """

    def __init__(self):
        self._entries: list = []

    def inserir(self, elemento: 'Element') -> None:
        self._entries.append(elemento)

    def busca(self, identificador: str, nivel_maximo: int = None) -> 'Element | None':
        # busca do nivel mais alto ate 0
        for entry in reversed(self._entries):
            if entry.identificador != identificador:
                continue
            if nivel_maximo is not None and entry.nivel > nivel_maximo:
                continue
            return entry
        return None

    def busca_nivel_atual(self, identificador: str, nivel_atual: int) -> 'Element | None':
        # só no nível exato, para detectar redeclaração no mesmo escopo
        for entry in self._entries:
            if entry.identificador == identificador and entry.nivel == nivel_atual:
                return entry
        return None

    def remover_nivel(self, nivel: int) -> None:
        self._entries = [e for e in self._entries if e.nivel != nivel]

    def marcar_utilizada(self, identificador: str) -> None:
        for entry in reversed(self._entries):
            if entry.identificador == identificador:
                entry.utilizada = True
                return

    def __repr__(self):
        return 'SymbolicTable([\n  ' + ',\n  '.join(repr(e) for e in self._entries) + '\n])'
