from flask import Flask, render_template, request, redirect, session, url_for, flash
import os
import psycopg2
from flask_session import Session
from tempfile import mkdtemp
from helpers import login_required, lookup
from werkzeug.security import generate_password_hash, check_password_hash
from flask_heroku import Heroku
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
heroku = Heroku(app)
# Configure app
app.config.from_object(__name__)

# Configure session to use filesystem
app.config['FILE_SESSION_DIR'] = mkdtemp()
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

#configures sqlalchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/crws_app'

# disables sqlalchemy modification tracking for improved perfomance
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# @app.route('/')
# def hello_world():
# return "Hello, World!"

# ARBITRARY SECRET KEY FROM DOCS!!!!!!!!!!!!
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# Ensures templates autp-reload.
app.config['TEMPLATES_AUTO_RELOAD'] = True

@app.after_request
def after_request(response):
    """Ensures responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# connects to database
DATABASE_URL = os.environ['DATABASE_URL']

connection = psycopg2.connect(DATABASE_URL)

cursor = connection.cursor()

# index route
@app.route('/')
@login_required
def index():
    """Displays index page"""
    cursor.execute("SELECT username FROM users WHERE id = %s" % session["user_id"])
    current_user = cursor.fetchone()
    return render_template('index.html', current_user=current_user[0])

@app.route('/login', methods=["GET", "POST"])
def login():
    """Logs user in"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        cursor.execute("SELECT * FROM users WHERE username = $$%s$$" % username)
        print(generate_password_hash(password))
        check_username = cursor.fetchall()
        # clears any existing user_id
        session.clear()

        # Ensures user entered a username and password
        if not username or not password:
            return render_template("error.html", message="Enter a username and password to continue!")
        # Ensures username exists
        if not check_username:
            return render_template("error.html", message="Invalid username!")
        # Ensures password is correct
        if not check_password_hash(check_username[0][2], password):
            return render_template("error.html", message="Invalid password!")

        # stores current user info
        session["user_id"] = check_username[0][0]

        # redirects to index
        flash("Hi, " + username + "!")
        return redirect('/')

    # Get route
    else:
        return render_template("login.html")

@app.route('/logout')
def logout():
    """Logs user out"""
    # clears out user data
    session.clear()

    # redirects to login page
    return redirect('/login')

# index page route
# @app.route('/index')
# @login_required
# def index():
#   return render_template('index.html')

@app.route('/breweries/new', methods=['GET', 'POST'])
@login_required
def add_brewery():
    """Allows user to add breweries to the database"""
    return render_template('add.html')

@app.route('/breweries', methods=['GET', 'POST', 'DELETE', 'PUT', 'PATCH'])
@login_required
def breweries():
    """Brewery index route"""

    # Brewery post route
    if request.method == 'POST':
        brewery = request.form.get('brewery')

        # escapes single quotes from brewery names
        if "'" in brewery:
            brewery.replace("'", "\'")
        new_brewery = lookup(brewery)
        if new_brewery is None:
            new_brewery = {'name': brewery,
                           'state': None,
                           'website': None}
        distributor = request.form.get('distributor')
        cursor.execute("SELECT name FROM breweries Where name = $$%s$$" % new_brewery["name"])
        row = cursor.fetchone()

        # Ensures user entered a brewery
        if new_brewery is None:
            return render_template("error.html", message="Invalid brewery!")

        # Handles duplicate brewery name
        if row is not None:
            return render_template("error.html", message="That brewery is already listed!")
        cursor.execute("INSERT INTO breweries (name, distributor, state, website, added_by) \
                        VALUES (%s, %s, %s, %s, %s)",
                        (new_brewery["name"], 
                         distributor, 
                         new_brewery["state"], 
                         new_brewery["website"], 
                         session["user_id"]))
        connection.commit()
        flash(new_brewery["name"] + " added!")
        return redirect('/breweries')
    # Brewery get route
    else:
        cursor.execute("SELECT * FROM breweries ORDER BY name ASC")
        breweries = cursor.fetchall()
        return render_template('viewall.html', breweries=breweries)

