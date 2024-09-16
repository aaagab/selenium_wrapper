#!/usr/bin/env python3
import sys

from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import ElementNotInteractableException

from .windows import Windows
from .processes import Processes, Proc

from ..gpkgs.timeout import TimeOut
from ..gpkgs import message as msg


def send_keys(elem:WebElement, value:str):
    wait_ms=5000
    timer=TimeOut(wait_ms, unit="milliseconds").start()
    while True:
        try:
            elem.send_keys(value)
            break
        except ElementNotInteractableException:
            pass

        if timer.has_ended(pause=.001):
            break

def window_focus(processes_obj:Processes, exe_name:str, debug:bool):
    windows_obj=Windows(debug=debug)
    dy_procs:dict[float, list[Proc]]=dict()

    for p in processes_obj.from_name(name=exe_name):
        tmptime=p.psproc.create_time()
        if tmptime not in dy_procs:
            dy_procs[tmptime]=[]
        dy_procs[tmptime].append(p)

    if len(dy_procs) == 0:
        msg.error("Process not found '{}'".format(exe_name))
        sys.exit(1)

    for tmptime in sorted(dy_procs, reverse=True):
        pid=dy_procs[tmptime][-1].pid
        windows_obj.focus(pid)
        break
