#!/usr/bin/env python

"""An attempt to implement Xoomonk in Python.  Embryonic, as of this writing;
only includes some runtime support,  no parser.

"""

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
