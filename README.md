# Compilador LALG

Compilador completo para LALG, um subconjunto de Pascal com tipos inteiros e booleanos, estruturas de controle (`if`/`while`), procedimentos e I/O via `read`/`write`. Implementado manualmente em Python puro.

O pipeline tem cinco fases: análise léxica, análise sintática, análise semântica, geração de código intermediário (MEPA) e interpretação. 

Todas as fases compartilham um único objeto `Diagnostics` que acumula erros; qualquer erro em qualquer fase impede as fases seguintes de executar.

---

## Estrutura dos módulos

```
modules/
├── formal_grammar.py   alfabeto e classificação de símbolos
├── abstractions.py     Token, AST_Node, AST
├── utils.py            constantes, tabela de símbolos inicial
├── registry.py         Element, SymbolicTable
├── diagnostics.py      coletor de erros e avisos
├── engine.py           LexicalAnalyzer + RDP (parser, semântica, codegen integrados)
├── codegen.py          Instruction, CodeGenerator
├── interpreter.py      MEPA_VM
└── pseudomain.py       orquestrador do pipeline
```

---

## Análise Léxica

**Módulo:** `engine.py` - classe `LexicalAnalyzer`

O analisador léxico é um autômato manual implementado como um loop de leitura caractere a caractere sobre o código-fonte (com um `$` sentinela ao final). A cada chamada de `get_next_token()` ele consome exatamente um token e retorna um objeto `Token(name, value, col, lin)`.

O alfabeto é definido em `formal_grammar.py` e carregado a partir de `utils.py`. Cada símbolo é classificado em uma de quatro categorias — `digit`, `character`, `operator`, `separator` — e o analisador usa essa classificação para decidir qual autômato acionar:

- **Espaços, quebras de linha e comentários** (`/` até fim da linha; `{...}` para blocos) são silenciosamente consumidos sem produzir token.
- **Separadores** (parênteses, vírgulas, ponto-e-vírgula, etc.) geram um token de um único caractere imediatamente.
- **Operadores** (`+`, `-`, `*`, `=`, `<`, `>`, `:`) são lidos e, quando seguidos de outro operador compatível, formam tokens compostos (`:=`, `<=`, `>=`, `<>`).
- **Identificadores e palavras reservadas**: lê caracteres alfanuméricos até encontrar algo que não seja letra nem dígito. O lexema lido é então comparado contra `RESERVED_WORDS` (conjunto fixo de 14 palavras: `program`, `procedure`, `begin`, `end`, `var`, `if`, `then`, `else`, `while`, `do`, `div`, `and`, `or`, `not`). Se pertencer ao conjunto, o token recebe `name='keyword'`; caso contrário, `name='identifier'`. **Identificadores pré-declarados** (`int`, `boolean`, `true`, `false`, `read`, `write`) são tokenizados como `identifier` normalmente — eles existem na tabela de símbolos, não no conjunto de palavras reservadas.
- **Literais inteiros**: sequência de dígitos. Se seguido de `.` e mais dígitos, o léxico reconhece um número real e emite token `real_number` (que será rejeitado semanticamente, já que a LALG não suporta o tipo `real`).

A distinção entre `keyword` e `identifier` é puramente baseada no conjunto `RESERVED_WORDS`, sem consultar a tabela de símbolos — isso simplifica o analisador e evita dependências circulares com as fases posteriores.

---

## Análise Sintática

**Módulo:** `engine.py`, classe `RDP` (Recursive Descent Parser)

O parser é recursivo-descendente, implementado seguindo a gramática LL(1) da LALG (documentada em `grammar_construction.md`). Cada não-terminal da gramática corresponde a um método privado `__parse_X` na classe `RDP`. O parser consome tokens via `get_next_token()` do léxico e constrói a AST (`abstractions.py`) durante o percurso.

### Estrutura geral da gramática

