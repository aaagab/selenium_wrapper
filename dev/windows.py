#!/usr/bin/env python3
from __future__ import print_function
import json
from pprint import pprint
import os
import re
import shlex
import subprocess
import sys
import threading

import ctypes
from ctypes import wintypes
from collections import namedtuple

class Windows():
    def __init__(self, debug=False):
        self.debug=debug

        self.user32 = ctypes.WinDLL('user32', use_last_error=True)
        if not hasattr(wintypes, 'LPDWORD'): # PY2
            wintypes.LPDWORD = ctypes.POINTER(wintypes.DWORD)

        self.WindowInfo = namedtuple('WindowInfo', 'pid title')

        self.WNDENUMPROC = ctypes.WINFUNCTYPE(
            wintypes.BOOL,
            wintypes.HWND,    # _In_ hWnd
            wintypes.LPARAM,) # _In_ lParam

        self.user32.EnumWindows.errcheck = self.check_zero
        self.user32.EnumWindows.argtypes = (
        self.WNDENUMPROC,      # _In_ lpEnumFunc
        wintypes.LPARAM,) # _In_ lParam

        self.user32.IsWindowVisible.argtypes = (
            wintypes.HWND,) # _In_ hWnd

        self.user32.GetWindowThreadProcessId.restype = wintypes.DWORD
        self.user32.GetWindowThreadProcessId.argtypes = (
        wintypes.HWND,     # _In_      hWnd
        wintypes.LPDWORD,) # _Out_opt_ lpdwProcessId

        self.user32.GetWindowTextLengthW.errcheck = self.check_zero
        self.user32.GetWindowTextLengthW.argtypes = (
        wintypes.HWND,) # _In_ hWnd

        self.user32.GetWindowTextW.errcheck = self.check_zero
        self.user32.GetWindowTextW.argtypes = (
            wintypes.HWND,   # _In_  hWnd
            wintypes.LPWSTR, # _Out_ lpString
            ctypes.c_int,)   # _In_  nMaxCount

    def check_zero(self, result, func, args):    
        if not result:
            err = ctypes.get_last_error()
            if err:
                raise ctypes.WinError(err)
        return args

    def list_windows(self):
        '''Return a sorted list of visible windows.'''
        result = []
        @self.WNDENUMPROC
        def enum_proc(hwnd, lParam):
            if self.user32.IsWindowVisible(hwnd):
                pid = wintypes.DWORD()
                tid = self.user32.GetWindowThreadProcessId(
                            hwnd, ctypes.byref(pid))
                length = self.user32.GetWindowTextLengthW(hwnd) + 1
                title = ctypes.create_unicode_buffer(length)
                self.user32.GetWindowTextW(hwnd, title, length)

                result.append(dict(
                    title=title.value,
                    hwnd=hwnd,
                    pid=pid.value,
                ))
            return True
        self.user32.EnumWindows(enum_proc, 0)
        # return sorted(result)
        return result

    def focus(self, pid):
        found=False
        for window in self.list_windows():
            if self.debug is True:
                print(window)
            if window["pid"] == int(pid):
                found=True
                self.user32.SetForegroundWindow(window["hwnd"])
                break
        if found is False:
            print("No Window Found for pid '{}'".format(pid))

    # h_wnd = user32.GetForegroundWindow()
    # pid = wintypes.DWORD()
    # user32.GetWindowThreadProcessId(h_wnd, ctypes.byref(pid))
    # print(pid.value)