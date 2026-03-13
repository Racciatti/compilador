import tkinter as tk
from tkinter import filedialog, scrolledtext
import sys
import os
import io

# Adiciona o diretório pai ao path para importar o módulo logic
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.lexical_analysis import read_text

class AnalisadorLexicoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Analisador Léxico")
        self.root.geometry("800x600")
        
        # Frame superior para entrada
        frame_entrada = tk.Frame(root, padx=10, pady=10)
        frame_entrada.pack(fill=tk.BOTH, expand=True)
        
        # Label e área de texto de entrada
        tk.Label(frame_entrada, text="Texto de Entrada:", font=("Arial", 12, "bold")).pack(anchor=tk.W)
        
        self.texto_entrada = scrolledtext.ScrolledText(frame_entrada, height=10, width=80, font=("Courier", 10))
        self.texto_entrada.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Frame para botões
        frame_botoes = tk.Frame(root, padx=10, pady=5)
        frame_botoes.pack()
        
        # Botões
        btn_carregar = tk.Button(frame_botoes, text="Carregar Arquivo .txt", command=self.carregar_arquivo, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), padx=10, pady=5)
        btn_carregar.pack(side=tk.LEFT, padx=5)
        
        btn_analisar = tk.Button(frame_botoes, text="Analisar Texto", command=self.analisar, bg="#2196F3", fg="white", font=("Arial", 10, "bold"), padx=10, pady=5)
        btn_analisar.pack(side=tk.LEFT, padx=5)
        
        btn_limpar = tk.Button(frame_botoes, text="Limpar", command=self.limpar, bg="#f44336", fg="white", font=("Arial", 10, "bold"), padx=10, pady=5)
        btn_limpar.pack(side=tk.LEFT, padx=5)
        
        # Frame inferior para resultados
        frame_resultado = tk.Frame(root, padx=10, pady=10)
        frame_resultado.pack(fill=tk.BOTH, expand=True)
        
        # Label e área de texto de resultado
        tk.Label(frame_resultado, text="Resultados da Análise:", font=("Arial", 12, "bold")).pack(anchor=tk.W)
        
        self.texto_resultado = scrolledtext.ScrolledText(frame_resultado, height=10, width=80, font=("Courier", 10), bg="#f0f0f0")
        self.texto_resultado.pack(fill=tk.BOTH, expand=True, pady=5)

    def carregar_arquivo(self):
        """
        Abre um diálogo para selecionar um arquivo .txt e carrega seu conteúdo
        """
        arquivo = filedialog.askopenfilename(
            title="Selecione um arquivo de texto",
            filetypes=[("Arquivos de Texto", "*.txt"), ("Todos os Arquivos", "*.*")]
        )
        
        if arquivo:
            try:
                with open(arquivo, "r", encoding="utf-8") as file:
                    conteudo = file.read()
                    self.texto_entrada.delete(1.0, tk.END)
                    self.texto_entrada.insert(1.0, conteudo)
            except Exception as e:
                self.texto_resultado.delete(1.0, tk.END)
                self.texto_resultado.insert(1.0, f"Erro ao carregar arquivo: {str(e)}")
    
    def analisar(self):
        """
        Analisa o texto de entrada e exibe os resultados
        """
        texto = self.texto_entrada.get(1.0, tk.END)
        
        if not texto.strip():
            self.texto_resultado.delete(1.0, tk.END)
            self.texto_resultado.insert(1.0, "Por favor, insira um texto ou carregue um arquivo!")
            return
        
        # Captura a saída do print da função read_text
        captura = io.StringIO()
        sys.stdout = captura
        
        try:
            read_text(texto)
        finally:
            sys.stdout = sys.__stdout__
        
        resultado = captura.getvalue()
        
        self.texto_resultado.delete(1.0, tk.END)
        
        if resultado.strip():
            self.texto_resultado.insert(1.0, resultado)
        else:
            self.texto_resultado.insert(1.0, "Nenhum caractere válido encontrado.")
    
    def limpar(self):
        """
        Limpa os campos de entrada e resultado
        """
        self.texto_entrada.delete(1.0, tk.END)
        self.texto_resultado.delete(1.0, tk.END)


def main():
    root = tk.Tk()
    app = AnalisadorLexicoGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
