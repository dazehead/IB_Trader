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
from strategies.strategy import Strategy
import sys

class Engulfing(Strategy):
    """Class to store strategy resources"""
    def __init__(self, df_manager, risk=None, barsize=None):
        super().__init__(df_manager, risk=risk, barsize=barsize)

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