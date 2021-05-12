from peewee import *
import csv
import requests
from bs4 import BeautifulSoup
import re
import json
import multiprocessing
import operator
import functools

class Stock(Model):
    symbol = CharField(primary_key = True)
    name = CharField(null = True)
    market_cap = FloatField(null = True)
    current_ratio = FloatField(null = True)
    debt_to_assets = FloatField(null = True)
    earnings_history = IntegerField(null = True)
    dividend_history = IntegerField(null = True)
    eps_growth = FloatField(null = True)
    price_to_earnings = FloatField(null = True)
    price_to_book = FloatField(null = True)
    class Meta:
        database = SqliteDatabase('data/stocks.db')

def constituents():
    with requests.Session() as s:
        file = s.get('http://www.crsp.org/files/CRSP_Constituents.csv')
        content = file.content.decode('utf-8')
        data = list(csv.reader(content.splitlines(), delimiter = ','))
    for row in data[1:]:
        index = row[2]
        if index == 'Total Market':
            symbol = row[3]
            name = row[4]
            Stock(symbol = symbol, name = name).save(force_insert = True)
        else:
            break

def soupify(url):
    html = requests.get(url)
    soup = BeautifulSoup(html.text, 'html.parser')
    return soup

def market_cap(stock): 
    soup = soupify('https://www.macrotrends.net/stocks/charts/'+stock.symbol+'//market-cap')
    stock.market_cap = float(soup.find('strong').text[1:-1])
    stock.save() 

def current_ratio(stock):           
    soup = soupify('https://www.macrotrends.net/stocks/charts/'+stock.symbol+'//current-ratio')
    stock.current_ratio = float(soup.find('tbody').find('tr').find_all('td')[3].text)
    if stock.current_ratio != 0:
        stock.save()

def debt_to_assets(stock):
    soup = soupify('https://www.macrotrends.net/stocks/charts/'+stock.symbol+'//balance-sheet')
    javascript = re.search('var originalData = (.*);', str(soup))
    array = json.loads(javascript.group(1))
    for element in array:
        if 'Total Current Assets' in element['field_name']:
            assets = float(list(element.values())[2])
        if 'Total Current Liabilities' in element['field_name']:
            liabilities = float(list(element.values())[2])
        if 'Long Term Debt' in element['field_name']:
            if list(element.values())[2] != '':
                debt = float(list(element.values())[2])
            else:
                debt = 0.0
    if assets-liabilities > 0:
        stock.debt_to_assets = round(debt/(assets-liabilities), 2)
        stock.save()

def earnings_history(stock):
    soup = soupify('https://www.macrotrends.net/stocks/charts/'+stock.symbol+'//net-income')
    rows = soup.find('tbody').find_all('tr')
    count = 0
    for row in rows:
        if not row.find_all('td')[1].text[1:]:
            break
        else:
            income = int(re.sub(',', '', row.find_all('td')[1].text[1:]))
            if income > 0:
                count += 1
            else:
                break
    stock.earnings_history = count
    stock.save()

def dividend_history(stock):
    soup = soupify('https://finance.yahoo.com/quote/'+stock.symbol+'/history?period1=-10000000000&period2=10000000000&filter=div')
    rows = soup.find_all('tr')[1:-1]
    if not rows:
        count = 0
    elif rows[0].find('td').text == 'No Dividends':
        count = 0
    else:
        target = int(rows[0].find('td').text[-4:])
        count = 0
        for row in rows:
            year = int(row.find('td').text[-4:])
            if year == target:
                count += 1
                target -= 1
    stock.dividend_history = count
    stock.save()

def eps_growth(stock):
    soup = soupify('https://www.macrotrends.net/stocks/charts/'+stock.symbol+'//eps-earnings-per-share-diluted')
    rows = soup.find('tbody').find_all('tr')
    rows = rows[:3]+rows[9:12]
    eps = [float(re.sub(',', '', row.find_all('td')[1].text[1:])) for row in rows]
    average1 = sum(eps[:3])/3
    average2 = sum(eps[-3:])/3
    if average2 > 0:
        stock.eps_growth = round(average1/average2-1, 2)
        stock.save()

def price_to_earnings(stock):
    soup = soupify('https://www.macrotrends.net/stocks/charts/'+stock.symbol+'//net-income') 
    rows = soup.find('tbody').find_all('tr')[:3]
    earnings = 0
    for row in rows: 
        earnings += int(re.sub(',', '', row.find_all('td')[1].text[1:]))
    stock.price_to_earnings = round(stock.market_cap*1000/(earnings/3), 2)
    stock.save()

def price_to_book(stock):
    soup = soupify('https://www.macrotrends.net/stocks/charts/'+stock.symbol+'//price-book')
    stock.price_to_book = float(soup.find('strong').text)
    if stock.price_to_book != 0:
        stock.save()    

class Consumer(multiprocessing.Process):
    def __init__(self, task_queue):
        multiprocessing.Process.__init__(self)
        self.task_queue = task_queue
    def run(self):
        while True:
            task = self.task_queue.get()
            if not task:
                self.task_queue.task_done()
                break
            print(self.task_queue.qsize()-3, task)
            task()
            self.task_queue.task_done()

class Task():
    def __init__(self, stock):
        self.stock = stock
    def __call__(self):
        functions = [market_cap, current_ratio, debt_to_assets, earnings_history, dividend_history, eps_growth, price_to_earnings, price_to_book]
        for function in functions:
            try:
                function(self.stock)
            except:
                pass
    def __str__(self):
        return self.stock.symbol

def scrape():
    import time
    start = time.time()

    print('Clearing database...')
    for stock in Stock.select():
        stock.delete_instance()

    print('Adding constituents...')
    constituents()

    print('Scraping data...')
    tasks = multiprocessing.JoinableQueue()
    for stock in Stock.select():
        tasks.put(Task(stock))

    consumers = [Consumer(tasks) for i in range(4)]
    for consumer in consumers:
        consumer.start()

    for i in range(4):
        tasks.put(None)
    tasks.join()

    finish = time.time()
    runtime = round(finish-start)
    print(f'Time taken: {runtime//60} minutes and {runtime%60} seconds')

def screen(dictionary):
    mc = []
    other = []
    for key in dictionary:
        if key == 'market_cap':
            for value in dictionary[key]:
                if value == 'small_cap':
                    mc.append(Stock._meta.fields[key] < 2)
                elif value == 'mid_cap':
                    mc.append(functools.reduce(operator.and_, [Stock._meta.fields[key] >= 2, Stock._meta.fields[key] <= 10]))
                else:
                    mc.append(Stock._meta.fields[key] > 10)
        else:
            field = Stock._meta.fields[key]
            if (key == 'debt_to_assets') or (key == 'price_to_earnings') or (key == 'price_to_book'):
                other.append(field <= dictionary[key])
            else:
                other.append(field >= dictionary[key])
    if mc and other:
        return [stock for stock in Stock.select().where(functools.reduce(operator.or_, mc) & functools.reduce(operator.and_, other))]
    elif mc:
        return [stock for stock in Stock.select().where(functools.reduce(operator.or_, mc))]
    elif other:
        return [stock for stock in Stock.select().where(functools.reduce(operator.and_, other))]
    else:
        return [stock for stock in Stock.select()]