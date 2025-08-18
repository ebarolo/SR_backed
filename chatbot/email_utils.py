from DB.rag_system import *
import os
import json

"""frasi = []
for i in range(100):
    with open(f"data/email_{i}.json", encoding="utf-8") as jsonf:
        frasi.append(json.loads(jsonf.read())['body'])

index_database(frasi)"""

# index_database(frasi)
matrix = load_embedding_matrix("embeddings.npy") 

def read_email(index):
    with open(f"data/email_{index}.json", encoding="utf-8") as jsonf:
        return json.dumps(json.loads(jsonf.read()))

def cerca_mail(query):
    out = search(query, matrix)[:3]
    return list(map(lambda x: read_email(x[0]), out))

"""out = cerca_mail("preventivo")
print(out)"""
    