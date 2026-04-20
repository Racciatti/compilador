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
                <block>.

2 <block> ::= [var_dec_section]
              [subr_dec_section]
              <comp_command>

3 <var_dec_section> ::= <var_dec> {;<var_dec>};

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
                <block>.
```

1 S $\rightarrow$ program ID;BLOCK.

```
2 <block> ::= [var_dec_section]
              [subr_dec_section]
              <comp_command>
```

2 BLOCK $\rightarrow$ VAR_DEC_SECTION SUBR_DEC_SECTION COMP_COMMAND | SUBR_DEC_SECTION COMP_COMMAND | COMP_COMMAND

```
3 <var_dec_section> ::= <var_dec> {;<var_dec>};
```

3.1 VAR_DEC_SECTION $\rightarrow$ VAR_DEC;VAR_DEC_SECTION_1
3.2 VAR_DEC_SECTION_1 $\rightarrow$ VAR_DEC;VAR_DEC_SECTION_1 | $\epsilon$


```
4 <var_dec> ::= <type> <id_list>
```
4 VAR_DEC $\rightarrow$ TYPE ID_LIST

```
5 <id_list> ::= <id>{,id}
```
5.1 ID_LIST $\rightarrow$ ID ID_LIST_1
5.2 ID_LIST_1 $\rightarrow$ ,ID ID_LIST_1 | $\epsilon$ 


```
6 <subr_dec_section> ::= {<proc_dec>;}
```

6 SUBR_DEC_SECTION $\rightarrow$ PROC_DEC; SUBR_DEC_SECTION | $\epsilon$


```
7 <proc_dec> ::= procedure <id> [<formal_params>]; <block>
```

7 PROC_DEC $\rightarrow$ procedure ID; BLOCK | procedure ID FORMAL_PARAMS; BLOCK

```
8 <formal_params> ::= (<formal_params_section> {;<formal_params_section>})
```

8.1 FORMAL_PARAMS $\rightarrow$ (FORMAL_PARAMS_SECTION FORMAL_PARAMS_1)
8.2 FORMAL_PARAMS_1 $\rightarrow$ ;FORMAL_PARAMS_SECTION FORMAL_PARAMS_1 | $\epsilon$ 

```
9 <formal_params_section> ::= [var] <id_list> : <id>
```

9 FORMAL_PARAMS_SECTION $\rightarrow$ VAR ID_LIST : ID | ID_LIST : ID

```
10 <comp_command> ::= begin <command> {; <command>} end
```

10.1 COMP_COMMAND $\rightarrow$ begin COMMAND COMP_COMMAND_1 end
10.2 COMP_COMMAND_1 $\rightarrow$ ;COMMAND COMP_COMMAND_1 | \epsilon 

```
11 <command> ::= <attr> | <proc_call> | <comp_command> | <cond_command 1> | <iter_command 1>
```

11 COMMAND $\rightarrow$ ATTR | PROC_CALL | COMP_COMMAND | COND_COMMAND | ITER_COMMAND

```
12 <attr> ::= <var> := <expr>
```

12 ATTR $\rightarrow$ VAR := EXPR

```
13 <proc_call> ::= <id> [(<expr_list>)]
```

13 PROC_CALL $\rightarrow$ ID | ID(EXPR_LIST)

```
14 <cond_command 1> ::= if <expr> then <command> [else <command>]
```

14 COND_COMMAND $\rightarrow$ if EXPR then COMMAND | if EXPR then COMMAND else COMMAND

```
15 <iter_command 1> ::= while <expr> do <command>
```

15 ITER_COMMAND $\rightarrow$ while EXPR do COMMAND

```
16 <expr> ::= <simple_expr> [<rel><simple_expr>]
```

16 EXPR $\rightarrow$ SIMPLE_EXPR | SIMPLE_EXPR REL SIMPLE_EXPR

```
17 <rel> ::= = | <> | < | <= | >= | >
```

17 REL $\rightarrow$ = | <> | < | <= | >= | >

```
18 <simple_expr> ::= [+ | -] <term> {(+|-|or)<term>}
```

18.1 SIMPLE_EXPR $\rightarrow$ TERM SIMPLE_EXPR_1 | + TERM SIMPLE_EXPR_1 | -TERM SIMPLE_EXPR_1
18.2 SIMPLE_EXPR_1 $\rightarrow$ + TERM SIMPLE_EXPR_1 | -TERM SIMPLE_EXPR_1 | or TERM SIMPLE_EXPR_1 | $\epsilon$

```
19 <term> ::= <factor> {(* | div | and)<factor>}
```

19.1 TERM $\rightarrow$ FACTOR TERM_1
19.2 TERM_1 $\rightarrow$ * FACTOR TERM_1 | div FACTOR TERM_1 | and FACTOR TERM_1 | $\epsilon$ 

```
20 <factor> ::= <var> | <num> | (<expr>) | not <factor>
```

20 FACTOR $\rightarrow$ VAR | NUM | (EXPR) | not FACTOR

```
21 <var> ::= <id> | <id> [<expr>]
```

21 VAR $\rightarrow$ ID | ID [EXPR]


```
22 <expr_list> ::= <expr> {, <expr>}
```

22.1 EXPR_LIST $\rightarrow$ EXPR EXPR_LIST_1
22.2 EXPR_LIST_1 $\rightarrow$ , EXPR EXPR_LIST_1 | $\epsilon$


Since numbers, IDs and letters are treated as atomic tokens, we do not need to use rules 23-26 for this.

**Result:**

1 S $\rightarrow$ program ID;BLOCK

2 BLOCK $\rightarrow$ VAR_DEC_SECTION SUBR_DEC_SECTION COMP_COMMAND | SUBR_DEC_SECTION COMP_COMMAND | COMP_COMMAND

3.1 VAR_DEC_SECTION $\rightarrow$ VAR_DEC;VAR_DEC_SECTION_1

3.2 VAR_DEC_SECTION_1 $\rightarrow$ VAR_DEC;VAR_DEC_SECTION_1 | $\epsilon$

4 VAR_DEC $\rightarrow$ TYPE ID_LIST

5.1 ID_LIST $\rightarrow$ ID ID_LIST_1

5.2 ID_LIST_1 $\rightarrow$ ,ID_LIST_1 | $\epsilon$ 

6 SUBR_DEC_SECTION $\rightarrow$ PROC_DEC; SUBR_DEC_SECTION | $\epsilon$

7 PROC_DEC $\rightarrow$ procedure ID; BLOCK | procedure ID FORMAL_PARAMS; BLOCK

8.1 FORMAL_PARAMS $\rightarrow$ (FORMAL_PARAMS_SECTION FORMAL_PARAMS_1)

8.2 FORMAL_PARAMS_1 $\rightarrow$ ;FORMAL_PARAMS_SECTION FORMAL_PARAMS_1 | $\epsilon$ 

9 FORMAL_PARAMS_SECTION $\rightarrow$ VAR ID_LIST : ID | ID_LIST : ID

10.1 COMP_COMMAND $\rightarrow$ begin COMMAND COMP_COMMAND_1 end

10.2 COMP_COMMAND_1 $\rightarrow$ ;COMMAND COMP_COMMAND_1 | \epsilon 

11 COMMAND $\rightarrow$ ATTR | PROC_CALL | COMP_COMMAND | COND_COMMAND | ITER_COMMAND

12 ATTR $\rightarrow$ VAR := EXPR

13 PROC_CALL $\rightarrow$ ID | ID(EXPR_LIST)

14 COND_COMMAND $\rightarrow$ if EXPR then COMMAND | if EXPR then COMMAND else COMMAND

15 ITER_COMMAND $\rightarrow$ while EXPR do COMMAND

16 EXPR $\rightarrow$ SIMPLE_EXPR | SIMPLE_EXPR REL SIMPLE_EXPR

17 REL $\rightarrow$ = | <> | < | <= | >= | >

18.1 SIMPLE_EXPR $\rightarrow$ TERM SIMPLE_EXPR_1 | + TERM SIMPLE_EXPR_1 | -TERM SIMPLE_EXPR_1

18.2 SIMPLE_EXPR_1 $\rightarrow$ + TERM SIMPLE_EXPR_1 | -TERM SIMPLE_EXPR_1 | or TERM SIMPLE_EXPR_1 | $\epsilon$

19.1 TERM $\rightarrow$ FACTOR TERM_1

19.2 TERM_1 $\rightarrow$ * FACTOR TERM_1 | div FACTOR TERM_1 | and FACTOR TERM_1 | $\epsilon$ 

20 FACTOR $\rightarrow$ VAR | NUM | (EXPR) | not FACTOR

21 VAR $\rightarrow$ ID | ID EXPR

22.1 EXPR_LIST $\rightarrow$ EXPR EXPR_LIST_1

22.2 EXPR_LIST_1 $\rightarrow$ , EXPR EXPR_LIST_1 | $\epsilon$