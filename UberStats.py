import imaplib
import email
from bs4 import BeautifulSoup

final_cost1 = ""
final_cost2 = ""
mail = imaplib.IMAP4_SSL('imap.gmail.com')
mail.login('my email', 'my password')

mail.list()
mail.select('inbox')
result,data = mail.search(None, 'FROM', '"Uber Receipts"')

ids = data[0]
id_list = ids.split()
latest = id_list[5]


result,data = mail.fetch(latest, "(RFC822)")

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
    print final_cost1
if final_cost2 != "":
    print final_cost2
