from flask import Flask, render_template, request, redirect
import psycopg2
# from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/crws_app'
# db = SQLAlchemy(app)

# @app.route('/')
# def hello_world():
# 	return "Hello, World!"

try:
	connection = psycopg2.connect(user = "patrickbreen",
								  password = "hustlebone$69",
								  host = "127.0.0.1",
								  port = "5432",
								  database = "crws_app")

	cursor = connection.cursor()
finally:

	@app.route('/')
	def index():
		return render_template('index.html')

	@app.route('/add_brewery', methods=['GET', 'POST'])
	def add_brewery():
		if request.method == 'POST':
			brewery = request.form.get('brewery')

			# escapes single quotes from brewery names
			if "'" in brewery:
				brewery.replace("'", "\'")
			distributor = request.form.get('distributor')
			cursor.execute("SELECT name FROM breweries")
			rows = cursor.fetchall()

			for row in rows:
				if brewery == row[0]:
					return("That brewery is already listed!")
			cursor.execute("INSERT INTO breweries (name, distributor) VALUES (%s, %s)", (brewery, distributor))
			connection.commit()
			return redirect('/view_all')
		else:
			return render_template('add.html')

	@app.route('/view_all')
	def viewall():
		cursor.execute("SELECT * FROM breweries")
		breweries = cursor.fetchall()
		# print(breweries)
		# for brewery in breweries:
		# 	print(brewery[1])
		# 	print(brewery[2])
		return render_template('viewall.html', breweries=breweries)

	@app.route('/search/')
	def search():
		return render_template('search.html')

	@app.route('/update/', methods=["GET", "POST"])
	def update():
		brewery = request.args.get("brewery")
		cursor.execute("SELECT name FROM breweries WHERE name = $$%s$$" % brewery)
		selectedBrewery = cursor.fetchone()
		cursor.execute("SELECT distributor FROM breweries GROUP BY distributor")
		distributors = cursor.fetchall()
		# print(selectedBrewery)
		if request.method == "POST":
			for distributor in distributors:
				print(selectedBrewery)
				print(selectedBrewery[0])
			newDistributor = request.form.get("distributor")
			# if updatedBrewery not in breweries:
			# 	return("Brewery not in system!")
			# else:
			cursor.execute("UPDATE breweries SET distributor = %s WHERE name = %s", (newDistributor, selectedBrewery))
			connection.commit()
			return redirect('/view_all')
		else:
			return render_template('update.html', brewery=selectedBrewery[0], distributors=distributors)

	@app.route('/login')
	def register():
		return "login route!"

	@app.route('/breweries/', methods=["GET", "POST"])
	def show_brewery_page():
		if request.method == "GET":
			brewery = request.args.get("brewery")
			# print(brewery)
			cursor.execute("SELECT * FROM breweries WHERE name = $$%s$$" % brewery)
			selectedBrewery = cursor.fetchone()
			if selectedBrewery is None:
				return("Brewery not found!")
			brewery_id = selectedBrewery[0]
			print("Brewery id: ", brewery_id)
			cursor.execute("SELECT name FROM beers WHERE brewery_id = %i" % brewery_id)
			beers = cursor.fetchall()
			return render_template('brewery.html', brewery = selectedBrewery[1], beers = beers, distributor = selectedBrewery[2])

	@app.route('/beers/')
	def show_beer_page():
		selected = request.args.get("beer")
		cursor.execute("SELECT * FROM beers WHERE name = $$%s$$" % selected)
		beername = cursor.fetchone()
		cursor.execute("SELECT name FROM breweries WHERE id = %i" % beername[2])
		brewery = cursor.fetchone()
		return render_template('beer.html', beername = beername, brewery = brewery[0])

	@app.route('/add_beer/', methods=["GET", "POST"])
	def add_beer():
		brewery = request.args.get("brewery")
		if request.method == "POST":
			return("TODO")
		else:
			return render_template("add_beer.html", brewery=brewery)

	@app.route('/beer_added/', methods=["GET", "POST"])
	def beer_added():
		brewery = request.args.get("brewery")
		if request.method == "POST":
			newBeer = request.form.get("new_beer")
			cursor.execute("SELECT id FROM breweries WHERE name = $$%s$$" % brewery)
			brewery_id = cursor.fetchone()
			cursor.execute("INSERT INTO beers (name, brewery_id) VALUES ('%s', %s)" % (newBeer, brewery_id[0]))
			connection.commit()
			return redirect('/breweries/?brewery=%s' % brewery)

	# @app.route('/<brewery>/beers/<beername>')
	# def show_beer_page(brewery, beername):
	# 	return render_template('beer.html', brewery = brewery, beername = beername)
