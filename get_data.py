from ib_insync import *
import pandas as pd
from dataframe_manager import DF_Manager

def upload_historical(tickers):
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
        df = util.df(bars)
        if to_csv:
            df.to_csv(f"historical_data/{ticker[0]}_5sec.csv", index=False)
        else:
            return df
'''
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)
tickers_list = ['LBPH', 'NEXI', 'MINM', 'AIMD', 'ACON', 'SNTG', 'ELAB', 'SGMT']
# dates are 1 day in future so we can get the previous day
date_list = ['20240103 00:00:00', '20240104 00:00:00', '20240105 00:00:00', '20240106 00:00:00', '20240109 00:00:00', '20240110 00:00:00', '20240117 00:00:00', '20240123 00:00:00']
tick_date_list = list(zip(tickers_list, date_list))

all_data = upload_historical(tickers_list)
print(all_data)
#download_historical(tick_date_list, to_csv=True)

ib.disconnect()
'''