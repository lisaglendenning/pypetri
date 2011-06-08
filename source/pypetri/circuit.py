# @copyright
# @license

r"""Control flow plumbing.

Every component is directional, with some set of inputs and outputs.
To push some input into a component, call 'send'.
To iterate over possible inputs, call 'next'.
"""

#############################################################################
#############################################################################

def nada(*args, **kwargs):
    pass

class Component(object):
    r"""Base component."""

    def pass_in(self, input):
        if isinstance(input, Component):
            return input.next
        else:
            return nada
    
    def pass_out(self, output):
        if isinstance(output, Component):
            return output.send
        else:
            return nada
            
    send = classmethod(nada)
    next = classmethod(nada)

#############################################################################
#############################################################################

class Pipe(Component):
    r"""One input to one output."""
    
    input = None
    output = None

    def next(self, *args, **kwargs):
        f = self.pass_in(self.input)
        return f(*args, **kwargs)
    
    def send(self, *args, **kwargs):
        f = self.pass_out(self.output)
        return f(*args, **kwargs)

    
class Multiplexer(Component):
    r"""Multiple inputs to one output."""

    inputs = None
    output = None

    def send(self, *args, **kwargs):
        f = self.pass_out(self.output)
        return f(*args, **kwargs)


class Demultiplexer(Component):
    r"""One input to multiple outputs."""

    input = None
    outputs = None

    def next(self, *args, **kwargs):
        f = self.pass_in(self.input)
        return f(*args, **kwargs)
    

class Switch(Component):
    r"""Multiple inputs to multiple outputs."""
    
    inputs = None
    outputs = None

#############################################################################
#############################################################################
