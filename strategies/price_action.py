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
import plotly.graph_objects as go

class PriceAction(Strategy):
    """Class to store strategy resources"""
    def __init__(self, df_manager, risk=None, barsize=None):
        super().__init__(df_manager=df_manager, risk=risk, barsize=barsize)
        self.speed = .2
        self.highest_high = None
        self.next_high = None
        self.lowest_low = None
        self.next_low = None

    def custom_indicator(self, open, high, low, close):
        pass
        

    def price_action_testing(self):
        """iterates through the dataframe adding the next bar every iteration"""
        for i in range(len(self.data_5min)):
            iterating_data = self.data_5min.iloc[:i+1]
            current_high = iterating_data.high.values[-1]
            current_index = len(iterating_data)
            current_low = iterating_data.low.values[-1]

            # if highest high is NONE
            self._calculate_highs(current_high, current_index, current_low)
            self._calculate_lows(current_low, current_index)

            self.graph_data(iterating_data, i)


    def _calculate_highs(self, current_high, current_index, current_low):
        if not self.highest_high:
            self.highest_high = (current_index, current_high)

        # if we do not have a new high, and last high is less than current high 
        if (current_high < self.highest_high[1]):
            self.next_high = (current_index, current_high)
        # sets higher high and previous high this means a breakout
        elif current_high > self.highest_high[1]:
            """break out reset everything"""
            self.highest_high = (current_index, current_high)
            self.lowest_low = (current_index, current_low)
            self.next_high = None
            self.next_low = None

    def _calculate_lows(self, current_low, current_index):
        if not self.lowest_low:
            self.lowest_low = (current_index, current_low)
        
        if current_low > self.lowest_low[1]:
            self.next_low = (current_index, current_low)
        elif current_low < self.lowest_low[1]:
            """ break out"""
            self.lowest_low = (current_index, current_low)
            self.next_low = None

    def graph_data(self, iterating_data, i):
        fig = iterating_data.vbt.ohlcv.plots(settings=dict(plot_type='candlestick'))
        print(self.highest_high, self.next_high)

        # Assuming you have only one trace in the figure
        candlestick_trace = fig.data[0]

        # Update x, open, high, low, close data
        candlestick_trace.x = [j for j in range(i+1)]
        candlestick_trace.open = iterating_data['open']
        candlestick_trace.high = iterating_data['high']
        candlestick_trace.low = iterating_data['low']
        candlestick_trace.close = iterating_data['close']

        # Show the updated figure
        if self.highest_high and self.next_high:
            line_trace = go.Scatter(
                x=[self.highest_high[0], self.next_high[0]], 
                y=[self.highest_high[1], self.next_high[1]],
                mode='lines',
                name='High Line')
            fig.add_trace(line_trace)
        if self.lowest_low and self.next_low:
            line_trace1 = go.Scatter(
                x=[self.lowest_low[0], self.next_low[0]],
                y=[self.lowest_low[1], self.next_low[1]],
                mode='lines',
                name='Low Line')
            fig.add_trace(line_trace1)

        fig.show()

        time.sleep(self.speed)

        