```
PROGRAM        → 'program' id ';' BLOCK '.'
BLOCK          → VAR_DEC_SECTION SUBR_DEC_SECTION COMP_COMMAND
VAR_DEC_SECTION→ 'var' VAR_DEC { ';' VAR_DEC } | ε
VAR_DEC        → id_list ':' tipo
SUBR_DEC_SECTION → PROC_DEC ';' SUBR_DEC_SECTION | ε
PROC_DEC       → 'procedure' id FORMAL_PARAMS ';' BLOCK
COMP_COMMAND   → 'begin' COMMAND { ';' COMMAND } 'end'
COMMAND        → ATTR_TAIL | COND_COMMAND | ITER_COMMAND | ε
COND_COMMAND   → 'if' EXPR 'then' COMMAND ['else' COMMAND]
ITER_COMMAND   → 'while' EXPR 'do' COMMAND
EXPR           → SIMPLE_EXPR [REL SIMPLE_EXPR]
SIMPLE_EXPR    → ['-'] TERM { ('+' | '-' | 'or') TERM }
TERM           → FACTOR { ('*' | 'div' | 'and') FACTOR }
FACTOR         → id | num | 'true' | 'false' | '(' EXPR ')' | 'not' FACTOR
```

### Recuperação de erros

Quando o token corrente não é o esperado, o parser chama `__handle_error`, que imprime `[ERRO SINTÁTICO]` e avança tokens até encontrar um elemento do conjunto LAST do não-terminal atual (tabela `LAST_SET` em `utils.py`). Isso implementa recuperação de erros por modo de pânico, permitindo que o parser continue e reporte múltiplos erros sintáticos em uma única passagem.

### AST

A árvore sintática é construída incrementalmente durante o parse. `AST` mantém um ponteiro `current_node` que avança para filhos (`add_node`) e retrocede para o pai (`validate_current_node`) conforme as produções são reconhecidas. 

---

## Análise Semântica

**Módulos:** `registry.py` (tabela de símbolos) + `diagnostics.py` (coletor) + `engine.py` (ações embutidas no RDP)

A análise semântica é integrada diretamente ao parser: Não há uma passagem separada sobre a AST. As ações semânticas são executadas nos pontos exatos das produções gramaticais, seguindo o modelo de tradução dirigida pela sintaxe.

### Tabela de símbolos (`registry.py`)

A tabela é uma estrutura única global (`SymbolicTable`), implementada como lista ordenada de `Element`. Cada entrada carrega:

| Campo | Descrição |
|---|---|
| `identificador` | chave de busca |
| `categoria` | `'tipo'`, `'const'`, `'proc'`, `'nome_prog'`, `'var'`, `'param'` |
| `tipo` | `'integer'`, `'boolean'`, ou `None` (para proc/nome_prog) |
| `valor` | usado só para constantes (`true`:1, `false`:0) |
| `nivel` | nível de aninhamento (0 = programa principal) |
| `utilizada` | flag para detectar variáveis declaradas e não usadas |
| `end_relativo` | endereço na pilha de dados (preenchido na geração de código) |
| `num_params` / `tipos_params` | para procedimentos, número e tipos dos parâmetros |

Antes do parse começar, `build_symbolic_table()` pré-insere os seis identificadores pré-declarados da LALG em `nivel=0`: `int`, `boolean`, `true`, `false`, `read`, `write`.

**Busca com escopo:** `busca(id)` percorre a lista de trás para frente (do nível mais alto para o 0), retornando a primeira ocorrência visível. Ao sair de um procedimento, `remover_nivel(n)` apaga todas as entradas do nível `n`, o que elimina automaticamente variáveis locais do escopo (sem necessidade de pilha de tabelas separadas).

### Ações semânticas integradas no parser

- **Ao declarar** (`VAR_DEC`, parâmetros formais, `PROC_DEC`): verifica duplicata no nível atual via `busca_nivel_atual`; insere a entrada com a categoria e tipo corretos; ao entrar em um procedimento, incrementa `nivel_atual`; ao sair, checa não-utilizadas e chama `remover_nivel`.
- **Ao usar** (`FACTOR`(id), chamada de procedimento): busca na tabela; emite `[ERRO SEMÂNTICO]` se não encontrado; marca `utilizada=True`.
- **Tipos nas expressões:** os métodos `__parse_expr`, `__parse_simple_expr`, `__parse_term` e `__parse_factor` retornam o tipo computado (`'integer'` ou `'boolean'`), propagando de baixo para cima. O tipo é verificado no ponto de uso.

