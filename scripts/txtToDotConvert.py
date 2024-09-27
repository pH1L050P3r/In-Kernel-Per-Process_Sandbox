import sys
import copy
import os
from collections import namedtuple
from pprint import pprint
from queue import Queue

Edge = namedtuple("Edge", ["node", "edge"])

class Graph():
    def __init__(self, name) -> None:
        self._start = "-1"
        self._end = "-1"
        self._graph = dict()
        self._name = name

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
            self._graph[src] = []
        if dst not in self._graph:
            self._graph[dst] = []
        
        self._graph[src].append(Edge(dst, name))

    def exportToDot(self, fp):
        for node, edges in self._graph.items():
            for e in edges:
                fp.write(f"""{node} -> {e.node}[label="{e.edge}"]\n""")

    def print(self):
        print(self._name)
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
            self.addEdge(caller, calle, f"call_{f}")
            self.addEdge(ret_from, ret_to, f"ret_{f}")
        return func
                

    def exportToDot(self, fp):
        for node, edges in self._graph.items():
            for e in edges:
                fp.write(f"""\t{node} -> {e.node}[label="{e.edge}"]\n""")


def exportDOTFormat(graphList, lis):
    with open("./graph.dot", "w") as fp:
        fp.write("digraph main {\n")
        for name in lis:
            graph_list.get(name).exportToDot(fp)
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
            lines = fp.readlines()
            # lines = input_data.splitlines()
            start_state = extracted_part + "_" + lines[0].split("\n")[0].strip()
            final_states = extracted_part + "_" + lines[1].split("\n")[0].strip()
            graph.setStart(start_state)
            graph.setEnd(final_states)
            for line in lines[2:]:
                fname, src, dst, ename = line.split('\n')[0].split(',')
                graph.addEdge(extracted_part + "_" + src, extracted_part + "_" + dst, ename)
        graph_list[extracted_part] = graph
    
    visited = set()
    queue = []
    queue.append("main")

    while len(queue)> 0:
        item = queue.pop()
        print(queue)
        if item in visited: continue
        visited.add(item)
        graph = graph_list.get(item)
        next_update = graph.update(graph_list)
        for item in next_update:
            queue.append(item)
        print(next_update)

    graph_list.get("main").print()
    exportDOTFormat(graph_list, visited)
    