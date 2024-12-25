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


class Index:
    def __init__(self,uri,token):
        self.chunk_size = 78
        self.cfp = configparser.RawConfigParser()
        self.collection = None
        self.uri= uri 
        self.token = token 
        
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

            fields = [
            FieldSchema(name='id', dtype=DataType.VARCHAR, descrition='ids', max_length=500, is_primary=True, auto_id=False),
            FieldSchema(name='embedding', dtype=DataType.FLOAT_VECTOR, descrition='embedding vectors', dim=dim),
            FieldSchema(name='text', dtype=DataType.VARCHAR,max_length=1000)
            ]
            schema = CollectionSchema(fields=fields, description='reverse image search')
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
        
        txt = open('5000.tab', 'r')
        for i in range(5):
            line = txt.readline()
            txtId = line.split("\t")[0]
            src = line.split("\t")[1].replace("\n","")
            if len(src) < 1000:
                continue
            text2 = base64.b64decode(src)
            decompressed_data=zlib.decompress(text2, 16+zlib.MAX_WBITS)
            p =(
                pipe.input('id', 'text', 'question' )
                .map('question', 'vec', ops.text_embedding.dpr(model_name='facebook/dpr-ctx_encoder-single-nq-base'))
                .map('text','text',lambda x: x)
                .map('vec', 'vec', lambda x: x / np.linalg.norm(x, axis=0))
                .map(('id', 'vec', 'text'), 'insert_status', ops.ann_insert.milvus_client(uri=self.uri, token=self.token, collection_name='testuser2'))
                .output()
                )
            
        deco_date = decompressed_data.decode()
    
        chunks = [deco_date[i:(i + self.chunk_size)] for i in range(0, len(deco_date), self.chunk_size)]
        return (chunks, txtId) 
    
    
    def collection(self,chunks, txtId):
        p = (
        pipe.input('id', 'text' ,'question','answer')
            .map('question', 'vec', ops.text_embedding.dpr(model_name='facebook/dpr-ctx_encoder-single-nq-base'))
            .map('text','text',lambda x: x)
            .map('vec', 'vec', lambda x: x / np.linalg.norm(x, axis=0))
            .map(('id', 'vec', 'text'), 'insert_status', ops.ann_insert.milvus_client(uri=self.uri, token=self.token, collection_name='testuser2'))
            .output()
        )
        for id, chunk in enumerate(chunks[:5]):
            res = DataCollection(p(f"{txtId}:{id}",chunk,chunk, txtId)).show()  
        return res
            
    def answer(self,question):
       self.collection.load()
       question = "question"
       ans_pipe = (
            pipe.input(question)
                .map('question', 'vec', ops.text_embedding.dpr(model_name="facebook/dpr-ctx_encoder-single-nq-base"))
                .map('vec', 'vec', lambda x: x / np.linalg.norm(x, axis=0))
                .map('vec', 'res', ops.ann_search.milvus_client(uri=self.uri, token= self.token, collection_name='testuser2', limit=1, **{'output_fields': ['id', 'text']}))
                .map('res', 'answer', lambda x: [x[0][0], x[0][3]])
                .output('question', 'answer')
        )
       return ans_pipe 
    
    def run():
        config = configparser.ConfigParser()
        config.read('settings.ini')
        uri = config.get("settings", "uri")
        token = config.get("settings", "token")
        
        index = Index(uri, token)

        if index.connect():
            try:
                collection = index.create_milvus_collection('testuser2', 768)
                if not collection:
                    raise ValueError("Failed to create collection")
                
                ans =index.answer(str(input("Введите часть статьи: ")))
                ans1 = DataCollection(ans)
                ans1.show() 
            except Exception as e:
                print(f"Error during execution: {e}")
            finally:
                    index.disconnect() 
            

if __name__ == "__main__":
    Index.run()