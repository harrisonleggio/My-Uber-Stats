from flask import Flask, request, url_for, session, redirect, jsonify, render_template
from flask_oauth import OAuth
import json
import imaplib
import email
from bs4 import BeautifulSoup
import base64





GOOGLE_CLIENT_ID = '838764710395-p7nk0fcig6cl27lhfs25l49sku98dfc4.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = 'c0kLkqaVfGueyxBN4OkwImEH'
REDIRECT_URI = '/authorized'  # one of the Redirect URIs from Google APIs console

SECRET_KEY = 'Uber'
DEBUG = True

app = Flask(__name__)
app.secret_key = 'Uber'
oauth = OAuth()

google = oauth.remote_app('google',
                          base_url='https://www.google.com/accounts/',
                          authorize_url='https://accounts.google.com/o/oauth2/auth',
                          request_token_url=None,
                          request_token_params={
                              'scope': 'https://www.googleapis.com/auth/userinfo.email https://mail.google.com/',
                              'response_type': 'code'},
                          access_token_url='https://accounts.google.com/o/oauth2/token',
                          access_token_method='POST',
                          access_token_params={'grant_type': 'authorization_code'},
                          consumer_key=GOOGLE_CLIENT_ID,
                          consumer_secret=GOOGLE_CLIENT_SECRET)

@app.route('/')
def landing():
    return render_template('index.html')

@app.route('/google')
def index():
    access_token = session.get('access_token')
    if access_token is None:
        return redirect(url_for('login'))

    access_token = access_token[0]
    from urllib2 import Request, urlopen, URLError

    headers = {'Authorization': 'OAuth '+access_token}
    req = Request('https://www.googleapis.com/oauth2/v1/userinfo',
                  None, headers)
    try:
        res = urlopen(req)
    except URLError, e:
        if e.code == 401:
            # Unauthorized - bad token
            session.pop('access_token', None)
            return redirect(url_for('login'))
        return res.read()
    j = json.loads(res.read())
    email_address = j['email']
    print email_address, access_token
    return Uber_Cost(email_address, access_token)


@app.route('/login')
def login():
    callback=url_for('authorized', _external=True)
    return google.authorize(callback=callback)



@app.route(REDIRECT_URI)
@google.authorized_handler
def authorized(resp):
    access_token = resp['access_token']
    session['access_token'] = access_token, ''
    return redirect(url_for('index'))


@google.tokengetter
def get_access_token():
    return session.get('access_token')


def GenerateOAuth2String(username, access_token, base64_encode=True):
    auth_string = 'user=%s\1auth=Bearer %s\1\1' % (username, access_token)
    if base64_encode:
        auth_string = base64.b64encode(auth_string)
    return auth_string




def Uber_Cost(email_address, access_token):

    auth_string = GenerateOAuth2String(email_address, access_token, base64_encode=False)
    print auth_string

    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.debug = 4
    mail.authenticate('XOAUTH2', lambda x: auth_string)
    mail.select('INBOX')

    final_cost1 = ""
    final_cost2 = ""

    cost_array = []
    output = []

    result,data = mail.search(None, 'FROM', '"Uber Receipts"')

    ids = data[0]
    id_list = ids.split()


    for id in id_list:
        result,data = mail.fetch(id, "(RFC822)")

        message_body = data[0][1]

        uber_email = email.message_from_string(message_body)
        for part in uber_email.walk():
            if part.get_content_type() == "text/html":
                body = part.get_payload(None, decode=True)

        soup = BeautifulSoup(body, 'html.parser')
        #print soup.prettify()

        for row in soup.find_all('td', attrs={"class" : "price final-charge"}):
            final_cost1 = row.text.lstrip().strip()

        for row in soup.find_all('td', attrs={"class" : "totalPrice chargedFare black"}):
            final_cost2 = row.text.lstrip().strip()

        if final_cost1 != "":
            cost_array.append(final_cost1)
        if final_cost2 != "":
            cost_array.append(final_cost2)

    cost_array = list(set(cost_array))

    cost_array = [x.lstrip("$") for x in cost_array]
    cost_array = [float(x) for x in cost_array]
    
    if len(cost_array) == 0:
        return render_template('error.html')
    
    total_cost = sum(cost_array)
    max_ride = max(cost_array)
    min_ride = min(cost_array)
    average_ride = total_cost/len(cost_array)
    total_cost = round(total_cost, 2)
    max_ride = round(max_ride, 2)
    min_ride = round(min_ride, 2)
    average_ride = round(average_ride, 2)
    
    output.append('<html> \
	<head> \
		<title>Uber History</title> \
		<meta charset="utf-8" /> \
		<meta name="viewport" content="width=device-width, initial-scale=1" /> \
		<link rel="stylesheet" href="static/main.css" /> \
	</head> \
	<body style="background-color:PowderBlue;"> \
        <!-- Header --> \
			<header id="header"> \
			<nav class="left"> \
            <a href="http://www.uber.com"> \
        <img border="0" alt="W3Schools" \
        src="https://fortunedotcom.files.wordpress.com/2016/02/rex.png" width="100" height="100"> \
			</nav> \
				<a href="/" class="logo">Uber History</a> \
			<nav class="right"> \
			<a href="#" class="content">Not affiliated with Uber.</a> \
				</nav \
			</header> \
		<!-- Banner --> \
			<section id="banner"> \
				<div class="content"> \
					<h1>Your ride history</h1><p>')
    output.append('<ul class="actions">')
    output.append('<li><center><a href="/google" class="button scrolly">You have taken ' + str(len(cost_array)) + ' rides</a></center></li>')
    output.append('<li><center><a href="/google" class="button scrolly">You have spent  $' + str(total_cost) + '</a></center></li>')
    output.append('<li><center><a href="/google" class="button scrolly">Your average ride costs $' + str(average_ride) + '</a></center></li>')    
    output.append('<li><center><a href="/google" class="button scrolly">Your most expensive ride was $ ' + str(max_ride) + '</a></center></li>')
    output.append('<li><center><a href="/google" class="button scrolly">Your least expensive ride was $ ' + str(min_ride) + '</a></center></ul></li>')

    """output.append('You have taken ' + str(len(cost_array)) + ' Uber rides totaling $' 
    + str(total_cost) + '<br>')
    output.append('Your average ride cost: $' + str(average_ride) + '<br>')
    output.append('Most Expensive Ride: $' + str(max_ride) + '<br>')
    output.append('Least Expensive Ride: $' + str(min_ride) + '<br></p>')"""
    output.append('</div> \
			</section> \
        <!-- One --> \
		<!-- Scripts --> \
			<script src="assets/js/jquery.min.js"></script> \
			<script src="assets/js/jquery.scrolly.min.js"></script> \
			<script src="assets/js/skel.min.js"></script> \
			<script src="assets/js/util.js"></script> \
			<script src="assets/js/main.js"></script> \
</body> \
</html>')

    return '\n'.join(output)



if __name__ == "__main__":
    app.run(threaded=True, host='0.0.0.0', port=80)
