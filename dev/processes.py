#!/usr/bin/env python3
from copy import deepcopy
from enum import Enum
from pprint import pprint, pformat
import json
import os
import psutil
from psutil import Process

class ReportOption(str, Enum):
    INDENT = 1
    PID = 2
    PPID = 3
    NAME = 4
    PROC = 5
    TCPCONNS = 6

class TcpConn():
    # sconn(fd=-1, family=<AddressFamily.AF_INET6: 10>, type=<SocketKind.SOCK_STREAM: 1>, laddr=addr(ip='::1', port=25), raddr=(), status='LISTEN', pid=None)
    def __init__(self,
        ip_local:str,
        port_local:int,
        ip_remote:str|None,
        port_remote:int|None,
        pid:int|None,
        status:str,
    ) -> None:
        self.ip_local=ip_local
        self.port_local=port_local
        self.ip_remote=ip_remote
        self.port_remote=port_remote
        self.pid=pid
        self.status=status

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)

class Proc():
    def __init__(self,
        name:str,
        pid:int,
        ppid:int,
        tcp_conns:list[TcpConn],
        psproc:Process,
    ) -> None:
        self.name=name
        self.pid=pid
        self.ppid=ppid
        self.tcp_conns=tcp_conns
        self._obj=deepcopy(self)
        self.parent:Proc|None=None
        self.children:list[Proc]=[]
        self.psproc=psproc

    def to_json(self):
        return json.dumps(self._obj, default=lambda o: o.__dict__)

class ProcInfo():
    def __init__(self,
        proc:Proc,
        level:int,
        parents:list[Proc],
        root:Proc|None,
    )-> None:
        self.proc=proc
        self.level=level
        self.parents=parents
        self.root=root

def get_tcp_connections(conn_kind:str="inet", debug:bool=False) -> list[TcpConn]:
    tcp_conns:list[TcpConn]=[]
    for conn in psutil.net_connections(kind=conn_kind):
        ip_local:str=conn.laddr.ip #type:ignore
        port_local:int=conn.laddr.port #type:ignore
        ip_remote:str|None=None
        try:
            ip_remote=conn.raddr.ip #type:ignore
        except AttributeError:
            pass
        
        port_remote:int|None=None
        try:
            port_remote=conn.addr.port #type:ignore
        except AttributeError:
            pass

        pid:int|None=conn.pid
        status:str=conn.status
        tcp_conn=TcpConn(
            ip_local=ip_local,
            port_local=port_local,
            ip_remote=ip_remote,
            port_remote=port_remote,
            pid=pid,
            status=status,
        )
        tcp_conns.append(tcp_conn)

    if debug is True:
        print(f"### connections '{conn_kind}':")
        for t in tcp_conns:
            print(t.to_json())

    return tcp_conns

