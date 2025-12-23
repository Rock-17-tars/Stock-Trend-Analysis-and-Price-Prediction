from nsepy import get_history
from datetime import date

data = get_history(symbol="RELIANCE", start=date(2024,1,1), end=date(2024,12,31))
print(data)
