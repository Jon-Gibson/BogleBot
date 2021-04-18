from urllib.request import urlopen
import re
import html

def getStockData(stockSymbol):
    page = urlopen("http://finance.yahoo.com/q/pr?s=" + stockSymbol + "+profile" )
    data = page.read()
    return str(data)

def getFullName(stockSymbol, stockData):
    row = re.findall("<h1[^>]*?>(.*?)</h1>", stockData)
    if len(row) > 0:
        return html.unescape(row[0])
    else:
        return stockSymbol

def getCategory(stockSymbol, stockData):
    row = re.findall("Category</span></span></span><span [^>]*>(.*?)</span>", stockData)
    if len(row) > 0:
        return html.unescape(row[0])
    else:
        return "N/A"

def getFundFamily(stockSymbol, stockData):
    row = re.findall("Fund Family</span></span></span><span [^>]*>(.*?)</span>", stockData)
    if len(row) > 0:
        return html.unescape(row[0])
    else:
        return "N/A"

def getExpenseRatio(stockSymbol, stockData):
    row = re.findall("Annual Report Expense Ratio.*?</span></span></span><span [^>]*>(.*?)</span>", stockData)
    if len(row) > 0:
        ER = row[0]
        return ER
    else:
        return "N/A"

def findInfo(stockSymbols):
    stockSymbols = list(set(stockSymbols))
    stockSymbols.sort()
    global cache
    expenses = []
    for stockSymbol in stockSymbols:
        if not stockSymbol in cache:
            stockData = getStockData(stockSymbol)
            info = [ 
                stockSymbol, 
                getFullName(stockSymbol, stockData), 
                getExpenseRatio(stockSymbol, stockData), 
                getCategory(stockSymbol, stockData), 
                getFundFamily(stockSymbol, stockData) 
            ]
            cache[stockSymbol] = info
        else: 
            info = cache[stockSymbol]
        if info[2] != "N/A" or info[3] != "N/A" or info[4] != "N/A":
            expenses.append( info[0:4] )
        else:
            print("Skipping", stockSymbol)
    return expenses

global cache
cache = {}