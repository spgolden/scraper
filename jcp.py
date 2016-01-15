import os
import pandas as pd
import requests
import unicodedata
import csv
import datetime
import time
import re
import sys
import math
import json
import config
import csv
from twilio.rest import TwilioRestClient
import grequests 
import lxml.html
from lxml.etree import tostring
#import ipdb; ipdb.set_trace()

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

class Category:
    def __init__(self, title, url):
        self.title = title
        self.url = url
        self.sub_categories = []

    def get_sub_cats(self, content):
        html = lxml.html.fromstring(content)
        # Grab categorie titles
        links = html.xpath('//*[@id="side_navigation"]/ul/li')
        cur_section = ''
        for link in links:
            # Check if an h2
            this_header = link.find('h2')
            if this_header is not None:
                cur_section = this_header.text_content().strip(' \t\r\n ')
                print cur_section
            else:
                if cur_section == "SHOP CLOTHING":
                    #  Grab categories
                    href = 'http://www.jcpenney.com' + link.xpath('a/@href')[0]
                    title = link.xpath('a/text()')[0]
                    print "appending... %s" % title
                    self.sub_categories.append(SubCategory(title, href, self.title))

class SubCategory:
    def __init__(self, title, url, parent):
        self.title = title
        self.url = url
        self.jcpClasses = []
        self.parent = parent
        self.path = clean_description(parent) + "/" + clean_description(title)
    
    def parse_links(self, link):
        href = 'http://www.jcpenney.com' + link.xpath('a/@href')[0] + '&pageSize=72'
        title = link.xpath('a/text()')[0]
        print "\tappending... %s" % title
        self.jcpClasses.append(JCPClass(title, href))

    def get_classes(self, content):
        html = lxml.html.fromstring(content)
        # Grab categorie titles
        links = html.xpath('//*[@id="UL600000"]/li')

        if self.title != 'dress shirts & ties':
            for link in links:
                #  Grab categories
                self.parse_links(link)

            if len(links) == 0:
                links = html.xpath('//*[@id="UL5"]/li')
                for link in links:
                    self.parse_links(link)

            if len(links) == 0:
                links = html.xpath('//*[@id="UL4"]/li')
                for link in links:
                    self.parse_links(link)
        else:
            if len(links) == 0:
                links = html.xpath('//*[@id="UL5"]/li')
                for link in links:
                    self.parse_links(link)

        if self.title == 'jeans':
            links = html.xpath('//*[@id="UL587"]/li')
            for link in links:
                self.parse_links(link)

        if self.title == 'workout clothes':
            links = html.xpath('//*[@id="side_navigation"]/ul/li')
            cur_section = ''
            for link in links:
                # Check if an h2
                this_header = link.find('h2')
                if this_header is not None:
                    cur_section = this_header.text_content().strip(' \t\r\n ')
                    print '\t\t' + cur_section
                else:
                    if cur_section == "SHOP CLOTHING":
                        #  Grab categories
                        href = 'http://www.jcpenney.com' + link.xpath('a/@href')[0] + '&pageSize=72'
                        title = link.xpath('a/text()')[0]
                        print "appending... %s" % title
                        self.jcpClasses.append(JCPClass(title, href))

    def save(self, path):
        with open(path + "/metadata.json", "wb") as f:
            all_classes = []
            for c in self.jcpClasses:
                all_classes.append({
                    "title": c.title,
                    "url": c.url
                })

            this_obj = {
                "title": self.title,
                "parent": self.parent,
                "url": self.url,
                "path": self.path,
                "classes": all_classes
            }
            f.write(json.dumps(this_obj))

    def load_from_file(self, path):
        with open(path + "/metadata.json", "rb") as f:
            this_obj = json.loads(f.read())

        classes = this_obj['classes']
        self.title = this_obj['title']
        self.parent = this_obj['parent']
        self.url = this_obj['url']
        self.path = this_obj['path']
        for c in classes:
            self.jcpClasses.append(JCPClass('', c))
   
class JCPClass:
    def __init__(self, title, url):
        self.title = title
        self.url = url
        self.items = []
        self.sub_cat = ''
        self.cat = ''
    
    def toDict(self):
        all_items = []
        for i in self.items:
            this_obj = {
                "title": self.title,
                "pid": i,
                "category": self.cat,
                "sub_category": self.sub_cat,
            }

            all_items.append(this_obj)
        return(all_items)

    def collect_items(self, content):
        # loop through each page and grab ppId
        html = lxml.html.fromstring(content)
        rows =  html.xpath('//*[@id="xgnContent"]/div/div[1]/div[3]/div[1]/div/ul/li')
        
        for row in rows:
            links = row.xpath('./div/div/div[2]/span[1]/a/@href')
            links2 = row.xpath('./div/div/div[3]/span[1]/a/@href')
            
            for link in links:
                #grab the ppId
                pid = re.search("(?<=ppId=)(.*)(?=&catId)", link).group(0)
                #print '\t\t\t\t' + pid
                self.items.append(pid)

            if links2:
                for link in links2:
                    pid = re.search("(?<=ppId=)(.*)(?=&catId)", link).group(0)
                    self.items.append(pid)

