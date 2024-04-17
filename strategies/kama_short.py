from strategies.kefr_kama import Kefr_Kama
import plotly.graph_objects as go
import pandas as pd
import talib as ta
import numpy as np
import math
import time
from numba import njit


class Kama_Short(Kefr_Kama):
    def __init__(self, df_manager, risk=None, barsize=None, index=None):
        """we have inversed the ATR to add instead of subtract and took the difference from close and added it to close"""
        super().__init__(df_manager=df_manager, risk=risk, barsize=barsize, index=index)

    def simple_atr_process(self, signals, atr, close):
        print('---simple atr process')
        if self.risk.ib is not None:
            """if we are connected to IB"""
            self.risk.stop_loss[self.ticker] = close[-1] + (close[-1] - round(self.kama[-1] + atr[-1] * self.risk.atr_perc, 2))
            print(f'---Stop Loss: {self.risk.stop_loss[self.ticker]}')
            if close[-1] <= self.risk.stop_loss[self.ticker]:
                print('----COVER SELL SIGNAL')
                """BUY"""
                new_signals = signals
                new_signals[-1] = -1
            elif close[-1] < self.risk.stop_loss[self.ticker]:
                print('----NOTHING SIGNAL')
                new_signals = signals
        else:
            """If we are only backtesting and NOT connected to IB"""
            stop_index = np.where(~np.isnan(atr))[0][0]
            zeros_array = np.zeros_like(signals)
            is_trading = signals[stop_index:]
            not_trading = zeros_array[:stop_index]
            new_signals = np.concatenate((is_trading, not_trading))
            self.risk.stop_loss = None

            in_trade = False
            for i,price in enumerate(close):
                try:
                    price = close[i+14]
                    #print(f"------------------------{i}------------------------")
                    # skips until atr has values populated
                    if np.isnan(atr[i]):
                        pass
                    else:
                        self.risk.stop_loss = close[-1] + (close[-1] -(self.kama[i] + atr[i] * self.risk.atr_perc))
                        if new_signals[i] == 1 and not in_trade:
                            #print(i, price, self.kama[i], price > self.kama[i])  
                            if price > self.kama[i]:
                            # assigns the price of stock during a BUY signal 
                                in_trade = True
                                #print('BUY')
                                #print(i, new_signals[i], price, self.kama[i], price > self.kama[i])
                            else:
                                new_signals[i] = 0
                        elif in_trade:
                            if price > self.risk.stop_loss:
                                """BUY COVER SELL"""
                                new_signals[i] = -1
                                in_trade = False
                            elif price < self.risk.stop_loss:
                                new_signals[i] = 0

                except IndexError:
                    pass
            #add 14 zeros to the front of atr
            temp_signals = new_signals[:-14]
            new_signals = np.concatenate((np.zeros(14), temp_signals))

        return new_signals