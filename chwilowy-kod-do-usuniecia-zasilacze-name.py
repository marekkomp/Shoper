import requests
import sqlite3
import pandas as pd
import streamlit as st
import xml.etree.ElementTree as ET
import io

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

# Zbiór wszystkich możliwych atrybutów (używanych później przy budowaniu DataFrame)
all_attributes = set()
for item in root.findall('o'):
    attrs = {attr.get("name") for attr in item.find("attrs").findall("a")}
    all_attributes.update(attrs)
all_attributes = sorted(list(all_attributes))

# Ekstrakcja danych z XML
data = []
for item in root.findall('o'):
    # Pobranie atrybutów jako słownik: nazwa atrybutu -> tekst
    attrs = {attr.get("name"): attr.text for attr in item.find("attrs").findall("a")}
    
    record = {
        "id": item.get("id"),
        "url": item.get("url"),
        "price": float(item.get("price")),
        "stock": int(item.get("stock")),
        "name": item.find("name").text.strip(),
        "category": item.find("cat").text.strip(),
    }
    
    # Dla każdego atrybutu – jeśli dany atrybut występuje, pobieramy jego wartość (ze strippingiem),
    # w przeciwnym wypadku ustawiamy "<nie dotyczy>"
    for attr in all_attributes:
        value = attrs.get(attr)
        record[attr] = value.strip() if value else "<nie dotyczy>"
    
    data.append(record)

# Konwersja do DataFrame i uzupełnienie ewentualnych braków
df = pd.DataFrame(data)
df.fillna("<nie dotyczy>", inplace=True)

# Zapis danych do bazy SQLite
conn = sqlite3.connect("produkty.db")
df.to_sql("produkty", conn, if_exists="replace", index=False)
conn.close()

# Streamlit – aplikacja interaktywna
conn = sqlite3.connect("produkty.db")
df = pd.read_sql_query("SELECT * FROM produkty", conn)

st.title("Stan magazynowy kompre.pl (BETA)")

# Wyszukiwanie po nazwie produktu
product_name = st.text_input("Wpisz fragment nazwy produktu:")

st.header("Filtry")

# Filtracja po cenie
min_price = st.slider("Minimalna cena", int(df['price'].min()), int(df['price'].max()), int(df['price'].min()))
max_price = st.slider("Maksymalna cena", int(df['price'].min()), int(df['price'].max()), int(df['price'].max()))

# Filtracja po kategorii
category = st.selectbox("Kategoria", options=["Wszystkie"] + df['category'].dropna().unique().tolist())

# Dynamiczne filtry dla pozostałych atrybutów
filters = {}
for attr in all_attributes:
    unique_values = df[attr].dropna().unique().tolist()
    if unique_values:
        filters[attr] = st.selectbox(f"{attr}", options=["Wszystkie"] + unique_values)

# Budowanie zapytania SQL na podstawie ustawionych filtrów
query = f"SELECT * FROM produkty WHERE price BETWEEN {min_price} AND {max_price}"
if category != "Wszystkie":
    query += f" AND category = '{category}'"
for attr, value in filters.items():
    if value != "Wszystkie":
        query += f" AND `{attr}` = '{value}'"
if product_name:
    query += f" AND name LIKE '%{product_name}%'"

filtered_data = pd.read_sql_query(query, conn)

st.header("Wyniki filtrowania")
if filtered_data.empty:
    st.warning("Brak wyników dla wybranych filtrów. Spróbuj zmienić ustawienia filtrów.")
