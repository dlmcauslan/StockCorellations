####                   Stock_Correlations_v2.py
''' Data science project that downloads stock data from yahoo finance, and 
calculates corellations over time.
Created: 16/04/2016
Modified: 25/04/2016
    Removed Heroku and flask stuff. Tidied up the code a bit.
    Clean the data when it is scraped instead of everytime it is accessed now.
    Data is saved in a single SQL database now with a reference column StockCode
    that describes which stock it is. This is instead of saving as a csv file.
    
    To do:
    Change current function to an initial stockscrape function, then add an update
    stock data function. 
    Figure out sorting by date in SQL, if can change format to make it more
    compatible with datetime in python. 
    Figure out plotting by day, month or year by moddifying SQL calls.
    Plot different plots on single graph - return plot handle in plot function.
    Readd plotting corellations etc
    Get Bokeh plots working, maybe
'''
#Import libraries to use
from bokeh.io import show, output_notebook
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import DatetimeTickFormatter
from bokeh.charts import Bar
from bs4 import BeautifulSoup
import datetime
import matplotlib.pyplot as plt
import numpy as np
import os
import os.path
import pandas as pd
import re
import urllib2
import sqlite3

# Create stock object, with stockName and database (that data is saved to)
class Stock(object):
    def __init__(self, stockName, databasePath):
        self.stockName = stockName
        self.databasePath = databasePath
        day,month,year = todaysDate()
        self.URL = 'http://finance.yahoo.com/q/hp?s='+self.stockName+'&d='+month+'&e='+day+'&f='+year+'&g=d&a=01&b=01&c=2015&z=66&y='        
               
    # initialStockScrape()
    def stockScrape(self):
        # function which does the first time initialization of the stock and 
        #downloads all past stock data, returns array of dates, and array of data
        
        #If the data has already been downloaded don't redownload it
        #if  os.path.isfile(self.stockName + '_data.csv'):
            #return pd.read_csv(self.stockName + '_data.csv')
        
        # Initialize pandas dataframe to hold stock data    
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
        
        # Cleans the numerical data before saving
        dataClean(stockDataFrame)
        
        # Adds a Column of Stock Name to dataframe
        nameCol=[]
        [nameCol.append(self.stockName) for n in xrange(len(stockDataFrame))]
        stockDataFrame["StockCode"] = nameCol

        # Save as csv
        stockDataFrame.to_csv(self.stockName + '_data.csv')
        # Add to SQL database
        self.addToDatabase(stockDataFrame)
        # Returns panda array of scraped data
        return stockDataFrame
        
    # addToDatabase()
    def addToDatabase(self,dataFrame):
        # function which adds scraped data to database
        conn = sqlite3.connect(self.databasePath)     
        dataFrame.to_sql(name = 'stocks', con = conn, flavor ='sqlite', if_exists = 'append')       
        conn.commit()
        conn.close()                    

        
    # readDatabase()
    def readDatabase(self, sqlQuery):
        # reads from database
        conn = sqlite3.connect(self.databasePath)        
        dataFrame = pd.read_sql(sqlQuery, conn)
        conn.close() 
        return dataFrame   

    def plotStockData(self, percentage='n', plottype='m'):
        #Read in stock data
        dateData, openData = self.convertPlotData(percentage='n')
        
        if plottype == 'm':
            self.plotStockDataMatplotlib(dateData, openData, percentage)
        elif plottype == 'b':
            self.plotStockDataBokeh(dateData, openData, percentage)
        else:
            print("Incorrect plot type")

    def plotStockDataMatplotlib(self, dateData, openData, percentage):
        #Plots Stock Data using Matplotlib        
        #Plots data
        plt.figure()
        plt.plot_date(dateData,openData,'-o')
        plt.xlabel('Date')
        if percentage=='y':
            plt.ylabel('Percentage')
        else:
            plt.ylabel('Index Level')
        plt.title(self.stockName)
        plt.show()   
            
    # plotStockDataBokeh(initialDate,finalDate)
    def plotStockDataBokeh(self, dateData, openData, percentage):
        output_notebook()
        #Plots Stock Data using Bokeh (in iPython or Jupyter notebook)        
        #Plots data
        plt = figure(plot_width=500, plot_height=500, title="Stock Indices")
        plt.line(dateData, openData, line_width=2)
        plt.xaxis.axis_label = "Date"
        if percentage=='y':
            plt.yaxis.axis_label('Percentage')
        else:
            plt.yaxis.axis_label('Index Level')
        show(plt) # show the results 
        return plt
        
    # convertPlotData(initialDate,finalDate)
    def convertPlotData(self, percentage='n'):
        # calls readDatabase, then uses pylab to plot the stock data from initialDate
        # to finalDate. Defaults are minDate and maxDate.
        #Read in stock data
        '''stockDataFrame = pd.read_csv(self.stockName + '_data.csv')'''
        format_str = """SELECT StockCode, Date, Open 
                        FROM stocks
                        WHERE StockCode = '{name}'; """
        sqlQuery = format_str.format(name = self.stockName)
        stockDataFrame = self.readDatabase(sqlQuery)
        dateData = stockDataFrame["Date"].tolist()
        openData = stockDataFrame["Open"]
                
        #converts date data into a type that can be used   
        dateData = convertDate(dateData)
       
        #converts it to percentage
        if percentage=='y':
            #firstPrice = float(openData[initN])
            firstPrice = float(openData[len(dateData)-1])
            for n in range(len(openData)): openData[n]*=100/firstPrice        

        return dateData, openData     

