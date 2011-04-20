# @copyright
# @license

import collections

import networkx as nx

import pypetri.trellis as trellis

#############################################################################
#############################################################################

class Graph(collections.Mapping, trellis.Component):

    CHANGE_ACTIONS = range(3)
    ADD_ACTION, REMOVE_ACTION, CLEAR_ACTION = CHANGE_ACTIONS
    CHANGE_TYPES = range(2)
    NODE_TYPE, EDGE_TYPE = CHANGE_TYPES
    
    Graph = nx.Graph
    
    graph = trellis.attr(None)
    changes = trellis.todo(list)
    to_change = changes.future

    def __init__(self, graph=None, *args, **kwargs):
        if graph is None:
            graph = self.Graph(*args, **kwargs)
        super(Graph, self).__init__(graph=graph)
        for k in dir(graph):
            if not hasattr(self, k):
                setattr(self, k, getattr(graph, k))

    def __getitem__(self, key):
        return self.graph[key]
    
    def __iter__(self):
        return iter(self.graph)
    
    def __len__(self):
        return len(self.graph)
    
    @trellis.modifier
    def add_node(self, *args, **kwargs):
        change = (self.ADD_ACTION, self.NODE_TYPE, args, kwargs,)
        self.to_change.append(change)
        
    @trellis.modifier
    def add_nodes_from(self, nbunch):
        for n in nbunch:
            self.add_node(n)
        
    @trellis.modifier
    def remove_node(self, *args, **kwargs):
        change = (self.REMOVE_ACTION, self.NODE_TYPE, args, kwargs,)
        self.to_change.append(change)
        
    @trellis.modifier
    def remove_nodes_from(self, nbunch):
        for n in nbunch:
            self.remove_node(n)
            
    @trellis.modifier
    def add_edge(self, *args, **kwargs):
        change = (self.ADD_ACTION, self.EDGE_TYPE, args, kwargs,)
        self.to_change.append(change)
        
    @trellis.modifier
    def add_edges_from(self, ebunch):
        for e in ebunch:
            self.add_edge(*e)
            
    @trellis.modifier
    def remove_edge(self, *args, **kwargs):
        change = (self.REMOVE_ACTION, self.EDGE_TYPE, args, kwargs,)
        self.to_change.append(change)
        
    @trellis.modifier
    def remove_edges_from(self, ebunch):
        for e in ebunch:
            self.remove_edge(*e)
            
    @trellis.modifier
    def add_star(self, nbunch):
        self.add_nodes_from(nbunch)
        hub = nbunch[0]
        for i in xrange(1, len(nbunch)):
            self.add_edge(hub, nbunch[i])
        
    @trellis.modifier
    def add_path(self, nbunch):
        self.add_nodes_from(nbunch)
        for i in xrange(len(nbunch)-1):
            self.add_edge(nbunch[i],nbunch[i+1])
        
    @trellis.modifier
    def add_cycle(self, nbunch):
        self.add_path(nbunch)
        self.add_edge(nbunch[-1], nbunch[0])
        
    @trellis.modifier
    def clear(self):
        change = (self.CLEAR_ACTION,)
        self.to_change.append(change)

    @trellis.maintain
    def regraph(self):
        graph = self.graph
        for change in self.changes:
            self.apply(graph, change)
        if self.changes:
            trellis.mark_dirty()

    def apply(self, graph, change, log=True):
        undos = []
        action = change[0]
        if action == self.ADD_ACTION:
            type, args, kwargs = change[1:]
            if type == self.NODE_TYPE:
                if not graph.has_node(args[0]):
                    undo = (self.REMOVE_ACTION, type, args,)
                    undos.append(undo)
                    graph.add_node(*args, **kwargs)
            elif type == self.EDGE_TYPE:
                if not graph.has_edge(*args[0:2]):
                    undo = (self.REMOVE_ACTION, type, args,)
                    undos.append(undo)
                    graph.add_edge(*args, **kwargs)
        elif action == self.REMOVE_ACTION:
            type, args, kwargs = change[1:]
            if type == self.NODE_TYPE:
                u = args[0]
                if graph.has_node(u):
                    edges = graph.edges(u, data=True)
                    for edge in edges:
                        undo = (self.ADD_ACTION, self.EDGE_TYPE, edge[:2], edge[2],)
                        undos.append(undo)
                    undo = (self.ADD_ACTION, type, (u,), dict(graph.node[u]),)
                    undos.append(undo)
                    graph.remove_node(*args, **kwargs)
            elif type == self.EDGE_TYPE:
                u,v = args[0:2]
                if graph.has_edge(u,v):
                    undo = (self.ADD_ACTION, type, args, dict(graph.edge[u][v]),)
                    undos.append(undo)
                    graph.remove_edge(*args, **kwargs)
        elif action == self.CLEAR_ACTION:
            for n in graph.nodes_iter(data=True):
                undo = (self.ADD_ACTION, self.NODE_TYPE, n[:1], n[-1],)
                undos.append(undo)
            for e in graph.edges_iter(data=True):
                undo = (self.ADD_ACTION, self.EDGE_TYPE, e[:2], e[-1],)
                undos.append(undo)
            graph.clear()
        else:
            assert False
        if log:
            trellis.on_undo(self.undo, graph, undos)

    def undo(self, graph, changes):
        for change in changes:
            self.apply(graph, change, False)
    
    def snapshot(self):
        return self.graph.copy()
            
#############################################################################
#############################################################################