else:
    # Definicje list kolumn dla różnych widoków
    monitor_columns = [
        "id", "price", "stock", "name", "category", "Kondycja", "Producent", "Kod producenta",
        "Stan ekranu", "Stan obudowy", "Ekran dotykowy", "Rozdzielczość ekranu", "Przekątna ekranu",
        "Powłoka matrycy", "Podświetlenie", "Typ matrycy", "Jasność", "Kontrast", "Kąt widzenia",
        "Stopa w komplecie", "Regulacja kąta nachylenia", "Regulacja wysokości", "Pivot",
        "Złącza zewnętrzne", "Kolor", "Wbudowany głośnik", "Informacje dodatkowe", "W zestawie", "Gwarancja"
    ]
    computer_parts_columns = [
        "id", "price", "stock", "name", "category", "Kondycja", "Kod producenta",
        "Rodzaj", "Przeznaczenie", "Typ", "Napięcie", "Pojemność", "Gwarancja"
    ]
    laptop_parts_columns = [
        "id", "price", "stock", "name", "category", "Kondycja", "Kod producenta",
        "Rodzaj", "Przeznaczenie", "Napięcie", "Pojemność", "Gwarancja", "Typ", "Moc",
        "Informacje dodatkowe", "W zestawie"
    ]
    
    # Wybór widoku kolumn
    preset = st.selectbox("Wybierz widok kolumn", 
                           options=["monitory", "części komputerowe", "części laptopowe", "zasilacze", "wszystkie"],
                           index=0)
    
    if preset == "monitory":
        filtered_data = filtered_data[filtered_data["category"] == "Monitory"]
        def build_monitor_name(row):
            cols = ["Producent", "Kod producenta", "Przekątna ekranu", "Typ matrycy", "Rozdzielczość ekranu"]
            parts = []
            for col in cols:
                value = row.get(col, "<nie dotyczy>")
                if value and value != "<nie dotyczy>":
                    parts.append(value)
            if parts:
                return "Monitor " + " ".join(parts)
            else:
                return row["name"]
        filtered_data["name"] = filtered_data.apply(build_monitor_name, axis=1)
        selected_columns = [col for col in monitor_columns if col in filtered_data.columns]
    
    elif preset == "części komputerowe":
        filtered_data = filtered_data[filtered_data["category"] == "Części komputerowe"]
        selected_columns = [col for col in computer_parts_columns if col in filtered_data.columns]
    
    elif preset == "części laptopowe":
        filtered_data = filtered_data[filtered_data["category"] == "Części laptopowe"]
        selected_columns = [col for col in laptop_parts_columns if col in filtered_data.columns]
    
    elif preset == "zasilacze":
        # Filtrowanie – wybieramy tylko produkty, których kategoria to "Zasilacze"
        filtered_data = filtered_data[filtered_data["category"] == "Zasilacze"]
        # Pobranie ręcznych danych od użytkownika
        manual_napiecie = st.text_input("Podaj napięcie zasilacza:", key="napiecie")
        manual_typ = st.text_input("Podaj typ zasilacza:", key="typ")
        manual_moc = st.text_input("Podaj moc zasilacza:", key="moc")
        # Funkcja modyfikująca nazwę produktu poprzez dołączenie wpisanych danych
        def build_zasilacz_name(row):
            details = []
            if manual_napiecie:
                details.append("Napięcie: " + manual_napiecie)
            if manual_typ:
                details.append("Typ: " + manual_typ)
            if manual_moc:
                details.append("Moc: " + manual_moc)
            if details:
                return row["name"] + " (" + ", ".join(details) + ")"
            else:
                return row["name"]
        filtered_data["name"] = filtered_data.apply(build_zasilacz_name, axis=1)
        # Wybieramy kolumny – tutaj pokazujemy podstawowe kolumny
        selected_columns = ["id", "price", "stock", "name", "category"]
    
    else:  # opcja "wszystkie"
        available_columns = list(filtered_data.columns)
        selected_columns = st.multiselect("Wybierz kolumny do wyświetlenia i pobrania", 
                                          options=available_columns, 
                                          default=available_columns)
    
    if not selected_columns:
        st.error("Wybierz przynajmniej jedną kolumnę.")
    else:
        filtered_data = filtered_data[selected_columns]
        st.write(f"Liczba pozycji: {len(filtered_data)}")
        st.dataframe(filtered_data, use_container_width=True)
        
        # Przygotowanie pliku Excel do pobrania
        excel_buffer = io.BytesIO()
        filtered_data.to_excel(excel_buffer, index=False, engine="openpyxl")
        excel_buffer.seek(0)
        
        st.download_button(
            label="Pobierz dane jako Excel",
            data=excel_buffer,
            file_name="produkty.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

conn.close()
