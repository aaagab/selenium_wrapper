#!/usr/bin/env python3
import json
from pprint import pprint
import re
import os
import sys
import subprocess
import shlex
import time
import traceback

import pyautogui

# pip3 install pyautogui

# mklink /H "C:\Users\john\Desktop\data\bin\selenium.py" "C:\Users\john\Desktop\data\bin\selenium\main.py"

if __name__ == "__main__":
    import sys, os

    import importlib
    direpa_script=os.path.dirname(os.path.realpath(__file__))
    direpa_script_parent=os.path.dirname(direpa_script)
    module_name=os.path.basename(os.path.dirname(os.path.realpath(__file__)))
    sys.path.insert(0, direpa_script_parent)
    pkg=importlib.import_module(module_name)
    del sys.path[0]

    args, dy_app=pkg.Options(filenpa_app="gpm.json", filenpa_args="config/options.json", allow_empty=True).get_argsns_dy_app()

    debug=args.debug.here
    direpa_media="Y:\\bin\\selenium_media"

    if args.selenium_options.here:
        srv=pkg.SeleniumServer(debug=debug, direpa_media=direpa_media)
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
    elif args.examples.here:
        print("""
selenium_wrapper --connect --driver chrome --accessibility --refresh --url https://www.example.com/e/example/login
selenium_wrapper --connect --driver firefox --url departments --path-project A:\wrk\e\example\1\src --params "{'fruit':'apple','region':'greenland'}"
selenium_wrapper --connect --driver firefox --url departments --hostname https://www.example.com/e/example
selenium_wrapper --connect --driver firefox --url events/create --select "[{'frmEventDescription': 'mytext'}]" --delay 1000
selenium_wrapper --connect --driver firefox --url events/create --select 'frmEventDescription' --delay 1000
        """)
        sys.exit(0)
    elif args.gui.here:
        srv=pkg.SeleniumServer(debug=debug, direpa_media=direpa_media)
        srv.show_gui()
        sys.exit(0)
    elif args.exit.here:
        srv=pkg.SeleniumServer(debug=debug, direpa_media=direpa_media)
        srv.reset()
        sys.exit(0)
    elif args.reset.here:
        srv=pkg.SeleniumServer(debug=debug, direpa_media=direpa_media)
        srv.reset(args.drivers.values)

    if args.connect.here or args.accessibility.here:
        srv=pkg.SeleniumServer(accessibility=args.accessibility.here, debug=debug, direpa_media=direpa_media)
        cmd_pid=None

        if args.cmd.here:
            cmd_pid=srv.windows.get_active()


        if args.accessibility.here and args.driver.value != "chrome":
            print("To use accessibility plugin, please use chrome driver.")
            sys.exit(1)
        # if args.connect.here:
        srv.connect(args.driver.value, reset=args.reset.here)
        # elif args.accessibility.here:
            # print("Here")
            # sys.exit()
            # srv.connect("chrome", reset=args.reset.here)

        if args.focus.here:
            srv.browser_focus()

        if args.url.here:
            url_alias=args.url_alias.value
            if url_alias is None:
                url_alias="hostname_url"
            url=pkg.geturl(
                args.url.value,
                alias=url_alias, 
                direpa_project=args.path_project.value,
                hostname_path=args.hostname.value,
                params=args.params.value,
            )

            if args.insecure.here:
                if srv.get_driver().dy["name"] == "firefox":
                    confirmCert=False
                    try:
                        srv.get_driver().get(url)
                    except BaseException as e:
                        if e.__class__.__name__ == "InsecureCertificateException":
                            print("Override certificate Exception")
                            confirmCert=True
                        else:
                            print(traceback.format_exc())

                    if confirmCert is True:
                        srv.get_driver().find_element_by_id("advancedButton").click()
                        srv.get_driver().find_element_by_id("exceptionDialogButton").click()
                elif srv.get_driver().dy["name"] == "chrome":
                    srv.get_driver().get(url)
                    advanced_button=srv.get_driver().get_elem("details-button", error=False, wait_ms=800)
                    if advanced_button is not None:
                        advanced_button.click()
                        srv.get_driver().find_element_by_id("proceed-link").click()

                    # print(advanced_button)
                else:
                    print("--insecure flag needs to be implemented for driver '{}'".format(srv.get_driver().dy["name"]))
                    sys.exit(1)
            else:
                srv.get_driver().get(url)




        if args.refresh.here:
            srv.refresh(wait_ms=args.refresh.value)

        if args.scroll.here:
            srv.get_driver().scroll(percent=args.scroll.value, wait_ms=args.delay.value)

        if args.select.here:
            if args.delay.value is not None:
                time.sleep(float(args.delay.value)/1000)

            if isinstance(args.select.value, str):
                elem=srv.get_elem(args.select.value)
                elem.send_keys("")
            elif isinstance(args.select.value, list):
                for dy in args.select.value:
                    if isinstance(dy, dict):
                        key=next(iter(dy))
                        elem=srv.get_elem(key)
                        elem.send_keys(dy[key])

        if args.console.here:
            if args.focus.here is False:
                srv.browser_focus()
            pyautogui.hotkey('ctrl', 'shift', 'k')

        if args.accessibility.here:
            import pyautogui
            # you have to take a screenshot of the button
            extn = pyautogui.locateOnScreen(os.path.join(srv.driver_data["direpa_extensions"], "site_improve_button.png"))
            offset=15
            if extn is None:
                print("Not Found button.png")
                sys.exit(1)
            pyautogui.click(x=extn[0]+offset,y=extn[1]+offset,clicks=1,interval=0.0,button="left")

        if args.driver_info.here:
            pprint(srv.get_driver().dy)

        if args.cmd.here:
            srv.windows.focus(cmd_pid)
           

        # if args.clear_cache.here:
        #     driver=srv.get_driver()
        #     if driver.dy["name"] == "firefox": 
        #         print("continue")

        #         dialog_selector = '#dialogOverlay-0 > groupbox:nth-child(1) > browser:nth-child(2)'
        #         accept_dialog_script = (
        #             f"const browser = document.querySelector('{dialog_selector}');" +
        #             "browser.contentDocument.documentElement.querySelector('#clearButton').click();"
        #         )
        #         driver.get('about:preferences#privacy')
        #         driver.get_elem("clearSiteDataButton", wait_ms=3000).click()
        #         # driver.find_element_by_css_selector("#clearButton")
        #         driver.get_elem("clearButton", wait_ms=3000).click()
        #         sys.exit()
        #         wait = WebDriverWait(driver, timeout)

        #         # Click the "Clear Data..." button under "Cookies and Site Data".
        #         wait.until(get_clear_site_data_button)
        #         get_clear_site_data_button(driver).click()

        #         # Accept the "Clear Data" dialog by clicking on the "Clear" button.
        #         wait.until(get_clear_site_data_dialog)
        #         driver.execute_script(accept_dialog_script)

        #         # Accept the confirmation alert.
        #         wait.until(EC.alert_is_present())
        #         alert = Alert(driver)
        #         alert.accept()



   


      


        # srv.window_focus("cmd.exe")
        # srv.window_focus("putty.exe")
        # srv.window_focus("Code.exe")


        # # Test section
        # srv.get_elem("email_input")

        # driver_name=dy_app.get_arg_values("--driver", ret="value", get_values=False)
        # if driver_name is not None:
        #     # print(srv.get_driver().dy["session"]["id"])
        #     # print(srv.get_driver().dy["browser_session"])
        #     # print(srv.get_driver().dy["browser_window"])

        #     srv.browser_focus()
        #     srv.get_driver().refresh()
