#!/usr/bin/env python3
from enum import Enum
from pprint import pprint
import os
import json
import sys
import time

from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException, JavascriptException, StaleElementReferenceException, ElementNotInteractableException

from .windows import Windows

from ..gpkgs.timeout import TimeOut
from ..gpkgs import message as msg
from ..gpkgs.timeout import TimeOut
from ..gpkgs import message as msg

class ElementNotFound(Exception):
    pass

class MouseEvents(str, Enum):
    CLICK="click"
    MOUSEDOWN="mousedown"
    MOUSEOVER="mouseover"
    MOUSEUP="mouseup"

# [{'capabilities': {'acceptInsecureCerts': True,
#                    'browserName': 'firefox',
#                    'browserVersion': '130.0',
#                    'moz:accessibilityChecks': False,
#                    'moz:buildID': '20240829075237',
#                    'moz:geckodriverVersion': '0.31.0',
#                    'moz:headless': False,
#                    'moz:platformVersion': '10.0',
#                    'moz:processID': 9284,
#                    'moz:profile': 'C:\\Users\\gabaaa\\AppData\\Local\\Temp\\rust_mozprofilefUp8CQ',
#                    'moz:shutdownTimeout': 60000,
#                    'moz:webdriverClick': True,
#                    'moz:windowless': False,
#                    'pageLoadStrategy': 'normal',
#                    'platformName': 'windows',
#                    'proxy': {},
#                    'setWindowRect': True,
#                    'strictFileInteractability': False,
#                    'timeouts': {'implicit': 0,
#                                 'pageLoad': 300000,
#                                 'script': 30000},
#                    'unhandledPromptBehavior': 'dismiss and notify',
#                    'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; '
#                                 'rv:130.0) Gecko/20100101 Firefox/130.0'},
#   'id': '087da373-eb62-421f-864d-28cba23cadbf'}]

class Session():
    def __init__(self,
        capabilities:dict,
        id: str,
    ):
        self.capabilities=capabilities
        self.id=id

class NetstatObj():
    def __init__(self, port:int, pid:int, proc_name:str):
        self.port=port
        self.pid=pid
        self.proc_name=proc_name

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)

class DriverData():
    def __init__(self,
        name:str,
        filen:str,
        direpa_drivers:str,
        proc_name:str,
    )->None:
        # self.filenpa_exe=
        self.name=name
        self.filenpa_exe=os.path.join(direpa_drivers, filen)
        self.proc_name=proc_name

class BrowserData():
    def __init__(self,
        name:str,
        driver_data:DriverData,
        filen_browser:str,
        proc_name:str,
        direpa_logs:str,
        direpa_extensions:str,
        log_label:str,
        capability_name:str,
        session_name:str,


        # filen_driver:str,
        # direpa_drivers:str,
        # driver_proc_name:str,
        # driver_label:str,

    )-> None:
        self.name=name
        self.driver_data=driver_data
        # self.filen_driver=filen_driver
        self.session_name=session_name
        self.filen_browser=filen_browser
        self.proc_name=proc_name
        # self.driver_proc_name=driver_proc_name
        self.filenpa_log=os.path.join(direpa_logs, "client_{}.txt".format(self.name))
        self.session:Session|None=None
        self.direpa_extensions=os.path.join(direpa_extensions, self.name)
        self.dwebdriver_args=[
            f"-Dwebdriver.{self.driver_data.name}.driver={self.driver_data.filenpa_exe}",
            f"-Dwebdriver.{log_label}.logfile={self.filenpa_log}",
            f"-Dwebdriver.{log_label}.loglevel=DEBUG",
        ]
        self.capabilities:dict[str, str]=getattr(DesiredCapabilities, capability_name)
        self.pid:int|None=None

    
    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
    
