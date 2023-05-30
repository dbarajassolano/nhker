### NHK Easy Reading Assistance

A Flask application for assisting reading NHK Easy news articles. It uses [Fugashi](https://github.com/polm/fugashi) to parse the article title and text to identify verbs, adjectives and nouns. If a Wanikani token is provided, these words are cross-referenced against WaniKani data to identify which words are below SRS level Guru II. For each of the identified words, a link is added to a [Jisho](https://jisho.org/) search so you can find the word's meanings. Finally, Google Cloud Translation is used to translate the text (translations are initially shown hidden).

This application uses code from [nhk-easy](https://github.com/nhk-news-web-easy/nhk-easy-api).

# Requirements

- [Fugashi](https://github.com/polm/fugashi) with the latest UniDic
- Google Cloud Translation Python API
- A WaniKani v2 API token (Optional)
- Flask
- Flask-Session
- redis-py
- A [redis](https://redis.io/) server up and running (to store the Wanikani data)

# Usage

```
PROJECT_ID=${GCLOUD_PROJECT_ID} python nhker.py
```
