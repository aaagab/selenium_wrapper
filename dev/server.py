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

import selenium
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from .update_driver import update_chrome_driver
from .drivers import get_drivers_data, get_driver_data, get_new_driver_session, close_driver, close_driver_browsers
from .browser_control import get_elem, scroll, refresh, window_focus, browser_focus, scroll_to, send_js_event
from .browser_window import get_root_browsers, get_selenium_browsers, get_browser_window
from .processes import Processes
from .sessions import set_sessions, close_sessions, get_session, get_browser_pid

from ..gpkgs import shell_helpers as shell
from ..gpkgs import message as msg
from ..gpkgs.timeout import TimeOut
from ..gpkgs.etconf import Etconf

from .windows import Windows

class SeleniumSettings():
    def __init__(
        self,
        direpa_drivers=None,
        direpa_extensions=None,
        direpa_logs=None,
        filenpa_java=None,
        filenpa_selenium_server=None,
        filenpa_server_log=None,
    ):
        self.direpa_drivers=direpa_drivers
        self.direpa_extensions=direpa_extensions
        self.direpa_logs=direpa_logs
        self.filenpa_java=filenpa_java
        self.filenpa_selenium_server=filenpa_selenium_server
        self.filenpa_server_log=filenpa_server_log

    def set(self, dy_settings: dict):
        if dy_settings.get("direpa_drivers") is not None:
            self.direpa_drivers=dy_settings["direpa_drivers"]
        if dy_settings.get("direpa_extensions") is not None:
            self.direpa_extensions=dy_settings["direpa_extensions"]
        if dy_settings.get("direpa_logs") is not None:
            self.direpa_logs=dy_settings["direpa_logs"]
        if dy_settings.get("filenpa_java") is not None:
            self.filenpa_java=dy_settings["filenpa_java"]
        if dy_settings.get("filenpa_selenium_server") is not None:
            self.filenpa_selenium_server=dy_settings["filenpa_selenium_server"]
        if dy_settings.get("filenpa_server_log") is not None:
            self.filenpa_server_log=dy_settings["filenpa_server_log"]

    def validate(self):
        if self.direpa_drivers is None:
            raise "settings 'direpa_drivers' must be provided"
        if self.direpa_extensions is None:
            raise "settings 'direpa_extensions' must be provided"
        if self.direpa_logs is None:
            raise "settings 'direpa_logs' must be provided"
        if self.filenpa_java is None:
            raise "settings 'filenpa_java' must be provided"
        if self.filenpa_selenium_server is None:
            raise "settings 'filenpa_selenium_server' must be provided"
        if self.filenpa_server_log is None:
            raise "settings 'filenpa_server_log' must be provided"

