####                   Stock_Correlations_v2.py
''' Data science project that downloads stock data from yahoo finance, and 
calculates corellations over time.
Created: 16/04/2016
Modified: 25/04/2016
    Removed Heroku and flask stuff. Tidied up the code a bit.
    Clean the data when it is scraped instead of everytime it is accessed now.
    Data is saved in a single SQL database now with a reference column StockCode
    that describes which stock it is. This is instead of saving as a csv file.
Modified: 27/04/2016
    Calculates correlations between pairs of stocks over the past 30 or so years
    and plots these.
    Calculates and plots the fraction of years that stock correlations are negative.
    Added the option to plot using Matplotlib or Bokeh
'''

#Import libraries to use
from bokeh.io import show, output_notebook
from bokeh.plotting import figure
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
        self.day,self.month,self.year = todaysDate()
        self.URL = 'http://finance.yahoo.com/q/hp?s='+self.stockName+'&d='+self.month+'&e='+self.day+'&f='+self.year+'&g=d&a=00&b=01&c=1970&z=66&y='   #Note if changing minimum date here, also need to change the default minDate in stockScrape()    
    
    # updateStockData()
    def updateStockData(self):
        # Checks whether stock is in database, if not it stockScrape to get all the data.
        #If it is in data base it checks whether the stock information is up to date and only fetches new data
        # Reads database
        format_str = """SELECT StockCode FROM stocks WHERE StockCode = '{name}'; """
        sqlQuery = format_str.format(name = self.stockName)
        print sqlQuery
        stockData = self.readDatabase(sqlQuery)
               
        # Checks whether any previous data has been added for the particular stock code
        # if not then run initialStockScrape to get all past data
        if stockData.empty:
            print 'Running stockScrape() on '+self.stockName+'. --First run.'
            #self.URL = 'http://finance.yahoo.com/q/hp?s='+self.stockName+'&d=02&e=25&f=2016&g=d&a=00&b=01&c=2015&z=66&y=' #Test URL
            self.stockScrape()
        else:
            #access database to get latestDate
            print 'Running stockScrape() on '+self.stockName+'. --Updating data.'
            # Performs SQL query to get the latest stock data date in database
            format_str = """SELECT StockCode, max(Date) AS Date FROM stocks WHERE StockCode = '{name}' GROUP BY StockCode"""
            sqlQuery = format_str.format(name = self.stockName)
            y = self.readDatabase(sqlQuery)            
            minDate = y.Date[0]    # minDate is the earliest data of data that the program needs to download
            # Updates stock data
            self.stockScrape(minDate)                     
    
    
    # stockScrape()
    def stockScrape(self, minDate = '1971-01-01'):
        # function which does the first time initialization of the stock and 
        #downloads all past stock data, returns array of dates, and array of data
        
        # Initialize pandas dataframe to hold stock data    
        stockDataFrame =  pd.DataFrame({'Date':[], 'Open':[], 'High':[], 'Low':[],\
                    'Close':[], 'Volume':[], 'AdjClose':[]});
        colName = ['Date','Open','High','Low','Close','Volume','AdjClose']
        
        #putting into a loop to download all pages of data
        done = False
        m=0
           
        while not done:
            rowTemp=[]
            print m,
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
                        rowTemp.append(td.string)
                        # Add entire row to dataFrame
                        if len(rowTemp)%7==0:
                            # If date is less than the minimum date then stop getting data
                            if convertDate([rowTemp[0]])[0] <= minDate:
                                done = True
                                break                                
                            stockDataFrame = stockDataFrame.append(pd.DataFrame([rowTemp], columns=colName), ignore_index=True)
                            #Clear rowTemp
                            rowTemp = []
            
            #increment m
            m+=66
                    
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
        
   # Calculate stock correlations
    def stockCorrelation(self, stockB):
        #Read in data frames for both stocks   
        format_str = """SELECT StockCode, Date, Open, CAST(strftime('%Y', Date) AS INT) AS Year 
                            FROM stocks
                            WHERE StockCode = '{name}'
                            ORDER BY Date DESC """
        sqlQuery = format_str.format(name = self.stockName)
        stockDataFrameA = self.readDatabase(sqlQuery)
        sqlQuery = format_str.format(name = stockB.stockName)
        stockDataFrameB = stockB.readDatabase(sqlQuery)
    
        # Find the first year with complete data
        minYear = max(min(stockDataFrameA["Year"]), min(stockDataFrameB["Year"]))+1
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

    def plotStockData(self, percentage='n', plottype='m', startDate='1800-01-01', endDate='2200-01-01', dayMonthYear = 'd'):
        # Percentage 'y' or 'n' whether you want the y axis as a percentage or not.
        # Plot type 'm' for matplotlib or 'b' for Bokeh (if using ipython/jupyter)
        # startDate and endDate are the plotting range, input as 'yyyy-mm-dd'
        # dayMonthYear - whether you want the data plotted daily 'd', monthly 'm', quarterly 'q', or yearly 'y'.
        #Read in stock data
        dateData, openData = self.convertPlotData(startDate, endDate, percentage, dayMonthYear)
        
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
        #Plots Stock Data using Bokeh (in iPython or Jupyter notebook)        
        #Plots data
        p = figure(plot_width=800, plot_height=350, title=self.stockName)
        p.line(dateData, openData, line_width=2)
        p.xaxis.axis_label = "Date"      
        if percentage=='y':
            p.yaxis.axis_label = 'Percentage'
        else:
            p.yaxis.axis_label = 'Index Level'
        p.xaxis[0].formatter = DatetimeTickFormatter(formats = dict(hours=["%B %Y"], days=["%B %Y"], months=["%B %Y"], years=["%B %Y"],)) 
        show(p) # show the results 
        
    # convertPlotData(initialDate,finalDate)
    def convertPlotData(self, startDate, endDate, percentage, dayMonthYear):
        # calls readDatabase, then converts database data to a format that can be plotted easily
        #Read in stock data
        if dayMonthYear == 'd':
            format_str = """SELECT StockCode, Date, Open 
                            FROM stocks
                            WHERE StockCode = '{name}' AND Date BETWEEN '{sDate}' AND '{eDate}'
                            ORDER BY Date DESC """
        elif dayMonthYear == 'm':
            format_str = """SELECT StockCode, min(Date) AS Date, strftime('%m', Date) AS Month, strftime('%Y', Date) AS Year, Open 
                        FROM stocks 
                        WHERE StockCode = '{name}' AND Date BETWEEN '{sDate}' AND '{eDate}'
                        GROUP BY Year, Month 
                        ORDER BY Date DESC"""
        elif dayMonthYear == 'q':
            format_str = """SELECT StockCode, min(Date) AS Date, strftime('%m', Date) AS Month, strftime('%Y', Date) AS Year, Open 
                        FROM stocks 
                        WHERE StockCode = '{name}' AND Date BETWEEN '{sDate}' AND '{eDate}'
                        GROUP BY Year, Month
                        HAVING Month IN ('01', '04', '07', '10') 
                        ORDER BY Date DESC"""
        elif dayMonthYear == 'y':
            format_str = """SELECT StockCode, min(Date) AS Date, strftime('%Y', Date) AS Year, Open 
                        FROM stocks 
                        WHERE StockCode = '{name}' AND Date BETWEEN '{sDate}' AND '{eDate}'
                        GROUP BY Year 
                        ORDER BY Date DESC"""
        else:
            print "Invalid plot frequency."
        sqlQuery = format_str.format(name = self.stockName, sDate = startDate, eDate = endDate)
        stockDataFrame = self.readDatabase(sqlQuery)
        dateData = stockDataFrame["Date"].tolist()
        openData = stockDataFrame["Open"]
                
        #converts date data into a type that can be used   
        dateData = convertDateSQL(dateData)
       
        #converts it to percentage
        if percentage=='y':
            firstPrice = float(openData[len(dateData)-1])
            openData = [n*100/firstPrice for n in openData]    

        return dateData, openData     

