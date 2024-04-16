from datetime import datetime
from ib_insync import *
from market_orders import Trade

class Trade_Short(Trade):
    def __init__(self, ib, risk, signals, contract, stop_loss_override=False, counter=None, logbook=None):

        super().__init__(
            ib=ib,
            risk=risk,
            signals=signals,
            contract=contract,
            stop_loss_override=stop_loss_override,
            counter=counter,
            logbook=logbook)

    def execute_trade(self, sell_now = False):
        """Logic for when to buy and sell based off signals and if we already hold positions"""
        print(f"--Signal: {self.signal}")
        print(f"--Spread: {self.bid}-{self.ask}")
        if self.halted == 0.0: # not halted
            if not self.symbol_has_positions and self.signal == 1 and self.risk.trade[self.top_stock.symbol] is None:
                if self.risk.active_buy_monitoring:
                    self.risk.get_buying_power(print_to_console=True)
                    self.num_shares = self.risk.balance_at_risk//self.price
                    self._sell_order(self.num_shares)
                else:
                    self.risk.get_buying_power(print_to_console=True)
                    self.num_shares = self.risk.balance_at_risk//self.price
                    self._sell_order(self.num_shares)

            elif self.symbol_has_positions and (self.signal == -1) and (self.risk.trade[self.top_stock.symbol] is None):
                """sell order but we need to check if there is already an order that has not filled then cancel and resubmit"""
                self._buy_order()
            elif self.symbol_has_positions and (self.signal == 0) and (self.risk.trade[self.top_stock.symbol].order.action == 'SELL'):
                self._check_order()
            elif self.symbol_has_positions and (self.signal == -1) and (self.risk.trade[self.top_stock.symbol].order.action == 'SELL'):
                if not self.stop_loss_override:
                    self._buy_order(sell_now=True)
                else:
                    print('\n*******STOPLOSS OVERRIDE PREVENTED SELL*******\n')

            else:
                """this section is to make sure that all positions were sold if not cancel and put in another market order"""
                self._check_order()
        else: # trading halted passing until trading is resumed
            print("----Trading has been Halted----")        

    def _sell_order(self, num_shares):
        """Buys order at market order"""
        if self.outside_rth:
            print('outside RTH')
        self.risk.trade_num_shares = num_shares
        buy_order = LimitOrder('SELL', num_shares, self.mid)
        buy_order.outsideRth = self.outside_rth
        trade = self.ib.placeOrder(self.top_stock, buy_order)
        self.risk.trade[self.top_stock.symbol] = trade
        print("----BOUGHT----")
        
    
    def _buy_order(self, sell_now = False):
        if self.outside_rth:
            print("outside RTH")
        """BUYS open positions at market"""
        positions = self.open_positions.position
        sell_order = LimitOrder("BUY", positions, self.risk.stop_loss[self.top_stock.symbol], self.risk.stop_loss[self.top_stock.symbol])
        if sell_now:
            market_data = self.ib.reqMktData(self.top_stock, '', False, False)
            self.bid = market_data.bid
            self.ib.cancelOrder(self.risk.trade[self.top_stock.symbol].order)
            sell_order = LimitOrder("BUY", positions, self.mid)
        sell_order.outsideRth = self.outside_rth
        trade = self.ib.placeOrder(self.top_stock, sell_order)
        self.risk.trade[self.top_stock.symbol] = trade

    def _check_order(self):
        """Checks to make sure the orders have been filled, if not then we cancel the orders and place the orders again with updated market"""
        print("--in checking order\n")
        if self.risk.trade[self.top_stock.symbol] is not None:
            print('-------------1-------------------')
            if self.risk.trade[self.top_stock.symbol].orderStatus.status != 'Filled' and self.risk.trade[self.top_stock.symbol].orderStatus.status != 'Cancelled':
                print('1-a')       
                if self.risk.trade[self.top_stock.symbol].order.action == 'SELL':
                    print('1-b')
                    if self.risk.trade[self.top_stock.symbol].orderStatus.status == 'PreSubmitted':
                        print('1-d')
                        self.risk.trade_counter[self.top_stock.symbol] += 1
                    elif self.risk.trade[self.top_stock.symbol].orderStatus.status == 'Submitted':
                        """buy order has not been filled yet"""
                        print('1-e')
                        #self.risk.trade_counter[self.top_stock.symbol] += 1
                        print(f"filled: {self.risk.trade[self.top_stock.symbol].orderStatus.filled} : needing: {self.risk.trade[self.top_stock.symbol].orderStatus.remaining}")
                        num_shares = self.risk.trade[self.top_stock.symbol].orderStatus.remaining
                        self.ib.cancelOrder(self.risk.trade[self.top_stock.symbol].order)
                        self._buy_order(num_shares)

                elif self.risk.trade[self.top_stock.symbol].order.action == 'BUY' and self.risk.trade[self.top_stock.symbol].orderStatus.status == 'PreSubmitted':
                    print('1-f')
                    print(self.risk.trade_counter)
                    print(f'trade_counter: {self.risk.trade_counter[self.top_stock.symbol]}')
                    if self.risk.trade_counter[self.top_stock.symbol] >= 2:
                        print('1-f-1')
                        self.risk.trade_counter[self.top_stock.symbol] = 0
                        if not self.stop_loss_override:
                            print("Updating Stop Loss")
                            self.ib.cancelOrder(self.risk.trade[self.top_stock.symbol].order)
                            self._sell_order()
                    print('1-f-2')
                    self.risk.trade_counter[self.top_stock.symbol] += 1
            elif self.risk.trade[self.top_stock.symbol].orderStatus.status == 'Filled' and self.risk.trade[self.top_stock.symbol].order.action == 'SELL':
                print('----------------2--------------------')
                if self.risk.stop_loss[self.top_stock.symbol] == None:
                    print(f"stop_loss is None")
                    pass
                else:
                    print('2-a')
                    self._sell_order()
            elif self.risk.trade[self.top_stock.symbol].orderStatus.status == 'Filled' and self.risk.trade[self.top_stock.symbol].order.action == 'BUY':
                print('----------------3--------------')
                self.risk.trade[self.top_stock.symbol] = None
            else:
                print('-----------------4------------')
                self.risk.trade[self.top_stock.symbol] = None
        print('-----------------5-----------------')
        pass