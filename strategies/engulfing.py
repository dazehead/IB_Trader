"""
This searches for an Engulfing candle as the signal
can be used as Bullish or Bearish
Bullish signals as 1, Bearish Signals as -1
"""
import vectorbt as vbt
import pandas as pd
import numpy as np
import talib as ta
from ib_insync import *

class Strategy:
    """Class to store strategy resources"""
    def __init__(self, df_manager):
        """Initialize different bar data"""
        #print("...Initializing Stategy")
        self.data_5sec = df_manager.data_5sec
        self.data_10sec = df_manager.data_10sec
        self.data_1min = df_manager.data_1min
        self.data_5min = df_manager.data_5min
        #print("...Strategy Initialized")

    def custom_indicator(self, open, high, low, close, rsi_window=14):
        """Actual Strategy to be used"""

        #Pattern Recognition
        engulfing = ta.CDLENGULFING(open, high, low, close)
        signals = self._process_ta_pattern_data(engulfing)
        #signals = self._process_signal_data(signals)

        # Technical Indicators
        rsi = vbt.RSI.run(close, window = rsi_window).rsi.to_numpy()# converting to numpy array
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

    def graph_data(self, data):
        """Function to graph data"""
        ########### Graphing for Visualization #################################
        fig = data.vbt.ohlcv.plots(settings=dict(plot_type='candlestick'))
        fig.show()