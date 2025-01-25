import streamlit as st
import pandas as pd
from io import BytesIO

# Funkcja do modyfikacji kolumny name i zamiany kategorii
def update_name_and_category(df):
    if 'name' in df.columns and 'category' in df.columns:
        # Mapowanie kategorii do zamiany
        category_replacements = {
            'Laptopy': 'Laptop',
            'Monitory': 'Monitor',
            'Komputery': 'Komputer',
            'Telefony': 'Telefon',
            'Tablety': 'Tablet'
        }

        # Zamiana wartości w kolumnie category
        df['category'] = df['category'].replace(category_replacements)

        # Aktualizacja kolumny name
        df['name'] = df['category'] + ' ' + df['name']
    else:
        st.error("Kolumny 'name' lub 'category' nie znaleziono w pliku.")
    return df

# Streamlit app
st.title("Aktualizacja kolumny 'name' na podstawie 'category'")
st.write("Wgraj plik Excel, aby dodać wartości z kolumny 'category' na początek kolumny 'name'.")

# Upload file
uploaded_file = st.file_uploader("Wgraj plik Excel", type=['xlsx', 'xlsm'])
if uploaded_file:
    try:
        # Wczytanie pliku Excel
        df = pd.read_excel(uploaded_file)

        # Wyświetlenie oryginalnych danych
        st.subheader("Oryginalne dane")
        st.write(df)

        # Modyfikacja danych
        updated_df = update_name_and_category(df)

        # Wyświetlenie zmodyfikowanych danych
        st.subheader("Zmodyfikowane dane")
        st.write(updated_df)

        # Pobranie zmodyfikowanego pliku
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            updated_df.to_excel(writer, index=False, sheet_name='Sheet1')
        processed_file = output.getvalue()

        st.download_button(
            label="Pobierz zmodyfikowany plik Excel",
            data=processed_file,
            file_name="updated_file.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Wystąpił błąd podczas przetwarzania pliku: {e}")
