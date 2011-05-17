# @copyright
# @license

r"""Control flow plumbing.

Every component is directional, with some set of inputs and outputs.
To push something into a component, call 'send'.
To iterate over possible events, use 'next'.
"""


from . import trellis

#############################################################################
#############################################################################

def nada(*args, **kwargs):
    pass

def pass_in(self):
    try:
        return self.input.next
    except AttributeError:
        return nada

def pass_out(self):
    try:
        return self.output.send
    except AttributeError:
        return nada

#############################################################################
#############################################################################

class Component(trellis.Component):
    
    send = classmethod(nada)
    next = classmethod(nada)


class Pipe(Component):
    
    input = trellis.attr(None)
    output = trellis.attr(None)

    next = trellis.compute(pass_in)
    send = trellis.compute(pass_out)

    @trellis.compute
    def connected(self):
        return None not in (self.input, self.output,)

    
class Multiplexer(Component):

    inputs = trellis.attr(None)
    output = trellis.attr(None)

    send = trellis.compute(pass_out)

class Demultiplexer(Component):

    input = trellis.attr(None)
    outputs = trellis.attr(None)

    next = trellis.compute(pass_in)
    
class Switch(Component):
    
    inputs = trellis.attr(None)
    outputs = trellis.attr(None)

#############################################################################
#############################################################################