### Regras de erro semântico

1. Identificador não declarado
2. Redeclaração no mesmo nível de escopo
3. Incompatibilidade de parâmetros em chamada de procedimento (número ou tipo)
4. Variável de escopo fechado (já removida da tabela → tratada como não declarada)
5. Atribuição com tipos incompatíveis
6. Operador usado com tipo errado (`div`/`*`/`+`/`-` exigem `integer`; `and`/`or`/`not` exigem `boolean`)
7. Condição de `if`/`while` não é `boolean`
8. `read(...)` com argumento que não é variável `integer`
9. `write(...)` com argumento que não é expressão `integer`
10. Variável declarada e nunca utilizada (emite `[AVISO SEMÂNTICO]`, não bloqueia compilação)
11. Indexação `id[expr]`: vetores não suportados pela LALG
12. Literal `real` em qualquer posição: tipo `real` não suportado pela LALG

Todos os erros são acumulados em `Diagnostics` e **não** interrompem o parse (o compilador continua para coletar o máximo de diagnósticos possível em uma única passagem).

---

## Geração de Código Intermediário

**Módulo:** `codegen.py` - `CodeGenerator`; ações de geração em `engine.py`

A máquina alvo é a **MEPA** (Máquina de Execução de Programas Algol), uma máquina de pilha com um vetor de instruções `C` e um vetor de dados `D`. O `CodeGenerator` mantém a lista `C` de objetos `Instruction(op, arg)` e um contador de offset para atribuição de endereços relativos a variáveis.

### Back-patching

Instruções de desvio condicional (`DSVF`) e incondicional (`DSVS`) são emitidas com argumento `None` quando o endereço de destino ainda não é conhecido (por exemplo, ao gerar o `DSVF` do `if` antes de saber onde o `else` começa). `gerar()` retorna o índice da instrução no vetor `C`; quando o endereço é conhecido, `back_patch(pos, alvo)` preenche o argumento. Esse mecanismo resolve todos os desvios de `if`/`if-else`/`while` em uma única passagem.

### Instruções geradas por construto

| Construto | Código gerado |
|---|---|
| Início do programa | `INPP` |
| Fim do programa | `PARA` |
| Declaração de variável | `AMEM 1`; grava `end_relativo` na tabela |
| Variável em expressão | `CRVL n` (n = end_relativo) |
| Literal inteiro | `CRCT valor` |
| `true` / `false` | `CRCT 1` / `CRCT 0` |
| `not` | (fator) + `NEGA` |
| Menos unário | (termo) + `INVR` |
| `+`, `-`, `or` | (operandos) + `SOMA` / `SUBT` / `DISJ` |
| `*`, `div`, `and` | (operandos) + `MULT` / `DIVI` / `CONJ` |
| `=`, `<>`, `<`, `<=`, `>`, `>=` | `CMIG` / `CMDG` / `CMME` / `CMEG` / `CMMA` / `CMAG` |
| Atribuição | (expressão) + `ARMZ n` |
| `if E then C1` | (E) + `DSVF ?` + (C1) + *back-patch* |
| `if E then C1 else C2` | (E) + `DSVF ?` + (C1) + `DSVS ?` + *back-patch DSVF* + (C2) + *back-patch DSVS* |
| `while E do C` | marca início + (E) + `DSVF ?` + (C) + `DSVS início` + *back-patch DSVF* |
| `read(v)` | `LEIT` + `ARMZ n` por variável |
| `write(e1,...,en)` | (e1) + `IMPR` + ... + (en) + `IMPR` + `IMPE` |

### Limitação: procedimentos

Programas com `procedure` passam normalmente pelas fases léxica, sintática e semântica. Porém, ao detectar qualquer declaração de procedimento (`_tem_procedure = True`), o gerador descarta o vetor `C` inteiro ao final do parse e registra um diagnóstico informativo. Isso porque a geração de código para chamadas de procedimento (registros de ativação, desvios para o corpo) não foi implementada — a limitação do material de aula não cobre esse caso.

---

## Fase 5 — Interpretação

