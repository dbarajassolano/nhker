import webbrowser
from threading import Timer, Thread
from flask import Flask, render_template
from turbo_flask import Turbo
from parse import NewsParser

app = Flask(__name__)
turbo = Turbo(app)

np = NewsParser()

@app.route('/')
def main():
    return render_template('index.html', articles=np.articles)

def update_article(article_id: int) -> None:
    with app.app_context():
        title, body = np.parse_article_threaded(article_id)
        turbo.push(turbo.replace(render_template('article.html', title=title, body=body), 'article_content'))

@app.route('/<int:article_id>')
def show_article(article_id):
    tparse = Thread(target=update_article, args=[article_id])
    tparse.start()
    return render_template('loading.html')

def open_browser():
      webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run(port=5000)
