"""
Two Crows Pattern is best used to detect a reversal for a possible exit strategy
note: the pattern must form during a clear uptrend
"""
import vectorbt as vbt
import pandas as pd
import numpy as np
import talib as ta
from ib_insync import *
import sys

class Strategy:
    """Class to store strategy resources"""
    def __init__(self, df_manager, risk=None, barsize=None):
        if barsize is None:
            print("You need to define barsize")
            sys.exit()

        """Initialize different bar data"""
        self.risk = risk
        self.barsize = barsize
        #print("...Initializing Stategy")
        self.data_5sec = df_manager.data_5sec
        self.data_10sec = df_manager.data_10sec
        self.data_1min = df_manager.data_1min
        self.data_5min = df_manager.data_5min
        #print("...Strategy Initialized")

    def custom_indicator(self, open, high, low, close):
        """Actual Strategy to be used"""
        #Pattern Recognition
        strat = ta.CDLENGULFING(open, high, low, close)
        signals = self._process_ta_pattern_data(strat)
        if self.risk:
            if self.risk.stop_time is not None:
                signals = self._stop_trading_time(signals)
            atr = ta.ATR(high, low, close, timeperiod=14)
            signals = self._process_atr_data(signals, atr, close, high)
        signals = self._process_signal_data(signals)
        
        # Technical Indicators
        #rsi = vbt.RSI.run(close, window = rsi_window).rsi.to_numpy()# converting to numpy array
        #entry_condition = (rsi > 50)
        #exit_condition = (rsi < 30)
        #signals = np.where(entry_condition, 1, np.where(exit_condition, -1, 0))
        #signals = self._process_signal_data(signals)
        #print(signals) # check if signals data is correct

        return signals

    def _process_atr_data(self, signals, atr, close, high):
        """Replaces atr nan with 0's on signals and calculates stop loss and profit target
        impements them into new_signals"""
        stop_index = np.where(~np.isnan(atr))[0][0]
        zeros_array = np.zeros_like(signals)
        is_trading = signals[stop_index:]
        not_trading = zeros_array[:stop_index]
        new_signals = np.concatenate((is_trading, not_trading))

        in_trade = False
        price_at_purchase = None
        new_high = None
        for i,price in enumerate(close):
            # skips until atr has values populated
            if np.isnan(atr[i]):
                pass
            else:
                if new_signals[i] == 1 and not in_trade:
                    # assigns the price of stock during a BUY signal 
                    price_at_purchase = price
                    new_high = high[i]
                    in_trade = True
                elif in_trade:
                    if new_high < high[i]:
                        new_high = high[i]
                    stop_loss = new_high - (price_at_purchase * (atr[i] + self.risk.atr_perc))
                    profit_target = price_at_purchase + (price_at_purchase * (atr[i] + self.risk.profit_target_perc))
                    #print(f"STOP LOSS: {stop_loss}")
                    #print(f"PRICE: {price}\n")
                    if price < stop_loss:
                        # hit our stop loss need to SELL
                        new_signals[i] = -1
                        in_trade = False
                    elif new_signals[i] == -1 and price > stop_loss and price < profit_target:
                        # SELL signal but stop loss not hit and profit target not hit: keep going                    
                        new_signals[i] = 0
                    elif (price > profit_target) and (new_signals[i] == -1):
                            # logic for if price is above profit target and a SELL signal occurs
                            in_trade = False

        return new_signals
        

    def _process_ta_pattern_data(self, signals):
        """Helper function to process signals generated through TA-LIB"""
        signals[signals == 100] = 1
        signals[signals == -100] = -1
        return signals

    def _process_signal_data(self, signals): # only use for backtest
        """Helper function to process signals so that Buy and Hold until sell signal"""
        """This might need to be deleted when live trading it does not allow for a Trade"""
        """to go through if the backtest shows 1 at the beginning of the day"""
        in_trade = False

        for i in range(len(signals)):
            if signals[i] == 1:
                if not in_trade:
                    in_trade = True
                else:
                    signals[i] = 0
            elif signals[i] == -1 and not in_trade:
                signals[i] = 0
            elif signals[i] == -1:
                in_trade = False

        return signals
    
    def _stop_trading_time(self, signals):
        #print("\n****************************")
        if self.barsize == '10sec':
            datetimes = self.data_10sec.index
            date = pd.to_datetime(f"{str(datetimes[0]).split()[0]} {self.risk.stop_time}")
            data = self.data_10sec
        elif self.barsize == '1min':
            datetimes = self.data_1min.index
            date = pd.to_datetime(f"{str(datetimes[0]).split()[0]} {self.risk.stop_time}")
            data = self.data_1min
        elif self.barsize == '5min':
            datetimes = self.data_5min.index
            date = pd.to_datetime(f"{str(datetimes[0]).split()[0]} {self.risk.stop_time}")
            data = self.data_5min

        zeros_array = np.zeros_like(signals)
        stop_index = (datetimes == date).argmax()
        trading_time_array = signals[:stop_index]
        stop_trading_array = zeros_array[stop_index:]
        new_signals = np.concatenate((trading_time_array, stop_trading_array))

        return new_signals


'''
    def graph_data(self, data):
        """Function to graph data"""
        ########### Graphing for Visualization #################################
        fig = data.vbt.ohlcv.plots(settings=dict(plot_type='candlestick'))
        fig.show()
'''