# @copyright
# @license

from __future__ import absolute_import

import collections

from .. import trellis

#############################################################################
#############################################################################

class Set(trellis.Component, collections.MutableSet):

    changes = trellis.todo(list)
    to_change = changes.future
    
    def __init__(self, iterable=None):
        super(Set, self).__init__()
        if iterable:
            self.update(iterable)
    
    def __contains__(self, v):
        return self._data.__contains__(v)
    
    def __len__(self):
        return self._data.__len__()

    def __iter__(self):
        return self._data.__iter__()
    
    def __nonzero__(self):
        return len(self) > 0
    
    def __getstate__(self):
        return tuple(self._data)
    
    @trellis.modifier
    def __setstate__(self, state):
        self.clear()
        self.update(state)
    
    @trellis.compute
    def __repr__(self):
        text = '%s%s' % (self.__class__.__name__, str(self))
        return lambda: text
    
    @trellis.compute
    def __str__(self):
        text = repr(self.__getstate__())
        return lambda: text
    
    @trellis.maintain(make=set)
    def _data(self):
        data = self._data
        changes = self.changes
        if changes:
            for fn, v in changes:
                if fn == 'add':
                    if v not in data:
                        data.add(v)
                        trellis.on_undo(data.discard, v)
                elif fn == 'discard':
                    if v not in data:
                        raise ValueError(v)
                    data.discard(v)
                    trellis.on_undo(data.add, v)
                else:
                    raise RuntimeError(fn)
            trellis.mark_dirty()
        return data
    
    @trellis.modifier
    def add(self, item):
        self.to_change.append(('add', item))

    @trellis.modifier
    def discard(self, item):
        self.to_change.append(('discard', item))
        
    @trellis.modifier
    def update(self, items):
        for item in items:
            self.add(item)
        
#############################################################################
#############################################################################
