#!/usr/bin/env python3
import json
from pprint import pprint
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
import threading


from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from .drivers import get_drivers_data, get_driver_data, get_new_driver_session, close_driver, close_driver_browsers
from .browser_control import get_elem, scroll, refresh, window_focus, browser_focus
from .browser_window import get_root_browsers, get_selenium_browsers, get_browser_window
from .processes import Processes
from .sessions import set_sessions, close_sessions

from ..gpkgs import shell_helpers as shell
from ..gpkgs import message as msg
from ..gpkgs.timeout import TimeOut

from .windows import Windows


class SeleniumServer():
    def __init__(
        self, 
        accessibility=False,
        debug=False,
        direpa_media=None,
    ):
        self.debug=debug
        self.processes=Processes(debug=self.debug)
        self.driver_data=None
        self.driver=None
        if direpa_media is None:
            msg.error("direpa_media needs to be provided")
            sys.exit(1)
        self.direpa_media=direpa_media
        self.direpa_drivers=os.path.join(self.direpa_media, "drivers")
        self.filenpa_java=r"C:\Program Files\Java\jre1.8.0_251\bin\java"
        self.filenpa_java=r"C:\Program Files (x86)\Common Files\Oracle\Java\javapath\java.exe"
        self.host="127.0.0.1"
        self.port="4444"
        self.grid_url = "http://127.0.0.1:{}/wd/hub".format(self.port)
        self.grid_url_pid=None
        self.filenpa_selenium_server=os.path.join(self.direpa_media, "selenium-server-standalone-3.141.59.jar")
        self.filenpa_webdrivermanager=os.path.join(self.direpa_media, "webdrivermanager-4.0.0-fat.jar")
        self.direpa_logs=os.path.join(self.direpa_media, "logs")
        self.direpa_extensions=os.path.join(self.direpa_media, "extensions")
        self.filenpa_log=os.path.join(self.direpa_logs, "server.txt")
        self.filenpa_drivers_info=os.path.join(self.direpa_drivers, "info.txt")


        self.driver_names=[
            "chrome",
            "firefox",
            "edge",
            "iexplorer",
            # "opera",
            # "phantomjs",
        ]

        self.drivers_data=get_drivers_data(
            accessibility=accessibility,
            direpa_drivers=self.direpa_drivers,
            direpa_extensions=self.direpa_extensions,
            direpa_logs=self.direpa_logs,
            driver_names=self.driver_names,
        )

        self.processes.init()
        self.windows=Windows(debug=self.debug)


    def connect(self, driver_name, reset=False):
        self.driver_data=get_driver_data(self.driver_names, self.drivers_data, driver_name)
        if reset is True:
            if self.debug is True:
                print("Start or Restart '{}'".format(os.path.basename(self.filenpa_selenium_server)))
            if self.get_grid_url_pid() is not None:
                self.processes.kill(self.get_grid_url_pid())
                self.grid_url_pid=None

        status=None
        if self.get_grid_url_pid() is None:
            driver_args=[]
            for args in [ driver["dwebdriver_args"] for name, driver in self.drivers_data.items()]:
                driver_args.extend(args)

            cmd=[
                self.filenpa_java,
                *driver_args,
                "-jar",
                self.filenpa_selenium_server,
                "-log",
                self.filenpa_log,
                "-timeout",
                "252000", # 70 hours before the session timeout
                "-host",
                self.host,
            ]

            print(" ".join(cmd))

            DETACHED_PROCESS = 0x00000008
            cmd_str=""
            for a, arg in enumerate(cmd):
                prefix=" "
                if " " in arg:
                    arg="\"{}\"".format(arg)
                if a == 0:
                    prefix=""
                cmd_str+=prefix+arg
            if self.debug is True:
                print(cmd_str)

            self.grid_url_pid=subprocess.Popen(cmd, creationflags=DETACHED_PROCESS).pid
            status="started"
        else:
            status="already running"

        if self.debug is True:
            print("Process '{}' '{}' '{}'".format(
                self.get_grid_url_pid(),
                status,
                os.path.basename(self.filenpa_selenium_server)
            ))

        self.driver=self.get_driver()

    def close_driver_processes(self,
        driver_filen_browser,
        driver_filen_exe,
        driver_name,
        driver_proc_name,
    ):
        root_browsers=get_root_browsers(self.debug, driver_filen_browser, self.processes)
        selenium_browsers=get_selenium_browsers(
            driver_filen_exe=driver_filen_exe,
            driver_name=driver_name,
            root_browsers=root_browsers,
        )
        close_driver_browsers(
            debug=self.debug,
            driver_name=driver_name,
            filen_browser=driver_filen_browser,
            processes_obj=self.processes,
            selenium_browsers=selenium_browsers,                    
        )
        close_driver(
            debug=self.debug, 
            driver_proc_name=driver_proc_name,
            processes_obj=self.processes,
        )

    def get_driver(self):
        if self.driver is None:
            set_sessions(
                debug=self.debug,
                drivers_data=self.drivers_data,
                grid_url=self.grid_url,
                grid_url_pid=self.get_grid_url_pid(),
                processes_obj=self.processes,
            )
            session=self.driver_data["session"]

            if session is None:
                self.close_driver_processes(
                    driver_filen_browser=self.driver_data["filen_browser"],
                    driver_filen_exe=self.driver_data["filen_exe"],
                    driver_name=self.driver_data["name"],
                    driver_proc_name=self.driver_data["driver_proc_name"],
                )
                self.driver = webdriver.Remote(self.grid_url, self.driver_data["capabilities"])
                self.processes.init()
                set_sessions(
                    debug=self.debug,
                    drivers_data=self.drivers_data,
                    grid_url=self.grid_url,
                    grid_url_pid=self.get_grid_url_pid(),
                    processes_obj=self.processes,
                )
                # populate session and browser from here.
            else:
                self.driver=get_new_driver_session(
                    grid_url=self.grid_url,
                    session_id=session["id"],
                )

                pprint(self.driver_data["browser_session"])                    

            setattr(self.driver, "dy", self.driver_data)
            setattr(self.driver, "scroll", self.scroll)
            setattr(self.driver, "get_elem", self.get_elem)

            root_browsers=get_root_browsers(self.debug, self.driver_data["filen_browser"], self.processes)
            self.driver_data["browser_window"]=get_browser_window(
                driver_browser_pid=self.driver_data["browser_session"]["pid"],
                driver_name=self.driver_data["name"],
                processes_obj=self.processes,
                root_browsers=root_browsers,
            )
        return self.driver

    def get_elem(self, id, wait_ms=2000, error=True):
        get_elem(self.get_driver(), id=id, wait_ms=wait_ms, error=error)

    def scroll(self, percent=None, wait_ms=None):
        scroll(self.get_driver(), percent=percent, wait_ms=wait_ms)

    def refresh(self, wait_ms=None):
        refresh(self.get_driver(), wait_ms=None)

    def window_focus(self, exe_name):
        window_focus(self.processes, self.windows, exe_name)

    def browser_focus(self):
        browser_focus(self.get_driver(), self.windows)

    def get_grid_url_pid(self):
        if self.grid_url_pid is None:
            for line in shell.cmd_get_value("netstat -ano").splitlines():
                # TCP    0.0.0.0:4444           0.0.0.0:0              LISTENING       23216
                reg_server=re.match(r"^\s+TCP\s+{}:{}\s+0.0.0.0:0\s+LISTENING\s+([0-9]+)$".format(self.host, self.port),line)
                if reg_server:
                    self.grid_url_pid=reg_server.group(1)
                    break

        return self.grid_url_pid

    def show_gui(self):
        os.system("firefox.exe {}/static/resource/hub.html".format(self.grid_url))
        os.system("firefox.exe {}/sessions".format(self.grid_url))
        for name, driver in self.drivers_data.items():
            for session in driver["sessions"]:
                os.system("firefox.exe {}/session/{}".format(self.grid_url, session["id"]))

    def reset(self, driver_names=[]):
        drivers=[]

        if driver_names:
            for name in driver_names:
                if name not in self.drivers_data:
                    print("In reset driver '{}' not found in {}".format(name, self.drivers_data))
                    sys.exit(1)
                drivers.append(self.drivers_data[name])
        else:
            drivers=self.drivers_data

        for name, driver_data in drivers.items():
            self.close_driver_processes(
                driver_filen_browser=driver_data["filen_browser"],
                driver_filen_exe=driver_data["filen_exe"],
                driver_name=driver_data["name"],
                driver_proc_name=driver_data["driver_proc_name"],
            )
            open(driver_data["filenpa_log"], "w").close()
        
        close_sessions(
            debug=self.debug,
            grid_url=self.grid_url,
            grid_url_pid=self.grid_url_pid,
        )
        
        open(self.filenpa_log, "w").close()

        if self.get_grid_url_pid() is not None:
            self.processes.kill(self.get_grid_url_pid())
            self.grid_url_pid=None

