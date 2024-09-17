#!/usr/bin/env python3
from pprint import pprint
from typing import cast
import os
import sys

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver

from selenium.webdriver.remote.remote_connection import LOGGER
import logging

from .processes import Processes, Proc

from .objs import BrowserData, DriverData

LOGGER.setLevel(logging.WARNING)

from urllib3.connectionpool import log as urllibLogger
urllibLogger.setLevel(logging.WARNING)

def get_browser_data(browser_names, browsers_data, name):
    if name not in browser_names:
        print("browser '{}' not found in {}".format(name, browser_names))
        sys.exit(1)
    return browsers_data[name]

def get_browsers_data(
    load_extensions:bool,
    direpa_drivers:str,
    direpa_extensions:str,
    direpa_logs:str,
    browser_names:list[str], 
):
    browsers_data:dict[str, BrowserData]=dict()
    for name in browser_names:
        capability_name=name.upper()
        proc_name:str|None=None
        driver_name:str|None=None
        session_name:str|None=None
        if name == "firefox":
            driver_name="gecko"
            session_name=name
            if sys.platform == "win32":
                filen_browser="firefox.exe"
                proc_name=filen_browser
                filen_driver="geckodriver.exe"
            elif sys.platform == "linux":
                filen_browser="firefox"
                proc_name="firefox-bin"
                filen_driver="geckodriver"
        elif name == "chrome":
            driver_name=name
            session_name=name
            if sys.platform == "win32":
                filen_browser="chrome.exe"
                proc_name=filen_browser
                filen_driver="chromedriver.exe"
            elif sys.platform == "linux": 
                filen_browser="chrome"
                proc_name=filen_browser
                filen_driver="chromedriver"
        elif name == "edge":
            session_name="MicrosoftEdge"
            if sys.platform != "win32":
                raise Exception(f"browser '{name}' is only available on Windows.")
            driver_name=name
            filen_browser="msedge.exe"
            proc_name=filen_browser
            capability_name="EDGE"
            filen_driver="msedgedriver.exe"

        if filen_driver is None:
            raise Exception(f"filen_driver has not been set for browser '{name}'")

        if driver_name is None:
            raise Exception(f"driver_name has not been set for browser '{name}'")

        if proc_name is None:
            raise Exception(f"proc_name has not been set for browser '{name}'")
    
        if session_name is None:
            raise Exception(f"session_name has not been set for browser '{name}'")

        log_label=name
        driver_proc_name=filen_driver

        driver_data=DriverData(
            direpa_drivers=direpa_drivers,
            filen=filen_driver,
            name=driver_name,
            proc_name=driver_proc_name,
        )

        browser_data=BrowserData(
            name=name,
            driver_data=driver_data,
            filen_browser=filen_browser,
            proc_name=proc_name,
            direpa_logs=direpa_logs,
            direpa_extensions=direpa_extensions,
            log_label=log_label,
            capability_name=capability_name,
            session_name=session_name,
        )

        browsers_data[name]=browser_data

        if name == "chrome":
            chrome_options=ChromeOptions()
            if load_extensions is True:
                for elem in sorted(os.listdir(browser_data.direpa_extensions)):
                    path_rel, ext=os.path.splitext(elem)
                    if ext == ".crx":
                        path_extension=os.path.join(browser_data.direpa_extensions, elem)
                        chrome_options.add_extension(path_extension)
            browser_data.capabilities=chrome_options.to_capabilities()
        elif name == "firefox":
            options = webdriver.FirefoxOptions()
            fp = webdriver.FirefoxProfile()
            fp.set_preference("marionette.actors.enabled", True)
            options.profile=fp
            options.set_capability("marionette", True)
            # https://firefox-source-docs.mozilla.org/testing/geckodriver/TraceLogs.html
            options.log.level = "trace" #type:ignore
            options.add_argument("-devtools")
            browser_data.capabilities=options.to_capabilities()
        elif name == "edge":
            if sys.platform == "win32":
                options = webdriver.EdgeOptions()
                # options.use_chromium = True
                browser_data.capabilities=options.to_capabilities()

                # add that 
                # https://stackoverflow.com/questions/70794746/ms-way-to-python-code-edge-session-using-selenium-4
                # options = webdriver.
                # options.ignore_protected_mode_settings = True
                # browser_data.capabilities=options.to_capabilities()
                    
                # with profile fp.set_preference("marionette.actors.enabled", False) not crashing working
    return browsers_data

def get_new_webdriver_session(
    grid_url:str,
    session_id:str,
):
    # Save the original function, so we can revert our patch
    org_command_execute = RemoteWebDriver.execute

    def new_command_execute(self, command, params=None):
        if command == "newSession":
            # Mock the response
            return {'success': 0, 'value': None, 'sessionId': session_id}
        else:
            return org_command_execute(self, command, params) #type:ignore

    # Patch the function before creating the driver object
    RemoteWebDriver.execute = new_command_execute #type:ignore

    new_driver = webdriver.Remote(command_executor=grid_url, desired_capabilities={})
    
    new_driver.session_id =session_id #type:ignore

    # Replace the patched function with original function
    RemoteWebDriver.execute = org_command_execute #type:ignore

    return new_driver

def close_browser_driver(
    debug:bool, 
    driver_proc_name:str,
    processes_obj:Processes,
):
    if debug is True:
        print("Closing Selenium Driver '{}'".format(driver_proc_name))
    for proc in processes_obj.from_name(driver_proc_name):
        processes_obj.kill(pid=proc.pid)

def close_selenium_browsers(
    debug:bool,
    browser_name:str,
    processes_obj:Processes,
    selenium_browsers:list[Proc],
):
    if debug is True:
        print("Closing Selenium Browsers '{}'".format(browser_name))
    
    for browser in selenium_browsers:
        pid:int|None=None
        if sys.platform == "win32":
            if browser_name == "firefox":
                pid=browser.children[0].pid
            else:
                pid=browser.pid
        elif sys.platform == "linux":
            pid=browser.pid

        if pid is not None:
            processes_obj.kill(pid)
