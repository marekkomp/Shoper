import requests
import pandas as pd
import streamlit as st
import xml.etree.ElementTree as ET

# URL do pliku XML
url = "https://firebasestorage.googleapis.com/v0/b/kompreshop.appspot.com/o/xml%2Fkompre.xml?alt=media"

# Pobranie pliku XML
response = requests.get(url)
if response.status_code == 200:
    xml_data = response.content
else:
    st.error(f"Błąd podczas pobierania pliku: {response.status_code}")
    st.stop()

# Wczytanie XML do struktury drzewa
root = ET.fromstring(xml_data)

# Lista wzorcowych producentów
producers_map = {
    "LENOVO": "LENOVO",
    "FUJITSU": "FUJITSU",
    "EIZO": "EIZO",
    "DELL": "DELL",
    "Toshiba": "Toshiba",
    "HP": "HP",
    "EPSON": "EPSON",
    "SAMSUNG": "SAMSUNG",
    "NEC": "NEC",
    "PHILIPS": "PHILIPS",
    "CODI": "CODI",
    "Gobi": "Gobi",
    "PORT": "PORT",
    "ESPERANZA": "ESPERANZA",
    "ERICSSON": "ERICSSON",
    "LG": "LG",
    "Blupop": "Blupop",
    "Titanum": "Titanum",
    "MSONIC": "MSONIC",
    "TP-LINK": "TP-LINK",
    "Apple": "Apple",
    "AOC": "AOC",
    "MEDIA-TECH": "MEDIA-TECH",
    "Logitech": "Logitech",
    "Rebeltec": "Rebeltec",
    "Natec": "Natec",
    "Gembird": "Gembird",
    "Vakoss": "Vakoss",
    "Tracer": "Tracer",
    "Manta": "Manta",
    "4World": "4World",
    "Creative": "Creative",
    "GoodRam": "GoodRam",
    "Maxtor": "Maxtor",
    "Silicon Power": "Silicon Power",
    "Koss": "Koss",
    "Logic": "Logic",
    "Logic Concept": "Logic Concept",
    "Microsoft": "Microsoft",
    "IIYAMA": "IIYAMA",
    "Green Cell": "Green Cell",
    "Acer": "Acer",
    "ViewSonic": "ViewSonic",
    "Asus": "Asus",
    "Pioneer": "Pioneer",
    "HUAWEI": "HUAWEI",
    "XQISIT": "XQISIT",
    "HYNIX": "HYNIX",
    "Xzero": "Xzero",
    "Art": "Art",
    "Kingston": "Kingston",
    "ADATA": "ADATA",
    "Targus": "Targus",
    "MOBILIS": "MOBILIS",
    "Intenso": "Intenso",
    "Modecom": "Modecom",
    "UGO": "UGO",
    "IBOX": "IBOX",
    "EVEREST": "EVEREST",
    "PNY": "PNY",
    "Hitachi": "Hitachi",
    "Corsair": "Corsair",
    "Whitenergy": "Whitenergy",
    "Benq": "Benq",
    "Gigabyte": "Gigabyte",
    "AVG": "AVG",
    "Panasonic": "Panasonic",
    "Seagate": "Seagate",
    "WD": "WD",
    "Novatech": "Novatech"
}

# Funkcja do dopasowania producenta
def map_producer(producer_name):
    if not producer_name:
        return None
    normalized_name = producer_name.strip().upper()
    for key, value in producers_map.items():
        if normalized_name == key.upper():
            return value
    return producer_name  # Zwraca oryginalną nazwę, jeśli nie ma dopasowania

