import webbrowser
from threading import Timer
from flask import Flask, render_template
from parse import NewsParser

app = Flask(__name__)

np = NewsParser()

@app.route('/')
def main():
    return render_template('index.html', articles=np.articles)

@app.route('/<int:article_id>')
def show_article(article_id):
    title, body = np.parse_article_threaded(article_id)
    return render_template('article.html', title=title, body=body)
    
def open_browser():
      webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run(port=5000)
