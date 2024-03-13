#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import time
import re
import os
from Database import App
from Patterns import Patterns

import logging
import sys
sys.path.append('/home/sdp/science/lcp/CallGraph/src/util')
from Dealjar import Jardealer

class Resolve:
    def __init__(self, log = True, driver=True):
        
        self.url = "neo4j://211.71.15.39:7687"
        self.app = App(self.url, "neo4j", "callgraph", "callgraph", log=log, driver=driver)
        self.databaseName = "callgraph"
        
        self.filePath = ""
        
        self.jardealer = Jardealer(log=log)
        
        if log: 
            self.pkgLogger = logging.getLogger("reslove_pkg_logger")
            pkgHandler = logging.FileHandler("reslove_pkg.log")
            pkgFormatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
            pkgHandler.setFormatter(pkgFormatter)
            self.pkgLogger.addHandler(pkgHandler)
            self.pkgLogger.setLevel(logging.CRITICAL)
            
            self.pkgDepLogger = logging.getLogger("reslove_pkgdep_logger")
            pkgDepHandler = logging.FileHandler("reslove_pkgdep.log")
            pkgDepFormatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
            pkgDepHandler.setFormatter(pkgDepFormatter)
            self.pkgDepLogger.addHandler(pkgDepHandler)
            self.pkgDepLogger.setLevel(logging.CRITICAL)
        
    def close(self):
        self.app.close()

    def setPath(self, file):
        self.filePath = file

    def solve_pkg(self, group, artifact, version, download=True, includedeps=True, depdep=True, cgdealer="/home/sdp/science/lcp/CallGraph/src/util/java_cg.jar"):
        print("----------Solving %s:%s:%s----------"%(group, artifact, version))

        st = time.time()
        
        downloadrlt = ""
        if download:
            downloadrlt = self.jardealer.mvn.downloadInfo(group, artifact, version, includedeps, depdep)
            print(downloadrlt)
        else:
            print("Can't find %s:%s:%s and not allowed to download!"%(group, artifact, version))
            return False

        print("---------------------")

        state, dealrlt = self.jardealer.deal_pkg_dep_jars(cgdealer, group, artifact, version, depdep) \
                         if includedeps else \
                             self.jardealer.deal_pkg_jar(cgdealer, group, artifact, version)
                         
        print(dealrlt)               
        print("---------------------") 

        loadrlt = self.app.loadPkgDepJsonTxt(group, artifact, version, depdep) \
                  if includedeps else \
                      self.app.loadPkgJsonTxt(group, artifact, version)
        
        
        print(loadrlt)               
        print("---------------------")  

        self.close()
        ed = time.time()
        
        solveType = "Solve pkgdeps" if includedeps else "Solve "
        rlt = "%s %s:%s:%s, Download: %s---Deal: %s---Load: %s---Total: %f"%(solveType, group, artifact, version, downloadrlt, dealrlt, loadrlt, ed-st)
        
        if includedeps:
            self.pkgDepLogger.critical(rlt)
        else:
            self.pkgLogger.critical(rlt)

        print(rlt)

    def solve_pkgs(self, pkgs):
        cnt = len(pkgs)
        print("start load %s pkgs..."%(cnt))
        
        suc = 0
        dup = 0
        noexsist = 0
        
        st = time.time()
        for pkg in pkgs:
            group = pkg['group']
            artifact = pkg['artifact']
            version = pkg['version']
            state, cur_rlt = self.app.loadPkgJsonTxt(group, artifact, version)
            
            if state == 1:
                suc += 1
            elif state == 0:
                dup += 1
            elif state == 0:
                noexsist += 1
        
        ed = time.time()
        rlt = "finish load %s pkgs, %s suc, %s dup, %s not exsist, time:%f"%(cnt, suc, dup, noexsist, ed-st)
        self.pkgLogger.critical(rlt)
        print(rlt)
        return

    def searchPkg(self, tx, pkgid):
        query = (
            "MATCH (p:Package{id:$id}) "
            "RETURN p.id as id"
        )

        rlt = tx.run(query, id=pkgid).data()
        
        if rlt:
            return True
        else:
            return False

    def createAllJsonInPath(self, jsonroot=None):
        if not jsonroot:
            jsonroot = self.jardealer.jsonroot
            
        if not os.path.isdir(jsonroot):
            print(jsonroot, " is not a valid directory!")
            return

        jsondirs = os.listdir(jsonroot)
        jsondir_pattern = r"(.*)--(.*)--(.*)-json$"
        
        jsondircnt = 0
        dup = 0
        create = 0
        
        allJsonLogger = logging.getLogger("allJson_logger")
        jsonHandler = logging.FileHandler("allJson.log")
        jsonFormatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
        jsonHandler.setFormatter(jsonFormatter)
        allJsonLogger.addHandler(jsonHandler)
        allJsonLogger.setLevel(logging.CRITICAL)

        st = time.time()

        for dir in jsondirs:
            cur_json_path = jsonroot + dir

            group = ""
            artifact = "" 
            version = ""

            if os.path.isdir(cur_json_path):
                m = re.match(jsondir_pattern, dir)
                if m:
                    jsondircnt += 1
                    group = m.group(1)
                    artifact = m.group(2)
                    version = m.group(3)
                    
                    allJsonPath = cur_json_path + "/allJson.json"
                    if os.path.exists(allJsonPath):
                        dup += 1
                        continue
                    
                    create += 1
                    st1 = time.time()
                    classcnt, allJson = self.app.createAlljsonFromPath(cur_json_path)
                    ed1 = time.time()
                    currlt = "Create allJson for %s:%s:%s, classcnt: %d, Time cosuming: %f s"%(group, artifact, version, classcnt, ed1 - st1)
                    print(currlt)
                    allJsonLogger.critical(currlt)

        ed = time.time()
        rlt = "Finish create allJson in %s,  total %d, create %d, exsit %d, Time cosuming: %f s"%(jsonroot, jsondircnt, create, dup, ed - st)
        print(rlt)
        allJsonLogger.critical(rlt)