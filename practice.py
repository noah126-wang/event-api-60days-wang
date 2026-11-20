
events = [
    {"type": "click", "value": 10},
    {"type": "purchase", "value": 120},
    {"type": "click", "value": 5},
    {"type": "purchase", "value": 80},
]

def purchase_total(records: list[dict]) -> float:
    return sum(
        record["value"]
        for record in records
        if record["type"] == "purchase"
    )

print(purchase_total(events))
