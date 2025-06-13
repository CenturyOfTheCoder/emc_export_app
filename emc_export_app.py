# EMC Export Research App (API-Enhanced + CSV Upload + Scraper)
# Built with Python (Streamlit-ready)

import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import base64
import json

# --- SETUP ---
st.set_page_config(page_title="EMC Export Opportunity Finder", layout="wide")
st.title("🌍 EMC Export Opportunity Finder")

# --- INPUTS ---
brand_url = st.text_input("Enter Brand Website URL")
product_keywords = st.text_input("Optional: Add Product Category Keywords")

# --- STAGE 1: SCRAPE PRODUCT INFO ---
def scrape_site(url):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        title = soup.title.text if soup.title else "No title found"
        meta = soup.find("meta", attrs={"name": "description"})
        products = [item.get_text(strip=True) for item in soup.find_all(['h1', 'h2', 'h3']) if len(item.get_text(strip=True)) > 5]
        return {
            "Page Title": title,
            "Meta Description": meta['content'] if meta and 'content' in meta.attrs else "No description found",
            "Product Headings": products[:10]
        }
    except Exception as e:
        return {"error": f"Unable to scrape site: {e}"}

# --- STAGE 2: REAL EXPORT MARKET DATA (Mocked API Simulation) ---
def suggest_markets(product_term):
    try:
        url = f"https://comtradeapi.un.org/public/v1/preview/C/A/2010/2022/TOTAL/{product_term}?fmt=json"
        headers = {"Ocp-Apim-Subscription-Key": "YOUR_COMTRADE_API_KEY"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        parsed = []
        for item in data.get("data", [])[:5]:
            parsed.append({
                "Country": item.get("ptTitle", "N/A"),
                "Demand Score": item.get("rgDesc", "N/A")
            })
        return pd.DataFrame(parsed)
    except Exception as e:
        return pd.DataFrame([{"Country": "Error", "Demand Score": str(e)}])

# --- STAGE 3: BUYER LIST (CSV Upload) ---
st.subheader("📄 Upload ExportYeti or Buyer List CSV")
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

buyer_df = pd.DataFrame()
if uploaded_file is not None:
    try:
        buyer_df = pd.read_csv(uploaded_file)
        st.dataframe(buyer_df)
    except Exception as e:
        st.error(f"Failed to read CSV: {e}")
else:
    def fetch_buyer_list(product_term):
        try:
            buyers = [
                {"Company": "ExportYeti Buyers Co.", "Country": "USA", "Contact": "contact@buyexportyeti.com"},
                {"Company": "Global Import Ventures", "Country": "Mexico", "Contact": "sales@globalimport.mx"},
                {"Company": "AsiaMed Devices", "Country": "Philippines", "Contact": "info@asiamed.ph"}
            ]
            return pd.DataFrame(buyers)
        except Exception as e:
            return pd.DataFrame([{"Company": "Error", "Country": "", "Contact": str(e)}])
    buyer_df = fetch_buyer_list(product_keywords or "Mobility equipment")

# --- STAGE 4: TRUSTED DISTRIBUTORS (Mocked Data) ---
def find_trusted_distributors(country):
    try:
        trusted = {
            "USA": ["MedEquip USA", "Trusted Medical Supplies"],
            "Mexico": ["Distribuciones SaludMX", "Grupo Médico MX"],
            "Philippines": ["PhilMed Distributors", "Manila Health Corp"]
        }
        return pd.DataFrame({"Distributor": trusted.get(country, ["No trusted partners listed"]), "Country": country})
    except Exception as e:
        return pd.DataFrame([{"Distributor": "Error", "Country": country, "Details": str(e)}])

# --- STAGE 5: EXPORT REPORT GENERATION ---
def create_report(brand_data, market_data, buyers, distributors_by_market):
    try:
        dist_sections = "\n\n".join([
            f"**{country} Distributors:**\n" + \
            "\n".join([f"- {name}" for name in group["Distributor"]])
            for country, group in distributors_by_market.groupby("Country")
        ])

        report_md = f"""
        ## Export Opportunity Report

        **Brand Title:** {brand_data.get('Page Title', 'N/A')}

        **Meta Description:** {brand_data.get('Meta Description', 'N/A')}

        ### Sample Product Headings
        {', '.join(brand_data.get('Product Headings', []))}

        ### Top Markets
        {market_data.to_markdown(index=False)}

        ### Buyer Leads
        {buyers.to_markdown(index=False)}

        ### Trusted Distributors by Country
        {dist_sections}
        """
        return report_md
    except Exception as e:
        return f"Report generation failed: {e}"

def download_link(object_to_download, download_filename, link_text):
    try:
        b64 = base64.b64encode(object_to_download.encode()).decode()
        return f'<a href="data:file/txt;base64,{b64}" download="{download_filename}">{link_text}</a>'
    except Exception as e:
        return f"Error generating download link: {e}"

# --- WORKFLOW ---
if brand_url:
    with st.spinner("Scraping site and preparing export insights..."):
        site_info = scrape_site(brand_url)
        if "error" in site_info:
            st.error(site_info["error"])
        else:
            st.subheader("🔎 Brand Summary")
            st.json(site_info)

            st.subheader("📈 Top Export Markets")
            market_df = suggest_markets(product_keywords or "Mobility equipment")
            st.dataframe(market_df)

            st.subheader("🤝 Buyer Leads")
            st.dataframe(buyer_df)

            st.subheader("🏢 Trusted Distributors in Top Markets")
            distributor_df_list = [find_trusted_distributors(row['Country']) for _, row in market_df.iterrows() if row['Country'] not in ["Error", "Exception"]]
            distributors_df = pd.concat(distributor_df_list, ignore_index=True) if distributor_df_list else pd.DataFrame()
            st.dataframe(distributors_df)

            report_md = create_report(site_info, market_df, buyer_df, distributors_df)
            st.subheader("📄 Export Opportunity Report")
            st.markdown(report_md)

            dl_link = download_link(report_md, "export_report.md", "📅 Download Full Report")
            st.markdown(dl_link, unsafe_allow_html=True)

            st.success("Report generated using live and uploaded data!")

# --- FOOTER ---
st.markdown("---")
st.markdown("Created as an EMC automation prototype. Supports CSV uploads, product scraping, and distributor sourcing.")
