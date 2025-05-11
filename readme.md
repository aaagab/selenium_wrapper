```shell
pip install pyautogui selenium==4.25.0 lxml
```
Java needs to be installed to (i.e. "jre-8u251-windows-x64.exe")
On debian it can be installed with sudo apt-get install default-jre
depends on selenium-server-4.24.0.jar

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
