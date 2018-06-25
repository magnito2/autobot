from binance.bind import bind_method
from binance.models import Entry, Order
from binance.client import BinanceRESTAPI

NO_ACCEPT_PARAMETERS = []

class CustomClient(BinanceRESTAPI):

    exchange_info = bind_method(
        path="/v1/exchangeInfo",
        method="GET",
        accepts_parameters=NO_ACCEPT_PARAMETERS,
        response_type="entry",
        root_class=Entry)

    new_order = bind_method(
        path="/v3/order",
        method="POST",
        accepts_parameters=["symbol", "side", "type", "time_in_force", "quantity", "price", "new_client_order_id",
                            "stop_price", "iceberg_qty", "timestamp", "recv_window"],
        signature=True,
        response_type="entry",
        root_class=Order)