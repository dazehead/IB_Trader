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
        self.scan_market()
        self.retreive_scanner_params()
        self.get_ticker_list()
        print("...Scanner Initialized")

    def scan_market(self):
        """Function to retrieve Tickers from Scanner"""
        gainSub = ScannerSubscription(
            instrument="STK",
            locationCode="STK.US.MAJOR",
            scanCode=self.scancode,
            stockTypeFilter="CORP",
            abovePrice=1.0,
            belowPrice=20.0,
            aboveVolume=999999)

        scanDataList = self.ib.reqScannerSubscription(gainSub)
        self.ib.sleep(1.5)
        for data in scanDataList:
            # retrieves all the tickers-converts to Stock object and appends them to a list
            stock = Stock(data.contractDetails.contract.symbol, 'SMART', 'USD')
            self.contracts.append(stock)
        print(f'{len(scanDataList)} Tickers found.')
        self.retreive_scanner_params()

    def retreive_scanner_params(self):
        """Function to retreive all parameters available to use in a scanner"""
        params = self.ib.reqScannerParameters()

        # Pars the XML string
        root = ET.fromstring(params)
        # Create a list of dictionaries to store data
        data = []
        for instrument in root.findall('.//Instrument'):
            instrument_data = {}
            for child in instrument:
                instrument_data[child.tag] = child.text
            data.append(instrument_data)

        # Create Pandas DataFrame
        self.parameters_df = pd.DataFrame(data)

    def search_param(self, param):
        """Function to search a particualar parameter----NOT DONE ONLY RETURNS INDICES"""
        indices_with_param = self.parameters_df[self.parameters_df['filters'].str.contains(param, case=False, na=False)].index
        print(f"Indices where {param} is present: ", indices_with_param)

    def get_ticker_list(self):
        """retreived a list of all the tickers found on scanner"""
        for contract in self.contracts:
            self.tickers_list.append(contract.symbol)

    def filter_floats(self, sec_data):
        for data in sec_data:
            ticker = data[0]
            company_float = data[1]
            if company_float > self.company_float_threshold:
                self.contracts = [contract for contract in self.contracts if contract.symbol != ticker]
                print(f"...{ticker} removed from list due to high float: {company_float}")
                
        