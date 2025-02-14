import zstandard as zstd
import io
import json
import re




def process_line(line):
    try:
        data = json.loads(line)
        return process(data)
    except json.JSONDecodeError as e:
        print(f"Ошибка парсинга JSON: {e}")
    except Exception as e:
        print(f"Ошибка при обработке данных: {e}")


def process(data):
    # Ваша логика обработки
    return data


def stream_process_file(file_path, max_lines=50):
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
                    return result
                    break


rez = stream_process_file("e:/lib/annas_archive_meta__aacid__worldcat__20231001T025039Z--20231001T235839Z.jsonl.zst")

citation_keys = ["creator", "title", "edition", "publisher", "publicationPlace", "publicationDate"]

# Извлекаем данные для цитирования
record = rez[44]["metadata"]["record"]
citation_data = {key: record.get(key) for key in citation_keys}

print(citation_data)


data = rez[44]

# Функция для извлечения количества страниц из 'physicalDescription'
def extract_page_count(physical_description):
    match = re.search(r"(\d+)\s+pages?", physical_description)
    if match:
        return match.group(1)
    return None


# Функция для форматирования авторов
def format_authors(contributors, style="APA"):
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
                initials = " ".join([f"{name[0]}." for name in first_name.split()])
                authors.append(f"{last_name} {initials}")
    return authors


# Извлекаем данные для цитирования
record = data["metadata"]["record"]
contributors = record.get("contributors", [])
title = record.get("title", "")
edition = record.get("edition", "")
publisher = record.get("publisher", "")
publication_place = record.get("publicationPlace", "")
publication_date = record.get("publicationDate", "")
physical_description = record.get("physicalDescription", "")
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
        citation = f"{authors_gost} {title} {edition_str} — {publication_place}: {publisher}, {publication_date}. — {pages_str} {series_str} {isbn_str}"
        citation = re.sub(" +", " ", citation).strip()
    else:
        citation = "Неизвестный стиль цитирования."
    return citation.strip()


# Выводим цитаты в разных стилях
styles = ["GOST"]
for style in styles:
    print(f"\nСтиль {style}:\n{generate_citation(style)}")

