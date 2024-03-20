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
ib.connect('127.0.0.1', 7497, clientId=1)

float_limit = 10
archive = True
counter = 0

if ib.client.port == 7496:
    to_go_on = input("YOU ARE FIXING TO TRADE ON A LIVE ACCOUNT PLEASE INPUT 'Y' TO CONTINUE...").upper()
    if to_go_on != 'Y':
        sys.exit()


"""---------------------START OF PROGRAM--------------------------"""
print("Initializing Trade Log...")
trade_log = LogBook(ib=ib)
print("Trade Log Initialized...")


def onNoTicker(scanDataList):
    print('TEST____________________________')


#initializing Scanner object
if not ib.positions():
    top_gainers = Scanner(ib, 'TOP_PERC_GAIN')
    print(top_gainers.tickers_list)
    top_gainers.filter_floats(float_percentage_limit= float_limit, archive=archive)
    while not top_gainers.tickers_list:
        ib.cancelScannerSubscription(top_gainers.scanDataList)
        ib.sleep(10)
        #top_gainers.scanDataList.updateEvent += onNoTicker
        top_gainers.scan_market()
        top_gainers.filter_floats(float_percentage_limit= float_limit, archive=archive)
        print('No tickers fall within parameters - Continuing to Scan Market....\n')
    print(f"Tickers after filter: {top_gainers.tickers_list}")
    symbols = top_gainers.tickers_list
    for i ,symbol in enumerate(symbols):
        print(f'{i+1}. {symbol}')
    choice = input('!!!!!!!!!!!!!!!!\n!!!!!!!!!\n!!!!!!\n!!!!!!!!!!\n!!!!!!!!!!\n!!!!!!!!!!\n!!!!!!!!!!!!!\n!!!!!!!!!!!!\nWould you like to remove any of these tickers?\n').lower()
    while choice != 'n':
        to_be_removed = int(choice) - 1
        symbols.pop(to_be_removed)
        for i, symbol in enumerate(symbols):
            print(f'{i+1}. {symbol}')
        choice = input('Would you like to remove any more of these tickers?\n').lower()

else:
    print('Tickers with open positions have been added to the list')
    top_gainers = Scanner(ib, 'TOP_PERC_GAIN')
    top_gainers.filter_floats(float_percentage_limit= float_limit, archive=archive)
    open_positions = ib.positions()
    for symbol in open_positions.contract.symbol:
        if symbol not in top_gainers.tickers_list:
            top_gainers.tickers_list.append(symbol)
    symbols = top_gainers.tickers_list
    for i ,symbol in enumerate(symbols):
        print(f'{i+1}. {symbol}')
    choice = input('Would you like to remove any of these tickers?\n').lower()
    while choice != 'n':
        to_be_removed = int(choice) - 1
        symbols.pop(to_be_removed)
        for i, symbol in enumerate(symbols):
            print(f'{i+1}. {symbol}')
        choice = input('Would you like to remove any more of these tickers?\n').lower()


contracts = []
contract_symbols = [obj.symbol for obj in contracts]
for symbol in symbols:
    contracts.append(Stock(symbol, 'SMART', 'USD'))

print("\nInitializing Risk_Handler...")
risk = Risk_Handler(
     ib=ib,
     backtest_db_table="KEFR_KAMA_ATR_below10",
     stop_time=None,
     start_time=None,
     atr_perc=1.5,
     contracts = contracts)
print("\nRisk_Handler Initialized...")


live_bars_dict = {}
barsize = '1 min'
for i, contract_obj in enumerate(contracts):
    live_bars_dict[contract_obj.symbol] = ib.reqHistoricalData(
        contract = contract_obj,
        endDateTime= '',
        durationStr= '1 D',
        barSizeSetting= barsize,
        whatToShow = 'TRADES',
        useRTH= False,
        keepUpToDate= True)
    ib.sleep(1)
print("\nInitiliazing DataFrame Mananger...")
df = DF_Manager(
    bars=live_bars_dict,
    ticker=symbols,
    barsize = barsize)
