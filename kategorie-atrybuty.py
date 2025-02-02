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

# Zestaw wszystkich możliwych atrybutów
all_attributes = set()

# Pierwsza iteracja – zbieranie nazw atrybutów
for item in root.findall('o'):
    attrs = {attr.get("name") for attr in item.find("attrs").findall("a")}
    all_attributes.update(attrs)

# Konwersja do listy dla późniejszego użycia w DataFrame
all_attributes = sorted(list(all_attributes))

# Ekstrakcja danych z XML
data = []
for item in root.findall('o'):
    attrs = {attr.get("name"): attr.text for attr in item.find("attrs").findall("a")}
    
    record = {
        "id": item.get("id"),
        "url": item.get("url"),
        "price": float(item.get("price")),
        "stock": int(item.get("stock")),
        "name": item.find("name").text.strip(),
        "category": item.find("cat").text.strip(),
    }
    
    # Dodanie wszystkich atrybutów – zamiast "Brak danych" używamy "<nie dotyczy>"
    for attr in all_attributes:
        record[attr] = attrs.get(attr, "<nie dotyczy>").strip() if attrs.get(attr) else "<nie dotyczy>"
    
    data.append(record)

# Konwersja danych do DataFrame
df = pd.DataFrame(data)

# Uzupełnianie brakujących danych w całym DataFrame
df.fillna("<nie dotyczy>", inplace=True)

# Zapisanie danych do SQLite
conn = sqlite3.connect("produkty.db")
df.to_sql("produkty", conn, if_exists="replace", index=False)
conn.close()

# Streamlit – interaktywna aplikacja
# Połączenie z bazą SQLite
conn = sqlite3.connect("produkty.db")

# Wczytanie danych z bazy
df = pd.read_sql_query("SELECT * FROM produkty", conn)

# Tytuł aplikacji
st.title("Stan magazynowy kompre.pl (BETA)")

# Pole do wyszukiwania nazwy produktu
product_name = st.text_input("Wpisz fragment nazwy produktu:")

# Dynamiczne budowanie filtrów
st.header("Filtry")

# Cena
min_price = st.slider("Minimalna cena", int(df['price'].min()), int(df['price'].max()), int(df['price'].min()))
max_price = st.slider("Maksymalna cena", int(df['price'].min()), int(df['price'].max()), int(df['price'].max()))

# Kategoria
category = st.selectbox("Kategoria", options=["Wszystkie"] + df['category'].dropna().unique().tolist())

# Pozostałe atrybuty
filters = {}
for attr in all_attributes:
    unique_values = df[attr].dropna().unique().tolist()
    if unique_values:
        filters[attr] = st.selectbox(f"{attr}", options=["Wszystkie"] + unique_values)

# Budowanie zapytania SQL na podstawie aktywnych filtrów
query = f"SELECT * FROM produkty WHERE price BETWEEN {min_price} AND {max_price}"

if category != "Wszystkie":
    query += f" AND category = '{category}'"

for attr, value in filters.items():
    if value != "Wszystkie":
        query += f" AND `{attr}` = '{value}'"

if product_name:
    query += f" AND name LIKE '%{product_name}%'"

# Pobranie danych po zastosowaniu filtrów
filtered_data = pd.read_sql_query(query, conn)

# Wyświetlanie wyników filtrowania
st.header("Wyniki filtrowania")
if filtered_data.empty:
    st.warning("Brak wyników dla wybranych filtrów. Spróbuj zmienić ustawienia filtrów.")
else:
    # Lista kolumn dla widoku "monitory" w żądanej kolejności
    monitor_columns = [
        "id", "price", "stock", "name", "category", "Kondycja", "Producent", "Kod producenta",
        "Stan ekranu", "Stan obudowy", "Ekran dotykowy", "Rozdzielczość ekranu", "Przekątna ekranu",
        "Powłoka matrycy", "Podświetlenie", "Typ matrycy", "Jasność", "Kontrast", "Kąt widzenia",
        "Stopa w komplecie", "Regulacja kąta nachylenia", "Regulacja wysokości", "Pivot",
        "Złącza zewnętrzne", "Kolor", "Wbudowany głośnik", "Informacje dodatkowe", "W zestawie", "Gwarancja"
    ]
    
    # Lista kolumn dla widoku "części komputerowe"
    computer_parts_columns = [
        "id", "price", "stock", "name", "category", "Kondycja", "Kod producenta",
        "Rodzaj", "Przeznaczenie", "Typ", "Napięcie", "Pojemność", "Gwarancja"
    ]
    
    # Lista kolumn dla widoku "części laptopowe"
    laptop_parts_columns = [
        "id", "price", "stock", "name", "category", "Kondycja", "Kod producenta",
        "Rodzaj", "Przeznaczenie", "Napięcie", "Pojemność", "Gwarancja", "Typ", "Moc",
        "Informacje dodatkowe", "W zestawie"
    ]
    
    # Wybór widoku kolumn – teraz dostępne są trzy opcje: "monitory", "części komputerowe" oraz "części laptopowe"
    preset = st.selectbox("Wybierz widok kolumn", options=["monitory", "części komputerowe", "części laptopowe", "wszystkie"], index=0)
    
    if preset == "monitory":
        # Filtrowanie – wyświetlamy tylko produkty, których kategoria to "Monitory"
        filtered_data = filtered_data[filtered_data["category"] == "Monitory"]
        # Ustawienie kolumn w żądanej kolejności (tylko te, które występują w danych)
        selected_columns = [col for col in monitor_columns if col in filtered_data.columns]
        
        # Modyfikacja kolumny 'name' – budowanie nowej nazwy na podstawie wybranych atrybutów
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
    
    elif preset == "części komputerowe":
        # Filtrowanie – wyświetlamy tylko produkty, których kategoria to "Części komputerowe"
        filtered_data = filtered_data[filtered_data["category"] == "Części komputerowe"]
        # Ustawienie kolumn zgodnie z listą dla części komputerowych
        selected_columns = [col for col in computer_parts_columns if col in filtered_data.columns]
    
    elif preset == "części laptopowe":
        # Filtrowanie – wyświetlamy tylko produkty, których kategoria to "Części laptopowe"
        filtered_data = filtered_data[filtered_data["category"] == "Części laptopowe"]
        # Ustawienie kolumn zgodnie z listą dla części laptopowych
        selected_columns = [col for col in laptop_parts_columns if col in filtered_data.columns]
    
    else:
        # Użytkownik wybiera dowolne kolumny
        available_columns = list(filtered_data.columns)
        selected_columns = st.multiselect(
            "Wybierz kolumny do wyświetlenia i pobrania", 
            options=available_columns, 
            default=available_columns
        )
    
    if not selected_columns:
        st.error("Wybierz przynajmniej jedną kolumnę.")
    else:
        # Aktualizacja danych do wyświetlenia na podstawie wybranych kolumn
        filtered_data = filtered_data[selected_columns]
        
        st.write(f"Liczba pozycji: {len(filtered_data)}")
        st.dataframe(filtered_data, use_container_width=True)
    
        # Przygotowanie pliku Excel
        excel_buffer = io.BytesIO()
        filtered_data.to_excel(excel_buffer, index=False, engine="openpyxl")
        excel_buffer.seek(0)
    
        st.download_button(
            label="Pobierz dane jako Excel",
            data=excel_buffer,
            file_name="produkty.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