# convertData
def convertData(datStr):
    return float("".join(datStr.split(',')))

# cleans dataframe data        
def dataClean(inptFrame):
    for n in ["AdjClose", "Close","High","Low","Open","Volume"]:
        inptFrame[n] = map(convertData,inptFrame[n])
    inptFrame["Date"] = convertDate(inptFrame["Date"].tolist())   
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
    #yyyy-mm-dd
    # a dictionary to convert months to a number
    monthDict = {'Jan': '01', 'Feb':'02', 'Mar':'03','Apr':'04','May':'05','Jun':'06',
    'Jul':'07','Aug':'08','Sep':'09','Oct':'10','Nov':'11','Dec':'12'}
    
    for n in range(len(dateString)):
        #splits the string
        splitDate = re.split('\W+',dateString[n])
        # cconverts the date into date object
        dateString[n] = datetime.date(int(splitDate[2]),int(monthDict[splitDate[0]]),int(splitDate[1])).isoformat() #y,m,d
    return dateString

# convertDateSQL    
def convertDateSQL(dateString):
    #takes a date from SQL database as 'yyyy-mm-dd' and converts to datetimeobject   
    for n in range(len(dateString)):
        #splits the string
        splitDate = map(int, dateString[n].split('-'))
        # cconverts the date into date object
        dateString[n] = datetime.date(splitDate[0],splitDate[1],splitDate[2]) #y,m,d
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

