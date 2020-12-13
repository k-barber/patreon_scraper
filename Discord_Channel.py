from seleniumwire import webdriver
from bs4 import BeautifulSoup
import re
import os
import pickle 
import time
import urllib.request


channel_url = "https://discord.com/channels/561827776571768833/561830072265474078"
driver = webdriver.Firefox()
driver.get(channel_url)

var = None
while (var != "Y"):
    var = input("Done logging in? (Y/N)")

'''
pickle.dump(driver.get_cookies(), open("cookies.pkl", "wb"))

soup = BeautifulSoup(driver.page_source, 'html.parser')

wrapper = soup.find(class_=re.compile("messagesWrapper.*"))

print (wrapper)

scroller = wrapper.contents[0]

print(scroller)

print(scroller['class'])

links = []

scroll = driver.find_element_by_class_name(scroller['class'][0])

scroll_position = driver.execute_script("return arguments[0].scrollTop", scroll)
print(scroll_position)
while (scroll_position > 0) :
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    images = soup.find_all(class_=re.compile("imageWrapper.*"))
    print(images)
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
    '''

with open('images.txt') as f:
    links = f.read().splitlines()

link = links[0]
filename = link[link.rindex("/") + 1:]
response_url = None
driver.get(link)

for link in links:
    filename = link[link.rindex("/") + 1:]
    response_url = None
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