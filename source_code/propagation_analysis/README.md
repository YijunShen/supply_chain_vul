## How to query propagation path:

#### 1. If the graph is not indexed (method nodes don't have inner_downstream attrbute):

(1) Run builder.py in package index_build.

(2) Change database url in line 6.

(3) If you want to focus on some specifical packages, and only get those packages' methods indexed, change get_pkg_list() in line 10 as you want.

####  2. If the graph is indexed, and fold tmp_data don't have file all_path.npy

 (1) Run AnalyseGraph.py in package propagation_analysis,  change database url in line 232, change the upstream package in line260, then we get a target_list.npy in tmp_data.

(2) Run path.py in package propagation_analysis, then we get a all_path.npy in tmp_data, and terminal will print the reachablility form upstream package to dowmstream package in method level.

#### 3. If fold tmp_data have file all_path.npy but don't have full_path.txt

(1) Run AnalysePath.py in package propagation_analysis

(2) If your all_path is more than one dependent package level, run AnalyseDemo.py in package propagation_analysis