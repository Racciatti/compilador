VALID_CATEGORIES = {'tipo', 'const', 'proc', 'nome_prog', 'var', 'param'}


class Element:
    """Entry in the symbolic table (plan Section 3 schema)."""

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
        if categoria not in VALID_CATEGORIES:
            raise ValueError(
                f'[ERRO] Categoria inválida: "{categoria}". '
                f'Valores válidos: {sorted(VALID_CATEGORIES)}'
            )

        if tipo is not None and tipo not in {'integer', 'boolean'}:
            raise ValueError(
                f'[ERRO] Tipo semântico inválido: "{tipo}". '
                f'Valores válidos: "integer", "boolean" ou None.'
            )

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
    Global symbolic table with per-entry scope level (plan Decision 3).
    Entries are stored in insertion order; search walks backwards (highest level first).
    """

    def __init__(self):
        self._entries: list = []

    def inserir(self, elemento: 'Element') -> None:
        """Inserts an element. Duplicate checking is the semantic analyser's responsibility."""
        self._entries.append(elemento)

    def busca(self, identificador: str, nivel_maximo: int = None) -> 'Element | None':
        """
        Searches from highest level down to 0.
        If nivel_maximo is given, entries with nivel > nivel_maximo are skipped.
        """
        for entry in reversed(self._entries):
            if entry.identificador != identificador:
                continue
            if nivel_maximo is not None and entry.nivel > nivel_maximo:
                continue
            return entry
        return None

    def busca_nivel_atual(self, identificador: str, nivel_atual: int) -> 'Element | None':
        """Searches only the exact scope level given (for duplicate detection in the same scope)."""
        for entry in self._entries:
            if entry.identificador == identificador and entry.nivel == nivel_atual:
                return entry
        return None

    def remover_nivel(self, nivel: int) -> None:
        """Removes all entries whose nivel matches the given level."""
        self._entries = [e for e in self._entries if e.nivel != nivel]

    def marcar_utilizada(self, identificador: str) -> None:
        """Sets utilizada=True on the most visible entry for the given identifier."""
        for entry in reversed(self._entries):
            if entry.identificador == identificador:
                entry.utilizada = True
                return

    def __repr__(self):
        return 'SymbolicTable([\n  ' + ',\n  '.join(repr(e) for e in self._entries) + '\n])'
