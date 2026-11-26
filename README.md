# Real Estate Research & Valuation
A comprehensive, data-driven Real Estate Research and Valuation platform designed to simplify property market research, real estate business discovery, location-based analysis, and structured data management. The system integrates Google Places API (New) to identify and collect relevant real estate business information, including property agents, dealers, agencies, consultants, developers, builders, and property management services across selected countries, cities, and geographical areas.

## Scope and data integrity

- The app searches Google Places for agents, dealers, agencies, consultants, property managers, developers, and builders in an entered country/city/area.
- It collects fields made available by Places: name, address, phone, website, Maps URI, rating, review count, a returned subset of reviews, categories, coordinates, place ID, and collection timestamp.
- Google Places is not treated as a property listings or transaction database. Asking prices, verified transactions, rental amounts, price trends, and market value are reported as unavailable unless an allowed Google API/source actually returns such evidence. This implementation does not calculate a price from business records.
- No Zillow, Zameen, Graana, Bayut, Property Finder, web search provider, or other third-party data API is integrated.
- Search progress and business rows are stored in SQLite. Rows are deduplicated by Google place ID; query/page state allows pagination to resume after interruption. Completed query results are reused on later runs.
- Google Maps Platform policies, attribution rules, and retention limits apply to Places content. Check the terms for your billing region before production use; the database is local and should be managed in accordance with those terms. API responses can be refreshed by clearing the local SQLite database if necessary.

## Setup

1. Use Python 3.10 or newer.
2. Create and activate a virtual environment.
3. Install: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and set `GOOGLE_MAPS_API_KEY` to your key. Enable Places API (New) in the Google Cloud project that owns that key. Do not commit `.env`.
5. Run: `streamlit run app.py`

Google Maps Platform applies quotas and may charge based on requested API fields/SKUs and account terms. Request only fields needed by the app; ratings, website, and reviews are higher-tier fields. A working key and API configuration are required for live searches.

## Search and persistence

Each submitted location triggers multiple Google Text Search query variations. The client follows every `nextPageToken` returned by Google, enriches returned place IDs with Place Details, retries transient failures with exponential backoff, and saves page progress. Google controls which results and pages are available; the tool does not claim internet-wide exhaustiveness. SQLite defaults to `data/research.sqlite3`, configurable with `DATABASE_PATH`.

## Valuation and model status

There was no source project, dataset, or trained model in the workspace. No synthetic training data or substitute model is created. Because this allowed data source does not supply comparable property prices, the report refuses to invent a value or present dealer discovery as valuation evidence. A valuation workflow needs a permitted Google data source that actually provides listing or transaction prices; otherwise price outputs remain unavailable.

## Data contents

`searches` stores query, location, continuation token, status, and update time. `businesses` stores one row per Google place ID plus available details, original query, source label, and collection timestamp. CSV and Markdown exports are available in the app.
