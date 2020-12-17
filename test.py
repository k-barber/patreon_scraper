from selenium import webdriver
from bs4 import BeautifulSoup
import json
import mimetypes
import os
from drive_downloader import download_drive_item
import re

driver = webdriver.Firefox()
#driver.get("https://drive.google.com/file/d/1ZrERhi01GMK_3VrQxTyCkcAniof_iV5P/view?usp=sharing")
driver.get("https://drive.google.com/drive/folders/1mx92hkkZXLbi1JIjm6PELj3a48jMgcJx?usp=sharing")

url = driver.current_url
soup = BeautifulSoup(driver.page_source, 'html.parser')
docs = soup.find_all(attrs={"data-target":"doc", "data-id": re.compile("\w*")})
subfolders = []

for doc in docs:
    data_id = doc.get("data-id")
    print(str(data_id))
    download_button = doc.find(attrs={"aria-label":"Download"})
    is_folder = doc.find(attrs={"aria-label": re.compile("Google Drive Folder")})
    if (is_folder):
        print("ID is folder")
    else:
        print("ID is not folder")




'''
soup = BeautifulSoup(driver.page_source, 'html.parser')
info = soup.find(id="drive-active-item-info")
print(str(info))
print(info.contents[0])
item_data = json.loads(info.contents[0])
print(item_data)

item_id = item_data['id']
full_name = item_data['title']
file_type = item_data['mimeType']
file_extension = mimetypes.guess_extension(file_type)

dot_spot = full_name.rindex(".")
file_name = full_name[:dot_spot]
extension_maybe = full_name[dot_spot:]
safe_name = "".join([c for c in file_name if c.isalpha() or c.isdigit()]).rstrip()

location = os.getcwd()+ "/scraped/" + safe_name + file_extension

download_drive_item(item_id, location)
'''