class Processes():
    def __init__(self, debug=False):
        self.debug=debug

    def init(self) -> None:
        self.tcp_connections=get_tcp_connections()
        self.processes=self.get_processes()

    def get_processes(self) -> list[Proc]:
        procs:list[Proc]=[]
        dy_procs:dict[int,Proc]=dict()
        to_set:dict[int, list[Proc]]=dict()
        for proc in psutil.process_iter():
            tcp_conns:list[TcpConn]=[t for t in self.tcp_connections if t.pid == proc.pid]
            pid=proc.pid
            ppid=proc.ppid()
            tmp_proc=Proc(
                name=proc.name(),
                pid=pid,
                ppid=ppid,
                psproc=proc,
                tcp_conns=tcp_conns,
            )
            dy_procs[pid]=tmp_proc

            if ppid == 0:
                if ppid in dy_procs:
                    tmp_proc.parent=dy_procs[ppid]
                    tmp_proc.parent.children.append(tmp_proc)
                else:
                    tmp_proc.parent=None
            else:
                if pid == ppid:
                    print(proc)
                    raise NotImplementedError("PID == PPID")
                if ppid in dy_procs:
                    tmp_proc.parent=dy_procs[ppid]
                    tmp_proc.parent.children.append(tmp_proc)
                else:
                    if ppid not in to_set:
                        to_set[ppid]=[]
                    to_set[ppid].append(tmp_proc)

            if pid in to_set:
                for p in to_set[pid]:
                    p.parent=tmp_proc
                    tmp_proc.children.append(p)
                del to_set[pid]

            procs.append(tmp_proc)

        if len(to_set) > 0:
            pprint(to_set)
            raise NotImplementedError("to_set is not empty")

        return procs
        
    def from_pid(self, pid:int) -> Proc | None:
        for proc in self.processes:
            if proc.pid == pid:
                return proc
        return None

    def from_name(self, name:str) -> list[Proc]:
        procs:list[Proc]=[]
        for proc in self.processes:
            if proc.name == name:
                procs.append(proc)
        return procs

    def kill(self, pid:int):
        proc=self.from_pid(pid)
        if proc is not None:
            proc.psproc.kill()

    def get_proc_info(self, proc:Proc):
        level=1
        parents:list[Proc]=[]
        tmp_proc=proc
        root:Proc|None=None
        while True:
            if tmp_proc.parent is None:
                break
            else:
                level+=1
                tmp_proc=tmp_proc.parent
                parents.insert(0, tmp_proc)
                root=tmp_proc
        return ProcInfo(proc=proc,level=level, parents=parents, root=root)

    def report(self,
        pid:int,                            # user
        indent:bool=True,                   # user
        from_root:bool=False,               # user
        opts:list[ReportOption]|None=None,  # user if None then all options are set
        show:bool=False,                    # user
        _infos:list[list[str|int|Process|list[TcpConn]]]|None=None,
        _pproc:Proc|None=None,
        _ref:ProcInfo|None=None,
        _to_return:bool=True,
    ):
        if _infos is None:
            _infos=[]

        if opts is None:
            opts=[
                ReportOption.INDENT,
                ReportOption.PID,
                ReportOption.PPID,
                ReportOption.NAME,
                ReportOption.PROC,
                ReportOption.TCPCONNS,
            ]

        if _pproc is None:
            _pproc=self.from_pid(pid)
            if _pproc is None:
                raise Exception(f"Unknown PID {pid}")

        pproc_info=self.get_proc_info(_pproc)
        if _ref is None:
            _ref=pproc_info

        if from_root is True:
            if pproc_info.root is not None:
                return self.report(
                    pid=pproc_info.root.pid,
                    from_root=False,
                    indent=indent,
                    opts=opts,
                    show=show,
                    _infos=_infos,
                    _pproc=pproc_info.root,
                    _ref=_ref,
                    _to_return=True,
                )
  
        values:list[str|int|Process|list[TcpConn]]=[]
        show_fields=""

        prefix=(pproc_info.level-1)*"  "
        for opt in opts:
            value=None
            field=None
            if opt == ReportOption.INDENT:
                value=prefix
            elif opt == ReportOption.NAME:
                value=_pproc.name
            elif opt == ReportOption.PID:
                value=_pproc.pid
            elif opt == ReportOption.PPID:
                value=_pproc.ppid
            elif opt == ReportOption.PROC:
                value=_pproc.psproc
            elif opt == ReportOption.TCPCONNS:
                value=_pproc.tcp_conns
            else:
                raise Exception(f"ReportOption unknown {opt}")

            values.append(value)
            if show is True:
                space=" "
                if show_fields == "":
                    space=""
                    if indent is True:
                        space+=prefix
                if opt == ReportOption.PID:
                    field="{:<6}".format(value)
                elif opt == ReportOption.PROC:
                    pass # print after
                elif opt == ReportOption.TCPCONNS:
                    pass # print after
                else:
                    field=value
                show_fields+=space+str(field)

        _infos.append(values)

        if show is True:
            if show_fields:
                print(show_fields)
                if ReportOption.PROC in opts:
                    print(''.join([ prefix+ "  " + l for l in pformat(_pproc.psproc).splitlines(True)]))
                if ReportOption.TCPCONNS in opts:
                    print(''.join([ prefix+ "  " + l for l in pformat(_pproc.tcp_conns).splitlines(True)]))

        for tmp_proc in _pproc.children:
            recurse=False
            tmp_proc_info=self.get_proc_info(tmp_proc)
            if tmp_proc_info.level < _ref.level:
                if tmp_proc in _ref.parents:
                    recurse=True
            elif tmp_proc_info.level == _ref.level:
                if tmp_proc == _ref.proc:
                    recurse=True
            else:
                recurse=True

            if recurse is True:
                self.report(
                    pid=pid,
                    indent=indent,
                    from_root=False,
                    opts=opts,
                    show=show, 
                    _infos=_infos,
                    _pproc=tmp_proc,
                    _ref=_ref,
                    _to_return=False,
                )

        if _to_return is True:
            return _infos
