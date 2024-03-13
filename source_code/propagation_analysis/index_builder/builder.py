from database import neo4j_db
import numpy as np
from queue import Queue
import os

db = neo4j_db.DataBase("http://211.71.15.39:7474")


# get all package nodes' identity, save as npy file
def get_pkg_list():
    pkg_list = db.get_all_pkg_identity()
    np.save("../tmp_data/pkg_list.npy", pkg_list)
    print("get pkg list succeed!")


# build subgraph which only contains inner-call relation and corresponding nodes by package identity
def build_inner_call_graph(pkg_id):
    methods = db.match_methods_by_package(pkg_id)
    # print("%s has %s methods" % (pkg_id, len(methods)))
    call_dict = {}
    count = 1
    for m in methods:
        query = f"MATCH (a)-[r:MethodCall|MethodExtend]->(b) where id(b) = {m} RETURN a"
        downstream = db.run(query).data()
        call_dict[m] = []
        for n in downstream:
            n_identity = n['a'].identity
            # subgraph only needs methods in this package
            if n_identity not in methods:
                continue
            call_dict[m].append(n_identity)
        print("\r build process:%s:%s" % (len(methods), count), end="")
        count += 1
    # print("\ndone!")
    return call_dict


# bfs inner-call subgraph to build index for all methods in this package
def build_index_for_method(call_dict):
    count = 1
    for key in call_dict:
        index_list = []
        visited = set()
        visited.add(key)
        method_queue = Queue()
        method_queue.put(key)
        while not method_queue.empty():
            method = method_queue.get()
            call_list = call_dict[method]
            for downstream_method in call_list:
                if downstream_method in visited:
                    continue
                method_queue.put(downstream_method)
                index_list.append(downstream_method)
                visited.add(downstream_method)
        # add result to database
        db.add_index_for_method(key, index_list)
        print("\r bfs process:%s:%s" % (len(call_dict), count), end="")
        count += 1
    print()


def start_build():
    if not os.path.exists("../tmp_data/pkg_list.npy"):
        get_pkg_list()
    pkg_list = np.load("../tmp_data/pkg_list.npy", allow_pickle=True).tolist()
    for i in range(len(pkg_list)):
        pkg_id = int(pkg_list[i]['id'])
        print("processing : %s:%s  " % (len(pkg_list), i+1))
        if pkg_list[i]['indexed']:
            continue
        call_dict = build_inner_call_graph(pkg_id)
        build_index_for_method(call_dict)
        pkg_list[i]['indexed'] = 1
        np.save("../tmp_data/pkg_list.npy", pkg_list)
    print("build all index done!")


start_build()
