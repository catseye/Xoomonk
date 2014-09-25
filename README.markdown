The Xoomonk Programming Language
================================

Language version 1.0

Abstract
--------

_Xoomonk_ is a programming language in which _malingering updatable stores_
are first-class objects.  Malingering updatable stores unify several language
constructs, including procedure activations, named parameters, and object-like
data structures.

    -> Functionality "Interpret Xoomonk program" is implemented by
    -> shell command "python src/xoomonk.py %(test-body-file)"

    -> Tests for functionality "Interpret Xoomonk program"

Description
-----------

Overall, Xoomonk looks like a "typical" imperative language.  The result
of evaluating an expression can be assigned to a variable, and the contents
of a variable can be used in a subsequent expression.

    | a := 1
    | b := a
    | print b
    = 1

Like most typical imperative languages, a block (delimited by curly braces)
may contain a sequence of imperative statements.  However, such blocks may
appear as terms in expressions; here they evaluate to entire updatable stores.

    | a := {
    |   c := 5
    |   d := c
    | }
    | print a
    = [c=5,d=5]

Once created, a store can be updated and accessed.

    | a := {
    |   c := 5
    |   d := c
    | }
    | print a
    | a.d := 7
    | print a
    | print a.c
    = [c=5,d=5]
    = [c=5,d=7]
    = 5

A store can also be assigned to a variable after creation.  Stores are
accessed by reference, so this creates two aliases to the same store.

    | a := {
    |   c := 5
    |   d := c
    | }
    | b := a
    | b.c := 17
    | print a
    | print b
    = [c=17,d=5]
    = [c=17,d=5]

To create an independent copy of the store, the postfix `*` operator is
used.

    | a := {
    |   c := 5
    |   d := c
    | }
    | b := a*
    | b.c := 17
    | print a
    | print b
    = [c=5,d=5]
    = [c=17,d=5]

Empty blocks are permissible.

    | a := {}
    | print a
    = []

Once a store has been created, only those variables used in the store can be
updated and accessed — new variables cannot be added.

    | a := { b := 6 }
    | print a.c
    ? Attempt to access undefined variable c

    | a := { b := 6 }
    | a.c := 12
    ? Attempt to assign undefined variable c

In the outermost level, as well, a variable cannot be used before it
has been assigned.

    | print r
    | r := 5
    ? Attempt to access undefined variable r

Stores and integers are the only two data types in Xoomonk.  However, there
are some special forms of the print statement, demonstrated here, which
allow for textual output.

    | a := 65
    | print char a
    | print string "Hello, world!"
    | print string "The value of a is ";
    | print a;
    | print string "!"
    = A
    = Hello, world!
    = The value of a is 65!

Xoomonk enforces strict block scope.  Variables can be shadowed in an
inner block.

    | a := 14
    | b := {
    |   a := 12
    |   print a
    | }
    | print a
    = 12
    = 14

We now present today's main feature.

It's important to understand that a block need not define all the variables
used in it.  That is, a block may contain variables which are used, but never
assigned a value, in the block.  Such blocks do not immediately evaluate to a
store.  Instead, they evaluate to an object called an _unsaturated store_.

Or, to put it another way:

If, in a block, you refer to a variable which has not yet been given
a value in that updatable store, the computations within the block are not
performed until that variable is given a value.  Such a store is called an
_unsaturated store_.

    | a := {
    |   d := c
    | }
    | print a
    = [c=?,d=0]

An unsaturated store behaves similarly to a saturated store in certain
respects.  In particular, unsaturated stores can be updated.  If doing
so means that all of the undefined variables in the store are now defined,
the block associated with that store is evaluated, and the store becomes
saturated.  In this sense, an unsaturated store is like a promise, and
this bears some resemblance to lazy evaluation (thus the term _malingering_).

    | a := {
    |   print string "executing block"
    |   d := c
    | }
    | print a
    | a.c := 7
    | print a
    = [c=?,d=0]
    = executing block
    = [c=7,d=7]

Once a store has become saturated, the block associated with it is not
executed again.

    | a := {
    |   d := c
    | }
    | a.c := 7
    | print a
    | a.c := 4
    | print a
    = [c=7,d=7]
    = [c=4,d=7]

Saturating one copy of an unsaturated store will not saturate the other
copy.

    | a := {
    |   print string "saturated"
    |   d := c
    | }
    | b := a*
    | print a
    | print b
    | a.c := 7
    | print a
    | print b
    | b.c := 5
    | print b
    = [c=?,d=0]
    = [c=?,d=0]
    = saturated
    = [c=7,d=7]
    = [c=?,d=0]
    = saturated
    = [c=5,d=5]

Unassigned variables cannot be accessed from an unsaturated store.

    | a := {
    |   d := c
    | }
    | x := a.c
    ? Attempt to access unassigned variable c

Assigned variables can be accessed from an unsaturated store, but they have
the value 0 until the store is saturated.

    | a := {
    |   d := c
    | }
    | print a.d
    = 0

