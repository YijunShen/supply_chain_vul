from database import neo4j_db
import numpy as np
import copy

db = neo4j_db.DataBase()
path = []
all_path = np.load("../tmp_data/all_path.npy").tolist()


# indexed path by dfs method
def dfs(node_id, target):
    index_method_list = db.get_index_for_method(node_id)
    target_method_list = db.match_methods_by_package(target)
    if index_method_list is None:
        return 0
    index_method_list.append(node_id)
    path.append(node_id)

    for index_method in index_method_list:
        path.append(index_method)
        out_call_method_list = db.match_out_call_by_method(index_method)
        for out_call_method in out_call_method_list:
            if out_call_method in target_method_list:
                path.append(out_call_method)
                print(path)
                tmp = copy.deepcopy(path)
                all_path.append(tmp)
                path.clear()
                return 1
            if dfs(out_call_method, target):
                return 1
        path.pop()
    path.pop()
    return 0


def query_indexed_path(upstream):

    target_list = np.load("../tmp_data/target_list.npy", allow_pickle=True).tolist()
    count = 0
    for node in target_list[1:]:
        target = node['id']
        if dfs(upstream, target):
            print("%s is reachable" % target)
            count += 1
        else:
            print("%s is unreachable" % target)
    np.save("../tmp_data/all_path.npy", all_path)
    print(count)

query_indexed_path(176)
