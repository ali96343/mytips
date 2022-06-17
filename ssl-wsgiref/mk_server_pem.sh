# openssl req -new -x509 -keyout server.pem -out server.pem -days 365 -nodes

openssl \
 req -x509 \
 -keyout server.pem \
 -out server.pem \
 -days 365 \
 -nodes \
 -subj "/C=RU/ST=Saint Petersburg/O=SPB/OU=AliBsk/CN=localhost/emailAddress=ab96343@gmail.com"

# openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
# -subj "/C=RU/ST=NRW/L=Earth/O=CompanyName/OU=IT/CN=www.example.com/emailAddress=email@example.com"

# -subj "/C=US/ST=NRW/L=Earth/O=CompanyName/OU=IT/CN=www.example.com/emailAddress=email@example.com"
# subject=C = RU, ST = Saint Petersburg, O = SPB, OU = AliBsk, CN = localhost
# https://www.devdungeon.com/content/creating-self-signed-ssl-certificates-openssl

