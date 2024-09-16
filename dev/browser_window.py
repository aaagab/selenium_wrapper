#!/usr/bin/env python3
from pprint import pprint
import json
import os
import re
import shlex
import subprocess
import sys

from ..gpkgs import message as msg
from .processes import Processes, Proc, ReportOption


def get_root_browsers(
    debug:bool,
    browser_proc_name:str,
    processes_obj:Processes,
):
    browsers=processes_obj.from_name(browser_proc_name)
    root_browsers:list[Proc]=[]
    for browser in browsers:
        if browser.parent is None or (browser.parent.name != browser_proc_name):
            root_browsers.append(browser)
            if debug is True:
                processes_obj.report(browser.pid, show=True, from_root=True, opts=[ReportOption.PID, ReportOption.NAME])
    return root_browsers

def get_browser_window(
    browser_pid:int,
    browser_name:str,
    processes_obj:Processes,
):
    if browser_name == "edge":
        if sys.platform != "win32":
            raise Exception(f"browser '{browser_name}' not available on platform '{sys.platform}'")
        return processes_obj.from_name("MicrosoftEdgeCP.exe")[0]
    elif browser_name in ["firefox", "chrome"]:
        return processes_obj.from_pid(browser_pid)

def get_selenium_browsers(
    driver_proc_name:str,
    browser_name:str,
    root_browsers:list[Proc]|None=None,
):
    if root_browsers is None:
        root_browsers=[]
    selenium_browsers:list[Proc]=[]


    for browser in root_browsers:
        if sys.platform == "win32":
            if browser_name == "edge":
                selenium_browsers.append(browser)
            elif browser_name == "firefox":
                input("ouais")
                if len(browser.children) == 1:
                    child=browser.children[0]
                    if len(child.children) > 0:
                        selenium_browsers.append(browser)
                else:
                    if len(browser.tcp_conns) > 0:
                        if browser.tcp_conns[0].status == "LISTEN":
                            selenium_browsers.append(browser)
            else:
                parent=browser.parent
                if parent is not None:
                    if parent.name in [driver_proc_name, "unknown"]: # selenium browser
                        selenium_browsers.append(browser)
        elif sys.platform == "linux":
            parent=browser.parent
            if parent is not None:
                if parent.name in [driver_proc_name, "unknown"]: # selenium browser
                    selenium_browsers.append(browser)
                else:
                    if browser_name == "firefox":
                        if len(browser.tcp_conns) > 0:
                            if browser.tcp_conns[0].status == "LISTEN":
                                selenium_browsers.append(browser)

    return selenium_browsers