@app.route('/search/brewery')
@login_required
def search():
    """Displays search page"""

    # Selects brewery names for autocomplete
    cursor.execute("SELECT name FROM breweries")
    breweries = cursor.fetchall()
    return render_template('search.html', breweries=breweries)

@app.route('/search/beer')
@login_required
def search_beers():
    """Displays beer search page"""

    # Selects brewery and beer names for autcomplete
    cursor.execute("SELECT breweries.name, beers.name FROM breweries INNER JOIN beers ON breweries.id = beers.brewery_id")
    beers = cursor.fetchall()
    return render_template('beer_search.html', beers=beers)

@app.route('/results/')
@login_required
def results():
    """Displays search results"""

    # Handles brewery searches
    if request.args.get("brewery"):
        searched = request.args.get("brewery")
        cursor.execute("SELECT name FROM breweries WHERE name ILIKE $$%%%s%%$$" % searched)
        results = cursor.fetchall()

        # if only one brewery is found, redirect to the appropriate page
        if len(results) == 1:
            return redirect('/breweries/%s' % results[0][0])
        return render_template("results.html", searched=searched, results=results)

    # Handles beer searches
    if request.args.get("beer"):
        searched = request.args.get("beer")
        cursor.execute("SELECT beers.name, breweries.name \
                       FROM breweries \
                       INNER JOIN beers \
                       ON breweries.id = beers.brewery_id \
                       WHERE beers.name ILIKE $$%%%s%%$$" % searched)
        results = cursor.fetchall()
        return render_template("beer_results.html", searched=searched, results=results)

@app.route('/breweries/<brewery>/update')
@login_required
def update(brewery):
    """Shows form to update distributor for given brewery"""
    cursor.execute("SELECT name FROM breweries WHERE name = $$%s$$" % brewery)
    selected_brewery = cursor.fetchone()
    cursor.execute("SELECT distributor FROM breweries GROUP BY distributor")
    distributors = cursor.fetchall()
    return render_template('update.html',
                           brewery=selected_brewery[0],
                           distributors=distributors)

@app.route('/breweries/<brewery>/edit')
@login_required
def edit_brewery_info(brewery):
    """Shows form to edit info for existing brewery"""
    cursor.execute("SELECT * FROM breweries WHERE name = $$%s$$" % brewery)
    edit_brewery = cursor.fetchall()
    return render_template('edit_brewery.html', edit_brewery=edit_brewery[0])

