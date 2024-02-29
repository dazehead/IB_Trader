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
from sec_data import SEC_Data
import datetime as dt

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
        global signal_log
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


"""---------------------START OF PROGRAM--------------------------"""
print("Initializing Trade Log...")
trade_log = LogBook(ib=ib)
print("Trade Log Initialized...")

# initializing Scanner object
if not ib.positions():
    top_gainers = Scanner(ib, 'TOP_PERC_GAIN')
    print(top_gainers.tickers_list)
    top_gainers.filter_floats(float_percentage_limit= 10, archive=True)
    print(f"Tickers after filter: {top_gainers.tickers_list}")
    top_gainers.calculate_percent_change()
    top_ticker = top_gainers.monitor_percent_change(perc_threshold=.03, time_interval=10)
    choice = input(f"{top_ticker.symbol} has been chosen.\nDo you want to trade this Ticker Y or N?\n").upper()
    while choice != 'Y':
        top_ticker = top_gainers.monitor_percent_change(perc_threshold=.03, time_interval=10)
        choice = input(f"Y or N? for {top_ticker.symbol}\n").upper()

    #top_ticker = top_gainers.contracts[0]
else:
    top_ticker =  Stock(ib.positions()[0].contract.symbol, 'SMART', 'USD')
    

print(f"--------------------------{top_ticker.symbol}--------------------------")
print("Qualifing Contract...")
ib.qualifyContracts(top_ticker)
print("Contract Qualified")

# risk handler
print("Initializing Risk_Handler...")
risk = Risk_Handler(
     ib=ib,
     backtest_db_table="KEFR_KAMA_ATR_below10",
     stop_time=None,
     start_time=None,
     atr_perc=1.5)
print("Risk_Handler Initialized...")

# Retrieving Historical data and keeping up to date with 5 second intervals
print("Starting Market Data Subscription...")
bars = ib.reqHistoricalData(contract = top_ticker,
                     endDateTime = '',
                     durationStr = '1 D',
                     barSizeSetting='1 min',
                     whatToShow='TRADES',
                     useRTH=False,
                     keepUpToDate=True
                     )
print("Market Data Subscription Successful...")
ib.sleep(1)
print(bars.barSizeSetting)
print("Initializing DF...")
df = DF_Manager(
     bars=bars,
     ticker=top_ticker.symbol)
print("DF intialized...")

#signal_log = LogBook(ib=ib)
#signal_log.get_head_node().name = top_ticker.symbol



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
            trade.execute_trade(sell_now=True)
            ib.sleep(5)
            counter = 0
            while risk.trade:
                trade.execute_trade(sell_now=True)
                #signal_log.get_head_node().value[dt.datetime.now()] = -1
                ib.sleep(5)
    trade_log.log_trades()
    #signal_log.log_signals()
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
            trade.execute_trade(sell_now=True)
            signal_log.get_head_node().value[dt.datetime.now()] = -1
            ib.sleep(5)
            while risk.trade:
                trade.execute_trade(sell_now=True)
                ib.sleep(5)
    trade_log.log_trades()
    #signal_log.log_signals()
    ib.disconnect()
    sys.exit()