## "Understanding Vulnerabilities in Software Supply Chains":

#### 1. The source_code consists of two part: the construction of fine-grained supply chain & the propagation analysis of the vulnerability:

#### 2. The study datasets include the processed vulnerability dataset, the client list depending on these vulnerable libraries, the fine-grained vulnerability propagation analysis result, and the whole propagation path of the vulnerable package plexus-archiver.

#### Instructions of these data are also presented in README files in the folder separately.


## Instruction of the source code:

#### 1. Use any package-level supply chain construction tool(e.g. Google open source insights) to construct the package-level supply chain first. This step helps obtain the dependents of the target packages.

#### 2. Use the code in 'fine-grained_supply_chain_analysis' to obtaining source code of projects and construct the method-level supply chain.

#### 3. Use the code in 'propagation_analysis' to conduct the method-level vulnerability propagation analysis.


## How to construct a method-level supply chain:

#### 1. Java environment, Python environment(3.8.8), and neo4j database(4.3.3) is needed 

#### 2. Change the neo4j address in the resolve.py under 'source_code/fine-grained_supply_chain_analysis/CallGraph/src/main'

#### 3. Change the input group, artifact, version in the main.py under 'source_code/fine-grained_supply_chain_analysis/CallGraph/src/main'

#### 5. Run main.py. Then the method-level supply chain will be constructed as follw: obtaining source jar file from the Maven Central website; analyzing the call-graph of the project; storing the result to target neo4j database

#### P.S. The java-call-graph tool is modified from the gr.gousiosg.javacg:0.1-SNAPSHOT. It has been complied and used as 'java_cg.jar'. The source code are disclosed under the folder ‘source_code_of_jave-call-graph_tool’


## How to query propagation path:

#### 1. If the graph is not indexed (method nodes don't have inner_downstream attrbute):

(1) Run builder.py in package index_build.

(2) Change database url in line 6.

(3) If you want to focus on some specifical packages, and only get those packages' methods indexed, change get_pkg_list() in line 10 as you want.

####  2. If the graph is indexed, and fold tmp_data don't have file all_path.npy

 (1) Run AnalyseGraph.py in package propagation_analysis,  change database url in line 232, change the upstream package in line260, then we get a target_list.npy in tmp_data.

(2) Run path.py in package propagation_analysis, then we get a all_path.npy in tmp_data, and terminal will print the reachablility form upstream package to dowmstream package in method level.


## Instruction of the study_data:

#### 1. Dataset
The Maven dataset and the vulnerability dataset are listed in "0_Maven_dataset.xlsx" and "1_vulnerability_dataset.xlsx".

#### 2. Vulnerability Source Study
The study data about the vulnerability source, which is categoried as "from self" and "from dependency", is listed in "0_Maven_dataset.xlsx" from column D to column G

#### 3. Vulnerability Propagation Study
(1) the direct dependents(clients) depending on these vulnerable libraries is liset in the file 'clients_list.json';
(2) the fine-grained vulnerability propagation analysis result is store as a txt file, whose download link is available in the file 'full_propgation_path_download.txt';
(3) the whole propagation path of the vulnerable package plexus-archiver is liset in the file 'plexus_propagation_path.txt'.

#### 4. Vulnerability Localization Study
The study data about the vulnerability localization, which is annotated by based on modifications made to the API, is listed in "2_vulnerability_localization.xlsx"

#### 5. Vulnerability Fix Study
(1)The study data about the vulnerability fix in the library end is listed in "3_vulnerability_fix_library.xlsx"
(2)The study data about the vulnerability fix in the client end is listed in "4_vulnerability_fix_client.xlsx"

