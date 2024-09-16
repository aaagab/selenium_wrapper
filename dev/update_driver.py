#!/usr/bin/env python3
from pprint import pprint
import os
import requests
import sys
import tempfile
import shutil

import subprocess

from ..gpkgs import message as msg

def update_chrome_driver(direpa_drivers:str):
    if sys.platform == "win32":
        proc=subprocess.Popen([
            "reg",
            "query",
            r"HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon",
            "/v",
            "version",
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr=proc.communicate()
        stdout=stdout.decode().strip()
        version_elems=stdout.split()[-1].split(".")
        chrome_version=".".join(version_elems[:-1])
        resp=requests.get("https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{}".format(chrome_version))
        resp.raise_for_status()

        driver_version=resp.content.decode()
        filename="chromedriver_win32.zip"
        url="https://chromedriver.storage.googleapis.com/{}/{}".format(driver_version, filename)
        resp=requests.get(url, stream=True)
        resp.raise_for_status()

        filenpa_zip=os.path.join(tempfile.gettempdir(), filename)
        with open (filenpa_zip,'wb') as f:
            for chunk in resp.iter_content(chunk_size=1024):
                f.write(chunk)

        filenpa_driver=os.path.join(direpa_drivers, "chromedriver.exe")
        if os.path.exists(filenpa_driver):
            os.remove(filenpa_driver)
        shutil.unpack_archive(filenpa_zip, direpa_drivers)

        msg.success("chromedriver '{}' installed".format(driver_version))
    else:
        raise Exception("update_chrome_driver is only available on Windows.")
