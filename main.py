#!/usr/bin/env python3
import json
from pprint import pprint
import re
import os
import sys
import subprocess
import shlex

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

        if args.connect.here:
            srv.connect(args.driver.value, reset=args.reset.here)
        elif args.accessibility.here:
            srv.connect("chrome", reset=args.reset.here)

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
            srv.get_driver().get(url)


        if args.refresh.here:
            srv.refresh(wait_ms=args.refresh.value)

        if args.scroll.here:
            srv.get_driver().scroll(percent=args.scroll.value)

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
