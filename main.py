from seleniumwire import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common import exceptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox import firefox_profile
from bs4 import BeautifulSoup
from binascii import a2b_base64
import time
import re
import os
import pathlib
import pickle 

driver = None
debug = True
post_links = []

def scrape_month(query_url, sentinel_url = None):
    '''sentinel_url - the URL that must be seen when going in reverse
    '''
    global driver
    global post_links
    if (driver is None):
        return

    if (sentinel_url == None):
        found_sentinel = True
    else:
        found_sentinel = False

    driver.get(query_url)
    height = driver.execute_script("return document.body.scrollHeight")
    x = 0
    stop = False
    old_href = None
    newest_href = None

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
                    newest_href = href
                    if (href == sentinel_url):
                        if debug: print("FOUND SENTINEL")
                        found_sentinel = True
                        break
                    if (href not in post_links):
                        if debug: print("Unique Link: " + href)
                        unique_post_found = True
                        post_links.append(href)

        #If we haven't seen the sentinel and we're not repeating post loads, keep searching
        keep_searching_for_sentinel = ((not found_sentinel) & (old_href != newest_href))

        if (unique_post_found or keep_searching_for_sentinel):
            wait = 1
            loader = soup.find(attrs={"aria-label":"loading more posts"})
            while (loader): 
                loader = soup.find(attrs={"aria-label":"loading more posts"})
                time.sleep(wait)
                wait = wait * 2
                if (wait > 120):
                    break
            a_string = soup.find(string=re.compile(r"^Load more$"))
            if (a_string):
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
        else:
            stop = True
    
    if debug: print(post_links)

    if debug: print("Found Sentinel? " + str(found_sentinel))
    return found_sentinel
    


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
        var = input("Enter a patreon posts tab URL (patreon.com/account/posts):")
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
    
    options = {
        'connection_timeout': None  # Never timeout
    }

    fp = webdriver.FirefoxProfile()
    fp.set_preference("browser.download.manager.showWhenStarting", False)
    fp.set_preference("browser.download.manager.showAlertOnComplete", False)
    fp.set_preference("browser.helperApps.neverAsk.saveToDisk", "image/jpg, image/jpeg, image/png, application/zip")
    fp.set_preference("browser.download.dir", os.getcwd() + "/scraped")


    driver = webdriver.Firefox(firefox_profile=fp, seleniumwire_options=options)
    WebDriverWait(driver, 5)
    driver.get(posts_url)

    if (os.path.isfile("patreon_cookie.pkl")):
        for cookie in pickle.load(open("patreon_cookie.pkl", "rb")):
            driver.add_cookie(cookie)
        driver.get(posts_url)

    var = ""
    while (var.lower() != "y"):
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

            sentinel = post_links[-1] #Most recent post

            if debug: print(post_links)

            time.sleep(1)

            # Go down the other way

            found_sentinel = scrape_month(inversion_url)

            while not found_sentinel:
                found_sentinel = scrape_month(inversion_url)

            if debug: print(post_links)

    with open('post_links.txt', mode="wt", encoding="utf-8") as myfile:
        myfile.write('\n'.join(post_links))
    
    #with open('post_links.txt') as f:
    #    post_links = f.read().splitlines()

    links = {}

    pathlib.Path(os.getcwd()+ "/scraped/").mkdir(parents=True, exist_ok=True)

    for post_link in post_links:
        successful = False
        wait = 60
        while not successful:
            try:
                driver.get(post_link)
                soup = BeautifulSoup(driver.page_source, 'html.parser')

                title = soup.find(attrs={"data-tag":"post-title"})
                title = title.contents[0]
                title = "".join([c for c in title if c.isalpha() or c.isdigit()]).rstrip()


                # If there are any links grab the post content (for Mega links with password)
                content = soup.find_all(attrs={"data-tag":"post-content"})
                if (content):
                    for content_piece in content:
                        content_links = content_piece.find_all("a")
                        if (content_links):
                            for link in content_links:
                                href = link.get("href")
                                if (href not in links.keys()):
                                    links[href] = content_piece.stripped_strings

                # Get all the images
                images = driver.find_elements_by_xpath('//img[@data-pin-nopin="true"]')

                # Only look at network traffic to the Patreon image server 
                driver.scopes = [
                    '.*c10\.patreonusercontent.*',
                    '.*patreon.com/file.*'
                ]
                for image in images:
                    del driver.requests
                    image.click()
                    driver.wait_for_request("c10.patreonusercontent", timeout=wait)
                    request = driver.last_request
                    image_url = request.url
                    if (request.response):

                        filename = image_url[image_url.rindex("/") + 1:image_url.rindex(".")]

                        fileextension = image_url[image_url.rindex("."):image_url.rindex("?")]

                        pathlib.Path(os.getcwd()+ "/scraped/" + title + "/").mkdir(parents=True, exist_ok=True)
                        path = os.getcwd()+ "/scraped/" + title + "/" + filename + fileextension

                        # Don't overwrite images
                        if (os.path.isfile(path)):
                            repeat = 1
                            while (os.path.isfile(path)):
                                path = os.getcwd()+ "/scraped/" + title + "/" + filename + " (" + str(repeat) + ")" + fileextension
                                repeat = repeat + 1
                    
                        output = open(path, "wb")
                        output.write(request.response.body)
                        output.close()

                    # Once the image is downloaded, close the highlight box to get the next one
                    time.sleep(0.5)
                    box = driver.find_element_by_xpath('//div[@data-target="lightbox-content"]')
                    while(box):
                        driver.execute_script("arguments[0].click()", box)
                        try:
                            WebDriverWait(driver, 1)
                            box = driver.find_element_by_xpath('//div[@data-target="lightbox-content"]')
                        except exceptions.NoSuchElementException as err:
                            box = None
                            WebDriverWait(driver, 5)
                            pass     
                        time.sleep(0.5)

                # Download any file attachments
                attachment_links = soup.find_all(href=re.compile(r"https://www\.patreon\.com/file"))

                # Only look at network requests for the Patreon file server
                for attachment_link in attachment_links:
                    del driver.requests
                    url = attachment_link.get("href")
                    print(url)
                    text = attachment_link.contents[0]
                    print(text)
                    filename = text[:text.index(".")]
                    fileextension = text[text.index("."):]

                    # get the file via XMLHttpRequest to prevent system "save as" dialog
                    script = """
                    var done = arguments[0];
                    let xhr = new XMLHttpRequest();
                    xhr.open("get", '""" + url + """')

                    let reader = new FileReader();

                    xhr.onload = function(){
                        done();
                    }

                    xhr.send()
                    """
                    stuff = driver.execute_async_script(script)
                    driver.wait_for_request("patreon.com/file", timeout=900)
                    request = driver.last_request
                    if (request.response):
                        pathlib.Path(os.getcwd()+ "/scraped/" + title + "/").mkdir(parents=True, exist_ok=True)
                        path = os.getcwd()+ "/scraped/" + title + "/" + filename + fileextension

                        # Don't overwrite images
                        if (os.path.isfile(path)):
                            repeat = 1
                            while (os.path.isfile(path)):
                                path = os.getcwd()+ "/scraped/" + title + "/" + filename + " (" + str(repeat) + ")" + fileextension
                                repeat = repeat + 1
                    
                        output = open(path, "wb")
                        output.write(request.response.body)
                        output.close()

                successful = True
            except exceptions.TimeoutException as err:
                print)
                print("Timeout Error!")
                print("Setting wait to: " + str(wait))
                WebDriverWait(driver, wait)
                wait = wait * 2

    with open(os.getcwd() + '/scraped/links.txt', mode="wt", encoding="utf-8") as myfile:
        for key, val in links.items():
            myfile.write(key + "\t" + '\t'.join(val) + '\n')

    driver.close()
    exit()

main()