@app.route('/breweries/<brewery>', methods=["GET", "POST", "DELETE", "PUT", "PATCH"])
@login_required
def brewery_page(brewery):
    """Brewery update routes"""

    # Updates distributor for given brewery
    if request.method == "PUT":
        new_distributor = request.form.get("new_distributor")
        print(new_distributor, brewery)
        cursor.execute("UPDATE breweries \
                        SET distributor = %s, updated_by = %s \
                        WHERE name = %s", (new_distributor, session["user_id"], brewery))
        connection.commit()
        flash(brewery + " distributor updated to " + new_distributor + "!")
        return redirect('/breweries')

    # Edits info for existing brewery
    if request.method == "PATCH":
        cursor.execute("SELECT id FROM breweries WHERE name = $$%s$$" % brewery)
        brewery_id = cursor.fetchone()
        new_name = request.form.get("new_name")
        new_distributor = request.form.get("new_distributor")
        new_website = request.form.get("new_website")
        new_state = request.form.get("new_state")
        if new_name:
            cursor.execute("UPDATE breweries \
                            SET name = %s \
                            WHERE id = %s",
                            (new_name, brewery_id))
            connection.commit()
        if new_distributor:
            cursor.execute("UPDATE breweries \
                            SET distributor = %s \
                            WHERE id = %s",
                            (new_distributor, brewery_id))
            connection.commit()
        if new_website:
            cursor.execute("UPDATE breweries \
                            SET website = %s \
                            WHERE id = %s",
                            (new_website, brewery_id))
            connection.commit()
        if new_state:
            cursor.execute("UPDATE breweries \
                            SET state = %s \
                            WHERE id = %s",
                            (new_state, brewery_id))
            connection.commit()
        cursor.execute("UPDATE breweries \
                        SET updated_by = %s \
                        WHERE id = %s",
                        (session["user_id"], brewery_id))
        return redirect("/breweries")

    # Brewery delete route
    if request.method == "DELETE":
        brewery = request.form.get("brewery")
        cursor.execute("SELECT id FROM breweries WHERE name = $$%s$$" % brewery)
        brewery_id = cursor.fetchone()
        if brewery_id is None:
            return render_template("error.html", message="Brewery not found.")

        # deletes beers associated with brewery from beers

        cursor.execute("DELETE FROM beers WHERE brewery_id = %i" % brewery_id)

        # deletes brewery from breweries
        cursor.execute("DELETE FROM breweries WHERE id = %i" % brewery_id)
        connection.commit()
        flash(brewery + " deleted!")
        return redirect("/breweries")

    # Shows page for given brewery
    else:
        cursor.execute("SELECT * FROM breweries WHERE name = $$%s$$" % brewery)
        selected_brewery = cursor.fetchone()

        # Handles invalide brewery names
        if selected_brewery is None:
            return render_template("error.html", message="Brewery not found!")
        brewery_id = selected_brewery[0]

        # Selects and formats the date the brewery was added
        if selected_brewery[7] is not None:
            cursor.execute("SELECT to_char(date_added, 'mm-dd-yy') \
                           FROM breweries \
                           WHERE id = %i" % brewery_id)
            date = cursor.fetchone()
        else:
            date = None
        # Accesses info for user who added the brewery
        if selected_brewery[3] is not None:
            cursor.execute("SELECT username \
                           FROM users \
                           WHERE id = %i" % selected_brewery[3])
            added_by = cursor.fetchone()
        else:
            added_by = None
        if selected_brewery[4] is not None:
            cursor.execute("SELECT username \
                           FROM users \
                           WHERE id = %i" % selected_brewery[4])
            updated_by = cursor.fetchone()
        else:
            updated_by = None
        # Uses brewery id to fetch associated beers
        cursor.execute("SELECT name \
                       FROM beers \
                       WHERE brewery_id = %i \
                       ORDER BY name ASC" % brewery_id)
        beers = cursor.fetchall()
        url_for('brewery_page', brewery=selected_brewery[1])
        return render_template('brewery.html',
                               brewery=selected_brewery[1],
                               beers=beers,
                               distributor=selected_brewery[2],
                               website=selected_brewery[5],
                               location=selected_brewery[6],
                               added_by=added_by,
                               updated_by=updated_by,
                               date=date
                               )

@app.route('/distributors/<distributor>')
@login_required
def distributor_page(distributor):
    """Shows page for specified distributor"""
    cursor.execute("SELECT * FROM breweries \
                   WHERE distributor = $$%s$$ \
                   ORDER BY name ASC" % distributor)
    breweries = cursor.fetchall()
    url_for('distributor_page', distributor=breweries[0][2])
    return render_template('distributor.html', breweries=breweries,
                           distributor=breweries[0][2])

@app.route('/breweries/<brewery>/beers/delete')
@login_required
def show_beer_delete_form(brewery):
    """Shows beer deletion form"""
    cursor.execute("SELECT id from breweries WHERE name = $$%s$$" % brewery)
    brewery_id = cursor.fetchone()
    print(brewery_id[0])
    cursor.execute("SELECT beers.name \
                   FROM beers, breweries \
                   WHERE brewery_id = %i \
                   GROUP BY beers.name" % brewery_id[0])
    beers = cursor.fetchall()
    print(beers)    
    return render_template("delete_beer.html", brewery=brewery, beers=beers)

