from ib_insync import *
import pandas as pd

class Risk_Handler:
    """A class to hanlde portfolio risk"""
    def __init__(self, ib=None, perc_risk=0.8,stop_time=None, atr_perc= .10):
        """Initializing Risk resources"""
        if ib is not None:
            self.ib = ib
            #top_ticker = Stock('SNTG', 'SMART', 'USD')
            #self.ib.qualifyContracts(top_ticker)
            self.account_summary = util.df(self.ib.accountSummary())
            balance = self.account_summary.loc[self.account_summary['tag'] == 'AvailableFunds', 'value']
            self.balance = pd.to_numeric(balance.iloc[0])
            print(f"Account Balance: {self.balance}")
            #self.bid_ask_df = None
            self.bid = None
            self.ask = None
            self.mid = None
            self.perc_risk = perc_risk
            self.balance_at_risk = self.balance * self.perc_risk
            print(f"balance to trade: {self.balance_at_risk}")
        self.perc_risk = perc_risk

        self.stop_time = stop_time
        # this creates a 2/1 proffit/loss ratio
        self.atr_perc = atr_perc
        self.profit_target_perc = atr_perc * 2


    def get_directive(self):
        for x in dir(self.ib):
            print(x)

    def calculate_shares(self, price):
        """Calculates how many shares to purchase based on ticker price and balance_at_risk"""
        ### no longer need since we put in self.ib.reqMktData(self.top_stock,'', False, False).marketPrice()
        return int((self.balance_at_risk // price))
    
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

        