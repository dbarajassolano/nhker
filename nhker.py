import webbrowser
from threading import Timer
from flask import Flask, redirect, render_template, request, session, url_for
from parse import NewsParser

app = Flask(__name__)
app.secret_key = 'dev'

np = NewsParser()

@app.route('/', methods=['POST', 'GET'])
def index():
    if 'wk_token' not in session:
        if request.method == 'POST':
            session.permanent = True
            wk_token = request.form['wk_token']
            status = np.set_wk_data(wk_token)
            if status == 0:
                session['wk_token'] = wk_token
                session['wk_username'] = np.wk_username
            else:
                session['wk_token'] = ''
                session['wk_username'] = ''
            return redirect(url_for('list_articles'))
        return render_template('index.html')
    else:
        return redirect(url_for('list_articles'))

@app.route('/list')
def list_articles():
    np.get_articles()
    return render_template('list.html', articles=np.articles)

@app.route('/refresh')
def refresh():
    np.set_wk_data(session['wk_token'])
    return redirect(url_for('list_articles'))

@app.route('/logout')
def logout():
    session.clear()
    np.clear_wk_data()
    return redirect(url_for('index'))

@app.route('/<int:article_id>')
def show_article(article_id):
    if not np.articles:
        return redirect(url_for('list_articles'))
    if article_id >= len(np.articles):
        return redirect(url_for('list_articles'))
    title, body = np.parse_article_threaded(article_id)
    return render_template('article.html', title=title, body=body)
    
def open_browser():
      webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run(port=5000)
