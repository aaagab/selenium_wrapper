#!/usr/bin/env python3
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

import pyautogui


from selenium.webdriver.common.by import By


# pip3 install pyautogui

if __name__ == "__main__":
    import sys, os

    import importlib
    direpa_script=os.path.dirname(os.path.realpath(__file__))
    direpa_script_parent=os.path.dirname(direpa_script)
    module_name=os.path.basename(os.path.dirname(os.path.realpath(__file__)))
    sys.path.insert(0, direpa_script_parent)
    pkg=importlib.import_module(module_name)
    del sys.path[0]

    # args, dy_app=pkg.Options(filenpa_app="gpm.json", filenpa_args="config/options.json", allow_empty=True, cli_expand=True).get_argsns_dy_app()

    args=pkg.Nargs(
        options_file="config/options.yaml",
        metadata=dict(executable="selenium_wrapper"),
        substitute=True,
    ).get_args()

    debug=args.debug._here
    direpa_media=os.path.join(os.path.expanduser("~"), "fty", "etc", "selenium_media")

    if args.selenium_options._here:
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
    elif args.gui._here:
        srv=pkg.SeleniumServer(debug=debug, direpa_media=direpa_media)
        srv.show_gui()
        sys.exit(0)
    elif args.exit._here:
        srv=pkg.SeleniumServer(debug=debug, direpa_media=direpa_media)
        srv.reset()
        sys.exit(0)
    elif args.reset._here:
        srv=pkg.SeleniumServer(debug=debug, direpa_media=direpa_media)
        srv.reset(args.drivers._values)

    if args.connect._here or args.accessibility._here:
        srv=pkg.SeleniumServer(accessibility=args.accessibility._here, debug=debug, direpa_media=direpa_media)
        cmd_pid=None

        if args.connect.cmd._here:
            cmd_pid=srv.windows.get_active()

        if args.accessibility._here and args.connect.driver._value != "chrome":
            print("To use accessibility plugin, please use chrome driver.")
            sys.exit(1)
        # if args.connect._here:
        srv.connect(args.connect.driver._value, reset=args.connect.driver.reset._here)
        # elif args.accessibility._here:
            # print("Here")
            # sys.exit()
            # srv.connect("chrome", reset=args.reset._here)

        if args.connect.focus._here:
            srv.browser_focus()

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
                        srv.get_driver().find_element(By.ID, "advancedButton").click()
                        srv.get_driver().find_element(By.ID, "exceptionDialogButton").click()
                elif srv.get_driver().dy["name"] == "chrome":
                    srv.get_driver().get(url)
                    advanced_button=srv.get_driver().get_elem(id="details-button", error=False, wait_ms=800)
                    if advanced_button is not None:
                        advanced_button.click()
                        srv.get_driver().find_element(By.ID, "proceed-link").click()

                    # print(advanced_button)
                else:
                    print("--insecure flag needs to be implemented for driver '{}'".format(srv.get_driver().dy["name"]))
                    sys.exit(1)
            else:
                srv.get_driver().get(url)


        if args.connect.refresh._here:
            srv.refresh(wait_ms=args.connect.refresh.wait._value)

        if args.connect.scroll._here:
            srv.get_driver().scroll(percent=args.connect.scroll._value, wait_ms=args.connect.scroll.wait._value)

        if args.connect.scroll_to._here:
            srv.get_driver().scroll_to(element_id=args.connect.scroll_to._value, wait_ms=args.connect.scroll_to.wait._value)

        for arg in args.connect.select._branches:
            if arg._here is True:
                if arg.wait._value is not None:
                    time.sleep(float(arg.wait._value)/1000)
                elem=srv.get_driver().get_elem(
                    id=arg.id._value, 
                    query=arg.query._value, 
                    query_index=arg.query.index._value
                )
                if arg.value._value is not None:
                    elem.send_keys(arg.value._value)
          
        for arg in args.connect.click._branches:
            if arg._here is True:
                if arg.wait._value is not None:
                    time.sleep(float(arg.wait._value)/1000)
                elem=srv.get_driver().get_elem(
                    id=arg.id._value, 
                    query=arg.query._value, 
                    query_index=arg.query.index._value
                )

                if arg.file._here is True:
                    elem.send_keys(arg.file._value)
                else:
                    elem.send_keys("")
                    elem.click()

        if args.connect.console._here:
            if args.connect.focus._here is False:
                srv.browser_focus()
            pyautogui.hotkey('ctrl', 'shift', 'k')

        if args.accessibility._here:
            import pyautogui
            # you have to take a screenshot of the button
            extn = pyautogui.locateOnScreen(os.path.join(srv.driver_data["direpa_extensions"], "site_improve_button.png"))
            offset=15
            if extn is None:
                print("Not Found button.png")
                sys.exit(1)
            time.sleep(.5)
            pyautogui.click(x=extn[0]+offset,y=extn[1]+offset,clicks=1,interval=0.0,button="left")

        if args.driver_info._here:
            pprint(srv.get_driver().dy)

        if args.connect.cmd._here:
            srv.windows.focus(cmd_pid)
           

        # if args.clear_cache._here:
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
        #         # driver.find_element(By.CSS_SELECTOR, "#clearButton")
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


