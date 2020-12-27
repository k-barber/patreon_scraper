from seleniumwire import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common import exceptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox import firefox_profile
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from binascii import a2b_base64
from drive_downloader import download_drive_item
import json
import mimetypes
import shutil
import time
import re
import os
import pathlib
import pickle 
import sys
import getopt
import datetime
import requests
import html

driver = None
debug = True
post_links = []
scraped_external_links = []
one_folder = False

def download_drive_file(id, destination):
    global driver
    url = driver.current_url
    if (re.match(r"https://drive\.google\.com/file/d/" + str(id), url) == None):
        time.sleep(1)
        get_url("https://drive.google.com/file/d/" + str(id))
    time.sleep(1)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    info = soup.find(id="drive-active-item-info")

    properly_escaped_string = info.contents[0].replace("\/", "/")
    item_data = json.loads(properly_escaped_string)

    file_extension = None
    file_extensions = mimetypes.guess_all_extensions(item_data['mimeType'], False)
    if (len(file_extensions) >= 1):
        file_extension = file_extensions[-1] # get the extension that was added to the dictionary first, as it is most likely to be accurate

    full_name = item_data['title']
    file_name = full_name[:full_name.rindex(".")]
    file_name = "".join([c for c in file_name if c.isalpha() or c.isdigit()]).rstrip()

    guessed_extension = full_name[full_name.rindex("."):]

    pathlib.Path(destination).mkdir(parents=True, exist_ok=True)

    if (file_extension == None):
        # File is non-standard Mime Type, use what should be the extension from the file name
        location = destination + file_name + guessed_extension
        if (os.path.isfile(location)):
            repeat = 1
            while (os.path.isfile(location)):
                location = destination + file_name + "_" + str(repeat) + guessed_extension
                repeat = repeat + 1
    else:
        location = destination + file_name + file_extension
        if (os.path.isfile(location)):
            repeat = 1
            while (os.path.isfile(location)):
                location = destination + file_name + "_" + str(repeat) + file_extension
                repeat = repeat + 1
    
    result = download_drive_item(item_data['id'], location)
    if (result == -1):
        return -1
    else:
        return id

def download_drive_folder(id, folder_name, destination):
    global driver
    global one_folder

    url = driver.current_url
    if (re.match(r"https://drive\.google\.com/drive/folders/" + str(id), url) == None):
        time.sleep(1)
        get_url("https://drive.google.com/drive/folders/" + str(id))
    time.sleep(1)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    docs = soup.find_all(attrs={"data-target":"doc", "data-id": re.compile("\w*")})

    if debug: print("Making folder: " + destination)
    pathlib.Path(destination).mkdir(parents=True, exist_ok=True)

    subfolders = []
    files = []

    error_code = None

    if (docs == None):
        if debug: print("ERROR scraping folder")
        time.sleep(60)
        return download_drive_folder(id, folder_name, destination)

    for doc in docs:
        data_id = doc.get("data-id")
        if debug: print("found data-id: " + str(data_id))
        download_button = doc.find(attrs={"aria-label":"Download"})
        folder_label = doc.find(attrs={"aria-label": re.compile("Google Drive Folder")})
        if (folder_label):
            if debug: print("ID is folder")
            label_text = folder_label.get("aria-label")
            # Labels are in form "subfolder name Google Drive Folder"
            sub_folder_name = label_text[:label_text.find(" Google Drive Folder")]
            subfolders.append({"ID" : data_id, "name":sub_folder_name})
        else:
            if debug: print("ID is not folder")
            files.append(data_id)
            
    for data_id in files:
        time.sleep(2)
        if debug: print("Downloading File: " + data_id)
        result = download_drive_file(data_id, destination)
        if debug: print("Result: " + result)
        if (result == -1):
            error_code = -1
    for subfolder in subfolders:
        time.sleep(2)
        if debug: print("Downloading Folder: " + subfolder["ID"])
        if (one_folder):
            location = destination
        else:
            location = destination + subfolder["name"] + "/"
        response = download_drive_folder(subfolder["ID"], subfolder["name"], location)
        if debug: print("Response: " + response)
        if (response == -1):
            error_code = -1
    if (error_code):
        return error_code
    return id

