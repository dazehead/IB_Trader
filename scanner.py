from ib_insync import *
import pandas as pd
import xml.etree.ElementTree as ET
from finvizfinance.quote import finvizfinance
import requests
import numpy as np
import datetime as dt
from get_data import download_historical
import sqlite3
import time

class Scanner:
    """A class to handle Scanner lookup and paramters"""

    def __init__(self, ib: object, scancode: str, changePercAbove: str, volume_above):
        print("...Initializing Scanner")
        self.ib = ib
        self.float_percentage_limit = None
        self.contracts = []
        self.parameters_df = None
        self.scancode = scancode
        self.tickers_list = []
        self.company_float_threshold = 50000000
        self.big_move = False
        self.prev_day_close = []
        self.percent_change = []
        self.ticker_floats = []
        self.ticker_market_cap = []
        self.ticker_float_percentage = []
        self.archive = False
        self.scanDataList = None
        self.counter = 0
        self.change_perc_above = changePercAbove
        self.volume_above = volume_above
        self.scan_market()
        print("...Scanner Initialized")

    def archive_data_for_download(self):
        """Function to archive or download data depending on time"""
        market_close = "20:00:00"
        date_now = dt.datetime.now().date()
        market_close_time = dt.datetime.combine(date_now, dt.datetime.strptime(market_close, '%H:%M:%S').time())
        file_path = 'to_be_downloaded.csv'
        file = pd.read_csv(file_path)
        file['date'] = pd.to_datetime(file['date'])

        # grabbing data to download and indexes where there at to remove them
        need_to_download = []
        indexes = []
        for i in range(len(file)):
            if file.iloc[i]['date'] < dt.datetime.now():
                need_to_download.append((file.iloc[i]['ticker'], file.iloc[i]['date']))
                indexes.append(i)

        # dropping all that have been downloading
        file.drop(indexes, inplace=True)
        file.reset_index(inplace=True, drop=True)

        float_perc_df = pd.DataFrame(self.ticker_float_percentage, columns=['ticker', 'float_perc'])
        market_cap_df = pd.DataFrame(self.ticker_market_cap, columns=['ticker', 'market_cap'])
        floats_df = pd.DataFrame(self.ticker_floats, columns=['ticker', 'float'])

        # new_data that will be downloaded
        if self.contracts:
            for contract in self.contracts:
                symbol = contract.symbol
                float_perc = list(float_perc_df['float_perc'][float_perc_df['ticker'] == symbol])[0]
                market_cap = list(market_cap_df['market_cap'][float_perc_df['ticker'] == symbol])[0]
                float = list(floats_df['float'][floats_df['ticker']==symbol])[0]
                for i in range(len(file)):
                    if file.iloc[i]['ticker'] == symbol and file.iloc[i]['date'] == market_close_time:
                        break
                file.loc[len(file.index)] = [
                    symbol,
                    market_close_time,
                    float_perc,
                    market_cap,
                    float
                    ]         
            #conn = sqlite3.connect('logbooks/tickers.db')
            #file.to_sql('statistics', conn, if_exists='append', index=False)
            file.drop_duplicates(subset=['ticker', 'date'],inplace=True)
            file.reset_index(inplace=True, drop=True)
            self.update_statistics_db(file)
            file.to_csv(file_path, index=False)

            #print('...downloading historical')
            download_historical(need_to_download, to_csv=True, ib=self.ib)
            #print('...finished downloading historical')
        else:
            pass

    def update_statistics_db(self, file_to_check):
            conn = sqlite3.connect('logbooks/tickers.db')
            stats_db = pd.read_sql('SELECT * FROM statistics;', conn)
            stats_db['date'] = pd.to_datetime(stats_db['date'])
            combined = pd.concat([stats_db, file_to_check])
            combined.drop_duplicates(subset=["ticker", "date"], inplace=True)
            combined.reset_index(inplace=True, drop=True)
            combined['date'] = pd.to_datetime(combined['date'])
            combined['float_perc'] = round(combined['float_perc'], 2)
            combined = combined.sort_values(by='date')
            combined.to_sql('statistics', conn, if_exists='replace', index=False)

    def monitor_percent_change(self, perc_threshold, time_interval):
        """
        Monitors the percent change of all tickers return by scanner
        if percentage change exceeds threshold after a time_interval
        returns that contract 
        """
        counter = 0
        while not self.big_move:
            if self.contracts:
                for i, contract in enumerate(self.contracts):
                    market_data = self.ib.reqMktData(contract, '', False, False)
                    market_price = market_data.marketPrice()
                    self.percent_change[i].append(((market_price - self.prev_day_close[i]) / self.prev_day_close[i]) * 100)
                    if (self.percent_change[i][-1] - self.percent_change[i][-2] > perc_threshold) and (self.percent_change[i][-1] > 0):
                        print(f"{self.tickers_list[i]} has broken the {perc_threshold} from {self.percent_change[i][-2]} to {self.percent_change[i][-1]}")
                        return contract
                    else:
                        print("...Monitoring Percent Change")
                        if counter ==2:
                            print("\n\t----------Update----------")
                            for i in range(len(self.tickers_list)):
                                print(f'\n\t-------------{i+1}------------')
                                print(f'\tTicker: {self.tickers_list[i]}')  
                                #print(f'\tFloat Percentage: {round(self.ticker_float_percentage[i][1], 2)}')
                                #print(f'\tFloat: {self.ticker_floats[i][1]}')
                        counter += 1
                        if counter > 3:
                            counter = 0
                        self.ib.cancelMktData(contract)
                        self.ib.sleep(time_interval)
            else:
                print("\n\n... Scanning Market for Tickers with Specified Parameters")
                self.scan_market()
                print(f"Tickers: {self.tickers_list}")
                if counter == 2:
                    print("\t----------Update----------")
                    for i in range(len(self.tickers_list)):
                        print(f'\n\t-------------{i+1}------------')
                        print(f'\tTicker: {self.tickers_list[i]}')  
                        print(f'\tFloat Percentage: {round(self.ticker_float_percentage[i][1], 2)}')
                        print(f'\tFloat: {self.ticker_floats[i][1]}')
                self.filter_floats(self.float_percentage_limit, archive=self.archive)
                print(f'Filtered Tickers: {self.tickers_list}')
                self.calculate_percent_change()
                self.ticker_floats = []
                counter += 1
                if counter > 3:
                    counter = 0
                self.ib.sleep(time_interval)
                


    def calculate_percent_change(self):
        """function creates a list of the percentage change"""
        for i, contract in enumerate(self.contracts):
            market_data = self.ib.reqMktData(contract, '', False, False)
            market_price = market_data.marketPrice()
            self.percent_change.append([((market_price - self.prev_day_close[i]) / self.prev_day_close[i]) * 100])
        #print(self.percent_change)

        

    def get_prev_day_close(self):
        """Function gets the previous days close so that we can calculate percentage change"""
        for contract in self.contracts:
            bars = self.ib.reqHistoricalData(
                contract=contract,
                endDateTime= '',
                durationStr='2 D',
                barSizeSetting='1 min',
                whatToShow='TRADES',
                useRTH=False,
                keepUpToDate=True)
            df = util.df(bars)
            df['date'] = df['date'].apply(lambda x: str(x).split()[0])
            prev_df = df[df['date'] == df['date'].unique()[0]]
            self.prev_day_close.append(prev_df.iloc[-1]['close'])


    def scan_market(self, callback=False):
        """Function to retrieve Tickers from Scanner"""
        #if callback:
        #    self.ib.cancelScannerSubscription(self.scanDataList)
        #    self.ib.sleep(1)
        gainSub = ScannerSubscription(
            instrument="STK",
            locationCode="STK.US.MAJOR",
            scanCode=self.scancode,
            stockTypeFilter="CORP")

        # full list of filters
        """https://nbviewer.org/github/erdewit/ib_insync/blob/master/notebooks/scanners.ipynb"""
        tagValues = [TagValue("priceAbove", '1'),
                     TagValue("priceBelow", '30'),
                     TagValue("volumeAbove", self.volume_above),
                     #TagValue("openGapPercAbove", '25'),
                     TagValue("changePercAbove", self.change_perc_above)]

        self.scanDataList = self.ib.reqScannerSubscription(gainSub, [], tagValues)
        #print(self.scanDataList.reqId)
        if not callback:
            self.ib.sleep(1)
                
        for data in self.scanDataList:
            # retrieves all the tickers-converts to Stock object and appends them to a list
            stock = Stock(data.contractDetails.contract.symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(stock)
            self.contracts.append(stock)
        print(f'\n{len(self.scanDataList)} Tickers found.')
        #self.ib.cancelScannerSubscription(self.scanDataList)

        self.get_prev_day_close()
        self.get_ticker_list()
        self.get_finviz_stats()



    def retreive_scanner_params(self):
        """Function to retreive all parameters available to use in a scanner"""
        params = self.ib.reqScannerParameters()

        # Pars the XML string
        root = ET.fromstring(params)
        # Create a list of dictionaries to store data
        data = []

        """NOTE: .//Instrument this will search for scanner paramters"""
        for instrument in root.findall('.//Instrument'):
            instrument_data = {}
            for child in instrument:
                instrument_data[child.tag] = child.text
            data.append(instrument_data)

        # Create Pandas DataFrame
        self.parameters_df = pd.DataFrame(data)

    def retreive_filter_params(self):
        """Retrives all filter parameters that can be used on a scanner"""
        xml = self.ib.reqScannerParameters()
        # parse XML deocument
        tree = ET.fromstring(xml)
        # find all tags that are available for filtering
        tags = [elem.text for elem in tree.findall('.//AbstractField/code')]
        print(len(tags), 'tags:')
        for tag in tags:
            print(tag)

    def search_param(self, param):
        """Function to search a particualar parameter----NOT DONE ONLY RETURNS INDICES"""
        indices_with_param = self.parameters_df[self.parameters_df['filters'].str.contains(param, case=False, na=False)].index
        print(f"Indices where {param} is present: ", indices_with_param)

    def get_ticker_list(self):
        """retreived a list of all the tickers found on scanner"""
        if self.tickers_list:
            self.tickers_list = []
        for contract in self.contracts:
            self.tickers_list.append(contract.symbol)

    def filter_floats(self, float_percentage_limit=None, archive = True):
        """filters contracts by which ones are less than pre-determined float"""
        self.archive = archive
        self.float_percentage_limit = float_percentage_limit
        for i,data in enumerate(self.ticker_floats):
            #print(i, data)
            ticker = data[0]
            company_float = data[1]
            if np.isnan(company_float):
                pass
            else:
                #print(self.ticker_float_percentage[i], i)
                float_percentage = self.ticker_float_percentage[i][1]
                #print(float_percentage)
                if self.float_percentage_limit is not None:
                    if company_float > self.company_float_threshold or float_percentage > self.float_percentage_limit:
                        self.contracts = [contract for contract in self.contracts if contract.symbol != ticker]
                        #print(f'\n{ticker} removed due to high float or precentage too high')
                        #print(f'Float: {company_float}, Percentage: {float_percentage}')
                else:
                    if company_float > self.company_float_threshold:
                        self.contracts = [contract for contract in self.contracts if contract.symbol != ticker]

        self.get_ticker_list()
        if self.archive:
            #print('...archiving data')
            self.archive_data_for_download()

    def get_finviz_stats(self):
        new_contracts = []
        
        for contract in self.contracts:
            ticker = contract.symbol
            try:
                fin = finvizfinance(ticker).ticker_fundament()
                try:
                    new_contracts.append(contract)
                    numeric_float = float(fin['Shs Float'][:-1])
                    numeric_market = float(fin['Market Cap'][:-1])
                    float_mb = fin['Shs Float'][-1]
                    market_mb = fin['Market Cap'][-1]
                    if float_mb == 'M':
                        final_float = int(numeric_float * 1_000_000)
                    elif float_mb == 'B':
                        final_float = int(numeric_float * 1_000_000_000)

                    if market_mb == 'M':
                        final_market = int(numeric_market * 1_000_000)
                    elif market_mb == 'B':
                        final_market = int(numeric_market * 1_000_000_000)

                    self.ticker_floats.append((ticker, final_float))
                    self.ticker_market_cap.append((ticker, final_market))
                    #print(f"\ncontaract: {contract.symbol}")
                    #print(f"Float: {final_float}, Market: {final_market}")
                    #print(f"Percentage: {(final_float/final_market)*100}")

                    self.ticker_float_percentage.append((ticker, (final_float/final_market) * 100))

                except ValueError:
                    #print(f"{ticker} has no float: {fin['Shs Float']}")
                    new_contracts.pop(-1)
            except requests.HTTPError as err:
                if err.response.status_code == 404:
                    pass
                    print(f"\nError 404: Ticker {ticker} not found on Finviz")
                else:
                    pass
                    print(f"\nHTTPError: {err}")
            except Exception as e:
                pass
                print(f"\nAn unexpected error occurred: {e}")
        self.contracts = new_contracts
        self.get_ticker_list()

    def filter_by_news(self):
        """gets news items for ticker; however, only 3 are available"""
        filtered_contracts = []
        news_providers = self.ib.reqNewsProviders()
        print(news_providers)
        codes = '+'.join(np.code for np in news_providers)

        for contract in self.contracts:
            self.ib.qualifyContracts(contract)
            headlines = self.ib.reqHistoricalNews(
                conId=contract.conId,
                providerCodes=codes,
                startDateTime='',
                endDateTime='',
                totalResults=10
                )
            try:
                for news_event in headlines:
                    print(news_event)
                    print('\n')
                latest = headlines[0]
                article = self.ib.reqNewsArticle(
                    providerCode=latest.providerCode,
                    articleId=latest.articleId
                    )
                filtered_contracts.append(contract)
            except IndexError:
                print(f'No News for {contract.symbol}')
        #self.contracts = filtered_contracts
        #self.get_ticker_list()
