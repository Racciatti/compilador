class Diagnostics:
    """
    Accumulates lexical, syntactic and semantic diagnostics throughout compilation.
    Semantic errors use add('semantica', ...) and do NOT interrupt parsing.
    """

    def __init__(self):
        self.errors: list = []

    def add(self, fase: str, mensagem: str, linha: int = None, coluna: int = None) -> None:
        """Appends a diagnostic entry."""
        self.errors.append({
            'fase': fase,
            'mensagem': mensagem,
            'linha': linha,
            'coluna': coluna,
        })

    def has_errors(self) -> bool:
        """Returns True if at least one diagnostic was recorded."""
        return len(self.errors) > 0

    def report(self) -> None:
        """Prints all accumulated diagnostics to stdout."""
        for entry in self.errors:
            linha_info = f' (linha {entry["linha"]})' if entry['linha'] is not None else ''
            coluna_info = f' (coluna {entry["coluna"]})' if entry['coluna'] is not None else ''
            print(f'{entry["mensagem"]}{linha_info}{coluna_info}')

    def __repr__(self):
        return f'Diagnostics({len(self.errors)} entries)'
