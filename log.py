import pandas as pd
import datetime
from ib_insync import *
import numpy as np
import datetime
import sqlite3
import os
import yfinance as yf
import pandas_market_calendars as mcal
from finvizfinance.quote import finvizfinance
import requests
import datetime as dt

class Log:
    """A class to log trades and store backtest results for analysis"""
    def __init__(self, node, next_node=None):
        self.value = node
        try:
            self.name = self.value.ticker
        except:
            self.name = None
        self.next_node = next_node
        self.float = None
        if self.value is not None:
            if not isinstance(self.value, list):
                self.get_float()

    def get_float(self):
        fin = finvizfinance(self.name).ticker_fundament()
        try:
            numeric_part = float(fin['Shs Float'][:-1])
            self.float = int(numeric_part * 1_000_000)
            #print(f"retrived float: {self.float}")
        except ValueError:
            print(f"{self.name} has no float: {fin['Shs Float']}")

    def get_name(self):
        return self.name
    
    def get_next_node(self):
        return self.next_node
    
    def set_next_node(self, next_node):
        self.next_node = next_node
    
    def get_signals(self):
        return self.value
    

class LogBook:
    """Linked List that holds all logs"""
    def __init__(self, ib, value=None):
        self.head_node = Log(value)
        self.ib = ib
        self.account_information = []
        if self.ib is not None:
            self.log_portfolio(initial_balance=True)
            #self.get_charts()
        #self.log_portfolio(initial_balance=True)

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
        """Removes a node"""
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

    
    def log_signals(self):
        head_node = self.get_head_node()
        file_path = 'signal_data/'
        signals = head_node.value
        name = head_node.name
        date = head_node.value.index[0]
        date = date.strftime("%Y-%m-%d")

        filename = f"{file_path}/{date}_{name}_signals.csv"
        if not os.path.exists(filename):  
            signals.to_csv(filename, index=True)
        else:
            signals.to_csv(filename, index=True, mode='w')
            # need to combine previous signal data with current signals
            # this will include creating fake times and 0's to fill void


        

    def export_hyper_to_db(self, name_of_strategy):
        """Function to export a hyper optimized backtest to a DB"""
        table_name = name_of_strategy
        current_node = self.get_head_node()
        counter = 0
        final_df = None
        """
        #Queary Genreation
        file_path = 'sql_info.txt'
        with open(file_path, 'r')as file:
            file_contents = file.read()
            strip_q = file_contents.split('SELECT * FROM')
            beginning = strip_q[0]
            ending = strip_q[-1].split(')')[1:]
            ending = ' '.join(ending)
            final_string = beginning
        """
        
        # Extracting data from nodes
        while current_node:
            counter +=1
            df = current_node.value.returns.reset_index()
            df.columns = ['_'.join(col.split('_')[1:])for col in df.columns]
            # These must be the names of the parameters tested
            df['ticker'] = f"{current_node.get_name()}_{counter}"
            if final_df is None:
                final_df = df
            else:
                final_df = pd.concat([final_df, df], ignore_index=True)
            current_node = current_node.get_next_node()
        conn = sqlite3.connect('logbooks/hyper.db')
        final_df.to_sql(table_name, conn, if_exists='replace', index=False)

        """
            #insert save to name so we can copy paste in sql
            if not current_node.get_next_node():
                format_string = f'SELECT * FROM {table_name}\n){ending}'
                final_string += format_string
            else:
                format_string = f'SELECT * FROM {table_name}\nUNION ALL\n\t'
                #print(format_string)
                final_string += format_string
            current_node = current_node.get_next_node()
            """

        #with open(file_path, 'w') as file:
        #    file.write(final_string)




    def export_backtest_to_db(self, name_of_strategy):
        """Function to export a backtest to a db"""
        df = self._convert_to_dataframe()
        name = name_of_strategy
        conn = sqlite3.connect('logbooks/backtests.db')
        df.to_sql(name, conn, if_exists='replace', index=False)
        #df.to_csv(path, index=False)
    

    def _convert_to_dataframe(self):
        """Helper function to convert a backtest information to a DataFrame"""
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
    
    def log_trades(self):
        """Function to retrieve trade information from IB"""
        print('\n...Logging Trades')
        # retrives trades, converts to df, creates new datframe with column names 
        trades = self.ib.trades()
        #print(trades)
        trades_df = util.df(trades)
        #print(trades_df)
        column_names = ['conId','symbol', 'action', 'orderType', 'float', 'market_cap','shares', 'avg_price', 'commission', 'fill_amt', 'time']
        new_df = pd.DataFrame(columns = column_names)
        
        # iterates through the trades and extracts disired data
        try:
            for i in range(len(trades_df)):
                current_node = self.get_head_node()
                #print(f'\n---------------------------{i}----------------------------\n')
                values = []
                values.append(trades_df.contract.iloc[i].conId)
                values.append(trades_df.contract.iloc[i].symbol)
                values.append(trades_df.order.iloc[i].action)
                values.append(trades_df.order.iloc[i].orderType)

                try:
                    fin = finvizfinance(trades_df.contract.iloc[i].symbol).ticker_fundament()
                    try:
                        numeric_float = float(fin['Shs Float'][:-1])                   
                        final_float = int(numeric_float * 1_000_000)
                        values.append(final_float)
                        #print(fin)
                        numeric_cap = float(fin['Market Cap'][:-1])
                        final_cap = int(numeric_cap * 1_000_000)
                        values.append(final_cap)
                    except ValueError:
                        values.append(np.NaN)
                        #print(f"{trades_df.contract.iloc[i].symbol} has no float: {fin['Shs Float']}")
                except requests.HTTPError as err:
                    if err.response.status_code == 404:
                        #print(f"Error 404: Ticker {trades_df.contract.iloc[i].symbol} not found on Finviz")
                        values.append(np.NaN)
                        # Handle the 404 error here
                    else:
                        #print(f"HTTPError: {err}")
                        values.append(np.Nan)
                        # Handle other HTTP errors here
                except Exception as e:
                    #print(f"An unexpected error occurred: {e}")
                    values.append(np.NaN)

                #values.append(trades_df.order.iloc[i].filledQuantity)

                # fills is filled with all order information some multiple orders in order to get filled
                fills = trades_df.fills.iloc[i]
                if len(fills) == 0:
                    # if the fills are empty ie: Cancelled orders I assume
                    values.append(np.NaN)
                    values.append(np.NaN)
                    values.append(np.NaN)
                    values.append(len(fills))
                    values.append(np.NaN)
                elif len(fills) > 1:
                    shares = 0
                    avg_price = 0
                    commission = 0
                    for fill in fills:
                        shares += fill.execution.shares
                        avg_price += fill.execution.price
                        commission += fill.commissionReport.commission

                    avg_price = avg_price / len(fills)
                    values.append(shares)
                    values.append(avg_price)
                    values.append(commission)
                    values.append(len(fills))
                    values.append(fills[-1].execution.time)
                else:
                    #print(fills)
                    values.append(fills[-1].execution.shares)
                    values.append(fills[-1].execution.price)
                    values.append(fills[-1].commissionReport.commission)
                    values.append(len(fills))
                    values.append(fills[-1].execution.time)

                    #print(trades_df.fills.iloc[i])
                #print(values)
                data_dict = dict(zip(column_names, values))
                #print('\n')
                #print(data_dict)
                new_df = new_df._append(data_dict, ignore_index=True)
                new_df.dropna(inplace=True)
                new_df.sort_values(by='time', inplace=True)
                #print(new_df)
            print(new_df)
            self.export_trades_to_db(new_df)
        except TypeError:
            print('Could not export logs as there are no trades for today')

    def calculate_portfolio(self):
        """need to add at the very end when we crl+C to add everything together for the date"""
        # 0: start balance
        # 1: end balance
        # 2: PnL
        # 4: Percent

        column_names = ['start balance', 'end balance', 'PnL', 'Total Return [%]', 'date']
        portfolio_df = pd.DataFrame(columns=column_names)
        if len(self.account_information) == 1:
            pass
        else:
            if not self.ib.positions():
                print('Retriving Portfolio information in calculate_portfolio')
                portfolio_df["start balance"] = self.account_information[0]
                portfolio_df["end balance"] = self.account_information[1]
                portfolio_df["PnL"] = self.account_information[2]
                portfolio_df["Total Return [%]"] = self.account_information[3]
                portfolio_df["date"] = datetime.now().date()
                self.account_information = []
                self.account_information.append(portfolio_df['start balance'])
                self.export_portfolio_to_db(portfolio_df)
            else:
                print("in calculate Portfolio but still has open positions")
                self.account_information = self.account_information[0]
    
    def export_portfolio_to_db(self, df):
        print("exporting portfolio to DB")
        conn = sqlite3.connect('logbooks/trade_log.db')
        if self.ib.client.port == 7497:
            name = 'paper_portfolio'
        else:
            name = 'live_portfolio'
        print("--1")
        df_from_db = pd.read_sql(f'SELECT * FROM {name}', conn)
        print("--2")
        df_from_db["date"] = pd.to_datetime(df_from_db["date"])
        print("--3")
        df["date"] = pd.to_datetime(df['date'])

        print("--4")
        merged_df = pd.merge(df, df_from_db[["date"]], on="date", how="left", indicator=True)
        print("--5")
        result = merged_df[merged_df['_merge'] == 'left_only'].drop('_merge', axis=1)
        print("--6")
        result.to_sql('portfolio_log', conn, if_exist='append', index=False)
        
    
    
    def export_trades_to_db(self, df):
        """takes df and exports it to the trade_log, also logic for duplicates, will not overwrite"""
        conn = sqlite3.connect('logbooks/trade_log.db')
        #print(df)
        if self.ib.client.port == 7497:
            # paper trading
            name = "paper_log"
        else:
            # 7496 -- real account
            name = "live_log"

        df_from_db= pd.read_sql(f'SELECT * FROM {name}', conn)
        df_from_db['time'] = pd.to_datetime(df_from_db['time'])
        df['time'] = pd.to_datetime(df['time'])

        merged_df = pd.merge(df, df_from_db[['time']], on='time', how='left', indicator=True)
        result = merged_df[merged_df['_merge'] == 'left_only'].drop('_merge', axis=1)

        result.to_sql(name, conn, if_exists='append', index=False)


    def get_charts(self):
        """Function retrives Histrocial data for trades in trade log"""
        conn = sqlite3.connect('logbooks/trade_log.db')
        # When we get actual trades db we will have to change this SQL statement to that table
        try: 
            trade_df = pd.read_sql(r"SELECT symbol, strftime('%Y-%m-%d',time) AS time FROM paper_log", conn)
            trade_df.drop_duplicates(subset=['symbol','time'], inplace=True)
        except sqlite3.OperationalError as e:
            print("no such table")
            return
            
        try:
            paper_df = pd.read_sql(r"SELECT symbol, strftime('%Y-%m-%d',time) AS time FROM paper_log", conn)
            paper_df.drop_duplicates(subset=['symbol','time'], inplace=True)
        except sqlite3.OperationalError as e:
            print("no such table")
            return
        
        trade_log = [trade_df, paper_df]
        for df in trade_log:
            
            for i in range(len(df)):
                symbol, date = df.iloc[i][0], df.iloc[i][1]
                filename = f"historical_data/{date}_{symbol}.csv"
                if not os.path.exists(filename):  
                    print(f"...Retreiving Historical Data for {symbol} on {date}")
                    date = pd.to_datetime(date).tz_localize('UTC')
                    cal = mcal.get_calendar('NYSE')
                    early = cal.schedule(start_date=date, end_date=datetime.datetime.now())
                    date = early.iloc[0][1]
                    contract = Stock(symbol, 'SMART', 'USD')
                    self.ib.qualifyContracts(contract)
                    bars = self.ib.reqHistoricalData(contract = contract,
                        endDateTime= date,
                        durationStr= '1 D',
                        barSizeSetting= "5 secs",
                        whatToShow= "TRADES",
                        useRTH= False)
                    self.ib.sleep(1)
                    df = util.df(bars)
                    df.to_csv(filename, index=False)
                else:
                    pass

    def log_portfolio(self, initial_balance = False, after_buy=False, after_sell=False):
        print('...logging portfolio')
        if not initial_balance and not after_buy and not after_sell:
            print('Need to assign something!')
            return
        print('starting account summary')
        self.account_summary = util.df(self.ib.accountSummary())[['tag', 'value']]
        print('getting cash balance')
        cash_balance = pd.to_numeric(
                self.account_summary.loc[self.account_summary['tag'] == 'TotalCashBalance', 'value'].iloc[0]
                )
        if initial_balance:
            self.account_information.append(cash_balance)
        elif after_sell:
            print('after sell is set to true-retrieving pnl')
            pnl = pd.to_numeric(
                self.account_summary.loc[self.account_summary['tag'] == 'RealizedPnL', 'value'].iloc[0]
            )
            print('appending to account information')
            self.account_information.append(cash_balance)
            self.account_information.append(pnl)
            if pnl < 0:
                print('pnl greater than 0')
                percent = abs((self.account_information[1] / self.account_information[0]) - 1)
            else:
                print('pnl less than 0')
                percent = ((self.account_information[1] / self.account_information[0]) - 1)* -1
            print('appending percent to account information')
            self.account_information.append(percent)
            print(self.account_information)


    




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