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
            # might put logic later for the previous highs and lows so as not to write it out all the time
            iterating_data = self.data_5min.iloc[:i+1]
            current_high = iterating_data.high.values[-1]
            print(f"\n\n-------Iteration: {i}----------")
            print(f"Current High : {current_high}")
            current_low = iterating_data.low.values[-1]

            self._calculate_highs(current_high, i)
            #self._calculate_lows(current_low, i)

            self.graph_data(iterating_data, i)


    def _calculate_highs(self, current_high, i):
        # if highest high is None -- first iteration
        current_pair = (i, current_high)
        previous_high = self.data_5min.iloc[i-1].high
        prev_prev_high = self.data_5min.iloc[i-2].high

        # need a new high --first iteration
        if self.highest_high is None:
            print("NONE")
            # assigning first data as highest
            self.highest_high = current_pair
            #self.lowest_low = (i, current_low)
            return

        # --breakout-- reset with current as highest 
        if current_high > self.highest_high[1]:
            print("BREAKOUT")
            self.highest_high = current_pair
            self.next_high = None

        # assigning next high
        else:# current_high < self.highest_high[1]:
            print("...next high logic")
            
            # if next_high is None
            if self.next_high is None:
                print("Next high is None")
                if current_high == self.highest_high[1]:
                    return
                #elif current_high > self.highest_high[1]:
                #    self.next_high = current_pair
                #    return
                else:# current_high < self.highest_high[1]
                    self.next_high = current_pair
                    

            # if current is going up
            elif current_high > previous_high:
                print("current is going up")

                # next high is None, assign next high to current
                if self.next_high is None:
                    print("next high is None - assign")
                    self.next_high = current_pair

                # assign next high if current going up
                elif current_high >= self.next_high[1]:
                    print("assign next high if current goin up")
                    self.next_high = current_pair

            # current is going down
            elif current_high < previous_high:
                # Green
                #if open > close:
                if prev_prev_high < previous_high:
                    # add logic for if prev close is > current close
                    print("triangle detected! set prev high to next_high")
                    self.next_high = (i-1, self.data_5min.iloc[i-1].high)
                else:
                    # and possiblely check for red v green maybe
                    print("current_high < previous high -- do nothing??????")
                    return
                

    def _calculate_lows(self, current_low, i):
        
        if not self.next_low:
            self.next_low = (i, current_low)
        elif current_low < self.next_low[1]:
            self.next_low = (i, current_low)


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

        