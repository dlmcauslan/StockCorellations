####                   Stock_Correlations.py
''' Data science project that downloads stock data from yahoo finance, and 
calculates corellations over time.
Created: 16/04/2016
'''
#Import libraries to use
from bokeh.io import show #, output_notebook
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import DatetimeTickFormatter
from bokeh.charts import Bar
from bs4 import BeautifulSoup
import datetime
from flask import Flask, render_template
#import matplotlib.pyplot as plt
import numpy as np
import os
import os.path
import pandas as pd
import re
import urllib2

#output_notebook()

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
        
        #If the data has already been downloaded don't redownload it
        if  os.path.isfile(self.stockName + '_data.csv'):
            return pd.read_csv(self.stockName + '_data.csv')
        
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
        
        # Save as csv
        stockDataFrame.to_csv(self.stockName + '_data.csv')
        # Returns panda array of scraped data
        return stockDataFrame
    
    # plotStockData(initialDate,finalDate)
    def plotStockData(self, percentage='n'):
        # calls readDatabase, then uses pylab to plot the stock data from initialDate
        # to finalDate. Defaults are minDate and maxDate.
        #Read in stock data
        
        dateData, openData = self.convertPlotData(percentage='n')
        
        #Plots data using Bokeh
        pTest = figure(plot_width=500, plot_height=500, title="Stock Indices")
        pTest.line(dateData, openData, line_width=2)
        pTest.xaxis.axis_label = "Date"
        pTest.yaxis.axis_label = "Index Level"
        show(pTest) # show the results 
        return pTest
        
    # convertPlotData(initialDate,finalDate)
    def convertPlotData(self, percentage='n'):
        # calls readDatabase, then uses pylab to plot the stock data from initialDate
        # to finalDate. Defaults are minDate and maxDate.
        #Read in stock data
        stockDataFrame = pd.read_csv(self.stockName + '_data.csv')
        dateData = stockDataFrame["Date"].tolist()
        openData = stockDataFrame["Open"]
                
        #converts data into a type that can be used (Cleans numeric data)    
        dateData = convertDate(dateData)
        openData = [float(''.join(re.split('\,',i))) for i in openData]       
        
        #converts it to percentage
        if percentage=='y':
            #firstPrice = float(openData[initN])
            firstPrice = float(openData[len(dateData)-1])
            for n in range(len(openData)): openData[n]*=100/firstPrice        

        return dateData, openData     



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
    # Add a column to the dataframe with clean price information
    stockDataFrameA["OpenClean"] = [float(''.join(re.split('\,',i))) for i in stockDataFrameA["Open"]]
    stockDataFrameB["OpenClean"] = [float(''.join(re.split('\,',i))) for i in stockDataFrameB["Open"]]
    
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
        tmpDataA = stockDataFrameA.OpenClean[stockDataFrameA["Year"]==years[n]]
        meanA[n] = tmpDataA.mean()
        stdA[n] = float(tmpDataA.std())
        diffMeanA = tmpDataA - meanA[n]
        # Calculate some properties of B
        tmpDataB = stockDataFrameB.OpenClean[stockDataFrameB["Year"]==years[n]]
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
   
### Code for downloading data and plotting in a Jupyter notebook    
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

yearData, correlationSP500SSEC = stockCorrelation(SP500,SSEC)
fracNegB = negativeCorrelation(SP500,SSEC)


# Create Flask app
app = Flask(__name__)

# Define our URLs and pages.
@app.route('/stockPlots')
def stockPlots():
    # Load the index data so that it can be plotted
    dateDataSP500, openDataSP500 = SP500.convertPlotData(percentage='y')
    dateDataSSEC, openDataSSEC = SSEC.convertPlotData(percentage='y')
    dateDataN225, openDataN225 = N225.convertPlotData(percentage='y')  
    dateDataASX, openDataASX = ASX.convertPlotData(percentage='y')  
    dateDataFTSE, openDataFTSE = FTSE.convertPlotData(percentage='y')         
    
    #Plots data using Bokeh
    pTest = figure(plot_width=1200, plot_height=700, title="Stock Indices")
    pTest.line(dateDataSP500, openDataSP500, line_width=2, line_color="green", legend = "S&P 500")
    pTest.line(dateDataSSEC, openDataSSEC, line_width=2, line_color="red", legend="SSEC")
    pTest.line(dateDataN225, openDataN225, line_width=2, legend="N225")
    pTest.line(dateDataASX, openDataASX, line_width=2, line_color="orange", legend="ASX")
    pTest.line(dateDataFTSE, openDataFTSE, line_width=2, line_color="purple", legend="FTSE")
    pTest.xaxis.axis_label = "Date"
    pTest.yaxis.axis_label = "Percentage change (%)"
    pTest.legend.location = "top_left"
    pTest.xaxis[0].formatter = DatetimeTickFormatter(formats = dict(hours=["%B %Y"],
                                                                    days=["%B %Y"],
                                                                    months=["%B %Y"],
                                                                    years=["%B %Y"],))        
    script, div = components(pTest)
    return render_template("simpleline.html", script=script, div=div)
    show(pTest)
    
