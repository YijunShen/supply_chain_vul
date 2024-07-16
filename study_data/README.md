## Understanding the dataset:

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
