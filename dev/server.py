#!/usr/bin/env python3
import json
import psutil
from pprint import pprint
from psutil import ZombieProcess
import os
import subprocess
import sys

from selenium import webdriver
from selenium.common.exceptions import SessionNotCreatedException

from .update_driver import update_chrome_driver
from .browsers import get_browsers_data, get_new_webdriver_session, close_browser_driver, close_selenium_browsers
from .browser_control import window_focus
from .browser_window import get_root_browsers, get_selenium_browsers
from .processes import Processes, get_tcp_connections
from .sessions import get_session, get_browser_pid, close_session
from .objs import BrowserData, Browser
from .windows import Windows

from ..gpkgs import message as msg
from ..gpkgs.timeout import TimeOut
from ..gpkgs import shell_helpers as shell

class SeleniumSettings():
    def __init__(
        self,
        dy_settings:dict[str, str],
    ) -> None:
        if dy_settings.get("direpa_drivers") is None:
            raise Exception("settings 'direpa_drivers' must be provided")
        else:
            self.direpa_drivers=dy_settings["direpa_drivers"]

        if dy_settings.get("direpa_extensions") is None:
            raise Exception("settings 'direpa_extensions' must be provided")
        else:
            self.direpa_extensions=dy_settings["direpa_extensions"]

        if dy_settings.get("direpa_logs") is None:
            raise Exception("settings 'direpa_logs' must be provided")
        else:
            self.direpa_logs=dy_settings["direpa_logs"]

        if dy_settings.get("filenpa_java") is None:
            raise Exception("settings 'filenpa_java' must be provided")
        else:
            self.filenpa_java=dy_settings["filenpa_java"]

        if dy_settings.get("filenpa_selenium_server") is None:
            raise Exception("settings 'filenpa_selenium_server' must be provided")
        else:
            self.filenpa_selenium_server=dy_settings["filenpa_selenium_server"]

        if dy_settings.get("filenpa_server_log") is None:
            raise Exception("settings 'filenpa_server_log' must be provided")
        else:
            self.filenpa_server_log=dy_settings["filenpa_server_log"]