def scrape_google_link(link, folder):
    global driver
    global scraped_external_links
    global one_folder

    link_type = None
    if re.match(r"(https?://)?(www\.)?drive\.google\.com/file/d/.*(/view|/edit)", link):
        link_type = "file"
        url = link
    else:
        get_url(link)
        url = driver.current_url
        if (url.find("folder") != -1):
            link_type = "folder"
        elif (url.find("file/d/") != -1):
            link_type = "file"
        else: # even /open/ links eventually redirect to /file/ or /folder/
            soup = BeautifulSoup(driver.page_source, "html.parser")
            a_string = soup.find(string=re.compile(r"404"))
            if a_string:
                print("File has been removed")
                return -1
            print("Couldn't Identify")
            return -1

    if (one_folder):
        location = folder
    else:
        location = folder + "Google_Drive/"

    if (link_type == "file"):
        return download_drive_file(url[url.find("file/d/") + 7 : url.rindex("/")], location)
    elif (link_type == "folder"):
        response = download_drive_folder(url[url.rindex("/") + 1:], "Google_Drive",  location)
        if (response == url[url.rindex("/") + 1:]):
            return url
        else :
            return -1
    else:
        return -1
    

def scrape_dropbox_link(link, folder):
    q_spot = link.find("?")
    if (q_spot > 1):
        direct_link = link[:link.find("?")]
    else:
        direct_link = link


    response = requests.get(direct_link, allow_redirects=False, stream=True, params = { 'dl' : 1 })

    while (300 <= response.status_code < 600): # Not final request yet
        if (400 <= response.status_code < 600):
            print("Dropbox refused our connection")
            print(response.url)
            print(str(response.status_code))
            print(response.headers)
            repeat = 1
            while (response.status_code != 200):
                if (repeat > 3):
                    return -1
                print("Waiting " + str(5) + " seconds and retrying")
                time.sleep(5)
                print("Retrying")
                response = requests.get(direct_link, stream = True, params = { 'dl' : 1 })
                repeat = repeat + 1
        elif (300 <= response.status_code < 400):
            print("Dropbox redirected our connection")
            redirect_URL2 = response.headers['Location']
            if (redirect_URL2.find("/") == 0):
                redirect_URL2 = "https://www.dropbox.com" + redirect_URL2
            response = requests.get(redirect_URL2, allow_redirects=False, stream = True)

    stuff = response.headers["content-disposition"]
    start_index = stuff.find("\"") + 1
    full_name = stuff[start_index: stuff.find("\"", start_index + 1 )]
    file_name = full_name[:full_name.find(".")]
    file_extension = full_name[full_name.find("."):]

    location = folder + file_name + file_extension

    if (os.path.isfile(location)):
        repeat = 1
        while (os.path.isfile(location)):
            location = folder + file_name + "_" + str(repeat) + file_extension
            repeat = repeat + 1

    with open(location, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    return link

def scrape_mega_link(link, folder):
    global driver
    global scraped_external_links
    get_url(link)
    link_type = None
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "transfer-wrapper"))
        )
        link_type = "file"
    except exceptions.TimeoutException:
        print("Not a file")
        try:
            print("Trying")
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "fm-right-files-block"))
            )
            print("Found")
            soup = BeautifulSoup(driver.page_source, "html.parser")
            a_string = soup.find(string=re.compile(r"The folder link you are trying to access is no longer available\."))
            if a_string:
                print("MEGA REMOVED")
                return -1
            link_type = "folder"
        except exceptions.TimeoutException:
            print("Couldn't Identify")
            return -1
    
    if (link_type == "file"):
        download_button = driver.find_element_by_css_selector(".download.big-button.button.download-file.green.transition")
        WebDriverWait(driver, 20).until(
            EC.visibility_of(download_button)
        )
        url = driver.current_url
        print("Scraping Mega url: " + url)
        if (url in scraped_external_links):
            print("DUPLICATE URL DETECTED")
            return url
        download_button.click()
        time.sleep(1)
        complete_notice = driver.find_element_by_css_selector(".download.main-transfer-info .download.complete-block")
        WebDriverWait(driver, 1800).until(
            EC.visibility_of(complete_notice)
        )
    elif (link_type == "folder"):
        download_button = driver.find_element_by_css_selector(".button.link-button.right.fm-download-as-zip")
        WebDriverWait(driver, 20).until(
            EC.visibility_of(download_button)
        )
        url = driver.current_url
        print("Scraping Mega url: " + url)
        if (url in scraped_external_links):
            print("DUPLICATE URL DETECTED")
            return url
        download_button.click()
        time.sleep(0.05)
        WebDriverWait(driver, 1800).until(
            EC.text_to_be_present_in_element((By.CLASS_NAME, "transfer-task-status"), "Completed")
        )
    else:
        return -1
    driver.get("about:downloads")
    fileName = driver.execute_script("return document.querySelector('#contentAreaDownloadsView .downloadMainArea .downloadContainer description:nth-of-type(1)').value")
    old_location = os.getcwd()+ "/scraped/" + fileName
    new_location = folder + fileName
    time.sleep(2) # Wait for the file to be completely written
    shutil.move(old_location, new_location)
    return url

