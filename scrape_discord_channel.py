from seleniumwire import webdriver
from bs4 import BeautifulSoup
import re
import os
import time


var = None
while (var == None):
    var = input("Please enter Discord channel URL (discord.com/channels/12345678910/12345678910):")
    if (re.match(r"(https?:\/\/)?(www\.)?(discord\.com/channels/\d*/\d*)", var)):
        channel_url = var
    else: 
        print("Channel URL must be in form 'discord.com/channels/12345678910/12345678910'")
        var = None

driver = webdriver.Firefox()
driver.get(channel_url)

var = None
while (var != "Y"):
    var = input("Done logging in? (Y/N)")

soup = BeautifulSoup(driver.page_source, 'html.parser')

wrapper = soup.find(class_=re.compile("messagesWrapper.*"))

scroller = wrapper.contents[0]

links = []

scroll = driver.find_element_by_class_name(scroller['class'][0])

scroll_position = driver.execute_script("return arguments[0].scrollTop", scroll)
while (scroll_position > 0) :
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    images = soup.find_all(class_=re.compile("imageWrapper.*"))
    for image in images:
        href = image.get("href")
        if href in links:
            continue
        elif (isinstance(href, str)):
            links.append(href)
    driver.execute_script("arguments[0].scrollTop = 0", scroll)
    time.sleep(1)
    scroll_position = driver.execute_script("return arguments[0].scrollTop", scroll)

# write in case of failure

with open('images.txt', mode="wt", encoding="utf-8") as myfile:
    myfile.write('\n'.join(links))
    
#
#with open('images.txt') as f:
#    links = f.read().splitlines()
#

for link in links:
    filename = link[link.rindex("/") + 1:]
    driver.get(link)

    for request in driver.requests:
        if request.response:
            if (request.url == link):
                print(request.url)
                print(request.response.status_code)
                print(request.response.headers['Content-Type'])
                output = open(os.getcwd() + "/scraped/" + filename, "wb")
                output.write(request.response.body)
                output.close()
            else:
                continue