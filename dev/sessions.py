#!/usr/bin/env python3
from requests.models import Response
from pprint import pprint
import json
import os
import requests
import shlex
import subprocess
import sys

from .objs import BrowserData, Session, NetstatObj
from .processes import Processes, get_tcp_connections

from ..gpkgs import shell_helpers as shell
from ..gpkgs import message as msg

def close_sessions(
    grid_url:str,
    grid_url_pid:int|None,
    debug:bool=False,
):
    if debug == True:
        print("Closing All Sessions")

    for session in get_sessions(
        debug=debug,
        grid_url=grid_url,
        grid_url_pid=grid_url_pid,
    ):
        session_close(
            grid_url=grid_url,
            session_id=session.id,
        )

def get_session(
    debug:bool,
    browser_data:BrowserData,
    grid_url:str,
    grid_url_pid:int|None,
) -> Session|None:
    sessions=get_sessions(
        debug=debug,
        grid_url=grid_url,
        grid_url_pid=grid_url_pid,
    )

    for session in sessions:
        browser_name=session.capabilities["browserName"]
        if browser_name == browser_data.name:
            return session
    return None

def session_close(
    grid_url:str,
    session_id:str,
):
    print("Closing the session")
    url=f"{grid_url}/session/{session_id}"
    res:Response=requests.delete(url)
    res.raise_for_status()
    
def get_browser_pid(
    browser_proc_name:str,
    driver_proc_name:str,
    grid_pid:int,
    processes_obj:Processes,
):
    driver_pid:int|None=None
    browser_pid:int|None=None
    grid_proc=processes_obj.from_pid(pid=grid_pid)
    if grid_proc is not None:
        for proc in grid_proc.children:
            if proc.name == driver_proc_name:
                if driver_pid is None:
                    driver_pid=proc.pid
                    for browser_proc in proc.children:
                        if browser_proc.name == browser_proc_name:
                            if browser_pid is None:
                                browser_pid=browser_proc.pid
                            else:
                                msg.error(f"There are at least two browsers '{browser_proc_name}' with driver '{driver_proc_name}' please --reset selenium")
                                sys.exit(1)
                else:
                    msg.error(f"There are at least two drivers '{driver_proc_name}' please --reset selenium")
                    sys.exit(1)

    if browser_pid is None:
        msg.error(f"No pid found for browser '{browser_proc_name}'")
        sys.exit(1)

    return browser_pid

def get_netstats(
    debug:bool,
    processes_obj:Processes,
):
    netstats:dict[str, list[NetstatObj]]=dict()
    tcp_conns=get_tcp_connections(conn_kind="tcp")
    for tcp_conn in tcp_conns:
        if tcp_conn.pid is not None:
            proc=processes_obj.from_pid(tcp_conn.pid)
            if proc is not None:
                if proc.name not in netstats:
                    netstats[proc.name]=[]
                netstats[proc.name].append(NetstatObj(
                    port=tcp_conn.port_local,
                    pid=tcp_conn.pid,
                    proc_name=proc.name,
                ))
                
    if debug is True:
        for key in sorted(netstats):
            for obj in netstats[key]:
                print(obj.to_json())
            
    return netstats

def get_sessions(
    debug:bool,
    grid_url:str,
    grid_url_pid:int|None,
) -> list[Session]:
    url=f"{grid_url}/sessions"
    res:Response=requests.get(url)
    res.raise_for_status()
    data=res.json()
    
    if debug is True:
        print(url)
        pprint(data)

    sessions:list[Session]=[]

    if grid_url_pid is not None:
        try:
            for session in data["value"]:
                sessions.append(Session(capabilities=session["capabilities"], id=session["id"]))
        except KeyError:
            pprint(data)
            raise Exception(f"Session from url: '{url}' unknown format.")

    return sessions