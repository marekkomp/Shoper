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
df = pd.DataFrame(data)

# Wyświetlenie w Streamlit
st.title("Tabela danych z XML")
st.dataframe(df, use_container_width=True)