def scrape_month(query_url, sentinel_url = None):
    '''sentinel_url - the URL that must be seen when going in reverse
    '''
    global driver
    global post_links
    if (driver is None):
        return

    print("Sentinel: ", sentinel_url)

    found_sentinel = None
    found_links = []

    get_url(query_url)
    height = driver.execute_script("return document.body.scrollHeight")
    x = 0
    stop = False
    old_href = None
    newest_href = None

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    a_string = soup.find(string=re.compile(r"This filter has no posts\."))
    if (a_string):
        if debug: print("THIS MONTH HAS NO POSTS")
        found_sentinel = "No Posts"
        stop = True

    while (stop != True):
        while x < height:
            time.sleep(0.01)
            driver.execute_script("window.scrollTo(0, " + str(x) +");")
            x = x + 500
        time.sleep(2)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if (new_height != height):
            height = new_height
            continue

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        loader = soup.find(attrs={"aria-label":"loading more posts"})
        if (loader): continue

        published_at_list = soup.find_all(attrs={'data-tag':'post-published-at'})
        unique_post_found = False
        for link in published_at_list:
            href = link.get('href')
            if (re.match(r"^https://www\.patreon\.com/posts/", href)):
                newest_href = href
                if (href == sentinel_url):
                    if debug: print("FOUND SENTINEL")
                    found_sentinel = "Found Sentinel"
                    break
                if (href not in post_links):
                    if debug: print("Unique Link: " + href)
                    if (sentinel_url == None):
                        found_sentinel = href
                    unique_post_found = True
                    post_links.append(href)
                    found_links.append(href)

        if (found_sentinel == "Found Sentinel"):
            break
        elif (old_href == newest_href):
            if (sentinel_url == None):
                if (found_links == []):
                    found_sentinel = "No Posts"
                break
            else:
                found_sentinel = "Did not find sentinel"
                break
            break
        else:

            old_href = newest_href

            # Wait for loading to finish before checking for button
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
                button = a_string.find_parent("button")
                if (button):
                    class_list = button['class']
                    class_string = ".".join(class_list)
                    more_button = driver.find_element_by_class_name(class_string)
                    more_button.click()
                    continue

            # No loading button, no load more button, therefore end of month 
            found_sentinel = "End of Month"
            stop = True
    
    if debug: print(found_links)
    return found_sentinel
    
