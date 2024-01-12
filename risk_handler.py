from ib_insync import *
import pandas as pd

class Risk_Handler:
    """A class to hanlde portfolio risk"""
    def __init__(self, ib=None, perc_risk=.8,stop_time=None, atr_perc= .10):
        """Initializing Risk resources"""
        if ib is not None:
            self.ib = ib
            top_ticker = Stock('SNTG', 'SMART', 'USD')
            self.ib.qualifyContracts(top_ticker)
            self.account_summary = util.df(self.ib.accountSummary())
            balance = self.account_summary.loc[self.account_summary['tag'] == 'AvailableFunds', 'value']
            self.balance = pd.to_numeric(balance.iloc[0])
            self.bid_ask_df = None
            self.bid = None
            self.ask = None
            self.mid = None
            self.balance_at_risk = self.balance * self.perc_risk
        self.perc_risk = perc_risk

        self.stop_time = stop_time
        # this creates a 2/1 proffit/loss ratio
        self.atr_perc = atr_perc
        self.profit_target_perc = atr_perc * 2


    def get_directive(self):
        for x in dir(self.ib):
            print(x)

    def calculate_shares(self, contract):
        """Calculates how many shares to purchase based on ticker price and balance_at_risk"""
        bars = self.ib.reqHistoricalData(contract = contract,
                     endDateTime = '',
                     durationStr = '1 D',
                     barSizeSetting='5 secs',
                     whatToShow='BID_ASK',
                     useRTH=False,
                     keepUpToDate=False,
                     )
        self.bid_ask_df = util.df(bars)
        self.bid = self.bid_ask_df['low'].iloc[-1]
        self.ask = self.bid_ask_df['high'].iloc[-1]
        self.mid = (self.bid + self.ask)/2
        num_shares = int((self.balance_at_risk // self.mid))
        return num_shares
    
    def calculate_limit(self, contract):
        """I dont think we will need this because we can just ge3t self.bid"""
        pass
                          

"""--------------------TESTING AREA-----------------------"""
"""
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=3)

top_ticker = Stock('SNTG', 'SMART', 'USD')
risk = Risk_Handler(ib)
risk.calculate_shares(top_ticker)
"""

        