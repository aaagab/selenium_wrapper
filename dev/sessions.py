#!/usr/bin/env python3
from pprint import pprint
import json
import os
import re
import shlex
import subprocess
import sys

from ..gpkgs import shell_helpers as shell

def close_sessions(
    debug=False,
    grid_url=None,
    grid_url_pid=None,
):
    if debug == True:
        print("Close All Sessions")

    for session in get_sessions(
        debug=debug,
        grid_url=grid_url,
        grid_url_pid=grid_url_pid,
    ):
        session_close(
            grid_url=grid_url,
            session_id=session["id"],
        )

def session_close(
    grid_url=None,
    session_id=None,
):
    subprocess.run(shlex.split("curl -sS -X \"DELETE\" {}/session/{}".format(grid_url, session_id)),stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    # you can also see the session from there on the browser, maybe modify it too.
    # http://127.0.0.1:4444/wd/hub/session/a09e521b-bfc7-4d8e-ab20-c50cf74160f9
    # http://127.0.0.1:4444/wd/hub/session/8e35d47a-9f98-4ff0-bb44-9eeb5d781ae3

def set_sessions(
    debug=False,
    drivers_data=dict(),
    grid_url=None,
    grid_url_pid=None,
    processes_obj=None,
):
    sessions=get_sessions(
        debug=debug,
        grid_url=grid_url,
        grid_url_pid=grid_url_pid,
    )
    if sessions:
        netstats=get_netstats(
            debug=debug,
            processes_obj=processes_obj,
        )
        for session in sessions:
            browser_name=session["capabilities"]["browserName"]
            driver_name=[k for k, v in drivers_data.items() if v["browser_name"] == browser_name][0]
            driver_data=drivers_data[driver_name]
            if driver_data["session"] is None:
                if driver_data["session_proc_name"] in netstats:
                    for netstat in netstats[driver_data["session_proc_name"]]:
                        if debug is True:
                            processes_obj.report(netstat["pid"], show=True, from_root=True, opts=["name", "pid"])
                        if is_session_driver(debug, netstat["port"], session["id"]) is True:
                            if debug is True:
                                print("For driver '{}' found active session '{}'".format(driver_name, session["id"]))
                            driver_data["session"]=session
                            driver_data["browser_session"]=netstat
                            break

def get_netstats(
    debug=False,
    processes_obj=None,
):
    netstats=dict()
    cmd="netstat -aon -p tcp"
    regex=r"^TCP\s+127.0.0.1:([0-9]+)\s+0.0.0.0:0\s+LISTENING\s+([0-9]+)$"
    for line in shell.cmd_get_value(cmd).splitlines():
        line=line.strip()
        if line:
            # TCP    127.0.0.1:57845        0.0.0.0:0              LISTENING       25612
            reg_listen=re.match(regex,line)
            if reg_listen:
                pid=reg_listen.group(2)
                port=reg_listen.group(1)
                proc_name=processes_obj.procs_by_pid[pid]["name"]
                if not proc_name in netstats:
                    netstats[proc_name]=[]

                netstats[proc_name].append(dict(
                    pid=pid,
                    port=port,
                ))

    if debug is True:
        print(cmd)
        print(regex)
        pprint(netstats)
    return netstats

def get_sessions(
    debug=False,
    grid_url=None,
    grid_url_pid=None,
):
    cmd="curl {}/sessions".format(grid_url)
    if debug is True:
        print(cmd)
    raw_curl=shell.cmd_get_value(cmd, none_on_error=True, no_err_if_std=True)
    if raw_curl is None:
        raw_curl=""

    dy_curl={}
    try:
        dy_curl = json.loads(raw_curl)
    except ValueError:
        if grid_url_pid is not None:
            print("Error when getting sessions data")
            pprint(raw_curl)
            sys.exit(1)

    sessions=[]
    if grid_url_pid is not None:
        for session in dy_curl["value"]:
            sessions.append(session)
    return sessions

def is_session_driver(
    debug=False,    
    port=None, 
    session_id=None,
):
    # >  curl -sSL http://127.0.0.1:46612/session/52A28BCF-FE74-4B1B-AAC7-23EBD0A82713
    # {"sessionId":"52A28BCF-FE74-4B1B-AAC7-23EBD0A82713","status":0,"value":{"browserName":"MicrosoftEdge","browserVersion":"44.17763.1.0","platformName":"windows","platformVersion":"10","takesElementScreenshot":true,"takesScreenshot":true,"acceptSslCerts":true,"applicationCacheEnabled":true,"locationContextEnabled":true,"webStorageEnabled":true,"ms:inPrivate":false,"pageLoadStrategy":"normal","unhandledPromptBehavior":"dismiss and notify"}}
    # >  curl -sSL http://127.0.0.1:21516/session/52A28BCF-FE74-4B1B-AAC7-23EBD0A82713
    # {"sessionId":"52A28BCF-FE74-4B1B-AAC7-23EBD0A82713","status":6,"value":{"error":"invalid session id","message":"The specified session ID does not exist or is no longer active.","stacktrace":""}}

    # port="5999"
    cmd="curl -sSL http://127.0.0.1:{}/session/{}".format(port, session_id)
    if debug is True:
        print(cmd)
    proc=subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr=proc.communicate()
    if stdout:
        try:
            data=json.loads(stdout)
        except ValueError:
            stdout=stdout.decode()
            if debug is True:
                print("stdout:", stdout)
            if '"applicationType":"gecko"' in stdout: # firefox
                return True
            elif stdout == "": # chrome
                return True
            return False

        if debug is True:
            print("stdout data:")
            pprint(data)

        if "status" in data: # edge
            if data["status"] == 0:
                return True
            else:
                return False
        elif "value" in data:
            if "browserName" in data["value"]:
                if data["value"]["browserName"] == "internet explorer":
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False
    elif stderr:
        if debug is True:
            print("stderr: {}".format(stderr.decode()))

        return False
    else:
        # google chrome returns nothing
        if debug is True:
            print("no stderr or stdout, returns empty")
        return True