def initialize_browser():
    global driver

    if (driver != None):
        return

    options = {
        'connection_timeout': None  # Never timeout
    }
    
    fp = webdriver.FirefoxProfile()
    fp.set_preference("browser.download.folderList", 2)
    fp.set_preference("general.useragent.override", "K-Barber's Patreon Scraper")
    fp.set_preference("browser.download.dir", os.getcwd() + "\\scraped")
    fp.set_preference("browser.download.manager.showWhenStarting", False)
    fp.set_preference("browser.download.manager.showAlertOnComplete", False)
    download_types = """
        image/jpg, image/jpeg, image/png, application/zip, application/x-photoshop, image/vnd.adobe.photoshop,
        application/photoshop, application/psd, image/psd
    """
    fp.set_preference("browser.helperApps.neverAsk.saveToDisk", download_types)

    driver = webdriver.Firefox(firefox_profile=fp, seleniumwire_options=options)
    WebDriverWait(driver, 5)
    get_url("https://www.patreon.com")

    if (os.path.isfile("patreon_cookie.pkl")):
        for cookie in pickle.load(open("patreon_cookie.pkl", "rb")):
            driver.add_cookie(cookie)
        get_url("https://www.patreon.com/login")
        if (driver.current_url == "https://www.patreon.com/home"):
            pickle.dump(driver.get_cookies(), open("patreon_cookie.pkl", "wb"))
            return
        else:
            var = ""
            while (var.lower() != "y"):
                var = input("Done logging in? (Y/N)")
    else:
        var = ""
        while (var.lower() != "y"):
            var = input("Done logging in? (Y/N)")
        
    pickle.dump(driver.get_cookies(), open("patreon_cookie.pkl", "wb"))

def get_url(url = ""):
    global driver
    if (driver != None):
        if (url.startswith("https://")):
            driver.get(url)
        else:
            if (url.startswith("http://")):
                driver.get("https://" + url[7:])
            else:
                driver.get("https://" + url)

def get_user_variables(patreon_url = None, start_date = None, end_date = None):
    if (patreon_url):
        var = patreon_url
        scrape_url = patreon_url
    else: 
        var = None
    while (var == None):
        var = input("Enter a patreon posts tab URL (patreon.com/account/posts):")
        matched = re.match(r"^(https?://)?(www.)?patreon.com\/([a-zA-Z0-9_]*)\/posts$", var)
        if (matched):
            scrape_url = var
        else:
            var = None

    if (start_date):
        var = start_date
        start_year = int(start_date[0:4])
        start_month = int(start_date[5:])
    else:
        var = None
    while (var == None):
        var = input("Enter a start date (YYYY/MM):")
        matched = re.match(r"^\d\d\d\d/\d\d$", var)
        if (matched):
            start_date = var
            start_year = int(start_date[0:4])
            start_month = int(start_date[5:])
            if ((start_year, month) < (2013, 5)):
                print("Start date must be no earlier than 2013/05 (Patreon's launch date)")
                var = None
                continue
            if (start_month > 12 or start_month < 1):
                print("months must be between 1 and 12")
                var = None
                continue
            today = datetime.datetime.today().date()
            if ((start_year, start_month) > (today.year, today.month)):
                print("Start date must be no later than " + str(today.year) + "/" + str(today.month) + " (the current month)")
                var = None
                continue
        else:
            print("Must be of format: YYYY/MM")
            var = None
    
        
    if (end_date):
        var = end_date
        end_year = int(end_date[0:4])
        end_month = int(end_date[5:])
    else:
        var = None
    while (var == None):
        var = input("Enter an end date (YYYY/MM):")
        matched = re.match(r"^\d\d\d\d/\d\d$", var)
        if (matched):
            end_date = var
            end_year = int(end_date[0:4])
            end_month = int(end_date[5:])
            if ((end_year, end_month) < (start_year, start_month)): 
                print("End date must be after start date")
                var = None
                continue
            if (end_month > 12 or end_month < 1):
                print("months must be between 1 and 12")
                var = None
                continue
            if ((end_year, end_month) < (2013, 5)):
                print("End date must be no earlier than 2013/05 (Patreon's launch date)")
                var = None
                continue
            today = datetime.datetime.today().date()
            if ((end_year, end_month) > (today.year, today.month)):
                print("End date must be no later than " + str(today.year) + "/" + str(today.month) + " (the current month)")
                var = None
                continue
        else:
            print("Must be of format: YYYY/MM")
            var = None
    
    if (debug):
        print(str((scrape_url, start_year, start_month, end_year, end_month)))
    
    return (scrape_url, start_year, start_month, end_year, end_month)
    

