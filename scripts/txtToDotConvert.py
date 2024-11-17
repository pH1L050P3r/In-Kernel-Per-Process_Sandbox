import os
from collections import namedtuple
from pprint import pprint


Edge = namedtuple("Edge", ["node", "edge"])

class Graph():
    def __init__(self, name) -> None:
        self._start = "-1"
        self._end = "-1"
        self._graph = dict()
        self._name = name
        self._nodes = set()

    def setStart(self, start):
        self._start = start

    def setEnd(self, end):
        self._end = end

    def getStart(self):
        return self._start

    def getEnd(self):
        return self._end
    
    def addEdge(self, src, dst, name):
        if src not in self._graph:
            self._graph[src] = set()
        if dst not in self._graph:
            self._graph[dst] = set()
        
        edge = Edge(dst, name)
        self._graph[src].add(Edge(dst, name))
        self._nodes.add(src)
        self._nodes.add(dst)
        return edge
    
    def removeNode(self, node):
        self._graph.remove(node)
    
    def removeEdge(self, src, edge):
        if edge in self._graph[src]:
            self._graph[src].remove(edge)
    
    def edges(self):
        for node, edges in self._graph.items():
            for edge in edges:
                yield node, edge.node, edge.edge

    def removeLoop(self):
        degree = {}
        for node in self._nodes:
            degree[node] = [set(), set()]
        
        # incomming = {(from, edge), ...} [0]
        # outgoing = {edge, ...}          [1]
        for node in self._nodes:
            for e in self._graph[node]:
                degree[node][1].add(e)
                degree[e.node][0].add((node, e))
        
        # loop till we have these kind of nodes (indegree == outDegree == 1) and any one edge(incomming and outgoing) is "e" 
        # 1) -e- N -e-
        # 2) -call- N -e-
        # 3) -e- N -call-
        isReduced = True
        while isReduced:
            isReduced = False
            node, inDeg, outDeg = None, None, None
            src, node, e1, e2 = None, None, None, None
            for _node, (_inDeg, _outDeg) in degree.items():
                if len(_inDeg) == len(_outDeg) == 1:
                    for (_src, _e1), _e2 in zip(_inDeg, _outDeg):
                        if _e1.edge == "e" or _e2.edge == "e":
                            src, node, e1, e2 = _src, _node, _e1, _e2
            
            if node is not None:
                isReduced = True
                self.removeEdge(src, e1)
                self.removeEdge(node, e2)
                edge = None
                if e1.edge == e2.edge == "e":
                    edge = self.addEdge(src, e2.node, "e")
                elif e1.edge == "e":
                    edge = self.addEdge(src, e2.node, e2.edge)
                elif e2.edge == "e":
                    edge = self.addEdge(src, e2.node, e1.edge)

                # merge  S -e- N -e- D => S -e- D
                # merge  S -f- N -e- D => S -f- D
                # merge  S -e- N -f- D => S -f- D
                degree.pop(node)
                degree[e2.node][0].remove((node, e2))
                degree[src][1].remove(e1)
                degree[src][1].add(edge)
                degree[e2.node][0].add((src, edge))                    

    def print(self):
        pprint(self._graph)

    def update(self, graph_list):
        func = []
        edges = []

        for node, edge in self._graph.items():
            for e in edge:
                if e[1] in graph_list and e[1] != self._name:
                    func.append(e[1])
                    edges.append((node, e))        

        for e in edges:
            self._graph.get(e[0]).remove(e[1])
            f = e[1][1]
            caller, calle, ret_from, ret_to = (
                e[0], 
                graph_list.get(f)._start, 
                graph_list.get(f)._end, 
                e[1][0]
            )
            # change code here if don't want label over call/return edge just replace it with epsillon
            self.addEdge(caller, calle, f"call_{f}")
            graph_list.get(f).addEdge(ret_from, ret_to, f"ret_{f}")
        return func
                

    def exportToDot(self, fp):
        for node, edges in self._graph.items():
            for e in edges:
                fp.write(f"""\t{node} -> {e.node}[label="{e.edge}"]\n""")

    @staticmethod
    def construct_from_dot(filepath):
        graph = Graph(name="restored_graph")
        with open(filepath, 'r') as file:
            for line in file:
                line = line.strip()
                if '->' not in line or '[label="' not in line:
                    continue
                parts = line.split("->")
                src = parts[0].strip()
                dst_label = parts[1].strip()
                dst_part, label_part = dst_label.split("[label=")
                dst = dst_part.strip()
                label = label_part.replace('"]', '').strip('"')
                graph.addEdge(src, dst, name=label)
        return graph


def exportDOTFormat(graphList, lis,file_name):
    with open(file_name, "w") as fp:
        fp.write("digraph main {\n")
        lis.remove("main")
        graphList.get("main").exportToDot(fp)
        for name in lis:
            graphList.get(name).exportToDot(fp)
        fp.write("}")


if __name__ == "__main__" :
    import glob

    # Use glob to find all files starting with "ENAF_" and ending with ".txt"
    file_pattern = "ENFA_*.txt"
    files = glob.glob(file_pattern)
    graph_list = dict()
    for file_name in files:
        base_name = os.path.basename(file_name)  # Get the file name without the path
        extracted_part = base_name[len("ENAF_"):-len(".txt")]
        graph = Graph(extracted_part)
        with open(file_name, 'r') as fp:
            # building graph for each ENFA file
            lines = fp.readlines()
            start_state = extracted_part + "_" + lines[0].split("\n")[0].strip()
            final_states = extracted_part + "_" + lines[1].split("\n")[0].strip()
            graph.setStart(start_state)
            graph.setEnd(final_states)
            for line in lines[2:]:
                fname, src, dst, ename = line.split('\n')[0].split(',')
                graph.addEdge(extracted_part + "_" + src, extracted_part + "_" + dst, ename)
        graph_list[extracted_part] = graph
        graph.removeLoop()
    
    visited = set()
    queue = []
    queue.append("main")
    while len(queue)> 0:
        item = queue.pop()
        if item in visited: continue
        visited.add(item)
        graph = graph_list.get(item)
        next_update = graph.update(graph_list)
        for item in next_update:
            queue.append(item)
    file_path = "./graph.dot"
    exportDOTFormat(graph_list, visited, file_path)
    # graph = Graph.construct_from_dot(file_path)
    # for u, v, e in graph.edges():
    #     print(f"{u} -> {v} [label={e}]")
