from ib_insync import *
import pandas as pd
import sys
import sqlite3
import numpy as np

class Risk_Handler:
    """A class to hanlde portfolio risk"""
    def __init__(self, ib=None, backtest_db_table = None ,stop_time=None,start_time=None, contracts = None):
        """Initializing Risk resources"""
        self.ib = ib
        if self.ib is not None:

            self.account_summary = util.df(self.ib.accountSummary())[['tag', 'value']]
            #for i in range(len(self.account_summary)):
            #    print(self.account_summary.iloc[i])

            self.balance = pd.to_numeric(
                self.account_summary.loc[self.account_summary['tag'] == 'TotalCashBalance', 'value'].iloc[0]
                )
            self.buying_power = pd.to_numeric(
                self.account_summary.loc[self.account_summary['tag'] == 'BuyingPower', 'value'].iloc[0]
                )
            
            self.perc_risk = .20#self.kelly_criterion(backtest_db_table)
            self.balance_at_risk = round(self.balance * self.perc_risk, 2)
            if self.buying_power < self.balance_at_risk:
                print(f"\n{self.balance_at_risk} is over our buying power of: {self.buying_power}.")
                print("Will only trade with Buying Power!\n")
                self.balance_at_risk = self.buying_power
                #to_go_on = input(f"Would you like to still trade today only using {self.buying_power}?\n Y or N").upper()
                #while to_go_on not in ['Y', 'N']:
                #    to_go_on = input(f"Invalid Response please enter 'Y' or 'N'").upper()
                #if to_go_on == 'Y':
                #    self.balance_at_risk = self.buying_power
                #elif to_go_on == 'N':
                #sys.exit() 
            self.highest_high = None
            self.trade = {}
            self.trade_num_shares = None
            self.trade_counter = {}
            for contract in contracts:
                self.trade[contract.symbol] = None
                self.trade_counter[contract.symbol] = 0

            print("\n*****************************************")
            print(f"Account Balance: {self.balance}")
            print(f"Buying Power: {self.buying_power}")
            print(f"Percent of Account Balance to be used: {self.perc_risk}")
            print(f"Balance to trade: {self.balance_at_risk}")
            print("*****************************************\n")


        self.stop_loss = {}
            #self.view_account_summary()
        #self.perc_risk = self.kelly_criterion(backtest_db_table)

        self.stop_time = stop_time
        self.start_time = start_time
        # this creates a 2/1 proffit/loss ratio
        self.atr_perc = None
        #self.profit_target_perc = atr_perc * 2
        

        self.active_buy_monitoring = False
        self.started_buy_monitoring = False
    
    def get_buying_power(self, print_to_console=False, only_print=False):
        if only_print:
            print("\n*****************************************")
            print(f"Account Balance: {self.balance}")
            print(f"Buying Power: {self.buying_power}")
            print(f"Percent of Account Balance to be used: {self.perc_risk}")
            print(f"Balance to trade: {self.balance_at_risk}")
            print("*****************************************\n")
        else:
            self.account_summary = util.df(self.ib.accountSummary())[['tag', 'value']]
            self.balance = pd.to_numeric(
                self.account_summary.loc[self.account_summary['tag'] == 'TotalCashBalance', 'value'].iloc[0]
                )
            self.buying_power = pd.to_numeric(
                self.account_summary.loc[self.account_summary['tag'] == 'BuyingPower', 'value'].iloc[0]
                )
            #self.perc_risk = .33#self.kelly_criterion(backtest_db_table)
            self.balance_at_risk = self.balance * self.perc_risk

            if self.buying_power < self.balance_at_risk:
                self.balance_at_risk = self.buying_power
            if print_to_console:
                print("\n*****************************************")
                print(f"Account Balance: {self.balance}")
                print(f"Buying Power: {self.buying_power}")
                print(f"Percent of Account Balance to be used: {self.perc_risk}")
                print(f"Balance to trade: {self.balance_at_risk}")
                print("*****************************************\n")



    def kelly_criterion(self, table):
        if table is not None:
            conn = sqlite3.connect('logbooks/backtests.db')
            df = pd.read_sql(f'SELECT "Total Return [%]" as total_return FROM {table};', conn)
            returns = df['total_return'].to_numpy()
            positive_count = np.sum(returns > 0)
            negative_count = np.sum(returns < 0)
            total_count = len(returns)
            ratio = positive_count/ negative_count
            win_percentage = positive_count / total_count
            kelly_percentage = win_percentage - ((1-win_percentage)/ ratio)

            return kelly_percentage
        else:
            return .10

        

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

        