class SeleniumServer():
    def __init__(
        self, 
        load_extensions=False,
        settings: SeleniumSettings = None,
        debug=False,
    ):

        def seed(pkg_major, direpas_configuration=dict(), fun_auto_migrate=None):
            fun_auto_migrate()

        filenpa_gpm=os.path.join(os.path.dirname(os.path.dirname(os.path.relpath(__file__))), "gpm.json")
        etconf=Etconf(
            filenpa_gpm=filenpa_gpm,
            enable_dev_conf=False, 
            tree=dict(), 
            seed=seed, 
        )

        if settings is None:
            filenpa_settings=os.path.join(etconf.direpa_configuration, "settings.json")
            settings=SeleniumSettings()
            dy_settings=dict()
            with open(filenpa_settings, "r") as f:
                dy_settings=json.load(f)
            settings.set(dy_settings)

        settings.validate()

        self.debug=debug
        self.load_extensions=load_extensions
        self.processes=Processes(debug=self.debug)
        self.driver_data=None
        self.driver=None

        self.direpa_drivers=settings.direpa_drivers
        self.direpa_extensions=settings.direpa_extensions
        self.direpa_logs=settings.direpa_logs
        self.filenpa_java=settings.filenpa_java
        self.filenpa_selenium_server=settings.filenpa_selenium_server
        self.filenpa_server_log=settings.filenpa_server_log

        self.host="127.0.0.1"
        self.port="4444"
        self.grid_url = "http://127.0.0.1:{}/wd/hub".format(self.port)
        self.grid_url_pid=None

        self.driver_names=[
            "chrome",
            "firefox",
            "edge",
            "iexplorer",
            # "msedge",
            # "opera",
            # "phantomjs",
        ]

        self.drivers_data=get_drivers_data(
            load_extensions=load_extensions,
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
                self.filenpa_server_log,
                "-timeout",
                "252000", # 70 hours before the session timeout
                "-host",
                self.host,
            ]

            # print(" ".join(cmd))

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

            if not os.path.exists(self.filenpa_java):
                msg.error("Java not found at '{}".format(self.filenpa_java),exit=1)

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
            session=get_session(
                debug=self.debug,
                driver_data=self.driver_data,
                grid_url=self.grid_url,
                grid_url_pid=self.get_grid_url_pid(),
            )

            if session is None:
                browser=self.driver_data["capabilities"]["browserName"]
                try:
                    self.driver = webdriver.Remote(self.grid_url, self.driver_data["capabilities"])
                    if self.load_extensions is True:
                        if browser == "firefox":
                            for elem in sorted(os.listdir(self.driver_data["direpa_extensions"])):
                                path_rel, ext=os.path.splitext(elem)
                                if ext == ".xpi":
                                    path_extension=os.path.join(self.driver_data["direpa_extensions"], elem)
                                    webdriver.Firefox.install_addon(self.driver, path_extension, temporary=True)

                except selenium.common.exceptions.SessionNotCreatedException as e:
                    if browser == "chrome":
                        self.reset()
                        os.system("taskkill /F /IM chromedriver.exe")
                        update_chrome_driver(self.direpa_drivers)
                        msg.success("Chrome driver updated. Please restart command.")
                        sys.exit(1)
                    else:
                        raise
                self.processes.init()
                
                self.driver_data["session"]=get_session(
                    debug=self.debug,
                    driver_data=self.driver_data,
                    grid_url=self.grid_url,
                    grid_url_pid=self.get_grid_url_pid(),
                )

            else:
                self.driver_data["session"]=session
                self.driver=get_new_driver_session(
                    grid_url=self.grid_url,
                    session_id=session["id"],
                )

            if self.driver_data["name"] == "firefox":
                self.driver_data["browser_pid"]=self.driver_data["session"]["capabilities"]["moz:processID"]
            else:
                self.driver_data["browser_pid"]=get_browser_pid(
                    self.driver_data["filen_browser"],
                    self.driver_data["driver_proc_name"],
                    self.get_grid_url_pid(),
                    self.processes,
                )

            setattr(self.driver, "dy", self.driver_data)
            setattr(self.driver, "scroll", self.scroll)
            setattr(self.driver, "scroll_to", self.scroll_to)
            setattr(self.driver, "send_js_event", self.send_js_event)
            setattr(self.driver, "get_elem", self.get_elem)
        return self.driver

    def get_elem(self, id=None, xpath=None, xpath_context=None, wait_ms=2000, error=True):
        return get_elem(self.get_driver(), id=id, xpath=xpath, xpath_context=xpath_context, wait_ms=wait_ms, error=error)

    # def scroll(self, percent=None, pause_ms=None):
    #     scroll(self.debug, self.get_driver(), percent=percent, pause_ms=pause_ms)


    def scroll(self, percent=None, pause_ms=None):
        scroll(self.debug, self.get_driver(), percent=percent, pause_ms=pause_ms)

    def scroll_to(self, id=None, xpath=None, xpath_context=None, wait_ms=None, pause_ms=None):
        scroll_to(self.get_driver(), id=id, xpath=xpath, xpath_context=xpath_context, wait_ms=wait_ms, pause_ms=pause_ms)

    def send_js_event(self, event_str, id=None, xpath=None, xpath_context=None, wait_ms=None, pause_ms=None):
        send_js_event(self.get_driver(), event_str, id=id, xpath=xpath, xpath_context=xpath_context, wait_ms=wait_ms, pause_ms=pause_ms)


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
            open(driver_data["filenpa_server_log"], "w").close()
        
        close_sessions(
            debug=self.debug,
            grid_url=self.grid_url,
            grid_url_pid=self.grid_url_pid,
        )
        
        open(self.filenpa_server_log, "w").close()

        if self.get_grid_url_pid() is not None:
            self.processes.kill(self.get_grid_url_pid())
            self.grid_url_pid=None

