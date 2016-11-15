from flask import Flask, request, render_template, redirect, session, url_for
from flask.json import jsonify
import requests
from requests_oauthlib import OAuth2Session
import imaplib
import email
from bs4 import BeautifulSoup

app = Flask(__name__)
app.secret_key = 'Uber'

client_id = '838764710395-p7nk0fcig6cl27lhfs25l49sku98dfc4.apps.googleusercontent.com'
client_secret = 'c0kLkqaVfGueyxBN4OkwImEH'
redirect_uri = 'http://stackoverflow.com/questions/tagged/python'

authorization_base_url = "https://accounts.google.com/o/oauth2/auth"
token_url = "https://accounts.google.com/o/oauth2/token"
refresh_url = token_url
scope = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

@app.route("/")
def demo():
    """Step 1: User Authorization.

    Redirect the user/resource owner to the OAuth provider (i.e. Google)
    using an URL with a few key OAuth parameters.
    """
    google = OAuth2Session(client_id, scope=scope, redirect_uri=redirect_uri)
    authorization_url, state = google.authorization_url(authorization_base_url,
        # offline for refresh token
        # force to always make user click authorize
        access_type="offline", approval_prompt="force")

    # State is used to prevent CSRF, keep this for later.
    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route("/callback", methods=["GET"])
def callback():
    """ Step 3: Retrieving an access token.

    The user has been redirected back from the provider to your registered
    callback URL. With this redirection comes an authorization code included
    in the redirect URL. We will use that to obtain an access token.
    """

    google = OAuth2Session(client_id, redirect_uri=redirect_uri,
                           state=session['oauth_state'])
    token = google.fetch_token(token_url, client_secret=client_secret,
                               authorization_response=request.url)

    # We use the session as a simple DB for this example.
    session['oauth_token'] = token

    print token

    return redirect(url_for('.menu'))


@app.route('/login', methods = ['POST'])
def process():
    email_address = request.form['email']
    password = request.form['password']
    return Uber_Cost(email_address, password)

def Uber_Cost(email_address, password):

    final_cost1 = ""
    final_cost2 = ""

    cost_array = []
    output = []


    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(email_address, password)

    mail.list()
    mail.select('inbox')
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
            #print final_cost1
            cost_array.append(final_cost1)
        if final_cost2 != "":
            #print final_cost2
            cost_array.append(final_cost2)

    cost_array = list(set(cost_array))

    cost_array = [x.lstrip("$") for x in cost_array]
    cost_array = [float(x) for x in cost_array]

    total_cost = sum(cost_array)
    max_ride = max(cost_array)
    min_ride = min(cost_array)

    print ("You've taken: {} Uber rides".format(len(cost_array)))
    print ("Trip total: ${}".format(total_cost))
    print ("Most expensive ride: ${}".format(max_ride))
    print ("Least expensive ride: ${}".format(min_ride))

    output.append('You have taken ' + str(len(cost_array)) + ' Uber rides' + '<br>')
    output.append('Total Uber Cost: ' + str(total_cost) + '<br>')
    output.append('Most Expensive Ride: ' + str(max_ride) + '<br>')
    output.append('Least Expensive Ride: ' + str(min_ride) + '<br>')

    return '\n'.join(output)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
