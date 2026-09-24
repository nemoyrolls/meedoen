from datetime import date
from datetime import datetime 


def filter_activities (activities, max_price):
    kept = []
    for item in activities:
        source = item.get('source')

        if not isinstance (source, str):
            continue
        elif not source.startswith('http'):
            continue
        price = item.get('price')
        if not isinstance (price , (int, float)):
            continue
        if price < 0:
            continue

        when_date= item.get('date')
        if when_date is not None:
            try: 
                when_date = datetime.strptime(when_date, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                continue
            if when_date < date.today():
                continue
        if price > max_price:
            continue
        
        
        kept.append(item)
        kept.sort(key=lambda a: a['price'])
    return kept   




if __name__ == "__main__":
    test = [
        {'date': None, "name": "Museum", "price": 0, "source": "https://example.com"},
        {'date': 'next Friday', "name": "Cinema", "price": 8, "source": ""},
        {'date': '2026-12-1',"name": "Concert", "price": 5},
        {'date': '2025-1-1',"name": "Park", "price": "free", "source": "https://example.com"},
        {"name": "Workshop", "price": -3, "source": "https://example.com"},
        {"name": "Library", "price": 7.5, "source": "https://example.com"},
        {"name": "Gallery", "source": "https://example.com"},
                {"name": "Bowling", "price": 6, "date": "2026-12-01", "source": "https://example.com"},
        {"name": "Festival", "price": 4, "date": "2025-01-01", "source": "https://example.com"},
        {"name": "Quiz", "price": 3, "date": "next Friday", "source": "https://example.com"},
    ]
    result = filter_activities(test, 10)
    print(result)