from datetime import datetime
from ib_insync import *

class Trade:
    """A class to handle interactions with IB"""
    def __init__(self, ib, risk, signals, contract, counter=None, logbook=None):
        self.ib = ib
        self.risk = risk
        self.top_stock = contract
        self.all_signals = signals

        self.todays_date = str(datetime.now()).split(' ')[0]
        self.outside_rth = self.check_RTH()

        if counter is not None:
            self.signal = signals[counter]
        else:
            self.signal = signals[-1]
        market_data = self.ib.reqMktData(self.top_stock, '', False, False)
        # we can get a lot of different dat from this market data
        # ticks(), vwap(), ticks(), volume(), low52wwk(), high52week(), ask(), modelGreeks, bidGreeks
        self.halted = market_data.halted
        self.price = market_data.marketPrice()
        self.num_shares = 200#self.risk.balance_at_risk // self.price
        self.ask = market_data.ask
        self.bid = market_data.bid
        self.symbol_has_positions, self.open_positions = self.check_and_match_positions()
        #self.midpoint = market_data.midpoint
    
    def check_and_match_positions(self):
        print(self.top_stock.symbol)
        for position in self.ib.positions():
            if position.contract.symbol == self.top_stock.symbol:
                print('--position open--')
                return True, position
        return False, []
        
    def execute_trade(self, sell_now = False):
        """Logic for when to buy and sell based off signals and if we already hold positions"""
        print(f"Signal: {self.signal}")
        print(f"Spread: {self.bid}-{self.ask}")
        if self.halted == 0.0: # not halted

            if not self.symbol_has_positions and self.signal == 1 and self.risk.trade[self.top_stock.symbol] is None:
                if self.risk.active_buy_monitoring:
                    # need to put stuff here for active_buy_monitoring
                    self._buy_order(self.num_shares)
                else:
                    self._buy_order(self.num_shares)

            elif self.symbol_has_positions and (self.signal == -1) and (self.risk.trade[self.top_stock.symbol] is None):
                """sell order but we need to check if there is already an order that has not filled then cancel and resubmit"""
                self._sell_order()
            elif self.symbol_has_positions and (self.signal == 0) and (self.risk.trade[self.top_stock.symbol].order.action == 'SELL'):
                self._check_order()
            elif self.symbol_has_positions and (self.signal == -1) and (self.risk.trade[self.top_stock.symbol].order.action == 'SELL'):
                self._sell_order(sell_now=True)

            else:
                """this section is to make sure that all positions were sold if not cancel and put in another market order"""
                self._check_order()
        else: # trading halted passing until trading is resumed
            print("----Trading has been Halted----")
    
    def _buy_order(self, num_shares):
        """Buys order at market order"""
        if self.outside_rth:
            self.risk.trade_num_shares = num_shares
            buy_order = LimitOrder('BUY', num_shares, self.ask)
            buy_order.outsideRth = self.outside_rth
            trade = self.ib.placeOrder(self.top_stock, buy_order)
            self.risk.trade[self.top_stock.symbol] = trade
            print("----BOUGHT----")
        else:
            self.risk.trade_num_shares = num_shares
            buy_order = LimitOrder('BUY', num_shares, self.ask)
            buy_order.outsideRth = self.outside_rth
            trade = self.ib.placeOrder(self.top_stock, buy_order)
            self.risk.trade[self.top_stock.symbol] = trade
            print("----BOUGHT----")
        
    
    def _sell_order(self, sell_now = False):
        if self.outside_rth:
            print("outside RTH")
            """Sells open positions at market"""
            #self.risk.trade = None
            positions = self.open_positions.position
            sell_order = StopOrder("SELL", positions, self.risk.stop_loss)
            if sell_now:
                market_data = self.ib.reqMktData(self.top_stock, '', False, False)
                self.bid = market_data.bid
                self.ib.cancelOrder(self.risk.trade[self.top_stock.symbol].order)
                sell_order = LimitOrder("SELL", positions, self.bid)
            sell_order.outsideRth = self.outside_rth
            trade = self.ib.placeOrder(self.top_stock, sell_order)
            self.risk.trade[self.top_stock.symbol] = trade
        else:
            """Sells open positions at market"""
            #self.risk.trade = None
            positions = self.open_positions.position
            sell_order = StopOrder("SELL", positions, self.risk.stop_loss)
            print(f"stop_loss --------: {self.risk.stop_loss}")
            if sell_now:
                market_data = self.ib.reqMktData(self.top_stock, '', False, False)
                self.bid = market_data.bid
                self.ib.cancelOrder(self.risk.trade[self.top_stock.symbol].order)
                sell_order = LimitOrder("SELL", positions, self.bid)
            sell_order.outsideRth = self.outside_rth
            trade = self.ib.placeOrder(self.top_stock, sell_order)
            self.risk.trade[self.top_stock.symbol] = trade
            print('should have placed stop loss at this moment')


    def _check_order(self):
        """Checks to make sure the orders have been filled, if not then we cancel the orders and place the orders again with updated market"""
        print("-in checking order-\n")
        if self.risk.trade[self.top_stock.symbol] is not None:
            print('-------------1-------------------')
            #print(f"Order Status: {self.risk.trade.orderStatus.status}")  
            if self.risk.trade[self.top_stock.symbol].orderStatus.status != 'Filled' and self.risk.trade[self.top_stock.symbol].orderStatus.status != 'Cancelled':
                #print(f"Order Status: {self.risk.trade.orderStatus.status}")             

                if self.risk.trade[self.top_stock.symbol].order.action == 'BUY':
                    if self.risk.trade_counter[self.top_stock.symbol] == 3:
                        """when the buy order still hasn't been filled and 3 iterations have passed"""
                        self.risk.trade_counter[self.top_stock.symbol] = 0
                        # below is what we previous did still need to verify the .remaining give correct shares
                        #shares_prev_bought = self.risk.trade.order.totalQuantity
                        #self.num_shares = round(self.risk.trade_num_shares - shares_prev_bought, 1)
                        print(f"filled: {self.risk.trade[self.top_stock.symbol].orderStatus.filled} : needing: {self.risk.trade[self.top_stock.symbol].orderStatus.remaining}")
                        self.num_shares = self.risk.trade[self.top_stock.symbol].orderStatus.remaining
                        self.ib.cancelOrder(self.risk.trade[self.top_stock.symbol].order)
                        self._buy_order(self.num_shares)
                        print('canceling and re-buying with calculated shares')
                    elif self.risk.trade[self.top_stock.symbol].orderStatus.status == 'PreSubmitted':
                        self.risk.trade_counter[self.top_stock.symbol] += 1
                    elif self.risk.trade[self.top_stock.symbol].orderStatus.status == 'Submitted':
                        self.risk.trade_counter[self.top_stock.symbol] += 1

                elif self.risk.trade[self.top_stock.symbol].order.action == 'SELL' and self.risk.trade[self.top_stock.symbol].orderStatus.status == 'PreSubmitted':
                    if self.risk.trade_counter[self.top_stock.symbol] == 13:
                        self.risk.trade_counter[self.top_stock.symbol] = 0
                        print("Updating Stop Loss")
                        # below does not update unsure how to modify existing order
                        #updated_order = self.risk.trade.order.update(stopPrice=self.risk.stop_loss)
                        #self.ib.placeOrder(self.top_stock, updated_order)

                        # As of right now we have to cancel and resubmit
                        self.ib.cancelOrder(self.risk.trade[self.top_stock.symbol].order)
                        self._sell_order()
                    #print(self.risk.trade_counter)
                    self.risk.trade_counter[self.top_stock.symbol] += 1
            elif self.risk.trade[self.top_stock.symbol].orderStatus.status == 'Filled' and self.risk.trade[self.top_stock.symbol].order.action == 'BUY':
                print('----------------2--------------------')
                if self.risk.stop_loss == None:
                    print(f"stop_loss is None")
                    pass
                else:
                    self._sell_order()
            else:
                print('-----------------3------------')
                self.risk.trade[self.top_stock.symbol] = None
        pass


    def check_RTH(self):
        """returns whether it is oRTH or not"""
        pre_market_time, post_market_time = self._format_market_times()
        current_time = datetime.now()
        if current_time <= pre_market_time or current_time >= post_market_time:
            return True
        else:
            return False
        
    def _format_market_times(self):
        """Helper function to format datetimes of pre/post market"""
        pre_market_start = str(datetime.strptime('08:30:00', '%H:%M:%S')).split(' ')[1]
        post_market_start = str(datetime.strptime('15:00:00', '%H:%M:%S')).split(' ')[1]        
        pre_market_combined = self.todays_date + " " + pre_market_start
        post_market_combined = self.todays_date + " " + post_market_start
        pre_market_time = datetime.strptime(pre_market_combined, "%Y-%m-%d %H:%M:%S")
        post_market_time = datetime.strptime(post_market_combined, "%Y-%m-%d %H:%M:%S")
        return pre_market_time, post_market_time
