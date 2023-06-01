from os import environ
from fugashi import Tagger #pyright: ignore
from google.cloud import translate
from collections import namedtuple
from nhk_easy_api import Api

jisho_root = 'https://jisho.org/search/'

ParsedSentence = namedtuple('ParsedSentence', ['raw', 'parsed', 'translation'])

def get_articles() -> list[tuple[str, str]]:
    print('Downloading articles...', end=' ', flush=True)
    nhk = Api()
    articles = [nhk.download_text_by_priority(i) for i in range(len(nhk.top_news))]
    print('Done')
    return articles

class NewsParser(object):

    def __init__(self) -> None:

        print('Preparing tagger...', end=' ', flush=True)
        self.tagger = Tagger()
        print('Done')
        
        print('Preparing translator...', end=' ', flush=True)
        pid = environ.get('PROJECT_ID', '')
        if pid == '':
            raise AssertionError(f'No Google Cloud Project ID set in environment')
        self.parent = f'projects/{pid}'
        self.client = translate.TranslationServiceClient()
        print('Done')

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

    def parse_article(self, id: int, articles: list[tuple[str, str]], gurued_vocab: list[str] | None) -> tuple[ParsedSentence, list[ParsedSentence]]:

        if not articles:
            return (ParsedSentence(raw='', parsed='', translation=''),
                    [ParsedSentence(raw='', parsed='', translation='')])

        title, body = articles[id]
        delimiter = '。'
        body_rows = [e + delimiter for e in body.split(delimiter) if e]

        print('Parsing and translating title...', end=' ', flush=True)
        response = self.client.translate_text(parent=self.parent,
                                              contents=[title], target_language_code='en')
        translated_title = response.translations[0].translated_text
        title_parsed = ParsedSentence(raw=title, parsed=self.parse_str(title, gurued_vocab),
                                      translation=translated_title)
        print('Done')

        print('Parsing body...', end=' ', flush=True)
        parsed_rows = []
        for line in body_rows:
            parsed_rows.append(self.parse_str(line, gurued_vocab))
        print('Done')

        print('Translating body...', end=' ', flush=True)
        translate_response = self.client.translate_text(parent=self.parent, contents=body_rows, target_language_code='en')
        translated_rows = [translation.translated_text for translation in translate_response.translations]
        print('Done')
        
        body_parsed = [ParsedSentence(raw=line, parsed=parsed_line, translation=translated_line) for (line, parsed_line, translated_line) in zip(body_rows, parsed_rows, translated_rows)]

        return title_parsed, body_parsed
