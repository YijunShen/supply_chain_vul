import numpy as np
from database.neo4j_db import DataBase
from index_builder.builder import build_inner_call_graph
from copy import deepcopy

db = DataBase()
inner_path = []
inner_path_list = []


def get_inner_node_pair(file_name="../tmp_data/all_path.npy"):
    all_path = np.load(file_name).tolist()
    print(len(all_path))
    node_pairs = []
    for path in all_path:
        pair = [path[0], path[1]]
        if pair not in node_pairs:
            node_pairs.append(pair)
    np.save("../tmp_data/node_pairs.npy", node_pairs)
    print(len(node_pairs))


def dfs(graph, start, end, depth):
    # avoid loop path
    if start not in inner_path:
        inner_path.append(start)
    else:
        return
    if start == end:
        tmp = deepcopy(inner_path)
        inner_path_list.append(tmp)
        inner_path.pop()
        return
    for nxt in graph[start]:
        dfs(graph, nxt, end, depth)
    inner_path.pop()


def inner_path_analyse():
    node_pairs = np.load("../tmp_data/node_pairs.npy").tolist()
    print(len(node_pairs))
    node_pair_path_dict = {}
    count = 1
    for pair in node_pairs:
        print(count)
        upstream_node = pair[0]
        downstream_node = pair[1]
        pkg_id = db.get_package_by_method_id(upstream_node)
        if pkg_id != db.get_package_by_method_id(downstream_node):
            print(pair)
            continue
        call_graph = build_inner_call_graph(pkg_id)
        dfs(call_graph, upstream_node, downstream_node, 0)
        print(inner_path_list)
        node_pair_path_dict[(upstream_node, downstream_node)] = deepcopy(inner_path_list)
        inner_path.clear()
        inner_path_list.clear()
        np.save("../tmp_data/node_pair_path_dict.npy", node_pair_path_dict)
        count += 1


def inner_node_analyse():
    node_pair_path_dict = np.load("../tmp_data/node_pair_path_dict.npy", allow_pickle=True).item()
    node_pair_node_dict = {}
    count = 1
    for pair in node_pair_path_dict:
        print(count)
        node_list = []
        path_list = node_pair_path_dict[pair]
        for path in path_list:
            for node in path:
                if node not in node_list:
                    node_list.append(node)
        node_pair_node_dict[pair] = {"node_list": deepcopy(node_list), "node_count": len(node_list), "out_call_count": 0}
        print(len(node_list))
        np.save("../tmp_data/node_pair_node_dict.npy", node_pair_node_dict)
        count += 1


def all_node_analyse():
    all_path = np.load("../tmp_data/all_path.npy").tolist()
    print(len(all_path))
    node_pair_node_dict = np.load("../tmp_data/node_pair_node_dict.npy", allow_pickle=True).item()
    for path in all_path:
        node_pair = (path[0], path[1])
        node_pair_node_dict[node_pair]['out_call_count'] += 1
    for key in node_pair_node_dict:
        print(node_pair_node_dict[key]['out_call_count'])
    np.save("../tmp_data/node_pair_node_dict.npy", node_pair_node_dict)


def calculate_node_count():
    count = 0
    node_pair_node_dict = np.load("../tmp_data/node_pair_node_dict.npy", allow_pickle=True).item()
    for key in node_pair_node_dict:
        count += node_pair_node_dict[key]['node_count']
        count += node_pair_node_dict[key]['out_call_count']
    print("total node count: %s" % count)


def calculate_edge_count():
    all_path = np.load("../tmp_data/all_path.npy").tolist()
    start_node_list = []
    count = 0
    for path in all_path:
        if path[0] not in start_node_list:
            start_node_list.append(path[0])
    print("total inner call pkg count: %s" % (37 - len(start_node_list)))
    for node in start_node_list:
        index_list = db.get_index_for_method(node)
        count += len(index_list)
    count += len(all_path)
    print("total edge count: %s" % count)


def generate_full_paths():
    all_path = np.load("../tmp_data/all_path.npy").tolist()
    node_pair_path_dict = np.load("../tmp_data/node_pair_path_dict.npy", allow_pickle=True).item()
    node_pair_node_dict = np.load("../tmp_data/node_pair_node_dict.npy", allow_pickle=True).item()
    pkg_dict = {}
    pkg_list = []
    for key in node_pair_node_dict:
        pkg_list.extend(node_pair_node_dict[key]['node_list'])
    pkg_list = list(set(pkg_list))
    for pkg_id in pkg_list:
        pkg_dict[pkg_id] = db.match_node_by_id(pkg_id)['id']
    count = 0
    for full_path in all_path:
        pair = (full_path[0], full_path[1])
        path_list = node_pair_path_dict[pair]
        for path in path_list:
            p = ""
            for node in path:
                p += pkg_dict[node] + " -> "
            # 加上终点
            p += db.match_node_by_id(full_path[2])['id'] + "\n"
            with open("../tmp_data/full_path.txt", 'a') as f:
                f.write(p)
            count += 1
    print("total path count: %s" % count)
    print("generate full paths done!")


get_inner_node_pair()
inner_path_analyse()
inner_node_analyse()
all_node_analyse()
calculate_node_count()
calculate_edge_count()
generate_full_paths()