**Módulo:** `interpreter.py` → classe `MEPA_VM`

A VM executa o vetor `C` produzido pelo `CodeGenerator`. O estado da máquina é:

- `D` — pilha de dados (lista Python, cresce dinamicamente)
- `s` — índice do topo da pilha (começa em -1)
- `i` — contador de programa (índice em `C`)

O loop principal despacha cada instrução para um método handler via dicionário `{opcode: método}`. Para instruções que alteram o fluxo (`DSVS`, `DSVF`), o handler retorna o novo valor de `i`; para todas as outras, retorna `None` e o loop incrementa `i` normalmente.

**`AMEM m`** aloca `m` posições inicializadas com `0` (adoção de convenção para tornar testes determinísticos — a especificação MEPA original não define o valor inicial). **`DSVF`** desvia se o topo da pilha for `0` (falso) e sempre consome o valor.

**Saída:** `IMPR` não imprime imediatamente — acumula o valor num buffer de linha interno. `IMPE` descarrega o buffer como uma linha com valores separados por espaço seguida de `\n`. Isso implementa a semântica de `write(e1,...,en)`: uma chamada gera uma linha, múltiplos valores na mesma chamada aparecem separados por espaço.

**`LEIT`** aceita um parâmetro `entrada: list[int]`. Se a lista for fornecida (modo de teste), consome dela sequencialmente; caso contrário, lê de `stdin` interativamente.

---

## Orquestrador do Pipeline

**Módulo:** `pseudomain.py` → função `compilar_e_executar(codigo_fonte, entrada)`

```
código-fonte (str)
       │
       ▼
  LexicalAnalyzer ──────────────────────────────── Diagnostics
       │
       ▼
     RDP.parse_program()
       ├── ações semânticas ──────────────────────► Diagnostics
       └── ações de codegen ──────────────────────► CodeGenerator.C
       │
       ▼
  has_errors() ?
  ├── sim  → retorna {sucesso: False, saida: ''}
  └── não
       │
       ▼
  _tem_procedure ?
  ├── sim  → retorna {sucesso: False, codigo: [], mensagem: info}
  └── não
       │
       ▼
  MEPA_VM.executar(C, entrada)
       │
       ▼
  retorna {sucesso: True, saida: str, codigo: list}
```

O resultado é sempre um dicionário com `sucesso`, `saida`, `codigo` e `diagnostics` — o que permite ao caller (interface web ou CLI) reagir de forma uniforme a qualquer desfecho.

---

## Decisões de Projeto Relevantes

**Palavras reservadas vs. pré-declarados:** a distinção é arquitetural. `RESERVED_WORDS` é um conjunto fixo consultado pelo léxico — esses lexemas nunca podem ser identificadores de usuário. Pré-declarados (`int`, `boolean`, `true`, `false`, `read`, `write`) são entradas normais na tabela de símbolos, tokenizados como `identifier`, e podem ser sombreados por declarações de usuário em níveis mais profundos (embora isso gere erro semântico de redeclaração no nível 0).

**Tabela única com campo de nível:** em vez de uma pilha de tabelas (uma por escopo), usa-se uma única lista com campo `nivel` por entrada. Ao fechar um escopo, `remover_nivel(n)` elimina todas as entradas daquele nível. A busca percorre a lista de trás para frente, garantindo que o nível mais interno sempre tem precedência — comportamento equivalente ao escopo léxico estático de Pascal.

**Tipo booleano representado como inteiro:** a VM não distingue `boolean` de `integer` em tempo de execução — ambos são inteiros na pilha `D`. A distinção existe apenas na análise semântica (em tempo de compilação). `true` gera `CRCT 1`, `false` gera `CRCT 0`, e operações booleanas (`CONJ`, `DISJ`, `NEGA`) operam sobre qualquer valor inteiro interpretado como booleano (`0` = falso, qualquer outro = verdadeiro).

**Operadores relacionais e tipos:** `=` e `<>` aceitam operandos do mesmo tipo (ambos `integer` ou ambos `boolean`); `<`, `<=`, `>`, `>=` exigem `integer` nos dois lados — comparar booleanos por ordem não tem semântica definida na LALG.
