#!/usr/bin/env python3
import json
from pprint import pprint
import os
import re
import shlex
import subprocess
import sys
import time
import threading

from .processes import Processes

from ..gpkgs import shell_helpers as shell
from ..gpkgs import message as msg
from ..gpkgs.timeout import TimeOut

r"""
"C:\Users\john\Desktop\data\bin\selenium\selenium_server.py"
"""

from .windows import Windows

class SeleniumServer():
    def __init__(
        self, 
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
        self.host="127.0.0.1"
        self.port="4444"
        self.grid_url = "http://127.0.0.1:{}/wd/hub".format(self.port)
        self.filenpa_selenium_server=os.path.join(self.direpa_media, "selenium-server-standalone-3.141.59.jar")
        self.filenpa_webdrivermanager=os.path.join(self.direpa_media, "webdrivermanager-4.0.0-fat.jar")
        self.direpa_logs=os.path.join(self.direpa_media, "logs")
        self.filenpa_log=os.path.join(self.direpa_logs, "server.txt")
        self.filenpa_drivers_info=os.path.join(self.direpa_drivers, "info.txt")
        self.set_drivers_data()
        self.processes.init()

    def set_sessions(self):
        sessions=self.get_sessions()
        if sessions:
            netstats=self.get_netstats()
            for session in sessions:
                browser_name=session["capabilities"]["browserName"]
                driver_name=[k for k, v in self.drivers_data.items() if v["browser_name"] == browser_name][0]
                driver_data=self.drivers_data[driver_name]
                if driver_data["session"] is None:
                    if driver_data["session_proc_name"] in netstats:
                        for netstat in netstats[driver_data["session_proc_name"]]:
                            if self.debug is True:
                                self.processes.report(netstat["pid"], show=True, from_root=True, opts=["name", "pid"])
                            if self.is_session_driver(netstat["port"], session["id"]) is True:
                                if self.debug is True:
                                    print("For driver '{}' found active session '{}'".format(driver_name, session["id"]))
                                driver_data["session"]=session
                                driver_data["browser_session"]=netstat
                                break

    def get_sessions(self):
        pid=self.get_pid()
        cmd="curl {}/sessions".format(self.grid_url)
        if self.debug is True:
            print(cmd)
        raw_curl=shell.cmd_get_value(cmd, none_on_error=True, no_err_if_std=True)
        if raw_curl is None:
            raw_curl=""

        dy_curl={}
        try:
            dy_curl = json.loads(raw_curl)
        except ValueError:
            if pid is not None:
                print("Error when getting sessions data")
                pprint(raw_curl)
                sys.exit(1)

        sessions=[]
        if pid is not None:
            for session in dy_curl["value"]:
                sessions.append(session)

        return sessions

    def session_close(self, session_id):
        subprocess.run(shlex.split("curl -sS -X \"DELETE\" {}/session/{}".format(self.grid_url, session_id)),stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        # you can also see the session from there on the browser, maybe modify it too.
        # http://127.0.0.1:4444/wd/hub/session/a09e521b-bfc7-4d8e-ab20-c50cf74160f9

    def set_driver_data(self, name):
        if name not in self.driver_names:
            print("driver '{}' not found in {}".format(name, self.driver_names))
            sys.exit(1)
        self.driver_data=self.drivers_data[name]

    def get_netstats(self):
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
                    proc_name=self.processes.procs_by_pid[pid]["name"]
                    if not proc_name in netstats:
                        netstats[proc_name]=[]

                    netstats[proc_name].append(dict(
                        pid=pid,
                        port=port,
                    ))

        if self.debug is True:
            print(cmd)
            print(regex)
            pprint(netstats)
        return netstats

    def is_session_driver(self, port, session_id):
        # >  curl -sSL http://127.0.0.1:46612/session/52A28BCF-FE74-4B1B-AAC7-23EBD0A82713
        # {"sessionId":"52A28BCF-FE74-4B1B-AAC7-23EBD0A82713","status":0,"value":{"browserName":"MicrosoftEdge","browserVersion":"44.17763.1.0","platformName":"windows","platformVersion":"10","takesElementScreenshot":true,"takesScreenshot":true,"acceptSslCerts":true,"applicationCacheEnabled":true,"locationContextEnabled":true,"webStorageEnabled":true,"ms:inPrivate":false,"pageLoadStrategy":"normal","unhandledPromptBehavior":"dismiss and notify"}}
        # >  curl -sSL http://127.0.0.1:21516/session/52A28BCF-FE74-4B1B-AAC7-23EBD0A82713
        # {"sessionId":"52A28BCF-FE74-4B1B-AAC7-23EBD0A82713","status":6,"value":{"error":"invalid session id","message":"The specified session ID does not exist or is no longer active.","stacktrace":""}}

        # port="5999"
        cmd="curl -sSL http://127.0.0.1:{}/session/{}".format(port, session_id)
        if self.debug is True:
            print(cmd)
        proc=subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr=proc.communicate()
        if stdout:
            try:
                data=json.loads(stdout)
            except ValueError:
                stdout=stdout.decode()
                if self.debug is True:
                    print("stdout:", stdout)
                if '"applicationType":"gecko"' in stdout: # firefox
                    return True
                elif stdout == "": # chrome
                    return True
                return False

            if self.debug is True:
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
            if self.debug is True:
                print("stderr: {}".format(stderr.decode()))

            return False
        else:
            # google chrome returns nothing
            if self.debug is True:
                print("no stderr or stdout, returns empty")
            return True

    def get_pid(self):
        for line in shell.cmd_get_value("netstat -ano").splitlines():
            # TCP    0.0.0.0:4444           0.0.0.0:0              LISTENING       23216
            reg_server=re.match(r"^\s+TCP\s+{}:{}\s+0.0.0.0:0\s+LISTENING\s+([0-9]+)$".format(self.host, self.port),line)
            if reg_server:
                pid=reg_server.group(1)
                return pid
        return None

    def show_gui(self):
        os.system("firefox.exe {}/static/resource/hub.html".format(self.grid_url))
        os.system("firefox.exe {}/sessions".format(self.grid_url))
        for name, driver in self.drivers_data.items():
            for session in driver["sessions"]:
                os.system("firefox.exe {}/session/{}".format(self.grid_url, session["id"]))
        
    def set_drivers_data(self):
        from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
        self.drivers_data=dict()
        self.driver_names=[
            "chrome",
            "firefox",
            "edge",
            "iexplorer",
            # "opera",
            # "phantomjs",
        ]
        for name in self.driver_names:
            self.drivers_data[name]=dict()
            driver=self.drivers_data[name]

            driver_label=name
            capability_name=name.upper()
            session_proc_name=None
            driver_proc_name=None
            log_label=None
            if name == "firefox":
                driver_label="gecko"
                browser_name=name
                filen_browser="firefox.exe"
                session_proc_name=filen_browser
                log_label="firefox"
                filen_exe="geckodriver.exe"
            elif name == "iexplorer":
                browser_name="internet explorer"
                driver_label="ie"
                capability_name="INTERNETEXPLORER"
                filen_exe="IEDriverServer.exe"
                filen_browser="iexplore.exe"
                log_label="ie.driver"
            elif name == "chrome":
                browser_name=name
                filen_browser="chrome.exe"
                filen_exe="chromedriver.exe"
                session_proc_name=filen_browser
            elif name == "edge":
                browser_name="MicrosoftEdge"
                filen_browser="MicrosoftEdge.exe"
                session_proc_name="System"
                filen_exe="MicrosoftWebDriver.bat"
                driver_proc_name=filen_exe.replace(".bat", ".exe")

            if log_label is None:
                log_label=driver_label

            if session_proc_name is None:
                session_proc_name=filen_exe

            if driver_proc_name is None:
                driver_proc_name=filen_exe

            driver["name"]=name
            driver["filen_exe"]=filen_exe
            driver["filenpa_exe"]=os.path.join(self.direpa_drivers, filen_exe)
            driver["filen_browser"]=filen_browser
            driver["browser_name"]=browser_name
            driver["driver_proc_name"]=driver_proc_name
            driver["session_proc_name"]=session_proc_name
            driver["filenpa_log"]=os.path.join(self.direpa_logs, "client_{}.txt".format(name))
            driver["session"]=None

            driver["dwebdriver_args"]="-Dwebdriver.{driver_label}.driver={filenpa_exe}\n-Dwebdriver.{log_label}.logfile={filenpa_log}\n-Dwebdriver.{log_label}.loglevel=DEBUG".format(
                driver_label=driver_label,
                log_label=log_label, 
                filenpa_exe=driver["filenpa_exe"],
                filenpa_log=driver["filenpa_log"],    
            ).splitlines()
            driver["capabilities"]=getattr(DesiredCapabilities, capability_name)

    def create_driver_session(self, session_id):
        from selenium import webdriver
        from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver

        # Save the original function, so we can revert our patch
        org_command_execute = RemoteWebDriver.execute

        def new_command_execute(self, command, params=None):
            if command == "newSession":
                # Mock the response
                return {'success': 0, 'value': None, 'sessionId': session_id}
            else:
                return org_command_execute(self, command, params)

        # Patch the function before creating the driver object
        RemoteWebDriver.execute = new_command_execute

        new_driver = webdriver.Remote(command_executor=self.grid_url, desired_capabilities={})
        new_driver.session_id = session_id

        # Replace the patched function with original function
        RemoteWebDriver.execute = org_command_execute

        return new_driver

    def close_driver(self, driver_data):
        if self.debug is True:
            print("Close Selenium Driver '{}'".format(driver_data["driver_proc_name"]))
        if driver_data["driver_proc_name"] in self.processes.procs_by_name:
            self.processes.kill(driver_data["driver_proc_name"])

    def get_root_browsers(self, driver_data):
        # print("here")
        browsers=self.processes.from_name(driver_data["filen_browser"])
        # pprint(browsers)
        # I should clean internetexplorer browser that are not used.
        # can you check if a windows exists for a pid.
        root_browsers=[]
        for browser in browsers:
            # print(browser)
            if browser["node"].parent.dy["name"] != driver_data["filen_browser"]:
                root_browsers.append(browser)
                if self.debug is True:
                    self.processes.report(browser["pid"], show=True, from_root=True, opts=["name", "pid"])
                    print()
        
        return root_browsers

    # def is_selenium_browser(self, ):

    def get_selenium_browsers(self, driver_data):
        selenium_browsers=[]

        for browser in self.get_root_browsers(driver_data):
            if driver_data["name"] == "edge":
                selenium_browsers.append(browser)
            elif driver_data["name"] == "firefox":
                # pprint(browser)
                if len(browser["node"].nodes) == 1:
                    child=browser["node"].nodes[0]
                    if len(child.nodes) > 0:
                        selenium_browsers.append(browser)
            else:
                parent_first=browser["node"].parent
                if parent_first.dy["name"] in [driver_data["filen_exe"], "unknown"]: # selenium browser
                    selenium_browsers.append(browser)

        return selenium_browsers

    def close_driver_browsers(self, driver_data):
        if self.debug is True:
            print("Close Selenium Browsers '{}'".format(driver_data["filen_browser"]))
        for browser in self.get_selenium_browsers(driver_data):
            pid=None
            if driver_data["name"] == "firefox":
                pid=browser["node"].nodes[0].dy["pid"]
            else:
                pid=browser["pid"]
            self.processes.kill(pid)
            pass

    def close_sessions(self):
        if self.debug == True:
            print("Close All Sessions")
        # pprint(self.drivers_data)
        for session in self.get_sessions():
            self.session_close(session["id"])

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

        for name, driver in drivers.items():
            self.close_driver_browsers(driver)
            self.close_driver(driver)
            open(driver["filenpa_log"], "w").close()
        self.close_sessions()
        open(self.filenpa_log, "w").close()

        server_pid=self.get_pid()
        if server_pid is not None:
            self.processes.kill(server_pid)

    def connect(self, driver_name, reset=False):
        from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
        # tasklist=shell.cmd_get_value("tasklist")
        self.set_driver_data(driver_name)

        pid=self.get_pid()
        if reset is True:
            if self.debug is True:
                print("Start or Restart '{}'".format(os.path.basename(self.filenpa_selenium_server)))
            if pid is not None:
                self.processes.kill(pid)
                pid=None

        status=None
        if pid is None:
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
            pid=subprocess.Popen(cmd, creationflags=DETACHED_PROCESS).pid
            status="started"
        else:
            status="already running"

        if self.debug is True:
            print("Process '{}' '{}' '{}'".format(
                pid,
                status,
                os.path.basename(self.filenpa_selenium_server)
            ))

        self.driver=self.get_driver()
    # )
    def get_browser_window(self, driver_data):
        browsers= self.get_root_browsers(driver_data)
        if self.debug is True:
            print(browsers)
        if driver_data["name"] == "edge":
            return self.processes.procs_by_name["MicrosoftEdgeCP.exe"][0]
            # print(browsers[0]["node"].nodes)
        elif driver_data["name"] == "iexplorer":
            for browser in browsers:
                if browser["ppid"] == self.driver_data["browser_session"]["pid"]:
                    return browser
        elif driver_data["name"] in ["firefox", "chrome"]:
            return self.processes.from_pid(self.driver_data["browser_session"]["pid"])
        # elif driver_data["name"] == "chrome":
            # print(s)
            # pprint(browsers)

    def get_driver(self):
        from selenium import webdriver

        if self.driver is None:
            self.set_sessions()
            session=self.driver_data["session"]
            if session is None:
                self.close_driver_browsers(self.driver_data)
                self.close_driver(self.driver_data)
                self.driver = webdriver.Remote(self.grid_url, self.driver_data["capabilities"])
                self.processes.init()
                self.set_sessions()
                # populate session and browser from here.
            else:
                self.driver=self.create_driver_session(session["id"])

            setattr(self.driver, "dy", self.driver_data)
            setattr(self.driver, "scroll", self.scroll)
            setattr(self.driver, "get_elem", self.get_elem)
            self.driver_data["browser_window"]=self.get_browser_window(self.driver_data)
        return self.driver

    def get_elem(self, 
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
                    return False
            
            try:
                elem=self.get_driver().find_element_by_id(id)
                break
            except BaseException as e:
                if e.__class__.__name__ == "NoSuchElementException":
                    continue
        return elem

    def scroll(self, percent=None):
        from selenium.webdriver.common.keys import Keys
        if percent is None:
            percent=100
        else:
            percent=int(percent)
        scroll_height=int(self.get_driver().execute_script("return document.documentElement.scrollHeight"))

        if self.debug is True:
            print("scroll page height: {}".format(scroll_height))
        if percent < 100:
            scroll_height=int(scroll_height*((percent/100)))

        self.get_driver().execute_script("window.scrollTo(0,{})".format(scroll_height))
        # self.get_driver().find_element_by_css_selector("body").send_keys(Keys.CONTROL, Keys.END)

    def refresh(self, wait_ms=None):
        self.get_driver().refresh()
        if wait_ms is not None:
            time.sleep(float(wait_ms)/1000)

    def browser_focus(self):
        import ctypes
        from ctypes import wintypes
        # print(self.get_window())
        # user32 = ctypes.windll.user32
        pid=self.get_driver().dy["browser_window"]["pid"]
        Windows(debug=self.debug).focus(pid)
        # for window in 
        # Windows().list_windows()
            # print(window)

        

        # h_wnd = user32.GetForegroundWindow()
        # pid = wintypes.DWORD()
        # user32.GetWindowThreadProcessId(h_wnd, ctypes.byref(pid))
        # print(pid.value)

    # def get_window(self, pid):
        # result = None
        # def callback(hwnd, _):
        #     nonlocal result
        #     ctid, cpid = win32process.GetWindowThreadProcessId(hwnd)
        #     if cpid == pid:
        #         result = hwnd
        #         return False
        #     return True
        # win32gui.EnumWindows(callback, None)
        # return result
    

# grid_url = "http://127.0.0.1:4444/wd/hub"
# driver_firefox = webdriver.Remote(grid_url, DesiredCapabilities.FIREFOX)
# driver_chrome = webdriver.Remote(grid_url, DesiredCapabilities.CHROME)


# > tasklist | findstr geckodriver
# geckodriver.exe              22464 RDP-Tcp#83                 2     11,324 K

# > tasklist | findstr chromedriver
# chromedriver.exe              9148 RDP-Tcp#83                 2     14,896 K