This is true, even if the variable is assigned a constant expression
inside the block.

    | a := {
    |   b := 7
    |   d := c
    | }
    | print a.b
    = 0

If, however, the unsaturated store contains some unassigned variables that have
been updated since the store was created, those variable may be accessed, even
if the store is still unsaturated.

    | a := {
    |   print string "executing block"
    |   p := q
    |   d := c
    | }
    | a.q := 7
    | print a.q
    = 7

It is possible to assign a variable in an unsaturated store which is
assigned somewhere in the block.  When the store becomes saturated, however,
that variable will be overwritten.

    | a := {
    |   b := 7
    |   d := c
    | }
    | a.b := 4
    | print a
    = [b=4,c=?,d=0]

    | a := {
    |   b := 7
    |   d := c
    | }
    | a.b := 4
    | a.c := 4
    | print a
    = [b=7,c=4,d=4]

It's important to note that a block is considered saturated when all the
variables *used* in the block are *assigned* somewhere in the block.  If, in a
block, a variable is used before it is assigned, the block will *still* be
executed, if saturated.

    | a := {
    |   c := b
    | }
    | a.b := 5
    | print a
    = [b=5,c=5]

    | a := {
    |   b := b
    | }
    ? Attempt to access undefined variable b

A way to work around this is to add an extra unassigned variable, to keep
the store unsaturated.

    | a := {
    |   print string "executing block"
    |   l := b
    |   b := 3
    |   l := 3
    | }
    | print string "saturating store"
    | a.b := 5
    | print a
    ? Attempt to access undefined variable b

    | a := {
    |   print string "executing block"
    |   l := b
    |   b := 3
    |   l := c
    |   l := 3
    | }
    | print string "saturating store"
    | a.b := 5
    | a.c := 9
    | print a
    = saturating store
    = executing block
    = [b=3,c=9,l=3]

We now describe how this language is (we reasonably assume) Turing-complete.

Firstly, there is a built-in special store called `$`, which is a Special
Name which is magically available in every scope and which cannot be assigned
to, but which can be modified.

    | $ := 4
    ? Cannot assign to $

    | $.foo := 4
    | print string "ok"
    = ok

Since `$` is available in every scope, it can be thought of as being the
"global scope", and can be conveniently used to communicate values across
scopes.

    | $.r := 4
    | q := {
    |   print string "hello"
    |   c := $.r
    |   j := d
    | }
    | q.d := 5
    | print q.c
    = hello
    = 4

Operations are accomplished with certain built-in unsaturated stores.  For
example, there is a store called `add`, which can be used for addition.  These
built-in stores are all located in the `$` store.

    | print $.add
    = [result=0,x=?,y=?]

    | a := {
    |   print $.add
    | }
    = [result=0,x=?,y=?]

    | $.add.x := 3
    | $.add.y := 5
    | print $.add.result
    | print $.add
    = 8
    = [result=8,x=3,y=5]

Because using a built-in operation store in this way saturates it, it cannot
be used again.  Typically, you will want to make a copy of the store first, and
use that copy, leaving the built-in store unmodified.

    | o1 := $.add*
    | o1.x := 4
    | o1.y := 7
    | o2 := $.add*
    | o2.x := o1.result
    | o2.y := 9
    | print o2.result
    = 20

Since Xoomonk is not a strictly minimalist language, there is a selection
of built-in stores which provide useful operations: `$.add`, `$.sub`, `$.mul`,
`$.div`, `$.gt`, and `$.not`.

    | o1 := $.sub*
    | o1.x := 7
    | o1.y := 4
    | print o1.result
    = 3

    | o1 := $.mul*
    | o1.x := 7
    | o1.y := 4
    | print o1.result
    = 28

    | o1 := $.div*
    | o1.x := 29
    | o1.y := 4
    | print o1.result
    = 7

    | o1 := $.gt*
    | o1.x := 29
    | o1.y := 4
    | print o1.result
    = 1

    | o1 := $.gt*
    | o1.x := 4
    | o1.y := 4
    | print o1.result
    = 0

    | o1 := $.not*
    | o1.x := 29
    | print o1.result
    = 0

    | o1 := $.not*
    | o1.x := 0
    | print o1.result
    = 1

Decision-making is also accomplished with a built-in store, `$.if`.  This store
contains variables caled `cond`, `then`, and `else`.  `cond` should
be an integer, and `then` and `else` should be unsaturated stores where `x` is
unassigned.  When the first three are assigned values, if `cond` is nonzero,
it is assigned to `x` in the `then` store; otherwise, if it is zero, it is
assigned to `x` in the `else` store.

    | o1 := $.if*
    | o1.then := {
    |   y := x
    |   print string "condition is true"
    | }
    | o1.else := {
    |   y := x
    |   print string "condition is false"
    | }
    | o1.cond := 0
    = condition is false

    | o1 := $.if*
    | o1.then := {
    |   y := x
    |   print string "condition is true"
    | }
    | o1.else := {
    |   y := x
    |   print string "condition is false"
    | }
    | o1.cond := 1
    = condition is true

