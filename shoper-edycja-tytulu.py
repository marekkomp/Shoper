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
        record = {
            "product_code": offer.get("id"),
            "category": offer.findtext("cat"),
            "Producent": offer.find("attrs/a[@name='Producent']").text if offer.find("attrs/a[@name='Producent']") else None,
            "Kod producenta": offer.find("attrs/a[@name='Kod producenta']").text if offer.find("attrs/a[@name='Kod producenta']") else None,
            "dysk": offer.find("attrs/a[@name='Dysk']").text if offer.find("attrs/a[@name='Dysk']") else None,
            "typ dysku": offer.find("attrs/a[@name='Typ dysku']").text if offer.find("attrs/a[@name='Typ dysku']") else None,
            "pamięć ram": offer.find("attrs/a[@name='Ilość pamięci RAM']").text if offer.find("attrs/a[@name='Ilość pamięci RAM']") else None,
            "Procesor": offer.find("attrs/a[@name='Procesor']").text if offer.find("attrs/a[@name='Procesor']") else None,
            "Rozdzielczość ekranu": offer.find("attrs/a[@name='Rozdzielczość ekranu']").text if offer.find("attrs/a[@name='Rozdzielczość ekranu']") else None,
            "Przekątna ekranu": offer.find("attrs/a[@name='Przekątna ekranu']").text if offer.find("attrs/a[@name='Przekątna ekranu']") else None,
            "Typ matrycy": offer.find("attrs/a[@name='Powłoka matrycy']").text if offer.find("attrs/a[@name='Powłoka matrycy']") else None,
        }
        data.append(record)
    return pd.DataFrame(data)

# Przetwórz jedną wartość product_code
def process_single_product(xml_df, excel_df, single_code):
    # Upewnij się, że kolumna product_code ma ten sam typ danych i usuń `.0`
    xml_df["product_code"] = xml_df["product_code"].astype(str)
    excel_df["product_code"] = excel_df["product_code"].astype(str).str.replace("\.0$", "", regex=True)

    # Filtruj dane dla jednego product_code
    filtered_excel = excel_df[excel_df["product_code"] == single_code]
    filtered_xml = xml_df[xml_df["product_code"] == single_code]

    # Debug: Wyświetl dane filtrowane
    st.write("Dane Excel dla product_code:")
    st.dataframe(filtered_excel)
    st.write("Dane XML dla product_code:")
    st.dataframe(filtered_xml)

    # Sprawdź, czy dane istnieją w obu źródłach
    if filtered_excel.empty:
        st.warning(f"Brak danych w Excel dla product_code: {single_code}")
        return excel_df

    if filtered_xml.empty:
        st.warning(f"Brak danych w XML dla product_code: {single_code}")
        return excel_df

    # Połącz dane i wygeneruj name
    merged_df = filtered_excel.merge(filtered_xml, on="product_code", how="left")

    def generate_name(row):
        columns = [
            "category", "Producent", "Kod producenta", "dysk", "typ dysku", 
            "pamięć ram", "Procesor", "Rozdzielczość ekranu", "Przekątna ekranu", "Typ matrycy"
        ]
        components = [row[col] for col in columns if col in row.index and pd.notnull(row[col])]
        return " ".join([str(c) for c in components if c])

    # Aktualizuj kolumnę name tylko dla jednej wartości
    filtered_excel["name"] = merged_df.apply(generate_name, axis=1)

    # Debug: Wyświetl wynik generowania name
    st.write("Wynik generowania kolumny 'name':")
    st.dataframe(filtered_excel[["product_code", "name"]])

    # Zaktualizuj oryginalny DataFrame
    excel_df.update(filtered_excel)

    return excel_df

# Streamlit aplikacja
st.title("Testowanie pojedynczego product_code")

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

        # Testuj dla jednej wartości product_code
        single_code = st.text_input("Podaj product_code do przetestowania", "229381687")
        updated_df = process_single_product(xml_df, excel_df, single_code)

        # Wyświetl zmienioną tabelę
        st.write("Podgląd zmienionej tabeli dla pojedynczego product_code:")
        st.dataframe(updated_df)

        # Przygotuj plik do pobrania
        output = BytesIO()
        updated_df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)

        st.success("Plik został zaktualizowany!")
        st.download_button(
            label="Pobierz zaktualizowany plik Excel",
            data=output,
            file_name="updated_single_excel.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
