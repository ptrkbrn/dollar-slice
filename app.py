from flask import Flask, render_template, request, redirect, session, url_for, flash
import psycopg2
from flask_session import Session
from tempfile import mkdtemp
from helpers import login_required, lookup
# from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configure app
app.config.from_object(__name__)

# Configure session to use filesystem
app.config['FILE_SESSION_DIR'] = mkdtemp()
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/crws_app'
# db = SQLAlchemy(app)

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
try:
    connection = psycopg2.connect(user="patrickbreen",
                                  password="hustlebone$69",
                                  host="127.0.0.1",
                                  port="5432",
                                  database="crws_app")

    cursor = connection.cursor()
finally:

    # index route
    @app.route('/')
    @login_required
    def index():
        """Displays index page"""
        return render_template('index.html')

    @app.route('/login', methods=["GET", "POST"])
    def login():
        """Logs user in"""
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            cursor.execute("SELECT * FROM users WHERE username = $$%s$$" % username)
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
            if password != check_username[0][2]:
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

    @app.route('/breweries', methods=['GET', 'POST', 'DELETE', 'PUT'])
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

    @app.route('/search/')
    @login_required
    def search():
        """Displays search page"""
        return render_template('search.html')

    @app.route('/results/')
    @login_required
    def results():
        """Displays search results"""
        searched = request.args.get("brewery")
        cursor.execute("SELECT name FROM breweries WHERE name ILIKE '%%%s%%'" % searched)
        results = cursor.fetchall()
        return render_template("results.html", searched=searched, results=results)

    @app.route('/breweries/<brewery>/update', methods=["GET"])
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

    @app.route('/breweries/<brewery>', methods=["GET", "POST", "DELETE", "PUT"])
    @login_required
    def brewery_page(brewery):
        """Brewery update routes"""

        # Updates distributor for given brewery
        if request.method == "PUT":
            new_distributor = request.form.get("new_distributor")
            print(new_distributor, brewery)
            cursor.execute("UPDATE breweries \
                            SET distributor = %s \
                            WHERE name = %s", (new_distributor, brewery))
            connection.commit()
            flash(brewery + " distributor updated to " + new_distributor + "!")
            return redirect('/breweries')

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

    @app.route('/breweries/<brewery>/beers/<beer>')
    @login_required
    def beer_page(brewery, beer):
        """Shows beer page"""
        # fetches db row for selected beer
        cursor.execute("SELECT * FROM beers WHERE name = $$%s$$" % beer)
        beername = cursor.fetchone()

        # fetches appropriate brewery name
        cursor.execute("SELECT name FROM breweries WHERE id = %i" % beername[2])
        brewery = cursor.fetchone()
        url_for('beer_page', brewery=brewery[0], beer=beername)
        return render_template('beer.html', beername=beername, brewery=brewery[0])

    # add a beer route
    @app.route('/breweries/<brewery>/beers/new')
    @login_required
    def add_beer(brewery):

        # Shows new beer form
        return render_template("add_beer.html", brewery=brewery)

    @app.route('/breweries/<brewery>/beers', methods=["GET", "POST"])
    @login_required
    def beers(brewery):
        """Adds beer to the database"""

        # Beer get route
        if request.method == "POST":
            new_beer = request.form.get("new_beer")
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
            cursor.execute("INSERT INTO beers (name, brewery_id) \
                            VALUES ($$%s$$, %s)" % (new_beer, brewery_id[0]))
            connection.commit()
            flash(new_beer + " added to " + brewery + "!")
            return redirect('/breweries/%s' % brewery)

    @app.route('/breweries/delete', methods=["GET", "POST"])
    @login_required
    def delete_brewery():
        cursor.execute("SELECT name FROM breweries ORDER BY name ASC")
        breweries = cursor.fetchall()
        return render_template("delete_brewery.html", breweries=breweries)

    @app.route("/delete_beer/", methods=["GET", "POST"])
    @login_required
    def delete_beer():
        """Removes beer from the database"""
        if request.method == "POST":
            delete = request.form.get("delete")
            print(delete)
            cursor.execute("SELECT brewery_id FROM beers WHERE name = $$%s$$" % delete)
            brewery_id = cursor.fetchone()
            cursor.execute("DELETE FROM beers WHERE name = $$%s$$" % delete)
            connection.commit()
            cursor.execute("SELECT name FROM breweries WHERE id = %i" % brewery_id)
            brewery = cursor.fetchone()
            return redirect("/breweries/%s" % brewery)
        else:
            brewery = request.args.get("brewery")
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