Repetition is also accomplished with a built-in store, `$.loop`.  This store
contains an unassigned variable called `do`.  When it is assigned a value,
assumed to be an unsaturated store, a copy of that unsaturated store is made.
The variable `x` inside that copy is assigned the value 0.  This is supposed
to saturate the store.  The variable `continue` is then accessed from the
store.  If it is nonzero, the process repeats, with another copy of the `do`
store getting 0 assigned to its `x`, and so forth.

    | l := $.loop*
    | $.counter := 5
    | l.do := {
    |   y := x
    |   print $.counter
    |   o := $.sub*
    |   o.x := $.counter
    |   o.y := 1
    |   $.counter := o.result
    |   continue := o.result
    | }
    | print string "done!"
    = 5
    = 4
    = 3
    = 2
    = 1
    = done!

Because the `$.loop` construct will always execute the `do` store at least once
(even assuming its only unassigned variable is `x`), it acts like a so-called
`repeat` loop.  It can be used in conjunction with `$.if` to simulate a
so-called `while` loop.  With this loop, the built-in operations provided,
and variables which may contain unbounded integer values, Xoomonk should
be uncontroversially Turing-complete.  (Although admittedly, using an unbounded
integer or two to simulate a Turing machine's tape, especially with Xoomonk's
arithmetic operations, would be fairly cumbersome.)

Finally, there is no provision for defining functions or procedures, because
malingering stores can act as these constructs.

    | perimeter := {
    |   o1 := $.mul*
    |   o1.x := x
    |   o1.y := 2
    |   o2 := $.mul*
    |   o2.x := y
    |   o2.y := 2
    |   o3 := $.add*
    |   o3.x := o1.result
    |   o3.y := o2.result
    |   result := o3.result
    | }
    | p1 := perimeter*
    | p1.x := 13
    | p1.y := 6
    | print p1.result
    | p2 := perimeter*
    | p2.x := 4
    | p2.y := 1
    | print p2.result
    = 38
    = 10

Grammar
-------

    Xoomonk ::= { Stmt }.
    Stmt    ::= Assign | Print.
    Assign  ::= Ref ":=" Expr.
    Print   ::= "print" ("string" <string> | "char" Expr | Expr) [";"].
    Expr    ::= (Block | Ref | Const) ["*"].
    Block   ::= "{" { Stmt } "}".
    Ref     ::= Name {"." Name}.
    Name    ::= "$" | <alphanumeric>.
    Const   ::= <integer-literal>.

Discussion
----------

There is some similarity with Wouter van Oortmerssen's language Bla, in that
function environments are very close cousins of updatable stores.  But
Xoomonk, quite unlike Bla, is an imperative language; once created, a store
may be updated at any point.  And, of course, this property is exploited in
the introduction of malingering stores.

The original idea for Xoomonk had an infix operator `&`, which took two stores
as its arguments (at least one of which must be saturated) and evaluated to a
third store which was the result of merging the two argument stores.  This
result store may be saturated even if only one of the argument stores was
saturated, if the saturated store gave all the values that the unsaturated
store needed.  This operator was dropped because it is mostly just syntactic
sugar for assigning each of the desired variables from one store to the other.
However, it does admittedly provide a very natural syntax, which orthogonally
includes "named arguments", when using unsaturated stores as procedures:

    perimeter = {
      # see example above
    }
    g := perimeter* & { x := 13 y := 6 }
    print g.result

Xoomonk 0.1 had slightly more sophisticated semantics for unsaturated stores
than Xoomonk 1.0 has.  Specifically, there was a (fuzzy) idea that a variable
could be "unresolved", that is, assigned a value derived from variables which
were unassigned.  Xoomonk 1.0 simplified this to assigned variables having
the value 0 until the store is saturated, and a store being saturated when
all of its unassigned variables have been given a value, even if some
assigned variables are used in the block before they have ever been assigned.
Xoomonk 1.0 also dropped the idea that the main program was a block.

In addition, in Xoomonk 0.1, `$` was an prefix operator rather than a
Special Name, and the Special Name `^` allowed access to the lexically
enclosing store of a block.  While there is a certain elegance to this, it
was deemed overkill, and in Xoomonk 1.0, `$` was changed to a Special Name
which referred to a global store (which can be used to communicate values
between scopes without messing about with lexically enclosing "upvalues".)

Xoomonk, as a project, was also an early experiment in _test-driven language
design_.  When Xoomonk 0.1 was released, the language was described only with
the set of examples (above) written in Falderal format, each of which both
illustrates some aspect of the language, and is used as a test case.  When a
reference interpreter was implemented for Xoomonk 1.0, this made implementation
much easier.  (Since Xoomonk 0.1 was released, I've used this technique
successfully for several other languages as well.)

Happy malingering!

-Chris Pressey  
Cat's Eye Technologies  
August 7, 2011  
Evanston, IL
