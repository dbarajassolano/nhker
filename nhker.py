import webbrowser
from threading import Timer
from flask import Flask, render_template
from parse import parse_top_article

app = Flask(__name__)

@app.route('/')
def main():
    title, body = parse_top_article()
    return render_template('index.html', title=title, body=body)

def open_browser():
      webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run(port=5000)
