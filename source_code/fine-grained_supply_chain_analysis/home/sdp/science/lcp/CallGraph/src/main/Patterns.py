#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import re

class Patterns:
    def __init__(self):
        self._class = r"([0-9a-zA-Z\_\$]+\.)*[0-9a-zA-Z\_\$]+"
        self._2class = r"^C\:(([0-9a-zA-Z\_\$]+\.)*[0-9a-zA-Z\_\$]+) (([0-9a-zA-Z\_\$]+\.)*[0-9a-zA-Z\_\$]+)$"
        self.class_method_name = r"(([0-9a-zA-Z\_\$]+\.)*[0-9a-zA-Z\_\$]+\:([0-9a-zA-Z\_\$]+))"

        self.arg = r"([0-9a-zA-Z\_\$]+\.)*[0-9a-zA-Z\_\$]+"
        self.argnames = r"((([0-9a-zA-Z\_\$]+\.)*[0-9a-zA-Z\_\$]+)\,)*(([0-9a-zA-Z\_\$]+\.)*[0-9a-zA-Z\_\$]*)"

        self.alpthaPattern = r"[0-9a-zA-Z\_\$]"
        self.noOroneToken = self.alpthaPattern + "*"
        self.oneToken = self.alpthaPattern + "+"

        self.classPattern = r"(" + self.oneToken + "\.)*" + self.oneToken 

        self.class_class_pattern = r"^C\:" + "(" + self.classPattern + ")" + " " + "(" + self.classPattern + ")" + "$" 

        self.class_method_pattern = r"(" + self.classPattern + "\:" + "(" + self.oneToken + "))" 
 
        self.argsPattern = r"(" + r"((" + self.classPattern + r")\,)*" + r"(" +  r"(" + self.oneToken + "\.)*" + self.noOroneToken + r"))"  
        self.methodPattern = r"(" + self.class_method_pattern + "\(" + self.argsPattern + "\)" + ")"

        self.method_method_pattern = r"^M\:" + r"(" + self.methodPattern + r" " + r"\(([MIOSD])\)" + self.methodPattern + r")$" 
        self.domain = r"^([0-9a-zA-Z\_\$]+)\..*"
        
        self.cmp =  r"(" + "("+self.classPattern+")" + "\:" + "(" + self.oneToken + "))"
        self.mp = r"(" + self.cmp + "\(" + self.argsPattern + "\)" + ")"

        self.mmp = r"^M\:" + r"(" + self.mp + r" " + r"\(([MIOSD])\)" + self.mp + r")$"

        self.ncmp = r"(" + "("+self.classPattern+")" + "\:" + "(" + "[0-9a-zA-Z\_\$\<\>]+" + "))"
        self.nmp = r"(" + self.ncmp + "\(" + self.argsPattern + "\)" + ")"
        self.nmmp = r"^M\:" + r"(" + self.nmp + r" " + r"\(([MIOSD])\)" + self.nmp + r")$" 