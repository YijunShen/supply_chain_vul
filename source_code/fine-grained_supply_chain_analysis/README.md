## How to construct method-level supply chain:

#### 1. copy the folder 'home' and all files inside it to the root folder of the linux system:

#### 2. Java environment, Python environment(3.8.8), and neo4j database(4.3.3) is needed 

#### 3. change the neo4j address in the resolve.py under '/home/sdp/science/lcp/CallGraph/src/main'

#### 4. change the input group, artifact, version in the main.py under '/home/sdp/science/lcp/CallGraph/src/main'

#### 5. run main.py. Then the method-level supply chain will be constructed as follw: obtaining source jar file from the Maven Central website; analyzing the call-graph of the project; storing the result to target neo4j database

#### P.S. The java-call-graph tool is modified from the gr.gousiosg.javacg:0.1-SNAPSHOT. It has been complied and used as 'java_cg.jar'. The source code are disclosed under the folder ‘source_code_of_jave-call-graph_tool’