
import networkx as nx

import pypetri.trellis as trellis

#############################################################################
#############################################################################

class Graph(trellis.Component):

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

    # proxy
    def __getattr__(self, attr):
        if hasattr(self, 'graph') \
            and self.graph is not None \
            and not attr.startswith('_'):
            return getattr(self.graph, attr)
        else:
            raise AttributeError(self, attr)
    
    @trellis.modifier
    def add_node(self, n):
        change = (self.ADD_ACTION, self.NODE_TYPE, [n])
        self.to_change.append(change)
        
    @trellis.modifier
    def add_nodes_from(self, nbunch):
        for n in nbunch:
            self.add_node(n)
        
    @trellis.modifier
    def remove_node(self, n):
        change = (self.REMOVE_ACTION, self.NODE_TYPE, [n])
        self.to_change.append(change)
        
    @trellis.modifier
    def remove_nodes_from(self, nbunch):
        for n in nbunch:
            self.remove_node(n)
            
    @trellis.modifier
    def add_edge(self, u, v):
        change = (self.ADD_ACTION, self.EDGE_TYPE, [u, v])
        self.to_change.append(change)
        
    @trellis.modifier
    def add_edges_from(self, ebunch):
        for e in ebunch:
            self.add_edge(*e)
            
    @trellis.modifier
    def remove_edge(self, u, v):
        change = (self.REMOVE_ACTION, self.EDGE_TYPE, [u, v])
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
        change = tuple([self.CLEAR_ACTION])
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
            type = change[1]
            args = change[2]
            if type == self.NODE_TYPE:
                if not graph.has_node(args[0]):
                    undo = tuple([self.REMOVE_ACTION] + list(change[1:]))
                    undos.append(undo)
                    graph.add_node(*args)
            if type == self.EDGE_TYPE:
                if not graph.has_edge(*args[0:2]):
                    undo = tuple([self.REMOVE_ACTION] + list(change[1:]))
                    undos.append(undo)
                    graph.add_edge(*args)
        elif action == self.REMOVE_ACTION:
            type = change[1]
            args = change[2]
            if type == self.NODE_TYPE:
                u = args[0]
                if graph.has_node(u):
                    for v in graph[u]:
                        undo = tuple([self.ADD_ACTION, self.EDGE_TYPE, [u,v]])
                        undos.append(undo)
                    undo = tuple([self.ADD_ACTION] + list(change[1:]))
                    undos.append(undo)
                    graph.remove_node(*args)
            if type == self.EDGE_TYPE:
                if graph.has_edge(*args[0:2]):
                    undo = tuple([self.ADD_ACTION] + list(change[1:]))
                    undos.append(undo)
                    graph.remove_edge(*args)
        elif action == self.CLEAR_ACTION:
            for n in graph.node_iter:
                undo = tuple([self.ADD_ACTION, self.NODE_TYPE, [n]])
                undos.append(undo)
            for e in graph.edge_iter:
                undo = tuple([self.ADD_ACTION, self.EDGE_TYPE, e])
                undos.append(undo)
            graph.clear()
        else:
            assert False
        trellis.on_undo(self.undo, graph, undos)
    
    def undo(self, graph, changes):
        for change in changes:
            self.apply(graph, change, False)
    
    def snapshot(self):
        return self.graph.copy()
            
#############################################################################
#############################################################################
