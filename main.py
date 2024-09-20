#!/usr/bin/env python3
from typing import Callable
import json
from pprint import pprint
import json
import re
import os
import sys
import subprocess
import shlex
import time
import traceback
import yaml

from selenium.webdriver.common.by import By

# pip3 install pyautogui

def get_accepted_keys():
    return ['\t', '\n', '\r', ' ', '!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-', '.', '/', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^', '_', '`', 'a', 'b', 'c', 'd', 'e','f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '{', '|', '}', '~', 'accept', 'add', 'alt', 'altleft', 'altright', 'apps', 'backspace', 'browserback', 'browserfavorites', 'browserforward', 'browserhome', 'browserrefresh', 'browsersearch', 'browserstop', 'capslock', 'clear', 'convert', 'ctrl', 'ctrlleft', 'ctrlright', 'decimal', 'del', 'delete', 'divide', 'down', 'end', 'enter', 'esc', 'escape', 'execute', 'f1', 'f10', 'f11', 'f12', 'f13', 'f14', 'f15', 'f16', 'f17', 'f18', 'f19', 'f2', 'f20', 'f21', 'f22', 'f23', 'f24', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'final', 'fn', 'hanguel', 'hangul', 'hanja', 'help', 'home', 'insert', 'junja', 'kana', 'kanji', 'launchapp1', 'launchapp2', 'launchmail', 'launchmediaselect', 'left', 'modechange', 'multiply', 'nexttrack', 'nonconvert', 'num0', 'num1', 'num2', 'num3', 'num4', 'num5', 'num6', 'num7', 'num8', 'num9', 'numlock', 'pagedown', 'pageup', 'pause', 'pgdn', 'pgup', 'playpause', 'prevtrack', 'print', 'printscreen', 'prntscrn', 'prtsc', 'prtscr', 'return', 'right', 'scrolllock', 'select', 'separator', 'shift', 'shiftleft', 'shiftright', 'sleep', 'space', 'stop', 'subtract', 'tab', 'up', 'volumedown', 'volumemute', 'volumeup', 'win', 'winleft', 'winright', 'yen', 'command', 'option', 'optionleft', 'optionright']

if __name__ == "__main__":
    import sys, os
    import typing
    import importlib
    direpa_script=os.path.dirname(os.path.realpath(__file__))
    direpa_script_parent=os.path.dirname(direpa_script)
    module_name=os.path.basename(os.path.dirname(os.path.realpath(__file__)))
    sys.path.insert(0, direpa_script_parent)
    if typing.TYPE_CHECKING:
        import __init__ as package #type:ignore
        from __init__ import MouseEvents
    pkg:"package" = importlib.import_module(module_name) #type:ignore
    del sys.path[0]

    if sys.platform == "win32":
        import pyautogui
    elif sys.platform == "linux":
        pass
    else:
        raise NotImplementedError(f"Platform not support '{sys.platform}'")

    def seed(pkg_major, direpas_configuration:dict|None, fun_auto_migrate:Callable):
        fun_auto_migrate()

    filenpa_gpm=os.path.join(direpa_script, "gpm.json")
    etconf=pkg._Etconf(filenpa_gpm=filenpa_gpm, enable_dev_conf=False, tree=dict(), seed=seed)

    args=pkg.Nargs(
        options_file="config/options.yaml",
        metadata=dict(executable="selenium_wrapper"),
        path_etc=etconf.direpa_configuration,
        substitute=True,
    ).get_args()

    debug=args.debug._here

    filenpa_settings=os.path.join(etconf.direpa_configuration, "settings.json")

    if args.selenium_options._here:
        srv=pkg.SeleniumServer(filenpa_settings=filenpa_settings, debug=debug)
        print()
        print("## Standalone")
        cmd=[ srv.filenpa_java, "-jar", srv.filenpa_selenium_server, "-help" ]
        subprocess.run(cmd)
        print()
        print("## -role hub")
        cmd=[ srv.filenpa_java, "-jar", srv.filenpa_selenium_server, "-role", "hub", "-help" ]
        subprocess.run(cmd)
        print()
        print("## -role node")
        cmd=[ srv.filenpa_java, "-jar", srv.filenpa_selenium_server, "-role", "node", "-help" ]
        subprocess.run(cmd)
        sys.exit(0)
    elif args.show_grid._here:
        srv=pkg.SeleniumServer(filenpa_settings=filenpa_settings, debug=debug)
        srv.show_grid()
        sys.exit(0)
    elif args.exit._here:
        srv=pkg.SeleniumServer(filenpa_settings=filenpa_settings, debug=debug)
        srv.exit_grid()
        sys.exit(0)

    if args.connect._here:
        srv=pkg.SeleniumServer(filenpa_settings=filenpa_settings, load_extensions=args.connect.extensions._here, debug=debug)

        release_keys=[]

        try:
            cmd_pid=srv.windows.get_active()

            if args.connect.extensions.accessibility._here and args.connect.browser._value != "chrome":
                print("To use accessibility plugin, please use chrome browser.")
                sys.exit(1)

            srv.connect(args.connect.browser._value, close=args.connect.browser.close._here, clear_cache=args.connect.browser.clear_cache._here)

            if args.connect.browser.info._here:
                print(srv.get_browser().data.to_json())

            if args.connect.focus._here:
                srv.get_browser().browser_focus(debug=debug)

            if args.connect.url._here:
                url_alias=args.connect.url.alias._value
                if url_alias is None:
                    url_alias="hostname_url"

                params=[]
                for arg in args.connect.url.param._branches:
                    if arg._here is True:
                        param=(arg._value, )
                        if arg.value._here is True:
                            param+=(arg.value._value,)
                        params.append(param)

                url=pkg.geturl(
                    args.connect.url._value,
                    alias=url_alias, 
                    direpa_project=args.connect.url.path_project._value,
                    hostname_path=args.connect.url.hostname._value,
                    params=params,
                )

                if args.connect.url.insecure._here:
                    if srv.get_browser().data.name == "firefox":
                        confirmCert=False
                        try:
                            srv.get_browser().driver.get(url)
                        except BaseException as e:
                            if e.__class__.__name__ == "InsecureCertificateException":
                                print("Override certificate Exception")
                                confirmCert=True
                            else:
                                print(traceback.format_exc())

                        if confirmCert is True:
                            srv.get_browser().driver.find_element(By.ID, "advancedButton").click()
                            srv.get_browser().driver.find_element(By.ID, "exceptionDialogButton").click()
                    elif srv.get_browser().data.name == "chrome":
                        srv.get_browser().driver.get(url)
                        advanced_button=srv.get_browser().get_elem(id="details-button", error=False, wait_ms=800)
                        if advanced_button is not None:
                            advanced_button.click()
                            srv.get_browser().driver.find_element(By.ID, "proceed-link").click()
                    else:
                        print("--insecure flag needs to be implemented for browser '{}'".format(srv.get_browser().data.name))
                        sys.exit(1)
                else:
                    srv.get_browser().driver.get(url)


            if args.connect.refresh._here:
                srv.get_browser().refresh(wait_ms=args.connect.refresh.wait._value)

            if args.connect.console._here:
                if args.connect.focus._here is False:
                    srv.get_browser().browser_focus(debug=debug)

                if sys.platform == "win32":
                    pyautogui.hotkey('ctrl', 'shift', 'k')
                elif sys.platform == "linux":
                    os.system(f"xdotool key 'ctrl+shift+k'")
                
                if args.connect.focus._here is False:
                    srv.windows.focus(cmd_pid)

            accepted_keys=None

            for cmd_arg in args.connect._args:
                if cmd_arg._name == "key":
                    if accepted_keys is None:
                        accepted_keys=get_accepted_keys()

                    if cmd_arg._value.lower() not in accepted_keys:
                        pkg.msg.error("key '{}' not found in {}".format(cmd_arg._value, accepted_keys), exit=1)

                    if cmd_arg.pause._value is not None:
                        time.sleep(float(cmd_arg.pause._value)/1000)

                    if cmd_arg.down._here:
                        if sys.platform == "win32":
                            pyautogui.keyDown(cmd_arg._value)
                        elif sys.platform == "linux":
                            os.system(f"xdotool keydown {cmd_arg._value}")
                        release_keys.append(cmd_arg._value)
                    elif cmd_arg.up._here:
                        if sys.platform == "win32":
                            pyautogui.keyUp(cmd_arg._value)
                        elif sys.platform == "linux":
                            os.system(f"xdotool keyup {cmd_arg._value}")
                        if cmd_arg._value in release_keys:
                            release_keys.remove(cmd_arg._value)
                    else:
                        if sys.platform == "win32":
                            pyautogui.press(cmd_arg._value)
                        else:
                            os.system(f"xdotool key {cmd_arg._value}")

                elif cmd_arg._name == "keys":
                    if accepted_keys is None:
                        accepted_keys=get_accepted_keys()

                    if cmd_arg.pause._value is not None:
                        time.sleep(float(cmd_arg.pause._value)/1000)

                    for key in cmd_arg._values:
                        if key.lower() not in accepted_keys:
                            pkg.msg.error("key '{}' not found in {}".format(key, accepted_keys), exit=1)

                    if sys.platform == "win32":
                        pyautogui.hotkey(*cmd_arg._values)
                    elif sys.platform == "linux":
                        os.system(f"xdotool key {"+".join(cmd_arg._values)}")
                        
                elif cmd_arg._name == "write":
                    if cmd_arg.pause._value is not None:
                        time.sleep(float(cmd_arg.pause._value)/1000)
                    if sys.platform == "win32":
                        pyautogui.write(cmd_arg._value)
                    else:
                        os.system(f"xdotool type {cmd_arg._value}")
                        
                elif cmd_arg._name == "scroll":
                    srv.get_browser().scroll(percent=cmd_arg._value, pause_ms=cmd_arg.pause._value, debug=debug)
                elif cmd_arg._name == "scroll_to":
                    srv.get_browser().scroll_to(
                        id=cmd_arg.id._value, 
                        xpath=cmd_arg.xpath._value,
                        xpath_context=cmd_arg.xpath.context._value,
                        wait_ms=cmd_arg.wait._value,
                        pause_ms=cmd_arg.pause._value,
                    ) 
                elif cmd_arg._name == "event":
                    event_str:MouseEvents|None=None

                    for event_arg in cmd_arg.name._args:
                        event_str=MouseEvents(event_arg._name)

                    if event_str is None:
                        pkg.msg.error("Please choose an event name.")
                        sys.exit(1)

                    srv.get_browser().send_js_event(
                        event_str=event_str,
                        id=cmd_arg.id._value, 
                        xpath=cmd_arg.xpath._value,
                        xpath_context=cmd_arg.xpath.context._value,
                        wait_ms=cmd_arg.wait._value,
                        pause_ms=cmd_arg.pause._value,
                    )                    
                elif cmd_arg._name == "select":
                    if cmd_arg.pause._value is not None:
                        time.sleep(float(cmd_arg.pause._value)/1000)
                    
                    elem=srv.get_browser().get_elem(
                        id=cmd_arg.id._value, 
                        xpath=cmd_arg.xpath._value,
                        xpath_context=cmd_arg.xpath.context._value,
                        wait_ms=cmd_arg.wait._value,
                        error=True,
                    )
                    if elem is None:
                        raise Exception("select elem returns None")
                    if cmd_arg.value._value is not None:
                        pkg.send_keys(elem, cmd_arg.value._value)
                elif cmd_arg._name == "click":
                    if cmd_arg.pause._value is not None:
                        time.sleep(float(cmd_arg.pause._value)/1000)
                    
                    elem=srv.get_browser().get_elem(
                        id=cmd_arg.id._value, 
                        xpath=cmd_arg.xpath._value,
                        xpath_context=cmd_arg.xpath.context._value,
                        wait_ms=cmd_arg.wait._value,
                        error=True,
                    )
                    if elem is None:
                        raise Exception("select elem returns None")


                    if cmd_arg.file._here is True:
                        pkg.send_keys(elem, cmd_arg.file._value)
                    else:
                        pkg.send_keys(elem, "")
                        elem.click()            

            if args.connect.extensions.accessibility._here:
                if sys.platform == "win32":
                    import pyautogui
                    # you have to take a screenshot of the button
                    extn = pyautogui.locateOnScreen(os.path.join(srv.get_browser().data.direpa_extensions, "site_improve_button.png"))
                    offset=15
                    if extn is None:
                        print("Not Found button.png")
                        sys.exit(1)
                    time.sleep(.5)
                    pyautogui.click(x=extn[0]+offset,y=extn[1]+offset,clicks=1,interval=0.0,button="left")
                else:
                    raise NotImplemented(f"extensions accessibility not implemented on platform '{sys.platform}'")

            if args.connect.cmd._here:
                srv.windows.focus(cmd_pid)

            if args.connect.logs._here:
                if srv.get_browser().data.name == "chrome":
                    wait_ms=args.connect.logs.wait._value
                    if wait_ms is not None:
                        time.sleep(float(wait_ms)/1000)
                    for entry in srv.get_browser().driver.get_log('browser'):
                        print(json.dumps(entry))
                else:
                    pkg.msg.error(f"--logs is not implemented for browser '{srv.get_browser().data.name}'", exit=1)
                
        except:
            srv.windows.focus(cmd_pid)
            raise
        finally:
            for key in release_keys:
                if sys.platform == "win32":
                    pyautogui.keyUp(key)
                elif sys.platform == "linux":
                    os.system(f"xdotool keyup {key}")
