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
        signals = self._process_signal_data(signals)
        if self.risk:
            signals = self._stop_trading_time(signals)

        # Technical Indicators
        #rsi = vbt.RSI.run(close, window = rsi_window).rsi.to_numpy()# converting to numpy array
        #entry_condition = (rsi > 50)
        #exit_condition = (rsi < 30)
        #signals = np.where(entry_condition, 1, np.where(exit_condition, -1, 0))
        #signals = self._process_signal_data(signals)
        #print(signals) # check if signals data is correct

        return signals

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
        #print(len(signals) == len(zeros_array))
        #print(len(data) == len(datetimes))
        #print(len(data), stop_index)
        #print(new_signals)
        #print("****************************\n")
        return new_signals


'''
    def graph_data(self, data):
        """Function to graph data"""
        ########### Graphing for Visualization #################################
        fig = data.vbt.ohlcv.plots(settings=dict(plot_type='candlestick'))
        fig.show()
'''