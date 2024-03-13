import argparse
import os
import csv
import inspect
import numpy as np

from neo4j import GraphDatabase

global Package
global Depends
global Id
global res_dict


def direct_dependencies(tx, file_path):
    global Package
    global Depends
    global Id
    attr = inspect.currentframe().f_code.co_name
    query = (
        f'MATCH (p:{Package}) '
        f'RETURN p.{Id} AS packageId, SIZE((p)-[:{Depends}]->()) AS directDependencies '
        f'ORDER BY directDependencies DESC'
    )
    results = tx.run(query).values('packageId', 'directDependencies')
    save(file_path + attr + '.csv', results, attr)
    print(f'finish analyse {attr}')


def total_dependencies(tx, file_path):  #
    global Package
    global Depends
    global Id
    attr = inspect.currentframe().f_code.co_name
    query = (
        f'MATCH (p:{Package}) '
        f'CALL apoc.path.subgraphNodes(p, {{relationshipFilter:"{Depends}>", labelFilter:"{Package}", maxLevel:10}}) YIELD node '
        f'WITH p, COUNT(DISTINCT node)-1 AS totalDeps '
        f'RETURN p.{Id} AS packageId, totalDeps '
        f'ORDER BY totalDeps DESC'
    )
    results = tx.run(query).values('packageId', 'totalDeps')
    save(file_path + attr + '.csv', results, attr)
    print(f'finish analyse {attr}')


def depend_layer(tx, file_path):
    global Package
    global Depends
    global Id
    attr = inspect.currentframe().f_code.co_name
    query = (
        f'MATCH (p:{Package}) '
        f'CALL apoc.path.expandConfig(p, {{relationshipFilter:"{Depends}>", labelFilter:"{Package}", uniqueness:"NODE_GLOBAL"}}) YIELD path '
        f'WITH p, MAX(length(path)-1) AS maxDepth '
        f'RETURN p.{Id} AS packageId, maxDepth '
        f'ORDER BY maxDepth DESC'
    )
    results = tx.run(query).values('packageId', 'maxDepth')
    save(file_path + attr + '.csv', results, attr)
    print(f'finish analyse {attr}')


def direct_dependents(tx, file_path):
    global Package
    global Depends
    global Id
    attr = inspect.currentframe().f_code.co_name
    query = (
        f'MATCH (p:{Package}) '
        f'CALL apoc.path.subgraphNodes(p, {{relationshipFilter:"{Depends}<", maxLevel:1}}) YIELD node '
        f'WITH p, COUNT(DISTINCT node)-1 AS numDependsOn '
        f'ORDER BY numDependsOn DESC '
        f'RETURN p.{Id} AS packageId, numDependsOn'
    )
    results = tx.run(query).values('packageId', 'numDependsOn')
    save(file_path + attr + '.csv', results, attr)
    print(f'finish analyse {attr}')


def total_dependents(tx, file_path):
    global Package
    global Depends
    global Id
    attr = inspect.currentframe().f_code.co_name
    query = (
        f'MATCH (p:{Package}) '
        f'CALL apoc.path.subgraphNodes(p, {{relationshipFilter:"{Depends}<", maxLevel:10}}) YIELD node '
        f'WITH p, COUNT(DISTINCT node)-1 AS numDependsOn '
        f'ORDER BY numDependsOn DESC '
        f'RETURN p.{Id} AS packageId, numDependsOn'
    )
    results = tx.run(query).values('packageId', 'numDependsOn')
    save(file_path + attr + '.csv', results, attr)
    print(f'finish analyse {attr}')


def save(filename, res, attr):
    with open(filename, 'w', encoding='utf8', newline='')as fp:
        csv_writer = csv.writer(fp)
        csv_writer.writerow(['PackageId', attr])
        csv_writer.writerows(res)


def one_direct_dependencies(tx, pkg_id):
    global Package
    global Depends
    global Id
    global res_dict
    query = (
        f'MATCH (p:{Package}) where p.{Id}="{pkg_id}" '
        f'RETURN p.{Id} AS packageId, SIZE((p)-[:{Depends}]->()) AS directDependencies '
        f'ORDER BY directDependencies DESC'
    )
    result = tx.run(query).values('packageId', 'directDependencies')[0]
    print(result)
    ver_detail = res_dict[result[0].split('@')[0]]['versions'][result[0].split('@')[1]]
    ver_detail['directDependencyCnt'] = result[1]


def one_total_dependencies(tx, pkg_id):
    global Package
    global Depends
    global Id
    global res_dict
    query = (
        f'MATCH (p:{Package}) where p.{Id}="{pkg_id}" '
        f'CALL apoc.path.subgraphNodes(p, {{relationshipFilter:"{Depends}>", labelFilter:"{Package}", maxLevel:10}}) YIELD node '
        f'WITH p, COUNT(DISTINCT node)-1 AS totalDeps '
        f'RETURN p.{Id} AS packageId, totalDeps '
    )
    result = tx.run(query).values('packageId', 'totalDeps')[0]
    print(result)


