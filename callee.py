#!/usr/bin/env python
#
# Copyright 2015 vonnyfly(lifeng1519@gmail.com)
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import commands
import sys
import string
import random
import os
import hashlib
from optparse import OptionParser

bt_threshold = 3
callgraph_threshold = 3
keep_dot_files = False
is_dtrace = False
output_format = "png"

def get_random_id():
    return ''.join(random.SystemRandom().choice(string.digits) for _ in range(3))

def write_file(basename, suffix, content):
    outfile = basename + suffix
    if os.path.exists(outfile):
        outfile = basename + "_" + get_random_id() + suffix
    with open(outfile, "w") as f:
        f.write(content)
    return outfile

def deduplicate(files):
    container = {}
    for f in files:
        hash = hashlib.sha256(open(f).read()).hexdigest()
        if hash in container:
            os.remove(f)
        else:
            container[hash] =f
    return container.values()

def draw_backtrace(funcs):
    if len(funcs) < bt_threshold:
        return None
    header = """digraph backtrace{
\tnode [shape="record"];
"""
    footer = "\n\t label=\"backtrace of %s\"}\n" %(funcs[0],)

    nodes = ""
    links = ""

    for i, func in enumerate(reversed(funcs)):
        nodes += "\t a%d[label=\"%s\"];\n" %(i, func)

    links = "\t" + ' -> '.join(["a%d" %(i,) for i in range(0, len(funcs))]) + ";\n"

    content = "%s%s%s%s" %(header, nodes, links, footer)
    return write_file(funcs[0], ".bt.dot", content)



class Tree:
    class Node:
        def __init__(self, data, id):
            self.data = data
            self.parent = None
            self.children = []
            self.head = self
            #self.id =get_random_id()
            #self.id = data
            self.id = id
            self.is_head = False
            self.first_child = None
            self.is_root = False

    def __init__(self, root = None):
        self.root = root;
        self.core_content = ""
        self.id = -1

    def create_node(self, data):
        self.id += 1
        return Tree.Node(data, "a" + str(self.id))

    def clean(self):
        self.root = None
        self.core_content = ""
        self.id = -1

    def travel_tree(self):
        if len(self.root.children) == 1 and self.root.data == self.root.children[0].data:
            self.root = self.root.children[0]
            self.root.parent = None
            self.root.is_root = True

        self._travel_tree(self.root)

    def _travel_tree(self, node):
        if node.first_child:
            if node.is_root:
                new_root = "\t %s [label=\"<%s>%s\", color=red];\n" %(node.id, node.data, node.data)
                self.core_content += new_root
                #print new_root
            new_node = "\t %s [label=\"%s\"];\n" %(node.first_child.id, " | ".join(["<" + i.data + ">" + i.data for i in node.children]))
            self.core_content += new_node
            #print new_node
            left = "\t %s:%s" % (node.head.id, node.data)
            right = "%s:%s" % (node.first_child.id, node.first_child.data)
            style = "[dir=both, arrowtail=dot];\n"
            new_link = "%s -> %s%s" %(left, right, style)
            self.core_content += new_link
            #print new_link

        for child in node.children:
            self._travel_tree(child)


def draw_callgraph(funcs):
    if len(funcs) < 2 * callgraph_threshold:
        return None
    header = """digraph callee {
\tsize="30,40";
\tcenter=true;
\tmargin=0.1;
\tnodesep=2;
\tranksep=0.5;
\trankdir=LR;
\tedge[arrowsize=1.0, arrowhead=vee];
\tnode[shape = record,fontsize=20, width=1, height=1, fixedsize=false];
"""

    is_first = True
    root = None
    index = None
    tree = Tree()
    for label in funcs:
        sign = label[0:2]
        func = label[2:]
        if sign == "->":
            new_node = tree.create_node(func)
            if is_first:
                root = new_node
                index = new_node
                is_first = False
                index.is_root = True
            else:
                new_node.parent = index
                if len(index.children) == 0:
                    new_node.is_first = True
                    index.first_child = new_node
                else:
                    new_node.head = index.first_child
                index.children.append(new_node)
                #print "%s -> %s\n" %(index.data, new_node.data)
                index = new_node
        elif sign == "<-":
            if not index:
                print "[-]except: ", label
                return None
            #print "from return : %s" %(index.data, )
            index = index.parent
            if not index:
                break


    #print "Begin travel:"
    tree.root = root
    tree.travel_tree()
    footer = "\n\t label=\"callgraph of %s\";\n}\n" %(tree.root.data,)
    content = "%s%s%s" % (header, tree.core_content, footer)
    outfile = write_file(tree.root.data, ".cg.dot", content)
    tree.clean()
    return outfile