class AppCrawler:
    def __init__(self):
        self.categories = []
        self.item_count = 1
    
    def create_node(self, sub_cat):
        #check for hierarchy
        this_path = "data-jcp/" + sub_cat.path
        if not os.path.exists(this_path):
            os.makedirs(this_path)

        if not os.path.exists(this_path):
            os.makedirs(this_path)
        return(this_path) 

    def crawl(self, debug=False, async=True):
        self.async = async
        # wrap everything in a notifcation...
        if True:
            url = 'http://www.jcpenney.com/men/dept.jump?id=dept20000014&cmJCP_T=G1&cmJCP_C=D5B'
            self.categories.append(Category("Men's", url))
            #import ipdb; ipdb.set_trace()
            for cat in self.categories:
                # visit the page
                page = requests.get(url, headers=headers, verify=False)
                cat.get_sub_cats(page.content)

                sub_cats = cat.sub_categories

                for sub_cat in sub_cats:
                    path = self.create_node(sub_cat)
                    if not os.path.exists(path + "/metadata.json"):
                        page = requests.get(sub_cat.url, headers=headers, verify=False)
                        sub_cat.get_classes(page.content)

                        # Save metadata
                        #sub_cat.save(path=path)
                    else:
                        #sub_cat.load_from_file(path)
                        page = requests.get(sub_cat.url, headers=headers, verify=False)
                        sub_cat.get_classes(page.content)

                    file_path = path + 'data.csv'
                    if not os.path.exists(file_path):
                        for jcp in sub_cat.jcpClasses:
                            print '\t\t\t' + jcp.title
                            try:
                                page = requests.get(jcp.url, headers=headers, verify=False)
                                jcp.collect_items(page.content)
                                
                                this_page = lxml.html.fromstring(page.content)
                                total_items = this_page.xpath('//*[@id="xgnContent"]/div/div[1]/div[2]/div[1]/div[2]/p/text()')[0].strip(' \t\r\n ')
                                total_items = int(re.search("(?<=of ).*$", total_items).group(0))

                                # Get the total number of pages
                                pages = math.ceil(total_items / 72.0)
                                page_args = [72*i for i in range(1, int(pages))]

                                urls_to_visit = []
                                base_url = jcp.url[0:len(jcp.url)-23]
                                for page in page_args:
                                    new_url = base_url + "Nao={0}&pageSize=72&pN={1}&extDim=true".format(page, (page/72 + 1))
                                    urls_to_visit.append(new_url)
                                    
                                chunk_size = 20
                                chunks=[urls_to_visit[x:x+chunk_size] for x in range(0, len(urls_to_visit), chunk_size)]

                                for chunk in chunks:
                                    rs = (grequests.get(u) for u in chunk)
                                    responses = grequests.map(rs)
                                    print "Processing chunks ... {0}".format(chunk)
                                    for response in responses:
                                        print "Parsing %(one)s of %(two)s " % {"one": self.item_count, "two": len(urls_to_visit)}
                                        jcp.collect_items(response.content)
                                        self.item_count = self.item_count + 1

                                jcp.sub_cat = sub_cat.title
                                jcp.cat = cat.title
                                self.item_count = 1
                            except Exception as e:
                                print 'Bad URL {0} {1}'.format(e, jcp.url)

                        master_list = []
                        for jcp in sub_cat.jcpClasses:
                            master_list.extend(jcp.toDict())
                        df = pd.DataFrame(master_list)
                        df.to_csv(file_path, encoding='utf-8', index=False, quoting=csv.QUOTE_ALL)
                    else:
                        print "Already loaded!"

                    clean_and_compile('data-jcp/mens')

def clean_and_compile(path):
    count = 0
    all_results = path + 'all_items.csv'
    for dirName, subdirList, fileList in os.walk(path):
        for this_file in fileList:
            if re.search('(?=.csv)', this_file):
                # it's a match!
                to_read = os.path.join(dirName, this_file)
                print "Collecting results for %s " % to_read
                df = pd.read_csv(to_read, encoding='utf-8')

                if not os.path.exists(all_results):
                    df.to_csv(all_results, encoding='utf-8', header=True, index=False, quoting=csv.QUOTE_ALL)
                else:
                    df.to_csv(all_results, encoding='utf-8', mode='a', header=False, index=False, quoting=csv.QUOTE_ALL)
                
                count = count + len(df)
    
    print "Total items for %s" % count



def clean_description(string):
    string = string.replace("'", '')
    return("".join([c.lower() if c.isalpha() or c.isdigit() else '-' for c in string]).rstrip())

if __name__ == '__main__':
    crawler = AppCrawler()
    crawler.crawl()
