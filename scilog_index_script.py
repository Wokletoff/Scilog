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


cfp = configparser.RawConfigParser()
cfp.read('settings.ini')
connections.connect(
    uri= cfp.get("settings","uri"),
    token= cfp.get("settings","token")
)

def create_milvus_collection(collection_name, dim):
    if utility.has_collection(collection_name):
        utility.drop_collection(collection_name)

    fields = [
    FieldSchema(name='id', dtype=DataType.VARCHAR, descrition='ids', max_length=500, is_primary=True, auto_id=False),
    FieldSchema(name='embedding', dtype=DataType.FLOAT_VECTOR, descrition='embedding vectors', dim=dim),
    FieldSchema(name='text', dtype=DataType.VARCHAR,max_length=1000)
    ]
    schema = CollectionSchema(fields=fields, description='reverse image search')
    collection = Collection(name=collection_name, schema=schema)

    # create IVF_FLAT index for collection.
    index_params = {
        'metric_type':'L2',
        'index_type':"IVF_FLAT",
        'params':{"nlist":2048}
    }
    collection.create_index(field_name="embedding", index_params=index_params)
    return collection

collection = create_milvus_collection('testuser2', 768)




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
        .map(('id', 'vec', 'text'), 'insert_status', ops.ann_insert.milvus_client(uri=cfp.get("settings","uri"), token=cfp.get("settings","token"), collection_name='testuser2'))
        .output()
        )


deco_date = decompressed_data.decode()
chunk_size = 78
chunks = [deco_date[i:(i + chunk_size)] for i in range(0, len(deco_date), chunk_size)]


p = (
    pipe.input('id', 'text' ,'question','answer')
        .map('question', 'vec', ops.text_embedding.dpr(model_name='facebook/dpr-ctx_encoder-single-nq-base'))
        .map('text','text',lambda x: x)
        .map('vec', 'vec', lambda x: x / np.linalg.norm(x, axis=0))
        .map(('id', 'vec', 'text'), 'insert_status', ops.ann_insert.milvus_client(uri=cfp.get("settings","uri"), token=cfp.get("settings","token"), collection_name='testuser2'))
        .output()
)
for id, chunk in enumerate(chunks[:50]):

    DataCollection(p(f"{txtId}:{id}",chunk,chunk, txtId))


collection.load()
ans_pipe = (
    pipe.input('question')
        .map('question', 'vec', ops.text_embedding.dpr(model_name="facebook/dpr-ctx_encoder-single-nq-base"))
        .map('vec', 'vec', lambda x: x / np.linalg.norm(x, axis=0))
        .map('vec', 'res', ops.ann_search.milvus_client(uri=cfp.get("settings","uri"), token=cfp.get("settings","token"), collection_name='testuser2', limit=1, **{'output_fields': ['id', 'text']}))
        .map('res', 'answer', lambda x: [x[0][0], x[0][3]])
        .output('question', 'answer')
)


ans = ans_pipe('nduty toward its neighbors, not perhaps to')
ans = DataCollection(ans)
ans.show()
