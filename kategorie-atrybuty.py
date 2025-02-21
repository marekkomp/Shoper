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
for item in root.findall('o'):
    attrs = {attr.get("name") for attr in item.find("attrs").findall("a")}
    all_attributes.update(attrs)
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
    for attr in all_attributes:
        record[attr] = attrs.get(attr, "<nie dotyczy>").strip() if attrs.get(attr) else "<nie dotyczy>"
    data.append(record)

# Konwersja danych do DataFrame
df = pd.DataFrame(data)
df.fillna("<nie dotyczy>", inplace=True)

# Zapis danych do SQLite
conn = sqlite3.connect("produkty.db")
df.to_sql("produkty", conn, if_exists="replace", index=False)
conn.close()

# Streamlit – interaktywna aplikacja
conn = sqlite3.connect("produkty.db")
df = pd.read_sql_query("SELECT * FROM produkty", conn)

st.title("Stan magazynowy kompre.pl (BETA)")
product_name = st.text_input("Wpisz fragment nazwy produktu:")

st.header("Filtry")
min_price = st.slider("Minimalna cena", int(df['price'].min()), int(df['price'].max()), int(df['price'].min()))
max_price = st.slider("Maksymalna cena", int(df['price'].min()), int(df['price'].max()), int(df['price'].max()))
category = st.selectbox("Kategoria", options=["Wszystkie"] + df['category'].dropna().unique().tolist())

