from ib_insync import *
from backtest import BackTest
from risk_handler import Risk_Handler
from get_data import upload_historical
from log import LogBook
from scanner import Scanner
from dataframe_manager import DF_Manager
from market_orders import Trade
import datetime
from strategies.price_action import PriceAction
from strategies.kefr_kama import Kefr_Kama
from finvizfinance.quote import finvizfinance
import yfinance as yf
import os
import re
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# CONSTANTS
#tickers_list = ['GHSI', 'SGMT', 'NEXI', 'LBPH', 'MINM', 'CCTG', 'MSS']
tickers_list_below_10 = ['GHSI', 'SUGP', 'SMGT', 'NEXI', 'PLCE', 'CCTG', 'LBPH', 'MGIH', 'BMR', 'MSS', 'MINM']


def get_tickers_below(float_perc):
    conn = sqlite3.connect('logbooks/tickers.db')
    tickers_list = pd.read_sql(f"SELECT ticker FROM statistics WHERE float_perc < {float_perc};", conn)
    tickers_list = tickers_list['ticker'].tolist()

    path = 'historical_data'
    historical_data_raw = os.listdir(path)
    historical_data_list = []
    
    # retrives only tickers
    for row in historical_data_raw:
        matches = re.findall(r'_(.*?)\.', row)
        historical_data_list.append(matches[0])

    # filters any tickers that we dont have historical data for i.e. todays tickers
    historical_set = set(historical_data_list)
    tickers_list = [value for value in tickers_list if value in historical_set]
    
    return tickers_list
#print(get_tickers_below(10))

def test_strategy():
    ticker = ['LBPH']
    df_manager = upload_historical(tickers=ticker)
    df_manager = df_manager[0]
    risk = Risk_Handler(
        ib=None,
        perc_risk=0.8,
        stop_time='10:00:00-05:00',
        atr_perc = .25)
    
    strat = Kefr_Kama(
        df_manager=df_manager,
        barsize="1min",
        risk=risk)
    
    backtest = BackTest(strat)
    backtest.graph_data()
    print(backtest.pf.stats())
#test_stretegy()





def test_price_action():
    ticker = ['LBPH']
    df_manager = upload_historical(tickers = ticker)
    df_manager = df_manager[0]
    risk = Risk_Handler(
        ib=None,
        perc_risk=0.8,
        stop_time="10:00:00-05:00",
        atr_perc = .25)
    
    strat = PriceAction(
        df_manager=df_manager,
        barsize="5min",
        risk=risk)

    strat.price_action_testing()
#test_price_action()





def run_backtest(tickers_list):
    """NOTE: update later so that it gets datetime by itself instead of manually inserting the date"""

    df_object_list = upload_historical(tickers=tickers_list)

    risk = Risk_Handler(ib = None,
                        stop_time="11:00:00-05:00",
                        start_time="07:00:00-05:00",
                        atr_perc = 1.2)

    # iterating of each DF_Manager and creating a strategy object with each manager
    logbook = LogBook(None, None)
    for i, manager in enumerate(df_object_list):
        print(f"---------------------------{manager.ticker}---------------------------------------")
        if i == 0:
            strat = Kefr_Kama(
                df_manager=manager,
                barsize= "1min",
                risk = risk)
            backtest = BackTest(strat)
            logbook = LogBook(ib=None, value=backtest)
        else:
            strat = Kefr_Kama(
                df_manager=manager,
                barsize='1min',
                risk=risk)
            backtest = BackTest(strat)
            logbook.insert_beginning(new_value=backtest)
        #print(list(dir(backtest.pf)))
        print(backtest.pf.stats())
        backtest.graph_data()
    return logbook
logbook = run_backtest(get_tickers_below(10))
logbook.export_backtest_to_db("KEFR_KAMA_ATR_below10")

#df = logbook._convert_to_dataframe()
#print(df)




def test_scanner():
    ib = IB()
    ib.connect('127.0.0.1', 7497, clientId=1)
    
    top_gainers = Scanner(ib, 'TOP_PERC_GAIN')
    top_gainers.calculate_percent_change()
    #top_gainers.filter_by_news()
    top_gainers.filter_floats(archive=False)
    print(top_gainers.tickers_list)
#test_scanner()





def test_ticker_retrieval():
    folder_path = 'historical_data'
    file_names = os.listdir(folder_path)
    tickers = []
    for name in file_names:
        date, ticker = name.split('_')
        ticker = ticker.split('.')[0]

        print(date, ticker)

    #print(file_names)

#test_ticker_retrieval()
        
