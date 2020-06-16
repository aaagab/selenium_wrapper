#!/usr/bin/env python3
import json
from pprint import pprint
import re
import os
import sys
import subprocess
import shlex

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

    if args.run.here:
        srv=pkg.SeleniumServer(debug=debug, direpa_media=direpa_media)
        srv.run(args.driver.value, reset=args.reset.here)

        if args.focus.here:
            srv.browser_focus()

        if args.url.here:
            srv.get_driver().get(args.url.value)

        if args.refresh.here:
            srv.get_driver().refresh()

        if args.scroll.here:
            srv.get_driver().scroll()

        if args.driver_info.here:
            pprint(srv.get_driver().dy)



    # driver_name=dy_app.get_arg_values("--driver", ret="value", get_values=False)
    # if driver_name is not None:
    #     # print(srv.get_driver().dy["session"]["id"])
    #     # print(srv.get_driver().dy["browser_session"])
    #     # print(srv.get_driver().dy["browser_window"])

    #     srv.browser_focus()
    #     srv.get_driver().refresh()
