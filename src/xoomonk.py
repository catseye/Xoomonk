#!/usr/bin/env python

"""An attempt to implement Xoomonk in Python.

"""

from optparse import OptionParser
import re
import sys


class AST(object):
    def __init__(self, type, children=None, value=None):
        self.type = type
        self.value = value
        if children is not None:
            self.children = children
        else:
            self.children = []

    def add_child(self, item):
        self.children.append(item)

    def __repr__(self):
        if self.value is None:
            return 'AST(%r,%r)' % (self.type, self.children)
        return 'AST(%r,value=%r)' % (self.type, self.value)


class Scanner(object):
    """A Scanner provides facilities for extracting successive
    Xoomonk tokens from a string.

    >>> a = Scanner("  {:= }  foo  ")
    >>> a.token
    '{'
    >>> a.type
    'operator'
    >>> a.scan()
    >>> a.on(":=")
    True
    >>> a.on_type('operator')
    True
    >>> a.check_type('identifier')
    Traceback (most recent call last):
    ...
    SyntaxError: Expected identifier, but found operator (':=')
    >>> a.scan()
    >>> a.consume(".")
    False
    >>> a.consume("}")
    True
    >>> a.expect("foo")
    >>> a.type
    'EOF'
    >>> a.expect("bar")
    Traceback (most recent call last):
    ...
    SyntaxError: Expected 'bar', but found 'None'

    """
    def __init__(self, text):
        self.text = text
        self.token = None
        self.type = None
        self.scan()

    def scan_pattern(self, pattern, type, token_group=1, rest_group=2):
        pattern = r'^(' + pattern + r')(.*?)$'
        match = re.match(pattern, self.text, re.DOTALL)
        if not match:
            return False
        else:
            self.type = type
            self.token = match.group(token_group)
            self.text = match.group(rest_group)
            #print >>sys.stderr, "(%r/%s->%r)" % (self.token, self.type, self.text)
            return True

    def scan(self):
        self.scan_pattern(r'[ \t\n\r]*', 'whitespace')
        if not self.text:
            self.token = None
            self.type = 'EOF'
            return
        if self.scan_pattern(r':=|\;|\{|\}|\*|\.|\^|\$', 'operator'):
            return
        if self.scan_pattern(r'\d+', 'integer literal'):
            return
        if self.scan_pattern(r'\"(.*?)\"', 'string literal',
                             token_group=2, rest_group=3):
            return
        if self.scan_pattern(r'\w+', 'identifier'):
            return
        if self.scan_pattern(r'.', 'unknown character'):
            return
        else:
            raise ValueError, "this should never happen, self.text=(%s)" % self.text

    def expect(self, token):
        if self.token == token:
            self.scan()
        else:
            raise SyntaxError("Expected '%s', but found '%s'" %
                              (token, self.token))

    def on(self, token):
        return self.token == token

    def on_type(self, type):
        return self.type == type

    def check_type(self, type):
        if not self.type == type:
            raise SyntaxError("Expected %s, but found %s ('%s')" %
                              (type, self.type, self.token))

    def consume(self, token):
        if self.token == token:
            self.scan()
            return True
        else:
            return False


# Parser

class Parser(object):
    """A Parser provides facilities for recognizing various
    parts of a Xoomonk program based on Xoomonk's grammar.

    >>> a = Parser("123")
    >>> a.expr()
    AST('IntLit',value=123)
    >>> a = Parser("{ a := 123 }")
    >>> a.expr()
    AST('Block',[AST('Assignment',[AST('Ref',[AST('Identifier',value='a')]), AST('IntLit',value=123)])])

    >>> a = Parser("a:=5 c:=4")
    >>> a.program()
    AST('Program',[AST('Assignment',[AST('Ref',[AST('Identifier',value='a')]), AST('IntLit',value=5)]), AST('Assignment',[AST('Ref',[AST('Identifier',value='c')]), AST('IntLit',value=4)])])

    >>> a = Parser("a := { b := 1 }")
    >>> a.program()
    AST('Program',[AST('Assignment',[AST('Ref',[AST('Identifier',value='a')]), AST('Block',[AST('Assignment',[AST('Ref',[AST('Identifier',value='b')]), AST('IntLit',value=1)])])])])

    """
    def __init__(self, text):
        self.scanner = Scanner(text)

    def program(self):
        p = AST('Program')
        while self.scanner.type != 'EOF':
            p.add_child(self.stmt())
        return p

    def stmt(self):
        if self.scanner.on("print"):
            return self.print_stmt()
        else:
            return self.assign()

    def assign(self):
        r = self.ref()
        self.scanner.expect(":=")
        e = self.expr()
        return AST('Assignment', [r, e])

    def print_stmt(self):
        s = None
        self.scanner.expect("print")
        if self.scanner.consume("string"):
            self.scanner.check_type("string literal")
            st = self.scanner.token
            self.scanner.scan()
            s = AST('PrintString', value=st)
        elif self.scanner.consume("char"):
            e = self.expr()
            s = AST('PrintChar', [e])
        else:
            e = self.expr()
            s = AST('Print', [e])
        newline = True
        if self.scanner.consume(";"):
            newline = False
        if newline:
            s = AST('Newline', [s])
        return s

    def expr(self):
        v = None
        if self.scanner.on("{"):
            v = self.block()
        elif self.scanner.on_type('integer literal'):
            v = AST('IntLit', value=int(self.scanner.token))
            self.scanner.scan()
        else:
            v = self.ref()
        if self.scanner.consume("*"):
            v = AST('CopyOf', [v])
        return v

    def block(self):
        b = AST('Block')
        self.scanner.expect("{")
        while not self.scanner.on("}"):
            b.add_child(self.stmt())
        self.scanner.expect("}")
        return b

    def ref(self):
        r = AST('Ref')
        r.add_child(self.name())
        while self.scanner.consume("."):
            r.add_child(self.name())
        return r

    def name(self):
        if self.scanner.consume("^"):
            return AST('Upvalue')
        elif self.scanner.consume("$"):
            self.scanner.check_type("identifier")
            id = self.scanner.token
            self.scanner.scan()
            return AST('Dollar', value=id)
        else:
            self.scanner.check_type("identifier")
            id = self.scanner.token
            self.scanner.scan()
            return AST('Identifier', value=id)


