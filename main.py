from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver import FirefoxProfile
import time
import re
import os
import pickle 

debug = False

def main():
    print("Hello World")

    posts_url = "https://www.patreon.com/AldhaRoku/posts"

    '''
    var = None
    while (var == None):
        var = input("Enter a patreon posts tab URL (patreon.com/artist/posts):")
        matched = re.match(r"^((https?://)?www.)?patreon.com\/([a-zA-Z0-9_]*)\/posts$", var)
        if (matched):
            posts_url = var
        else:
            var = None

    
    var = None
    while (var == None):
        var = input("Enter a start date (YYYY/MM):")
        matched = re.match(r"^\d\d\d\d/\d\d$", var)
        if (matched):
            start_date = var
        else:
            var = None
        
    var = None
    while (var == None):
        var = input("Enter an end date (YYYY/MM):")
        matched = re.match(r"^\d\d\d\d/\d\d$", var)
        if (matched):
            end_date = var
        else:
            var = None
    
    if (debug):
        print("Url: " + str(posts_url))
        print("Start Date: " + str(start_date))
        print("End Date: " + str(end_date))
    '''


    #firefox_capabilities = DesiredCapabilities.FIREFOX
    #firefox_capabilities['marionette'] = True

    options = Options()
    options.add_argument("--headless")
    #options.add_argument("-profile")
    #options.add_argument("C:/Users/redyo/AppData/Local/Mozilla/Firefox/Profiles/rf9xcvji.Selenium")
    #options.add_argument("C:/Users/redyo/AppData/Roaming/Mozilla/Firefox/Profiles/rf9xcvji.Selenium")
    #options.add_argument("--marionette")
    #driver = webdriver.Firefox(options=options, capabilities=firefox_capabilities)

    '''
    cwd = os.getcwd()
    path = cwd + "\geckodriver.exe"
    print(path)
    binary = FirefoxBinary(firefox_path=path, log_file=cwd + "\log.txt")
    
    driver = webdriver.Firefox()
    driver.get(posts_url)
    var = None
    while (var != "Y"):
        var = input("Done logging in? (Y/N)")
    f = open("source_1.txt", "w", encoding='utf-8')
    f.write(driver.page_source)
    f.close()
    pickle.dump(driver.get_cookies(), open("cookies.pkl", "wb"))
    driver.close()
    time.sleep(5)
    '''
    driver = webdriver.Firefox(options=options)
    driver.get(posts_url)
    for cookie in pickle.load(open("cookies.pkl", "rb")):
        driver.add_cookie(cookie)
    driver.get(posts_url)
    time.sleep(5)
    f = open("source_2.txt", "w", encoding='utf-8')
    f.write(driver.page_source)
    f.close()

main()