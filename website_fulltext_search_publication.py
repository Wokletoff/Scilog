# Заготовка для сервера приложения
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility, MilvusClient
from towhee import pipe, ops
from base64 import b64decode
import numpy as np
from towhee.datacollection import DataCollection
import configparser
import requests
import base64
import zlib
import urllib
import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# HTML template for the web app
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Scilog citations application</title>
</head>
<body>
    <h1>Scilog search article</h1>
    <form id="searchForm" onsubmit="sendQuery(); return false;">
        <input type="text" id="query" name="query" placeholder="Enter your search..." oninput="toggleButton()">
        <button type="button" id="searchButton" onclick="sendQuery()" disabled>Search</button>
    </form>
    <div id="result" style="margin-top:20px;"></div>
    <script>
        function toggleButton() {
            const query = document.getElementById('query').value;
            const button = document.getElementById('searchButton');
            button.disabled = query.length < 3;
        }

        async function sendQuery() {
            const query = document.getElementById('query').value;
            if (query.length < 3) return;
            const response = await fetch('/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query: query })
            });
            const data = await response.json();
            document.getElementById('result').innerText = data.message;
        }
    </script>
</body>
</html>
"""
class Index:
    def __init__(self,uri,token):
        self.chunk_size = 78
        self.cfp = configparser.RawConfigParser()
        self.collection = None
        self.uri= uri 
        self.token = token 
        self.sheme = None
        self.fealds = []
        
    def connect(self):  
            try:
                connections.connect(
                    uri= self.uri,
                    token= self.token
                ) 
                print("Successfully connected to Zilliz database")
                return True
            except Exception as e:
                print(f"Error connecting to Zilliz: {e}")
                return False
            
    def disconnect(self):
        """
        Закрытие соединения с базой данных
        """
        try:
            connections.disconnect("default")
            print("Successfully disconnected from Zilliz database")
        except Exception as e:
            print(f"Error disconnecting from Zilliz: {e}")

    def create_milvus_collection(self,collection_name, dim):
        try:            
            if utility.has_collection(collection_name):
                print(f"Collection {collection_name} already exists")
                self.collection = Collection(collection_name)
                return self.collection

            self.fields = [
            FieldSchema(name='id', dtype=DataType.VARCHAR, descrition='ids', max_length=500, is_primary=True, auto_id=False),
            FieldSchema(name='embedding', dtype=DataType.FLOAT_VECTOR, descrition='embedding vectors', dim=dim),
            FieldSchema(name='text', dtype=DataType.VARCHAR,max_length=1000)
            ]
            self.schema = CollectionSchema(fields=fields, description='reverse image search')
            self.collection = Collection(name=collection_name, schema=schema)

            # create IVF_FLAT index for collection.
            index_params = {
                'metric_type':'L2',
                'index_type':"IVF_FLAT",
                'params':{"nlist":2048}
            }
            self.collection.create_index(field_name="embedding", index_params=index_params)
            print(f"Successfully created collection {collection_name}")
            return self.collection
       
       
        except Exception as e:
            print(f"Error creating collection: {e}")
            return None
    
    

    def createcollection(self):
        chunks_data = []
        try:
            txt = open('5000.tab', 'r')
            for i in range(5):
                line = txt.readline()
                txtId = line.split("\t")[0]
                src = line.split("\t")[1].replace("\n","")
                if len(src) < 1000:
                    continue
                text2 = base64.b64decode(src)
                decompressed_data=zlib.decompress(text2, 16+zlib.MAX_WBITS)
                
            deco_date = decompressed_data.decode()
        
            chunks = [deco_date[i:(i + self.chunk_size)] for i in range(0, len(deco_date), self.chunk_size)]
            chunks_data.append((chunks, txtId))
            return chunks_data
        except Exception as e:
            print(f"Error processing file: {e}")
            return []
    
    
    def insert_chuncs(self, chunks_data):
        
        p = (
        pipe.input('id', 'text' ,'question','answer')
            .map('question', 'vec', ops.text_embedding.dpr(model_name='facebook/dpr-ctx_encoder-single-nq-base'))
            .map('text','text',lambda x: x)
            .map('vec', 'vec', lambda x: x / np.linalg.norm(x, axis=0))
            .map(('id', 'vec', 'text'), 'insert_status', ops.ann_insert.milvus_client(host="192.168.0.27", port="19530", collection_name='testuser2'))
            .output()
        )
        
        for chunks, txt_id in chunks_data:
            for idx, chunk in enumerate(chunks[:10]):
                
                DataCollection(p(f"{txt_id}:{idx}",chunk, chunk, txt_id)).show()

              
        
            
    def answer(self,question):
       self.collection.load()
       
       question = "question"
       ans_pipe = (
            pipe.input(question)
                .map('question', 'vec', ops.text_embedding.dpr(model_name="facebook/dpr-ctx_encoder-single-nq-base"))
                .map('vec', 'vec', lambda x: x / np.linalg.norm(x, axis=0))
                .map('vec', 'res', ops.ann_search.milvus_client(host="192.168.0.27", token= "19530", collection_name='testuser2', limit=1, **{'output_fields': ['id', 'text']}))
                .map('res', 'answer', lambda x: [x[0][0], x[0][3]])
                .output('question', 'answer')
        )
       ans = ans_pipe(question)
       ans = DataCollection(ans)
       ans.show()
       return ",".join(ans[0]["answer"])

        
        

# Route to serve the HTML page
@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


# API route to handle search requests
@app.route("/search", methods=["POST"])
def search():
    data = request.get_json()
    query = data.get("query", "")

    config = configparser.ConfigParser()
    config.read('settings.ini')
    uri = config.get("settings", "uri")
    token = config.get("settings", "token")
        
    index = Index(uri, token)
    if index.connect():
        collection = index.create_milvus_collection('testuser2', 768)
        if not collection:
            raise ValueError("Failed to create collection")
                    
        chunks_data = index.createcollection()
        if not chunks_data:
            raise ValueError("No valid data found in file")
                
        index.insert_chuncs(chunks_data)
        response_message = index.answer(query)

    return jsonify({"message": response_message})


if __name__ == "__main__":
    app.run(debug=True)
