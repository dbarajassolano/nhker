import functools
from flask import Flask, redirect, render_template, request, session, url_for
from flask_session import Session
from parse import NewsParser, get_articles
from wk import get_gurued_vocab, get_wk_username

app = Flask(__name__)
sess = Session(app)

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'wk_username' not in session:
            return redirect(url_for('index'))
        return view(**kwargs)
    return wrapped_view

def set_wk_data(wk_token: str) -> None:
    clear_wk_data()
    print('Downloading WK data...', end=' ', flush=True)
    session['wk_token'] = wk_token
    session['wk_username'] = get_wk_username(wk_token)
    session['gurued_vocab'] = get_gurued_vocab(wk_token)
    if session['wk_username'] is None or session['gurued_vocab'] is None:
        print('Failed to get WK data')
        clear_wk_data()
    else:
        print('Done')

def clear_wk_data() -> None:
    print('Clearing session data...', end=' ', flush=True)
    session['wk_token'] = ''
    session['wk_username'] = None
    session['gurued_vocab'] = None
    print('Done')

@app.route('/', methods=['POST', 'GET'])
def index():
    if 'wk_token' not in session:
        if request.method == 'POST':
            wk_token = request.form['wk_token']
            set_wk_data(wk_token)
            return redirect(url_for('list_articles'))
        return render_template('index.html')
    else:
        return redirect(url_for('list_articles'))

@app.route('/list')
@login_required
def list_articles():
    session['articles'] = get_articles()
    return render_template('list.html', articles=session['articles'])

@app.route('/refresh')
def refresh():
    set_wk_data(session['wk_token'])
    return redirect(url_for('list_articles'))

@app.route('/logout')
def logout():
    print('Clearing session data')
    session.clear()
    return redirect(url_for('index'))

@app.route('/<int:article_id>')
@login_required
def show_article(article_id):
    np = NewsParser()
    if 'articles' not in session:
        return redirect(url_for('list_articles'))
    if article_id >= len(session['articles']):
        return redirect(url_for('list_articles'))
    title, body = np.parse_article(article_id, session['articles'], session['gurued_vocab'])
    return render_template('article.html', title=title, body=body)
    
if __name__ == '__main__':

    app.config.from_mapping(
        SECRET_KEY = 'dev',
        SESSION_TYPE = 'redis',
        SESSION_PERMANENT = True
    )
    sess.init_app(app)
    app.run(port=5000)
