#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
from Patterns import Patterns
import re
import json as JSON
import os
import copy
import time
import logging
import queue

import sys
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0].replace("\\", "/")
sys.path.insert(0, rootPath + "/util")
from util.Dealjar import Jardealer


class App:
    def __init__(self, uri, user, password, databaseName, batchsize=2000, log=True, driver=True):
        if driver:
            self.driver = GraphDatabase.driver(uri, auth=(user, password), max_connection_lifetime=3600 * 24 * 30,
                                           keep_alive=True)
        
        self.databaseName = databaseName
        
        self.pattern = Patterns()
        self.jardealer = Jardealer(log=False)
        self.map = None
        self.batchsize = batchsize
        self.ordercnt = 0

        if log:
            self.logger = logging.getLogger("neo4j_logger")
            handler = logging.FileHandler("neo4j.log")
            formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.CRITICAL)
        
    def clearOrderCnt(self):
        self.ordercnt = 0

    def close(self):
        self.driver.close()
    
    def loadPkgDepJsonTxt(self, group, artifact, version, loaddepdep=True):
        st = time.time()
        rootstate, rootrlt =  self.loadPkgJsonTxt(group, artifact, version)
        print(rootrlt)
        
        DonePkg = set()
        DonePkg.add(group+":"+artifact+":"+version)
        
        depJsonPath = self.jardealer.mvn.getPkgDepJsonPath(group, artifact, version)

        deps = self.jardealer.mvn.getDepsFromJson(depJsonPath)
        rootdep = len(deps)
        totaldep = rootdep
        
        DoneDepsPkg = set()
        q = queue.Queue()

        deprlt = self.loadDepsJsonTxt(group, artifact, version)
        DoneDepsPkg.add(group+":"+artifact+":"+version)
        print(deprlt)

        if loaddepdep:
            info1 = "----LOAD DEPDEP %s:%s:%s"%(group, artifact, version)
            self.logger.critical(info1)
            print(info1)

            for dep in deps:
                depid = dep["groupId"] + ":" + dep["artifactId"] + ":" + dep["version"]
                DonePkg.add(depid)
                if depid not in DoneDepsPkg:
                    q.put(depid)
            
            while not q.empty():
                curid = q.get()
                curGroup, curArtifact, curVersion = curid.split(":")
                curdeprlt = self.loadDepsJsonTxt(curGroup, curArtifact, curVersion)
                DoneDepsPkg.add(curid)
                print(curdeprlt)
                
                curjsonPath = self.jardealer.mvn.getPkgDepJsonPath(curGroup, curArtifact, curVersion) 
                curdeps = self.jardealer.mvn.getDepsFromJson(curjsonPath)
                
                for curdep in curdeps:
                    curdepid = curdep["groupId"] + ":" + dep["artifactId"] + ":" + dep["version"]
                    DonePkg.add(curdepid)
                    if curdepid not in DoneDepsPkg:
                        q.put(curdepid)
            
            totaldep = len(DonePkg) - 1

            info2 = "----LOADED DEPDEP %s:%s:%s, %d root dep -> %d dep dep"%(group, artifact, version, rootdep, totaldep - rootdep) 
            self.logger.critical(info2)
            print(info2)
        
        ed = time.time()
        rlt = "load pkgdeps %s:%s:%s json and txt, root: %s, deal dep dep: %s, %d root dep -> %d dep dep, time: %f"%(group, artifact, version, rootstate, loaddepdep, rootdep, totaldep - rootdep, ed - st)
        print("---------------------")
        return rlt

    def loadDepsJsonTxt(self, groupID, artifactID, version):
        st = time.time()

        depJsonPath = self.jardealer.mvn.getPkgDepJsonPath(groupID, artifactID, version)

        deps = self.jardealer.mvn.getDepsFromJson(depJsonPath)
        depcnt = len(deps)      
        sucdepcnt = 0
        faildepcnt = 0
        dupdepcnt = 0

        info1 = "START LOAD DEPS %s:%s:%s json and txt, deps: %d"%(groupID, artifactID, version, depcnt)
        self.logger.critical(info1)
        print("LOAD DEPS %s:%s:%s json and txt, deps: %d"%(groupID, artifactID, version, depcnt))
        for dep in deps:
            depGroup = dep["groupId"]
            depArtifact = dep["artifactId"]
            depVersion = dep["version"]
            
            depstate, deprlt = self.loadPkgJsonTxt(depGroup, depArtifact, depVersion)
            if depstate == 1:
                sucdepcnt += 1
            elif depstate == 0:
                dupdepcnt += 1
            else:
                faildepcnt += 1
        
        ed = time.time()
        rlt = "load deps %s:%s:%s json and txt, deps: %d, suc: %d, dup: %d, fail: %d, time: %f"%(groupID, artifactID, version, depcnt, sucdepcnt, dupdepcnt, faildepcnt, ed - st)
        self.logger.critical(rlt)
        return rlt

    def loadPkgJsonTxt(self, groupID, artifactID, version):
        jsonpath = self.jardealer.getJsonPath(groupID, artifactID, version)
        txtpath = self.jardealer.getTxtPath(groupID, artifactID, version)
        state, rlt = self.loadJsonTxt(jsonpath, txtpath, groupID, artifactID, version)
        return state, rlt

    def loadJsonTxt(self, jsonpath, txtpath, groupID, artifactID, version):
        st = time.time()
        
        classcnt, t1 = self.myloadPkgJson(jsonpath, groupID, artifactID, version)
        
        match = 0 
        total = 0
        t2 = 0
        if classcnt >= 0:
            match, total, t2 = self.myloadTxt(txtpath, groupID, artifactID, version)
            ed = time.time()
            rlt = "load %s:%s:%s json and txt, class: %s, t1: %f s, call: %s/%s, t2: %f, time: %f s"%(groupID, artifactID, version, classcnt, t1, match, total, t2,  ed - st)

            self.logger.critical(f"{rlt}")
            return 1, rlt
        else:
            errtype =  "NOT EXIST" if classcnt == -2 else "LOADED"
            state = -1 if classcnt == -2 else 0
            rlt = "%s %s:%s:%s json and txt"%(errtype, groupID, artifactID, version)

            self.logger.critical(f"{rlt}")

            return state, rlt

    def myloadPkgJson(self, jsonpath, groupID, artifactID, version):
        if not os.path.exists(jsonpath):
            return -2, 0

        session = self.driver.session(database=self.databaseName)
        tx = session.begin_transaction()
        
        st = time.time()
        pkg_id = groupID + ":" + artifactID + ":" + version

        if self.searchPkgLoaded(tx, pkg_id):
            ed = time.time()
            tx.commit()
            session.close()
            return -1, 0
        
        classcnt = self.loadPkgJsons(session, tx, jsonpath, groupID, artifactID, version)
        session.close()
        self.clearOrderCnt()
        
        ed = time.time()
        t = ed - st
        
        return classcnt, t

    def myloadTxt(self, file, groupID, artifactID, version):
        if not os.path.exists(file):
            print("%s:%s:%s cgtxt not exist: %s"%(groupID, artifactID, version, file))
            return -1, -1, 0
        
        session = self.driver.session(database=self.databaseName)
        tx = session.begin_transaction()
        
        st = time.time()
        rlt = self.load(session, tx, file, groupID, artifactID, version)
        total = rlt["total"]
        match = rlt["match"]
        self.clearOrderCnt()
        
        ed = time.time()
        t = ed - st

        session.close()
        return match, total, t

    def getClassPkgDict(self, groupID, artifactID, version):
        self.map = self.jardealer.getLibDepClassDict(groupID, artifactID, version)
        self.ppc_map = {}
        self.ccm_map = {}

    def load(self, session, tx, file, groupID, artifactID, version):
        query = (
                "MERGE (p1:Package{id: $id}) set p1.name = $pkg_name, p1.version = $version "
                "RETURN p1"
        )  
        pkg_id = groupID + ":" + artifactID + ":" + version
        pkg_name = groupID + ":" + artifactID 
        tx.run(query, id=pkg_id, pkg_name=pkg_name, version=version)
        self.ordercnt += 1

        self.getClassPkgDict(groupID, artifactID, version)
        num = 0
        matchcnt = 0
        with open(file, 'r') as f:
            line = f.readline()
            while line:
                matched = self.loadOneCall(tx, line, groupID, artifactID, version)
                matchcnt += matched
                num += 1
                line = f.readline()

        tx.commit()
        self.clearOrderCnt()
        self.map.clear()
        self.ppc_map.clear()
        self.ccm_map.clear()
        
        return {"total":num, "match":matchcnt}

    def checkPkgType(self, pkg):
        tpm = re.match(self.pattern.domain, pkg)
        if tpm:
            if tpm.group(1) == "java":
                return "std"
            else :
                return tpm.group(1)
        else:
            return "unknown"

    def loadOneCall(self, tx, line, groupID, artifactID, version):
        if not self.map:
            print("LOADONECALL getClassPkgDict!!!")
            self.getClassPkgDict(groupID, artifactID, version)

        if line[0] == 'C':
            m = re.match(self.pattern.class_class_pattern, line) 
            if m :
                srcClassName = m.group(1)
                dstClassName = m.group(3)
                srcPkgid = self.map.get(srcClassName)
                dstPkgid = self.map.get(dstClassName)

                if not srcPkgid or not dstPkgid:
                    return 0

                srcClassid = srcPkgid + "@" + srcClassName 
                dstClassid = dstPkgid + "@" + dstClassName 

                srcType = self.checkPkgType(srcClassName)
                dstType = self.checkPkgType(dstClassName)

                callType = ""
                if dstType == "std":
                    callType = "stdCall"
                    return 0
                else:
                    callType = "Call"

                query = (
                    "MERGE (p1:Class{id: $srcClassid}) "
                    "MERGE (p2:Class{id: $dstClassid}) "
                    "MERGE (p1)-[call:ClassCall{type:$callType}]->(p2) "
                    "RETURN p1"
                )
                result = tx.run(query, srcClassid=srcClassid, dstClassid=dstClassid, callType=callType)
                self.ordercnt += 1
                return 1
            else:
                return 0
        elif line[0] == 'M':
            m = re.match(self.pattern.nmmp, line)
            if m :
                srcClassName = m.group(4)
                dstClassName = m.group(16)

                srcPkgid = self.map.get(srcClassName)
                dstPkgid = self.map.get(dstClassName)

                if not srcPkgid or not dstPkgid:
                    return 0

                callOut = False
                if srcPkgid != dstPkgid:
                    callOut = True

                srcClassid = srcPkgid + "@" + srcClassName 
                dstClassid = dstPkgid + "@" + dstClassName 

                srcMthdName = m.group(2)
                dstMthdName = m.group(14)
                srcMthdid = srcPkgid + "@" + srcMthdName 
                dstMthid = dstPkgid + "@" + dstMthdName  

                if len(srcMthdid) > 1500 or len(dstMthid) > 1500:
                    return 0

                curpp = srcPkgid + "-" + dstPkgid
                curcc = srcClassid + "-" + dstClassid   
                curmm = srcMthdid + "-" + dstMthid

                callId = m.group(13)

                srcType = self.checkPkgType(srcClassName)
                dstType = self.checkPkgType(dstClassName)

                callType = ""
                if dstType == "std":
                    callType = "stdCall"
                    return 0
                else:
                    callType = "Call"

                if callOut:
                    query = (
                        "MERGE (m1:Method{id: $srcMthdid}) set m1.outCall = true "
                        "MERGE (m2:Method{id: $dstMthid}) set m2.inCall = true "
                        "MERGE (m1)-[call:MethodCall{id:$callId, type:$callType}]->(m2) "
                        "ON CREATE SET call.weight = 1 "
                        "ON MATCH SET call.weight = COALESCE(call.weight, 0) + 1 "
                        "SET call.outCall = true "
                    )
                else:    
                    query = (
                        "MERGE (m1:Method{id: $srcMthdid}) "
                        "MERGE (m2:Method{id: $dstMthid}) "
                        "MERGE (m1)-[call:MethodCall{id:$callId, type:$callType}]->(m2) "
                        "ON CREATE SET call.weight = 1 "
                        "ON MATCH SET call.weight = COALESCE(call.weight, 0) + 1 "
                        "SET call.outCall = false "
                    )
                
                tx.run(query, srcMthdid=srcMthdid, dstMthid=dstMthid, callId = callId, callType=callType)
                self.ordercnt += 1

                newcc = False
                newmm = False
                
                if curpp not in self.ppc_map:
                    self.ppc_map[curpp] = set() 
                if curcc not in self.ppc_map[curpp]:
                    newcc = True
                    self.ppc_map[curpp].add(curcc)
                
                if curcc not in self.ccm_map:
                    self.ccm_map[curcc] = set()
                if curmm not in self.ccm_map[curcc]:
                    self.ccm_map[curcc].add(curmm)
                    newmm = True
               
                if callOut:
                    query = (
                        "MERGE (p1:Class{id: $srcClassid}) set p1.outCall = true "
                        "MERGE (p2:Class{id: $dstClassid}) set p2.inCall = true "
                        "MERGE (p1)-[call:ClassCall{type:$callType}]->(p2) "
                        "ON CREATE SET call.weight = 1 "
                        "ON MATCH SET call.weight = COALESCE(call.weight, 0) + 1 "
                        "SET call.outCall = true "
                    )
                else:
                    query = (
                        "MERGE (p1:Class{id: $srcClassid}) "
                        "MERGE (p2:Class{id: $dstClassid}) "
                        "MERGE (p1)-[call:ClassCall{type:$callType}]->(p2) "
                        "ON CREATE SET call.weight = 1 "
                        "ON MATCH SET call.weight = COALESCE(call.weight, 0) + 1 "
                        "SET call.outCall = false "
                )
                tx.run(query, srcClassid=srcClassid, dstClassid=dstClassid, callType=callType)
                self.ordercnt += 1 
                
                if newmm:
                    query = (
                        "MATCH (p1:Class{id: $srcClassid}) "
                        "MATCH (p2:Class{id: $dstClassid}) "
                        "MATCH (p1)-[call:ClassCall]->(p2) " 
                        "SET call.mmCnt = COALESCE(call.mmCnt, 0) + 1 "
                    )
                    result = tx.run(query, srcClassid=srcClassid, dstClassid=dstClassid)
                    self.ordercnt += 1

                if newcc:
                        query = (
                        "MERGE (p1:Package{id: $srcPkgid}) "
                        "MERGE (p2:Package{id: $dstPkgid}) "
                        "MERGE (p1)-[depend:DependOn]->(p2) "
                        "ON CREATE SET depend.weight = 1 "
                        "ON MATCH SET depend.weight = COALESCE(depend.weight, 0) + 1 "
                        "SET depend.ccCnt = COALESCE(depend.ccCnt, 0) + 1 "
                    )
                else:
                    query = (
                        "MERGE (p1:Package{id: $srcPkgid}) "
                        "MERGE (p2:Package{id: $dstPkgid}) "
                        "MERGE (p1)-[depend:DependOn]->(p2) "
                        "ON CREATE SET depend.weight = 1 "
                        "ON MATCH SET depend.weight = COALESCE(depend.weight, 0) + 1 "
                    )
                tx.run(query, srcPkgid=srcPkgid, dstPkgid=dstPkgid)
                self.ordercnt += 1
                
                return 1
            else:
                return 0
        else:
            return 0

    def loadPkgJsons(self, session, tx, path, groupID, artifactID, version):
        query = (
                "MERGE (p1:Package{id: $id})set p1.Loaded = True, p1.name = $pkg_name, p1.version = $version "
                "RETURN p1"
        )  
        pkg_id = groupID + ":" + artifactID + ":" + version
        pkg_name = groupID + ":" + artifactID 
        tx.run(query, id=pkg_id, pkg_name=pkg_name, version=version)

        allJson = self.getAlljsonFromPath(path)
        classcnt = 0
        for className, classJson in allJson.items():
            self.loadClassJson(tx, allJson, classJson, pkg_id)
            classcnt += 1
        tx.commit()

        return classcnt

    def loadClassJson(self, tx, allJson, classJson, pkgid):
        className = classJson["className"]
        isFinal = classJson["isFinal"] 
        isAbstract = classJson["isAbstract"]
        isInterface = classJson["isInterface"]
        superClassName = classJson["superClassName"]
        methods = classJson["methods"]
        interfaceObj = classJson["interNames"]
        
        classid = pkgid + "@" + className
        query = (
                "MATCH (pkg:Package{id: $id}) "
                "MERGE (p1:Class{id: $src}) set p1.className = $className, p1.isFinal = $isFinal, p1.isAbstract = $isAbstract, p1.isInterface = $isInterface "
                "MERGE (pkg) -[has:HasClass]->(p1) "
                "RETURN p1"
        ) 
        tx.run(query, id=pkgid, src=classid, className=className, isFinal=isFinal, isAbstract=isAbstract, isInterface=isInterface)
        self.ordercnt += 1

        for interName in interfaceObj:
            if interName in allJson:
                interquery = (
                    "MERGE (p1:Class{id: $src}) "
                    "MERGE (p2:Class{id: $dst}) "
                    "MERGE (p1)-[call:ClassCall]->(p2) set call.type = $callType "
                )
                if isInterface:
                    callType = "ExtendInter"
                else:
                    callType = "ImpleInter"

                interid = pkgid + "@" + interName
                tx.run(interquery, src=classid, dst=interid, callType=callType)
                self.ordercnt += 1    

        if not isInterface:
            if superClassName in allJson:
                query1 = (
                    "MERGE (p1:Class{id: $src}) "
                    "MERGE (p2:Class{id: $dst}) "
                    "MERGE (p1)-[call:ClassCall]->(p2) set call.type = 'ExtendClass' "
                )

                superClassid = pkgid + "@" + superClassName
                tx.run(query1, src=classid, dst=superClassid)
                self.ordercnt += 1

        for methodKey, methodObj in methods.items():
            methodName = methodObj["name"]
            methodArgs = methodObj["args"]
            methodType = methodObj["type"]

            methodId = pkgid + "@" + className + ":" + methodName + methodArgs

            if len(methodId) > 1500:
                continue

            isMethodStatic = methodObj["isStatic"]
            isMethodFinal = methodObj["isFinal"]
            isMethodAbstract = methodObj["isAbstract"]

            methodQuery = (
                "MERGE (c1:Class{id: $classid}) "
                "MERGE (m1:Method{id: $methodId}) set m1.Name=$methodName, m1.Type = $methodType, m1.isStatic = $isMethodStatic, m1.isFinal = $isMethodFinal, m1.isAbstract = $isMethodAbstract "
                "MERGE (c1) -[has:HasMethod]->(m1) "
                "RETURN c1, m1 " 
            )
            tx.run(methodQuery, classid=classid, methodId=methodId, methodName=methodName, methodType=methodType, isMethodStatic=isMethodStatic, isMethodFinal=isMethodFinal, isMethodAbstract=isMethodAbstract)
            self.ordercnt += 1

            if isInterface and methodType == "extend":
                for interName in interfaceObj:
                    if interName in allJson:
                        curInterObj = allJson[interName]
                        if methodKey in curInterObj["methods"]:
                            extendQuery = (
                                "MERGE (m1:Method{id: $methodId}) "
                                "MERGE (m2:Method{id: $supermethodId}) "
                                "MERGE (m1) -[call:MethodExtend]->(m2) set call.type = 'Extend' "
                                "RETURN m1, m2 "  
                            )
                            superMethodId = pkgid + "@" + interName + ":" + methodName + methodArgs 
                            tx.run(extendQuery, methodId=methodId, supermethodId=superMethodId)
                            self.ordercnt += 1
                            break

            elif not isInterface:
                if methodType == "extend" and superClassName in allJson:
                    extendQuery = (
                            "MERGE (m1:Method{id: $methodId}) "
                            "MERGE (m2:Method{id: $supermethodId}) "
                            "MERGE (m1) -[call:MethodCall]->(m2) set call.type = 'Extend' "
                            "RETURN m1, m2 "  
                        )
                    
                    superMethodId = pkgid + "@" + superClassName + ":" + methodName + methodArgs
                    tx.run(extendQuery, methodId=methodId, supermethodId=superMethodId)
                    self.ordercnt += 1

                elif methodType == "implement" and superClassName in allJson:
                    
                    implementQuery = (
                            "MERGE (m1:Method{id: $methodId}) "
                            "MERGE (m2:Method{id: $supermethodId}) "
                            "MERGE (m2) -[call:MethodCall]->(m1) set call.type = 'ImplementBy' "
                            "RETURN m1, m2 "  
                        )                
                    superMethodId = pkgid + "@" + superClassName + ":" + methodName + methodArgs
                    tx.run(implementQuery, methodId=methodId, supermethodId=superMethodId)
                    self.ordercnt += 1               

                elif methodType == "define":
                    for interName in interfaceObj:
                        if interName in allJson:
                            curInterObj = allJson[interName]
                            if methodKey in curInterObj["methods"]: 
                                extendQuery = (
                                    "MERGE (m1:Method{id: $methodId}) "
                                    "MERGE (m2:Method{id: $intermethodId}) "
                                    "MERGE (m2) -[call:MethodCall]->(m1) set call.type = 'ImplementBy' "
                                    "RETURN m1, m2 "  
                                )
                                intermethodId = pkgid + "@" + interName + ":" + methodName + methodArgs 
                                tx.run(extendQuery, methodId=methodId, intermethodId=intermethodId)
                                self.ordercnt += 1
                                break

    def check(self, superJson, curJson, isClass):
        if "methods" in superJson and "methods" in curJson:
            superMethods = superJson["methods"]
            curMethods = curJson["methods"]
    
            for superMethodName,superMethodObj in superMethods.items():
                if isClass:
                    if superMethodObj["isStatic"]:
                        if superMethodName not in curMethods:
                            copyMethodObj = copy.deepcopy(superMethodObj)
                            copyMethodObj["type"] = "extend"
                            curMethods[superMethodName] = copyMethodObj

                    elif superMethodObj["isFinal"]:
                        copyMethodObj = copy.deepcopy(superMethodObj)
                        copyMethodObj["type"] = "extend"
                        curMethods[superMethodName] = copyMethodObj 
                    
                    elif superMethodObj["isAbstract"]:
                        if superMethodName not in curMethods or curMethods[superMethodName]["sig"] != superMethodObj["sig"]:
                            copyMethodObj = copy.deepcopy(superMethodObj)
                            copyMethodObj["type"] = "extend"
                            curMethods[superMethodName] = copyMethodObj

                        elif curMethods[superMethodName]["isAbstract"]:
                            curMethods[superMethodName]["type"] = "extend" 
                           
                        else:
                            curMethods[superMethodName]["type"] = "implement"

                    else:
                        if superMethodName in curMethods and curMethods[superMethodName]["sig"] == superMethodObj["sig"]:
                            curMethods[superMethodName]["type"] = "override"

                        else:
                            copyMethodObj = copy.deepcopy(superMethodObj)
                            copyMethodObj["type"] = "extend"
                            curMethods[superMethodName] = copyMethodObj

                else: 
                        copyMethodObj = copy.deepcopy(superMethodObj)
                        copyMethodObj["type"] = "extend" 
                        curMethods[superMethodName] = copyMethodObj 

    def recur(self, allJson, json):
        if json["finishedSearch"]:
            return
        
        superClassName = json["superClassName"]
        if superClassName not in allJson:
            json["finishedSearch"] = True
            return
        
        superJson = allJson[superClassName]
        if not superJson["finishedSearch"]:
            self.recur(allJson, superJson)
        
        self.check(superJson, json, True)
        json["finishedSearch"] = True
            
    def recurInterface(self, allJson, json):
        if json["finishedSearch"]:
            return
        
        if len(json["interNames"]) == 0:
            json["finishedSearch"] = True
            return
        
        for superInterfaceName in json["interNames"]:
            if superInterfaceName not in allJson:
                continue
            superJson = allJson[superInterfaceName]
            if not superJson["finishedSearch"]:
                self.recurInterface(allJson, superJson)
            self.check(superJson, json, False)
             
        json["finishedSearch"] = True    

    def dealJosnsFromPath(self, path):
        files = os.listdir(path)
        filecnt = len(files)
        allJson = {}
        for file in files:
            if not os.path.isdir(file):
                f = open(path + "/" + file, 'r')
                content = f.read()
                fileJson = JSON.loads(content)
                f.close
                allJson[fileJson["className"]] = fileJson

        try:
            for myjson in allJson.values():
                if not myjson["isInterface"]:
                    self.recur(allJson, myjson)
                else:
                    self.recurInterface(allJson, myjson)
            
            return filecnt, allJson
        except RecursionError:
            print("RecursionError: %s" % path)
            return 0, {}

    def createAlljsonFromPath(self, path):
        allJsonPath = path + "/allJson.json"
        jsoncnt, allJson = self.dealJosnsFromPath(path)
        with open(allJsonPath, 'w') as f:
            JSON.dump(allJson, f)
        return jsoncnt, allJson
    
    def getAlljsonFromPath(self, path):
        allJsonPath = path + "/allJson.json"
        allJson = {}
        if os.path.exists(allJsonPath):
            with open(allJsonPath, 'r') as f:
                allJson = JSON.load(f)
                return allJson
        else:
            jsoncnt, allJson = self.createAlljsonFromPath(path)
            return allJson
            
    def searchNoSelfCirclePkg(self, tx):
        query = (
            "MATCH (n:Package) "
            "WHERE NOT (n)-[:DependOn]->(n) "
            "RETURN n.id as id"
        )

        result = tx.run(query).data()
        cnt = 0
        pkgs = []
        if result:
            for record in result:
                cnt += 1
                pkgs.append((record['id']))

        return pkgs

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
    
    def searchPkgLoaded(self, tx, pkgid):
        query = (
            "MATCH (p:Package{id:$id}) "
            "RETURN p.Loaded as loaded"
        )

        rlt = tx.run(query, id=pkgid).data()
        if rlt:
            rlt = rlt[0]['loaded']
            if rlt:
                return True
            else:
                return False
        else:
            return False

    def testPkgLoaded(self, pkgid):
        with self.driver.session() as session:
            tx = session.begin_transaction()
            rlt = self.searchPkgLoaded(tx, pkgid)
            return rlt
    
    def testPkg(self, pkgid):
        with self.driver.session() as session:
            tx = session.begin_transaction()
            rlt = self.searchPkg(tx, pkgid)
            return rlt