print("\nDataFrame Mananger Initialized...")

    
#print(live_bars_dict['BAND'][-1])
#print(live_bars_dict['AAPL'][-1].date)

last_update_time = live_bars_dict[symbols[0]][-1].date

def hasNewBarForAllSymbols(live_bars_dict):
    global last_update_time
    latest_timestamps = [bars[-1].date for symbol,bars in live_bars_dict.items()]
    # Check if all latest timstamps are equal
    new_bar_for_all_symbols = all(time==latest_timestamps[0] for time in latest_timestamps)
    if new_bar_for_all_symbols: # if all latest timestamps are equal
        if latest_timestamps[0] > last_update_time: # means we have a new bar
            last_update_time = latest_timestamps[0]
        else:
            new_bar_for_all_symbols = False
    return new_bar_for_all_symbols

# Defining callback on_bar_update but this time globally not just to the specififc real time bars

def on_bar_update(bars, hasNewBar):
    global top_gainers
    global contracts
    global contracts_symbols
    global live_bars_dict
    global df
    global counter
    if hasNewBarForAllSymbols(live_bars_dict):
        counter += 1
        df.update(live_bars_dict)
        for i, contract_obj in enumerate(contracts):
            open = df.main_data[i].open
            high = df.main_data[i].high
            low = df.main_data[i].low
            close = df.main_data[i].close
            strat = Kefr_Kama(
                df_manager=df,
                risk=risk,
                barsize=barsize,
                index=i)
            
            signals = strat.custom_indicator(
                open=open,
                high=high,
                low=low,
                close=close)

            trade = Trade(
                ib=ib, 
                risk=risk, 
                signals=signals,
                contract=contract_obj)
            
            trade.execute_trade()
                    
        print('-------------------------------------------------------------')
def onScanData(scanDataList):
    global live_bars_dict
    global contract_symbols
    global contracts
    global counter
    if counter < 1:
        pass
    else:
        new_symbols = []
        for data in top_gainers.scanDataList:
            symbol = data.contractDetails.contract.symbol
            print(symbol)
            new_symbols.append(symbol)
        for symbol in contract_symbols:
            if symbol not in contract_symbols:
                contract_symbols.append(symbol)
                stock = Stock(symbol, 'SMART', 'USD')
                ib.qualifyContracts(stock)
                contracts.append(stock)
        
        #print(f'\n{len(top_gainers.scanDataList)} Tickers found.')
        #self.ib.cancelScannerSubscription(self.scanDataList)

        top_gainers.get_ticker_list()
        top_gainers.get_finviz_stats()
        top_gainers.filter_floats(float_percentage_limit= float_limit, archive=archive)
        #print(f"Tickers after filter: {top_gainers.tickers_list}")
        for ticker in top_gainers.tickers_list:
            #print(ticker)
            if ticker not in live_bars_dict.keys():
                print(f'.............New ticker {ticker} from scanner....................')
                stock = Stock(ticker, 'SMART', 'USD')
                print('--------------appending contract------------')
                contracts.append(stock)
                print('---------------cancelling sub')
                ib.cancelScannerSubscription(top_gainers.scanDataList)

                print('----------creating new gainSub')
                gainSub = ScannerSubscription(
                    instrument="STK",
                    locationCode="STK.US.MAJOR",
                    scanCode=top_gainers.scancode,
                    stockTypeFilter="CORP")

                # full list of filters
                """https://nbviewer.org/github/erdewit/ib_insync/blob/master/notebooks/scanners.ipynb"""
                tagValues = [TagValue("priceAbove", '1'),
                            TagValue("priceBelow", '20'),
                            TagValue("volumeAbove", '999999'),
                            #TagValue("openGapPercAbove", '25'),
                            TagValue("changePercAbove", "20")]
                print('----------------reqScannerSub')
                top_gainers.scanDataList = ib.reqScannerSubscription(gainSub, [], tagValues)
                print('-------------------canceling historical data')
                for key, data in live_bars_dict.items():
                    ib.cancelHistoricalData(data)
                print('---------------live_bars_dict')
                live_bars_dict = {}
                for i, contract_obj in enumerate(contracts):
                    live_bars_dict[contract_obj.symbol] = ib.reqHistoricalData(
                        contract = contract_obj,
                        endDateTime= '',
                        durationStr= '1 D',
                        barSizeSetting= barsize,
                        whatToShow = 'TRADES',
                        useRTH= False,
                        keepUpToDate= True)
                    ib.sleep(1)
                print('-----------sleeping')
                ib.sleep(1)
            else:
                print('...Scanner has not picked up any new tickers')
        