class Browser():
    def __init__(
        self, 
        driver:WebDriver,
        data:BrowserData,
        debug:bool,
    ):
        self.driver=driver
        self.data=data
        self.debug=debug

    def refresh(self, wait_ms:int|None=None):
        self.driver.refresh()
        if wait_ms is not None:
            time.sleep(float(wait_ms)/1000)

    def get_elem(
        self,
        id:str|None=None,
        xpath:str|None=None, 
        xpath_context:str|None=None,
        wait_ms:int|None=2000,
        error:bool=True,
    ):
        if wait_ms is None:
            wait_ms=2000

        timer=TimeOut(wait_ms, unit="milliseconds").start()

        if id is None and xpath is None:
            msg.error("When finding an element, at id or xpath must be provided", trace=True, exit=1)

        if xpath_context is None:
            xpath_context="document"

        while True:
            if timer.has_ended(pause=.001):
                if error is True:
                    if id is None:
                        raise ElementNotFound("element not found with xpath '{}'".format(xpath))
                    else:
                        raise ElementNotFound("element not found with id '{}'".format(id))
                else:
                    return None

            element=None
            try:
                if xpath is None:
                    try:
                        element=self.driver.find_element(By.ID, id)
                    except NoSuchElementException as e:
                        pass
                else:
                    if len(xpath) >=2:
                        if xpath[0] == "'" and xpath[-1] == "'":
                            xpath=xpath[1:len(xpath)-1]
                            xpath=xpath.replace("\"", "\\\"")

                    try:
                        elems=self.driver.execute_script("""
                            results=document.evaluate(\"{}\", {}, null, XPathResult.ORDERED_NODE_ITERATOR_TYPE, null);
                            var elements = []; 
                            var element= results.iterateNext(); 
                            while (element) {{
                                elements.push(element);
                                element = results.iterateNext();
                            }}
                            return elements;
                        """.format(
                            xpath,
                            xpath_context,
                        ))

                        if elems is None:
                            continue
                        elif len(elems) == 1:
                            element=elems[0]
                        elif len(elems) > 0:
                            msg.error("for xpath '{}': '{}' elements have been found but only one needs to be selected. (use xpath index notation)".format(xpath, len(elems)))
                            index=1
                            for elem in elems:
                                print("    {}- tag={} text={}".format(
                                    index,
                                    elem.tag_name,
                                    elem.text,
                                ))
                                index+=1
                            sys.exit(1)

                    except JavascriptException:
                        msg.error("Wrong javascript syntax for xpath '{}' and context '{}'.".format(xpath, xpath_context))
                        raise

                if element is not None:
                    element.is_enabled() and element.is_displayed() #type:ignore
                    if isinstance(element, WebElement):
                        return element
                    else:
                        raise Exception("Unknown type for WebElement.")
            except StaleElementReferenceException:
                continue

        return None

    def send_js_event(
        self, 
        event_str:MouseEvents,
        id:str|None=None,
        xpath:str|None=None,
        xpath_context:str|None=None,
        wait_ms:int|None=None,
        pause_ms:int|None=None
    ):
        if pause_ms is not None:
            time.sleep(float(pause_ms)/1000)

        element=self.get_elem(
            id=id,
            xpath=xpath,
            xpath_context=xpath_context,
            wait_ms=wait_ms,
        )

        self.driver.execute_script(f"var clickEvent=document.createEvent('MouseEvents'); clickEvent.initEvent('{event_str.value}', true, true); arguments[0].dispatchEvent(clickEvent);", element)

    def scroll_to(
        self,
        id:str|None=None,
        xpath:str|None=None,
        xpath_context:str|None=None,
        wait_ms:int|None=None,
        pause_ms:int|None=None
    ):
        if pause_ms is not None:
            time.sleep(float(pause_ms)/1000)

        element=self.get_elem(
            id=id,
            xpath=xpath,
            xpath_context=xpath_context,
            wait_ms=wait_ms,
        )

        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)

    def scroll(
        self,
        debug:bool, 
        percent:int|None=None, 
        pause_ms:int|None=None,
    ):
        from selenium.webdriver.common.keys import Keys
        if pause_ms is not None:
            time.sleep(float(pause_ms)/1000)

        if percent is None:
            percent=100
        else:
            percent=int(percent)
        scroll_height=int(self.driver.execute_script("return document.documentElement.scrollHeight"))

        if debug is True:
            print("scroll page height: {}".format(scroll_height))
        if percent < 100:
            scroll_height=int(scroll_height*((percent/100)))
        self.driver.execute_script("window.scrollTo(0,{})".format(scroll_height))

    def browser_focus(self, debug:bool):
        pid=self.data.pid
        if pid is None:
            raise Exception(f"Can't focus browser {self.data.name} when its PID is None")
        Windows(debug=debug).focus(pid)