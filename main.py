from flask import Flask, request, send_from_directory, jsonify
from flask_cors import CORS
import logging
import os

from importRicette.importVideo import import_recipe
from getRecipeList.getRecipeList import merge_json_files

# Configurazione del logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='backend.log'
)

logger = logging.getLogger(__name__)
# Initialize Flask app with custom template folder
app = Flask(__name__, static_folder='www', template_folder='www')

app.config['SECRET_KEY'] = b'0\xa38\xab\xc9D\xc30\xda\x1b\x84;p\x12\t['
CORS(app)  # This allows your Ionic app to make requests to this Flask app

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

@app.route('/process_url', methods=['POST'])
async def process_url():
    if 'url' not in request.json:
        return jsonify({"error": "URL mancante nella richiesta"}), 500
    url = request.json['url']
    urls = [url]
    await import_recipe(urls)
    return jsonify({"message": "Elaborazione conclusa"}), 200

@app.route('/getRecipeList', methods=['GET'])
async def getRecipeList():
 directory = 'static/ricette/'
 
 return jsonify(merge_json_files(directory)), 200

if __name__ == '__main__':
 app.run()
