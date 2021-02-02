#!/usr/bin/env python3
from pprint import pprint
import json
import os
import re
import shlex
import subprocess
import sys


def get_root_browsers(
    debug=False,
    filen_browser=None,
    processes_obj=None,    
):
    browsers=processes_obj.from_name(filen_browser)
    root_browsers=[]
    for browser in browsers:
        if browser["node"].parent is None or (browser["node"].parent.dy["name"] != filen_browser):
            root_browsers.append(browser)
            if debug is True:
                processes_obj.report(browser["pid"], show=True, from_root=True, opts=["name", "pid"])
                print()
    return root_browsers

def get_browser_window(
    debug=False, 
    driver_browser_pid=None,
    driver_name=None,
    processes_obj=None,
    root_browsers=[]
):
    if debug is True:
        print(root_browsers)
    if driver_name == "edge":
        return processes_obj.procs_by_name["MicrosoftEdgeCP.exe"][0]
    elif driver_name == "iexplorer":
        for browser in root_browsers:
            if browser["ppid"] == driver_browser_pid:
                return browser
        hasBeenKilled=False
        for browser in root_browsers:
            hasBeenKilled=True
            processes_obj.kill(browser["pid"])

        if hasBeenKilled is True:
            msg.error("Stalled browser for '{}' has been killed please relaunch command".format(driver_name), exit=1)
        else:
            msg.error("No Suitable existing browser has been found for '{}'. Try reset".format(driver_name), exit=1)
    elif driver_name in ["firefox", "chrome"]:
        return processes_obj.from_pid(driver_browser_pid)
    # elif driver_name == "chrome":
        # print(s)
        # pprint(browsers)

def get_selenium_browsers(
    driver_filen_exe=None,
    driver_name=None,
    root_browsers=[],  
):
    selenium_browsers=[]
    for browser in root_browsers:
        if driver_name == "edge":
            selenium_browsers.append(browser)
        elif driver_name == "firefox":
            if len(browser["node"].nodes) == 1:
                child=browser["node"].nodes[0]
                if len(child.nodes) > 0:
                    selenium_browsers.append(browser)
            else:
                if len(browser["netstat"]) > 0:
                    if browser["netstat"][0]["state"] == "LISTENING":
                        selenium_browsers.append(browser)
        else:
            parent_first=browser["node"].parent
            if parent_first.dy["name"] in [driver_filen_exe, "unknown"]: # selenium browser
                selenium_browsers.append(browser)

    return selenium_browsers
