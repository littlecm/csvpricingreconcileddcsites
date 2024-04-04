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

def reconcile_prices(vinsolutions_data, other_data, dealer_id, vinsolutions_type_field, other_type_field, other_new_value, other_used_value, vinsolutions_new_price_field, vinsolutions_used_price_field, other_new_price_field, other_used_price_field):
    price_discrepancies = []
    
    filtered_other_data = other_data[other_data['dealer_id'] == dealer_id]

    for index, row in vinsolutions_data.iterrows():
        vin = row['VIN']
        vehicle_type = row[vinsolutions_type_field].strip()
        vinsolutions_price = row[vinsolutions_new_price_field] if vehicle_type == 'New' else row[vinsolutions_used_price_field]

        other_vehicle = filtered_other_data[filtered_other_data['vin'] == vin]
        
        if not other_vehicle.empty:
            other_vehicle_type = other_vehicle.iloc[0][other_type_field].strip()
            # Map the custom 'New' and 'Used' values to the standard 'New' and 'Used' labels
            standardized_other_type = 'New' if other_vehicle_type == other_new_value else 'Used'
            other_price = other_vehicle.iloc[0][other_new_price_field] if standardized_other_type == 'New' else other_vehicle.iloc[0][other_used_price_field]

            if vinsolutions_price != other_price:
                price_discrepancies.append({
                    'VIN': vin,
                    'Vehicle Type': vehicle_type,
                    'Vinsolutions Price': vinsolutions_price,
                    'Other Price': other_price,
                    'Discrepancy': abs(vinsolutions_price - other_price)
                })

    return pd.DataFrame(price_discrepancies)

# Streamlit UI
st.title("Vehicle Pricing Reconciliation")

vinsolutions_url = st.text_input("Vinsolutions Feed URL")
other_csv_url = st.text_input("Other CSV Feed URL")
dealer_id = st.text_input("Dealer ID")

vinsolutions_type_field = st.text_input("Vinsolutions Type Field Label", value="Type")
other_type_field = st.text_input("Other CSV Type Field Label", value="Type")

# Inputs for custom 'New' and 'Used' values in the 'Other CSV'
other_new_value = st.text_input("Other CSV 'New' Vehicle Type Value", value="New")
other_used_value = st.text_input("Other CSV 'Used' Vehicle Type Value", value="Pre-Owned")

vinsolutions_new_price_field = st.text_input("Vinsolutions New Vehicle Price Field", value="BookValue")
vinsolutions_used_price_field = st.text_input("Vinsolutions Used Vehicle Price Field", value="SellingPrice")

other_new_price_field = st.text_input("Other CSV New Vehicle Price Field", value="RetailValue")
other_used_price_field = st.text_input("Other CSV Used Vehicle Price Field", value="InternetPrice")

if st.button("Reconcile Prices"):
    if vinsolutions_url and other_csv_url and dealer_id:
        vinsolutions_content = download_csv(vinsolutions_url)
        other_content = download_csv(other_csv_url)
        
        if vinsolutions_content and other_content:
            vinsolutions_data = read_csv_with_encoding(vinsolutions_content)
            other_data = read_csv_with_encoding(other_content)
            
            discrepancies_df = reconcile_prices(vinsolutions_data, other_data, dealer_id, vinsolutions_type_field, other_type_field, other_new_value, other_used_value, vinsolutions_new_price_field, vinsolutions_used_price_field, other_new_price_field, other_used_price_field)
            st.write(discrepancies_df)
        else:
            st.error("Failed to download one or both CSV files.")
    else:
        st.error("Please fill in all input fields.")
