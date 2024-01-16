from ib_insync import *
import time
from scanner import Scanner
from risk_handler import Risk_Handler
from dataframe_manager import DF_Manager
from strategies.engulfing import Engulfing



ib = IB()
ib.connect('127.0.0.1', 7497, clientId=2)

def onBarUpdate(bars, hasNewBar):
    """handles logic for new bar data- Main Loop"""
    if hasNewBar:
        global df
        start_time = time.time()
        df.update(bars)
        open = df.data_1min.open
        high = df.data_1min.high
        low = df.data_1min.low
        close = df.data_1min.close

        engulf_strat = Engulfing(
             df_manager=df,
             risk=risk,
             barsize='1min')
        
        signals = engulf_strat.custom_indicator(open=open,
                                         high=high,
                                         low=low,
                                         close=close)
        market_orders(signals, close)
        print(f"Elapsed Time: {time.time() - start_time}")

def market_orders(signals, close):
        """Logic for sending orders to IB"""
        num_shares = risk.calculate_shares(close)
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
top_gainers = Scanner(ib, 'TOP_PERC_GAIN')
print(top_gainers.tickers_list)
        
# getting float data from SEC        
#sec_data = SEC_Data(top_gainers.tickers_list)
#top_gainers.filter_floats(sec_data.company_float_list)

# extracting best gainer
top_ticker = top_gainers.contracts[0]

print(f"--------------------------{top_ticker.symbol}--------------------------")
print("Qualifing Contract...")
ib.qualifyContracts(top_ticker)
print("Contract Qualified")

# risk handler
print("Initializing Risk_Handler...")
risk = Risk_Handler(
     ib=ib,
     perc_risk=0.8,
     stop_time=None,
     atr_perc=.1)
print("Risk_Handler Initialized...")


# Initialize Strategy Object
#print("Initializing Strategy...")
#strat_engulf = Strategy(
#     df_manager=df,
#     barsize='1min',
#     risk=risk)
#print("Strategy Initialzied...")

# Initalize Backtest Object
#backtest = BackTest(strat_engulf)

# tesitings backtest
#print(backtest.pf.stats())
#backtest.graph_data()


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

# CallBacks
try:
    bars.updateEvent.clear()
    bars.updateEvent += onBarUpdate
    ib.sleep(10000)
except KeyboardInterrupt:
    ib.cancelHistoricalData(bars)
    ib.disconnect()
else:
    ib.cancelHistoricalData(bars)
    ib.disconnect()