import numpy as np
from database.neo4j_db import DataBase
from index_builder.builder import build_inner_call_graph
from copy import deepcopy

db = DataBase()
inner_path = []
inner_path_list = []


def dfs(graph, start, end, depth):
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


def preprocess():
    all_path = np.load("../tmp_data/demo_all_path.npy", allow_pickle=True).item()['all_path']
    call_graph_set = {}
    print(len(all_path))
    node_pairs = []
    for path in all_path:
        for i in range(int(len(path)/2)):
            pair = [path[0+2*i], path[1+2*i]]
            if pair not in node_pairs:
                node_pairs.append(pair)
    print(len(node_pairs))

    node_pair_path_dict = {}
    count = 1
    for pair in node_pairs:
        print(count)
        upstream_node = pair[0]
        downstream_node = pair[1]
        pkg_id = db.get_package_by_method_id(upstream_node)
        if pkg_id != db.get_package_by_method_id(downstream_node):
            continue
        if call_graph_set.get(pkg_id) is None:
            call_graph_set[pkg_id] = build_inner_call_graph(pkg_id)
        dfs(call_graph_set[pkg_id], upstream_node, downstream_node, 0)
        print(inner_path_list)
        node_pair_path_dict[(upstream_node, downstream_node)] = deepcopy(inner_path_list)
        inner_path.clear()
        inner_path_list.clear()
        count += 1
        np.save("../tmp_data/demo_node_pair_path_dict.npy", node_pair_path_dict)

    node_pair_node_dict = {}
    for pair in node_pair_path_dict:
        node_list = []
        path_list = node_pair_path_dict[pair]
        for path in path_list:
            for node in path:
                if node not in node_list:
                    node_list.append(node)
        node_pair_node_dict[pair] = {"node_list": deepcopy(node_list), "node_count": len(node_list), "out_call_count": 0}
        print(len(node_list))
        np.save("../tmp_data/demo_node_pair_node_dict.npy", node_pair_node_dict)
        count += 1

    for path in all_path:
        for i in range(int(len(path) / 2)):
            node_pair = (path[0 + 2 * i], path[1 + 2 * i])
            node_pair_node_dict[node_pair]['out_call_count'] += 1
    np.save("../tmp_data/demo_node_pair_node_dict.npy", node_pair_node_dict)
    # print(node_pair_path_dict)
    # print(node_pair_node_dict)


def calculate_node_count():
    count = 0
    node_pair_node_dict = np.load("../tmp_data/demo_node_pair_node_dict.npy", allow_pickle=True).item()
    for key in node_pair_node_dict:
        count += node_pair_node_dict[key]['node_count']
        count += node_pair_node_dict[key]['out_call_count']
    print("total node count: %s" % count)


def calculate_edge_count():
    all_path = np.load("../tmp_data/demo_all_path.npy", allow_pickle=True).item()['all_path']
    start_node_list = []
    count = 0
    for path in all_path:
        for i in range(int(len(path) / 2)):
            if path[0+2*i] not in start_node_list:
                start_node_list.append(path[0+2*i])
    for node in start_node_list:
        index_list = db.get_index_for_method(node)
        count += len(index_list)
    for path in all_path:
        for i in range(int(len(path) / 2)):
            count += 1
    print("total edge count: %s" % count)


def dfs_print(full_path, node_pair_path_dict, pkg_dict, i, p):
    if 0+2*i == len(full_path)-1:
        p += db.match_node_by_id(full_path[-1])['id'] + "\n"
        with open("../tmp_data/demo_full_path.txt", 'a') as f:
            f.write(p)
        return
    pair = (full_path[0+2*i], full_path[1+2*i])
    path_list = node_pair_path_dict[pair]
    for path in path_list:
        for node in path:
            p += pkg_dict[node] + " -> "
        dfs_print(full_path, node_pair_path_dict, pkg_dict, i+1, p)


def generate_full_paths():
    all_path = np.load("../tmp_data/demo_all_path.npy", allow_pickle=True).item()['all_path']
    node_pair_path_dict = np.load("../tmp_data/demo_node_pair_path_dict.npy", allow_pickle=True).item()
    node_pair_node_dict = np.load("../tmp_data/demo_node_pair_node_dict.npy", allow_pickle=True).item()
    pkg_dict = {}
    pkg_list = []
    for key in node_pair_node_dict:
        pkg_list.extend(node_pair_node_dict[key]['node_list'])
    pkg_list = list(set(pkg_list))
    for pkg_id in pkg_list:
        pkg_dict[pkg_id] = db.match_node_by_id(pkg_id)['id']
    for full_path in all_path:
        dfs_print(full_path, node_pair_path_dict, pkg_dict, 0, "")
    print("generate full paths done!")


preprocess()
calculate_node_count()
calculate_edge_count()
generate_full_paths()
