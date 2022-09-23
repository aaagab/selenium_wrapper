```shell
pip install pyautogui selenium lxml msedge-selenium-tools
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

I didn't find a way to disable Firefox Update, why would that be an easy task?  
The bug may be that:  
https://bugzilla.mozilla.org/show_bug.cgi?id=1676671  
created a ticket on github https://github.com/mozilla/geckodriver/issues/1837  

I was able to correct the issue by adding preferences like:
```python
options = webdriver.FirefoxOptions()
fp = webdriver.FirefoxProfile()
# the line below fixed the issue
fp.set_preference("marionette.actors.enabled", False)
options.profile=fp
options.set_capability("marionette", True)
options.log.level = "trace"
options.add_argument("-devtools")
driver["capabilities"]=options.to_capabilities()
```

I problem come back, let's get rid of curl to check what if browser if from selenium, maybe create a tmp file or something with the process at startup.
Also one problem maybe that I try to get the curl before the command has been send. so what about I wait for the curl and I get it after?
ok that is where I have all my pids:
```python
for node in self.processes.from_pid(self.get_grid_url_pid())["node"].nodes:
                print(node.dy)
```
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

## Debug Firefox Gecko Driver
selenium.common.exceptions.WebDriverException: Message: NotFoundError: WindowGlobalParent.getActor: No such JSWindowActor 'MarionetteCommands'issue:  
### How to manually check what browser is needed for the session?  
```shell
# So get all pid for firefox.exe:  
# use task manager just look at firefox pid
tasklist  | findstr firefox.exe

# go to page and get pid from json "moz:processID": 18776,
http://127.0.0.1:4444/wd/hub/sessions
# Then for each pid get the netstat port:  
netstat -aon -p tcp | findstr "18776"
# Then try curl on ports
>  curl -sSL http://127.0.0.1:2344/status
curl: (7) Failed to connect to 127.0.0.1 port 2344: Connection refused
>  curl -sSL http://127.0.0.1:54130/status
curl: (7) Failed to connect to 127.0.0.1 port 54130: Connection refused
>  curl -sSL http://127.0.0.1:54129/status
50:{"applicationType":"gecko","marionetteProtocol":3}

# How to send url to session with curl?
# I don't know but lets just find where the browser pid is defined and lets just try to change it if possible
# I found that with firefox logs:
POST /session/ca02d309-33f9-4767-89a6-3d20c5f9e8e4/url {"url": "https://www.example.com/e/example/login"}
curl --data "param1=value1&param2=value2" https://example.com/resource.cgi

http://127.0.0.1:4444/wd/hub/sessions/session/ca02d309-33f9-4767-89a6-3d20c5f9e8e4/url

curl -sSL http://127.0.0.1:58503/session/ca02d309-33f9-4767-89a6-3d20c5f9e8e4


http://127.0.0.1:4444/session/ca02d309-33f9-4767-89a6-3d20c5f9e8e4

echo '{"text": "Hello **world**!"}' | curl -d @- https://api.github.com/markdown
echo '{"url": "https://www.example.com/e/example/login"}' | curl -d @- http://127.0.0.1:58503/session/ca02d309-33f9-4767-89a6-3d20c5f9e8e4/url


echo '{"url": "https://www.example.com/e/example/login"}' | curl -d @- http://127.0.0.1:58503/session/ca02d309-33f9-4767-89a6-3d20c5f9e8e4/url

curl --header "Content-Type: application/json" --request POST --data '{"url": "https://www.example.com/e/example/login"}' http://127.0.0.1:58503/session/ca02d309-33f9-4767-89a6-3d20c5f9e8e4/url

curl --header "Content-Type: application/json" --request POST --data "{\"url\": \"https://www.example.com/e/example/login\"}" http://127.0.0.1:59544/session/ca02d309-33f9-4767-89a6-3d20c5f9e8e4/url

tail -f /mnt/c/Users/john/fty/etc/selenium_media/logs/client_firefox.txt

# launch hub with this command
C:\Program Files (x86)\Common Files\Oracle\Java\javapath\java.exe -Dwebdriver.gecko.driver=%userprofile%\fty\etc\selenium_media\drivers\geckodriver.exe -Dwebdriver.firefox.logfile=%userprofile%\fty\etc\selenium_media\logs\client_firefox.txt -Dwebdriver.firefox.loglevel=DEBUG -jar %userprofile%\fty\etc\selenium_media\selenium-server-standalone-3.141.59.jar -log %userprofile%\fty\etc\selenium_media\logs\server.txt -timeout 252000 -host 127.0.0.1

# go to hub and get moz:processID 
http://127.0.0.1:4444/wd/hub/sessions
# get port from pid
netstat -aon -p tcp | findstr "17888"
# curl browser with get
curl -sSL http://127.0.0.1:49888/status
# then try a post to change url
# curl --header "Content-Type: application/json" --request POST --data "{\"url\": \"https://github.com\"}" http://127.0.0.1:49888/session/3f44419b-dee1-4a68-8eca-27ee6be29c3e/url
echo  | curl -d @- 
https://hexdocs.pm/webdriver/WebDriver.Session.html
window.open("https://www.example.com", "_blank"); 

POST 	/session/{session id}/execute/async

curl -d "{\"url\": \"https://github.com\"}" -H "Content-Type: application/json" -X POST http://127.0.0.1:44444/session/3f44419b-dee1-4a68-8eca-27ee6be29c3e/url

curl -d '{window.open\"https://www.example.com\", \"_blank\")' -H "Content-Type: application/json" -X POST http://127.0.0.1:49888/session/3f44419b-dee1-4a68-8eca-27ee6be29c3e/execute/async


