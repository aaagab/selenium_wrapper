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
from selenium.common.exceptions import NoSuchElementException, JavascriptException, StaleElementReferenceException

from ..gpkgs.timeout import TimeOut
from ..gpkgs import message as msg

def get_elem(
    driver, 
    id=None,
    xpath=None, 
    xpath_context=None,
    wait_ms=None,
    error=True
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
                    msg.error("element not found with xpath '{}'".format(xpath))
                else:
                    msg.error("element not found with id '{}'".format(id))
                sys.exit(1)
            else:
                return None

        element=None
        try:
            if xpath is None:
                try:
                    element=driver.find_element(By.ID, id)
                except NoSuchElementException as e:
                    pass
            else:
                if len(xpath) >=2:
                    if xpath[0] == "'" and xpath[-1] == "'":
                        xpath=xpath[1:len(xpath)-1]
                        xpath=xpath.replace("\"", "\\\"")

                try:
                    elems=driver.execute_script("""
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

                    if len(elems) == 1:
                        element=elems[0]
                    elif len(elems) > 0:
                        msg.error("'{}' elements have been found but only one needs to be selected. (use xpath index notation)".format(len(elems)))
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
                    element.is_enabled() and element.is_displayed()
                    return element
        except StaleElementReferenceException:
            continue

    return None

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