@app.route('/correlations')
def correlationsPlots():
    # Calculate correlations for different indices and the S&P500
    yearDataSP500SSEC, correlationSP500SSEC = stockCorrelation(SP500,SSEC)
    yearDataSP500N225, correlationSP500N225 = stockCorrelation(SP500,N225)
    yearDataSP500ASX, correlationSP500ASX = stockCorrelation(SP500,ASX)
    yearDataSP500FTSE, correlationSP500FTSE = stockCorrelation(SP500,FTSE)     
    
    #Plots data using Bokeh
    pTest = figure(plot_width=1200, plot_height=700, title="Correlations with S&P500")
    pTest.line(yearDataSP500SSEC, correlationSP500SSEC, line_width=2, line_color="red")
    pTest.circle(yearDataSP500SSEC, correlationSP500SSEC, line_width=2, line_color="red", legend = "SSEC", fill_color="white", size=10)
    pTest.line(yearDataSP500N225, correlationSP500N225, line_width=2)
    pTest.circle(yearDataSP500N225, correlationSP500N225, line_width=2, legend = "N225", fill_color="white", size=10)
    pTest.line(yearDataSP500ASX, correlationSP500ASX, line_width=2, line_color="orange")
    pTest.circle(yearDataSP500ASX, correlationSP500ASX, line_width=2, line_color="orange", legend = "ASX", fill_color="white", size=10)
    pTest.line(yearDataSP500FTSE, correlationSP500FTSE, line_width=2, line_color="purple")
    pTest.circle(yearDataSP500FTSE, correlationSP500FTSE, line_width=2, line_color="purple", legend = "FTSE", fill_color="white", size=10)
    
    pTest.xaxis.axis_label = "Year"
    pTest.yaxis.axis_label = "Correlation"
    pTest.legend.location = "bottom_left"
    script, div = components(pTest)
    return render_template("simpleline.html", script=script, div=div)
    show(pTest)
    
@app.route('/correlationsBar')
def correlationsBar():
    # Creates a bar plot showing the fraction of years that correlations have gone
    # below 0.
    # Create a dictionary of the different pairs of stocks for correlations calculations
    combinations = {'SP500-SSEC':[SP500,SSEC],'SP500-N225':[SP500,N225],'SP500-ASX':[SP500,ASX], 
                'SP500-FTSE':[SP500,FTSE],'SSEC-N225':[SSEC,N225],'SSEC-ASX':[SSEC,ASX],
                'SSEC-FTSE':[SSEC,FTSE],'N225-ASX':[N225,ASX],'N225-FTSE':[N225,FTSE],'ASX-FTSE':[ASX,FTSE]}
    
    #Calculate the fraction of years that the correlations were less than 0
    fracNeg =[]
    for x in combinations.keys():
        fracNeg.append(negativeCorrelation(combinations[x][0],combinations[x][1]))
   
    # Add data to dataframe for plotting 
    dictTest = {'values':fracNeg, 'names':combinations.keys()}
    df = pd.DataFrame(dictTest)
    
    #Plots data using Bokeh
    pTest = figure(plot_width=1200, plot_height=700, title="Correlations with S&P500")
    pTest = Bar(df, 'names', values='values', title = "Fraction of years where correlations are below 0",
            xlabel="Indices", ylabel="Fraction of years below 0")
    
    script, div = components(pTest)
    return render_template("simpleline.html", script=script, div=div)
    show(pTest)

if __name__ == '__main__':
    #app.run(debug=True)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
      
           
