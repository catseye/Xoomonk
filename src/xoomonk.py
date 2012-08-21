#!/usr/bin/env python

"""An attempt to implement Xoomonk in Python.

"""

import re

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
    >>> a.check_type('literal')
    Traceback (most recent call last):
    ...
    SyntaxError: Expected literal, but found operator (':=')
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

    def scan_pattern(self, pattern):
        pattern = r'^(' + pattern + r')(.*?)$'
        match = re.match(pattern, self.text)
        if not match:
            return False
        else:
            self.token = match.group(1)
            self.text = match.group(2)
            return True

    def scan(self):
        self.scan_pattern(r'\s+')
        if not self.text:
            self.token = None
            self.type = 'EOF'
            return
        if self.scan_pattern(r':=|\;|\{|\}|\*|\.|\^|\$'):
            self.type = 'operator'
            return
        if self.scan_pattern(r'\d+'):
            self.type = 'literal'
            return
        if self.scan_pattern(r'\w+'):
            self.type = 'identifier'
            return

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
    123
    >>> a = Parser("{ a := 123 }")
    >>> a.expr()
    (block)

    """
    def __init__(self, text):
        self.scanner = Scanner(text)

    def program(self):
        while not self.scanner.at_end():
            self.stmt()

    def stmt(self):
        if self.scanner.on("print"):
            self.print_stmt()
        else:
            self.assign()

    def assign(self):
        self.ref()
        self.scanner.expect(":=")
        self.expr()

    def print_stmt(self):
        self.scanner.expect("print")
        if self.scanner.consume("string"):
            st = self.scanner.token
            self.scanner.scan()
        elif self.scanner.consume("char"):
            self.expr()
        else:
            self.expr()
        if self.scanner.consume(";"):
            # mark as no nl
            pass

    def expr(self):
        v = None
        if self.scanner.on("{"):
            v = self.block()
        elif self.scanner.on_type('literal'):
            v = int(self.scanner.token)
        else:
            v = self.ref()
        if self.scanner.consume("*"):
            # v = copy(v)
            pass
        return v

    def block(self):
        self.scanner.expect("{")
        while not self.scanner.on("}"):
            self.stmt()
        self.scanner.expect("}")

    def ref(self):
        self.name()
        while self.scanner.consume("."):
            self.name()

    def name(self):
        if self.scanner.consume("^"):
            return "^"
        elif self.scanner.consume("$"):
            self.scanner.check_type("identifier")
            id = self.scanner.token
            self.scanner.scan()
            return id
        else:
            self.scanner.check_type("identifier")
            id = self.scanner.token
            self.scanner.scan()
            return id


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


if __name__ == "__main__":
    import doctest
    (fails, something) = doctest.testmod()
    if fails == 0:
        print "All tests passed."
        exit_code = 0
    else:
        exit_code = 1
