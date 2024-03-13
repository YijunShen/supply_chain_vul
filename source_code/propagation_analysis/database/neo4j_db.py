from py2neo import Node, Relationship, Graph, NodeMatcher, RelationshipMatcher


# identity means a number arranged by neo4j automatic, id is set by developer according to realist.
class DataBase:

    # url where the neo4j database is running
    def __init__(self, url="http://211.71.15.39:10474"):
        self.graph = Graph(url, password="callgraph", name="callgraph")
        self.nodes = NodeMatcher(self.graph)
        self.relations = RelationshipMatcher(self.graph)

    def run(self, query):
        res = self.graph.run(query)
        return res

    # get neo4j identity(int) by package node id(string)
    def match_id_by_pkg(self, package_id):
        query = f"MATCH (n:Package) where n.id='{package_id}' RETURN n"
        res = self.run(query).data()
        return res.data()[0]['n'].identity

    # get identity list of all package node in call graph
    def get_all_pkg_identity(self):
        pkg_list = []
        query = f"MATCH (n:Package) RETURN id(n) as id"
        res = self.run(query).data()
        for pkg in res:
            pkg_list.append({
                'id': pkg['id'],
                'indexed': 0
            })
        return pkg_list

    # get node by neo4j identity
    def match_node_by_id(self, neo4j_id):
        query = f"MATCH (n) where id(n)={neo4j_id} RETURN n"
        res = self.run(query).data()[0]['n']
        return res

    # get all methods for single package, argument is package identity, return a list of method identity
    def match_methods_by_package(self, pkg_id):
        method_list = []
        query1 = f"MATCH p=(n:Package)-[r:HasClass]->(m) where id(n)={pkg_id} RETURN m"
        res1 = self.run(query1).data()
        for Class in res1:
            class_identity = Class['m'].identity
            query2 = f"MATCH p=(n:Class)-[r:HasMethod]->(m) where id(n)={class_identity} RETURN m"
            res2 = self.run(query2).data()
            for Method in res2:
                method_identity = Method['m'].identity
                method_list.append(method_identity)
        return method_list

    # get all out-call methods for a method, argument is method identity, return a list of method identity
    def match_out_call_by_method(self, node_id):
        method_list = []
        query = f"MATCH p=(n)-[r:MethodCall]->(m) where id(m)={node_id} and r.outCall=true RETURN n"
        res = self.run(query).data()
        for Method in res:
            method_identity = Method['n'].identity
            method_list.append(method_identity)
        return method_list

    # add index attribute to method node, argument is method identity and downstream method identity list
    def add_index_for_method(self, method_id, index_list):
        query = f"MATCH (n:Method) where id(n)={method_id} set n.inner_downstream={index_list}"
        self.graph.run(query)

    # get downstream method identity list of a method node, argument is method identity
    def get_index_for_method(self, method_id):
        query = f"MATCH (n:Method) where id(n)={method_id} RETURN n"
        method = self.run(query).data()[0]['n']
        return method['inner_downstream']

