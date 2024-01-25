from ib_insync import *
import pandas as pd
from dataframe_manager import DF_Manager
import os

def upload_historical(tickers):
    """ Retrieves any amount of historical data and creates a DF_Manager with data"""
    if isinstance(tickers, str):
        tickers = [tickers]
    all_data = []
    for ticker in tickers:
        tickers_filename = f"{ticker}_5sec"
        df = pd.read_csv(f'historical_data/{tickers_filename}.csv', delimiter=',')
        df['date'] = pd.to_datetime(df['date'])
        all_data.append(DF_Manager(df, ticker))

    return all_data


def download_historical(tickers_list, to_csv=True):
    for ticker in tickers_list:
        contract = Stock(ticker[0], 'SMART', 'USD')
        ib.qualifyContracts(contract)
        bars = ib.reqHistoricalData(contract = contract,
            endDateTime= ticker[1],
            durationStr= '1 D',
            barSizeSetting= "5 secs",
            whatToShow= "TRADES",
            useRTH= False)
        ib.sleep(1)
        df = util.df(bars)
        #ib.cancelHistoricalData(bars)
        if to_csv:
            filename = f"historical_data/{ticker[0]}_5sec.csv"
            if not os.path.exists(filename):  
                df.to_csv(filename, index=False)
        else:
            return df
'''
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)
tickers_list = ['LBPH', 'NEXI', 'MINM', 'AIMD', 'ACON', 'SNTG', 'ELAB', 'SGMT', 'SPRC']
# dates are 1 day in future so we can get the previous day
date_list = ['20240103 00:00:00', '20240104 00:00:00', '20240105 00:00:00', '20240106 00:00:00', '20240109 00:00:00', '20240110 00:00:00', '20240117 00:00:00', '20240123 00:00:00', '20240125 00:00:00']
#tickers_list = ['ELAB', 'SGMT']
#date_list = ['20240117 00:00:00', '20240123 00:00:00']
tick_date_list = list(zip(tickers_list, date_list))

#all_data = upload_historical(tickers_list)
download_historical(tick_date_list, to_csv=True)

#print(all_data)

ib.disconnect()
'''