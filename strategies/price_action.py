"""
Price Action Strategy
"""
import vectorbt as vbt
import pandas as pd
import numpy as np
import talib as ta
from ib_insync import *
import sys
from strategy import Strategy

class PriceAction(Strategy):
    """Class to store strategy resources"""
    def __init__(self, df_manager, risk=None, barsize=None):
        super().__init__(df_manager=df_manager, risk=risk, barsize=barsize)

    def custom_indicator(self, open, high, low, close):
        pass
    def graph_data():