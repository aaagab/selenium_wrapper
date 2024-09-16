#!/usr/bin/env python3
from typing import Any
from pprint import pprint
from copy import deepcopy
import types
import json
import os
import sys
import traceback

def get_class_name(obj):
    return str(obj.__class__).replace("<class '", "").replace("'>", "")

def get_obj_info(
    direpa_app:str, 
    obj:Any, 
    dy_files:dict[str,str|dict[str, bool|dict|int|list|str|None]]|None=None, 
    dy_file:dict[str,str|dict[str, bool|dict|int|list|str|None]]|None=None, 
    known_types:set|None=None, 
    root:bool=True, 
    keys:list[str]|None=None,
):
    import selenium

    if dy_files is None:
        dy_files=dict()

    if dy_file is None:
        dy_file=dict()

    if known_types is None:
        known_types=set()

    if keys is None:
        keys=[]

    if len(keys) == 0:
        keys.append(get_class_name(obj))

    for var in sorted(dir(obj)):
        if not var.startswith("__"):
            try:
                member=getattr(obj, var)
                member_type=type(member)
                dy_files[var]=str(member_type)
                dy_file[var]=str(member_type)
                if isinstance(member, types.MethodType):
                    if hasattr(member, "__code__"):
                        if type(dy_files[var]) is  str:
                            dy_files[var]+=" "+str(member.__code__.co_varnames) #type:ignore
                        dy_file[var]+=" "+str(member.__code__.co_varnames) #type:ignore
                else:
                    if member.__class__.__module__ == "builtins":
                        known_types.add(str(member_type))
         
                        if isinstance(member, bool) or isinstance(member, dict) or isinstance(member, int) or isinstance(member, list) or isinstance(member, str):
                            value:bool|dict|int|list|str
                            if isinstance(member, str):
                                value=member[:100]
                            else:
                                value=member
                            dy_files[var]={ str(type(member)): value }
                            dy_file[var]={ str(type(member)): value }
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
                                dy_files[var][str(member_type)], #type:ignore
                                dy_file=dict(),
                                known_types=known_types,
                                root=False,
                                keys=tmp_keys
                            )

            except Exception as e:
                dy_files[var]=None #type:ignore
                dy_file[var]=None #type:ignore

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
    with open(r"{}\doc\WebDriver\{}.json".format(direpa_app, filen), "w") as f:
        f.write(json.dumps(dy_file, sort_keys=True, indent=4))

    if root is True:
        filen_files=filen+"_recursive"
        with open(r"{}\doc\WebDriver\{}.json".format(direpa_app, filen_files), "w") as f:
            f.write(json.dumps(dy_files, sort_keys=True, indent=4))
