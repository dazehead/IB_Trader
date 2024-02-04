from ib_insync import *
import pandas as pd
from dataframe_manager import DF_Manager
import os

def upload_historical(tickers=None):
    """ Retrieves any amount of historical data and creates a DF_Manager with data"""
    if not tickers:
        folder_path = 'historical_data'
        file_names = os.listdir(folder_path)
        all_data = []
        for name in file_names:
            date, ticker = name.split('_')
            ticker = ticker.split('.')[0]
            df = pd.read_csv(f"historical_data/{date}_{ticker}.csv", delimiter=',')
            df['date'] = pd.to_datetime(df['date'])
            all_data.append(DF_Manager(df, ticker))

    else:
        if isinstance(tickers, str):
            tickers = [tickers]
        all_data = []

        folder_path = 'historical_data'
        file_names = os.listdir(folder_path)
        
        files_done = []
        for ticker in tickers:
            for name in file_names:
                if ticker in name:
                    date = name.split('_')[0]
                    tickers_filename = f"{date}_{ticker}.csv"
                    if tickers_filename in files_done:
                        pass
                    files_done.append(tickers_filename)
                    df = pd.read_csv(f'historical_data/{tickers_filename}', delimiter=',')
                    df['date'] = pd.to_datetime(df['date'])
                    all_data.append(DF_Manager(df, ticker))

    return all_data


def download_historical(tickers_list, to_csv=True):
    """Downloads historical data from IB"""
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

    def convert_for_hyper(df):
        pass
"""
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
"""