@app.route('/breweries/<brewery>/beers/<beer>', methods=["GET", "DELETE", "PATCH"])
@login_required
def beer_page(brewery, beer):
    """Beer routes"""
    if request.method == "DELETE":
        cursor.execute("DELETE FROM beers WHERE name = $$%s$$" % beer)
        connection.commit()
        flash(beer + " deleted!")
        return redirect("/breweries/%s" % brewery)

    if request.method == "PATCH":
        cursor.execute("SELECT id FROM beers WHERE name = $$%s$$" % beer)
        beer_id = cursor.fetchone();
        new_name = request.form.get("new_name")
        new_style = request.form.get("new_style")
        new_abv = request.form.get("new_abv")
        new_price = request.form.get("new_price")
        print(new_name, new_style, new_abv, new_price)

        if new_name:
            cursor.execute("UPDATE beers \
                            SET name = %s \
                            WHERE id = %s",
                            (new_name, beer_id))
            connection.commit()
        if new_style:
            cursor.execute("UPDATE beers \
                            SET style = %s \
                            WHERE id = %s",
                            (new_style, beer_id))
            connection.commit()
        if new_abv:
            cursor.execute("UPDATE beers \
                            SET abv = %s \
                            WHERE id = %s",
                            (new_abv, beer_id))
            connection.commit()
        if new_price:
            cursor.execute("UPDATE beers \
                            SET price = %s \
                            WHERE id = %s",
                            (new_price, beer_id))
            connection.commit()
        return redirect("/breweries/%s" % brewery)
    # fetches db row for selected beer
    cursor.execute("SELECT * FROM beers WHERE name = $$%s$$" % beer)
    beername = cursor.fetchone()

    # fetches appropriate brewery name
    cursor.execute("SELECT name FROM breweries WHERE id = %i" % beername[2])
    brewery = cursor.fetchone()
    url_for('beer_page', brewery=brewery[0], beer=beername)
    return render_template('beer.html', beername=beername, brewery=brewery[0])

@app.route('/breweries/<brewery>/beers/new')
@login_required
def add_beer(brewery):
    """Shows new beer form"""

    return render_template("add_beer.html", brewery=brewery)

@app.route('/breweries/<brewery>/beers/<beer>/edit')
@login_required
def edit_beer(brewery, beer):
    """Edit beer info"""
    cursor.execute("SELECT * FROM beers WHERE name = $$%s$$" % beer)
    edit_beer = cursor.fetchall()
    print(edit_beer)
    return render_template("edit_beer.html", beer=beer, brewery=brewery, edit_beer=edit_beer[0])



@app.route('/breweries/<brewery>/beers', methods=["GET", "POST"])
@login_required
def beers(brewery):
    """Adds beer to the database"""

    # Beer get route
    if request.method == "POST":
        new_beer = request.form.get("new_beer")
        price = request.form.get("price")
        if not price:
            price = None
        print(price)
        abv = request.form.get("abv")
        if not abv:
            abv = None
        style = request.form.get("style")
        if not style:
            style = None
        cursor.execute("SELECT id FROM breweries WHERE name = $$%s$$" % brewery)
        brewery_id = cursor.fetchone()

        # Fetches beers currently listed for brewery
        cursor.execute("SELECT name FROM beers WHERE brewery_id = %i" % brewery_id)
        current_beers = cursor.fetchall()

        # Ensures new beer isn't a duplicate
        for beer in current_beers:
            if new_beer == beer[0]:
                return render_template("error.html", message="Beer already listed!")
       
        # Adds new beer to database
        cursor.execute("INSERT INTO beers (name, brewery_id, price, style, abv) \
                        VALUES (%s, %s, %s, %s, %s)", (new_beer, brewery_id[0], price, style, abv))
        connection.commit()
        flash(new_beer + " added to " + brewery + "!")
        return redirect('/breweries/%s' % brewery)

@app.route('/breweries/delete', methods=["GET", "POST"])
@login_required
def delete_brewery():
    cursor.execute("SELECT name FROM breweries ORDER BY name ASC")
    breweries = cursor.fetchall()
    return render_template("delete_brewery.html", breweries=breweries)

if __name__ == ' __main__':
    #app.debug = True
    app.run()