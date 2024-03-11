#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import re

class Patterns:
    def __init__(self):
        self._class = r"([0-9a-zA-Z\_\$]+\.)*[0-9a-zA-Z\_\$]+"
        self._2class = r"^C\:(([0-9a-zA-Z\_\$]+\.)*[0-9a-zA-Z\_\$]+) (([0-9a-zA-Z\_\$]+\.)*[0-9a-zA-Z\_\$]+)$"
        self.class_method_name = r"(([0-9a-zA-Z\_\$]+\.)*[0-9a-zA-Z\_\$]+\:([0-9a-zA-Z\_\$]+))"

        self.arg = r"([0-9a-zA-Z\_\$]+\.)*[0-9a-zA-Z\_\$]+"
        self.argnames = r"((([0-9a-zA-Z\_\$]+\.)*[0-9a-zA-Z\_\$]+)\,)*(([0-9a-zA-Z\_\$]+\.)*[0-9a-zA-Z\_\$]*)"  # arg1,arg2,arg3

        self.alpthaPattern = r"[0-9a-zA-Z\_\$]"
        self.noOroneToken = self.alpthaPattern + "*"
        self.oneToken = self.alpthaPattern + "+"

        self.classPattern = r"(" + self.oneToken + "\.)*" + self.oneToken # 1group
        # m.group(1): srcClassName, m.group(3): dstClassName
        self.class_class_pattern = r"^C\:" + "(" + self.classPattern + ")" + " " + "(" + self.classPattern + ")" + "$" 

        self.class_method_pattern = r"(" + self.classPattern + "\:" + "(" + self.oneToken + "))" #m.group(1) == class:method
        
        self.argsPattern = r"(" + r"((" + self.classPattern + r")\,)*" + r"(" +  r"(" + self.oneToken + "\.)*" + self.noOroneToken + r"))"  # 1+1+1+1+1=5groups
        self.methodPattern = r"(" + self.class_method_pattern + "\(" + self.argsPattern + "\)" + ")" # 1 + 3 + 1 + 5 = 10group

        self.method_method_pattern = r"^M\:" + r"(" + self.methodPattern + r" " + r"\(([MIOSD])\)" + self.methodPattern + r")$" 
        self.domain = r"^([0-9a-zA-Z\_\$]+)\..*"
        
        self.cmp =  r"(" + "("+self.classPattern+")" + "\:" + "(" + self.oneToken + "))"
        self.mp = r"(" + self.cmp + "\(" + self.argsPattern + "\)" + ")"

        # srcMthdName: group(2)
        # dstMthdName: group(14)
        # srcClassName: group(4)
        # dstClassName: group(16)
        # callId: group(13)
        self.mmp = r"^M\:" + r"(" + self.mp + r" " + r"\(([MIOSD])\)" + self.mp + r")$"

        self.ncmp = r"(" + "("+self.classPattern+")" + "\:" + "(" + "[0-9a-zA-Z\_\$\<\>]+" + "))"
        self.nmp = r"(" + self.ncmp + "\(" + self.argsPattern + "\)" + ")"
        self.nmmp = r"^M\:" + r"(" + self.nmp + r" " + r"\(([MIOSD])\)" + self.nmp + r")$" 