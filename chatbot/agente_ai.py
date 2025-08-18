import streamlit as st
import openai
import time
import json
from typing import Dict, List
from dotenv import load_dotenv
import os

from email_utils import cerca_mail

load_dotenv()
openai_api_key = os.environ['OpenAI_API_Key']

# Configurazione di Streamlit e OpenAI
st.set_page_config(page_title="Assistant API Chatbot", page_icon="🤖")

# Inizializzazione delle variabili di sessione
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'thread_id' not in st.session_state:
    st.session_state.thread_id = None

# Funzione per cercare le email (implementazione di esempio)
def search_emails(query: str) -> List[Dict]:
    """
    Funzione di esempio per la ricerca delle email.
    Nella realtà, questa funzione dovrebbe interfacciarsi con il tuo sistema email.
    """
    print(f"Cerca la mail con la query:{query}")
    # Questo è solo un esempio - sostituisci con la tua logica di ricerca email
    return cerca_mail(query)

# Configurazione delle chiavi API
OPENAI_API_KEY = openai_api_key  # Configura questo in Streamlit Secrets
ASSISTANT_ID = "asst_ospySOMp9lqoJ42gq1wtosqQ"      # Il tuo Assistant ID

# Inizializzazione del client OpenAI
client = openai.Client(api_key=OPENAI_API_KEY)

def create_thread():
    """Crea un nuovo thread di conversazione"""
    thread = client.beta.threads.create()
    return thread.id

def process_message(user_input: str, thread_id: str):
    """Processa il messaggio dell'utente e ottiene la risposta dall'assistente"""
    # Aggiunge il messaggio dell'utente al thread
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_input
    )
    
    # Esegue l'assistente
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=ASSISTANT_ID
    )
    
    # Attende il completamento dell'esecuzione
    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )
        
        if run_status.status == 'requires_action':
            # Gestisce la chiamata alla funzione
            tool_calls = run_status.required_action.submit_tool_outputs.tool_calls
            tool_outputs = []
            
            for tool_call in tool_calls:
                if tool_call.function.name == "search_emails":
                    # Estrae gli argomenti della funzione
                    arguments = json.loads(tool_call.function.arguments)
                    query = arguments.get("query", "")
                    
                    # Esegue la ricerca delle email
                    result = search_emails(query)
                    
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": str(result)
                    })
            
            # Sottomette i risultati della funzione
            client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )
        
        elif run_status.status == 'completed':
            break
        
        elif run_status.status in ['failed', 'cancelled']:
            st.error(f"Run failed or cancelled: {run_status.status}")
            return None
        
        time.sleep(1)
    
    # Ottiene i messaggi più recenti
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    return messages.data[0].content[0].text.value

def main():
    st.title("📧 Email Assistant Chatbot")
    st.write("Chiedimi qualsiasi cosa riguardo le tue email!")

    # Inizializza il thread se non esiste
    if not st.session_state.thread_id:
        st.session_state.thread_id = create_thread()

    # Input dell'utente
    user_input = st.chat_input("Scrivi il tuo messaggio qui...")

    # Mostra la cronologia dei messaggi
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Processa il nuovo input dell'utente
    if user_input:
        # Mostra il messaggio dell'utente
        with st.chat_message("user"):
            st.write(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Ottiene e mostra la risposta dell'assistente
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            response = process_message(user_input, st.session_state.thread_id)
            response_placeholder.write(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()