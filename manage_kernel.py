#!/usr/bin/env python3

import sys
import os

class element:
    
    def __init__(self,name,parent,etype):
        
        self.name = name
        self.parent = parent
        self.description = None
        self.dependencies = []
        self.childs = []
        self.selections = []
        self.etype = etype
    
    def add_dependency(self,dep):
        
        self.dependencies.append(dep)
    
    def add_selection(self,selection):

        self.selections.append(selection)
    
    def add_child(self,child):
        
        self.childs.append(child)
        
    def set_description(self,description):
        
        self.description = description
    
    def get_parent(self):
        
        return self.parent
    
    def set_name(self,name):

        self.name = name
    
    def print_data(self,pos):
        
        if (self.description != None):
            print(pos*"  ", end="")
            print(self.description, end="")
            if (self.name != None):
                print (" ("+str(self.name)+")",end ="")
            print()
        for e in self.childs:
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
        help_mode = False
        for line_i in kfile:
            line = line_i.rstrip().replace("$SRCARCH",arch)
            if (len(line.strip())<1):
                continue
            line = append_line + line
            if (line[-1] == '\\'):
                append_line = line
                continue
            append_line = ""
            if ((line[0] != ' ') and (line[0] != '\t')):
                help_mode = False
            if (help_mode):
                continue
            line = line.strip()
            if (line[0]=='#'):
                continue

            pos = line.find(" ")
            pos2 = line.find("\t")
            if (pos != -1) and (pos2 != -1):
                if (pos2 < pos):
                    pos = pos2
                pos2 = -1
            if (pos == -1):
                pos = pos2
            if (pos != -1):
                data = line[:pos]
                if (data == "depends"):
                    pos+=3
                    data = "depends on"
                params = line[pos+1:].replace('"','')
            else:
                params = ""
                data = line

            if ((data == 'option') or (data == 'default')):
                continue

            if ((data == "help") or (data == "---help---")):
                help_mode = True
                continue

            if (data == "source"):
                process_kfile(basepath,params,arch,self.parent)
                continue

            if (data == "config"):
                current_item = element(params,self.parent,"config")
                if (self.parent != None):
                    self.parent.add_child(current_item)
                continue

            if (data == "menuconfig"):
                current_item = element(params,self.parent,"menuconfig")
                if (self.parent != None):
                    self.parent.add_child(current_item)
                self.parent = current_item
                continue


            if (data == "choice"):
                current_item = element (params,self.parent,"choice")
                if (self.parent != None):
                    self.parent.add_child(current_item)
                self.parent = current_item
                continue

            if (data == "comment"):
                current_item = element(None,self.parent,"comment")
                current_item.set_description(params)
                if (self.parent != None):
                    self.parent.add_child(current_item)
                continue

            if (data == "menu") or (data == "mainmenu"):
                current_item = element (None,self.parent,"menu")
                current_item.set_description(params)
                if (self.parent != None):
                    self.parent.add_child(current_item)
                self.parent = current_item
                continue

            if (data == 'prompt'):
                current_item.set_description(params)
                continue
            
            if (data == 'bool') or (data == 'boolean') or (data == 'tristate') or (data == 'string') or (data == 'hex') or (data == 'int'):
                if (params != "") and (current_item != None):
                    current_item.set_description(params)
                continue
            
            if (data=='depends on'):
                if (current_item != None):
                    current_item.add_dependency(params)
                continue
            
            if (data=='select'):
                if (current_item!=None):
                    current_item.add_selection(params)
                continue

            if (data == 'endmenu') or (data == 'endchoice') :
                self.parent = self.parent.get_parent()
                continue;

            #print("Unknown element: "+str(data))


arch = sys.argv[1]

p = process_kfile(sys.argv[2],"Kconfig",arch,None)

p.parent.print_data(0)