curl http://localhost:49888/session/3f44419b-dee1-4a68-8eca-27ee6be29c3e/url -d '{"url":"http://example.com/"}'
curl http://localhost:44444/session/3f44419b-dee1-4a68-8eca-27ee6be29c3e/url -d '{"url":"http://example.com/"}'

curl -d "[0,8,\"WebDriver:Navigate\",{\"url\":\"https://google.com\"}]" -H "Content-Type: application/json" -X POST http://127.0.0.1:49888/session/3f44419b-dee1-4a68-8eca-27ee6be29c3e/url
curl -d "[0,8,\"WebDriver:Navigate\",{\"url\":\"https://google.com\"}]" -H "Content-Type: application/json" -X POST http://127.0.0.1:49888/session/3f44419b-dee1-4a68-8eca-27ee6be29c3e/url

curl -X POST -H "Content-Type: text/plain" --data "this is raw data" http://127.0.0.1:49888/session/3f44419b-dee1-4a68-8eca-27ee6be29c3e/url

curl -d "{\"script\": \"window.open('https://github.com')\"}" -H "Content-Type: application/json" -X POST http://127.0.0.1:49888/session/3f44419b-dee1-4a68-8eca-27ee6be29c3e/execute/async


# window.open("https://www.example.com", "_blank")
# window.open("https://www.example.com", "_blank"); 
webdriver API
https://chromium.googlesource.com/chromium/src/+/master/docs/chromedriver_status.md
https://hexdocs.pm/webdriver/WebDriver.Session.html

how to send a raw curl javascript to webdriver

https://makandracards.com/makandra/49096-how-to-control-chromedriver-using-curl
```

Typical Debug:  
- At Selenium Class Init get all drivers
- At Selenium().connect
  - get driver
  - get grid url pid self.get_grid_url_pid()
    - if reset is True and pid exists then it is killed.
    - Then selenium.jar is launched with the related webdriver executable and logs set on localhost 
    - and driver is set
- get session or create session
- get browser window
- launch driver



### Additional Info
```shell
# grid_url = "http://127.0.0.1:4444/wd/hub"
# driver_firefox = webdriver.Remote(grid_url, DesiredCapabilities.FIREFOX)
# driver_chrome = webdriver.Remote(grid_url, DesiredCapabilities.CHROME)


# > tasklist | findstr geckodriver
# geckodriver.exe              22464 RDP-Tcp#83                 2     11,324 K

# > tasklist | findstr chromedriver
# chromedriver.exe              9148 RDP-Tcp#83                 2     14,896 K
```

```json
// # disable firefox updates
// # There is an alternative solution suggested by our reader EP. You can create a policies.json file and store that file into the ‘C:\Program Files\Mozilla Firefox\distribution’ folder. Create a ‘distribution’ folder in \Program Files\Mozilla Firefox\ folder and place that policies.json file into that folder with the following contents:
{
"policies": 
   {
     "DisableAppUpdate": true
    }
}
// To confirm, you can go to the URL about:policies and check if there's an entry like this
// I also deleted files updaters and maintenance
    // update-settings.ini,
    // updater.ini,
    // updater.exe (updater in Linux).

```

If firefox stops working again because of Marion




The latest edge finally installed during an update: Version 88.0.705.74 (Official build) (64-bit)
```python
pip3 install msedge-selenium-tools

from msedge.selenium_tools import EdgeOptions
 elif name == "edge":
            # browser_name="MicrosoftEdge"
            # session_proc_name="System"
            # filen_exe="MicrosoftWebDriver.bat"
            # driver_proc_name=filen_exe.replace(".bat", ".exe")
            browser_name="msedge"
            filen_browser="msedge.exe"
            capability_name="EDGE"
            session_proc_name="Msedge"
            filen_exe="msedgedriver.exe"

     elif name == "edge":
            options = EdgeOptions()
            options.use_chromium = True
            driver["capabilities"]=options.to_capabilities()
```

for internet explorer make sure you go to options and security tab and for each zone, unchek "enable protected mode" otherwise you are going to have issue in the log file "iexplorer a Protected Mode boundary has been crossed"

### Add an extension / accessibility
#### Chrome
go to chrome://extensions
click on one installed extension and get id from url
`chrome://extensions/?id=djcglbmbegflehmbfleechkjhmedcopn`
Then on page chrome://extensions enable "developer mode" and click on "Pack extension"
In extension root directory type:
C:\Users\user\AppData\Local\Google\Chrome\User Data\Default\Extensions\djcglbmbegflehmbfleechkjhmedcopn\2022.1.18.937_0
Leave the "Private Key" field blank" and click "Pack extension".

It will create the two files:
"C:\Users\user\AppData\Local\Google\Chrome\User Data\Default\Extensions\djcglbmbegflehmbfleechkjhmedcopn\2022.1.18.937_0.crx"
"C:\Users\user\AppData\Local\Google\Chrome\User Data\Default\Extensions\djcglbmbegflehmbfleechkjhmedcopn\2022.1.18.937_0.pem"
copy these two files to: 
"C:\Users\user\fty\etc\selenium_media\extensions\chrome\site_improve_2022.1.18.937_0.pem"
"C:\Users\user\fty\etc\selenium_media\extensions\chrome\site_improve_2022.1.18.937_0.crx"

check the name of the extension in drivers.py
take a screenshot of the button and add it in the folder

then when launching selenium you have to pin the extension to make the button visible by clicking on the extensions icon on the navbar and pin the icon.
`main.py --connect --driver chrome --accessibility --refresh --focus --url /`

Software center deleted my java install with script "Java Removal Script - Silent User Interface"
So Reinstall java in a home folder, renamed that folder after install, launched the uninstall from programs, rever the folder name back, add the path to filenpa_java, seems to work allright.