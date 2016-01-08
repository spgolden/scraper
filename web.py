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
import json
import config
import csv
from twilio.rest import TwilioRestClient 
#import ipdb; ipdb.set_trace()

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

# Categories in clothing to *not* scrape
blacklist = [
    "Perfume & Cologne",
    "Engagement Rings",
    "Toys",
    "Jewelry",
    "Makeup & Skincare",
    "Sporting Goods",
    "Golf Apparel & Golf Equipment",
    "Health & Beauty"
]


class Item:

    def __init__(self, title, category, sub_category, pid, price, orig_price, time, url):
        self.title = title
        self.pid = pid
        self.category = category
        self.sub_category = sub_category
        self.price = price
        self.orig_price = orig_price
        self.time = time
        self.url = url

    def __str__(self):
        return ("Title: " + self.title.encode('UTF-8') + 
        "\r\nPrice: " + self.price.encode('UTF-8') + 
        "\r\nOriginal Price: " + self.orig_price.encode('UTF-8') + 
        "\r\nSource: " + self.url + "\r\n")

    def toDict(self):
        this_obj = {
            "title": self.title,
            "pid": self.pid,
            "category": self.category,
            "sub_category": self.sub_category,
            "price": self.price,
            "orig_price": self.orig_price,
            "time": self.time,
            "url": self.url
        }
        return(this_obj)

class Category:
    def __init__(self, title):
        self.title = title
        self.sub_categories = []


class SubCategory:
    def __init__(self, title, parent, url):
        self.title = title
        self.parent = parent
        self.url = url
        self.path = clean_description(parent) + "/" + clean_description(title)
        self.items = []
    
    def __str__(self):
        return ("Title: " + self.title.encode('UTF-8') + 
        "\r\nParent: " + self.parent.encode('UTF-8') + 
        "\r\nPath: " + self.path.encode('UTF-8') +
        "\r\nItems: " + str(len(self.items)) + 
        "\r\nURL: " + self.url + "\r\n")

    def save(self, path):
        with open(path + "/metadata.json", "wb") as f:
            this_obj = {
                "title": self.title,
                "parent": self.parent,
                "url": self.url,
                "path": self.path,
                "items": self.items
            }
            f.write(json.dumps(this_obj))

    def load_from_file(self, path):
        with open(path + "/metadata.json", "rb") as f:
            this_obj = json.loads(f.read())
            self.items = this_obj['items']

    def extract_search_links(self, response):
        links = set([])
        base_url = 'http://www.kohls.com'
        divs = response.findAll("div", {"class":"prod_nameBlock"})
       
        for d in divs:
            links.add(base_url + d.find("p").get('rel'))
            
        return(links)

    def collect_urls_for_category(self, wait=3):
        all_urls = self.url
        try:
            del driver
        except Exception:
            ''
        driver = set_up_browser()
        driver.get(all_urls)
        time.sleep(wait)
        response = BeautifulSoup(driver.page_source)

        # Start crawling the page results
        prod_links = set([])
        prod_links.update(self.extract_search_links(response))

        num_results = int(response.select(".result_count")[0].text.replace('(', '').replace(')', ''))
        pages = math.ceil(num_results / 120.0)

        page_args = [str(120*i) for i in range(1, int(pages))]

        for p in page_args:
            new_url = all_urls + '&WS=%s' % p
            print "Connecting to %s ..." % new_url
            driver.get(new_url)
            time.sleep(wait)
            response = BeautifulSoup(driver.page_source)
            divs = response.findAll("div", {"class":"prod_nameBlock"})
            prod_links.update(self.extract_search_links(response))

        # Try and cache some resources...
        driver.quit()
        del driver
        self.items = list(prod_links)

