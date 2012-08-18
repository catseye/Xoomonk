encoding: UTF-8

An attempt to implement Xoomonk in Haskell.  Not entirely successful
(representing malingering updatable stores as immutable data structures is,
well, awkward) and may be abandoned.

> module Xoomonk where

> import Text.ParserCombinators.Parsec
> import qualified Data.Map as Map

AST
---

    Xoomonk ::= { Stmt }.
    Stmt    ::= Assign | Print.
    Assign  ::= Ref ":=" Expr.
    Print   ::= "print" ("string" <string> | "char" Expr | Expr) [";"].
    Expr    ::= (Block | Ref | Const) ["*"].
    Block   ::= "{" { Stmt } "}".
    Ref     ::= Name {"." Name}.
    Name    ::= "^" | "$" <alphanumeric> | <alphanumeric>.
    Const   ::= <integer-literal>.


> data Stmt = Assign Expr Expr -- 1st must be a Ref
>           | Print Expr Bool
>           | PrintString String Bool
>           | PrintChar Expr Bool
>     deriving (Show, Ord, Eq)

> data Expr = Block [Stmt]
>           | Ref [Name]
>           | Const Integer
>           | New Expr
>     deriving (Show, Ord, Eq)

> data Name = Identifier String
>           | Builtin String
>           | Upvalue
>     deriving (Show, Ord, Eq)

Parser
------

> symbol :: String -> Parser ()
> symbol s = do
>     string s
>     spaces

> get :: String -> Parser Bool
> get s = do
>     d <- symbol s
>     return True

Names:

> identifier :: Parser Name
> identifier = do
>     c <- letter
>     cs <- many alphaNum
>     spaces
>     return $ Identifier (c:cs)

> builtin :: Parser Name
> builtin = do
>     string "$"
>     cs <- many alphaNum
>     spaces
>     return $ Builtin cs

> upvalue :: Parser Name
> upvalue = do
>     symbol "^"
>     return Upvalue

> name :: Parser Name
> name = do
>     ((try upvalue) <|>
>      (try builtin) <|>
>      identifier)

Expressions:

> block :: Parser Expr
> block = do
>     symbol "{"
>     l <- many statement
>     symbol "}"
>     return $ Block l

> ref :: Parser Expr
> ref = do
>     names <- sepBy1 name (symbol ".")
>     return (Ref names)

> constant :: Parser Expr
> constant = do
>     i <- many1 digit
>     spaces
>     return $ Const (intval i 0)
>   where
>     intval [] acc = acc
>     intval (digit:rest) acc =
>         intval rest (acc * 10 + digitVal digit)

> digitVal '0' = 0
> digitVal '1' = 1
> digitVal '2' = 2
> digitVal '3' = 3
> digitVal '4' = 4
> digitVal '5' = 5
> digitVal '6' = 6
> digitVal '7' = 7
> digitVal '8' = 8
> digitVal '9' = 9

> bareexpr :: Parser Expr
> bareexpr = do
>     ((try block) <|>
>      (try constant) <|>
>      ref)

> expr :: Parser Expr
> expr = do
>     e <- bareexpr
>     newit <- option False (get "*")
>     case newit of
>         True -> return $ New e
>         False -> return e

Statements:

> trailingsemi :: Parser Bool
> trailingsemi = option False (get ";")

> printexpr :: Parser Stmt
> printexpr = do
>     symbol "print"
>     e <- expr
>     semi <- trailingsemi
>     return $ Print e semi

> printchar :: Parser Stmt
> printchar = do
>     symbol "print"
>     symbol "char"
>     e <- expr
>     semi <- trailingsemi
>     return $ Print e semi

> printstring :: Parser Stmt
> printstring = do
>     symbol "print"
>     symbol "string"
>     char '"'
>     s <- many $ noneOf ['"']
>     char '"'
>     spaces
>     semi <- trailingsemi
>     return $ PrintString s semi

> assignment :: Parser Stmt
> assignment = do
>     lhs <- ref
>     symbol ":="
>     rhs <- expr
>     return $ Assign lhs rhs

> statement :: Parser Stmt
> statement = do
>     ((try printstring) <|>
>      (try printchar) <|>
>      (try printexpr) <|>
>      assignment)

Main:

> program :: Parser Expr
> program = do
>     l <- many statement
>     return $ Block l

Drivers for the parser.

> pa s = case parse program "" s of
>     Left perr -> show perr
>     Right prog -> show prog

> parseFile fileName = do
>     programText <- readFile fileName
>     outputText <- return $ pa programText
>     putStrLn outputText

Static Analysis
---------------

The static analysis phase of Xoomonk is concerned with
detecting whether a store is saturated or unsaturated, and if
the latter, which identifiers inside the store generated
by the block are unassigned.  All others are assumed to be
derived.