#plotCorrelations    
def plotCorrelations(primaryStock, secondaryStocks, plotType='m'):
    #primaryStock is the name of the primary Stock, secondaryStock is a list
    #containing the names of thes secondary stocks, plotType = 'm' (matplotlib) or 'b'(Bokeh)   
    if plotType=='m':            
        plt.figure()
    elif plotType=='b':
        colors = ['green','red','mediumblue','orange','purple','teal','gold']
        i=0
        p = figure(plot_width=800, plot_height=350, title="Correlations with " + primaryStock.stockName)
        
    for stock in secondaryStocks:
        yearData, corrAB = primaryStock.stockCorrelation(stock)        
        if plotType=='m':            
            plt.plot(yearData,corrAB,'-o')
        elif plotType=='b':
            p.line(yearData, corrAB, line_width=2, line_color=colors[i])
            p.circle(yearData, corrAB, line_width=2, line_color=colors[i], legend = stock.stockName, fill_color="white", size=10)
            i+=1
    
    if plotType=='m':            
        plt.xlabel('Year')
        plt.ylabel('Correlation coefficient')
        plt.title("Correlations with " + primaryStock.stockName)
        plt.legend([n.stockName for n in secondaryStocks], loc=3)
        plt.show()
    elif plotType=='b':
        p.xaxis.axis_label = "Year"      
        p.yaxis.axis_label = 'Correlation coefficient'
        p.legend.location = "bottom_left"
        show(p)


# Calculate the fraction of years that have a negative correlation
def negativeCorrelation(stockA, stockB):
    #Calculate the correlations between Index A and B for each year
    years, correlation = stockA.stockCorrelation(stockB) 
    # Find what years the correlations are negative
    boolVect = np.array(correlation)<0
    # Count the number of negative years
    numNegatives = sum(boolVect)
    # Calculate the fraction of negative years
    fractionNegative = numNegatives/float(len(correlation))
    return fractionNegative


#plotCorrelations    
def plotNegativeCorrelations(stockList, plotType='m'):
    #stockList is a list of the stocks to have their correlations compared
    #containing the names of thes secondary stocks, plotType = 'm' (matplotlib) or 'b'(Bokeh)
    fracNeg=[]
    names =[]
    #Calculate the fraction of years that have a negative correlation for all pairs
    # of stocks in stockList
    for i in xrange(len(stockList)-1):
        stockA = stockList[i]
        for stockB in stockList[i+1:]:
            #Calculates negative correlation fraction
            fracNeg.append(negativeCorrelation(stockA,stockB))
            #Gives names of stock pairs. For x tick labels
            names.append(stockA.stockName + '--' + stockB.stockName)
    
    #Plot as matplotlib
    if plotType=='m':
        plt.figure()            
        plt.bar(range(len(fracNeg)), fracNeg, width=0.9)   
        plt.ylabel('Proportion of years')
        plt.xlabel('Stock pairing')
        plt.title("Proportion of Years the Stock Correlation Coefficient is Less than 0.")
        plt.xticks(np.arange(len(fracNeg))+.45, names, rotation='horizontal')
        plt.show()
    #Plots data using Bokeh
    elif plotType=='b':
        df = pd.DataFrame({'values':fracNeg, 'names':names})    
        p = figure(plot_width=800, plot_height=350, title="Correlations with S&P500")
        p = Bar(df, 'names', values='values', title = "Proportion of Years the Stock Correlation Coefficient is Less than 0.",
            xlabel="Stock pairing", ylabel="Proportion of years")
        show(p)            
        
