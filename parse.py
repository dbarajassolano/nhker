from os import environ
from fugashi import Tagger
from google.cloud import translate
from collections import namedtuple
from nhk_easy_api import Api
import requests
import concurrent.futures

jisho_root = 'https://jisho.org/search/'

ParsedSentence = namedtuple('ParsedSentence', ['raw', 'parsed', 'translation'])

class ParserTranslator(object):
    def __init__(self, tagger: Tagger, parent: str,
                 client: translate.TranslationServiceClient,
                 gurued_vocab: list[str]) -> None:
        self.tagger = tagger
        self.parent = parent
        self.client = client
        self.gurued_vocab = gurued_vocab

    def parse_str(self, text: str) -> str:
        words = self.tagger(text)
        output = ''
        
        for word in words:
            
            search_url = ''
            if (word.feature.pos1 == '名詞'
                and word.feature.pos2 != '数詞'
                and word.feature.pos3 != '助数詞可能'):
                search_url = jisho_root + word.surface
            elif (word.feature.pos2 == '名詞的'
                  and word.feature.pos3 != '助数詞'):
                search_url = jisho_root + word.surface
            elif (word.feature.pos1 == '動詞'
                  and word.feature.lemma not in {'居る', '為る', '行く', '有る'}):
                search_url = jisho_root + word.feature.lemma + '#verb'
            elif word.feature.pos1 == '形容詞':
                search_url = jisho_root + word.feature.lemma + '#adjective'
            elif word.feature.pos1 == '副詞':
                search_url = jisho_root + word.feature.lemma + '#adv'

            if word.feature.lemma in self.gurued_vocab:
                search_url = ''

            if search_url != '':
                pron = word.feature.pron if word.feature.pron is not None else ''
                output = output + '<a href="{:s}"><ruby>{:s}<rt>{:s}</rt></ruby></a>'.format(search_url, word.surface, pron)
            else:
                output = output + word.surface

        return output

    def translate_str(self, text: str) -> str:
        response = self.client.translate_text(parent=self.parent,
                                              contents=[text], target_language_code='en')
        return response.translations[0].translated_text

    def translate_and_parse(self, text: str) -> ParsedSentence:
        return ParsedSentence(raw=text, parsed=self.parse_str(text),
                              translation=self.translate_str(text))

def get_gurued_vocab(wk_token: str) -> list[str]:
    base_url = 'https://api.wanikani.com/v2/'
    headers = {'Authorization': 'Bearer ' + wk_token}
    wk_data = get_wk_url(base_url + 'subjects?types=vocabulary', headers)
    gurued_data = get_wk_url(base_url + 'assignments?subject_types=vocabulary&srs_stages=6,7,8,9', headers)
    gurued_ids = [item['data']['subject_id'] for item in gurued_data]
    return [item['data']['characters'] for item in wk_data if item['id'] in gurued_ids]
    
def get_wk_url(url: str, headers: dict) -> list[dict]:
    req = requests.get(url, headers=headers)
    data = req.json()['data']
    next_url = req.json()['pages']['next_url']
    while True:
        req = requests.get(next_url, headers=headers)
        assert req.status_code==200, f'Failed to get {next_url}, got code {req.status_code}'
        data = data + req.json()['data']
        next_url = req.json()['pages']['next_url']
        if next_url is None:
            break
    return data

class NewsParser(object):

    def __init__(self) -> None:

        print('Downloading articles...')
        self.nhk = Api()
        self.articles = self.get_articles()
        
        print('Preparing tagger...')
        self.tagger = Tagger()
        
        print('Preparing translator...')
        pid = environ.get('PROJECT_ID', '')
        assert pid, f'No Google Cloud Project ID'
        self.parent = f'projects/{pid}'
        self.client = translate.TranslationServiceClient()

        print('Preparing WaniKani data...')
        wk_token = environ.get('WK_TOKEN', '')
        assert pid, f'No WaniKani token'
        self.gurued_vocab = get_gurued_vocab(wk_token)

        print('Preparing parsing and translating (PTing) object...')
        self.PT = ParserTranslator(self.tagger, self.parent, self.client, self.gurued_vocab)
        
    def get_articles(self) -> list[tuple[str, str]]:

        return [self.nhk.download_text_by_priority(i) for i in range(len(self.nhk.top_news))]

    def parse_article(self, id: int) -> tuple[ParsedSentence, list[ParsedSentence]]:

        title, body = self.articles[id]
        delimiter = '。'
        body_rows = [e + delimiter for e in body.split(delimiter) if e]

        print('PTing title...')
        title_parsed = self.PT.translate_and_parse(title)

        print('PTing body...')
        body_parsed = []
        for i in range(len(body_rows)):
            print(f'{(i * 100 / len(body_rows)):{3}}%\tParsing: {body_rows[i]}')
            body_parsed.append(self.PT.translate_and_parse(body_rows[i]))
        print('100%')

        return title_parsed, body_parsed

    def parse_article_threaded(self, id: int) -> tuple[ParsedSentence, list[ParsedSentence]]:

        title, body = self.articles[id]
        delimiter = '。'
        body_rows = [e + delimiter for e in body.split(delimiter) if e]

        print('PTing title...')
        title_parsed = self.PT.translate_and_parse(title)

        print('PTing body...')
        with concurrent.futures.ThreadPoolExecutor() as executor:
            body_parsed = list(executor.map(self.PT.translate_and_parse, body_rows))

        return title_parsed, body_parsed
