"""Version A: transparent baseline. NOT IMPLEMENTED YET (step 3: tests are written first)."""


class OrderBookA:
    name = "A"

    def process(self, event):
        return {}

    def add_limit_order(self, event):
        return {}

    def cancel_order(self, event):
        return {}

    def fill_market_sell(self, event):
        return {}

    def snapshot(self):
        return {"bids": [], "asks": []}

    def best_bid(self):
        return None

    def best_ask(self):
        return None

    AddLimitOrder = add_limit_order
    CancelOrder = cancel_order
    FillMarketSell = fill_market_sell
