#!/usr/bin/env python3

import sys
import os

class element:

    def __init__(self,parent,etype):

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
                current_item = element(self.parent,"config")
                current_item.set_symbol(line[6:])
                continue

            if (line.startswith("menuconfig")):
                current_item = element(self.parent,"menuconfig")
                current_item.set_symbol(line[10:])
                self.parent = current_item
                continue

            if (line.startswith("choice")):
                current_item = element(self.parent,"choice")
                current_item.set_symbol(line[6:])
                self.parent = current_item
                continue

            if (line.startswith("endchoice")):
                self.parent = self.parent.get_parent()
                continue;

            if (line.startswith("comment")):
                current_item = element(self.parent,"comment")
                current_item.set_prompt(line[7:])
                continue

            if (line.startswith("menu")):
                current_item = element(self.parent,"menu")
                current_item.set_prompt(line[4:])
                self.parent = current_item
                continue

            if (line.startswith("endmenu")):
                self.parent = self.parent.get_parent()
                continue;

            if (line.startswith("mainmenu")):
                current_item = element(self.parent,"mainmenu")
                current_item.set_prompt(line[8:])
                self.parent = current_item
                continue

            if (line.startswith("source")):
                process_kfile(basepath,line[6:].replace('"','').strip(),arch,self.parent)
                continue

            if (line.startswith("if")):
                current_item = element(self.parent,"if")
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


arch = sys.argv[1]

p = process_kfile(sys.argv[2],"Kconfig",arch,None)

p.parent.print_data(0)