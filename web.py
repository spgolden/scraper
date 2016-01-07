import os
import pandas as pd
from bs4 import BeautifulSoup
import requests
import unicodedata
import csv
import datetime
import dateutil
import hashlib
import time
import re
import sys
import math
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium import webdriver


class Item:

    def __init__(self, title, pid, price, orig_price, time, url):
        self.title = title
        self.pid = pid
        self.price = price
        self.orig_price = orig_price
        self.time = time
        self.url = url

    def __str__(self):
        return ("Title: " + self.title.encode('UTF-8') + 
        "\r\nPrice: " + self.price.encode('UTF-8') + 
        "\r\nOriginal Price: " + self.orig_price.encode('UTF-8') + 
        "\r\nSource: " + self.url + "\r\n")


def parse_item(box_soup, url):
    try:
        title = box_soup.find('h1', {"class":'title'}).text.strip()

        try:
            price = box_soup.select("div.sale span.price_ammount")[0].text.strip()
            orig_price = box_soup.select('div.original')[0].text.strip().replace('Original\n \r','').replace('$','')
        except Exception:
            price = box_soup.select("div.original")[0].text.strip().replace('Original\n','').replace('$', '')
            orig_price = price
            
    except Exception:
        title = "Out of Stock"
        price = 0
        orig_price = 0
    pid = re.search("(prd-[0-9]+)", page_url).group(0)
    this_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
    url = page_url

    return(Item(title, pid, price, orig_price, this_time, url))

def parse_javascript(url):
    session = dryscrape.Session()
    session.set_attribute('auto_load_images', False)
    session.set_header('User-agent', 'Google Chrome')
    session.visit(url)
    return (BeautifulSoup(session.body()))

from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium import webdriver

def set_up_browser(agent=True):
    dcap = dict(DesiredCapabilities.PHANTOMJS)
    dcap["phantomjs.page.settings.userAgent"] = (
        "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 "
    )

    try:
        del driver
    except Exception:
        "No driver"

#    p = os.popen('pgrep phantomjs | sudo xargs kill',"r")

    if agent:
        driver = webdriver.PhantomJS(executable_path='/usr/local/bin/phantomjs', desired_capabilities=dcap, service_args=['--ignore-ssl-errors=true', '--load-images=no']) 
    else:
        driver = webdriver.PhantomJS(executable_path='/usr/local/bin/phantomjs', service_args=['--ignore-ssl-errors=true', '--load-images=no']) 
    
    driver.set_window_size(1024, 768) # optional
    return(driver)
    
    

def parse_javascript_selenium(url, screen_shot=None):
    driver = set_up_browser()
    
    print(url)
    driver.get(url)

    time.sleep(3)
    
    if screen_shot is not None:
        driver.save_screenshot('%s.png' % screen_shot)
    else:
        driver.save_screenshot('screenz.png') 
        
    res = BeautifulSoup(driver.page_source)
    driver.quit()
    
    # Really makes sure it's dead
    p = os.popen('pgrep phantomjs | sudo xargs kill',"r")
    
    return(res)

def extract_search_links(response):
    links = set([])
    base_url = 'http://www.kohls.com'
    divs = response.findAll("div", {"class":"prod_nameBlock"})
   
    for d in divs:
        links.add(base_url + d.find("p").get('rel'))
        
    return(links)


all_urls = "http://www.kohls.com/catalog/womens-sweaters-tops-clothing.jsp?CN=4294720878+4294719467+4294719805+4294719810&PPP=120"

try:
    del driver
except Exception:
    ''
driver = set_up_browser()
driver.get(all_urls)
time.sleep(3)
response = BeautifulSoup(driver.page_source)

# Start crawling the page results
prod_links = set([])
prod_links.update(extract_search_links(response))
driver.quit()
del driver

num_results = int(response.select(".result_count")[0].text.replace('(', '').replace(')', ''))
pages = math.ceil(num_results / 120.0)

page_args = [str(120*i) for i in range(1, int(pages))]

for p in page_args:
    new_url = all_urls + '&WS=%s' % p
    print "Connecting to %s ..." % new_url
    response = parse_javascript_selenium(url=new_url, screen_shot=p)
    divs = response.findAll("div", {"class":"prod_nameBlock"})
    prod_links.update(extract_search_links(response))

print len(prod_links)