top_gainers.scanDataList.updateEvent += onScanData
ib.barUpdateEvent.clear()
ib.barUpdateEvent+= on_bar_update
ib.sleep(10000)


# print(f"--------------------------{top_ticker.symbol}--------------------------")
# print("Qualifing Contract...")
# ib.qualifyContracts(top_ticker)
# print("Contract Qualified")








# # risk handler
# print("Initializing Risk_Handler...")
# risk = Risk_Handler(
#      ib=ib,
#      backtest_db_table="KEFR_KAMA_ATR_below10",
#      stop_time=None,
#      start_time=None,
#      atr_perc=1.5)
# print("Risk_Handler Initialized...")

# # Retrieving Historical data and keeping up to date with 5 second intervals
# print("Starting Market Data Subscription...")
# bars = ib.reqHistoricalData(contract = top_ticker,
#                      endDateTime = '',
#                      durationStr = '1 D',
#                      barSizeSetting='1 min',
#                      whatToShow='TRADES',
#                      useRTH=False,
#                      keepUpToDate=True
#                      )
# print("Market Data Subscription Successful...")
# ib.sleep(1)
# print(bars.barSizeSetting)
# print("Initializing DF...")
# df = DF_Manager(
#      bars=bars,
#      ticker=top_ticker.symbol)
# print("DF intialized...")

# #signal_log = LogBook(ib=ib)
# #signal_log.get_head_node().name = top_ticker.symbol



# # CallBacks
# try:
#     bars.updateEvent.clear()
#     bars.updateEvent += onBarUpdate
#     ib.sleep(10000)
# except KeyboardInterrupt:
#     ib.cancelHistoricalData(bars)
#     if ib.positions():
#         choice = input("Would you like to sell all positions? Y or N\n").strip().upper()
#         while choice not in ['Y', 'N']:
#             choice = input("Invalid response please Enter 'Y' or 'N'\n").strip().upper()
#         if choice == 'Y':
#         # need to change to something like ib.sell_all_positions
#             trade = Trade(
#                 ib=ib,
#                 risk=risk,
#                 signals = [-1, -1, -1, -1, -1, -1],
#                 contract=top_ticker)
#             trade.execute_trade(sell_now=True)
#             ib.sleep(5)
#             counter = 0
#             while risk.trade:
#                 trade.execute_trade(sell_now=True)
#                 #signal_log.get_head_node().value[dt.datetime.now()] = -1
#                 ib.sleep(5)
#     trade_log.log_trades()
#     #signal_log.log_signals()
#     ib.disconnect()
#     sys.exit()
# else:
#     ib.cancelHistoricalData(bars)
#     if ib.positions():
#         choice = input("Would you like to sell all positions? Y or N\n").strip().upper()
#         while choice not in ['Y', 'N']:
#             choice = input("Invalid response please Enter 'Y' or 'N'\n").strip().upper()
#         if choice == 'Y':
#         # need to change to something like ib.sell_all_positions
#             trade = Trade(
#                 ib=ib,
#                 risk=risk,
#                 signals = [-1, -1, -1, -1, -1, -1],
#                 contract=top_ticker)
#             trade.execute_trade(sell_now=True)
#             #signal_log.get_head_node().value[dt.datetime.now()] = -1
#             ib.sleep(5)
#             while risk.trade:
#                 trade.execute_trade(sell_now=True)
#                 ib.sleep(5)
#     trade_log.log_trades()
#     #signal_log.log_signals()
#     ib.disconnect()
#     sys.exit()