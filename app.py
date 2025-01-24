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

# Ekstrakcja danych z XML
data = []
for item in root.findall('o'):
    # Wydobywanie wszystkich atrybutów z sekcji <attrs>
    attrs = {attr.get("name"): attr.text for attr in item.find("attrs").findall("a")}

    # Tworzymy słownik z danymi
    record = {
        "product_code": item.get("id"),
        "name": item.find("name").text.strip() if item.find("name") is not None else "",
        "price": float(item.get("price")) if item.get("price") else None,
        "category": item.find("cat").text.strip() if item.find("cat") is not None else "",
        "stock": int(item.get("stock")) if item.get("stock") else None,
        "availability": "Dostępny" if int(item.get("stock")) > 0 else "Niedostępny",
    }

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
df_processed["unit"] = "szt."
df_processed["price"] = df_processed["price"].fillna(0).round(2)

# Wybranie tylko określonych kolumn do tabeli przetworzonej
df_processed = df_processed[[col for col in selected_columns if col in df_processed.columns]]

# Wyświetlenie w Streamlit
st.title("Tabele danych z XML")

st.header("Tabela surowych danych")
st.dataframe(df_raw, use_container_width=True)

st.header("Tabela przetworzonych danych")
st.dataframe(df_processed, use_container_width=True)
