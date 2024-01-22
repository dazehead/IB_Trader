import pandas as pd
import datetime
from ib_insync import util
import numpy as np

class Log:
    """A class to log trades and store backtest results for analysis"""
<<<<<<< HEAD
    def __init__(self, log_file, next_node=None):
        self.value = log_file
        if self.value is not None:
            self.name = self.value.contract.symbol
=======
    def __init__(self, node, next_node=None):
        self.value = node
        try:
            self.name = self.value.ticker
        except:
            print("--------------------get error type so as to add in Log Node for Except function--------------------------------")
>>>>>>> price_action
        self.next_node = next_node
        self.list = []

    def get_name(self):
        return self.name
    
    def get_next_node(self):
        return self.next_node
    
    def set_next_node(self, next_node):
        self.next_node = next_node

class LogBook:
    """Linked List that holds all logs"""
    def __init__(self, ib, value=None):
        self.head_node = Log(value)
        self.ib = ib

    def get_head_node(self):
        return self.head_node
    
    def insert_beginning(self, new_value):
        new_node = Log(new_value)
        new_node.set_next_node(self.head_node)
        self.head_node = new_node

    def insert_end(self, new_value):
        new_node = Log(new_value)
        current_node = self.head_node
        while current_node.get_next_node():
            current_node = current_node.get_next_node()
        current_node.set_next_node(new_node)

    def stringify_tickers(self):
        """this is where we will export our backtests"""
        string_list = ""
        current_node = self.get_head_node()
        while current_node:
            if current_node.get_name() != None:
                string_list += str(current_node.get_name()) + "\n"
            current_node = current_node.get_next_node()
        return string_list
    
    def remove_node(self, name_to_remove):
        current_node = self.get_head_node()
        if current_node.get_name() == name_to_remove:
            self.head_node = current_node.get_next_node()
        else:
            while current_node:
                next_node = current_node.get_next_node()
                if next_node.get_name() == name_to_remove:
                    current_node.set_next_node(next_node.get_next_node())
                    current_node = None
                else:
                    current_node = next_node

    def export_backtest_data(self, path):
        df = self._convert_to_dataframe()
        df.to_csv(path, index=False)

    def _convert_to_dataframe(self):
        data = []
        index_values = []
        tickers = []
        current_node = self.get_head_node()

        while current_node:
            series = current_node.value.pf.stats().rename(current_node.get_name())

            # Append the values and index separately
            data.append(series.values)
            index_values.append(series.index)
            tickers.append(current_node.get_name())

            current_node = current_node.get_next_node()

        # Create a DataFrame using numeric indices and column names from the first backtest
        df = pd.DataFrame(data, index=range(len(data)), columns=index_values[0])
        df['tickers'] = tickers
        return df
<<<<<<< HEAD
    
    def log_trades(self):
        """Function to retrieve trade information from IB"""
        # retrives trades, converts to df, creates new datframe with column names 
        trades = self.ib.trades()
        trades_df = util.df(trades)
        column_names = ['conId', 'symbol', 'action', 'orderType','filledQuantity', 'avg_price', 'commission', 'fill_amt', 'time']
        new_df = pd.DataFrame(columns = column_names)
        
        # iterates through the trades and extracts disired data
        for i in range(len(trades_df)):
            print(f'\n---------------------------{i}----------------------------\n')
            values = []
            values.append(trades_df.contract.iloc[i].conId)
            values.append(trades_df.contract.iloc[i].symbol)
            values.append(trades_df.order.iloc[i].action)
            values.append(trades_df.order.iloc[i].orderType)
            values.append(trades_df.order.iloc[i].filledQuantity)

            # fills is filled with all order information some multiple orders in order to get filled
            fills = trades_df.fills.iloc[i]
            if len(fills) == 0:
                # if the fills are empty ie: Cancelled orders I assume
                values.append(np.NaN)
                values.append(np.NaN)
                values.append(len(fills))
                values.append(np.NaN)
            elif len(fills) > 1:
                avg_price = 0
                commission = 0
                for fill in fills:
                    avg_price += fill.execution.price
                    commission += fill.commissionReport.commission

                avg_price = avg_price * len(fills)
                values.append(avg_price)
                values.append(commission)
                values.append(len(fills))
                values.append(fills[-1].execution.time)
            else:
                print(fills)
                values.append(fills[-1].execution.price)
                values.append(fills[-1].commissionReport.commission)
                values.append(len(fills))
                values.append(fills[-1].execution.time)

                #print(trades_df.fills.iloc[i])
            data_dict = dict(zip(column_names, values))
            new_df = new_df._append(data_dict, ignore_index=True)
            print(new_df.head(10))
            

        


            
        """
        data = []
        current_node = self.get_head_node()
        while current_node:
            data.append(current_node.value.pf.stats().rename(current_node.get_name()))
            current_node = current_node.get_next_node()

        df = pd.concat(data, axis=1)
        return df
        """



=======
>>>>>>> price_action


"""
class Test:
    def __init__(self, object, ticker):
        self.object = object
        self.ticker = ticker

a = Test('data', 'ABCD')
b = Test('data', 'DEFG')
c = Test('data', 'HIJK')
d = Test('data', 'LMNO')


ll = LogBook(d)
ll.insert_beginning(c)
ll.insert_beginning(b)
ll.insert_beginning(a)
print(ll.stringify_tickers())
ll.remove_node('ABCD')
print(ll.stringify_tickers())
"""