# convertData
def convertData(datStr):
    return float("".join(datStr.split(',')))

# cleans dataframe data        
def dataClean(inptFrame):
    for n in ["AdjClose", "Close","High","Low","Open","Volume"]:
        inptFrame[n] = map(convertData,inptFrame[n])   
    return inptFrame

# createDatabase(databaseName)
def createDatabase(databasePath):
    # function which creates database
    # Check if database exists, if it does do nothing
    if os.path.isfile(databasePath) == False:
        conn = sqlite3.connect(databasePath)  
        cursor = conn.cursor()
        
        #Created database
        sql_command = """
        CREATE TABLE stocks (StockCode TEXT, Date TEXT, AdjClose REAL, Close REAL,
        High REAL, Low REAL, Open REAL, Volume REAL) 
        """
    
        cursor.execute(sql_command)
        conn.commit()
        conn.close()
        print "Database created" 

    
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

# Calculate stock correlations
def stockCorrelation(stockA, stockB):
    #Read in data frames for both stocks
    stockDataFrameA = pd.read_csv(stockA.stockName + '_data.csv')
    stockDataFrameB = pd.read_csv(stockB.stockName + '_data.csv')
    dateDataA = convertDate(stockDataFrameA["Date"].tolist())
    dateDataB = convertDate(stockDataFrameB["Date"].tolist())
    yearA = [n.year for n in dateDataA]
    yearB = [n.year for n in dateDataB]
    # Add a column to the data frame for the year
    stockDataFrameA["Year"] = yearA
    stockDataFrameB["Year"] = yearB
    '''# Add a column to the dataframe with clean price information
    #stockDataFrameA["OpenClean"] = [float(''.join(re.split('\,',i))) for i in stockDataFrameA["Open"]]
    #stockDataFrameB["OpenClean"] = [float(''.join(re.split('\,',i))) for i in stockDataFrameB["Open"]]'''
    
    # Find the first year with complete data
    minYear = max(min(yearA), min(yearB))+1
    # Years to iterate over
    years = range(minYear,datetime.date.today().year)
    # Create empty numpy arrays to store data in
    meanA = np.zeros(len(years))
    stdA = np.zeros(len(years))
    meanB = np.zeros(len(years))
    stdB = np.zeros(len(years))
    cover = np.zeros(len(years))
    
    # Iterate over years
    for n in range(len(years)):
        # Calculate some properties of A
        tmpDataA = stockDataFrameA.Open[stockDataFrameA["Year"]==years[n]]
        meanA[n] = tmpDataA.mean()
        stdA[n] = float(tmpDataA.std())
        diffMeanA = tmpDataA - meanA[n]
        # Calculate some properties of B
        tmpDataB = stockDataFrameB.Open[stockDataFrameB["Year"]==years[n]]
        meanB[n] = tmpDataB.mean()
        stdB[n] = float(tmpDataB.std())
        diffMeanB = tmpDataB - meanB[n]
        # Make sure vectors are the same length
        minLength = min(len(tmpDataA),len(tmpDataB))
        #Covariance COVER = { (X1-Mx)(Y1-My) + (X2-Mx)(Y2-My) + ...+ (Xn-Mx)(Yn-My) }/n
        cover[n] = np.dot(diffMeanA[:minLength], diffMeanB[:minLength])/minLength
        
    # correlation Correlation = COVER / ( Sx Sy)
    correlation = cover/(stdA*stdB)    

    return years, correlation

# Calculate the fraction of years that have a negative correlation
def negativeCorrelation(stockA, stockB):
    #Calculate the correlations between Index A and B for each year
    years, correlation = stockCorrelation(stockA, stockB) 
    # Find what years the correlations are negative
    boolVect = np.array(correlation)<0
    # Count the number of negative years
    numNegatives = sum(boolVect)
    # Calculate the fraction of negative years
    fractionNegative = numNegatives/float(len(correlation))
    return fractionNegative
   
### Code for downloading data and plotting it
# Create SQL database
databasePath = "C:/Users/dlmca/OneDrive/Python/Canopy/StockCorellations/Databases/stockDataBase.db"
createDatabase(databasePath)

'''######### Clear db
conn = sqlite3.connect(databasePath)
stockDataFrameClear =  pd.DataFrame({'StockCode':[],'Date':[], 'Open':[], 'High':[], 'Low':[],\
                    'Close':[], 'Volume':[], 'AdjClose':[]});     
stockDataFrameClear.to_sql(name = 'stocks', con = conn, flavor ='sqlite', if_exists = 'replace')       
conn.commit()
conn.close() 
##############'''
        
plt.close("all")      
#USA S&P500 
SP500 = Stock('^GSPC', databasePath)
SP500_stockData = SP500.stockScrape()
sqlQuery = """SELECT StockCode, Date, Open FROM stocks"""
y = SP500.readDatabase(sqlQuery)
SP500.plotStockData(percentage='n', plottype='m')

   
#China Shanghai Composite
SSEC = Stock('000001.SS', databasePath)
SSEC_stockData = SSEC.stockScrape()
SSEC.plotStockData(percentage='n', plottype='m')

'''
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

yearData, correlationSP500SSEC = stockCorrelation(SP500,SSEC)
fracNegB = negativeCorrelation(SP500,SSEC)
'''