# Ekstrakcja danych z XML
data = []
for item in root.findall('o'):
    # Wydobywanie wszystkich atrybutów z sekcji <attrs>
    attrs = {attr.get("name"): attr.text for attr in item.find("attrs").findall("a")}

    # Zdjęcia z sekcji <imgs>
    imgs = item.find("imgs")
    images = []
    if imgs is not None:
        main_img = imgs.find("main")
        if main_img is not None:
            images.append(main_img.get("url"))
        for i, img in enumerate(imgs.findall("i"), start=1):
            images.append(img.get("url"))

    # Tworzymy słownik z danymi
    record = {
        "product_code": item.get("id"),
        "name": item.find("name").text.strip() if item.find("name") is not None else "",
        "price": float(item.get("price")) if item.get("price") else None,
        "vat": "23%",
        "unit": "szt.",
        "category": item.find("cat").text.strip() if item.find("cat") is not None else "",
        "producer": map_producer(attrs.get("Producent", "")),
        "currency": "PLN",
        "priority": 1,
        "short_description": attrs.get("Krótki opis", ""),
        "description": attrs.get("Opis", ""),
        "stock": int(item.get("stock")) if item.get("stock") else None,
        "availability": "Dostępny" if int(item.get("stock")) > 0 else "Niedostępny",
        "delivery": "3 dni",
    }

    # Dodanie obrazów do rekordu
    for i in range(1, 46):
        record[f"images {i}"] = images[i - 1] if i - 1 < len(images) else None

    # Dodajemy dynamicznie wszystkie atrybuty z XML jako kolumny
    record.update(attrs)

    data.append(record)

# Konwersja danych do DataFrame
df_raw = pd.DataFrame(data)

# Lista kolumn, które mają znaleźć się w tabeli przetworzonej
selected_columns = [
    "product_code", "active", "name", "price", "vat", "unit", "category", "producer", "currency",
    "gauge", "priority", "short_description", "description", "stock", "availability", "delivery",
    "images 1", "images 2", "images 3", "images 4", "images 5", "images 6", "images 7", "images 8",
    "images 9", "images 10", "images 11", "images 12", "images 13", "images 14", "images 15", "images 16",
    "images 17", "images 18", "images 19", "images 20", "images 21", "images 22", "images 23", "images 24",
    "images 25", "images 26", "images 27", "images 28", "images 29", "images 30", "images 31", "images 32",
    "images 33", "images 34", "images 35", "images 36", "images 37", "images 38", "images 39", "images 40",
    "images 41", "images 42", "images 43", "images 44", "images 45", "seo_title", "seo_description",
    "seo_keywords", "booster", "producer_code", "warehouse_code"
]

# Przetwarzanie danych
df_processed = df_raw.copy()

# Dodanie kolumn aktywności i jednostki
df_processed["active"] = df_processed["stock"].apply(lambda x: 1 if x and x > 0 else 0)

# Wypełnienie kolumn SEO
def generate_seo_data(row):
    name = row.get("name", "")
    category = row.get("category", "")
    producer = row.get("producer", "")
    price = row.get("price", "")
    currency = row.get("currency", "")
    delivery = row.get("delivery", "")

    seo_title = f"{name} - {category} - {producer}"
    seo_description = f"Kup {name} w kategorii {category}. Producent: {producer}. Cena: {price} {currency}. Dostawa: {delivery}."
    seo_keywords = f"{name}, {category}, {producer}, tanie {category}, {name} w dobrej cenie"

    return pd.Series({"seo_title": seo_title, "seo_description": seo_description, "seo_keywords": seo_keywords})

df_processed = df_processed.merge(df_processed.apply(generate_seo_data, axis=1), left_index=True, right_index=True)

# Dodanie brakujących kolumn z pustymi wartościami
def ensure_columns(df, columns):
    for col in columns:
        if col not in df.columns:
            df[col] = None
    return df

df_processed = ensure_columns(df_processed, selected_columns)

# Wybranie tylko określonych kolumn do tabeli przetworzonej
df_processed = df_processed[selected_columns]

# Wyświetlenie brakujących kolumn w tabeli przetworzonej
missing_columns = [col for col in selected_columns if col not in df_raw.columns]

# Wyświetlenie w Streamlit
st.title("Tabele danych z XML")

st.header("Tabela surowych danych")
st.dataframe(df_raw, use_container_width=True)

st.header("Tabela przetworzonych danych")
st.dataframe(df_processed, use_container_width=True)

if missing_columns:
    st.warning("Kolumny dodane do tabeli przetworzonej jako puste:")
    st.write(missing_columns)

# Wyświetlenie wszystkich kolumn z tabeli surowej
df_raw_columns = list(df_raw.columns)
st.header("Kolumny z tabeli surowej")
st.write(df_raw_columns)
