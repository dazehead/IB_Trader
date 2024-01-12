import vectorbt as vbt
import numpy as np
import pandas as pd
import talib as ta
import datetime as dt
from ib_insync import *
import time
from scanner import Scanner
from sec_data import SEC_Data
from risk_handler import Risk_Handler
from dataframe_manager import DF_Manager
from strategies.englufing.strategy import Strategy
from strategies.englufing.backtest import BackTest


ib = IB()
ib.connect('127.0.0.1', 7497, clientId=2)

def onBarUpdate(bars, hasNewBar):
    """handles logic for new bar data- Main Loop"""
    if hasNewBar:
        global df
        start_time = time.time()
        df.update(bars)
        engulf_strat = Strategy(df)
        signals = engulf_strat.custom_indicator(open=df.data_1min.open,
                                         high=df.data_1min.high,
                                         low=df.data_1min.low,
                                         close=df.data_1min.close,
                                         rsi_window=14)
        #market_orders(signals)
        print(f"Elapsed Time: {time.time() - start_time}")


def market_orders(signals):
        """Logic for sending orders to IB"""
        num_shares = risk.calculate_shares(top_ticker)
        if not ib.positions() and signals[-1] == 1:
            buy_order = MarketOrder('BUY', num_shares)
            trade = ib.placeOrder(top_ticker, buy_order)
            while not trade.isDone():
                ib.waitOnUpdate()
            print("BUY")
        elif signals[-1] == -1 and ib.positions():
            positions = ib.positions()[0].position
            sell_order = MarketOrder('SELL', positions)
            trade = ib.placeOrder(top_ticker, sell_order)
            while not trade.isDone():
                ib.waitOnUpdate()
            print("SELL")
        #print('OPEN POSITION:' + str(positions))


"""---------------------START OF PROGRAM--------------------------"""
# initializing Scanner object
#top_gainers = Scanner(ib, 'TOP_PERC_GAIN')
#print(top_gainers.tickers_list)
        
# getting float data from SEC        
#sec_data = SEC_Data(top_gainers.tickers_list)
#top_gainers.filter_floats(sec_data.company_float_list)

# extracting best gainer
#top_ticker = top_gainers.contracts[0]
top_ticker = Stock('SNTG', 'SMART', 'USD')

print(f"--------------------------{top_ticker.symbol}--------------------------")
ib.qualifyContracts(top_ticker)

# Retrieving Historical data and keeping up to date with 5 second intervals
bars = ib.reqHistoricalData(contract = top_ticker,
                     endDateTime = '',
                     durationStr = '1 D',
                     barSizeSetting='5 secs',
                     whatToShow='TRADES',
                     useRTH=False,
                     keepUpToDate=True,
                     )


# Initialize DataFrame Manager
df = DF_Manager(bars)

# Initialize Strategy Object
strat_engulf = Strategy(df)

# Initalize Backtest Object
backtest = BackTest(df.data_1min, strat_engulf)

# Initialize Risk Object
risk = Risk_Handler(df)
# tesitings backtest
print(backtest.pf.stats())
backtest.graph_data()


# CallBacks
bars.updateEvent.clear()
bars.updateEvent += onBarUpdate
ib.sleep(10000)
ib.cancelHistoricalData(bars)
ib.disconnect()

