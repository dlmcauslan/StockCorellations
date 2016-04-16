####                   Stock Corellations.py
''' Data science project that downloads stock data from yahoo finance, and 
calculates corellations over time.
Created: 16/04/2016
'''

import urllib2
from bs4 import BeautifulSoup
import datetime
import matplotlib.pyplot as plt
import os.path
import pandas as pd
import numpy as np
import re
import timeit

# Create stock object, with stockName and database (that data is saved to)
class Stock(object):
    def __init__(self, stockName):
        self.stockName = stockName
        day,month,year = todaysDate()
        self.URL = 'http://finance.yahoo.com/q/hp?s='+self.stockName+'&d='+month+'&e='+day+'&f='+year+'&g=d&a=01&b=01&c=1970&z=66&y='        
               
    # initialStockScrape()
    def stockScrape(self):
        # function which does the first time initialization of the stock and 
        #downloads all past stock data, returns array of dates, and array of data
        #initializes arrays
        
        #If the data has already been downloaded don't redownload it
        if  os.path.isfile(self.stockName + '_data.csv'):
            return pd.read_csv(self.stockName + '_data.csv')
        
        print self.stockName
                        
        stockDataFrame =  pd.DataFrame({'Date':[], 'Open':[], 'High':[], 'Low':[],\
                    'Close':[], 'Volume':[], 'AdjClose':[]});
        colName = ['Date','Open','High','Low','Close','Volume','AdjClose']
        #putting into a loop to download all pages of data
        done = False
        m=0    
        while not done:
            rowTemp=[]
            #print m
            URLPage = self.URL+str(m)        
            #creates soup and dowloads data
            soup = BeautifulSoup(urllib2.urlopen(URLPage).read())
            table = soup.find('table','yfnc_datamodoutline1')
            #breaks loop if it doesnt find a table
            if table==None:
                done = True
                break                
            
            #takes data from soup and processes it into a way that can be used 
            for td in table.tr.findAll("td"):
                #print td
                if td.string != None:                    
                    #Only get stock data
                    if 'Dividend' not in td.string and '/' not in td.string:
                        #tableTemp.append(td.string)
                        rowTemp.append(td.string)
                        # Add entire row to dataFrame
                        if len(rowTemp)%7==0:
                            #print pd.DataFrame([rowTemp], columns=colName)
                            stockDataFrame = stockDataFrame.append(pd.DataFrame([rowTemp], columns=colName), ignore_index=True)
                            #Clear rowTemp
                            rowTemp = []
            
            #increment m
            m+=66
            print m
        
        # Save as csv
        stockDataFrame.to_csv(self.stockName + '_data.csv')
        # Returns panda array of scraped data
        return stockDataFrame

               
    
    # plotStockData(initialDate,finalDate)
    def plotStockData(self, percentage='n',initialDate=None, finalDate=None):
        # calls readDatabase, then uses pylab to plot the stock data from initialDate
        # to finalDate. Defaults are minDate and maxDate.
        #Read in stock data
        stockDataFrame = pd.read_csv(self.stockName + '_data.csv')
        dateData = stockDataFrame["Date"].tolist()
        openData = stockDataFrame["Open"]
                
        #converts data into a type that can be used      
        dateData = convertDate(dateData)
        openData = [float(''.join(re.split('\,',i))) for i in openData]       
        
        #converts it to percentage
        if percentage=='y':
            #firstPrice = float(openData[initN])
            firstPrice = float(openData[len(dateData)-1])
            for n in range(len(openData)): openData[n]*=100/firstPrice        
        
        #plots data
        plt.figure()
        #plt.plot_date(dateData[initN:finN],openData[initN:finN],'-o')
        plt.plot_date(dateData,openData,'-')
        plt.xlabel('Date')
        if percentage=='y':
            plt.ylabel('Percentage')
        else:
            plt.ylabel('Price ($)')
        plt.title(self.stockName)
        plt.show()       

# convertDate(dateString)
def convertDate(dateString):
    #takes a date input as a list of strings in the format 'mmm d, yyyy' and converts it to
    #a date object
    # a dictionary to convert months to a number
    monthDict = {'Jan': '01', 'Feb':'02', 'Mar':'03','Apr':'04','May':'05','Jun':'06',
    'Jul':'07','Aug':'08','Sep':'09','Oct':'10','Nov':'11','Dec':'12'}
    
    for n in range(len(dateString)):
        #splits the string
        splitDate = re.split('\W+',dateString[n])
        #print splitDate
        # cconverts the date into date object
        dateString[n] = datetime.date(int(splitDate[2]),int(monthDict[splitDate[0]]),int(splitDate[1])) #y,m,d
    return dateString   

#todaysDate()
def todaysDate():
    #gets todays date and converts it into a format that the URL for downloading
    # can use. Returns (dd,mm-1,yy)
    todaysDate = datetime.date.today()
    year = str(todaysDate.year)
    if todaysDate.month<11:
        month = '0'+str(todaysDate.month-1)
    else:
        month = str(todaysDate.month-1)
    if todaysDate.day<10:
        day = '0'+str(todaysDate.day)
    else:
        day = str(todaysDate.day)
        
    return day, month, year

# and does the plotting
 
plt.close("all")
    
#USA S&P500 
SP500 = Stock('^GSPC')
SP500.stockScrape()
SP500.plotStockData(percentage='n')
    
#China Shanghai Composite
SSEC = Stock('000001.SS')
SSEC_stockData = SSEC.stockScrape()
SSEC.plotStockData(percentage='n')

#Japan Nikei 225
N225 = Stock('^N225')
N225_stockData = N225.stockScrape()
N225.plotStockData(percentage='n')

#Australia S&P/ASX200
ASX = Stock('^AXJO')
ASX_stockData = ASX.stockScrape()
ASX.plotStockData(percentage='n')

#England FTSE100
FTSE = Stock('^FTSE')
FTSE_stockData = FTSE.stockScrape()
FTSE.plotStockData(percentage='n')


      
           
