# Tabela de Rastreamento de Erros Sintáticos - Compilador LALG

Esta tabela contém uma lista exaustiva de erros realistas para o teste do Analisador Sintático Descendente Recursivo (RDP).

| ERROR                     | VALIDATED | FILE  |                       OBS                                 |
| CATEGORIA | ERROR | VALIDATED | FILE | OBS |
|---------------|---------------------------|-----------|-------|-----------------------------------------------------------|
| **Básicos**   | Repeated operators        | YES       | 1     |                            -                              |
| **Básicos**   | Missing ";"               | YES       | 1     | Consumes the entire procedure body; add more sync tokens  |
| **Básicos**   | "fi" instead of "if"      | YES       | 1     |                                                           |
| **Básicos**   | "else" mispelling         | YES       | 1     | Consumes the entire procedure body; add more sync tokens  |
| **Estrutural** | Missing `program` keyword | NO | err_struct_no_program | O parser deve falhar imediatamente se não encontrar o início do programa. |
| **Estrutural** | Missing ID after `program` | NO | err_struct_no_prog_id | Erro: `program ;`. |
| **Estrutural** | Missing `;` after program ID | NO | err_struct_no_prog_semi | Erro de terminação de cabeçalho. |
| **Estrutural** | Missing `.` at the very end | NO | err_struct_no_dot | O ponto final encerra a produção inicial <programa>. |
| **Estrutural** | Code after the final `.` | NO | err_struct_code_after_dot | Lixo no final do arquivo após o fechamento do bloco principal. |
| **Declarações** | Missing type in variable dec | NO | err_decl_no_type | Ex: `var x, y;` (sem o tipo `int` ou `boolean`). |
| **Declarações** | Missing `,` in ID list | NO | err_decl_no_comma | Ex: `int x y;`. |
| **Declarações** | Missing `;` after declaration | NO | err_decl_no_semi | Falta de delimitador entre seções de declaração. |
| **Declarações** | Repeated type keyword | NO | err_decl_repeated_type | Ex: `int int x;`. |
| **Declarações** | Invalid type name | NO | err_decl_invalid_type | Uso de tipos não suportados como `float` ou `string`. |
| **Sub-rotinas** | `procedure` misspelling | NO | err_sub_proc_spell | Ex: `procedur`, `proc`. |
| **Sub-rotinas** | Missing ID in procedure | NO | err_sub_no_proc_id | Ex: `procedure (var x: int);`. |
| **Sub-rotinas** | Missing `(` in formal params | NO | err_sub_no_lparen | Ex: `procedure p x: int);`. |
| **Sub-rotinas** | Missing `)` in formal params | NO | err_sub_no_rparen | Parênteses não balanceados em parâmetros. |
| **Sub-rotinas** | Missing `:` in parameters | NO | err_sub_no_colon | Erro: `(var x int)`. |
| **Sub-rotinas** | Missing `;` after procedure head | NO | err_sub_no_semi | A gramática exige `;` antes do bloco da procedure. |
| **Blocos** | Missing `begin` | NO | err_blk_no_begin | Início de bloco composto mal formado. |
| **Blocos** | Missing `end` | NO | err_blk_no_end | Bloco não fechado; deve testar sincronização. |
| **Blocos** | `end` with `;` in final block | NO | err_blk_end_semi | Verificação se o parser aceita `end` seguido de `.` ou `;`. |
| **Comandos** | `=` instead of `:=` | NO | err_cmd_assign_eq | Confusão comum entre atribuição e igualdade relacional. |
| **Comandos** | Missing `then` in `if` | NO | err_cmd_no_then | Ex: `if x > 0 write(x);`. |
| **Comandos** | Missing `do` in `while` | NO | err_cmd_no_do | Ex: `while x < 10 begin x := x + 1; end;`. |
| **Comandos** | Missing command after `then` | NO | err_cmd_empty_then | Ex: `if x then ;`. |
| **Comandos** | Missing command after `else` | NO | err_cmd_empty_else | Ex: `if x then x:=1 else ;`. |
| **Comandos** | `else` without previous `if` | NO | err_cmd_dangling_else | Erro de aninhamento ou dangling else. |
| **Comandos** | Missing `[` or `]` in array assignment | NO | err_cmd_array_bracket | Erro na indexação de variável. |
| **Comandos** | Empty index in array `x[]` | NO | err_cmd_empty_index | A gramática exige uma expressão dentro dos colchetes. |
| **Comandos** | Missing `;` between commands | NO | err_cmd_no_semi | O separador de comandos em blocos compostos é obrigatório. |
| **Expressões** | Unbalanced parentheses `(` | NO | err_expr_unbal_paren | Expressão como `((a + b)`. |
| **Expressões** | Missing operand | NO | err_expr_missing_operand | Ex: `x := 5 + * 2;`. |
| **Expressões** | Missing operator | NO | err_expr_missing_op | Ex: `x := 5 (a + b);`. |
| **Expressões** | Invalid relational operator `==` | NO | err_expr_double_eq | Pascal/LALG usa apenas `=` para comparação. |
| **Expressões** | Relational op in invalid place | NO | err_expr_chained_rel | Ex: `if (a > b > c) then ...`. |
| **Expressões** | Missing factor after `not` | NO | err_expr_not_no_factor | Erro: `x := not ;`. |
| **Sincronização** | Garbage inside `begin...end` | NO | err_sync_garbage_block | Testar se o parser recupera até o próximo `;` ou `end`. |
| **Sincronização** | Extra symbols between decls | NO | err_sync_extra_decl | Testar sincronização em seções de variáveis. |
| **Léxico/Sint** | Mispelled reserved word `begim` | NO | err_lex_begim | Identificado como ID pelo léxico, deve falhar no sintático. |
| **Léxico/Sint** | "fi" instead of "if" | YES | ? | Já validado. |
