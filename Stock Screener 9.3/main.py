from screener import Stock, scrape, screen
from peewee import *
import flask

db = SqliteDatabase('data/stocks.db')
db.connect()

app = flask.Flask(__name__)

@app.route('/stock-screener')
def home(): 
    return flask.render_template('home.html')

@app.route('/stock-screener/new-screen', methods = ['GET', 'POST'])
def form():
    if flask.request.method == 'POST':
        data = flask.request.form.to_dict(flat = False)
        dictionary = {}
        for key in data:
            if data[key][0]:
                if key == 'market_cap':
                    dictionary[key] = data[key]
                elif key == 'earnings_history' or key == 'dividend_history':
                    if int(data[key][0]) != 0:
                        dictionary[key] = data[key][0]
                else:
                    dictionary[key] = data[key][0]
        table = []
        for stock in screen(dictionary):
            row = []
            cells = [stock.symbol, stock.name, stock.market_cap, stock.current_ratio, stock.debt_to_assets, stock.earnings_history, stock.dividend_history, stock.eps_growth, stock.price_to_earnings, stock.price_to_book]
            for cell in cells:
                if cell:
                    row.append(cell)
                else:
                    row.append('N/A')
            table.append(row)
        return flask.render_template('results.html', results = table)
    return flask.render_template('form.html')

@app.route('/ajax')
def ajax():
    dictionary = {}
    mc = ['a', 'b', 'c']
    other = {'d':'current_ratio', 'e':'debt_to_assets', 'f': 'earnings_history', 'g': 'dividend_history', 'h': 'eps_growth', 'i': 'price_to_earnings', 'j': 'price_to_book'}
    if flask.request.args.get('a', 0) or flask.request.args.get('b', 0) or flask.request.args.get('c', 0):
        mc_inputs = []
        for letter in mc:
            if flask.request.args.get(letter, 0):
                mc_inputs.append(flask.request.args.get(letter, 0))
        dictionary['market_cap'] = mc_inputs
    for letter in other:
        if flask.request.args.get(letter, 0):
            if letter == 'f' or letter == 'g':
                if flask.request.args.get(letter, 0) != '0':
                    dictionary[other[letter]] = flask.request.args.get(letter, 0)
            else:
                dictionary[other[letter]] = flask.request.args.get(letter, 0)
    estimate = 0
    if dictionary:
        for stock in screen(dictionary):
            estimate += 1
    else:
        for stock in Stock.select():
            estimate += 1
    return flask.jsonify(estimate)

@app.route('/stock-screener/about')
def about():
    return flask.render_template('about.html')

@app.route('/stock-screener/about/criteria')
def criteria():
    return flask.render_template('criteria.html')

@app.route('/stock-screener/about/timeline', methods = ['GET', 'POST'])
def timeline():
    if flask.request.method == 'POST':
        return flask.render_template('timeline2.html')
    return flask.render_template('timeline.html')

@app.route('/stock-screener/feedback')
def feedback():
    return flask.render_template('feedback.html')

if __name__ == '__main__':
    prompt = input('Enter 1 to scrape, 2 to run flask: ')
    if prompt == '1':
        confirm = input('Are you sure you want to clear the database? Press enter to continue. ')
        if not confirm:
            scrape()
    elif prompt == '2':
        app.run(port = 80)