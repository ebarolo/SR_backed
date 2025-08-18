from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
openai_api_key = os.environ['OpenAI_API_Key']
client = OpenAI(api_key=openai_api_key)

for i in range(100):
    print(i)
    response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
        "role": "system",
        "content": [
            {
            "type": "text",
            "text": "Generi email realistiche di contatto, di preventivi, di informazioni, di collaborazioni, di acquisto prodotti e tante altre, ricche di dettagli. Inventati il cliente, il settore, il progetto che vogliono fare tutto rendendo l'idea che sono email realistiche, metti anche cifre di preventivi e contratti da firmare/firmati. Io mi chiamo Simone Rizzo e sono il CEO di Inferentia e sviluppiamo soluzioni AI custom per i clienti su qualsiasi settore. Devi formattare la mail in JSON."
            }
        ]
        },
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": "genera una mail"
            }
        ]
        },
        {
        "role": "assistant",
        "content": [
            {
            "type": "text",
            "text": "{\"date\":\"25 ottobre 2023, 14:37 CET\",\"subject\":\"Richiesta di Preventivo per Servizi di Marketing Digitale\",\"from\":\"m.rossi@azienda.it\",\"body\":\"Gentile Sig.ra Bianchi,\\n\\nSpero che questa e-mail vi trovi bene. Mi chiamo Marco Rossi e sono il direttore marketing di Azienda S.R.L. Ho avuto modo di conoscere i vostri servizi attraverso il sito web e sono rimasto colpito dalla vostra reputazione nel settore.\\n\\nStiamo attualmente cercando un partner per aiutare a lanciare una nuova campagna di marketing digitale mirata per il nostro portfolio di prodotti. Vorremmo ricevere un preventivo dettagliato per i seguenti servizi:\\n\\n1. Gestione completa dei social media, inclusi la creazione di contenuti e l'engagement.\\n2. Campagne pubblicitarie pay-per-click su Google e Facebook.\\n3. Ottimizzazione SEO per incrementare la visibilità organica del nostro sito.\\n\\nPer darvi un'idea del nostro progetto, la campagna dovrebbe lanciarsi entro il 15 dicembre 2023 e la durata stimata è di sei mesi. Il nostro budget orientativo per l'intero progetto è di circa €50.000.\\n\\nSarebbe possibile organizzare una riunione, anche virtuale, per discutere ulteriormente le nostre esigenze e le vostre proposte? Vi prego di farmi sapere le vostre disponibilità per la prossima settimana.\\n\\nIn attesa di un vostro riscontro, vi ringrazio anticipatamente per la vostra collaborazione.\\n\\nCordiali Saluti,\\n\\nMarco Rossi\\nAzienda S.R.L\\nVia della Innovazione, 25, 20100 Milano\\nTelefono: +39 02 1234567\\nEmail: m.rossi@azienda.it\\nSito Web: www.azienda.it\"}"
            }
        ]
        }
    ],
    response_format={
        "type": "json_schema",
        "json_schema": {
        "name": "email_schema",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
            "date": {
                "type": "string",
                "description": "The date and time when the email was sent."
            },
            "subject": {
                "type": "string",
                "description": "The subject line of the email."
            },
            "from": {
                "type": "string",
                "description": "The sender's email address."
            },
            "body": {
                "type": "string",
                "description": "The main content or body of the email."
            }
            },
            "required": [
            "date",
            "subject",
            "from",
            "body"
            ],
            "additionalProperties": False
        }
        }
    },
    temperature=1,
    max_completion_tokens=2048,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0
    )

    # parse this into a json dictionary
    import json

    # Assuming the response contains a correctly formatted JSON string in the message content
    json_string = response.choices[0].message.content
    email_data = json.loads(json_string)

    # Save the data into a JSON file
    with open(f'data/email_{i}.json', 'w', encoding='utf-8') as f:
        json.dump(email_data, f, ensure_ascii=False, indent=4)
