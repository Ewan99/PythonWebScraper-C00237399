import logging
import threading
import time
import sys
import requests
import MySQLdb
from multiprocessing import Pool    #Solves an issue with multi-threading Requests_HTML
from requests_html import HTMLSession
from flask import Flask, render_template
from flask_mysqldb import MySQL
from bs4 import BeautifulSoup
from bs4.element import Tag
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def flask():

    logging.info("STARTING FLASK SERVER")
    app = Flask(__name__)
    x = 20
    @app.route("/")
    def index():
        return render_template('index.html')

    if __name__ == "__main__":
        app.run()

    logging.info("FLASK SERVER ENDED!")

def jsScraping(iter):
    if iter == 0:
        session = HTMLSession()
        session.browser
        r = session.get('https://www.fireeye.com/cyber-map/threat-map.html')
        r.html.render()
        r.close()
        extract = r.html.find('#totalAttacksToday')
        for item in extract:
            stat = item.text
        return stat

def htmlScraping():
    logging.info("GATHERING DATA...")
    start = round(time.time() * 1000)
    #Function to cleanup extracted HTML data

    def cleanUp(maxRange,extract,tagSearch):
       cleanExtract = []
       for i in range(0, maxRange):
            extract = soup.find_all(tagSearch)[i].text
            cleanExtract.append(' '.join(extract.split()))
       return cleanExtract

    #Retrieve HTML

    URL = 'https://haveibeenpwned.com/PwnedWebsites'
    page = requests.get(URL)

    soup = BeautifulSoup(page.content, 'html.parser')

    #Parse attack names - WORKING

    tagSearch = 'h3'
    extract = soup.find_all(tagSearch)
    maxRange = len(extract)

    attackNames = cleanUp(maxRange,extract,tagSearch)

    #Parse attack descriptions - WORKING

    attackDsc = []
    tagSearch = 'p'
    example = soup.find_all("div", {"class": "col-sm-10"})
    for div in example:
        extract = div.find(tagSearch).text
        attackDsc.append(extract)

    #Parse attack date, no. of compromised, and type of data - WORKING

    attackDate = []
    numOfComp = []
    dataTypes = []
    tagSearch = 'p'
    example = soup.find_all("div", {"class": "col-sm-10"})
    for div in example:
        example = div.find_all(tagSearch)[1]
        i = 0
        for strong_tag in example('strong'):
            if(i == 0):
                attackDate.append(strong_tag.next_sibling)
            elif(i == 2):
                numOfComp.append(strong_tag.next_sibling)
            elif(i == 3):
                dataTypes.append(strong_tag.next_sibling)
            i+=1

    maxRange = len(attackDate)

    #Parse Threat Map

    iter = range(2)
    pool = Pool(processes=1)
    extract = pool.map(jsScraping, iter)
    pool.close()
    pool.join()
    attacksToday = extract[0]

    #Google News Search Cyber Attacks

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging']);

    driver = webdriver.Chrome(options=chrome_options)

    google_url = "https://consent.google.com/ml?continue=https://news.google.com/search?q%3Dcyber%2Battacks%2Bwhen:24h%26hl%3Den-IE%26gl%3DIE%26ceid%3DIE:en%26num%3D5&gl=IE&hl=en-IE&pc=n&src=1" + "&num=" + str(5)
    driver.get(google_url)
    time.sleep(3)
    try:
        button = driver.find_element_by_class_name('button')
        button.click()
    except:
        None

    time.sleep(3)

    title = []
    source = []
    timeAgo = []
    timeStamp = []
    imgURL = []
    artURL = []

    soup = BeautifulSoup(driver.page_source,'lxml')
    result_title_list = soup.find_all('h3', attrs={'class': 'ipQwMb ekueJc RD0gLb'})
    result_source_list = soup.find_all('a', attrs={'class': 'wEwyrc AVN2gc uQIVzc Sksgp'})
    result_time_list = soup.find_all('time', attrs={'class': 'WW6dff uQIVzc Sksgp'})
    result_img_list = soup.find_all('img', attrs={'class': 'tvs3Id QwxBBf'})
    result_a_list = soup.find_all('a', attrs={'class': 'VDXfz'})

    for item1 in result_title_list:
        #print(len(item1.text),"\n")
        title.append(item1.text)

    for item2 in result_source_list:
        #print(item2.text,"\n")
        source.append(item2.text)

    for item3 in result_time_list:
        #print(item3.text,"\n")
        timeAgo.append(item3.text)
        newDate = item3['datetime'].replace('T',' ')
        newDate = newDate.replace('Z','')
        #print(newDate)
        timeStamp.append(newDate)

    for item4 in result_img_list:
        #print(item4['src'],"\n")
        imgURL.append(item4['src'])

    for item5 in result_a_list:
        #print(item5['href'],"\n")
        insertURL = "http://www.news.google.com/" + item5['href']
        artURL.append(insertURL)

    #Upload data to database

    logging.info("UPLOADING DATA TO DATABASE...")
    db = MySQLdb.connect(host="localhost",
                         user="app",
                         passwd="1907ed",
                         db="pythonapp")
    cur = db.cursor()
    cur.execute('truncate table attackHistory')
    cur.execute('truncate table stats')
    cur.execute('truncate table articles')
    db.commit()
    cur.execute('INSERT INTO stats (attacksToday) VALUES (%s)', (attacksToday.encode("utf-8"),))

    for i in range(0,maxRange):
        cur.execute('INSERT INTO attackHistory (victim, brief, date, numComp, compData) VALUES (%s, %s, %s, %s, %s)', (attackNames[i].encode("utf-8"), attackDsc[i].encode("utf-8"), attackDate[i], numOfComp[i], dataTypes[i]))

    if(len(imgURL) < len(artURL)):
        for i in range(0,len(artURL) - len(imgURL)):
            imgURL.append('NULL')
    
    for i in range(0,len(title)): 
        cur.execute('INSERT INTO articles (title, source, timeAgo, timestamp, imgURL, artURL) VALUES (%s, %s, %s, %s, %s, %s)', (title[i].encode("utf-8"), source[i].encode("utf-8"), timeAgo[i].encode("utf-8"), timeStamp[i], imgURL[i].encode("utf-8"), artURL[i].encode("utf-8")))
   
    db.commit()
    end = round(time.time() * 1000)
    print("ITERATION FINISHED (", "%.2f" % ((end-start) / 1000.0), "s)")
    print("----------------------------------------")

    #Main

if __name__ == "__main__":
    timing = 10
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")

    t1 = threading.Thread(target=flask)
    t1.start()
    time.sleep(2)
    print("--------------------------------------------------")
    logging.info("WEB SCRAPER STARTING")
    print("\nScraping occurs after", timing, "second(s) of each iteration")
    print("--------------------------------------------------")
    while True:
        t2 = threading.Thread(target=htmlScraping)
        t2.start()
        t2.join()
        time.sleep(timing)

    logging.info("Main    : all done")