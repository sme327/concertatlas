
from pathlib import Path
import sqlite3
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'; db=DATA/'concerts.sqlite'
cache=pd.read_csv(DATA/'geocoded_locations.csv')
over=DATA/'geocode_manual_overrides.csv'
if over.exists() and over.stat().st_size: 
    manual=pd.read_csv(over)
    if len(manual):
        manual['location_type']=manual['location_type'].astype(str)
        manual['geocode_status']='manual'; manual['source']='manual override'; manual['canonical_name']=manual['venue'].fillna(manual['city']); manual['review_note']=manual.get('note','')
        cache=pd.concat([cache,manual[cache.columns]],ignore_index=True)
conn=sqlite3.connect(db)
for _,r in cache.dropna(subset=['latitude','longitude']).iterrows():
    if r.location_type=='city':
        conn.execute('UPDATE cities SET latitude=?,longitude=?,geocode_status=? WHERE city=? AND state_region=?',(r.latitude,r.longitude,r.geocode_status,r.city,r.state_region))
    else:
        conn.execute("UPDATE venues SET latitude=?,longitude=?,geocode_status=? WHERE venue_name_recorded=? AND city_id IN (SELECT city_id FROM cities WHERE city=? AND state_region=?)",(r.latitude,r.longitude,r.geocode_status,r.venue,r.city,r.state_region))
conn.commit(); conn.close(); print('Applied coordinate cache to SQLite.')
