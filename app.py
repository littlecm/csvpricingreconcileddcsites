import streamlit as st
import requests
import pandas as pd
from io import StringIO

def download_csv(url):
    response = requests.get(url)
    if response.ok:
        return response.content
    else:
        return None

def read_csv_with_encoding(content, encoding='utf-8'):
    try:
        return pd.read_csv(StringIO(content.decode(encoding)))
    except UnicodeDecodeError:
        return pd.read_csv(StringIO(content.decode('ISO-8859-1')))

def reconcile_prices(vinsolutions_data, dealerdotcom_data, dealer_id, vinsolutions_type_field, vinsolutions_new_price_field, vinsolutions_used_price_field, dealerdotcom_new_price_field, dealerdotcom_used_price_field):
    price_discrepancies = []
    
    # Filter the dealerdotcom_data by dealer_id
    filtered_dealerdotcom_data = dealerdotcom_data[dealerdotcom_data['dealer_id'] == dealer_id]

    for index, row in vinsolutions_data.iterrows():
        vin = row['VIN']
        vehicle_type = row[vinsolutions_type_field].strip()  # Ensure vehicle type is stripped of leading/trailing spaces
        vinsolutions_price = row[vinsolutions_new_price_field] if vehicle_type == 'New' else row[vinsolutions_used_price_field]

        dealerdotcom_vehicle = filtered_dealerdotcom_data[filtered_dealerdotcom_data['VIN'] == vin]
        
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

# Streamlit UI
st.title("Vehicle Pricing Reconciliation")

vinsolutions_url = st.text_input("Vinsolutions Feed URL")
dealer_id = st.text_input("Dealerdotcom Dealer ID")

# Predefined Dealerdotcom CSV Feed URL
dealerdotcom_csv_url = "https://feeds.amp.auto/feeds/coxautomotive/dealerdotcom.csv"

vinsolutions_type_field = st.text_input("Vinsolutions Type Field Label", value="Type")

vinsolutions_new_price_field = st.text_input("Vinsolutions New Vehicle Price Field", value="BookValue")
vinsolutions_used_price_field = st.text_input("Vinsolutions Used Vehicle Price Field", value="SellingPrice")

dealerdotcom_new_price_field = st.text_input("Dealerdotcom New Vehicle Price Field", value="RetailValue")
dealerdotcom_used_price_field = st.text_input("Dealerdotcom Used Vehicle Price Field", value="InternetPrice")

if st.button("Reconcile Prices"):
    if vinsolutions_url and dealer_id:
        vinsolutions_content = download_csv(vinsolutions_url)
        dealerdotcom_content = download_csv(dealerdotcom_csv_url)
        
        if vinsolutions_content and dealerdotcom_content:
            vinsolutions_data = read_csv_with_encoding(vinsolutions_content)
            dealerdotcom_data = read_csv_with_encoding(dealerdotcom_content)
            
            discrepancies_df = reconcile_prices(vinsolutions_data, dealerdotcom_data, dealer_id, vinsolutions_type_field, vinsolutions_new_price_field, vinsolutions_used_price_field, dealerdotcom_new_price_field, dealerdotcom_used_price_field)
            st.write(discrepancies_df)
        else:
            st.error("Failed to download one or both CSV files.")
    else:
        st.error("Please fill in all input fields.")
