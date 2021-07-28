import requests
import json

# api страница википедии

with open ('config.json', 'rb') as f:
    config = json.load(f)

url = config["url"]

def connection():
    """
    Подключение к ICSTECH WIKI, а также поддержание сессии
    :return: ответ POST запроса
    """
    s = requests.Session()
    token_params = {
        'action': 'query',
        'meta': 'tokens',
        'type': 'login',
        'format': 'json'
    }
    r = s.get(url=url, params = token_params)
    data = r.json()
    login_token = data['query']['tokens']['logintoken']
    wiki_connect = {
        'action':'login',
        'lgname':config["wiki_login"],
        'lgpassword':config["wiki_password"],
        'lgtoken':login_token,
        'format':'json'
    }
    s.post(url, data=wiki_connect)
    return s




def searching(word):
    """
    Поиск по WIKI (названия страниц и содержание текста в страницах)
    :param word : На вход принимает str (искомый текст)
    :return: Два списка: все заголовки страниц и название страниц содержащих нужный текст
    """
    # Поиск по заголовкам
    search_head = {
        'action':'query',
        'format':'json',
        'list':'search',
        'srsearch': word,
        'srwhat':'title'
    }
    data_head = connection().get(url=url, params = search_head).json() # делаем get запрос на поиск слова
    sp_search_head = []
    for i in data_head['query']['search']:
        sp_search_head.append(i['title'])

    # Поиск внутри страниц
    search_page = {
        'action':'query',
        'format':'json',
        'list':'search',
        'srsearch': word,
        'srwhat':'text'
    }
    data_page = connection().get(url=url, params=search_page).json()
    sp_search_page = []
    for i in data_page['query']['search']:
        sp_search_page.append(i['title'])
    return sp_search_page, sp_search_head


def wiki_search_page(word):
    """
    Тоже самое, что и функция searching, но ищет ТОЛЬКО заголовки
    :param word: str слово на поиск
    :return: список заголовков страниц
    """
    search_head = {
        'action':'query',
        'format':'json',
        'list':'search',
        'srsearch': word,
        'srwhat':'title'
    }
    data_head = connection().get(url=url, params = search_head).json()
    sp_search_head = []
    for i in data_head['query']['search']:
        sp_search_head.append(i['title'])
    return sp_search_head


def wiki_search_text(word):
    """
    Тоже самое, что и функция searching, но ищет ТОЛЬКО внутри страниц
    :param word: str слово на поиск
    :return: список заголовков страниц
    """
    search_page = {
        'action':'query',
        'format':'json',
        'list':'search',
        'srsearch': word,
        'srwhat':'text'
    }
    data_page = connection().get(url=url, params=search_page).json()
    sp_search_page = []
    for i in data_page['query']['search']:
        sp_search_page.append(i['title'])
    return sp_search_page


def content(word):
    """
    Получает контент страницы
    :param word: str название страницы
    :return: str текст в формате wikitext
    """
    # Вытаскивание содержимого страницы
    try:
        params = {
            'action':'query',
            'prop':'revisions',
            'titles':f'{word}',
            'rvslots':'*',
            'rvprop':'content',
            'formatversion':2
        }
        data = json.loads(connection().get(url=url, params=params).text.split('<pre class="api-pretty-content">')[1].split('</pre></div><div class="printfooter">')[0])
        sp = data['query']['pages'][0]['revisions'][0]['slots']['main']['content']
        return sp
    except:
        print(word)



def recent_changes():
    search_page = {
        "format": "json",
        "rcprop": "user|userid|comment|parsedcomment|flags|timestamp|title|ids|sizes"
                  "|redirect|loginfo|tags|sha1",
        "list": "recentchanges",
        "action": "query",
        "rclimit": "3"
    }

    data_page = connection().get(url=url, params=search_page).json()["query"]["recentchanges"]
    for i in data_page:
        print(i)

    # for i in data_page:
    #     print(str(i['title']))