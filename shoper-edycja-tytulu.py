import pandas as pd
import streamlit as st
import requests
import xml.etree.ElementTree as ET
from io import BytesIO

# URL XML
XML_URL = "https://firebasestorage.googleapis.com/v0/b/kompreshop.appspot.com/o/xml%2Fkompre.xml?alt=media"

# Pobierz dane XML
def fetch_xml_data(url):
    response = requests.get(url)
    response.raise_for_status()
    return ET.fromstring(response.content)

# Przetwórz XML na DataFrame
def parse_xml_to_df(xml_root):
    data = []
    for offer in xml_root.findall(".//o"):
        attrs = {a.get("name"): a.text.strip() for a in offer.findall("attrs/a")}
        record = {
            "product_code": offer.get("id"),
            "category": offer.findtext("cat").strip() if offer.findtext("cat") else None,  # Pobranie kategorii
            "Producent": attrs.get("Producent"),
            "Kod producenta": attrs.get("Kod producenta"),
            "dysk": attrs.get("Dysk"),
            "typ dysku": attrs.get("Typ dysku"),
            "pamięć ram": attrs.get("Ilość pamięci RAM"),
            "Procesor": attrs.get("Procesor"),
            "Rozdzielczość ekranu": attrs.get("Rozdzielczość ekranu"),
            "Przekątna ekranu": attrs.get("Przekątna ekranu"),
            "Typ matrycy": attrs.get("Typ matrycy"),
        }
        data.append(record)
    return pd.DataFrame(data)

# Przetwórz dane z XML i Excel
def process_data(xml_df, excel_df):
    # Dopasowanie typów danych i usunięcie `.0`
    xml_df["product_code"] = xml_df["product_code"].astype(str)
    excel_df["product_code"] = excel_df["product_code"].astype(str).str.replace("\.0$", "", regex=True)

    # Połączenie danych
    merged_df = excel_df.merge(xml_df, on="product_code", how="left")

    # Skrócenie kolumny Procesor do 10 pierwszych liter
    merged_df["Procesor"] = merged_df["Procesor"].apply(lambda x: x[:10] if isinstance(x, str) else x)

    # Generowanie kolumny name
    def generate_name(row):
        columns = [
            "category",  # Kategoria jako pierwszy element
            "Producent", 
            "Kod producenta", 
            "Procesor", 
            "pamięć ram", 
            "dysk", 
            "typ dysku", 
            "Rozdzielczość ekranu", 
            "Przekątna ekranu", 
            "Typ matrycy"
        ]
        components = [str(row[col]).strip() for col in columns if col in row.index and pd.notnull(row[col])]
        return " ".join(components).replace("\n", " ").replace("\r", " ")

    merged_df["name"] = merged_df.apply(generate_name, axis=1)

    # Zaktualizuj kolumnę name w oryginalnym DataFrame
    excel_df["name"] = merged_df["name"]
    return excel_df

# Streamlit aplikacja
st.title("XML + Excel Merger")

# Wybierz plik Excel
uploaded_file = st.file_uploader("Wgraj plik Excel", type=["xlsx"])
if uploaded_file:
    excel_df = pd.read_excel(uploaded_file)

    # Sprawdź, czy plik zawiera kolumnę product_code
    if "product_code" not in excel_df.columns:
        st.error("Plik Excel musi zawierać kolumnę 'product_code'.")
    else:
        # Pobierz i przetwórz dane XML
        st.info("Pobieranie danych z XML...")
        xml_root = fetch_xml_data(XML_URL)
        xml_df = parse_xml_to_df(xml_root)

        # Przetwórz dane
        st.info("Przetwarzanie danych...")
        updated_df = process_data(xml_df, excel_df)

        # Wyświetl zmienioną tabelę
        st.write("Podgląd zmienionej tabeli:")
        st.dataframe(updated_df)

        # Przygotuj plik do pobrania
        output = BytesIO()
        updated_df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)

        st.success("Plik został zaktualizowany!")
        st.download_button(
            label="Pobierz zaktualizowany plik Excel",
            data=output,
            file_name="updated_excel.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
