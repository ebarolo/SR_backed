from DB.rag_system import *
import os
import json

from utility import logger

"""frasi = []
for i in range(100):
    with open(f"data/email_{i}.json", encoding="utf-8") as jsonf:
        frasi.append(json.loads(jsonf.read())['body'])

index_database(frasi)"""

# index_database(frasi)
matrix = load_embedding_matrix("embeddings.npy") 

def read_recipes(shortcode):
    with open(f"static/mediaRicette/{shortcode}/{shortcode}.json", encoding="utf-8") as jsonf:
     return json.dumps(json.loads(jsonf.read()))

def cerca_recipes(query):
    out = search(query, matrix)[:3]
    logger.info(f"cerca_recipes output: {out}")

    # Questa riga restituisce una lista dei contenuti delle ricette corrispondenti ai primi 3 risultati della ricerca.
    # 'out' è una lista di tuple (indice, similarità), quindi x[0] prende l'indice delle ricette.
    # Per ogni indice, la funzione read_recipe legge il file JSON corrispondente e ne restituisce il contenuto come stringa JSON.
    return list(map(lambda x: read_recipes(x[0]), out))

"""out = cerca_mail("preventivo")
print(out)"""
    