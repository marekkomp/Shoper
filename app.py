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

# Ekstrakcja danych z XML
data = []
for item in root.findall('o'):
    # Wydobywanie wszystkich atrybutów z sekcji <attrs>
    attrs = {attr.get("name"): attr.text for attr in item.find("attrs").findall("a")}
    
    # Tworzymy słownik z danymi, w tym dynamicznie dodane atrybuty
    record = {
        "id": item.get("id"),
        "url": item.get("url"),
        "price": float(item.get("price")),
        "stock": int(item.get("stock")),
        "name": item.find("name").text.strip() if item.find("name") is not None else "",
        "category": item.find("cat").text.strip() if item.find("cat") is not None else "",
    }
    
    # Dodajemy wszystkie atrybuty z sekcji <attrs>
    record.update(attrs)
    
    data.append(record)

# Konwersja danych do DataFrame
df = pd.DataFrame(data)

# Zapisanie danych do SQLite
conn = sqlite3.connect("produkty.db")
df.to_sql("produkty", conn, if_exists="replace", index=False)
conn.close()

# Streamlit - interaktywna aplikacja
# Połączenie z bazą SQLite
conn = sqlite3.connect("produkty.db")

# Wczytanie danych z bazy
df = pd.read_sql_query("SELECT * FROM produkty", conn)

# Tytuł aplikacji
st.title("Stan magazynowy kompre.pl (BETA)")

# Filtry w układzie wielu kolumn
st.header("Filtry")
col1, col2, col3, col4 = st.columns(4)

with col1:
    min_price = st.slider("Minimalna cena", int(df['price'].min()), int(df['price'].max()), int(df['price'].min()))
    max_price = st.slider("Maksymalna cena", int(df['price'].min()), int(df['price'].max()), int(df['price'].max()))

with col2:
    stock_filter = st.checkbox("Dostępne (stock > 0)")
    category = st.selectbox("Kategoria", options=["Wszystkie"] + df['category'].dropna().unique().tolist())

with col3:
    if 'screen_size' in df.columns:
        screen_size = st.selectbox("Rozmiar ekranu", options=["Wszystkie"] + df['screen_size'].dropna().unique().tolist())
    else:
        screen_size = "Wszystkie"

    if 'resolution' in df.columns:
        resolution = st.selectbox("Rozdzielczość", options=["Wszystkie"] + df['resolution'].dropna().unique().tolist())
    else:
        resolution = "Wszystkie"

with col4:
    if 'processor_series' in df.columns:
        processor_series = st.selectbox("Seria procesora", options=["Wszystkie"] + df['processor_series'].dropna().unique().tolist())
    else:
        processor_series = "Wszystkie"

    if 'processor' in df.columns:
        processor = st.selectbox("Procesor", options=["Wszystkie"] + df['processor'].dropna().unique().tolist())
    else:
        processor = "Wszystkie"

    if 'touchscreen' in df.columns:
        touchscreen = st.selectbox("Ekran dotykowy", options=["Wszystkie", "Tak", "Nie"])
    else:
        touchscreen = "Wszystkie"

    if 'cores' in df.columns:
        cores = st.selectbox("Rdzenie", options=["Wszystkie"] + df['cores'].dropna().unique().tolist())
    else:
        cores = "Wszystkie"

# Pole do wyszukiwania nazwy produktu
product_name = st.text_input("Wpisz fragment nazwy produktu:")

# Budowanie zapytania SQL na podstawie aktywnych filtrów
query = f"SELECT * FROM produkty WHERE price BETWEEN {min_price} AND {max_price}"

if stock_filter:
    query += " AND stock > 0"
if category != "Wszystkie":
    query += f" AND category = '{category}'"
if screen_size != "Wszystkie" and 'screen_size' in df.columns:
    query += f" AND screen_size = '{screen_size}'"
if resolution != "Wszystkie" and 'resolution' in df.columns:
    query += f" AND resolution = '{resolution}'"
if processor_series != "Wszystkie" and 'processor_series' in df.columns:
    query += f" AND processor_series = '{processor_series}'"
if processor != "Wszystkie" and 'processor' in df.columns:
    query += f" AND processor = '{processor}'"
if touchscreen != "Wszystkie" and 'touchscreen' in df.columns:
    query += f" AND TRIM(touchscreen) = '{touchscreen}'"
if cores != "Wszystkie" and 'cores' in df.columns:
    query += f" AND cores = '{cores}'"
if product_name:
    query += f" AND name LIKE '%{product_name}%'"

# Pobranie danych po zastosowaniu filtrów
filtered_data = pd.read_sql_query(query, conn)

# Wyświetlanie wyników automatycznych
st.header("Wyniki filtrowania")
if filtered_data.empty:
    st.warning("Brak wyników dla wybranych filtrów. Spróbuj zmienić ustawienia filtrów.")
else:
    st.write(f"Liczba pozycji: {len(filtered_data)}")
    st.dataframe(filtered_data, use_container_width=True)
    
    # Eksport do Excela dla tabeli głównej
    excel_buffer_main = io.BytesIO()
    filtered_data.to_excel(excel_buffer_main, index=False, engine="openpyxl")
    excel_buffer_main.seek(0)

    st.download_button(
        label="Pobierz dane jako Excel",
        data=excel_buffer_main,
        file_name="glowna_tabela.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Sekcja dla polecanych produktów
st.header("Styczeń - najnowsza dostawa i polecane produkty")
show_recommended = st.checkbox("Pokaż/Ukryj polecane produkty")

# Lista ID polecanych produktów
recommended_ids = ['279877756', '311442840', '238803967', '230090911']  # Wpisz tutaj ID polecanych produktów

if show_recommended:
    recommended_data = df[df['id'].isin(recommended_ids)]
    if not recommended_data.empty:
        st.write(f"Polecane produkty ({len(recommended_data)} pozycji):")
        st.dataframe(recommended_data, use_container_width=True)

        # Eksport do Excela dla polecanych produktów
        excel_buffer_recommended = io.BytesIO()
        recommended_data.to_excel(excel_buffer_recommended, index=False, engine="openpyxl")
        excel_buffer_recommended.seek(0)

        st.download_button(
            label="Pobierz dane jako Excel",
            data=excel_buffer_recommended,
            file_name="polecane_produkty.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("Brak polecanych produktów do wyświetlenia.")
