#!/usr/bin/env python3
from copy import deepcopy
import json
from pprint import pprint, pformat
import re
import os
import shlex
import subprocess
import sys

from ..gpkgs import shell_helpers as shell

#  wmic process get Caption,ParentProcessId,ProcessId
class Node():
    # def __init__(self, dy=None, parent=None, netstat_pids=None):
    def __init__(self, dy=None, parent=None):
        self.parent=parent
        self.is_leaf=True
        self.nodes=[]
        self.dy=dy
        self.parents=[]
        # self.alldescendants=[]
        # self.tree={ self: dict() }

        # self.dy["netstat"] = dict()
        # if self.dy["pid"] in netstat_pids:
            # self.dy["netstat"]=netstat_pids[self.dy["pid"]]

        if self.parent is None:
            self.root=self
            self.is_root=True
            self.level=1
            self.count=1
        else:
            self.root=self.parent.root
            self.root.count+=1
            self.is_root=False
            self.parent.is_leaf=False
            self.level=self.parent.level+1
            self.parent.nodes.append(self)
            if self.parent.parents:
                self.parents.extend(self.parent.parents)

            self.parents.append(parent)
            # self.parent.tree[self.parent].update(self.tree)

            # tmp_parent=self.parent
            # while True:
            #     tmp_parent.alldescendants.append(self)
            #     if tmp_parent.parent is None:
            #         break
            #     else:
            #         tmp_parent=tmp_parent.parent

