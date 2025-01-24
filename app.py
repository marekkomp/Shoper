import requests
import pandas as pd
import streamlit as st
import xml.etree.ElementTree as ET
import json
import io
from utils import map_producer, map_gauge

# Wczytanie listy producentów z pliku JSON
with open("producers.json", "r") as file:
    producers_map = json.load(file)

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

# Ekstrakcja danych z XML
data = []
for item in root.findall('o'):
    attrs = {attr.get("name"): attr.text for attr in item.find("attrs").findall("a")}
    imgs = item.find("imgs")
    images = [imgs.find("main").get("url")] if imgs is not None and imgs.find("main") else []
    images += [img.get("url") for img in imgs.findall("i")] if imgs is not None else []

    record = {
        "product_code": item.get("id"),
        "name": item.find("name").text.strip() if item.find("name") is not None else "",
        "price": float(item.get("price")) if item.get("price") else None,
        "vat": "23%",
        "unit": "szt.",
        "category": item.find("cat").text.strip() if item.find("cat") is not None else "",
        "producer": map_producer(attrs.get("Producent", ""), producers_map),
        "currency": "PLN",
        "priority": 1,
        "short_description": attrs.get("Krótki opis", ""),
        "description": attrs.get("Opis", ""),
        "stock": int(item.get("stock")) if item.get("stock") else None,
        "availability": "auto",
        "delivery": "3 dni",
        "obudowa": attrs.get("Obudowa", ""),
    }

    for i in range(1, 46):
        record[f"images {i}"] = images[i - 1] if i - 1 < len(images) else None

    data.append(record)

# Konwersja danych do DataFrame
df_raw = pd.DataFrame(data)

# Przetwarzanie danych
df_processed = df_raw.copy()
df_processed["active"] = df_processed["stock"].apply(lambda x: 1 if x and x > 0 else 0)
df_processed["gauge"] = df_processed.apply(map_gauge, axis=1)

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

# Wybranie tylko określonych kolumn
def ensure_columns(df, columns):
    for col in columns:
        if col not in df.columns:
            df[col] = None
    return df

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

df_processed = ensure_columns(df_processed, selected_columns)

# Wybranie przetworzonych kolumn
df_processed = df_processed[selected_columns]

# Wyświetlenie danych w Streamlit
st.title("Tabele danych z XML")

st.header("Tabela surowych danych")
st.dataframe(df_raw, use_container_width=True)

st.header("Tabela przetworzonych danych")
st.dataframe(df_processed, use_container_width=True)

# Pobieranie tabel jako Excel
excel_raw = io.BytesIO()
df_raw.to_excel(excel_raw, index=False, engine="openpyxl")
excel_raw.seek(0)

excel_processed = io.BytesIO()
df_processed.to_excel(excel_processed, index=False, engine="openpyxl")
excel_processed.seek(0)

st.download_button(
    label="Pobierz surowe dane jako Excel",
    data=excel_raw,
    file_name="surowe_dane.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.download_button(
    label="Pobierz przetworzone dane jako Excel",
    data=excel_processed,
    file_name="przetworzone_dane.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.header("Kolumny z tabeli surowej")
st.write(list(df_raw.columns))
