import logging
import threading
import time
import sys
import os
import subprocess
import requests
import MySQLdb as MySQLdatabase
import mysql.connector as sqlConnector
from multiprocessing import Pool    #Solves an issue caused by multi-threading 'Requests_HTML'
from requests_html import HTMLSession
from flask import Flask, render_template, request
from flask.sessions import SecureCookieSessionInterface
from flask_mysqldb import MySQL
from bs4 import BeautifulSoup
from bs4.element import Tag
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def flask():

    logging.info("STARTING FLASK SERVER")
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    app = Flask(__name__)
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    @app.route("/")

    def index():

        db= sqlConnector.connect(
        host="localhost",
        user="root",
        passwd="1907ed",
        )

        mysql = MySQL()
        mysql.init_app(app)

        cursor2 = db.cursor()
        cursor2.execute("USE pythonapp")

        jobs = []
        cursor2.execute("SELECT * FROM jobs")
        for careers in cursor2:
            jobs.append(careers)

        attacksToday = 0
        cursor2.execute("SELECT * FROM stats")
        for stats in cursor2:
            attacksToday = stats[0]

        articles = []
        cursor2.execute("SELECT * FROM articles")
        for news in cursor2:
            articles.append(news)

        livenews = []
        cursor2.execute("SELECT * FROM articles WHERE timestamp >= NOW() - INTERVAL 6 HOUR ORDER BY 5 DESC LIMIT 20;")
        for live in cursor2:
            livenews.append(live)

        attackHistory = []
        cursor2.execute("SELECT * FROM attackHistory ORDER BY 5 DESC;")
        for attacks in cursor2:
            attackHistory.append(attacks)

        topCountries = []
        cursor2.execute("SELECT * FROM topCountries")
        for countries in cursor2:
            topCountries.append(countries)

        cryptos = []
        cursor2.execute("SELECT * FROM crypto")
        for coins in cursor2:
            cryptos.append(coins)

        cursor2.close()

        db.close()

        return render_template('index.html', attacksToday=attacksToday, jobs=jobs, articles=articles, livenews=livenews, attackHistory=attackHistory, topCountries=topCountries, cryptos=cryptos)
        
        @app.after_request
        def add_header(response):
            response.cache_control.max_age = 31536000
            return response    

    if __name__ == "__main__":
        app.run()

    logging.info("FLASK SERVER ENDED!")

    

def timestampConvert(input):
    months=["January","February","March","April","May","June","July","August","September","October","November","December"]
    if(input[0] == " "):
        input = input.replace(" ","",1)
    output = input.replace(' ','-')
    output = output.upper()
    for i in range(0,len(months)):
        month = output.find(months[i].upper())
        if(month != -1):
            month = i+1
            year = output[len(output)-4:len(output)]
            date = output[0:output.find("-")]
            timestamp = str(year)+"-"+str(month)+"-"+str(date)+" 00:00:00"
            return timestamp

def jsScraping(iter):
    if iter == 0:
        session = HTMLSession()
        session.browser
        r = session.get('https://www.fireeye.com/cyber-map/threat-map.html')
        r.html.render(timeout=30)
        r.close()
        extract = r.html.find('#totalAttacksToday')
        for item in extract:
            stat = item.text
        return stat