def generate_pngs(dotfiles):
    dotfiles = deduplicate(dotfiles)
    for f in dotfiles:
        cmd = 'filename=%s; dot $filename -T%s >${filename%%.*}.%s' % (f, output_format, output_format)
        commands.getstatusoutput(cmd)
        if not keep_dot_files:
            os.remove(f)
        print "Generated %s.%s" % (f[0:-4], output_format)

def main():
    global callgraph_threshold, bt_threshold, keep_dot_files, is_dtrace
    global output_format
    parser = OptionParser(usage='%prog [options] log_file', 
            description='Generate pngs from Dtrace or Systemtap log')
    parser.add_option('-k', '--keep-dot', action = 'store_true',
            help = 'keep dot file, default delect it')
    parser.add_option('-o', '--output-format', type = "string",
            help = 'output file format, could be ["png", "jpg", "svg"], '
            ' default is png')
    parser.add_option('-d', '--is_dtrace_log', action = 'store_true',
            help = 'default is systemtap log, -d stand for dtrace log')
    parser.add_option('-c', '--threshold_cg', type = "int",
            help = 'only generate call graph when the call link'
            ' extend to threshold_cg')
    parser.add_option('-b', '--threshold_bt', type = "int",
            help = 'only generate backtrace graph when the call link'
            ' extend to threshold_bt')

    (options, args) = parser.parse_args()

    if options.keep_dot:
        keep_dot_files = True
    if options.is_dtrace_log:
        is_dtrace = True
    if options.output_format and options.output_format in ["png", "jpg", "svg"]:
        output_format = options.output_format
    if options.threshold_cg and options.threshold_cg > 0:
        callgraph_threshold = options.threshold_cg
    if options.threshold_bt and options.threshold_bt > 0:
        bt_threshold = options.threshold_bt

    if len(args) != 1:
        parser.error("incorrect number of arguments")
    try:
        with open(args[0]) as f:
            content = f.readlines()
    except:
        sys.exit("No file!")

    bt_list = []
    callgraph_list = []
    dotfiles = []
    for l in content:
        #print l
        if '+' not in l:
            outfile = draw_backtrace(bt_list)
            if outfile:
                dotfiles.append(outfile)
            bt_list = []

        if '->' not in l and '<-' not in l and '|' not in l:
            outfile = draw_callgraph(callgraph_list);
            if outfile:
                dotfiles.append(outfile)
            callgraph_list = []

        if '+' in l:
            if is_dtrace:
                func_name = l.split('+')[0].strip().split('`')[-1]
            else:
                func_name = l.split(':')[1].split('+')[0].strip()
            bt_list.append(func_name)

        if '|' in l and is_dtrace:
            if 'entry' in l:
                func_name = "->" + l.strip(' \n\t').split('|')[-1].split(':')[0].strip(' \n\t')
            elif ':return' in l:
                continue
            else:
                func_name = l.strip(' \n\t').split('|')[-1].strip(' \n\t')
            callgraph_list.append(func_name)

        if '->' in l or '<-' in l:
            if is_dtrace:
                func_name = ''.join(l.strip(' \n\t').split(' ')[-2:])
            else:
                func_name = l.split(':')[-1].strip().split(' ')[0]
            callgraph_list.append(func_name)
    outfile = draw_backtrace(bt_list)
    if outfile:
        dotfiles.append(outfile)
    outfile = draw_callgraph(callgraph_list)
    if outfile:
        dotfiles.append(outfile)

    generate_pngs(dotfiles)


if __name__ == "__main__":
    main()
