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

# Create stock object, with stockName and database (that data is saved to)
class Stock(object):
    def __init__(self, stockName):
        self.stockName = stockName
        day,month,year = todaysDate()
        #self.URL = 'https://nz.finance.yahoo.com/q/hp?s='+self.stockName+'&a=09&b=10&c=1800&d='+month+'&e='+day+'&f='+year+'&g=d&z=66&y='
        self.URL = 'http://finance.yahoo.com/q/hp?s='+self.stockName+'&d='+month+'&e='+day+'&f='+year+'&g=d&a=09&b=10&c=1800&z=66&y='        
               
    # initialStockScrape()
    def initialStockScrape(self):
        # function which does the first time initialization of the stock and 
        #downloads all past stock data, returns array of dates, and array of data
        #initializes arrays
        dateTable=[]
        openTable=[]
        #putting into a loop to download all pages of data
        done = False
        m=0    
        while not done:
            tableTemp=[]
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
                if td.string != None:                    
                    #Only get stock data
                    if 'Dividend' not in td.string and '/' not in td.string:
                        tableTemp.append(td.string)           
            #only intersted in data for date and opening price
            for n in range(len(tableTemp)/7):
                #Check if we are scraping a page which has data on it which has already
                # been downloaded. If so break out of loop
                if tableTemp[7*n] in dateTable:
                    done = True
                    break
                #append data to tables
                dateTable.append(tableTemp[7*n])
                openTable.append(float(tableTemp[7*n+1]))
            #increment m
            m+=66
        
        #Returns panda array of scraped data
        return dateTable, openTable
               
    
    # plotStockData(initialDate,finalDate)
    def plotStockData(self, percentage='n',initialDate=None, finalDate=None):
        # calls readDatabase, then uses pylab to plot the stock data from initialDate
        # to finalDate. Defaults are minDate and maxDate.
        
        # Reads data to be plotted from database
        dateTable,openTable,nameTable = self.readDatabase()
        
        #converts date data into a type that can be used  
        dateTable = convertDate(dateTable) 
               
        #Sets initialDate and finalDate
        if initialDate==None:
            initN=0
        else:
            minDelta=abs(dateTable[0]-convertDate(initialDate))
            for nInit in range(len(dateTable)):
                tDelta = abs(dateTable[nInit]-convertDate(initialDate))
                if tDelta<=minDelta:
                    minDelta = tDelta
                    initN = nInit
            
        if finalDate==None:
            finN=None
        else:
            minDelta=abs(dateTable[-1]-convertDate(finalDate))
            for nFin in range(len(dateTable)):
                tDelta = abs(dateTable[nFin]-convertDate(finalDate))
                if tDelta<=minDelta:
                    minDelta = tDelta
                    finN=nFin+1
        
        #converts it to percentage
        if percentage=='y':
            firstPrice = float(openTable[initN])
            for n in range(len(openTable)): openTable[n]*=100/firstPrice        
        
        #plots data
        plt.figure()
        plt.plot_date(dateTable[initN:finN],openTable[initN:finN],'-o')
        plt.xlabel('Date')
        if percentage=='y':
            plt.ylabel('Percentage')
        else:
            plt.ylabel('Price ($)')
        plt.title(self.stockName)
        plt.show()       

# convertDate(dateString)
def convertDate(dateStringArray):
    #takes a date input as an array of strings in the format 'yyyy-mm-dd' and converts it to
    #a date object
    if type(dateStringArray)==list:
        #loop over the array
        for n in range(len(dateStringArray)):
            #Sometimes need to force it to be a string
            dateStringArray[n] = str(dateStringArray[n])
            #splits the string
            splitDate = str.split(dateStringArray[n],'-')
            # cconverts the date into date object
            dateStringArray[n] = datetime.date(int(splitDate[0]),int(splitDate[1]),int(splitDate[2]))
    #Or if its just a string
    else:
        #Sometimes need to force it to be a string
        dateStringArray = str(dateStringArray)
        #splits the string
        splitDate = str.split(dateStringArray,'-')
        # cconverts the date into date object
        dateStringArray = datetime.date(int(splitDate[0]),int(splitDate[1]),int(splitDate[2]))  
    return dateStringArray

        
# convertDateSQL
def convertDateSQL(dateString):
    #takes a date input in the format 'd mmm yyyy' and converts it to a format that
    #can be sorted in SQL 'yyyy-mm-dd'
    # a dictionary to convert months to a number
    monthDict = {'Jan': '01', 'Feb':'02', 'Mar':'03','Apr':'04','May':'05','Jun':'06',
    'Jul':'07','Aug':'08','Sep':'09','Oct':'10','Nov':'11','Dec':'12'}
    #Sometimes need to force it to be a string
    dateString = str(dateString)
    #splits the string
    splitDate = str.split(dateString)
    # converts the date into new format yyyy-mm-dd
    if int(splitDate[0])<10:
        newDateString = splitDate[2]+'-'+monthDict[splitDate[1]]+'-0'+splitDate[0]
    else:
        newDateString = splitDate[2]+'-'+monthDict[splitDate[1]]+'-'+splitDate[0]
    return newDateString
    

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



def main():          
    # main file, which adds stocks to be checked, initializes each, updates each
    # and does the plotting
 
    plt.close("all")
    
    #S&P500 
    SP500 = Stock('^GSPC')
    SP500.updateStockData()
    SP500.plotStockData('n','2015-01-01','2017-01-01')
      
           
main()