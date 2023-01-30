#!/usr/bin/env python3
from pprint import pprint
import json
import os
import re
import shlex
import subprocess
import sys
import time

from selenium.webdriver.common.by import By

from ..gpkgs.timeout import TimeOut
from ..gpkgs import message as msg

def get_elem(
    driver, 
    id, 
    wait_ms=2000,
    error=True
):
    timer=TimeOut(wait_ms, unit="milliseconds").start()
    elem=None
    while True:
        if timer.has_ended(pause=.001):
            if error is True:
                msg.error("element not found '{}'".format(id))
                sys.exit(1)
            else:
                return None
        try:
            elem=driver.find_element(By.ID, id)
            break
        except BaseException as e:
            if e.__class__.__name__ == "NoSuchElementException":
                continue

    return elem

def scroll_to(debug, driver, element_id, wait_ms=None):
    if wait_ms is not None:
        time.sleep(float(wait_ms)/1000)

    driver.execute_script("document.getElementById('{}').scrollIntoView()".format(element_id))

def scroll(debug, driver, percent=None, wait_ms=None):
    from selenium.webdriver.common.keys import Keys
    if wait_ms is not None:
        time.sleep(float(wait_ms)/1000)

    if percent is None:
        percent=100
    else:
        percent=int(percent)
    scroll_height=int(driver.execute_script("return document.documentElement.scrollHeight"))

    if debug is True:
        print("scroll page height: {}".format(scroll_height))
    if percent < 100:
        scroll_height=int(scroll_height*((percent/100)))
    driver.execute_script("window.scrollTo(0,{})".format(scroll_height))

def refresh(driver, wait_ms=None):
    driver.refresh()
    if wait_ms is not None:
        time.sleep(float(wait_ms)/1000)

def window_focus(processes_obj, windows_obj, exe_name):
    if not exe_name in processes_obj.procs_by_name:
        msg.error("Process not found '{}'".format(exe_name))
        sys.exit(1)
    pid=processes_obj.procs_by_name[exe_name][0]["pid"]
    windows_obj.focus(pid)

def browser_focus(driver, windows_obj):
    pid=driver.dy["browser_pid"]
    # pid=5300
    windows_obj.focus(pid)