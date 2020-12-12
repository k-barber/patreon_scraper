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
    '''
    
    var = None
    while (var == None):
        var = input("Enter a start date (YYYY/MM):")
        matched = re.match(r"^\d\d\d\d/\d\d$", var)
        if (matched):
            start_date = var
            start_year = int(start_date[0:4])
            start_month = int(start_date[5:])
            if (start_month > 12 or start_month < 1):
                print("months must be between 1 and 12")
                var = None
        else:
            var = None
        
    var = None
    while (var == None):
        var = input("Enter an end date (YYYY/MM):")
        matched = re.match(r"^\d\d\d\d/\d\d$", var)
        if (matched):
            end_date = var
            end_year = int(end_date[0:4])
            end_month = int(end_date[5:])
            if (end_year < start_year):
                print("end year must be after start year")
                var = None
            if (end_year == start_year) & (end_month < start_month):
                print("end month must be after start month")
                var = None
            if (end_month > 12 or end_month < 1):
                print("months must be between 1 and 12")
                var = None
        else:
            var = None
    
    if (debug):
        print("Url: " + str(posts_url))
        print("Start Date: " + str(start_date))
        print("End Date: " + str(end_date))

    for year in range(start_year, end_year+1):
        if (year == start_year):
            loop_start_month = start_month
        else :
            loop_start_month = 1
        if (year == end_year):
            loop_end_month = end_month + 1
        else :
            loop_end_month = 12
        
        for month in range(loop_start_month, loop_end_month):
            if (debug): print(str(year) + "-" + str(month))
            query_url = posts_url + "?filters[month]=" + str(year) + "-" + str(month)
            if (debug): print(query_url)
            inversion_url = query_url + "&sort=published_at"
            if (debug): print(inversion_url)

    print ("Done")


    '''
    driver = webdriver.Firefox()
    driver.get(posts_url)
    var = None
    while (var != "Y"):
        var = input("Done logging in? (Y/N)")


    pickle.dump(driver.get_cookies(), open("cookies.pkl", "wb"))
    driver.close()
    time.sleep(5)
    
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)
    driver.get(posts_url)
    for cookie in pickle.load(open("cookies.pkl", "rb")):
        driver.add_cookie(cookie)
    driver.get(posts_url)
    time.sleep(5)
    f = open("source_2.txt", "w", encoding='utf-8')
    f.write(driver.page_source)
    f.close()
    '''

main()