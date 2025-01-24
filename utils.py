def map_producer(producer_name, producers_map):
    if not producer_name:
        return "Niezdefiniowany"
    normalized_name = producer_name.strip().upper()
    return producers_map.get(normalized_name, "Niezdefiniowany")

def map_gauge(row):
    category = row.get("category", "").strip().lower()
    obudowa = row.get("obudowa", "").strip().lower()

    if category == "laptopy":
        return "Laptopy"
    if obudowa == "desktop":
        return "Komputer Desktop"
    if obudowa == "tower":
        return "Komputer Tower"
    if obudowa == "all in one":
        return "AIO"
    if obudowa == "sff":
        return "Komputer Desktop SFF"
    if obudowa in ["micro / mini / tiny", "usff"]:
        return "Laptopy"
    if category == "monitory":
        return "Monitory"
    if category == "desktop":
        return "Desktop"

    return "Laptopy"  # Domyślna wartość
