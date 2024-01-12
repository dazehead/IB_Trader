import vectorbt as vbt
import pandas as pd
import numpy as np
import talib as ta

class BackTest:
    """Class to handle Backtests"""
    def __init__(self, data, strategy_object):
        """Initialize backtesting resources from VectorBT"""
        print("...Initializing BackTest")
        self.strategy = strategy_object
        self.data = data
        self.ind = self.build_indicator_factory()
        self.res = self.generate_signals() 
        self.entries, self.exits = self.convert_signals()
        self.pf = self.run_portfolio()
        self.returns = self.pf.total_return()
        print("...BackTest Initialized")

    def build_indicator_factory(self):
        print("...Building Indicator Factory")
        ind = vbt.IndicatorFactory(
            class_name = 'Custom',
            short_name = 'cust',
            input_names = ['open', 'high', 'low', 'close'],
            param_names = ['rsi_window'],
            output_names = ['value']
            ).from_apply_func(
                self.strategy.custom_indicator,
                rsi_window = 14, # param1
                to_2d=False
            )
        print("...Completed Building Indicator Factory")
        return ind

    def generate_signals(self):
        print("...Generating Signals")
        res = self.ind.run(
            self.data.open,
            self.data.high,
            self.data.low,
            self.data.close,
            rsi_window = 14, #np.arange(70,100, step=2, dtype=int)
            param_product=True
        )
        print("...Completed Generating Signals")
        return res

    def convert_signals(self):
        print("...Converting Signals")
        entries = self.res.value == 1.0
        exits = self.res.value == -1.0
        print("...Completed Converting Signals")
        return entries, exits

    def run_portfolio(self):
        print("...Running Portfolio Analysis")
        pf = vbt.Portfolio.from_signals(self.data.close,
                                            self.entries,
                                            self.exits,
                                            fees=0.0,
                                            init_cash=10000.0)
        print("...Completed Portfolio Analysis")
        return pf

    def graph_data(self):
        """Function to graph data"""
        fig = self.data.vbt.ohlcv.plots(settings=dict(plot_type='candlestick'))
        fig = self.entries.vbt.signals.plot_as_entry_markers(self.data.close, fig=fig)
        fig = self.exits.vbt.signals.plot_as_exit_markers(self.data.close, fig=fig)
        fig.show()