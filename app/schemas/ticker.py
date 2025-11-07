from pydantic import BaseModel


class TickerData(BaseModel):
    ticker_id: str