Compiler
--------

> compileExpr :: StoreBase -> Expr -> StoreBase

> compileExpr sb e@(Block _) = compileBlock sb e
> compileExpr sb (Ref names) = sb -- XXX
> compileExpr sb (Const i) = sb{ result=(IntVal i) }
> compileExpr sb (New e) =
>     let
>         sb' = compileExpr sb e
>         target = result sb'
>     in
>         sb'{ result=(copyValue target) }

> compileBlock sb (Block []) = sb
> compileBlock sb (Block (s:ss)) =
>     let
>         sb' = compileStmt sb s
>     in
>         compileBlock sb' $ Block ss

> compileStmt sb (Assign e1 e2) = sb -- XXX
> compileStmt sb (Print e noNewLine) = sb -- XXX
> compileStmt sb (PrintString s noNewLine) = sb -- XXX
> compileStmt sb (PrintChar e noNewLine) = sb -- XXX

> compileName sb (Identifier s) = sb -- XXX get s from current store
> compileName sb (Builtin "add") = sb -- XXX get a magical store based on builtin's name
> compileName sb (Builtin "sub") = sb -- XXX get a magical store based on builtin's name
> compileName sb (Builtin "mul") = sb -- XXX get a magical store based on builtin's name
> compileName sb (Builtin "div") = sb -- XXX get a magical store based on builtin's name
> compileName sb (Builtin "gt") = sb -- XXX get a magical store based on builtin's name

> compileName sb Upvalue = sb -- XXX get the store that is the lexical encloser of the current store

Runtime
-------

> data Value = IntVal Integer
>            | StoreVal StoreID
>     deriving (Show, Ord, Eq)

> type Store = Map.Map String Value

> type StoreID = Integer

A StoreBase contains all the stores.  It must make
each of them independently accessible, as the language
supports aliasing the same store in two different
variables.  It also contains some other state of the
evaluation, including the last result, the ID of the
current store, the next ID to be used when allocating
a new store, etc.  Lame for now.

> data StoreBase = StoreBase { baseMap :: Map.Map StoreID Store
>                            , parentMap :: Map.Map StoreID StoreID
>                            , result :: Value
>                            , currentStoreID :: StoreID
>                            , nextStoreID :: StoreID
>                            } deriving (Show, Ord, Eq)

> newStoreBase = StoreBase {
>                  baseMap=Map.empty,
>                  parentMap=Map.empty,
>                  result=(IntVal 0),
>                  currentStoreID=0,
>                  nextStoreID=0
>                }

> getStore StoreBase{ baseMap=b } id =
>     Map.lookup id b
> currentStore sb@StoreBase{ currentStoreID=c } =
>     case getStore sb c of
>         Just store -> store

> lookupName sb names = lookupNameIn (currentStore sb) sb names

> lookupNameIn store sb [Identifier k] =
>     let
>         Just value = Map.lookup k store
>     in
>         value
> lookupNameIn store sb ((Identifier k):rest) =
>     case Map.lookup k store of
>         Just (StoreVal id) ->
>             let
>                 Just store' = getStore sb id
>             in
>                 lookupNameIn store' sb rest

> copyValue (IntVal i) = IntVal i
> copyValue (StoreVal id) = StoreVal id -- XXX

Evaluator
---------

> evalExpr sb (Block []) = sb
> evalExpr sb (Block (s:ss)) =
>     let
>         sb' = evalStmt sb s
>     in
>         evalExpr sb' $ Block ss

> evalExpr sb (Ref names) = sb -- XXX
> evalExpr sb (Const i) = sb{ result=(IntVal i) }
> evalExpr sb (New e) =
>     let
>         sb' = evalExpr sb e
>         target = result sb'
>     in
>         sb'{ result=(copyValue target) }

> evalStmt sb (Assign e1 e2) = sb -- XXX
> evalStmt sb (Print e noNewLine) = sb -- XXX
> evalStmt sb (PrintString s noNewLine) = sb -- XXX
> evalStmt sb (PrintChar e noNewLine) = sb -- XXX

> evalName sb (Identifier s) = sb -- XXX get s from current store
> evalName sb (Builtin "add") = sb -- XXX get a magical store based on builtin's name
> evalName sb (Builtin "sub") = sb -- XXX get a magical store based on builtin's name
> evalName sb (Builtin "mul") = sb -- XXX get a magical store based on builtin's name
> evalName sb (Builtin "div") = sb -- XXX get a magical store based on builtin's name
> evalName sb (Builtin "gt") = sb -- XXX get a magical store based on builtin's name

> evalName sb Upvalue = sb -- XXX get the store that is the lexical encloser of the current store
