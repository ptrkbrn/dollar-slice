import requests
import urllib.parse

from flask import session, redirect, request
from functools import wraps

# decorates routes, requiring user login
def login_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if session.get("user_id") is None:
			return redirect("/login")
		return f(*args, **kwargs)
	return decorated_function

def lookup(searched_brewery):
	"""Query API for brewery info"""

	# Contact API
	try:
		response = requests.get(f"https://api.openbrewerydb.org/breweries?by_name={urllib.parse.quote_plus(searched_brewery)}")
		response.raise_for_status()
	except requests.RequestException:
		return None

	# Parse response
	try:
		brewery = response.json()
		return {
			"name": brewery[0]["name"],
			"state": brewery[0]["state"],
			"website": brewery[0]["website_url"]
		}
	except (KeyError, TypeError, ValueError):
		return None