### Code for downloading data and plotting it
# Create SQL database
databasePath = "C:/Users/dlmca/OneDrive/Python/Canopy/StockCorellations/Databases/stockDataBase.db"
createDatabase(databasePath)

######## Clear db (set to True if you need to clear the data)
if False:
    conn = sqlite3.connect(databasePath)
    stockDataFrameClear =  pd.DataFrame({'StockCode':[],'Date':[], 'Open':[], 'High':[], 'Low':[],\
                    'Close':[], 'Volume':[], 'AdjClose':[]});     
    stockDataFrameClear.to_sql(name = 'stocks', con = conn, flavor ='sqlite', if_exists = 'replace')       
    conn.commit()
    conn.close()
#############
#Plot using matplotlib ('m') or bokeh ('b')
plotType = 'm'
if plotType == 'b':
    output_notebook()
            
plt.close("all")      
#USA S&P500 
SP500 = Stock('^GSPC', databasePath)
SP500_stockData = SP500.updateStockData()
SP500.plotStockData(percentage='y', plottype=plotType, startDate = '1990-01-15', endDate = '2016-04-26', dayMonthYear = 'd')

#### TEST SQL QUERIES
'''sqlQuery = """SELECT DISTINCT StockCode, Date, Open FROM stocks ORDER BY StockCode, Date DESC"""
#sqlQuery = """SELECT StockCode, Date, Open FROM stocks WHERE Date BETWEEN '2016-03-23' AND '2016-06-25' AND StockCode = '^GSPC' ORDER BY Date DESC """
#sqlQuery = """SELECT StockCode, CAST(Date AS VARCHAR) AS Date, Open FROM stocks WHERE StockCode = '^GSPC' ORDER BY StockCode, Date DESC """
#sqlQuery = """SELECT StockCode, min(Date) AS Date, strftime('%m', Date) AS Month, strftime('%Y', Date) AS Year, Open FROM stocks WHERE Date BETWEEN '2000-02-23' AND '2016-06-25' AND StockCode = '^GSPC' GROUP BY Year, Month HAVING Month IN ('01', '04', '07', '10') ORDER BY Date DESC"""
sqlQuery = """SELECT StockCode, Date, Open, CAST(strftime('%Y', Date) AS INT) AS Year FROM stocks WHERE StockCode = '^GSPC' ORDER BY Date DESC """
y = SP500.readDatabase(sqlQuery)
y'''
##########
    
#China Shanghai Composite
SSEC = Stock('000001.SS', databasePath)
SSEC_stockData = SSEC.updateStockData()
SSEC.plotStockData(percentage='n', plottype=plotType)


#Japan Nikei 225
N225 = Stock('^N225', databasePath)
N225_stockData = N225.updateStockData()
N225.plotStockData(percentage='n', plottype=plotType)


#Australia S&P/ASX200
ASX = Stock('^AXJO', databasePath)
ASX_stockData = ASX.updateStockData()
ASX.plotStockData(percentage='n', plottype=plotType, dayMonthYear = 'm')

#England FTSE100
FTSE = Stock('^FTSE', databasePath)
FTSE_stockData = FTSE.updateStockData()
FTSE.plotStockData(percentage='n', plottype=plotType, dayMonthYear = 'm')

#### Correlations
plotCorrelations(SP500, [SSEC, N225, ASX, FTSE], plotType=plotType)
plotNegativeCorrelations([SP500, SSEC, N225, ASX, FTSE], plotType=plotType)