filters = {}
for attr in all_attributes:
    unique_values = df[attr].dropna().unique().tolist()
    if unique_values:
        filters[attr] = st.selectbox(f"{attr}", options=["Wszystkie"] + unique_values)

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
    # Listy kolumn dla poszczególnych widoków
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
    computers_columns = [
        "id", "price", "stock", "name", "category",
        "Kondycja", "Producent", "Seria procesora", "Stan ekranu",
        "Obudowa", "Stan obudowy", "Gwarancja", "Procesor", "Taktowanie", "Ilość rdzeni",
        "Gniazdo procesora", "Ilość pamięci RAM", "Typ pamięci RAM", "Dysk", "Typ dysku",
        "Licencja", "Typ licencji", "Ekran dotykowy", "Rozdzielczość ekranu", 
        "Przekątna ekranu", "Powłoka matrycy", "Podświetlenie",
        "Jasność", "Pivot", "Regulacja wysokości", "Regulacja kąta nachylenia",
        "Wbudowany głośnik", "Rodzaj karty graficznej", "Model karty graficznej",
        "Złącza wewnętrzne", "Złącza z tyłu", "Złącza z boku", "Napęd", "Kamera",
        "Karta Sieciowa", "Informacje dodatkowe", "Kod producenta", "Dodatkowy dysk", "Zainstalowany system", "W zestawie"
    ]
    akcesoria_columns = [
        "id", "price", "stock", "name", "category", "Kondycja", "Stan obudowy", "Kod producenta",
        "Rodzaj", "Długość (cm)", "Przeznaczenie", "Napięcie", "Pojemność", "Gwarancja", "Typ",
        "Interfejs", "Układ", "Moc", "Kolor", "Informacje dodatkowe", "W zestawie"
    ]
    laptopy_columns = [
        "id", "price", "stock", "name", "category",
        "Kondycja", "Producent", "Kod producenta", "Seria procesora", "Stan ekranu",
        "Stan obudowy", "Procesor", "Taktowanie", "Ilość rdzeni",
        "Ilość pamięci RAM", "Typ pamięci RAM", "Dysk", "Dodatkowy dysk", "Typ dysku",
        "Licencja", "Typ licencji", "Zainstalowany system", "Ekran dotykowy",
        "Rozdzielczość ekranu", "Przekątna ekranu", "Powłoka matrycy",
        "Rodzaj karty graficznej", "Model karty graficznej", 
        "Złącza zewnętrzne", "Napęd", "Kamera",
        "Komunikacja", "Bateria", "Klawiatura", "Informacje dodatkowe", "W zestawie", "Gwarancja"
    ]
    
    # Wybór widoku kolumn
    preset = st.selectbox("Wybierz widok kolumn", 
                           options=["monitory", "części komputerowe", "części laptopowe", "komputery", "akcesoria", "laptopy", "wszystkie"], 
                           index=0)
    
    if preset == "monitory":
        filtered_data = filtered_data[filtered_data["category"] == "Monitory"]
        selected_columns = [col for col in monitor_columns if col in filtered_data.columns]
        def build_monitor_name(row):
            cols = ["Producent", "Kod producenta", "Przekątna ekranu", "Typ matrycy", "Rozdzielczość ekranu"]
            parts = [row.get(col, "<nie dotyczy>") for col in cols if row.get(col, "<nie dotyczy>") != "<nie dotyczy>"]
            return "Monitor " + " ".join(parts) if parts else row["name"]
        filtered_data["name"] = filtered_data.apply(build_monitor_name, axis=1)
    
    elif preset == "części komputerowe":
        filtered_data = filtered_data[filtered_data["category"] == "Części komputerowe"]
        selected_columns = [col for col in computer_parts_columns if col in filtered_data.columns]
    
    elif preset == "części laptopowe":
        filtered_data = filtered_data[filtered_data["category"] == "Części laptopowe"]
        selected_columns = [col for col in laptop_parts_columns if col in filtered_data.columns]
    
    elif preset == "komputery":
        filtered_data = filtered_data[filtered_data["category"] == "Komputery"]
        selected_columns = [col for col in computers_columns if col in filtered_data.columns]
        def build_computer_name(row):
            parts = ["Komputer"]
            for col in ["Producent", "Kod producenta", "Ilość pamięci RAM", "Dysk", "Dodatkowy dysk", "Procesor", "Obudowa", "Przekątna ekranu", "Rozdzielczość ekranu"]:
                val = row.get(col, "")
                if val:
                    val = str(val).strip()
                    if val and val not in ("<nie dotyczy>", "<brak danych>"):
                        if col == "Procesor":
                            val = val[:9]
                        parts.append(val)
            parts = [token for token in parts if "brak" not in token.lower()]
            return " ".join(parts)
        filtered_data["name"] = filtered_data.apply(build_computer_name, axis=1)
    
    elif preset == "akcesoria":
        filtered_data = filtered_data[filtered_data["category"] == "Akcesoria"]
        selected_columns = [col for col in akcesoria_columns if col in filtered_data.columns]
    
    elif preset == "laptopy":
        filtered_data = filtered_data[filtered_data["category"] == "Laptopy"]
        selected_columns = [col for col in laptopy_columns if col in filtered_data.columns]
        # Budowanie nazwy dla "Laptopy" zgodnie z nowym schematem
        def build_laptop_name(row):
            # Grupa 1: Producent, Kod producenta, Procesor (skrócony do 10 znaków)
            group1 = []
            for col in ["Producent", "Kod producenta", "Procesor"]:
                val = row.get(col, "<nie dotyczy>")
                if val and val != "<nie dotyczy>":
                    group1.append(val[:10] if col == "Procesor" else val)
            # Grupa 2: Ilość pamięci RAM, Dysk, Dodatkowy dysk, Typ dysku
            group2 = [row.get(col, "<nie dotyczy>") for col in ["Ilość pamięci RAM", "Dysk", "Dodatkowy dysk", "Typ dysku"]]
            group2 = [v for v in group2 if v and v != "<nie dotyczy>"]
            # Grupa 3: Przekątna ekranu, Rozdzielczość ekranu
            group3 = [row.get(col, "<nie dotyczy>") for col in ["Przekątna ekranu", "Rozdzielczość ekranu"]]
            group3 = [v for v in group3 if v and v != "<nie dotyczy>"]
            # Grupa 4: Zainstalowany system
            group4 = [row.get("Zainstalowany system", "<nie dotyczy>")]
            group4 = [v for v in group4 if v and v != "<nie dotyczy>"]
            parts = []
            if group1:
                parts.append(" ".join(group1))
            if group2:
                parts.append(" ".join(group2))
            if group3:
                parts.append(" ".join(group3))
            if group4:
                parts.append(" ".join(group4))
            return "Laptop " + " | ".join(parts) if parts else row["name"]
        filtered_data["name"] = filtered_data.apply(build_laptop_name, axis=1)
    
    else:
        available_columns = list(filtered_data.columns)
        selected_columns = st.multiselect(
            "Wybierz kolumny do wyświetlenia i pobrania", 
            options=available_columns, 
            default=available_columns
        )
    
    # Dodanie sufiksu z kolumny "Kondycja" (usuwamy cudzysłowy przed porównaniem)
    def append_kondycja_suffix(row):
        cond = row.get("Kondycja", "").replace('"', '').strip()
        suffix = ""
        if cond == "A- poleasingowy, przetestowany":
            suffix = "[A-]"
        elif cond == "A poleasingowy, przetestowany":
            suffix = "[A]"
        elif cond == "B poleasingowy, przetestowany":
            suffix = "[B]"
        elif cond == "Powystawowy / Leżak magazynowy":
            suffix = "[Powystawowy]"
        return row["name"] + (" " + suffix if suffix else "")
    
    filtered_data["name"] = filtered_data.apply(append_kondycja_suffix, axis=1)
    
    if not selected_columns:
        st.error("Wybierz przynajmniej jedną kolumnę.")
    else:
        filtered_data = filtered_data[selected_columns]
        st.write(f"Liczba pozycji: {len(filtered_data)}")
        st.dataframe(filtered_data, use_container_width=True)
        
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
