# Grammar Construction

## Executive Summary

### Purpose 
The goal of this file is to transform the LALG grammar into a grammar that can be parsed by a Recursive Descendent Parser (RSP).  

### Methodology
Since the constraints imposed by the RSP on the grammar are for it to be LL(1), we need to transform the grammar into LL(1) by eliminating left recursion (both immediate and indirect) and performing left factoring, which will be done systematically:
1. Remove indirect left recursion 
2. Remove immediate left recursion 
3. Perform left factoring

## Grammar transformation

### Language definition

**The formal language is specified below in the Extended Backus-Naur Form (EBNF)** 

```
1 <program> ::= program <id>;
                <block>

2 <block> ::= [var_dec_section]
              [subr_dec_section]
              <comp_command>

3 <var_dec_section> ::= <var_dev> {;<var_dec>};

4 <var_dec> ::= <type> <id_list>

5 <id_list> ::= <id>{,id}

6 <subr_dec_section> ::= {<proc_dec>;}

7 <proc_dec> ::= procedure <id> [<formal_params>]; <block>

8 <formal_params> ::= (<formal_params_section> {;<formal_params_section>})

9 <formal_params_section> ::= [var] <id_list> : <id>

10 <comp_command> ::= begin <command> {; <command>} end

11 <command> ::= <attr> | <proc_call> | <comp_command> | <cond_command 1> | <iter_command 1>

12 <attr> ::= <var> := <expr>

13 <proc_call> ::= <id> [(<expr_list>)]

14 <cond_command 1> ::= if <expr> then <command> [else <command>]

15 <iter_command 1> ::= while <expr> do <command>

16 <expr> ::= <simple_expr> [<rel><simple_expr>]

17 <rel> ::= = | <> | < | <= | >= | >

18 <simple_expr> ::= [+ | -] <term> {(+|-|or)<term>}

19 <term> ::= <factor> {(* | div | and)<factor>}

20 <factor> ::= <var> | <num> | (<expr>) | not <factor>

21 <var> ::= <id> | <id> [<expr>]

22 <expr_list> ::= <expr> {, <expr>}

23 <num> ::= <digit>{<digit>}

24 <digit> ::= 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9

25 <id> ::= <letter>{<letter> | <digit>}

26 <letter> ::= _ | a-z | A-Z

```

### Formal Grammar

**Turning the language specified in EBNF into formal grammar production rules:**

```
1 <program> ::= program <id>;
                <block>
```

1 S $\rightarrow$ program ID;BLOCK

```
2 <block> ::= [var_dec_section]
              [subr_dec_section]
              <comp_command>
```

2 BLOCK $\rightarrow$ VAR_DEC_SECTION SUBR_DEC_SECTION COMP_COMMAND | SUBR_DEC_SECTION COMP_COMMAND | COMP_COMMAND

```
3 <var_dec_section> ::= <var_dec> {;<var_dec>};
```
VAR_DEC_SECTION $\rightarrow$ VAR_DEC;VAR_DEC_SECTION_1
VAR_DEC_SECTION_1 $\rightarrow$ VAR_DEC;VAR_DEC_SECTION_1 | $\epsilon$


```
4 <var_dec> ::= <type> <id_list>
```

```
5 <id_list> ::= <id>{,id}
```

```
6 <subr_dec_section> ::= {<proc_dec>;}
```

```
7 <proc_dec> ::= procedure <id> [<formal_params>]; <block>
```

```
8 <formal_params> ::= (<formal_params_section> {;<formal_params_section>})
```

```
9 <formal_params_section> ::= [var] <id_list> : <id>
```

```
10 <comp_command> ::= begin <command> {; <command>} end
```

```
11 <command> ::= <attr> | <proc_call> | <comp_command> | <cond_command 1> | <iter_command 1>
```

```
12 <attr> ::= <var> := <expr>
```

```
13 <proc_call> ::= <id> [(<expr_list>)]
```

```
14 <cond_command 1> ::= if <expr> then <command> [else <command>]
```

```
15 <iter_command 1> ::= while <expr> do <command>
```

```
16 <expr> ::= <simple_expr> [<rel><simple_expr>]
```

```
17 <rel> ::= = | <> | < | <= | >= | >
```

```
18 <simple_expr> ::= [+ | -] <term> {(+|-|or)<term>}
```

```
19 <term> ::= <factor> {(* | div | and)<factor>}
```

```
20 <factor> ::= <var> | <num> | (<expr>) | not <factor>
```

```
21 <var> ::= <id> | <id> [<expr>]
```

```
22 <expr_list> ::= <expr> {, <expr>}
```

```
23 <num> ::= <digit>{<digit>}
```

```
24 <digit> ::= 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9
```

```
25 <id> ::= <letter>{<letter> | <digit>}
```

```
26 <letter> ::= _ | a-z | A-Z
```