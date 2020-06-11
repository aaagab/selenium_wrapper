#!/usr/bin/env python3
from datetime import datetime
from pprint import pprint
from copy import deepcopy
import inspect
import types
import json
import glob
from lxml import etree
import os
import re
import sys
import urllib.parse
import subprocess
import shlex
import traceback

def get_class_name(obj):
    return str(obj.__class__).replace("<class '", "").replace("'>", "")

def get_obj_info(direpa_app, obj, dy_files=dict(), dy_file=dict(), known_types=set(), root=True, keys=[]):
    import selenium
    if not keys:
        keys.append(get_class_name(obj))

    for var in sorted(dir(obj)):
        if not var.startswith("__"):
            try:
                member=getattr(obj, var)
                member_type=type(member)
                dy_files[var]=str(member_type)
                dy_file[var]=str(member_type)
                if isinstance(member, types.MethodType):
                    dy_files[var]+=" "+str(member.__code__.co_varnames)
                    dy_file[var]+=" "+str(member.__code__.co_varnames)
                else:
                    if member.__class__.__module__ == "builtins":
                        known_types.add(str(member_type))
                        for t in [
                            bool,
                            dict,
                            int,
                            list,
                            str,
                        ]:
                            if member_type == t:
                                if member_type == str:
                                    value=member[:100]
                                else:
                                    value=member
                                dy_files[var]={ str(member_type): value }
                                dy_file[var]={ str(member_type): value }
                                break
                    else:
                        dy_file[var]={ str(member_type): dict() }
                        obj_name=get_class_name(member)
                        if obj_name not in keys:
                            tmp_keys=deepcopy(keys)
                            tmp_keys.append(obj_name)
                            dy_files[var]={ str(member_type): dict() }
                            get_obj_info(
                                direpa_app,
                                member,
                                dy_files[var][str(member_type)],
                                dy_file=dict(),
                                known_types=known_types,
                                root=False,
                                keys=tmp_keys
                            )

            except Exception as e:
                dy_files[var]=None
                dy_file[var]=None

                if e.__class__.__name__ not in [
                    "TypeError",
                    "WebDriverException",
                    "InvalidSessionIdException",
                    "NoAlertPresentException",
                ]:
                    print("##################################")
                    print(var)
                    print(e.__class__.__name__)
                    print(traceback.format_exc())

    filen=get_class_name(obj)
    with open("{}\doc\WebDriver\{}.json".format(direpa_app, filen), "w") as f:
        f.write(json.dumps(dy_file, sort_keys=True, indent=4))

    if root is True:
        filen_files=filen+"_recursive"
        with open("{}\doc\WebDriver\{}.json".format(direpa_app, filen_files), "w") as f:
            f.write(json.dumps(dy_files, sort_keys=True, indent=4))
