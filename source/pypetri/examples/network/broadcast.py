
from pypetri import net, trellis, operators

from .link import *

#############################################################################
#############################################################################

class Broadcast(net.Network):
    r"""Connects a collection of Channels with a shared broadcast medium."""
    
    class Broadcast(net.Transition):
        
        class Multiplexer(operators.Multiplexer):
            
            # executes only one input at a time
            def next(self, inputs=iter, **kwargs):
                for input in inputs(self.inputs):
                    for event in input.next(**kwargs):
                        yield event
        
        def Pipe(self):
            return operators.Call()
    
    channels = trellis.make(trellis.List)
    
    @trellis.maintain(make=lambda self: self.Transition(Transition=self.Broadcast))
    def deliver(self):
        transition = self.deliver
        # two-way link to every channel
        for channel in self.channels:
            input = channel.sending.output
            output = channel.receiving.input
            self.linked(transition, output)
            self.linked(input, transition)
        return transition

#############################################################################
#############################################################################
