from ib_insync import *
import pandas as pd
import xml.etree.ElementTree as ET

class Scanner:
    """A class to handle Scanner lookup and paramters"""
    def __init__(self, ib, scancode):
        print("...Initializing Scanner")
        self.ib = ib
        self.contracts = []
        self.parameters_df = None
        self.scancode = scancode
        self.tickers_list = []
        self.company_float_threshold = 70000000
        self.big_move = False
        self.prev_day_close = []
        self.percent_change = []
        self.scan_market()
        print("...Scanner Initialized")

    def monitor_percent_change(self, perc_threshold, time_interval):

        while not self.big_move:
            for i, contract in enumerate(self.contracts):
                market_data = self.ib.reqMktData(contract, '', False, False)
                market_price = market_data.marketPrice()
                self.percent_change[i].append(((market_price - self.prev_day_close[i]) / self.prev_day_close[i]) * 100)
                if self.percent_change[i][-1] - self.percent_change[i][-2] > perc_threshold:
                    return contract
                else:
                    self.ib.sleep(time_interval)
            print(self.percent_change)


    def calculate_percent_change(self):
        """function creates a list of the percentage change"""
        for i, contract in enumerate(self.contracts):
            market_data = self.ib.reqMktData(contract, '', False, False)
            market_price = market_data.marketPrice()
            self.percent_change.append([((market_price - self.prev_day_close[i]) / self.prev_day_close[i]) * 100])
        print(self.percent_change)

        

    def get_prev_day_close(self):
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


    def scan_market(self):
        """Function to retrieve Tickers from Scanner"""
        gainSub = ScannerSubscription(
            instrument="STK",
            locationCode="STK.US.MAJOR",
            scanCode=self.scancode,
            stockTypeFilter="CORP")
        
        # full list of filters
        """https://nbviewer.org/github/erdewit/ib_insync/blob/master/notebooks/scanners.ipynb"""
        tagValues = [TagValue("priceAbove", '1'),
                     TagValue("priceBelow", '20'),
                     TagValue("volumeAbove", '999999'),
                     #TagValue("openGapPercAbove", '25'),
                     TagValue("changePercAbove", "20")]

        scanDataList = self.ib.reqScannerSubscription(gainSub, [], tagValues)
        self.ib.sleep(1.5)
        for data in scanDataList:
            # retrieves all the tickers-converts to Stock object and appends them to a list
            stock = Stock(data.contractDetails.contract.symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(stock)
            self.contracts.append(stock)
        print(f'{len(scanDataList)} Tickers found.')
        self.get_prev_day_close()
        self.get_ticker_list()

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

    def filter_floats(self, sec_data):
        for data in sec_data:
            ticker = data[0]
            company_float = data[1]
            if company_float > self.company_float_threshold:
                self.contracts = [contract for contract in self.contracts if contract.symbol != ticker]
                print(f"...{ticker} removed from list due to high float: {company_float}")
                
    def filter_by_news(self):
        """gets news items for ticker; however, only 3 are available"""
        filtered_contracts = []
        news_providers = self.ib.reqNewsProviders()
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
                latest = headlines[0]
                article = self.ib.reqNewsArticle(
                    providerCode=latest.providerCode,
                    articleId=latest.articleId
                    )
                filtered_contracts.append(contract)
            except IndexError:
                pass
        self.contracts = filtered_contracts
        self.get_ticker_list()