def htmlScraping():
    logging.info("GATHERING DATA...")

    printProgressBar(0, 1, prefix = 'Progress:', suffix = 'Complete', length = 50)

    start = round(time.time() * 1000)
    #Function to cleanup extracted HTML data

    def cleanUp(maxRange,extract,tagSearch):
       cleanExtract = []
       for i in range(0, maxRange):
            extract = soup.find_all(tagSearch)[i].text
            cleanExtract.append(' '.join(extract.split()))
       return cleanExtract

    URL = 'https://haveibeenpwned.com/PwnedWebsites'
    #print("--HaveIBeenPwned--")
    page = requests.get(URL)

    soup = BeautifulSoup(page.content, 'html.parser')

    #Parse attack names

    tagSearch = 'h3'
    extract = soup.find_all(tagSearch)
    maxRange = len(extract)

    attackNames = cleanUp(maxRange,extract,tagSearch)

    printProgressBar(0 + 0.05, 1, prefix = 'Progress:', suffix = 'Complete', length = 50)

    #Parse attack descriptions

    attackDsc = []
    tagSearch = 'p'
    example = soup.find_all("div", {"class": "col-sm-10"})
    for div in example:
        extract = div.find(tagSearch).text
        attackDsc.append(extract)

    printProgressBar(0 + 0.09, 1, prefix = 'Progress:', suffix = 'Complete', length = 50)

    #Parse attack date, no. of compromised, type of data, and images

    attackTimestamp = []
    attackDate = []
    numOfComp = []
    dataTypes = []
    imgURLs = []

    extract_div = soup.find_all("div", {"class": "col-sm-10"})
    for div in extract_div:
        extract_p = div.find_all('p')[1]
        i = 0
        for strong_tag in extract_p('strong'):
            if(i == 1):
                attackDate.append(strong_tag.next_sibling)
                attackTimestamp.append(timestampConvert(strong_tag.next_sibling))
            elif(i == 2):
                numOfComp.append(strong_tag.next_sibling)
            elif(i == 3):
                dataTypes.append(strong_tag.next_sibling)
            i+=1

    printProgressBar(0 + 0.12, 1, prefix = 'Progress:', suffix = 'Complete', length = 50)

    extract_div = soup.find_all("div", {"class": "col-sm-2"})
    for div in extract_div:
        extract_img = div.find_all('img')
        for image in extract_img:
            imgURLs.append("https://haveibeenpwned.com" + image['src'])


    maxRange = len(attackDate)

    printProgressBar(0 + 0.14, 1, prefix = 'Progress:', suffix = 'Complete', length = 50)

    #Parse LinkedIn Jobs

    URL = 'https://www.linkedin.com/jobs/search?keywords=Cyber&location=Ireland&geoId=&trk=public_jobs_jobs-search-bar_search-submit&position=1&pageNum=0'
    page = requests.get(URL)

    soup = BeautifulSoup(page.content, 'html.parser')

    extract_jobs = soup.find_all('li', attrs={'class': 'result-card job-result-card result-card--with-hover-state'})

    jobTitles = []
    jobCompanies = []
    jobLocations = []
    jobPosted = []
    jobURL = []
    imageURL = []

    for jobs in extract_jobs:
        jobSoup = BeautifulSoup(str(jobs), 'lxml')
        extract_jobTitles = jobSoup.find_all('span', attrs={'class': 'screen-reader-text'})
        extract_jobURL = jobSoup.find_all('a', attrs={'class': 'result-card__full-card-link'})
        extract_imageURL = jobSoup.find_all('img')
        try:
            extract_jobCompanies = jobSoup.find_all('a', attrs={'class': 'result-card__subtitle-link job-result-card__subtitle-link'})
            jobCompanies.append(extract_jobCompanies[0].text)
        except:
            extract_jobCompaniesNoURL = jobSoup.find_all('h4', attrs={'class': 'result-card__subtitle job-result-card__subtitle'})
            jobCompanies.append(extract_jobCompaniesNoURL[0].text)

        printProgressBar(0 + 0.27, 1, prefix = 'Progress:', suffix = 'Complete', length = 50)

        extract_jobLocations = jobSoup.find_all('span', attrs={'class': 'job-result-card__location'})
        extract_jobPosted = jobSoup.find_all('time', attrs={'class': 'job-result-card__listdate'})

        for i in range(0,len(extract_jobTitles)):
            jobTitles.append(extract_jobTitles[i].text)

        printProgressBar(0 + 0.33, 1, prefix = 'Progress:', suffix = 'Complete', length = 50)

        for i in range(0,len(extract_jobLocations)):
            jobLocations.append(extract_jobLocations[i].text)

        printProgressBar(0 + 0.35, 1, prefix = 'Progress:', suffix = 'Complete', length = 50)

        for i in range(0,len(extract_jobPosted)):
            jobPosted.append(extract_jobPosted[i].text)

        printProgressBar(0 + 0.37, 1, prefix = 'Progress:', suffix = 'Complete', length = 50)

        for i in range(0,len(extract_jobURL)):
            jobURL.append(extract_jobURL[i]['href'])

        printProgressBar(0 + 0.39, 1, prefix = 'Progress:', suffix = 'Complete', length = 50)

        for i in range(0,len(extract_imageURL)):
            imageURL.append(extract_imageURL[i]['data-delayed-url'])

    printProgressBar(0 + 0.41, 1, prefix = 'Progress:', suffix = 'Complete', length = 50)
    
    #Parse Threat Map

    iter = range(2)
    pool = Pool(processes=1)
    extract = pool.map(jsScraping, iter)
    pool.terminate()
    pool.join()
    attacksToday = extract[0]

    printProgressBar(0 + 0.45, 1, prefix = 'Progress:', suffix = 'Complete', length = 50)

    #Google News Search Cyber Attacks

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging']);

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(60)
    url = "https://consent.google.com/ml?continue=https://news.google.com/search?q%3Dcyber-attack%2Bwhen:24h%26hl%3Den-IE%26gl%3DIE%26ceid%3DIE:en%26num%3D5&gl=IE&hl=en-IE&pc=n&src=1" + "&num=" + str(5)

    driver.get(url)
    button = driver.find_elements_by_css_selector('.U26fgb.YOnsCc.waNn5b.ZqhUjb.ztUP4e.tHCKTc.cd29Sd.w0hkKb.naBZYc.BZL7If.M9Bg4d')    
    for clicks in button:
        clicks.click()
        time.sleep(2)

    time.sleep(5)
    soup = BeautifulSoup(driver.page_source,'lxml')
    result_headlines = soup.find_all('div', attrs={'class': 'xrnccd F6Welf R7GTQ keNKEd j7vNaf'})

    imgURL = []
    titles = []
    count = 0
    for headlines in result_headlines:
        headlineSoup = BeautifulSoup(str(headlines), 'lxml')
        result_h3 = headlineSoup.find_all('h3', attrs={'class': 'ipQwMb ekueJc RD0gLb'})
        result_h4 = headlineSoup.find_all('h4', attrs={'class': 'ipQwMb ekueJc RD0gLb'})
        result_img_list = soup.find_all('img', attrs={'class': 'tvs3Id QwxBBf'})
        for item1 in result_h3:
            
            newTitle = item1.text.replace('‘',"'")
            newTitle = newTitle.replace('’',"'")
            newTitle = newTitle.replace('–','-')
            newTitle = newTitle.replace('—','-')
            newTitle = newTitle.replace('í','i')
            titles.append(newTitle)
            imgURL.append(result_img_list[count]['src'])
            count += 1
        for item2 in result_h4:
            newTitle = item2.text.replace('‘',"'")
            newTitle = newTitle.replace('’',"'")
            newTitle = newTitle.replace('–','-')
            newTitle = newTitle.replace('—','-')
            newTitle = newTitle.replace('í','i')
            titles.append(newTitle)
            imgURL.append("")

    printProgressBar(0 + 0.50, 1, prefix = 'Progress:', suffix = 'Complete', length = 50)

    headlineSoup = BeautifulSoup(str(result_headlines), 'lxml')
    result_source = headlineSoup.find_all('a', attrs={'class': 'wEwyrc AVN2gc uQIVzc Sksgp'})
    result_time_list = headlineSoup.find_all('time', attrs={'class': 'WW6dff uQIVzc Sksgp'})
    result_img_list = soup.find_all('img', attrs={'class': 'tvs3Id QwxBBf'})
    result_articles_list = headlineSoup.find_all('a', attrs={'class': 'VDXfz'})

    sources = []
    for item3 in result_source:
        sources.append(item3.text)

    printProgressBar(0 + 0.52, 1, prefix = 'Progress:', suffix = 'Complete', length = 50)
    timeAgo = []
    timeStamp = []
    for item4 in result_time_list:
        timeAgo.append(item4.text)
        newDate = item4['datetime'].replace('T',' ')
        newDate = newDate.replace('Z','')
        timeStamp.append(newDate)

    printProgressBar(0 + 0.57, 1, prefix = 'Progress:', suffix = 'Complete', length = 50)

    for i in range(0,count):
        result_img_list.pop(i)

    for item5 in result_img_list:
        imgURL.append(item5['src'])

    printProgressBar(0 + 0.59, 1, prefix = 'Progress:', suffix = 'Complete', length = 50)

    artURL = []
    for item6 in result_articles_list:
        insertURL = "http://www.news.google.com/" + item6['href']
        artURL.append(insertURL)

    printProgressBar(0 + 0.61, 1, prefix = 'Progress:', suffix = 'Complete', length = 50)

    result_articles = soup.find_all('div', attrs={'class': 'NiLAwe y6IFtc R7GTQ keNKEd j7vNaf nID9nc'})
    headlineSoup = BeautifulSoup(str(result_articles), 'lxml')
    result_h3 = headlineSoup.find_all('h3', attrs={'class': 'ipQwMb ekueJc RD0gLb'})
    result_source = headlineSoup.find_all('a', attrs={'class': 'wEwyrc AVN2gc uQIVzc Sksgp'})
    result_time_list = headlineSoup.find_all('time', attrs={'class': 'WW6dff uQIVzc Sksgp'})
    result_img_list = soup.find_all('img', attrs={'class': 'tvs3Id QwxBBf'})
    result_articles_list = headlineSoup.find_all('a', attrs={'class': 'VDXfz'})
        
    for item1 in result_h3:
        newTitle = item1.text.replace('‘',"'")
        newTitle = newTitle.replace('’',"'")
        newTitle = newTitle.replace('–','-')
        newTitle = newTitle.replace('—','-')
        newTitle = newTitle.replace('í','i')
        titles.append(newTitle)

    printProgressBar(0 + 0.64, 1, prefix = 'Progress:', suffix = 'Complete', length = 50)

    for item3 in result_source:
        sources.append(item3.text)

    printProgressBar(0 + 0.66, 1, prefix = 'Progress:', suffix = 'Complete', length = 50)

    for item4 in result_time_list:
        timeAgo.append(item4.text)
        newDate = item4['datetime'].replace('T',' ')
        newDate = newDate.replace('Z','')
        timeStamp.append(newDate)

    printProgressBar(0 + 0.70, 1, prefix = 'Progress:', suffix = 'Complete', length = 50)

    for item5 in result_img_list:
        imgURL.append(item5['src'])

    printProgressBar(0 + 0.73, 1, prefix = 'Progress:', suffix = 'Complete', length = 50)

    for item6 in result_articles_list:
        insertURL = "http://www.news.google.com/" + item6['href']
        artURL.append(insertURL)

    printProgressBar(0 + 0.74, 1, prefix = 'Progress:', suffix = 'Complete', length = 50)

    if(len(imgURL) < len(artURL)):
        for i in range(0,len(artURL) - len(imgURL)):
            imgURL.append('NULL')

    printProgressBar(0 + 0.75, 1, prefix = 'Progress:', suffix = 'Complete', length = 50)

    #Checkpoint ThreatMap

    url = "https://threatmap.checkpoint.com/"

    driver.set_window_size(1600,1000)
    driver.set_page_load_timeout(60)
    driver.get(url)
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source,'lxml')
    topCountries = []
    result_divs = soup.find_all('div', attrs={'class': 'top-target-entity'})
    for divs in result_divs:
        countriesSoup = BeautifulSoup(str(divs), 'lxml')
        result_countries = countriesSoup.find_all('div', attrs={'class': 'icon-and-title interactive'})
        for countries in result_countries:
            topCountries.append(countries.text)

    printProgressBar(0 + 0.77, 1, prefix = 'Progress:', suffix = 'Complete', length = 50)

    #Crypto Currencies

    url = "https://coinmarketcap.com/"

    driver.set_page_load_timeout(60)
    driver.get(url)
    driver.execute_script("window.scrollTo(0,700)")
    time.sleep(1)
    soup = BeautifulSoup(driver.page_source,'lxml')
    driver.close()
    result_coinNames = soup.find_all('p', attrs={'class': 'sc-1eb5slv-0 iJjGCS'})

    coinNames = []
    for names in result_coinNames:
            coinNames.append(names.text)

    printProgressBar(0 + 0.82, 1, prefix = 'Progress:', suffix = 'Complete', length = 50)

    result = soup.find_all('div', attrs={'class': 'price___3rj7O'})
    priceSoup = BeautifulSoup(str(result),'lxml')

    result_coinPrices = priceSoup.find_all('a', attrs={'class': 'cmc-link'})

    coinPrices = []
    for prices in result_coinPrices:
            coinPrices.append(prices.text)

    printProgressBar(0 + 0.86, 1, prefix = 'Progress:', suffix = 'Complete', length = 50)

    result = soup.find_all('tr', attrs={'class': None})[1:]

    coinChanges = []

    for coins in result:
        changeSoup = BeautifulSoup(str(coins), 'lxml')
        try:
            result_coinChanges = changeSoup.find_all('span', attrs={'class': 'sc-1v2ivon-0 jvNdfB'})[0]
            insert = "-" + result_coinChanges.text
            insert = insert.replace('%','')
            coinChanges.append(insert)
        except:
            result_coinChanges = changeSoup.find_all('span', attrs={'class': 'sc-1v2ivon-0 fJLBDK'})[0]
            insert = result_coinChanges.text.replace('%','')
            coinChanges.append(insert)

    printProgressBar(0 + 0.90, 1, prefix = 'Progress:', suffix = 'Complete', length = 50)

    #Upload data to database

    db = MySQLdatabase.connect(host="localhost",
                         user="app",
                         passwd="1907ed",
                         db="pythonapp",
                         charset="utf8mb4")
    cur = db.cursor()
    cur.execute('truncate table attackHistory')
    cur.execute('truncate table stats')
    cur.execute('truncate table articles')
    cur.execute('truncate table topCountries')
    cur.execute('truncate table jobs')
    cur.execute('truncate table crypto')
    db.commit()
    printProgressBar(0 + 0.95, 1, prefix = 'Progress:', suffix = 'Complete', length = 50)
    cur.execute('INSERT INTO stats (attacksToday) VALUES (%s)', (attacksToday.encode("utf-8"),))
    

    for i in range(0,maxRange):
        cur.execute('INSERT INTO attackHistory (victim, brief, date, timestamp, numComp, compData, imgURL) VALUES (%s, %s, %s, %s, %s, %s, %s)', (attackNames[i].encode("utf-8"), attackDsc[i].encode("utf-8"), attackDate[i].encode("utf-8"), attackTimestamp[i], numOfComp[i].encode("utf-8"), dataTypes[i].encode("utf-8"), imgURLs[i].encode("utf-8")))
    
    checkList = ["CYBER","SECURITY","HACK","HACKED","DATA","HACKER","BREACH","CYBERATTACKS","CYBERATTACK","CYBER-ATTACK","CYBER-ATTACKS","DEFENCE","DEFENSE","BREACH","BREACHED","WEBSITE","ONLINE","INTERNET","COMPUTER","RANSOM","VIRUS","MALWARE","ATTACK","ATTACKS"]

    for i in range(0,len(titles)):
        if(i < 15):
            cur.execute('INSERT INTO articles (title, source, timeAgo, timestamp, imgURL, artURL) VALUES (%s, %s, %s, %s, %s, %s)', (titles[i].encode("utf-8"), sources[i].encode("utf-8"), timeAgo[i].encode("utf-8"), timeStamp[i], imgURL[i].encode("utf-8"), artURL[i].encode("utf-8")))
        else:
            if any(substring in titles[i].upper() for substring in checkList):
                cur.execute('INSERT INTO articles (title, source, timeAgo, timestamp, imgURL, artURL) VALUES (%s, %s, %s, %s, %s, %s)', (titles[i].encode("utf-8"), sources[i].encode("utf-8"), timeAgo[i].encode("utf-8"), timeStamp[i], imgURL[i].encode("utf-8"), artURL[i].encode("utf-8")))

    if len(jobPosted) < len(jobTitles):
        for i in range (0,len(jobTitles) - len(jobPosted)):
            jobPosted.append("Unknown")

    for i in range(0,len(jobTitles)):
        cur.execute('INSERT INTO jobs (titles, company, location, timePosted, jobURL, imageURL) VALUES (%s, %s, %s, %s, %s, %s)', (jobTitles[i].encode("utf-8"), jobCompanies[i].encode("utf-8"), jobLocations[i].encode("utf-8"), jobPosted[i].encode("utf-8"), jobURL[i].encode("utf-8"), imageURL[i].encode("utf-8")))
                
    for i in range(0,len(topCountries)):
        cur.execute('INSERT INTO topCountries (countries) VALUES (%s)', (topCountries[i],))

    for i in range(0,len(coinNames)):
        cur.execute('INSERT INTO crypto (coinNames, coinPrices, coinChanges) VALUES (%s, %s, %s)', (coinNames[i].encode("utf-8"), coinPrices[i].encode("utf-8"), coinChanges[i].encode("utf-8")))

    db.commit()
    end = round(time.time() * 1000)
    printProgressBar(0 + 1, 1, prefix = 'Progress:', suffix = 'Complete', length = 50)
    print("\nITERATION FINISHED (", "%.2f" % ((end-start) / 1000.0), "s)")
    print("----------------------------------------")
    subprocess.run('taskkill /F /IM chrome.exe',capture_output=True)
    #Main

if __name__ == "__main__":

    def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)

    timing = 10
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")

    t1 = threading.Thread(target=flask)
    t1.start()
    time.sleep(2)
    print("--------------------------------------------------")
    logging.info("WEB SCRAPER STARTING")
    print("\nData is refreshed after", timing, "second(s)")
    print("--------------------------------------------------")
    while True:
        t2 = threading.Thread(target=htmlScraping)
        t2.start()
        t2.join()
        time.sleep(timing)

    logging.info("Main    : all done")