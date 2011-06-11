# @copyright
# @license

from __future__ import absolute_import

import collections

from .. import trellis

#############################################################################
#############################################################################

class Queue(trellis.Component, collections.Sequence):

    maxlen = trellis.attr(None)
    changes = trellis.todo(list)
    to_change = changes.future
    
    def Queue(self):
        return collections.deque(maxlen=self.maxlen)
    
    def __init__(self, iterable=None, maxlen=None):
        super(Queue, self).__init__(maxlen=maxlen)
        if iterable:
            self.extend(iterable)
    
    @trellis.modifier
    def _change(self, attr, *args):
        to_change = self.to_change
        to_change.append((attr, args))
    
    @trellis.compute
    def __len__(self):
        return self._data.__len__

    @trellis.compute
    def __getitem__(self):
        return self._data.__getitem__
    
    @trellis.compute
    def __iter__(self):
        return self._data.__iter__
    
    def __nonzero__(self):
        return len(self) > 0
    
    def __getstate__(self):
        return tuple(self._data)
    
    @trellis.modifier
    def __setstate__(self, state):
        self.clear()
        self.extend(state)
    
    @trellis.compute
    def __repr__(self):
        text = '%s%s' % (self.__class__.__name__, str(self))
        return lambda: text
    
    @trellis.compute
    def __str__(self):
        text = repr(self.__getstate__())
        return lambda: text
    
    @trellis.maintain(make=lambda self: self.Queue())
    def _data(self):
        data = self._data
        changes = self.changes
        if changes:
            for fn, args in changes:
                if fn == 'append':
                    data.append(args[0])
                    trellis.on_undo(data.pop)
                elif fn == 'appendleft':
                    data.appendleft(args[0])
                    trellis.on_undo(data.popleft)
                elif fn == 'pop':
                    v = data.pop()
                    trellis.on_undo(data.append, v)
                elif fn == 'popleft':
                    v = data.popleft()
                    trellis.on_undo(data.appendleft, v)
                elif fn == 'clear':
                    v = data.copy()
                    data.clear()
                    trellis.on_undo(data.extend, v)
                else:
                    raise RuntimeError(fn)
            trellis.mark_dirty()
        return data

    def append(self, item):
        self._change('append', item)

    def appendleft(self, item):
        self._change('appendleft', item)
        
    def pop(self):
        self._change('pop')
        
    def popleft(self):
        self._change('popleft')
    
    def clear(self):
        self._change('clear')
    
    @trellis.compute
    def enqueue(self):
        return self.append
    
    @trellis.compute
    def dequeue(self):
        return self.popleft
        
    @trellis.compute
    def head(self):
        if self:
            return self[0]
    
    @trellis.compute
    def tail(self):
        if self:
            return self[-1]
        
    @trellis.modifier
    def extend(self, items):
        for item in items:
            self.append(item)
        
#############################################################################
#############################################################################
