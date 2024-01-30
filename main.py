from ib_insync import *
import time
from scanner import Scanner
from risk_handler import Risk_Handler
from dataframe_manager import DF_Manager
from strategies.engulfing import Engulfing
from market_orders import Trade
from log import LogBook
from backtest import BackTest
import sys
from strategies.kefr_kama import Kefr_Kama

"""
7496 - live
7497 - paper
"""
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=2)

if ib.client.port == 7496:
    to_go_on = input("YOU ARE FIXING TO TRADE ON A LIVE ACCOUNT PLEASE INPUT 'Y' TO CONTINUE...").upper()
    if to_go_on != 'Y':
        sys.exit()

def onBarUpdate(bars, hasNewBar):
    """handles logic for new bar data- Main Loop"""
    if hasNewBar:
        global df
        #start_time = time.time()
        df.update(bars)
        open = df.data_1min.open
        high = df.data_1min.high
        low = df.data_1min.low
        close = df.data_1min.close

        strat = Kefr_Kama(
             df_manager=df,
             risk=risk,
             barsize='1min')
        
        signals = strat.custom_indicator(
            open=open,
            high=high,
            low=low,
            close=close)
        
        trade = Trade(
            ib=ib, 
            risk=risk, 
            signals=signals,
            contract=top_ticker)

        trade.execute_trade()
        
        #if signals[-1] == 1 or signals[-1] == -1:
        #    backtest = BackTest(strat)
        #    backtest.graph_data()
        #print(f"Elapsed Time: {time.time() - start_time}")
        #print("------------------------------------------------------------\n")



"""---------------------START OF PROGRAM--------------------------"""
# initializing Scanner object
if not ib.positions():
    top_gainers = Scanner(ib, 'TOP_PERC_GAIN')
    print(top_gainers.tickers_list)
    top_gainers.calculate_percent_change()
    top_ticker = top_gainers.monitor_percent_change(perc_threshold=.04, time_interval=10)
else:
    top_ticker =  Stock(ib.positions()[0].contract.symbol, 'SMART', 'USD')
    
# getting float data from SEC        
#sec_data = SEC_Data(top_gainers.tickers_list)
#top_gainers.filter_floats(sec_data.company_float_list)
# extracting best gainer

print(f"--------------------------{top_ticker.symbol}--------------------------")
print("Qualifing Contract...")
ib.qualifyContracts(top_ticker)
print("Contract Qualified")

# risk handler
print("Initializing Risk_Handler...")
risk = Risk_Handler(
     ib=ib,
     perc_risk=0.1,
     stop_time=None,
     atr_perc=.2)
print("Risk_Handler Initialized...")

# Retrieving Historical data and keeping up to date with 5 second intervals
print("Starting Market Data Subscription...")
bars = ib.reqHistoricalData(contract = top_ticker,
                     endDateTime = '',
                     durationStr = '1 D',
                     barSizeSetting='5 secs',
                     whatToShow='TRADES',
                     useRTH=False,
                     keepUpToDate=True
                     )
print("Market Data Subscription Successful...")
ib.sleep(1)

print("Initializing DF...")
df = DF_Manager(
     bars=bars,
     ticker=top_ticker.symbol)
print("DF intialized...")

print("Initializing Trade Log...")
trade_log = LogBook(ib=ib)
print("Trade Log Initialized...")


# CallBacks
try:
    bars.updateEvent.clear()
    bars.updateEvent += onBarUpdate
    ib.sleep(10000)
except KeyboardInterrupt:
    ib.cancelHistoricalData(bars)
    if ib.positions():
        choice = input("Would you like to sell all positions? Y or N\n").strip().upper()
        while choice not in ['Y', 'N']:
            choice = input("Invalid response please Enter 'Y' or 'N'\n").strip().upper()
        if choice == 'Y':
        # need to change to something like ib.sell_all_positions
            trade = Trade(
                ib=ib,
                risk=risk,
                signals = [-1, -1, -1, -1, -1, -1],
                contract=top_ticker)
            trade.execute_trade()
            ib.sleep(5)
            while risk.trade:
                trade.execute_trade()
                ib.sleep(5)
    trade_log.log_trades()
    ib.disconnect()
    sys.exit()
else:
    ib.cancelHistoricalData(bars)
    if ib.positions():
        choice = input("Would you like to sell all positions? Y or N\n").strip().upper()
        while choice not in ['Y', 'N']:
            choice = input("Invalid response please Enter 'Y' or 'N'\n").strip().upper()
        if choice == 'Y':
        # need to change to something like ib.sell_all_positions
            trade = Trade(
                ib=ib,
                risk=risk,
                signals = [-1, -1, -1, -1, -1, -1],
                contract=top_ticker)
            trade.execute_trade()
            ib.sleep(5)
            while risk.trade:
                trade.execute_trade()
                ib.sleep(5)
    trade_log.log_trades()
    ib.disconnect()
    sys.exit()