from ib_insync import *
import pandas as pd
import sys

class Risk_Handler:
    """A class to hanlde portfolio risk"""
    def __init__(self, ib=None, perc_risk=0.8,stop_time=None,start_time=None, atr_perc= 1.5):
        """Initializing Risk resources"""
        self.ib = ib
        if self.ib is not None:

            self.account_summary = util.df(self.ib.accountSummary())[['tag', 'value']]
            self.balance = pd.to_numeric(
                self.account_summary.loc[self.account_summary['tag'] == 'AvailableFunds', 'value'].iloc[0]
                )
            self.buying_power = pd.to_numeric(
                self.account_summary.loc[self.account_summary['tag'] == 'BuyingPower', 'value'].iloc[0]
                )
            
            self.perc_risk = perc_risk
            self.balance_at_risk = self.balance * self.perc_risk
            if self.buying_power < self.balance_at_risk:
                print("!!!!!!!!BUYING POWER TOO LOW!!!!!!!!")
                to_go_on = input(f"Would you like to still trade today only using {self.buying_power}?\n Y or N").upper()
                while to_go_on not in ['Y', 'N']:
                    to_go_on = input(f"Invalid Response please enter 'Y' or 'N'").upper()
                if to_go_on == 'Y':
                    self.balance_at_risk = self.buying_power
                elif to_go_on == 'N':
                    sys.exit()
            self.highest_high = None
            self.trade = None
            self.trade_num_shares = None
            self.trade_counter = 0

            print(f"Account Balance: {self.balance}")
            print(f"Buying Power: {self.buying_power}")
            print(f"balance to trade: {self.balance_at_risk}")
            #self.view_account_summary()

        self.perc_risk = perc_risk

        self.stop_time = stop_time
        self.start_time = start_time
        # this creates a 2/1 proffit/loss ratio
        self.atr_perc = atr_perc
        self.profit_target_perc = atr_perc * 2
        self.stop_loss = None


    def get_directive(self):
        """Returns the directory of IB class"""
        for x in dir(self.ib):
            print(x)
    
    def view_account_summary(self):
        """prints out our account summary"""
        for i in range(len(self.account_summary)):
            print("-----------------------------------------")
            print(self.account_summary.iloc[i])
                          

"""--------------------TESTING AREA-----------------------"""
"""
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=3)

top_ticker = Stock('SNTG', 'SMART', 'USD')
risk = Risk_Handler(ib)
risk.calculate_shares(top_ticker)
"""

        