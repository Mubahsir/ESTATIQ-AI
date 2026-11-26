"""SQLite persistence for resumable Google Places searches and businesses."""
from __future__ import annotations
import csv, io, json, sqlite3
from pathlib import Path
from datetime import datetime, timezone

def now(): return datetime.now(timezone.utc).isoformat()

class ResearchStore:
    def __init__(self, path):
        self.path = Path(path); self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as c:
            c.executescript('''
            CREATE TABLE IF NOT EXISTS searches(query TEXT PRIMARY KEY, location TEXT NOT NULL, page_token TEXT, status TEXT NOT NULL DEFAULT 'pending', updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS businesses(place_id TEXT PRIMARY KEY, name TEXT, address TEXT, phone TEXT, website TEXT, maps_url TEXT, rating REAL, review_count INTEGER, reviews_json TEXT, categories_json TEXT, latitude REAL, longitude REAL, source TEXT NOT NULL DEFAULT 'Google Places API (New)', collected_at TEXT NOT NULL, query TEXT);
            CREATE INDEX IF NOT EXISTS idx_businesses_query ON businesses(query);
            ''')
    def connect(self): return sqlite3.connect(self.path, timeout=30)
    def ensure_search(self, query, location):
        with self.connect() as c: c.execute("INSERT OR IGNORE INTO searches(query,location,updated_at) VALUES(?,?,?)", (query,location,now()))
    def get_page_token(self, query):
        with self.connect() as c:
            row=c.execute("SELECT page_token FROM searches WHERE query=?",(query,)).fetchone(); return row[0] if row else None
    def is_complete(self, query):
        with self.connect() as c:
            row=c.execute("SELECT status FROM searches WHERE query=?",(query,)).fetchone(); return bool(row and row[0]=='complete')
    def save_page_token(self, query, token):
        with self.connect() as c: c.execute("UPDATE searches SET page_token=?,status=?,updated_at=? WHERE query=?",(token,'in_progress' if token else 'pages_complete',now(),query))
    def finish_search(self, query):
        with self.connect() as c: c.execute("UPDATE searches SET status='complete',page_token=NULL,updated_at=? WHERE query=?",(now(),query))
    def save_places(self, query, places, page):
        stamp=now()
        with self.connect() as c:
            for p in places:
                loc=p.get('location') or {}; dname=p.get('displayName') or {}
                c.execute('''INSERT INTO businesses(place_id,name,address,phone,website,maps_url,rating,review_count,reviews_json,categories_json,latitude,longitude,source,collected_at,query)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(place_id) DO UPDATE SET name=excluded.name,address=excluded.address,phone=COALESCE(excluded.phone,businesses.phone),website=COALESCE(excluded.website,businesses.website),maps_url=COALESCE(excluded.maps_url,businesses.maps_url),rating=COALESCE(excluded.rating,businesses.rating),review_count=COALESCE(excluded.review_count,businesses.review_count),reviews_json=COALESCE(excluded.reviews_json,businesses.reviews_json),categories_json=excluded.categories_json,latitude=excluded.latitude,longitude=excluded.longitude,collected_at=excluded.collected_at,query=excluded.query''', (p.get('id'),dname.get('text'),p.get('formattedAddress'),p.get('nationalPhoneNumber') or p.get('internationalPhoneNumber'),p.get('websiteUri'),p.get('googleMapsUri'),p.get('rating'),p.get('userRatingCount'),json.dumps(p.get('reviews')) if p.get('reviews') else None,json.dumps(p.get('types',[])),loc.get('latitude'),loc.get('longitude'),'Google Places API (New)',stamp,query))
    def businesses(self, location):
        # Keep location scope visible by joining query text; API results are retained by place ID.
        with self.connect() as c:
            rows=c.execute("SELECT name,address,phone,website,maps_url,rating,review_count,categories_json,reviews_json,latitude,longitude,collected_at,query FROM businesses WHERE query LIKE ? ORDER BY rating DESC",(f'%{location}%',)).fetchall()
        cols=['Business','Address','Phone','Website','Google Maps','Rating','Review count','Categories','Google reviews (available subset)','Latitude','Longitude','Collected at (UTC)','Search query']
        return [dict(zip(cols,r)) for r in rows]
    def businesses_csv(self, location):
        rows=self.businesses(location); out=io.StringIO(); w=csv.DictWriter(out,fieldnames=list(rows[0]) if rows else ['Business']); w.writeheader(); w.writerows(rows); return out.getvalue()
