#!/usr/bin/env python3
from pprint import pprint
import os
import sys

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

from selenium.webdriver.remote.remote_connection import LOGGER
import logging

LOGGER.setLevel(logging.WARNING)

from urllib3.connectionpool import log as urllibLogger
urllibLogger.setLevel(logging.WARNING)

def get_driver_data(driver_names, drivers_data, name):
    if name not in driver_names:
        print("driver '{}' not found in {}".format(name, driver_names))
        sys.exit(1)
    return drivers_data[name]

def get_drivers_data(
    load_extensions=False,
    direpa_drivers=None,
    direpa_extensions=None,
    direpa_logs=None,
    driver_names=[], 
):
    drivers_data=dict()
    for name in driver_names:
        drivers_data[name]=dict()
        driver=drivers_data[name]

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
        # elif name == "msedge":
        #     browser_name="msedge"
        #     filen_browser="msedge.exe"
        #     capability_name="EDGE"
        #     session_proc_name="Msedge"
        #     filen_exe="msedgedriver.exe"
        elif name == "edge":
            # browser_name="MicrosoftEdge"
            # session_proc_name="System"
            # filen_exe="MicrosoftWebDriver.bat"
            # driver_proc_name=filen_exe.replace(".bat", ".exe")
            browser_name="msedge"
            filen_browser="msedge.exe"
            capability_name="EDGE"
            session_proc_name="Msedge"
            filen_exe="msedgedriver.exe"

        if log_label is None:
            log_label=driver_label

        if session_proc_name is None:
            session_proc_name=filen_exe

        if driver_proc_name is None:
            driver_proc_name=filen_exe

        driver["name"]=name
        driver["filen_exe"]=filen_exe
        driver["filenpa_exe"]=os.path.join(direpa_drivers, filen_exe)
        driver["filen_browser"]=filen_browser
        driver["browser_name"]=browser_name
        driver["driver_proc_name"]=driver_proc_name
        driver["session_proc_name"]=session_proc_name
        driver["filenpa_log"]=os.path.join(direpa_logs, "client_{}.txt".format(name))
        driver["session"]=None
        driver["direpa_extensions"]=os.path.join(direpa_extensions, driver["name"])

        driver["dwebdriver_args"]="-Dwebdriver.{driver_label}.driver={filenpa_exe}\n-Dwebdriver.{log_label}.logfile={filenpa_log}\n-Dwebdriver.{log_label}.loglevel=DEBUG".format(
            driver_label=driver_label,
            log_label=log_label, 
            filenpa_exe=driver["filenpa_exe"],
            filenpa_log=driver["filenpa_log"],    
        ).splitlines()

        driver["capabilities"]=getattr(DesiredCapabilities, capability_name)

        if name == "chrome":
            chrome_options=ChromeOptions()
            if load_extensions is True:
                for elem in sorted(os.listdir(driver["direpa_extensions"])):
                    path_rel, ext=os.path.splitext(elem)
                    if ext == ".crx":
                        path_extension=os.path.join(driver["direpa_extensions"], elem)
                        chrome_options.add_extension(path_extension)
            driver["capabilities"]=chrome_options.to_capabilities()
        elif name == "iexplorer":
            # solve issue:  Protected Mode settings are not the same for all zones.
            options = webdriver.IeOptions()
            options.ignore_protected_mode_settings = True
            # options.set_capability("marionette", True)

            driver["capabilities"]=options.to_capabilities()
        elif name == "firefox":
            options = webdriver.FirefoxOptions()
            fp = webdriver.FirefoxProfile()
            fp.set_preference("marionette.actors.enabled", True)
            driver["profile"]=fp
            options.profile=fp
            options.set_capability("marionette", True)
            # https://firefox-source-docs.mozilla.org/testing/geckodriver/TraceLogs.html
            options.log.level = "trace"
            options.add_argument("-devtools")
            driver["capabilities"]=options.to_capabilities()

        elif name == "edge":
            options = webdriver.EdgeOptions()
            options.use_chromium = True
            driver["capabilities"]=options.to_capabilities()

            # add that 
            # https://stackoverflow.com/questions/70794746/ms-way-to-python-code-edge-session-using-selenium-4
            # options = webdriver.
            # options.ignore_protected_mode_settings = True
            # driver["capabilities"]=options.to_capabilities()
                
            # with profile fp.set_preference("marionette.actors.enabled", False) not crashing working
    return drivers_data

def get_new_driver_session(
    grid_url=None,
    session_id=None,
):
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

    new_driver = webdriver.Remote(command_executor=grid_url, desired_capabilities={})
    new_driver.session_id = session_id

    # Replace the patched function with original function
    RemoteWebDriver.execute = org_command_execute

    return new_driver

def close_driver(
    debug=False, 
    driver_proc_name=None,
    processes_obj=None,
):
    if debug is True:
        print("Close Selenium Driver '{}'".format(driver_proc_name))
    if driver_proc_name in processes_obj.procs_by_name:
        processes_obj.kill(driver_proc_name)

def close_driver_browsers(
    debug=False,
    driver_name=None,
    filen_browser=None,
    processes_obj=None,
    selenium_browsers=dict(),
):
    if debug is True:
        print("Close Selenium Browsers '{}'".format(filen_browser))
    
    for browser in selenium_browsers:
        pid=None
        if driver_name == "firefox":
            pid=browser["node"].nodes[0].dy["pid"]
        else:
            pid=browser["pid"]
        processes_obj.kill(pid)
        pass
