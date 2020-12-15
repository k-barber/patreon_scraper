from seleniumwire import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver import ActionChains
from selenium.common import exceptions
from bs4 import BeautifulSoup
import time
import re
import os
import pathlib
import pickle 

driver = None
debug = True
post_links = []

def scrape_month(query_url):
    global driver
    global post_links
    if (driver is None):
        return

    driver.get(query_url)
    height = driver.execute_script("return document.body.scrollHeight")
    x = 0
    stop = False

    while (stop != True):
        while x < height:
            time.sleep(0.01)
            if debug: print("Scroll to: " + str(x))
            driver.execute_script("window.scrollTo(0, " + str(x) +");")
            x = x + 100
        time.sleep(3)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if (new_height != height):
            if debug: print("Page extended")
            height = new_height
            stop = False
            continue

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        loader = soup.find(attrs={"aria-label":"loading more posts"})
        if (loader): continue

        titles = soup.find_all(attrs={'data-tag':'post-title'})
        if debug: print("Titles found: ")
        if debug: print(titles)
        unique_post_found = False
        for link in titles:
            a = link.find("a")
            if debug: print("a: " + str(a))
            if (a):
                href = a.get('href')
                if debug: print("href: " + href)
                if debug: print(re.match(r"^https://www\.patreon\.com/posts/", href))
                if (re.match(r"^https://www\.patreon\.com/posts/", href)):
                    if debug: print("regex match")
                    if (href not in post_links):
                        if debug: print("Unique Link: " + href)
                        unique_post_found = True
                        post_links.append(href)

        if (unique_post_found):
            a_string = soup.find(string=re.compile(r"^Load more$"))
            if debug: print(a_string)
            button = a_string.find_parent("button")
            if debug: print(button)
            if(button):
                class_list = button['class']
                class_string = ".".join(class_list)
                if debug: print(class_string)
                more_button = driver.find_element_by_class_name(class_string)
                if debug: print(more_button)
                more_button.click()
            else:
                stop = True
        else:
            stop = True
    
    if debug: print(post_links)
    


def main():
    global driver
    global post_links

    '''
    posts_url = "https://www.patreon.com/AldhaRoku/posts"
    start_year = 2020
    end_year = 2020
    start_month = 11
    end_month = 11
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
        driver.get(posts_url)

    var = None
    while (var != "Y"):
        var = input("Done logging in? (Y/N)")

    pickle.dump(driver.get_cookies(), open("patreon_cookie.pkl", "wb"))
    
    post_links = []
    
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

            if debug: print(post_links)

            time.sleep(1)

            # Go down the other way

            scrape_month(inversion_url)

            if debug: print(post_links)

    with open('post_links.txt', mode="wt", encoding="utf-8") as myfile:
        myfile.write('\n'.join(post_links))
    
    with open('post_links.txt') as f:
        post_links = f.read().splitlines()

    links = []

    pathlib.Path(os.getcwd()+ "/scraped/").mkdir(parents=True, exist_ok=True)

    for post_link in post_links:
        driver.get(post_link)
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        title = soup.find(attrs={"data-tag":"post-title"})
        title = title.contents[0]
        title = "".join([c for c in title if c.isalpha() or c.isdigit()]).rstrip()

        content = soup.find_all(attrs={"data-tag":"post-content"})
        if (content):
            for content_piece in content:
                content_links = content_piece.find_all("a")
                if (content_links):
                    for link in content_links:
                        href = link.get("href")
                        if (href not in links):
                            links.append(href)

        images = driver.find_elements_by_xpath('//img[@data-pin-nopin="true"]')
        driver.scopes = [
            '.*c10\.patreonusercontent.*'
        ]
        for image in images:
            del driver.requests
            image.click()
            driver.wait_for_request("c10.patreonusercontent")
            request = driver.last_request
            image_url = request.url
            if (request.response):
                filename = image_url[image_url.rindex("/") + 1:image_url.rindex(".")]
                fileextension = image_url[image_url.rindex("."):image_url.rindex("?")]
                pathlib.Path(os.getcwd()+ "/scraped/" + title + "/").mkdir(parents=True, exist_ok=True)
                path = os.getcwd()+ "/scraped/" + title + "/" + filename + fileextension
                if (os.path.isfile(path)):
                    repeat = 1
                    while (os.path.isfile(path)):
                        path = os.getcwd()+ "/scraped/" + title + "/" + filename + " (" + str(repeat) + ")" + fileextension
                        repeat = repeat + 1
            
                output = open(path, "wb")
                output.write(request.response.body)
                output.close()
            time.sleep(1)
            box = driver.find_element_by_xpath('//div[@data-target="lightbox-content"]')
            while(box):
                driver.execute_script("arguments[0].click()", box)
                try:
                    box = driver.find_element_by_xpath('//div[@data-target="lightbox-content"]')
                except exceptions.NoSuchElementException as err:
                    box = None
                    pass   
                time.sleep(1)

    with open(os.getcwd() + '/scraped/links.txt', mode="wt", encoding="utf-8") as myfile:
        myfile.write('\n'.join(links))


main()