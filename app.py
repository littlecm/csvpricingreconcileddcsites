import streamlit as st
import requests
import pandas as pd
from io import StringIO

# Function to download CSV content from a given URL
def download_csv(url):
    response = requests.get(url)
    if response.ok:
        return response.content
    else:
        return None

# Function to read CSV from content with specified encoding, handling UnicodeDecodeError
def read_csv_with_encoding(content, encoding='utf-8'):
    try:
        return pd.read_csv(StringIO(content.decode(encoding)))
    except UnicodeDecodeError:
        return pd.read_csv(StringIO(content.decode('ISO-8859-1')))

# Function to reconcile prices between Vinsolutions data and Dealerdotcom data
def reconcile_prices(vinsolutions_data, dealerdotcom_data, dealer_id, vinsolutions_type_field, vinsolutions_new_price_field, vinsolutions_used_price_field, dealerdotcom_new_price_field, dealerdotcom_used_price_field):
    price_discrepancies = []
    
    # Filter the Dealerdotcom data by dealer_id
    filtered_dealerdotcom_data = dealerdotcom_data[dealerdotcom_data['dealer_id'] == dealer_id]

    for index, row in vinsolutions_data.iterrows():
        vin = row['VIN']
        vehicle_type = row[vinsolutions_type_field].strip()  # Ensure vehicle type is stripped of leading/trailing spaces
        vinsolutions_price = row[vinsolutions_new_price_field] if vehicle_type == 'New' else row[vinsolutions_used_price_field]

        # Use 'vin' instead of 'VIN' to match the column name in dealerdotcom_data
        dealerdotcom_vehicle = filtered_dealerdotcom_data[filtered_dealerdotcom_data['vin'] == vin]
        
        if not dealerdotcom_vehicle.empty:
            dealerdotcom_price = dealerdotcom_vehicle.iloc[0][dealerdotcom_new_price_field] if vehicle_type == 'New' else dealerdotcom_vehicle.iloc[0][dealerdotcom_used_price_field]

            if vinsolutions_price != dealerdotcom_price:
                price_discrepancies.append({
                    'VIN': vin,
                    'Vehicle Type': vehicle_type,
                    'Vinsolutions Price': vinsolutions_price,
                    'Dealerdotcom Price': dealerdotcom_price,
                    'Discrepancy': abs(vinsolutions_price - dealerdotcom_price)
                })

    return pd.DataFrame(price_discrepancies)


# Streamlit UI setup
st.title("Vehicle Pricing Reconciliation")

# Download Dealerdotcom data and prepare dealer_id dropdown
dealerdotcom_csv_url = "https://feeds.amp.auto/feeds/coxautomotive/dealerdotcom.csv"
dealerdotcom_content = download_csv(dealerdotcom_csv_url)
if dealerdotcom_content:
    dealerdotcom_data = read_csv_with_encoding(dealerdotcom_content)
    dealer_ids = dealerdotcom_data['dealer_id'].unique().tolist()
else:
    st.error("Failed to download Dealerdotcom data.")
    dealer_ids = []

# User inputs
vinsolutions_url = st.text_input("Vinsolutions Feed URL")
selected_dealer_id = st.selectbox("Select Dealer ID", dealer_ids)

vinsolutions_type_field = st.text_input("Vinsolutions Type Field Label", value="Type")
vinsolutions_new_price_field = st.text_input("Vinsolutions New Vehicle Price Field", value="BookValue")
vinsolutions_used_price_field = st.text_input("Vinsolutions Used Vehicle Price Field", value="SellingPrice")

dealerdotcom_new_price_field = st.text_input("Dealerdotcom New Vehicle Price Field", value="RetailValue")
dealerdotcom_used_price_field = st.text_input("Dealerdotcom Used Vehicle Price Field", value="InternetPrice")

# Reconcile prices on button click
if st.button("Reconcile Prices"):
    if vinsolutions_url and selected_dealer_id:
        vinsolutions_content = download_csv(vinsolutions_url)
        
        if vinsolutions_content:
            vinsolutions_data = read_csv_with_encoding(vinsolutions_content)
            discrepancies_df = reconcile_prices(vinsolutions_data, dealerdotcom_data, selected_dealer_id, vinsolutions_type_field, vinsolutions_new_price_field, vinsolutions_used_price_field, dealerdotcom_new_price_field, dealerdotcom_used_price_field)
            st.write(discrepancies_df)
        else:
            st.error("Failed to download Vinsolutions data.")
    else:
        st.error("Please fill in all input fields.")
