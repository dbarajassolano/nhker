### NHK Easy Reading Assistance

A Flask application for assisting reading NHK Easy news articles. It uses [Fugashi](https://github.com/polm/fugashi) to parse the article title and text to identify verbs, adjectives and nouns. These are cross-referenced against WaniKani data to identify which words are below SRS level Guru II. For these words, a link is added to a [Jisho](https://jisho.org/) search so you can find the words' meanings. Finally, Google Cloud Translation is used to translate the text (translations are initially shown hidden).

This application uses code from [nhk-easy](https://github.com/nhk-news-web-easy/nhk-easy-api).

# Requirements

- [Fugashi](https://github.com/polm/fugashi) with the latest UniDic
- Google Cloud Translation Python API
- A WaniKani v2 API token

# Usage

```
PROJECT_ID=${GCLOUD_PROJECT_ID} WK_TOKEN=$(API_TOKEN) python nhker.py
```