def one_dependency_layer(tx, pkg_id):
    global Package
    global Depends
    global Id
    global res_dict
    query = (
        f'MATCH (p:{Package}) where p.{Id}="{pkg_id}" '
        f'CALL apoc.path.expandConfig(p, {{relationshipFilter:"{Depends}>", labelFilter:"{Package}", uniqueness:"NODE_GLOBAL"}}) YIELD path '
        f'WITH p, MAX(length(path)) AS maxDepth '
        f'RETURN p.{Id} AS packageId, maxDepth '
    )
    result = tx.run(query).values('packageId', 'maxDepth')[0]
    print(result)
    ver_detail = res_dict[result[0].split('@')[0]]['versions'][result[0].split('@')[1]]
    ver_detail['dependencyHeight'] = result[1]


def one_direct_dependents(tx, pkg_id):
    global Package
    global Depends
    global Id
    global res_dict
    query = (
        f'MATCH (p:{Package}) where p.{Id}="{pkg_id}" '
        f'CALL apoc.path.subgraphNodes(p, {{relationshipFilter:"{Depends}<", maxLevel:1}}) YIELD node '
        # f'WITH p, COUNT(DISTINCT node)-1 AS numDirectDependsOn ' 
        f'RETURN DISTINCT node'
    )
    result = tx.run(query).values()
    print(len(result)-1)
    target = []
    for node in result:
        print(node[0]['id'])
        target.append({
            'id': node[0].element_id,
            'indexed': 0
        })
    return target


def one_dependents_by_level(tx, pkg_id, maxlevel):
    global Package
    global Depends
    global Id
    global res_dict
    query = (
        f'MATCH (p:{Package}) where p.{Id}="{pkg_id}" '
        f'CALL apoc.path.subgraphNodes(p, {{relationshipFilter:"{Depends}<", maxLevel:{maxlevel}}}) YIELD node '
        f'WITH p, COUNT(DISTINCT node)-1 AS numDependsOn '
        f'RETURN p.{Id} AS packageId, numDependsOn '
    )
    result = tx.run(query).values('packageId', 'numDirectDependsOn')[0]
    print(result)


def one_total_dependents(tx, pkg_id):
    global Package
    global Depends
    global Id
    global res_dict
    query = (
        f'MATCH (p:{Package}) where p.{Id}="{pkg_id}" '
        f'CALL apoc.path.subgraphNodes(p, {{relationshipFilter:"{Depends}<", maxLevel:10}}) YIELD node '
        # f'WITH p, DISTINCT node AS nodes '
        f'RETURN DISTINCT node'
    )
    result = tx.run(query).values()
    print(len(result) - 1)
    target = []
    for node in result:
        target.append({
            'id': node[0].element_id,
            'indexed': 0
        })
    # print(len(target))
    np.save("../tmp_data/target_list.npy", target)


# 统计每个节点的依赖层数
def one_dependent_layer(tx, pkg_id):
    global Package
    global Depends
    global Id
    global res_dict
    query = (
        f'MATCH (p:{Package}) where p.{Id}="{pkg_id}" '
        f'CALL apoc.path.expandConfig(p, {{relationshipFilter:"{Depends}<", labelFilter:"{Package}", uniqueness:"NODE_GLOBAL"}}) YIELD path '
        f'WITH p, MAX(length(path)) AS maxDepth '
        f'RETURN p.{Id} AS packageId, maxDepth '
    )
    result = tx.run(query).values('packageId', 'maxDepth')[0]
    print(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-uri', default='neo4j://211.71.15.39:7687')
    parser.add_argument('--username', default='neo4j')
    parser.add_argument('--password', default='callgraph')
    parser.add_argument('--pkg_name', default='Package')
    parser.add_argument('--id_name', default='id')
    parser.add_argument('--depend_name', default='DependOn')
    # parser.add_argument('--output_dir', default='./analyse_python/', help='result file path')

    args = parser.parse_args()

    uri = args.uri
    username = args.username
    password = args.password
    filepath = args.output_dir
    pkg_name = args.pkg_name
    depend_name = args.depend_name
    Package = args.pkg_name
    Depends = args.depend_name
    Id = args.id_name

    # if not os.path.exists(args.output_dir):
    #     os.mkdir(args.output_dir)

    driver = GraphDatabase.driver(uri, auth=(username, password),
                                  max_connection_lifetime=3600 * 24 * 30, keep_alive=True)

    with driver.session() as session:

        session.execute_read(one_total_dependents, "org.codehaus.plexus:plexus-archiver:3.5")






