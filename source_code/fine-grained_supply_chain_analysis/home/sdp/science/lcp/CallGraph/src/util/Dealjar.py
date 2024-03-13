import subprocess
import os
import time
import json
import re
import logging
import queue
from Mvncmd import Mvncmd

class Jardealer:

    def __init__(self, txtdirname="cgtxt/", jsondirname="classjson/", log=True):
        self.jarroot = "/home/sdp/science/lcp/CallGraph/data/jars/"
        self.cgroot = "/home/sdp/science/lcp/CallGraph/data/cgdata/"
        self.txtroot = self.cgroot + txtdirname 
        self.jsonroot = self.cgroot + jsondirname 
        self.mvn = Mvncmd(log=log) 

        if log:
            self.log = True
            
            self.pkgLogger = logging.getLogger("deal_pkg_logger")
            pkgHandler = logging.FileHandler("deal_pkg.log")
            pkgFormatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
            pkgHandler.setFormatter(pkgFormatter)
            self.pkgLogger.addHandler(pkgHandler)
            self.pkgLogger.setLevel(logging.CRITICAL)
            
            self.pkgDepLogger = logging.getLogger("deal_pkgdep_logger")
            pkgDepHandler = logging.FileHandler("deal_pkgdep.log")
            pkgDepFormatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
            pkgDepHandler.setFormatter(pkgDepFormatter)
            self.pkgDepLogger.addHandler(pkgDepHandler)
            self.pkgDepLogger.setLevel(logging.CRITICAL)
        else:
            self.log = False

    def call_jar(self, jar_path, filepath):
        execute = "java -jar {} {}".format(jar_path, filepath)
        output = subprocess.Popen(execute, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        res = output.stdout.readlines()
        return res

    def call_jar(self, jar_path, filepath, cgroot):
        execute = "java -jar {} {} {}".format(jar_path, filepath, cgroot)
        output = subprocess.Popen(execute, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        res = output.stdout.readlines()
        return res 

    def find_jars(self, directory):
        jars = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.jar'):
                    jars.append(os.path.join(root, file))
        return jars

    def find_jarpath(self, directory):
        pkgs = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.jar'):
                    pkgs.append(root)
        return pkgs
    
    def find_jarPathandName(self, directory):
        data = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.jar'):
                    data.append({"path":root+"/", "name":file})
        return data

    def deal_jars_under(self, cgdealer, path):
        jars = self.find_jars(path)
        cnt = len(jars)
        
        print("find %s jars in path"%(cnt))

        succnt = 0
        exsitcnt = 0
        faillist = []
        st = time.time()

        for jar in jars:
            name = os.path.basename(jar)
            txtfile = self.txtroot + name  + "-single.txt"

            if os.path.exists(txtfile):
                exsitcnt += 1
                continue

            res = self.call_jar(cgdealer, jar, self.cgroot)

            if os.path.exists(txtfile):
                succnt += 1
            else:
                faillist.append({name:res})

        ed = time.time()
        print("dealt", exsitcnt, "before,  finish", succnt, "jars of", cnt, "files in", path)
        print('Time cosuming: %f s\n'%(ed - st))

        json_data = json.dumps(faillist)
        filename = "/home/sdp/science/lcp/CallGraph/data/jars/fail_cg.json"
        if not os.path.exists(filename):
            with open(filename, 'w') as f:
                f.write(json_data)

    def getTxtPath(self, group, artifact, version):
        return self.txtroot + group + "--" + artifact + "--" + version + ".jar-single.txt"

    def checkTxtExist(self, group, artifact, version):
        return os.path.exists(self.getTxtPath(group, artifact, version))
    
    def getJsonPath(self, group, artifact, version):
        return self.jsonroot + group + "--" + artifact + "--" + version + "-json"

    def getDepsFromJson(self, jsonPath):
        if not os.path.exists(jsonPath):
            return []
        
        deps = []
        with open(jsonPath, 'r') as f:
            data = json.load(f)
            for dep in data:
                deps.append({"groupId":dep["groupId"], "artifactId":dep["artifactId"], "version":dep["version"]})
        
        return deps

    def deal_pkg_jar(self, cgdealer, group, artifact, version):
        rootJarPath = self.mvn.getPkgJarPath(group, artifact, version)
        if not os.path.exists(rootJarPath):
            rlt = "NOT EXIST %s:%s:%s jar"%(group, artifact, version)
            if self.log:
                self.pkgLogger.critical(rlt)
            return -2, rlt
        
        if self.checkTxtExist(group, artifact, version):
            rlt = "DEALED %s:%s:%s jar"%(group, artifact, version)
            if self.log:
                self.pkgLogger.critical(rlt)
            return 0, rlt
        else:
            st = time.time()
            self.call_jar(cgdealer, rootJarPath, self.cgroot)
            ed = time.time()
            
            if not self.checkTxtExist(group, artifact, version):
                rlt = "FAIL DEAL %s:%s:%s jar"%(group, artifact, version)
                if self.log:
                    self.pkgLogger.critical(rlt)
                return -1, rlt
            else:
                rlt = "deal %s:%s:%s jar, time: %f s"%(group, artifact, version, ed - st)
                if self.log:
                    self.pkgLogger.critical(rlt)
                return 1, rlt

    def del_dep_jars(self, cgdealer, group, artifact, version):
        st = time.time()        
        depJsonPath = self.mvn.getPkgDepJsonPath(group, artifact, version)
        deps = self.mvn.getDepsFromJson(depJsonPath)
        depcnt = len(deps)
        
        depsuccnt = 0
        depdupcnt = 0
        depfailcnt = 0
        depmisscnt = 0
        
        for dep in deps:
            depGroup = dep["groupId"]
            depArtifact = dep["artifactId"]
            depVersion = dep["version"]
            
            depstate, deprlt = self.deal_pkg_jar(cgdealer, depGroup, depArtifact, depVersion)

            if depstate == -2:
                depmisscnt += 1
            elif depstate == -1:
                depfailcnt += 1
            elif depstate == 0:
                depdupcnt += 1
            else:
                depsuccnt += 1

        ed = time.time()
        rlt = "deal deps %s:%s:%s, %s deps, %s succ, %s dup, %s fail, %s miss in %s s"%(group, artifact, version, depcnt, depsuccnt, depdupcnt, depfailcnt, depmisscnt, ed - st)
        if self.log:
            self.pkgDepLogger.critical(rlt)
        return rlt

    def deal_pkg_dep_jars(self, cgdealer, group, artifact, version, dealdepdep=True):
        st = time.time()

        state, rlt = self.deal_pkg_jar(cgdealer, group, artifact, version)
        print(rlt)

        if state == -2:
            return False, ""
        
        DonePkg = set() 
        DonePkg.add(group+":"+artifact+":"+version)
        
        depJsonPath = self.mvn.getPkgDepJsonPath(group, artifact, version)

        deps = self.mvn.getDepsFromJson(depJsonPath)
        rootdep = len(deps)
        totaldep = rootdep
        
        DoneDepsPkg = set()
        q = queue.Queue()

        deprlt = self.del_dep_jars(cgdealer, group, artifact, version)
        DoneDepsPkg.add(group+":"+artifact+":"+version)
        print(deprlt)

        if dealdepdep:
            info1 = "----DEAL DEPDEP %s:%s:%s"%(group, artifact, version)
            if self.log:
                self.pkgDepLogger.critical(info1)
            print(info1)
            
            for dep in deps:
                depid = dep["groupId"] + ":" + dep["artifactId"] + ":" + dep["version"]
                DonePkg.add(depid) 
                if depid not in DoneDepsPkg:
                    q.put(depid)
            
            while not q.empty():
                curid = q.get()
                curGroup, curArtifact, curVersion = curid.split(":")
                curdeprlt = self.del_dep_jars(cgdealer, curGroup, curArtifact, curVersion)
                DoneDepsPkg.add(curid)
                print(curdeprlt)
                
                curjsonPath = self.mvn.getPkgDepJsonPath(curGroup, curArtifact, curVersion) 
                curdeps = self.mvn.getDepsFromJson(curjsonPath)
                
                for curdep in curdeps:
                    curdepid = curdep["groupId"] + ":" + dep["artifactId"] + ":" + dep["version"]
                    DonePkg.add(curdepid)
                    if curdepid not in DoneDepsPkg:
                        q.put(curdepid)
            
            totaldep = len(DonePkg) - 1
 
            info2 = "----DEALED DEPDEP %s:%s:%s, %d root dep -> %d dep dep"%(group, artifact, version, rootdep, totaldep - rootdep) 
            if self.log:
                self.pkgDepLogger.critical(info2)
            print(info2)
        
        ed = time.time()
        rlt = "deal pkgdeps %s:%s:%s, deal dep dep: %s, %d root dep -> %d dep dep, in %s s"%(group, artifact, version, dealdepdep, rootdep, totaldep - rootdep, ed - st)
        if self.log:
            self.pkgDepLogger.critical(rlt)
        return True, rlt
        
    def getClassPkgDict(self, group, artifact, version, cgdealer="/home/sdp/science/lcp/CallGraph/src/util/java_cg.jar"):
        rlt = {}

        libPkgid = group + ":" + artifact + ":" + version
        libDir = self.jsonroot + group + "--" + artifact + "--" + version + "-json/"

        if not os.path.exists(libDir):
            print("download and deal: %s:%s:%s"%(group, artifact, version))
            downloadrlt = self.mvn.downloadInfo(group, artifact, version, downloadDeps = False, downloaddepdeps = False)
            print(downloadrlt)
            state, dealrlt = self.deal_pkg_jar(cgdealer, group, artifact, version)
            print(dealrlt)
            if not os.path.exists(libDir):
                print("not exsist:",libDir) 
                return rlt

        libJsons = os.listdir(libDir)

        pattern = r"(.*)\.json$"

        for libJson in libJsons:
            m = re.match(pattern, libJson)
            if m:
                libClassName = m.group(1)
                rlt[libClassName] = libPkgid

        return rlt
    
    def getLibDepClassDict(self, group, artifact, version):
        rlt = self.getClassPkgDict(group, artifact, version)

        grouppath = group.replace(".", "/")
        pomPath = self.jarroot + grouppath + '/' + artifact + "/" + version +"/"
        depJsonPath =  pomPath + "deps.json"

        if not os.path.exists(depJsonPath):
            cmd = self.mvn
            cmd.getPomDefault(group, artifact, version)

            for i in range(2):
                if not os.path.exists(depJsonPath):
                    cmd.getDeps(pomPath, pomPath, True)
                else:
                    break

        if not os.path.exists(depJsonPath):
            return rlt

        with open(depJsonPath, 'r') as f:
            data = json.load(f)

        for dep in data:
            depGroup = dep["groupId"]
            depArtifact = dep["artifactId"]
            depVersion = dep["version"]

            depDict = self.getClassPkgDict(depGroup, depArtifact, depVersion)
            rlt.update(depDict)

        return rlt