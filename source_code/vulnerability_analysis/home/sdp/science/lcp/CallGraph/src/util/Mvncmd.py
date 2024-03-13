import subprocess
import os
import shutil
import re
import json
import time
import logging
import queue

class Mvncmd:
    def __init__(self, log=True):
        self.depRltRegex = r"([A-Za-z0-9_\-.]+):([A-Za-z0-9_\-.]+):([A-Za-z0-9_\-.]+):([A-Za-z0-9_\-.]+):([A-Za-z0-9_\-.]+)"

        self.logger = None
        if log:
            self.logger = logging.getLogger("mvn_logger")
            mvnhandler = logging.FileHandler("mvn.log")
            mvnformatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
            mvnhandler.setFormatter(mvnformatter)
            self.logger.addHandler(mvnhandler)
            self.logger.setLevel(logging.CRITICAL)
     
    def getDeps(self, pomPath, outPath="./", save = False, scope = "compile", excludeTransitive = "false"):
        filename = pomPath + "pom.xml"
        if not os.path.exists(filename):
            return {False:[]}

        depJsonPath = pomPath +  ("deps.json" if excludeTransitive == "false" else "directDeps.json")
        if os.path.exists(depJsonPath):
            deps = self.getDepsFromJson(depJsonPath)
            return {True:deps}

        try:
            output = None

            for i in range(3):
                output = subprocess.check_output("cd {} && mvn dependency:list -DincludeScope={} -DexcludeTransitive={}".format(pomPath, scope, excludeTransitive), shell=True, stderr=subprocess.DEVNULL)
                output = output.decode('utf-8')

                if "FAILURE" in output:
                    continue
                else:
                    break

            if not output or "FAILURE" in output:
                print("cannot resolve dependencies in", pomPath)
                return {False:[]}

            matches = re.findall(self.depRltRegex, output)
            deps = []

            for match in matches:
                dependency = {
                    "groupId": match[0],
                    "artifactId": match[1],
                    "packaging": match[2],
                    "version": match[3],
                    "scope": match[4]
                    }
                
                deps.append(dependency)
            
            if save:
                json_data = json.dumps(deps)
                filename = outPath + ("deps.json" if excludeTransitive == "false" else "directDeps.json")
                if not os.path.exists(filename):
                    with open(filename, 'w') as f:
                        f.write(json_data)

        except Exception as e:
            print("cannot resolve dependencies in", pomPath, ": ", e, "\n")
            errfile = outPath + ("errdep.json" if excludeTransitive == "false" else "errDirectDeps.json")
            with open(errfile, 'w') as file:
                pass

            return {False:[]} 


        return {True:deps}

    def getDepJarDirect(self, group, artifact, version, rootpath = "/home/sdp/science/lcp/CallGraph/data/jars/", scope = "compile", excludeTransitive = "false"):
        grouppath = group.replace(".", "/")
        pomPath = rootpath + grouppath + '/' + artifact + "/" + version + "/"

        pomfile = pomPath + "pom.xml"
        if not os.path.exists(pomfile):
            self.getPomDefault(group, artifact, version)

        deps = self.getDeps(pomPath, pomPath, True)

        if True in deps:
            deps = deps[True]
            cnt = len(deps)
            success = 0
            fail = 0
            onlyjar = 0
            for dep in deps:
                depgroup = dep['groupId']
                departifact = dep['artifactId']
                depversion = dep['version'] 

                curjarrlt = self.getJarDefault(depgroup, departifact, depversion)
                curpomrlt = self.getPomDefault(depgroup, departifact, depversion)

                if not curjarrlt:
                    fail += 1
                elif curpomrlt:
                    success += 1
                else:
                    onlyjar += 1

            if success == cnt:
                return {1: "finish all %s resolved deps"%(cnt)}
            else:
                return {2: "success:%s, fail:%s, onlyjar:%s in %s"%(success, fail, onlyjar, cnt)}

        else:
            return {0:"no pom found/resolve failure"}

    def getJarDefault(self, group, artifact, version, rootpath = "/home/sdp/science/lcp/CallGraph/data/jars/"):
        grouppath = group.replace(".", "/")
        newpath = rootpath + grouppath + "/" + artifact + "/" + version + "/"
        if not os.path.exists(newpath):
            os.makedirs(newpath)

        newname = group + "--" + artifact + '--' + version +".jar"
        filename = newpath + newname

        if os.path.exists(filename):
            return True

        try:
            output = None
            for i in range(3):
                output = subprocess.check_output("mvn dependency:get -Dartifact={}:{}:{}:jar -Dtransitive=false -Ddest={}".format(group, artifact, version, filename), shell=True, stderr=subprocess.DEVNULL)
                output = output.decode('utf-8')
                if "FAILURE" in output:
                    continue
                else:
                    return True

            if not output or "FAILURE" in output:
                print("cannot download jar:", group+":"+artifact+":"+version, "\n")
                return False

        except Exception as e:
            print("cannot download jar:", group+":"+artifact+":"+version, e, "\n") 
            return False

    
    def getPomDefault(self, group, artifact, version, rootpath = "/home/sdp/science/lcp/CallGraph/data/jars/"):

        grouppath = group.replace(".", "/")
        newpath = rootpath + grouppath + "/" + artifact + "/" + version + "/"
        if not os.path.exists(newpath):
            os.makedirs(newpath) 

        filename = newpath + "pom.xml"
        depsjson = newpath + "deps.json"
        directdepsjson = newpath + "directDeps.json"

        if os.path.exists(filename):
            if not os.path.exists(depsjson):
                deps = self.getDeps(newpath, newpath, True)
            if not os.path.exists(directdepsjson):
                directdeps = self.getDeps(newpath, newpath, True, "compile", "true")
            return True

        try:
            output = None
            for i in range(3):
                output = subprocess.check_output("mvn dependency:get -Dartifact={}:{}:{}:pom -Dtransitive=false -Ddest={}".format(group, artifact, version, filename), shell=True, stderr=subprocess.DEVNULL)
                output = output.decode('utf-8')

                if "FAILURE" in output:
                    continue
                else:
                    deps = self.getDeps(newpath, newpath, True)
                    directdeps = self.getDeps(newpath, newpath, True, "compile", "true")
                    return True 
            
            if not output or "FAILURE" in output:
                print("cannot download pom:", group+":"+artifact+":"+version, "\n")
                return False

        except Exception as e:
            print("cannot download pom:", group+":"+artifact+":"+version, e, "\n") 
            return False 

    def downloadInfo(self, group, artifact, version, downloadDeps = True, downloaddepdeps = True):
        st = time.time()

        jarrlt = self.getJarDefault(group, artifact, version)
        pomrlt = self.getPomDefault(group, artifact, version)
        
        ed1 = time.time()

        DonePkg = set()
        DonePkg.add(group+":"+artifact+":"+version)
        
        ed2 = 0
        ed3 = 0
        ed4 = 0
        
        rootdep = 0
        totaldep = 0
        
        if downloadDeps:
            
            DoneDepsPkg = set()
            
            q = queue.Queue()
            
            ed2 = time.time()
            deprlt = self.getDepJarDirect(group, artifact, version)
            DoneDepsPkg.add(group+":"+artifact+":"+version)
            ed3 = time.time()
            
            jsonPath = self.getPkgDepJsonPath(group, artifact, version) 
            deps = self.getDepsFromJson(jsonPath)
            rootdep = len(deps)
            totaldep = len(deps)
            
            if downloaddepdeps:
                for dep in deps:
                    depid = dep["groupId"] + ":" + dep["artifactId"] + ":" + dep["version"]
                    DonePkg.add(depid)
                    if depid not in DoneDepsPkg:
                        q.put(depid)
                        
                while not q.empty():
                    curid = q.get()
                    curGroup, curArtifact, curVersion = curid.split(":")
                    
                    self.getDepJarDirect(curGroup, curArtifact, curVersion)
                    DoneDepsPkg.add(curid)
                
                    curjsonPath = self.getPkgDepJsonPath(curGroup, curArtifact, curVersion) 
                    curdeps = self.getDepsFromJson(curjsonPath)
                    for curdep in curdeps:
                        curdepid = curdep["groupId"] + ":" + dep["artifactId"] + ":" + dep["version"]
                        DonePkg.add(curdepid)
                        if curdepid not in DoneDepsPkg:
                            q.put(curdepid)
                
                totaldep = len(DonePkg) - 1

                    
            ed4 = time.time()
        
        else:
            deprlt = {0:"no need to download deps"}

        pkg = group + ":" + artifact + ":" + version
        
        ed = time.time()
        
        rlt = "download %s jar and pom, t1: %f s, deps: %s, t2: %f s, downlaod depdep: %s, t3: %f s, root dep cnt: %d, total dep cnt: %d, time: %f s"%(pkg, ed1 - st, deprlt, ed3 - ed2, downloaddepdeps, ed4 - ed3, rootdep, totaldep, ed - st)

        if self.logger:
            self.logger.critical(rlt)
        return rlt
    
    def getPkgRoot(self, group, artifact, version, rootpath = "/home/sdp/science/lcp/CallGraph/data/jars/"):
        grouppath = group.replace(".", "/")
        pkgroot = rootpath + grouppath + "/" + artifact + "/" + version + "/" 
        return pkgroot
    
    def getPkgJarPath(self, group, artifact, version, rootpath = "/home/sdp/science/lcp/CallGraph/data/jars/"):
        root = self.getPkgRoot(group, artifact, version)
        jarName = group + "--" + artifact + '--' + version +".jar"
        jarPath = root + jarName
        return jarPath
    
    def getPkgPomPath(self, group, artifact, version, rootpath = "/home/sdp/science/lcp/CallGraph/data/jars/"):
        root = self.getPkgRoot(group, artifact, version)
        pomPath = root + "pom.xml"
        return pomPath 
    
    def getPkgDepJsonPath(self, group, artifact, version, rootpath = "/home/sdp/science/lcp/CallGraph/data/jars/"):
        root = self.getPkgRoot(group, artifact, version)
        DepjsonPath = root + "deps.json"
        return DepjsonPath
    
    def getPkgDirectDepJsonPath(self, group, artifact, version, rootpath = "/home/sdp/science/lcp/CallGraph/data/jars/"):
        root = self.getPkgRoot(group, artifact, version)
        directDepjsonPath = root + "directDeps.json"
        return directDepjsonPath

    def getPkgTransDepJsonPath(self, group, artifact, version, rootpath = "/home/sdp/science/lcp/CallGraph/data/jars/"):
        root = self.getPkgRoot(group, artifact, version)
        transDepjsonPath = root + "transDeps.json"
        return transDepjsonPath
    
    def getDepsFromJson(self, jsonPath):
        if not os.path.exists(jsonPath):
            return []
        
        deps = []
        with open(jsonPath, 'r') as f:
            data = json.load(f)
            for dep in data:
                deps.append({"groupId":dep["groupId"], "artifactId":dep["artifactId"], "version":dep["version"]})
        
        return deps