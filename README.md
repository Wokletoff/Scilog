# Scilog

Проект создания LLM интерфейса к базе данных научных публикаций.
.

## Содержание
- [Технологии](#технологии)
- [Начало работы](#начало-работы)
- [Тестирование](#тестирование)
- [Contributing](#contributing)
- [To do](#to-do)
- [Команда проекта](#команда-проекта)

## Технологии
- [Milvus](https://milvus.io/docs/integrate_with_haystack.md)
- [Ziliz - облачное хранилище](https://zilliz.com/)
- [VSCode](https://code.visualstudio.com/)
- [Huggingface - Facebook LLM ](https://huggingface.co/facebook/dpr-ctx_encoder-single-nq-base)
- [Библиотека Towhee](https://towhee.io/)


## Использование
Для запуска проекта:
 1. Клонировать проект.
 2. Сделать копию settings.ini  из файла settings_sample.ini.
 3. Заполнить URI и Toklen внутри файла settings.ini из аккаунта Ziliz или собственного хранилища.
 4. Создать вертуальное окружение и установить модули из файла requirements.txt.


## Разработка
### Требования
Для установки и запуска проекта, необходим Python v3.11.2.

## Contributing
Для отправки доработок (оформить pull request).

## To do
- [x] Опробация модели Вопрос-ответ - 1_build_question_answering_engine.ipynb
- [ ] Отработка процесса формирования векторной базы данных - 3_build_question_answering_engine.ipynb
- [ ] Devops автоматизация распередиленная векторная индексация научных статей как больших данных
- [ ] Разработка интерфейса для симантического поиска научных статей
- [ ] Разработка нейросетивого интерфейса для коммуникации научного контента

## Команда проекта
- [Wokletoff](https://github.com/Wokletoff)
- [rahalos](https://github.com/rahalos)

## Источники
- [Towhee.io](https://github.com/towhee-io/examples/tree/main/nlp/question_answering) 