def get_post_urls(patreon_url, start_year, start_month, end_year, end_month):
    global post_links
    post_links = []
    
    for year in range(start_year, end_year+1):
        if (year == start_year):
            loop_start_month = start_month
        else :
            loop_start_month = 1
        if (year == end_year):
            loop_end_month = end_month + 1
        else :
            loop_end_month = 13
        
        for month in range(loop_start_month, loop_end_month):
            sentinel = None
            if (debug): print(str(year) + "-" + str(month))
            query_url = patreon_url + "?filters[month]=" + str(year) + "-" + str(month)
            if (debug): print(query_url)
            inversion_url = query_url + "&sort=published_at"
            if (debug): print(inversion_url)

            # Go down one way

            found_sentinel = scrape_month(query_url)

            if (found_sentinel == "No Posts" or found_sentinel == "End of Month"):
                if (debug): print("Found end of month, don't reverse")
                continue
            
            time.sleep(1)

            # Go down the other way

            found_sentinel = scrape_month(inversion_url, found_sentinel)

            while not (found_sentinel == "Found Sentinel"):
                found_sentinel = scrape_month(inversion_url, sentinel)

    with open('post_links.txt', mode="wt", encoding="utf-8") as myfile:
        myfile.write('\n'.join(post_links))

    return post_links

def get_post_urls_from_file():
    post_links = []
    with open('post_links.txt', mode="rt") as f:
        post_links = f.read().splitlines()
    return post_links


