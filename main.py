from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
import time
import re
import os
import pickle 

driver = None
debug = False
links = []

def scrape_month(url):
    global driver
    global links
    if (driver is None):
        return

    driver.get(query_url)
    height = driver.execute_script("return document.body.scrollHeight")
    x = 0
    stop = False

    while (stop != True):
        while x < height:
            time.sleep(0.01)
            driver.execute_script("window.scrollTo(0, " + str(x) +");")
            x = x + 100
        time.sleep(1)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if (new_height != height):
            height = new_height
            stop = False
            continue

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        titles = soup.find_all(attrs={'data-tag':'post-title'})
        unique_post_found = False
        for link in titles:
            a = link.find("a")
            if (a):
                href = a.get('href')
                if (href not in links & re.match(r"patreon.com/posts/", href)):
                    unique_post_found = True
                    links.append(href)

        if (unique_post_found):
            a_string = soup.find(string=re.compile(r"^Load more$"))
            button = a_string.find_parent("button")
            if(button):
                class_list = button['class']
                class_string = ".".join(class_list)
                more_button = driver.find_element_by_class_name(class_string)
                more_button.click()
            else:
                stop = True
        else:
            stop = True
    


def main():
    global driver
    print("Hello World")

    posts_url = "https://www.patreon.com/AldhaRoku/posts"
    start_year = 2020
    end_year = 2020
    start_month = 1
    end_month = 1

    
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
            start_year = int(start_date[0:4])
            start_month = int(start_date[5:])
            if (start_month > 12 or start_month < 1):
                print("months must be between 1 and 12")
                var = None
                continue
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
                continue
            if (end_year == start_year) & (end_month < start_month):
                print("end month must be after start month")
                var = None
                continue
            if (end_month > 12 or end_month < 1):
                print("months must be between 1 and 12")
                var = None
                continue
        else:
            var = None
    
    if (debug):
        print("Url: " + str(posts_url))
        print("Start Date: " + str(start_date))
        print("End Date: " + str(end_date))

    
    driver = webdriver.Firefox()
    driver.get(posts_url)

    if (os.path.isfile("patreon_cookie.pkl")):
        for cookie in pickle.load(open("patreon_cookie.pkl", "rb")):
            driver.add_cookie(cookie)
    
    '''
        driver.get(posts_url)

    var = None
    while (var != "Y"):
        var = input("Done logging in? (Y/N)")
    '''
    pickle.dump(driver.get_cookies(), open("patreon_cookie.pkl", "wb"))
    
    links = []

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

            # Go down one way

            scrape_month(query_url)

            time.sleep(1)

            # Go down the other way

            scrape_month(inversion_url)

            print(links)

    with open('links.txt', mode="wt", encoding="utf-8") as myfile:
        myfile.write('\n'.join(links))
            
    #with open('links.txt') as f:
    #    links = f.read().splitlines()



main()