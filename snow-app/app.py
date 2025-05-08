import streamlit as st
import pandas as pd
import requests

# Load secret token
NOAA_TOKEN = st.secrets[KCXhuxVVfqigkxFLpsKoNrknfxnmwtrJ]
STATION_ID = "GHCND:USC00106048"  # Ketchum, Idaho station

st.set_page_config(page_title="Snowfall vs Snow Removal Costs", page_icon="❄️")
st.title("❄️ Snowfall vs Snow Removal Cost Tracker")

@st.cache_data(show_spinner=False)
def get_snow_data(start_date, end_date):
    headers = {"token": NOAA_TOKEN}
    params = {
        "datasetid": "GHCND",
        "datatypeid": "SNOW",
        "stationid": STATION_ID,
        "startdate": start_date,
        "enddate": end_date,
        "units": "standard",
        "limit": 1000
    }
    response = requests.get("https://www.ncei.noaa.gov/cdo-web/api/v2/data", headers=headers, params=params)
    if response.status_code != 200:
        st.error(f"Error fetching data from NOAA: {response.text}")
        return pd.DataFrame()
    data = response.json().get("results", [])
    df = pd.DataFrame(data)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df["snow_inches"] = df["value"]
        return df[["date", "snow_inches"]]
    return pd.DataFrame()

st.subheader("Select Date Range")
col1, col2 = st.columns(2)
with col1:
    start = st.date_input("Start Date")
with col2:
    end = st.date_input("End Date")

invoice_file = st.file_uploader("Upload Snow Removal Invoice (CSV)", type=["csv"])

if invoice_file and start and end:
    invoices = pd.read_csv(invoice_file)
    
    # Expecting columns: date, cost
    try:
        invoices['date'] = pd.to_datetime(invoices['date'])
        invoices['cost'] = invoices['cost'].astype(float)
    except Exception as e:
        st.error(f"Error processing CSV: {e}")
        st.stop()

    snow_data = get_snow_data(str(start), str(end))

    if snow_data.empty:
        st.warning("No snowfall data found for the selected date range.")
    else:
        combined = pd.merge(invoices, snow_data, on="date", how="left")
        combined["snow_inches"].fillna(0, inplace=True)

        st.subheader("📊 Invoice vs Snowfall Comparison")
        st.dataframe(combined)

        st.subheader("🚩 High-Cost, Low-Snow Days (Potential Anomalies)")
        mean_cost = combined["cost"].mean()
        anomalies = combined[(combined["snow_inches"] < 1) & (combined["cost"] > mean_cost)]
        st.dataframe(anomalies)

        st.download_button("Download Comparison CSV", data=combined.to_csv(index=False), file_name="snow_comparison.csv")

else:
    st.info("Upload an invoice CSV with at least two columns: `date` and `cost`.")
