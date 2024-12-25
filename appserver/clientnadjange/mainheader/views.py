from django.shortcuts import render
from pymilvus import Collection, connections

# Установите соединение с Milvus
connections.connect("default", host='localhost', port='19530')  # Укажите ваш хост и порт

# Предположим, что у вас есть коллекция с именем "my_collection"
collection_name = "my_collection"

def search_view(request):
    query = request.GET.get('text', '')  # Получаем текст из формы
    results = []

    if query:
        # Выполняем поиск в Milvus
        collection = Collection(collection_name)
        # Здесь вы можете использовать метод поиска, например, search
        # Предположим, что вы ищете по вектору, который соответствует вашему запросу
        # Вам нужно будет преобразовать строку в вектор (например, с помощью модели векторизации)
        # В этом примере мы просто используем заглушку для вектора
        vector = [0.0] * 128  # Замените на ваш вектор, полученный из строки
        search_results = collection.search(vector, "your_vector_field", limit=10)

        # Обработка результатов поиска
        for result in search_results:
            results.append(result.id)  # Или другой атрибут, который вам нужен

    return render(request, 'mainheader/index.html', {'results': results, 'query': query})