def scrape_links(post_links):
    global one_folder
    pathlib.Path(os.getcwd()+ "/scraped/").mkdir(parents=True, exist_ok=True)

    for post_link in post_links:
        images_done = False
        external_links_done = False
        attachments_done = False
        successful = False
        wait = 60
        while not successful:
            try:
                get_url(post_link)
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                title = post_link[post_link.rindex("/") + 1 :]
                if (one_folder):
                    folder = os.getcwd()+ "/scraped/"
                else:
                    folder = os.getcwd()+ "/scraped/" + title + "/"

                pathlib.Path(folder).mkdir(parents=True, exist_ok=True)

                time.sleep(2) # delay a bit

                # Only look at network traffic to the Patreon image server 
                driver.scopes = [
                    '.*c10\.patreonusercontent.*',
                    '.*patreon.com/file.*'
                ]

                # Get all the images
                if (not images_done):
                    images = driver.find_elements_by_xpath('//img[@data-pin-nopin="true"]')

                    for image in images:
                        del driver.requests
                        driver.execute_script("arguments[0].scrollIntoView()", image)
                        time.sleep(0.5)
                        driver.execute_script("arguments[0].click()", image)
                        time.sleep(0.5)
                        driver.wait_for_request("c10.patreonusercontent", timeout=wait)
                        request = driver.last_request
                        image_url = request.url
                        if (request.response):

                            filename = image_url[image_url.rindex("/") + 1:image_url.rindex(".")]

                            if (re.match(r"\d*", filename)): # Patreon has a habit of renaming images to "1.png"
                                post_title = soup.find(attrs={"data-tag":"post-title"})
                                if (post_title):
                                    post_title = post_title.contents[0]
                                    filename = "".join([c for c in post_title if c.isalpha() or c.isdigit()]).rstrip()
                                elif (title):
                                    filename = "".join([c for c in title if c.isalpha() or c.isdigit()]).rstrip()

                            fileextension = image_url[image_url.rindex("."):image_url.rindex("?")]

                            path = folder + filename + fileextension

                            # Don't overwrite images
                            if (os.path.isfile(path)):
                                repeat = 1
                                while (os.path.isfile(path)):
                                    path = folder + filename + "_" + str(repeat) + fileextension
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

                    images_done = True

                # Download any file attachments
                if (not attachments_done):

                    attachment_links = soup.find_all(href=re.compile(r"https://www\.patreon\.com/file"))

                    # Only look at network requests for the Patreon file server
                    for attachment_link in attachment_links:
                        del driver.requests
                        url = attachment_link.get("href")
                        print(url)
                        text = attachment_link.contents[0]
                        print(text)
                        filename = text[:text.find(".")]
                        fileextension = text[text.find("."):]

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
                        # Attached files like .zip or .psd can be very large, so timeout is set to 30 minutes
                        driver.set_script_timeout(1800) 
                        stuff = driver.execute_async_script(script)
                        driver.wait_for_request("patreon.com/file", timeout=1800)
                        driver.set_script_timeout(30) 
                        request = driver.last_request
                        if (request.response):
                            path = folder + filename + fileextension

                            # Don't overwrite images
                            if (os.path.isfile(path)):
                                repeat = 1
                                while (os.path.isfile(path)):
                                    path = folder + filename + "_" + str(repeat) + fileextension
                                    repeat = repeat + 1
                        
                            output = open(path, "wb")
                            output.write(request.response.body)
                            output.close()

                    attachments_done = True

                # Scrape External G Drive, Dropbox and Mega links
                if (not external_links_done):

                    # If there are any links grab the post content (for Mega links with password)
                    content = soup.find(attrs={"data-tag":"post-content"})

                    if (content):
                        path = folder + "post-text.txt"
                        content_links = content.find_all("a")
                        external_links = []
                        unscraped_links = []
                        duplicate_links = []
                        strings = []
                        for line in content.strings:
                            if (line.strip() != ""):
                                strings.append(line.strip())
                        if (content_links):
                            for link in content_links:
                                href = link.get("href")
                                if (re.match(r"(https?://)?(www\.)?drive\.google\.com", href)):
                                    if (re.match(r"(https?://)?(www\.)?drive\.google\.com/(file/d/\S*|drive/folders/\S*|open\?id=\S*)", href)):
                                        print("Complete Google Drive link")
                                        print(href)
                                        result = scrape_google_link(href, folder)
                                    else: 
                                        print("Incomplete Google Drive link")
                                        for num, line in enumerate(strings):
                                            if re.match(r"(https?://)?(www\.)?drive\.google\.com", line):
                                                rest_of_link = strings[num+1]
                                                if (rest_of_link.find(" ") > -1):
                                                    rest_of_link = rest_of_link[:rest_of_link.find(" ")].strip()
                                                href = line + rest_of_link
                                                print("complete link: " + href)
                                                result = scrape_google_link(href, folder)
                                                break
                                    pass 
                                elif (re.match(r"(https?://)?(www\.)?dropbox\.com", href)):
                                    if (re.match(r"(https?://)?(www\.)?dropbox\.com/[/\S]+", href)):
                                        print("Dropbox link")
                                        result = scrape_dropbox_link(href, folder)
                                    else:
                                        print("Incomplete Dropbox link")
                                        for num, line in enumerate(strings):
                                            if re.match(r"(https?://)?(www\.)?dropbox\.com", line):
                                                rest_of_link = strings[num+1]
                                                if (rest_of_link.find(" ") > -1):
                                                    rest_of_link = rest_of_link[:rest_of_link.find(" ")].strip()
                                                href = line + rest_of_link
                                                print("complete link: " + href)
                                                result = scrape_dropbox_link(href, folder)
                                                break
                                    pass
                                elif (re.match(r"(https?://)?(www\.)?mega\.(co\.)?nz/", href)):
                                    if (re.match(r"(https?://)?(www\.)?mega\.(co\.)?nz/(folder/\S*#|file/\S*#|#)", href)):
                                        print("Complete Mega link")
                                        result = scrape_mega_link(href, folder)
                                    else:
                                        print("Incomplete MEGA link")
                                        for num, line in enumerate(strings):
                                            if re.match(r"(https?://)?(www\.)?mega\.(co\.)?nz/", line):
                                                rest_of_link = strings[num+1]
                                                if (rest_of_link.find(" ") > -1):
                                                    rest_of_link = rest_of_link[:rest_of_link.find(" ")].strip()
                                                href = line + rest_of_link
                                                print("complete link: " + href)
                                                result = scrape_mega_link(href, folder)
                                                break
                                else:
                                    result = -1
                                
                                external_links.append(href)
                                if (result == -1):
                                    unscraped_links.append(href)
                                elif (result not in scraped_external_links):
                                    scraped_external_links.append(result)
                                elif (result in scraped_external_links):
                                    duplicate_links.append(result)
                        if (len(strings) > 0):
                            output = open(path, "at", encoding="utf-8")
                            output.write("----- " + post_link + "  (" + time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()) + ") -----\n")
                            for line in strings:
                                output.write(str(line) + "\n")
                            if (external_links):
                                output.write("\nExternal Links:\n")
                                for external_link in external_links:
                                    output.write(external_link + "\n")
                            if (duplicate_links):
                                output.write("\nDuplicate Links:\n")
                                for duplicate_link in duplicate_links: 
                                    output.write(duplicate_link + "\n")
                            output.close()

                        if (len(unscraped_links) > 0):
                            output = open(folder + "UNSCRAPED-LINKS.txt", "at", encoding="utf-8")
                            output.write("----- " + post_link  + "  (" + time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()) + ") -----\n")
                            for line in strings:
                                output.write(str(line) + "\n")
                            output.write("\nUnscraped Links:\n")
                            for unscraped_link in unscraped_links:
                                output.write(unscraped_link + "\n")
                            output.close()
                    
                    external_links_done = True

                successful = True
            except exceptions.TimeoutException as err:
                print("Timeout Error!")
                print("Setting wait to: " + str(wait))
                WebDriverWait(driver, wait)
                wait = wait * 2
            except exceptions.ElementNotInteractableException as err:
                print("Couldn't click")
                time.sleep(3)
                continue
            except exceptions.ElementClickInterceptedException as err:
                print("Couldn't click")
                time.sleep(3)
                continue

