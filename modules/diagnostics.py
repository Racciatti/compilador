class Diagnostics:
    """Acumula erros e avisos durante a compilação."""

    def __init__(self):
        self.errors: list = []

    def add(self, fase: str, mensagem: str, linha: int = None, coluna: int = None) -> None:
        self.errors.append({
            'fase': fase,
            'mensagem': mensagem,
            'linha': linha,
            'coluna': coluna,
        })

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def report(self) -> None:
        for entry in self.errors:
            linha_info = f' (linha {entry["linha"]})' if entry['linha'] is not None else ''
            coluna_info = f' (coluna {entry["coluna"]})' if entry['coluna'] is not None else ''
            print(f'{entry["mensagem"]}{linha_info}{coluna_info}')

    def __repr__(self):
        return f'Diagnostics({len(self.errors)} entries)'