class SeleniumServer():
    def __init__(
        self, 
        filenpa_settings:str,
        debug:bool=False,
        load_extensions:bool=False,
    ):

        settings:SeleniumSettings
        with open(filenpa_settings, "r") as f:
            dy_settings=json.load(f)
            settings=SeleniumSettings(dy_settings)

        self.debug=debug
        self.load_extensions=load_extensions
        self.processes=Processes(debug=self.debug)
        self.browser_data:BrowserData|None=None
        self.browser:Browser|None=None

        self.direpa_drivers=settings.direpa_drivers
        self.direpa_extensions=settings.direpa_extensions
        self.direpa_logs=settings.direpa_logs
        self.filenpa_java=settings.filenpa_java
        self.filenpa_selenium_server=settings.filenpa_selenium_server
        self.filenpa_server_log=settings.filenpa_server_log

        self.host="127.0.0.1"
        self.port=4444
        self.grid_url = f"http://127.0.0.1:{self.port}"
        self.grid_url_pid=None

        self.browser_names=[]
        if sys.platform in ["win32", "linux"]:
            self.browser_names.extend([
                "chrome",
                "firefox",
            ])

            if sys.platform == "win32":
                self.browser_names.extend([
                    "edge",
                ])

        self.browsers_data=get_browsers_data(
            load_extensions=load_extensions,
            direpa_drivers=self.direpa_drivers,
            direpa_extensions=self.direpa_extensions,
            direpa_logs=self.direpa_logs,
            browser_names=self.browser_names,
        )

        self.processes.init()
        self.windows=Windows(debug=self.debug)

    def connect(self, driver_name:str, close:bool=False, clear_cache:bool=False):
        if driver_name not in self.browsers_data:
            print("browser '{}' not found in {}".format(driver_name, sorted(self.browsers_data)))
            sys.exit(1)
        self.browser_data=self.browsers_data[driver_name]
        if clear_cache is True:
            if os.path.exists(self.browser_data.driver_data.direpa_data):
                shell.rmtree(self.browser_data.driver_data.direpa_data)
                os.makedirs(self.browser_data.driver_data.direpa_data, exist_ok=True)
     
        status=None
        if self.debug is True:
            print("grid_pid:", self.get_grid_url_pid())

        if self.get_grid_url_pid() is None:
            driver_args:list[str]=[]
            for args in [ browser_data.dwebdriver_args for name, browser_data in self.browsers_data.items()]:
                driver_args.extend(args)

            cmd=[
                self.filenpa_java,
                *driver_args,
                "-jar",
                self.filenpa_selenium_server,
                "standalone",
                "--log",
                self.filenpa_server_log,
                "--session-timeout",
                "252000", # 70 hours before the session timeout
                "--host",
                self.host,
            ]

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

            if sys.platform == "win32":
                self.grid_url_pid=subprocess.Popen(cmd, creationflags=DETACHED_PROCESS).pid
            elif sys.platform == "linux":
                self.grid_url_pid=subprocess.Popen(cmd).pid

            timer=TimeOut(20000, unit="milliseconds").start()
            while self.get_grid_url_pid() is None:
                if timer.has_ended(pause=.001):
                    raise Exception(f"Can't start '{self.filenpa_selenium_server}'")

        if self.debug is True:
            print("Process '{}' '{}' '{}'".format(
                self.get_grid_url_pid(),
                status,
                os.path.basename(self.filenpa_selenium_server)
            ))

        self.browser=self.get_browser(close=close)

    def get_browser(self, close:bool=False):
        if self.browser is None:
            if self.browser_data is None:
                raise Exception("browser_data must be set before calling get_browser.")
            session=get_session(
                debug=self.debug,
                browser_data=self.browser_data,
                grid_url=self.grid_url,
                grid_url_pid=self.get_grid_url_pid(),
            )

            if session is None:
                if close is True:
                    msg.warning(f"There is no running session to close for '{self.browser_data.name}'.")
                    sys.exit(1)
                
                browser=self.browser_data.name
                try:
                    self.browser = Browser(
                        driver=webdriver.Remote(self.grid_url, options=self.browser_data.options),
                        data=self.browser_data,
                        debug=self.debug,
                    )
                    if self.load_extensions is True:
                        if browser == "firefox":
                            for elem in sorted(os.listdir(self.browser_data.direpa_extensions)):
                                path_rel, ext=os.path.splitext(elem)
                                if ext == ".xpi":
                                    path_extension=os.path.join(self.browser_data.direpa_extensions, elem)
                                    webdriver.Firefox.install_addon(self.browser.driver, path_extension, temporary=True) #type:ignore

                except SessionNotCreatedException as e:
                    msg.warning(f"driver needs to be updated for browser '{self.browser_data.name}'")
                    raise
                self.processes.init()
                
                timer=TimeOut(20000, unit="milliseconds").start()
                while True:
                    if timer.has_ended(pause=.001):
                        raise Exception("browser_data.session has not been set")
                    self.browser_data.session=get_session(
                        debug=self.debug,
                        browser_data=self.browser_data,
                        grid_url=self.grid_url,
                        grid_url_pid=self.get_grid_url_pid(),
                    )
                    if self.browser_data.session is not None:
                        break

            else:
                if close is True:
                    if self.debug is True:
                        print(f"Close '{self.browser_data.name}' selenium session.")
                    close_session(self.grid_url, session.id)
                    sys.exit(0)
                    
                self.browser_data.session=session
                self.browser=Browser(driver=get_new_webdriver_session(
                        grid_url=self.grid_url,
                        options=self.browser_data.options,
                        session_id=session.id,
                    ),
                    data=self.browser_data,
                    debug=self.debug,
                )
            
            
            grid_pid=self.get_grid_url_pid()
            if grid_pid is None:
                raise Exception("Can't get grid url pid.")
            if self.browser_data.name == "firefox":
                self.browser_data.pid=self.browser_data.session.capabilities["moz:processID"]
            else:
                self.browser_data.pid=get_browser_pid(
                    browser_proc_name=self.browser_data.filen_browser,
                    driver_proc_name=self.browser_data.driver_data.proc_name,
                    grid_pid=grid_pid,
                    processes_obj=self.processes,
                )

        return self.browser

    def window_focus(self, exe_name:str):
        window_focus(self.processes, exe_name, debug=self.debug)

    def get_grid_url_pid(self):
        tcp_conns=get_tcp_connections(conn_kind="tcp")
        for tcp_conn in tcp_conns:
            if  tcp_conn.ip_local in [
                    self.host,
                    f"::ffff:{self.host}"
                ] and tcp_conn.port_local == self.port:
                return tcp_conn.pid
        return None
                
    def show_grid(self):
        exe_name:str
        if sys.platform == "win32":
            exe_name="firefox.exe"
        elif sys.platform == "linux":
            exe_name="firefox"
        os.system(f"{exe_name} {self.grid_url}")

    def close_browser_processes(self,
        browser_name:str,
        browser_proc_name:str,
        driver_proc_name:str,
        filenpa_log:str,
    ):
        root_browsers=get_root_browsers(debug=self.debug, browser_proc_name=browser_proc_name, processes_obj=self.processes)

        if self.debug is True:
            print("\nRoot Browsers:")
            for b in root_browsers:
                print(b.to_json())

        selenium_browsers=get_selenium_browsers(
            driver_proc_name=driver_proc_name,
            browser_name=browser_name,
            root_browsers=root_browsers,
        )
        
        if self.debug is True:
            print("\nSelenium Browsers:")
            for b in selenium_browsers:
                print(b.to_json())

        close_selenium_browsers(
            debug=self.debug,
            browser_name=browser_name,
            processes_obj=self.processes,
            selenium_browsers=selenium_browsers,                    
        )
        close_browser_driver(
            debug=self.debug, 
            driver_proc_name=driver_proc_name,
            processes_obj=self.processes,
        )
        open(filenpa_log, "w").close()


    def exit_grid(self):
        drivers:list[BrowserData]=[d for n, d in self.browsers_data.items()]
        for browser_data in drivers:
            self.close_browser_processes(
                browser_name=browser_data.name,
                browser_proc_name=browser_data.proc_name,
                driver_proc_name=browser_data.driver_data.proc_name,
                filenpa_log=browser_data.filenpa_log,
            )

        open(self.filenpa_server_log, "w").close()

        grid_pid=self.get_grid_url_pid()
        if grid_pid is not None:
            self.processes.kill(pid=grid_pid)
            self.grid_url_pid=None
        for proc in self.processes.from_name("java"):
            try:
                if self.filenpa_selenium_server in psutil.Process(proc.pid).cmdline():
                    self.processes.kill(proc.pid)
            except ZombieProcess:
                pass
                

