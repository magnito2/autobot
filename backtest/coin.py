class Coin:

    def __init__(self):
        self._amount = 0
        self.name = "Default Coin"

    def deposit(self, deposit_amount):
        self._amount += deposit_amount

    def withdraw(self, withdraw_amount):
        if self._amount < withdraw_amount:
            raise ValueError('You have insufficient amount')
        else:
            self._amount -= withdraw_amount

    def balance(self):
        return self._amount

    def __repr__(self):
        return f"<{self.name} Bal- {self.balance()}>"

class BitCoin(Coin):
    def __init__(self):
        Coin.__init__(self)
        self.name = "BTC"

class USDT(Coin):
    def __init__(self):
        Coin.__init__(self)
        self.name = "USDT"