def test_update_sql():
    file_path = 'sql_info.txt'
    test = ['THIS_IS_THE_TEST1', 'THIS_IS_THE_TEST2', 'THIS_IS_THE_TEST3', 'THIS_IS_THE_TEST4']
    with open(file_path, 'r') as file:
        file_contents = file.read()
        strip_q = file_contents.split('SELECT * FROM')
        beginning = strip_q[0]
        ending = strip_q[-1].split(')')[1:]
        ending = ' '.join(ending)
        last_i = len(test) - 1
        final_string = beginning
        print(final_string)

        for i, table in enumerate(test):
            print(i, last_i)
            if i == last_i:
                format_string = f'SELECT * FROM {table}\n){ending}'
                final_string += format_string + ending
            else:
                format_string = f'SELECT * FROM {table}\nUNION ALL\n\t'
                #print(format_string)
                final_string += format_string
        print(final_string)

#test_update_sql()
        
def plot_from_db(table_name):
    conn= sqlite3.connect("logbooks/hyper.db")
    df = pd.read_sql(f'SELECT AVG(return) AS average_return FROM {table_name} GROUP BY efratio_timeperiod, threshold, atr_perc ORDER BY average_return DESC', conn)
    mean = np.mean(df['average_return'])
    standard_dev = np.std(df['average_return'])
    std_1 = mean-standard_dev
    std_2 = mean + standard_dev
    std_3 = std_1-standard_dev
    std_4 = std_2 + standard_dev
    print(standard_dev)

    
    plt.hist(df['average_return'], bins=30)
    plt.axvline(mean, color='red', label=f'mean: {mean}')
    plt.axvline(std_1,color='orange')
    plt.axvline(std_2, color='orange')
    plt.axvline(std_3,color='orange')
    plt.axvline(std_4, color='orange')
    plt.legend()
    plt.show()
    
        
#plot_from_db('KEFR_KAMA_ATR_below10')
#plot_from_db('KEFR_below_10_active_buying')

def kelly_criterion(table):
    conn = sqlite3.connect('logbooks/backtests.db')
    df = pd.read_sql(f'SELECT "Total Return [%]" as total_return FROM {table};', conn)
    returns = df['total_return'].to_numpy()
    positive_count = np.sum(returns > 0)
    negative_count = np.sum(returns < 0)
    total_count = len(returns)
    ratio = positive_count/ negative_count
    win_percentage = positive_count / total_count
    kelly_percentage = win_percentage - ((1-win_percentage)/ ratio)

    print(f"Win Ratio: {ratio}")
    print(f"Win Percentage: {win_percentage}")
    print(f"Kelly Percentage: {kelly_percentage}")

    return kelly_percentage
#kelly_criterion('KEFR_KAMA_ATR_below10')

"""
def onBarUpdate(bars, hasNewBar):
    if hasNewBar:
        global df
        global counter

        df.update(bars)

        trade = Trade(
            ib=ib,
            risk=risk,
            signals=test_data,
            contract=top_stock,
            counter = counter
            )
        
        trade.execute_trade()
        counter += 1
        print(counter)


ib = IB()
ib.connect("127.0.0.1", 7497, clientId=2)

top_gainers = Scanner(ib, 'TOP_PERC_GAIN')
top_gainers.filter_floats(float_percentage_limit=10, archive=False)
top_stock = top_gainers.contracts[0]
#top_stock = Stock('CHEA', 'SMART', 'USD')
print(f"-------------------------{top_stock.symbol}-------------------------")
ib.qualifyContracts(top_stock)

risk = Risk_Handler(
    ib=ib,
    stop_time=None,
    atr_perc=1.5
)
bars = ib.reqHistoricalData(
    contract=top_stock,
    endDateTime= '',
    durationStr='1 D',
    barSizeSetting='5 secs',
    whatToShow='TRADES',
    useRTH=False,
    keepUpToDate=True
)
df = DF_Manager(
        bars=bars,
        ticker=top_stock.symbol
)
trade_log = LogBook(ib=ib)
#trade_log.log_trades()
counter = 0
test_data = [0,0,0,0,1,0,0,0,0,0,0,0,0,0]

try:
    bars.updateEvent.clear()
    bars.updateEvent += onBarUpdate
    ib.sleep(30000)

except KeyboardInterrupt:
    '''fill doesn't have full shares executed ---- maybe some sleep'''
    ib.cancelHistoricalData(bars)
    #trade_log.log_trades()
    ib.disconnect()

else:
    ib.cancelHistoricalData(bars)
    #trade_log.log_trades()
    ib.disconnect()
"""