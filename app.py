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

df_raw = pd.DataFrame(data)

# Przetwarzanie danych
df_raw["gauge"] = df_raw.apply(map_gauge, axis=1)

# Eksport do Excela
excel_buffer = io.BytesIO()
df_raw.to_excel(excel_buffer, index=False, engine="openpyxl")
excel_buffer.seek(0)

# Streamlit UI
st.title("Przetwarzanie danych XML")
st.dataframe(df_raw, use_container_width=True)

st.download_button(
    label="Pobierz dane jako Excel",
    data=excel_buffer,
    file_name="przetworzone_dane.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
