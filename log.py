import pandas as pd

class Log:
    """A class to log trades and store backtest results for analysis"""
    def __init__(self, backtest, next_node=None):
        self.value = backtest
        self.name = self.value.ticker
        self.next_node = next_node

    def get_name(self):
        return self.name
    
    def get_next_node(self):
        return self.next_node
    
    def set_next_node(self, next_node):
        self.next_node = next_node

class LogBook:
    def __init__(self, value=None):
        self.head_node = Log(value)

    def get_head_node(self):
        return self.head_node
    
    def insert_beginning(self, new_value):
        new_node = Log(new_value)
        new_node.set_next_node(self.head_node)
        self.head_node = new_node

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
        """
        data = []
        current_node = self.get_head_node()
        while current_node:
            data.append(current_node.value.pf.stats().rename(current_node.get_name()))
            current_node = current_node.get_next_node()

        df = pd.concat(data, axis=1)
        return df
        """





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