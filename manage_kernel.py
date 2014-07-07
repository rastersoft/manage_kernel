#!/usr/bin/env python3

# Copyright 2014 (C) Raster Software Vigo (Sergio Costas)

# This file is part of Manage Kernel Config
#
# Manage Kernel Config is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# Manage Kernel Config is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import sys
import os

class kfile_element:

    def __init__(self,parent,etype):

        self.marked = False
        self.etype = etype
        self.parent = parent
        self.symbol = None
        self.prompt = None
        self.help = False
        self.condition = None

        if (self.parent != None):
            self.parent.add_child(self)

        self.childs = []
        self.selections = []
        self.depends = []


    def get_parent(self):
        return self.parent


    def set_symbol(self,symbol):
        self.symbol = symbol.strip()


    def set_prompt(self,prompt):
        self.prompt = prompt.replace('"','').strip()


    def set_condition(self,condition):

        if (condition == None):
            return

        c = condition.strip()

        if (c.startswith("if ") or (c.startswith("if\t"))):
            c = c[2:].strip()
            self.condition = c


    def add_child(self,child):

        self.childs.append(child)


    def get_prompt(self,line):

        pos1 = line.find(" ")

        if (pos1 == -1):
            return

        line2 = line[pos1:].strip()
        if (len(line2) == 0):
            return

        if (line2[0] == '"'):
            pos = 0
            while(True):
                pos = line2.find('"',pos+1)
                if (pos == -1):
                    return
                # don't take into account '\"'
                if (line2[pos-1] != '\\'):
                    break

            line3 = line2[pos+1:]
            line2 = line2[1:pos]
        else:
            pos = line2.find(' ')
            if (pos == -1):
                line3 = None
            else:
                line3 = line2[pos+1:]
                line2 = line2[0:pos]

        self.prompt = line2
        self.set_condition(line3)

    def add_selection(self,line):

        pos1 = line.find(" ")

        if (pos1 == -1):
            return

        line2 = line[pos1:].strip()
        if (len(line2) == 0):
            return

        pos = line2.find(' ')
        if (pos == -1):
            element = [line2, None]
        else:
            c = line2[pos+1:].strip()
            if (c.startswith("if ")):
                c = c[2:].strip()
            element = [line2[0:pos], c]

        self.selections.append(element)

    def add_depend(self,line):

        line2 = line.strip()
        if (len(line2) == 0):
            return

        self.depends.append(line2)

    def add_attribute(self,attr):

        if (self.help):
            return

        attribute = attr.strip()
        if (attribute == "help") or (attribute == "---help---"):
            self.help = True

        if (attribute.startswith("prompt")):
            self.get_prompt(attribute[6:])
            return

        if (attribute.startswith("bool")):
            self.get_prompt(attribute[4:])
            return

        if (attribute.startswith("tristate")):
            self.get_prompt(attribute[8:])
            return

        if (attribute.startswith("string")):
            self.get_prompt(attribute[6:])
            return

        if (attribute.startswith("hex")):
            self.get_prompt(attribute[3:])
            return

        if (attribute.startswith("int")):
            self.get_prompt(attribute[3:])
            return

        if (attribute.startswith("select")):
            self.add_selection(attribute[6:])
            return

        if (attribute.startswith("depends on")):
            self.add_depend(attribute[10:])
            return


    def print_tree(self,pos):

        if (self.marked == False):
            return

        if (self.prompt != None):
            print(pos*"  ", end = "")
            print(self.prompt)

        for e in self.childs:
            if (self.etype == "if"):
                e.print_tree(pos)
            else:
                e.print_tree(pos+1)


    def print_data(self,pos):

        if (self.prompt != None):
            print(pos*"  ", end = "")
            print(self.prompt, end = "")
            if (self.symbol != None):
                print (" ["+str(self.symbol)+"]",end = "")
            if (self.condition != None):
                print (" ("+str(self.condition)+")",end = "")
            print()
            for l in self.selections:
                print((pos+1)*"  "+"*"+l[0], end = "")
                if (l[1]!= None):
                    print("("+l[1]+")", end = "")
                print("")
            for l in self.depends:
                print((pos+1)*"  "+"+"+l)

        for e in self.childs:
            if (self.etype == "if"):
                e.print_data(pos)
            else:
                e.print_data(pos+1)


    def mark_to_print(self):

        self.marked = True
        if (self.parent != None):
            self.parent.mark_to_print()


    def find_definition(self, definition):

        if (definition.startswith("CONFIG_")):
            definition = definition[7:]

        if (self.prompt != None):
            if (self.symbol == definition):
                self.mark_to_print()
                return self.prompt

            for l in self.selections:
                if (l == definition):
                    self.mark_to_print()
                    return self.prompt

        for e in self.childs:
            retval = e.find_definition(definition)
            if (retval != None):
                return retval

        return None