class Processes():
    def __init__(self, debug=False):
        self.debug=debug

    def init(self):
        self.procs_by_name=dict()
        self.procs_by_pid=dict()
        # self.netstat_pids=dict()
        # self.set_tcp_connections()
        self.set_processes()
        # sys.exit()

    # def set_tcp_connections(self):
    #     for line in shell.cmd_get_value("netstat -aon").splitlines():
    #         # Proto  Local Address          Foreign Address        State           PID
    #         #  TCP    0.0.0.0:22             0.0.0.0:0              LISTENING       4664
    #         #   UDP    0.0.0.0:123            *:*                                    1484
    #         # reg_line=re.match(r"^\s+TCP\s+127.0.0.1:([0-9]+)\s+[0-9]+.[0-9]+.[0-9]+.[0-9]+:([0-9]+)\s+([A-Z]+)\s+([0-9]+)$", line)
    #         line=line.strip()
    #         if line:
    #             fields=re.sub(r"\s+", r" ", line).split()
    #             if len(fields) > 3:
    #                 if fields[0] != "Proto":
    #                     if len(fields) == 5:
    #                         proto, ip_port_local, ip_port_foreign, state, pid = fields
    #                     elif len(fields) == 4:
    #                         proto, ip_port_local, ip_port_foreign, pid = fields
    #                         state=None

    #                     reg_ip_port_local=re.match(r"^(.+):([0-9]+)$", ip_port_local)
    #                     ip_local=reg_ip_port_local.group(1)
    #                     port_local=reg_ip_port_local.group(2)
    #                     reg_ip_port_foreign=re.match(r"^(.+):(.+)$", ip_port_foreign)
    #                     ip_foreign=reg_ip_port_foreign.group(1)
    #                     port_foreign=reg_ip_port_foreign.group(2)

    #                     if not pid in self.netstat_pids:
    #                         self.netstat_pids[pid]=[]

    #                     self.netstat_pids[pid].append(dict(
    #                         ip_foreign=ip_foreign,
    #                         ip_local=ip_local,
    #                         ip_port_foreign=ip_port_foreign,
    #                         ip_port_local=ip_port_local,
    #                         pid=pid,
    #                         port_foreign=port_foreign,
    #                         port_local=port_local,
    #                         proto=proto,
    #                         state=state,
    #                     ))


    def set_processes(self):   
        header=True
        for line in shell.cmd_get_value("powershell.exe wmic process get Caption,ParentProcessId,ProcessId").splitlines():
            line=line.strip()
            if line:
                if header is True:
                    header=False
                    continue
                reg_line=re.match(r"^(.+?)\s+([0-9]+?)\s+([0-9]+?)$", line)
                name=reg_line.group(1)
                ppid=reg_line.group(2)
                pid=reg_line.group(3)
                proc=dict(
                    name=name,
                    ppid=ppid,
                    pid=pid,
                )
                self.procs_by_pid[pid]=proc

        while True:
            unknown=False
            all_checked=True
            for pid, proc in self.procs_by_pid.items():
                if not "node" in proc:
                    all_checked=False
                    if proc["ppid"] in self.procs_by_pid:
                        pproc=self.procs_by_pid[proc["ppid"]]
                        if not "node" in pproc:
                            if proc["pid"] == proc["ppid"]:
                                proc["node"]=Node(dy=proc)
                                # proc["node"]=Node(dy=proc, netstat_pids=self.netstat_pids)
                        else:
                            proc["node"]=Node(dy=proc, parent=pproc["node"])
                            # proc["node"]=Node(dy=proc, parent=pproc["node"], netstat_pids=self.netstat_pids)
                    else:
                        dy=dict(
                            name="unknown",
                            pid=proc["ppid"],
                            ppid=proc["ppid"],
                        )
                        self.procs_by_pid[proc["ppid"]]=dy;
                        self.procs_by_pid[proc["ppid"]]["node"]=Node(dy=dy)
                        # self.procs_by_pid[proc["ppid"]]["node"]=Node(dy=dy, netstat_pids=self.netstat_pids)
                        pproc=self.procs_by_pid[proc["ppid"]]
                        proc["node"]=Node(parent=pproc["node"], dy=proc)
                        # proc["node"]=Node(parent=pproc["node"], dy=proc, netstat_pids=self.netstat_pids)
                        unknown=True
                        break

            if unknown is False:
                if all_checked is True:
                    break
                
                

        for pid, proc in self.procs_by_pid.items():
            if not proc["name"] in self.procs_by_name:
                self.procs_by_name[proc["name"]]=[]
            self.procs_by_name[proc["name"]].append(proc)

        # browsers=self.from_name("iexplore.exe")
        # pprint(browsers)
            
        # output=self.report(
        #     "11260",
        #     # pid=7932,
        #     # pid=11260,
        #     # from_root=True,
        #     # only_children=True,
        #     # depth=1,
        #     separator=None,
        #     show=True,
        #     opts=[
        #         # "indent", 
        #         "pid"
        #     ],
        # )

        # pprint(self.procs_by_pid["11260"]["node"].tree)

        # work on how to display a tree.

                # ppids=
                # del procs[pid]
                # print(proc["name"])
                # generate_tree(proc, procs)
        # pprint(proc_pids)
        # processes=dict(
        #     by_name=proc_names,
        #     by_pid=proc_pids,
        # )


    def from_pid(self, pid):
        pid=str(pid)
        if pid in self.procs_by_pid:
            return self.procs_by_pid[pid]
        return None

    def from_name(self, name):
        if name in self.procs_by_name:
            return self.procs_by_name[name]
        return []

    def kill(self, pid_name):
        try:
            pid_name=int(pid_name)
            cmd="taskkill /PID {} /F".format(pid_name)
        except:
            cmd="taskkill /F /IM {}".format(pid_name)
        
        if self.debug is True:
            print(cmd)

        proc=subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        if self.debug is True:
            if stdout:
                print(stdout.decode())
            if stderr:
                print(stderr.decode())

    def report(self,
        pid,                    # user
        depth=None,             # user
        depth_node=None,
        indent=True,            # user
        infos=[],
        from_root=False,        # user
        only_children=False,    # user
        opts=["all"],           # user
        pnode=None,
        ref_node=None,
        separator=list(),       # user
        show=False,             # user
    ):
        opts_choices=[
            "indent",
            "pid",
            "ppid",
            "name",
            "node",
            # "netstat",
        ]

        if "all" in opts:
            opts=opts_choices

        if depth_node is None:
            try:
                pid=int(pid)
            except:
                print("pid '{}' is not {}".format(pid, str))
                sys.exit(1)

            pid=str(pid)
            this_node=self.procs_by_pid[pid]["node"]

            if ref_node is None:
                ref_node=this_node
            pnode=this_node
            depth_node=this_node

            if from_root is True:
                if pnode.is_root is False:
                    return self.report(
                        this_node.root.dy["pid"],
                        depth=depth,
                        depth_node=None,
                        from_root=from_root,
                        only_children=only_children,
                        indent=indent,
                        infos=infos,
                        opts=opts,
                        pnode=pnode,
                        ref_node=ref_node,
                        separator=separator,
                        show=show,
                    )


        if separator is None:
            if len(opts) > 1:
                separator=list()

        if only_children is True and depth_node == pnode:
            if depth is not None:
                depth+=1
        else:
            values=[]
            show_fields=""

            children_level=1
            if only_children is True:
                children_level=0
            relative_depth=(pnode.level - depth_node.level) + children_level
            prefix=(relative_depth-1)*"  "
            for opt in opts:
                if opt in opts_choices:
                    value=None
                    field=None
                    if opt == "indent":
                        value=prefix
                    else:
                        value=pnode.dy[opt]

                    values.append(value)
                    if show is True:
                        space=" "
                        if show_fields == "":
                            space=""
                            if indent is True:
                                space+=prefix
                        if opt == "pid":
                            field="{:<6}".format(value)
                        # elif opt == "netstat":
                            # pass # print after
                        else:
                            field=value
                        show_fields+=space+str(field)
                else:
                    print("For report opts '{}' not found in {}".format(opt, opts_choices))
                    sys.exit(1)

            if values:
                if isinstance(separator, list):
                    pass
                elif isinstance(separator, dict):
                    dy=dict()
                    for v, value in enumerate(values):
                        dy[opts[v]]=value
                    values=dy
                elif separator is None:
                    values=values[0]

                infos.append(values)

            if show is True:
                if show_fields:
                    print(show_fields)
                    # if "netstat" in opts:
                        # print(''.join([ prefix+ "  " + l for l in pformat(pnode.dy["netstat"]).splitlines(True)]))

        recurse=False
        if depth is None:
            recurse=True
        else:
            if relative_depth < depth:
                recurse=True

        if recurse is True:
            for node in pnode.nodes:
                recurse_node=False
                if from_root is True:
                    # print(ref_node)
                    if node.level < ref_node.level:
                        if node in ref_node.parents:
                            recurse_node=True
                    elif node.level == ref_node.level:
                        if node == ref_node:
                            recurse_node=True
                    else:
                        recurse_node=True
                else:
                    recurse_node=True

                if recurse_node is True:
                    self.report(
                        pid,
                        depth=depth,
                        depth_node=depth_node,
                        indent=indent,
                        infos=infos,
                        from_root=from_root,
                        only_children=only_children,
                        opts=opts,
                        pnode=node,
                        ref_node=ref_node,
                        separator=separator,
                        show=show, 
                    )

        if pnode == depth_node:
            return infos
        # print(pid)

# def generate_tree(pproc, procs, tree=dict()):
#     # if not tree:
#     tree[pproc["pid"]]=deepcopy(pproc)
#     tree[pproc["pid"]]["procs"]=dict()

#     for node in pproc["node"].nodes:
#         pid, proc = node.items()
#         # tree[proc["pid"]]["nodes"][node["pid"]]=deepcopy(node)

#         del procs[pid]
#         # return generate_tree(deepcopy(proc), procs, tree)

#     # return tree
# # def 
