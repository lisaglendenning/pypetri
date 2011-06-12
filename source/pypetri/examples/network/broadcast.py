
from pypetri import net, trellis, operators

from .link import *

#############################################################################
#############################################################################
# TODO: can make channel set dynamic?
class Broadcast(net.Network):
    r"""Connects a fixed array of Channels with a shared broadcast medium."""
    
    class Broadcast(net.Transition):
        
        class Multiplexer(operators.Multiplexer):
            
            # executes only one input at a time
            def next(self, inputs=iter, **kwargs):
                for input in inputs(self.inputs):
                    for event in input.next(**kwargs):
                        yield event
        
        def Pipe(self):
            return operators.Call()
    
    def Transition(self, *args, **kwargs):
        return super(Broadcast, self).Transition(Transition=self.Broadcast, *args, **kwargs)
    
    @trellis.modifier
    def Arcs(self):
        transition = self.deliver
        # two-way link to every channel
        for channel in self.channels:
            input = channel.sending.output
            output = channel.receiving.input
            self.Arc(transition, output)
            self.Arc(input, transition)
            
    def __init__(self, *args, **kwargs):
        super(Broadcast, self).__init__(*args, **kwargs)
        self.Arcs()
        
    channels = trellis.make(tuple)
    deliver = trellis.make(lambda self: self.Transition())

#############################################################################
#############################################################################