# Runtime support for Xoomonk.

def demo(store):
    print "demo!"

class MalingeringStore(object):
    """
    >>> a = MalingeringStore(['a','b'], [], demo)
    demo!
    >>> a['a'] = 7
    >>> print a['a']
    7
    >>> a['c'] = 7
    Traceback (most recent call last):
    ...
    ValueError: Attempt to assign undefined variable c
    >>> a = MalingeringStore(['a','b'], ['a'], demo)
    >>> a['a'] = 7
    demo!
    >>> a = MalingeringStore(['a','b'], ['a'], demo)
    >>> a['b'] = 7
    Traceback (most recent call last):
    ...
    ValueError: Attempt to assign unresolved variable b

    """
    def __init__(self, variables, unassigned, fun):
        self.dict = {}
        self.variables = variables
        for variable in self.variables:
            self.dict[variable] = 0
        self.unassigned = unassigned
        self.fun = fun
        if not self.unassigned:
            self.run()
    
    def run(self):
        self.fun(self)

    def __getitem__(self, name):
        if name not in self.variables:
            raise ValueError("Attempt to access undefined variable %s" % name)
        # check to see if it is unassigned or derived
        return self.dict[name]

    def __setitem__(self, name, value):
        if name not in self.variables:
            raise ValueError("Attempt to assign undefined variable %s" % name)          
        if name in self.unassigned:
            self.dict[name] = value
            self.unassigned.remove(name)
            if not self.unassigned:
                self.run()
        elif self.unassigned:
            raise ValueError("Attempt to assign unresolved variable %s" % name)          
        else:
            # the store is saturated, do what you want
            self.dict[name] = value


def eval_xoomonk(ast, state):
    type = ast.type
    if type == 'Program':
        for node in ast.children:
            eval_xoomonk(node, state)
        return 0
    elif type == 'Assignment':
        # XXX not the real deal yet.
        ref = ast.children[0]
        name = ref.children[0].value
        value = eval_xoomonk(ast.children[1], state)
        state[name] = value
        return value
    elif type == 'PrintString':
        sys.stdout.write(ast.value)
    elif type == 'PrintChar':
        value = eval_xoomonk(ast.children[0], state)
        sys.stdout.write(chr(value))
        return 0
    elif type == 'Print':
        value = eval_xoomonk(ast.children[0], state)
        sys.stdout.write(str(value))
        return 0
    elif type == 'Newline':
        eval_xoomonk(ast.children[0], state)
        sys.stdout.write('\n')
        return 0
    elif type == 'Ref':
        # XXX not the real deal yet.
        name = ast.children[0].value
        return state.get(name, 0)
    elif type == 'IntLit':
        return ast.value
    else:
        raise NotImplementedError, "not an AST type I know: %s" % type


def main(argv):
    optparser = OptionParser(__doc__)
    optparser.add_option("-a", "--show-ast",
                         action="store_true", dest="show_ast", default=False,
                         help="show parsed AST before evaluation")
    optparser.add_option("-t", "--test",
                         action="store_true", dest="test", default=False,
                         help="run test cases and exit")
    (options, args) = optparser.parse_args(argv[1:])
    if options.test:
        import doctest
        (fails, something) = doctest.testmod()
        if fails == 0:
            print "All tests passed."
            sys.exit(0)
        else:
            sys.exit(1)
    file = open(args[0])
    text = file.read()
    file.close()
    p = Parser(text)
    ast = p.program()
    if options.show_ast:
        print repr(ast)
    result = eval_xoomonk(ast, {})
    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)
