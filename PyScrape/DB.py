import psycopg2
import csv

conn = psycopg2.connect("host=localhost password=2539 dbname=EbayListingData user=postgres")
cur = conn.cursor()

cur.execute("""
CREATE TABLE results(
title text PRIMARY KEY,
closing text,
seconds integer,
condition text,
price float,
link text
 )
""")
conn.commit()
