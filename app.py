"""Google Places-only real estate business discovery and evidence-limited research."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from realestate.db import ResearchStore
from realestate.places import GooglePlacesClient, PlaceAPIError
from realestate.report import build_report
from realestate.requirements import PROPERTY_TYPES, TRANSACTIONS, fields_for

load_dotenv()
st.set_page_config(page_title="Property Research", page_icon="🏠", layout="wide")
st.title("Real Estate Research & Valuation")
st.caption("Google Places business discovery. Google Places does not provide property listings or sale prices; unavailable price evidence is shown as unavailable.")

with st.sidebar:
    st.header("Google API configuration")
    key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    st.write("API key: configured" if key else "API key: missing")
    st.caption("Enable Places API (New) for the Google Cloud project linked to this key. Google billing and quotas may apply.")

st.subheader("1 · Location")
c1, c2, c3 = st.columns(3)
with c1:
    country = st.text_input("Country", placeholder="e.g. Pakistan")
with c2:
    city = st.text_input("City", placeholder="e.g. Lahore")
with c3:
    area = st.text_input("Area / neighborhood", placeholder="e.g. DHA Phase 6")

st.subheader("2 · Property and intent")
c1, c2 = st.columns(2)
with c1:
    property_type = st.selectbox("Property type", PROPERTY_TYPES)
with c2:
    transaction = st.selectbox("Purpose", TRANSACTIONS)
specs = {}
cols = st.columns(3)
for i, (name, kind) in enumerate(fields_for(property_type)):
    with cols[i % len(cols)]:
        if kind == "bool":
            specs[name] = st.selectbox(name, ["Not specified", "Yes", "No"], key=f"spec_{name}")
        elif kind == "number":
            specs[name] = st.number_input(name, min_value=0.0, value=0.0, key=f"spec_{name}")
        else:
            specs[name] = st.text_input(name, key=f"spec_{name}")

area_size = st.number_input("Property size (optional)", min_value=0.0, value=0.0)
measurement = st.selectbox("Measurement unit", ["Not specified", "Square feet", "Square yards", "Square meters", "Acres", "Hectares", "Marla (regional convention required)", "Kanal (regional convention required)"])
st.caption("Measurements are kept as entered. No Marla/Kanal conversion is applied without a user-selected regional convention.")

location = ", ".join(x.strip() for x in (area, city, country) if x.strip())
store_path = os.getenv("DATABASE_PATH", "data/research.sqlite3")
store = ResearchStore(store_path)

if st.button("Find real estate businesses on Google", type="primary", disabled=not bool(location)):
    if not key:
        st.error("Set GOOGLE_MAPS_API_KEY in your .env file, then restart the app.")
    else:
        client = GooglePlacesClient(key)
        terms = ["real estate agent", "property dealer", "real estate agency", "property consultant", "property management company", "real estate developer", "builder"]
        progress = st.progress(0, text="Starting resumable Google Places searches…")
        status = st.empty()
        try:
            for i, term in enumerate(terms):
                query = f"{term} in {location}"
                status.write(f"Searching Google Places: {query}")
                store.ensure_search(query, location)
                if store.is_complete(query):
                    progress.progress((i + 1) / len(terms), text=f"Reusing saved results ({i + 1} of {len(terms)} queries)")
                    continue
                saved_token = store.get_page_token(query)
                for page, places, next_token in client.search_pages(query, first_page_token=saved_token):
                    store.save_places(query, places, page)
                    store.save_page_token(query, next_token)
                    if not next_token:
                        break
                store.finish_search(query)
                progress.progress((i + 1) / len(terms), text=f"Completed {i + 1} of {len(terms)} query variations")
            st.success("Google Places discovery completed. Results are stored in SQLite and can be reused.")
        except PlaceAPIError as exc:
            st.error(str(exc))
            st.info("Completed pages and query state are saved. Retry to resume where possible.")

st.subheader("3 · Research results")
businesses = store.businesses(location)
if businesses:
    st.dataframe(businesses, use_container_width=True, hide_index=True)
    st.download_button("Download business results (CSV)", store.businesses_csv(location), "google_places_businesses.csv", "text/csv")
else:
    st.info("No saved Google Places businesses match this location yet.")

requirements = {"country": country, "city": city, "area": area, "property_type": property_type, "transaction": transaction, "specifications": specs, "size": area_size or None, "measurement": measurement}
report = build_report(requirements, businesses)
st.subheader("4 · Evidence-limited valuation report")
st.markdown(report)
st.download_button("Download report (Markdown)", report, "property_research_report.md", "text/markdown")