class process_kfile:

    def __init__(self,basepath,filename,arch,parent=None):

        self.parent = parent

        try:
            kfile = open(os.path.join(basepath,filename),"r")
        except:
            print("Error al abrir "+str(basepath)+" "+str(filename))
            return
        current_item = None
        append_line = ""

        for line_i in kfile:

            line = line_i.rstrip().replace("$SRCARCH",arch).replace("\t"," ")

            line = append_line + line

            if (len(line.strip())<1):
                continue

            if (line[-1] == '\\'):
                append_line = line[:-1]
                continue
            else:
                append_line = ""

            if (line.strip()[0]=='#'):
                continue

            if ((line[0] == ' ') or self.check_attribute(line)):
                if (current_item != None):
                    while (line.find("  ") != -1):
                        line = line.replace("  "," ")
                    current_item.add_attribute(line)
                continue

            if (line.startswith("config")):
                current_item = kfile_element(self.parent,"config")
                current_item.set_symbol(line[6:])
                continue

            if (line.startswith("menuconfig")):
                current_item = kfile_element(self.parent,"menuconfig")
                current_item.set_symbol(line[10:])
                self.parent = current_item
                continue

            if (line.startswith("choice")):
                current_item = kfile_element(self.parent,"choice")
                current_item.set_symbol(line[6:])
                self.parent = current_item
                continue

            if (line.startswith("endchoice")):
                self.parent = self.parent.get_parent()
                continue;

            if (line.startswith("comment")):
                current_item = kfile_element(self.parent,"comment")
                current_item.set_prompt(line[7:])
                continue

            if (line.startswith("menu")):
                current_item = kfile_element(self.parent,"menu")
                current_item.set_prompt(line[4:])
                self.parent = current_item
                continue

            if (line.startswith("endmenu")):
                self.parent = self.parent.get_parent()
                continue;

            if (line.startswith("mainmenu")):
                current_item = kfile_element(self.parent,"mainmenu")
                current_item.set_prompt(line[8:])
                self.parent = current_item
                continue

            if (line.startswith("source")):
                process_kfile(basepath,line[6:].replace('"','').strip(),arch,self.parent)
                continue

            if (line.startswith("if")):
                current_item = kfile_element(self.parent,"if")
                current_item.set_symbol(line[2:])
                self.parent = current_item
                continue

            if (line.startswith("endif")):
                self.parent = self.parent.get_parent()
                continue;

            print("Unknown element: "+str(line))

    def check_attribute(self,line):

        if (line.startswith("option")):
            return True

        if (line.startswith("default")):
            return True

        if (line.startswith("help")):
            return True

        if (line.startswith("---help---")):
            return True

        if (line.startswith("prompt")):
            return True

        if (line.startswith("bool")):
            return True

        if (line.startswith("boolean")):
            return True

        if (line.startswith("tristate")):
            return True

        if (line.startswith("string")):
            return True

        if (line.startswith("hex")):
            return True

        if (line.startswith("int")):
            return True

        if (line.startswith("depends on")):
            return True

        if (line.startswith("select")):
            return True



class kbuild_element:

    def __init__(self, parent, condition):

        self.parent = parent
        self.condition = condition
        self.childs = []
        self.calls = []


    def add_child(self,child):
        self.childs.append(child)


    def add_call(self,callname):
        self.calls.append(callname)

    def print_data(self,pos):

        for e in self.calls:
            print(pos*"  ", end = "")
            if (self.condition != None):
                print("("+self.condition+") ",end = "")
            print (e)

        for e in self.childs:
            e.print_data(pos+1)

    def find_symbol(self,symbol):

        for e in self.calls:
            if (e == symbol):
                return [ self.condition ]

        for e in self.childs:
            retval = e.find_symbol(symbol)
            if (retval == None):
                continue
            if (len(retval) != 0):
                if (self.condition != None):
                    return retval.insert(0,self.condition)
                else:
                    return retval

        return []

