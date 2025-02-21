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
def process_line(line):
    try:
        data = json.loads(line)
        return data
    except json.JSONDecodeError as e:
        print(f"Ошибка парсинга JSON: {e}")
    except Exception as e:
        print(f"Ошибка при обработке данных: {e}")

def stream_process_file(file_path, max_lines=4):
    line_count = 0
    result = []
    with open(file_path, "rb") as compressed_file:
        dctx = zstd.ZstdDecompressor(max_window_size=2**31)
        with dctx.stream_reader(compressed_file) as reader:
            text_stream = io.TextIOWrapper(reader, encoding="utf-8")
            for line in text_stream:
                result.append(process_line(line))
                line_count += 1
                if line_count >= max_lines:
                    return  result
                    break
print(1)
rez = stream_process_file("/mnt/disk2/annas_llm.jsonl.zst")


# Извлекаем данные для цитирования
def getcit(rez):
   citation_keys = ["creator", "title", "edition", "publisher", "publicationPlace", "publicationDate","physicalDescription", "isbns", "isbn13"]
   result = []
   for value in rez:
      value = value["metadata"]
      if "record" in value:
         record = value["record"]
         result.append( {key: record.get(key) for key in citation_keys})
   return result

citation_data = getcit(rez)
print(2)



print(3)

data = citation_data
for el in citation_data:
    # Функция для извлечения количества страниц из 'physicalDescription'
    def extract_page_count(physical_description):
        match = re.search(r"(\d+)\s+pages?", physical_description)
        if match:
            return match.group(1)
        return None

    def format_authors(contributors, style="GOST"):
        authors = []
        for contributor in contributors:
            if "firstName" in contributor and "secondName" in contributor:
                first_name = contributor["firstName"]["text"]
                last_name = contributor["secondName"]["text"]
                if style == "APA":
                    authors.append(f"{last_name}, {first_name[0]}.")
                elif style == "MLA":
                    authors.append(f"{last_name}, {first_name}")
                elif style == "Chicago":
                    authors.append(f"{first_name} {last_name}")
                elif style == "Harvard":
                    authors.append(f"{last_name}, {first_name}")
                elif style == "GOST":
                    authors.append(f"{last_name} {initials}")
        return authors

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
        print(4)
        return collection


    # Составляем ссылки в разных стилях
    def generate_citation(style):
        authors = format_authors(contributors, style)
        authors_str = ", ".join(authors)
        if edition:
                edition_str = f"{edition}."
        else:
                edition_str = ""

        if page_count:
                pages_str = f"{page_count} pp."
        else:
                pages_str = ""

        if isbn:
                isbn_str = f"ISBN {isbn}."
        else:
                isbn_str = ""

        if series:
                series_str = f"Series: {series}."
        else:
                series_str = ""

        if style == "GOST":
                # Для ГОСТ: Фамилия И.О. Название: подзаголовочные данные. — Сведения об издании. — Место издания: Издательство, Год. — Объём. — (Серия). — ISBN.
                authors_gost = "; ".join([f"{a}" for a in authors])
                citation = f"{autors}{title}{edition_str} — {publication_place}: {publisher}, {publication_date}. — {pages_str} {series_str} {isbn_str}"
                citation = re.sub(" +", " ", citation).strip()
        else:
                citation = "Неизвестный стиль цитирования."
        return citation.strip()

# Извлекаем данные для цитирования
    chunks =[]
    record = el
    contributors = record.get("contributors", [])
    autors = record.get("creator", "")
    title = record.get("title", "")
    edition = record.get("edition", "")
    publisher = record.get("publisher", "")
    publication_place = record.get("publicationPlace", "")
    publication_date = record.get("publicationDate", "")
    publication_date = "" if publication_date is None else publication_date
    physical_description = record["physicalDescription"] if "physicalDescription"  in  record and record["physicalDescription"] is not None else ""
    isbn13 = record.get("isbn13", "")
    isbns = record.get("isbns")  # Может быть None
    series = record.get("series", None)

    # Убираем квадратные скобки из даты
    publication_date = re.sub(r"[\[\]]", "", publication_date)

    # Извлекаем количество страниц
    page_count = extract_page_count(physical_description)

    
    # Обрабатываем ISBN
    if isbn13:
        isbn = isbn13
    elif isbns and isinstance(isbns, list) and isbns:
        isbn = isbns[0]
    else:
        isbn = ""


    # Выводим цитаты в разных стилях
    styles = ["GOST"]
    for style in styles: 
        chunks.append(generate_citation(styles[0]))

def create_milvus_collection(collection_name, dim):
        if utility.has_collection(collection_name):
            utility.drop_collection(collection_name)

        fields = [
        FieldSchema(name='id', dtype=DataType.VARCHAR, descrition='ids', max_length=500, is_primary=True, auto_id=False),
        FieldSchema(name='embedding', dtype=DataType.FLOAT_VECTOR, descrition='embedding vectors',dim=dim),
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
        print(4)
        return collection
 
collection = create_milvus_collection('testuser2', 768) 
collection.load()

p = (
                pipe.input('id', 'text' ,'question','answer')
                .map('question', 'vec', ops.text_embedding.dpr(model_name='facebook/dpr-ctx_encoder-single-nq-base'))
                .map('text','text',lambda x: x)
                .map('vec', 'vec', lambda x: x / np.linalg.norm(x, axis=0))
                .map(('id', 'vec', 'text'), 'insert_status', ops.ann_insert.milvus_client(host ="192.168.0.27", port ="19530" , collection_name='testuser2'))
                .output()
    )

DataCollection(p(chunks[0],chunks, chunks, chunks[0])).show()
print(DataCollection)

ans_pipe = (pipe.input('question')
        .map('question', 'vec', ops.text_embedding.dpr(model_name="facebook/dpr-ctx_encoder-single-nq-base"))
        .map('vec', 'vec', lambda x: x / np.linalg.norm(x, axis=0))
        .map('vec', 'res', ops.ann_search.milvus_client(host="192.168.0.27", port = "19530", collection_name='testuser2', limit=1, **{'output_fields': ['id', 'text']}))
        .map('res', 'answer', lambda x: [x[0][0], x[0][3]])
        .output('question', 'answer')
)
print(6)

ans = ans_pipe(input("введите статью:"))
ans = DataCollection(ans)
ans.show()
        
            
               
                
                
                
            
        

# Route to serve the HTML page
@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


# API route to handle search requests
@app.route("/search", methods=["POST"])
def search():
    data = request.get_json()
    query = data.get("query", "")

    connections.connect(
        alias = "default",
        host = "192.168.0.27",
        port = "19530"
    )
        
    


    return jsonify({"message": response_message})


if __name__ == "__main__":
    app.run(debug=True)