def main(argv):
    global one_folder

    print("Num arguments: ", len(argv))
    print("Arguments: " + str(argv))

    try:
        opts, args = getopt.getopt(argv, "s: e: h u: c f", ("start-date=", "end-date=", "help", "url=", "continue", "one-folder"))
    except getopt.GetoptError:
        print("Commands not recognized. To get help, use the following command:\n")
        print("\t'main.exe -h'")
        sys.exit(2)

    load_from_file = False
    one_folder = False

    start_date = None
    end_date = None
    patreon_url = None

    for opt, arg in opts:
        if (opt in ('-h', "--help")):
            print("main.exe --start-date|-s <start-date (YYYY/MM)> --end-date|-e <end-date (YYYY/MM)>")
            sys.exit()
        elif opt in ("-c", "--continue"):
            load_from_file = True
        elif opt in ("-f", "--one-folder"):
            one_folder = True
        elif opt in ("-u", "--url"):
            if (re.match(r"^(https?://)?(www.)?patreon.com\/([a-zA-Z0-9_]*)\/posts$", arg)):
                patreon_url = arg
            else:
                print("URL must be in format: https://patreon.com/creator_name/posts")
        elif opt in ("-s", "--start-date"):
            if (re.match(r"\d\d\d\d/\d\d", arg)):
                given_date = datetime.datetime(int(arg[0:4]), int(arg[5:]), 1).date()
                patreon_start = datetime.datetime(2013, 5, 1).date()
                today = datetime.datetime.today().date()
                if (patreon_start <= given_date <= today):
                    start_date = arg
                else: 
                    print("Start date must be between 2013/05 (Patreon's launch date) and the current month " + str(today.year) + "/" + str(today.month))
                    sys.exit()
            else:
                print("start date must be in format 'YYYY/MM', ex: '2015/03'")
                sys.exit(2)
        elif opt in ("-e", "--end-date"):
            if (re.match(r"\d\d\d\d/\d\d", arg)):
                given_date = datetime.datetime(int(arg[0:4]), int(arg[5:]), 1).date()
                patreon_start = datetime.datetime(2013, 5, 1).date()
                today = datetime.datetime.today().date()
                if (patreon_start <= given_date <= today):
                    end_date = arg
                else: 
                    print("Start date must be between 2013/05 (Patreon's launch date) and the current month " + str(today.year) + "/" + str(today.month))
                    sys.exit()
            else:
                print("start date must be in format 'YYYY/MM', ex: '2015/03'")
                sys.exit(2)
        else:
            print("Found option: " + opt)

    if (load_from_file == True):
        post_urls = get_post_urls_from_file()
        initialize_browser()
    else:
        results = get_user_variables(patreon_url, start_date, end_date)
        initialize_browser()
        post_urls = get_post_urls(*results)

    scrape_links(post_urls)

    driver.close()
    exit()

if __name__ == "__main__":
    main(sys.argv[1:])