class AppCrawler:

    def __init__(self):
        self.items_to_visit = []
        self.sub_categories_to_visit = []
        self.current_category = ''
        self.current_sub_category = ''
        self.year = datetime.datetime.fromtimestamp(time.time()).strftime('%Y')
        self.month = datetime.datetime.fromtimestamp(time.time()).strftime('%m')
        self.day = datetime.datetime.fromtimestamp(time.time()).strftime('%d')
        self.items = []
        self.categories = []
        self.item_count = 1

    def crawl(self):
        # wrap everything in a notifcation...
        try:
            # collect the categories, sub categories, and sub cat links
            try:
                self.collect_categories()
            except Exception as e:
                print "Error collecting categories ... %s" % e

            
            for cat in self.categories:
                self.current_category = cat.title
                print "\n\n\n" + cat.title + "\n\n\n"

                # For each subcategory
                for sub_cat in cat.sub_categories:
                    self.current_sub_category = sub_cat.title
                    #try:
                    self.visit_subcat(sub_cat)
                    #except Exception as e:
                    #    print 'Error visiting sub_cat %s' % sub_cat.url

            self.collect_results_and_clean()

            # success!
            msg = "Finished at {0}!".format(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            send_sms(msg)
            print msg
        except Exception as e:
            error = "Failure {0} at {1}".format(e, datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            print error
            send_sms(error)

    def visit_subcat(self, cat):
            # set up filesystem
            path = self.create_node(cat)

            #try:
            if not os.path.exists(path + "/metadata.json"):
                cat.collect_urls_for_category()
                # Save metadata
                cat.save(path=path)
            else:
                # read from file
                #try:
                cat.load_from_file(path)
                #except ValueError as e:
                #print 'Problem reading metadata ... repulling: %s' % e
                #cat.collect_urls_for_category()
        
            #except Exception as e:
            #    print "Erorr collecting urls for %s" % cat.title

            if self.process_items(path, cat):
                print "Processed %(num)s items for sub cat %(sub_cat)s" % {'num': len(self.items), 'sub_cat': cat.title}
            else:
                print "Problem processing items for %s ..." % cat.title
            # empty the list
            self.item_count = 1
            del self.items[:]
            self.items = []
    

    def collect_results_and_clean(self):
        today = self.year + "-" + self.month + "-" + self.day
        all_results = "data/" + today + ".csv"
        count = 0
        for dirName, subdirList, fileList in os.walk("data"):
            if dirName[-10:] == today:
                this_file = os.path.join(dirName, "prices.csv")
                if os.path.exists(this_file):
                    print "Collecting results for %s " % this_file
                    df = pd.read_csv( this_file, encoding='utf-8')

                    # Write headers if first time
                    if not os.path.exists(all_results):
                        df.to_csv(all_results, encoding='utf-8', mode='a', header=False, index=False, quoting=csv.QUOTE_ALL)
                    else:
                        df.to_csv(all_results, encoding='utf-8', mode='a', header=True, index=False, quoting=csv.QUOTE_ALL)
                    count = count + len(df)
                    #os.remove(this_file)
        print "Total items for {0}: {1}".format(today, count)
        

    def process_items(self, path, sub_cat):
        # Check to see which prices exist and remove them from the 
        #  queue if they've already been collected
        self.shorten_list_of_items(path, sub_cat)
        #   visit pages       
        self.items_to_visit = sub_cat.items    
        for link in sub_cat.items:
            self.items.append(self.parse_item(link))
            time.sleep(.2)
        
        file_path = path + "/prices.csv"

        df = pd.DataFrame([item.toDict() for item in self.items])

        # In case we have to restart a download, there may be 
        #  items already in the file
        if os.path.exists(file_path):
            df_orig = pd.read_csv(file_path, encoding='utf-8')

            if len(df.columns) == len(df_orig.columns):
                df_orig = df_orig[ ~df_orig['url'].isin(df['url'])]
                df = pd.concat([df_orig, df])
            else:
                df = df_orig

        df.to_csv(file_path, encoding='utf-8', index=False, quoting=csv.QUOTE_ALL)
        
        return(True)

    def shorten_list_of_items(self, path, sub_cat):
        path1 = path + "/prices.csv"
        path2 = "data/" + self.year + "-" + self.month + "-" + self.day + ".csv"        
        already_ran = None

        if os.path.exists(path1):
            try:
                already_ran = pd.read_csv(path1, encoding='utf-8')
            except Exception:
                print "Problem reading from file %s" % path1

        # path2 takes precedence
        if os.path.exists(path2):
            try:
                already_ran = pd.read_csv(path2, encoding='utf-8')
            except Exception:
                print "Problem reading from file %s" % path2

        old_len = len(sub_cat.items)
        
        if already_ran is not None and len(already_ran.columns) > 1:
            sub_cat.items = [item for item in sub_cat.items if item not in already_ran['url'].tolist()]
        
        print "Found an existing prices file. Removing duplicates ... \
                old len {0}, new len {1}".format(old_len, len(self.items))

    def collect_categories(self):
        url = 'http://www.kohls.com/feature/sitemapmain.jsp'

        # Get a mapping of all cats / subcats
        cats = requests.get(url, headers=headers, verify=False)
        cats = BeautifulSoup(cats.text) 
        # Every ul is a category! neat
        all_cats = cats.find("div", {"id":"clothing-accessories"}).findAll("ul")
        
        for this_cat in all_cats:
            cat_name = this_cat.previousSibling.previousSibling.text
            cat = Category(cat_name)

            # skip some categories for now for efficiency
            if cat.title not in blacklist:
                print "Collecting links for %s ..." % cat.title

                for sub_cat in this_cat.findAll('a'):
                    sub_name = sub_cat.text
                    sub_link = 'http://www.kohls.com' + sub_cat['href'] + '&PPP=120'
                    cat.sub_categories.append(SubCategory(sub_name, cat_name, sub_link))

                self.categories.append(cat)

    def create_node(self, cat):
        #check for hierarchy
        this_path = "data/" + cat.path
        if not os.path.exists(this_path):
            os.makedirs(this_path)

        # check for day
        today = this_path + "/" + self.year + "-" + self.month + "-" + self.day

        if not os.path.exists(today):
            os.makedirs(today)
        return(today)        

    def parse_item(self, url):
        print "Parsing %(one)s of %(two)s ... %(url)s" % {"one": self.item_count, "two": len(self.items_to_visit), "url":url}

        box_r = requests.get(url, headers=headers, verify=False)
        box_soup = BeautifulSoup(box_r.text)    

        try:
            title = box_soup.find('h1', {"class":'title'}).text.strip()

            try:
                price = box_soup.select("div.sale span.price_ammount")[0].text.strip()
                orig_price = box_soup.select('div.original')[0].text.strip().replace('Original\n \n','').replace('$','')
            except Exception:
                price = box_soup.select("div.original")[0].text.strip().replace('Original\n','').replace('$', '')
                orig_price = price
                
        except Exception:
            title = "Out of Stock"
            price = 0
            orig_price = 0
        try:
            pid = re.search("(prd-[a-zA-Z0-9]+)", url).group(0)
        except AttributeError:
            pid = "bad-url"
        this_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        self.item_count = self.item_count + 1
        return(Item(title, self.current_category, self.current_sub_category, pid, price, orig_price, this_time, url))


def send_sms(msg):
    client = TwilioRestClient(config.api_key, config.api_secret) 
 
    client.messages.create(
        to=config.phone, 
        from_=from_phone, 
        body=msg,  
    )

def clean_description(string):
    string = string.replace("'", '')
    return("".join([c.lower() if c.isalpha() or c.isdigit() else '-' for c in string]).rstrip())

def set_up_browser(agent=True):
    dcap = dict(DesiredCapabilities.PHANTOMJS)
    dcap["phantomjs.page.settings.userAgent"] = (
        "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 "
    )

    try:
        del driver
    except Exception:
        "No driver"

    if agent:
        driver = webdriver.PhantomJS(executable_path='/usr/local/bin/phantomjs', desired_capabilities=dcap, service_args=['--ignore-ssl-errors=true', '--load-images=no']) 
    else:
        driver = webdriver.PhantomJS(executable_path='/usr/local/bin/phantomjs', service_args=['--ignore-ssl-errors=true', '--load-images=no']) 
    
    driver.set_window_size(1024, 768) # optional
    return(driver)
    

def parse_javascript_selenium(url, screen_shot=None):
    driver = set_up_browser()
    
    driver.get(url)

    time.sleep(3)
    
    if screen_shot is not None:
        driver.save_screenshot('%s.png' % screen_shot)
    else:
        driver.save_screenshot('screenz.png') 
        
    res = BeautifulSoup(driver.page_source)
    driver.quit()
    
    # Really makes sure it's dead
    # p = os.popen('pgrep phantomjs | xargs kill',"r")
    
    return(res)

if __name__ == '__main__':
    crawler = AppCrawler()
    crawler.crawl()
