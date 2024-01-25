from flask import Flask
from elasticapm.contrib.flask import ElasticAPM

app = Flask(__name__)
# TODO: Move to .env with onepassword vault
app.config['ELASTIC_APM'] = {
    'SERVICE_NAME': 'Your Service Name',
    'SERVER_URL': 'http://your-apm-server:8200',
    'SECRET_TOKEN': 'Your Secret Token',
    'DEBUG': True  # Set to False in production
}

apm = ElasticAPM(app)

@app.route('/')
def home():
    return 'Welcome to the home page!'

@app.route('/about')
def about():
    return 'This is the about page.'

if __name__ == '__main__':
    app.run()
