import vectorbt as vbt
import pandas as pd
import numpy as np
import talib as ta

class BackTest:
    """Class to handle Backtests"""
    def __init__(self, strategy_object):
        """Initialize backtesting resources from VectorBT"""
        self.strategy = strategy_object
        self.ticker = self.strategy.ticker

        # retrieves data from from Strategy() class
        if self.strategy.barsize == '1min':
            self.data = self.strategy.data_1min
        elif self.strategy.barsize == '5min':
            self.data = self.strategy.data_5min

        # Building/ performed backtest
        self.ind = self.build_indicator_factory()
        self.res = self.generate_signals() 
        self.entries, self.exits = self.convert_signals()
        self.pf = self.run_portfolio()
        self.returns = self.pf.total_return()


    def build_indicator_factory(self):
        """Builds the Indicator Factory"""
        ind = vbt.IndicatorFactory(
            class_name = 'Custom',
            short_name = 'cust',
            input_names = ['open', 'high', 'low', 'close'],
            param_names = ['efratio_timeperiod', 'threshold', 'atr_perc'],
            output_names = ['value']
            ).from_apply_func(
                self.strategy.custom_indicator,
                efratio_timeperiod=4,
                threshold=.9,
                atr_perc=1.5,
                # param1
                to_2d=False
            )
        
        return ind

    def generate_signals(self):
        """Generates the entrie/exits signals"""
        res = self.ind.run(
            self.data.open,
            self.data.high,
            self.data.low,
            self.data.close,
            efratio_timeperiod=3,
            threshold=.5,
            atr_perc=1.2,
            #np.arange(70,100, step=2, dtype=int)
            param_product=True
        )

        return res

    def convert_signals(self):
        """Converts signals to entries and exits"""
        entries = self.res.value == 1.0
        exits = self.res.value == -1.0
        return entries, exits

    def run_portfolio(self):
        """performing backtest"""
        pf = vbt.Portfolio.from_signals(
            self.data.close,
            self.entries,
            self.exits,
            fees=0.0,
            init_cash=10000.0)
        return pf

    def graph_data(self):
        """Function to graph data"""
        fig = self.data.vbt.ohlcv.plots(
            settings=dict(plot_type='candlestick'))
        fig = self.entries.vbt.signals.plot_as_entry_markers(
            self.data.close, fig=fig)
        fig = self.exits.vbt.signals.plot_as_exit_markers(
            self.data.close, fig=fig)
        fig.show()