"""
Price Action Strategy
"""
import vectorbt as vbt
import pandas as pd
import numpy as np
import talib as ta
from ib_insync import *
import sys
from strategies.strategy import Strategy
import time

class PriceAction(Strategy):
    """Class to store strategy resources"""
    def __init__(self, df_manager, risk=None, barsize=None):
        super().__init__(df_manager=df_manager, risk=risk, barsize=barsize)
        self.speed = .2

    def custom_indicator(self, open, high, low, close):
        pass
        

    def graph_data(self):
        for i in range(len(self.data_5min)):
            iterating_data = self.data_5min.iloc[:i]
            fig = iterating_data.vbt.ohlcv.plots(settings=dict(plot_type='candlestick'))

            # Assuming you have only one trace in the figure
            candlestick_trace = fig.data[0]

            # Update x, open, high, low, close data
            candlestick_trace.x = iterating_data.index
            candlestick_trace.open = iterating_data['open']
            candlestick_trace.high = iterating_data['high']
            candlestick_trace.low = iterating_data['low']
            candlestick_trace.close = iterating_data['close']

            # Show the updated figure
            fig.show()

            time.sleep(self.speed)

        