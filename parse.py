from os import environ
from functools import partial
from fugashi import Tagger
from google.cloud import translate
from collections import namedtuple
from nhk_easy_api import Api
import concurrent.futures

jisho_root = 'https://jisho.org/search/'

ParsedSentence = namedtuple('ParsedSentence', ['raw', 'parsed', 'translation'])

def get_articles() -> list[tuple[str, str]]:
    nhk = Api()
    return [nhk.download_text_by_priority(i) for i in range(len(nhk.top_news))]

class ParserTranslator(object):
    def __init__(self, tagger: Tagger, parent: str,
                 client: translate.TranslationServiceClient) -> None:
        
        self.tagger = tagger
        self.parent = parent
        self.client = client

    def parse_str(self, text: str, gurued_vocab: list[str] | None) -> str:
        
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

            if gurued_vocab is not None:
                if word.feature.lemma in gurued_vocab:
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

    def translate_and_parse(self, text: str, gurued_vocab) -> ParsedSentence:
        return ParsedSentence(raw=text, parsed=self.parse_str(text, gurued_vocab),
                              translation=self.translate_str(text))

class NewsParser(object):

    def __init__(self) -> None:

        print('Preparing tagger...')
        self.tagger = Tagger()
        
        print('Preparing translator...')
        pid = environ.get('PROJECT_ID', '')
        if pid == '':
            raise AssertionError(f'No Google Cloud Project ID set in environment')
        self.parent = f'projects/{pid}'
        self.client = translate.TranslationServiceClient()

        self.PT = ParserTranslator(self.tagger, self.parent, self.client)

    def parse_article(self, id: int, articles: list[tuple[str, str]], gurued_vocab: list[str] | None) -> tuple[ParsedSentence, list[ParsedSentence]]:
        
        if not articles:
            return (ParsedSentence(raw='', parsed='', translation=''),
                    [ParsedSentence(raw='', parsed='', translation='')])
        
        title, body = articles[id]
        delimiter = '。'
        body_rows = [e + delimiter for e in body.split(delimiter) if e]

        print('PTing title...')
        title_parsed = self.PT.translate_and_parse(title, gurued_vocab)

        print('PTing body...')
        body_parsed = []
        for i in range(len(body_rows)):
            print(f'{(i * 100 / len(body_rows)):{3}}%\tParsing: {body_rows[i]}')
            body_parsed.append(self.PT.translate_and_parse(body_rows[i], gurued_vocab))
        print('100%')

        return title_parsed, body_parsed

    def parse_article_threaded(self, id: int, articles: list[tuple[str, str]], gurued_vocab: list[str] | None) -> tuple[ParsedSentence, list[ParsedSentence]]:

        if not articles:
            return (ParsedSentence(raw='', parsed='', translation=''),
                    [ParsedSentence(raw='', parsed='', translation='')])
        
        title, body = articles[id]
        delimiter = '。'
        body_rows = [e + delimiter for e in body.split(delimiter) if e]

        print('PTing title...')
        title_parsed = self.PT.translate_and_parse(title, gurued_vocab)

        print('PTing body...')
        partial_PT = partial(self.PT.translate_and_parse, gurued_vocab=gurued_vocab)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            body_parsed = list(executor.map(partial_PT, body_rows))

        return title_parsed, body_parsed
