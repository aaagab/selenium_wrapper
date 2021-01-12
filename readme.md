```shell
pip3 install selenium
```
Java needs to be installed to (i.e. "jre-8u251-windows-x64.exe")

Problem drivers need to be related to the version of the browser that you are using, otherwise it broke the software. It means that this application break every now and then. Better disable update on browsers and decide when and update the related driver at the same time.

error:
When trying to use geckodriver.exe  
`selenium.common.exceptions.WebDriverException: Message: NotFoundError: WindowGlobalParent.getActor: No such JSWindowActor 'MarionetteCommands'`
I have version 84.0.2  
fix:
so I went back to version 82.0.1 with driver geckodriver-v0.26.0-win64 and it starts working again.  
https://ftp.mozilla.org/pub/firefox/releases/82.0.1/win64/en-US/  

I didn't find a way to disable Google Update, why would that be an easy task?


## Install Edge Driver
Open elevated prompt and:
```shell
# enable developer mode
$ reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock" /t REG_DWORD /f /v "AllowDevelopmentWithoutDevLicense" /d "1"
The operation completed successfully.
# install webdriver (it takes maybe one minute), it freezes if developer mode is not enabled first
$ DISM.exe /Online /Add-Capability /CapabilityName:Microsoft.WebDriver~~~~0.0.1.0

Deployment Image Servicing and Management tool
Version: 10.0.18362.1139

Image Version: 10.0.18363.1256

[==========================100.0%==========================]
The operation completed successfully.
# it installs that file
c:\Windows\SysWOW64\MicrosoftWebDriver.exe
```

Then error:
Hmmm...can’t reach this page with edge for local iis server
With elevated prompt do:
```shell
> CheckNetIsolation LoopbackExempt -a -n="Microsoft.MicrosoftEdge_8wekyb3d8bbwe
OK.
```