from ib_insync import *
from strategies.engulfing import Engulfing
from backtest import BackTest
from risk_handler import Risk_Handler
from get_data import upload_historical
from log import LogBook
from scanner import Scanner
from dataframe_manager import DF_Manager
from market_orders import Trade
import datetime

from strategies.price_action import PriceAction

# CONSTANTS
tickers_list = ['LBPH', 'NEXI', 'MINM', 'AIMD', 'ACON', 'SNTG']


def test_price_action():
    ticker = ['LBPH']
    df_manager = upload_historical(tickers = ticker)
    df_manager = df_manager[0]
    risk = Risk_Handler(
        ib=None,
        perc_risk=0.8,
        stop_time="10:00:00-05:00",
        atr_perc = .1)
    
    strat = PriceAction(
        df_manager=df_manager,
        barsize="5min",
        risk=risk)
    
    strat.price_action_testing()

test_price_action()


def run_backtest(tickers_list):
    """NOTE: update later so that it gets datetime by itself instead of manually inserting the date"""
    df_object_list = upload_historical(tickers=tickers_list)

    risk = Risk_Handler(ib = None,
                        perc_risk = 0.8,
                        stop_time="10:00:00-05:00",
                        atr_perc = .1)

    # iterating of each DF_Manager and creating a strategy object with each manager
    logbook = None
    for i, manager in enumerate(df_object_list):
        if i == 0:
            strat = Engulfing(
                df_manager=manager,
                barsize= "1min",
                risk = risk)
            backtest = BackTest(strat)
            logbook = LogBook(backtest)
        else:
            strat = Engulfing(
                df_manager=manager,
                barsize='1min',
                risk=risk)
            backtest = BackTest(strat)
            logbook.insert_beginning(backtest)
        #print(list(dir(backtest.pf)))
        #print(backtest.pf.stats())
        #backtest.graph_data()
    return logbook
#logbook.export_backtest_data("logbooks/backtests_01152024.csv")
#logbook = run_backtest(tickers_list=tickers_list)
#df = logbook._convert_to_dataframe()
#print(df)

def test_scanner():
    ib = IB()
    ib.connect('127.0.0.1', 7497, clientId=2)
    
    top_gainers = Scanner(ib, 'TOP_PERC_GAIN')
    print(top_gainers.tickers_list)
    top_gainers.filter_by_news()
    print(top_gainers.tickers_list)
    #top_gainers.retreive_filter_params()

#test_scanner()

'''
def onBarUpdate(bars, hasNewBar):
    if hasNewBar:
        global df
        global counter

        df.update(bars)
        trade_handler = Trade(
            ib=ib,
            risk=risk,
            signals=test_data,
            contract=top_stock,
            counter = counter
            )
        print(f"outside RTH: {trade_handler.outside_rth}")
        #if trade_handler.trade is None:
        #    """need to test more but this should stop program from putting in excessive sell orders"""
        #    trade_handler.execute_trade()
        #    counter += 1
        #    print(counter)
        trade_handler.execute_trade()
        counter += 1
        print(counter)


ib = IB()
ib.connect("127.0.0.1", 7497, clientId=2)

top_gainers = Scanner(ib, 'TOP_PERC_GAIN')
top_stock = top_gainers.contracts[0]
#top_stock = Stock('AAPL', 'SMART', 'USD')
#print(f"-------------------------{top_stock.symbol}-------------------------")
ib.qualifyContracts(top_stock)

risk = Risk_Handler(
    ib=ib,
    perc_risk=0.05,
    stop_time=None,
    atr_perc=.1
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
trade_log = LogBook(ib)
trade_log.log_trades()
counter = 0
test_data = [0,0,0,0,1,0,0,0,0,-1,0,0,0,0]

try:
    bars.updateEvent.clear()
    bars.updateEvent += onBarUpdate
    ib.sleep(10000)

except KeyboardInterrupt:
    """fill doesn't have full shares executed ---- maybe some sleep"""
    ib.cancelHistoricalData(bars)
    trade_log.log_trades()
    ib.disconnect()

else:
    ib.cancelHistoricalData(bars)
    trade_log.log_trades()
    ib.disconnect()
    
'''