class kbuild:

    def __init__(self,path,arch,parent = None,dictionary = None):

        if (parent == None):
            first_time = True
            self.current_parent = kbuild_element(None,None)
        else:
            first_time = False
            self.current_parent = parent

        if (dictionary == None):
            self.dictionary = []
        else:
            self.dictionary = dictionary

        self.arch = arch
        self.path = path

        if (first_time):
            self.find_childs()
        else:
            self.process_file()


    def find_childs(self):

        elements = os.listdir(self.path)
        for l in elements:
            fullpath = os.path.join(self.path,l)
            if (os.path.isdir(fullpath)):
                kbuild(fullpath,arch,self.current_parent,self.dictionary)


    def process_file(self):

        try:
            kfile = open(os.path.join(self.path,"Kbuild"),"r")
        except:
            pass

        try:
            kfile = open(os.path.join(self.path,"Makefile"),"r")
        except:
            return

        append_line = ""
        for line in kfile:

            line = line.rstrip().replace("$SRCARCH",arch).replace("\t"," ")

            line = append_line + line

            if (len(line.strip())<1):
                continue

            if (line[-1] == '\\'):
                append_line = line[:-1]
                continue
            else:
                append_line = ""

            if (line.startswith("obj-y")):
                self.process_elements(self.current_parent,line[5:])
                continue
            if (line.startswith("obj-$")):
                pos = line.find(")")
                child = kbuild_element(self.current_parent,line[6:pos])
                self.current_parent.add_child(child)
                self.process_elements(child,line[pos+1:])


    def process_elements(self,parent,line):

        while (line.find("  ") != -1):
            line = line.replace("  "," ")
        line = line.replace("+=","").replace(":=","").replace("=","")
        newl = ""
        parenteses = 0
        for l in line:
            if l == "$":
                continue
            if l == '(':
                parenteses+=1
                continue
            if (l == ')') and (parenteses > 0):
                parenteses-=1
                continue
            if (parenteses == 0):
                newl+=l
        line = newl

        pos = line.find("#")
        if (pos != -1):
            line = line[0:pos]
        elements = line.strip().split(" ")

        for l in elements:
            full_path = os.path.join(self.path,l)
            if l.endswith("/"): # process a folder
                kbuild(full_path,self.arch,parent,self.dictionary)
                continue

            if (full_path.endswith(".o")):
                full_path = full_path[:-1]+"c"
            else:
                continue
            try:
                cfile = open(full_path,"r",encoding='latin1')
            except:
                continue


            for line in cfile:
                line = line.strip()

                if (line.startswith("#if")):
                    pos = line.find(" ")
                    if (pos != -1):
                        child = kbuild_element(parent,line[pos+1:])
                        parent.add_child(child)
                        parent = child
                        continue

                if (line.startswith("#endif")):
                    if (parent.parent != None):
                        parent = parent.parent

                pos = line.find("EXPORT_SYMBOL")
                if (-1 == pos):
                    continue
                pos2 = line.find("(",pos)
                if (pos2 == -1):
                    continue
                pos3 = line.find(")",pos2)
                if (pos3 == -1):
                    data = line[pos2+1:]
                else:
                    data = line[pos2+1:pos3]
                parent.add_call(data)

arch = sys.argv[1]

p = process_kfile(sys.argv[2],"Kconfig",arch,None)

#p.parent.print_data(0)

q = kbuild(sys.argv[2],arch)
#q.current_parent.print_data(0)

symbols = []

syscalls = open(sys.argv[3],"r",encoding='latin1')
for line in syscalls:
    elements = line.split(" ")
    if (len(elements) != 3):
        continue
    call = elements[2].strip()
    if (call.startswith("__ksymtab_") == False):
        continue
    symbol = call[10:]
    if (symbols.count(symbol) == 0):
        symbols.append(symbol)

definitions = []
for symbol in symbols:
    definition = q.current_parent.find_symbol(symbol)
    if (len(definition) != 0):
        if (len(definition)==1) and (definition[0] == None):
            continue
        for d in definition:
            if (definitions.count(d)==0):
                definitions.append(d)

for l in definitions:
    l = l.replace("defined","").strip()
    retval = p.parent.find_definition(l)
    if (retval == None):
        print("definition not found: "+l)

print()
p.parent.print_tree(0)
