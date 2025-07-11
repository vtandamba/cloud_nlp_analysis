import os
from flask import *
from article_processor import *
from lifespan_processor import *
from urllib.parse import urlparse
from flask_httpauth import HTTPBasicAuth
from google.oauth2 import credentials as google_credentials
from google_auth_oauthlib.flow import Flow

auth = HTTPBasicAuth()

app = Flask(__name__)
app.secret_key = os.urandom(24)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./json/my-project-9994-1685444919368-374f28ab3233.json"

@auth.verify_password
def verify_password(username, password):
    return username == 'admin' and password == 'secret'

@app.route('/')
@auth.login_required
def home():
    return render_template("index.html", results=None)

@app.route('/robots.txt')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

@app.route('/submit_urls', methods=['POST'])
@auth.login_required
def submit_urls():
    urls_input = request.form['urls']
    threshold_input = request.form.get('threshold', '').replace(',', '.')
    strict_mode = request.form.get('strict_mode') == 'on'

    try:
        threshold = float(threshold_input) if threshold_input else None
    except ValueError:
        threshold = None

    urls = [url.strip() for url in urls_input.split('\n') if url.strip()]
    results = process_articles(urls, threshold)

    filtered = [r for r in results if not r.get('error')]

    if strict_mode and threshold is not None:
        filtered = [r for r in filtered if all(c['confidence'] >= threshold for c in r['categories'])]

    if not filtered:
        message = "Aucun article ne correspond aux critères. Diminuez le seuil ou désactivez le mode strict."
        return render_template("index.html", results=f"<p class='error-message'>{message}</p>")

    csv_file_path = 'articles_analysis.csv'
    write_to_csv(filtered, csv_file_path)
    return send_file(csv_file_path, as_attachment=True, download_name='articles_analysis.csv')

@app.route('/submit_url', methods=['GET', 'POST'])
@auth.login_required
def submit_url():
    url = request.values.get('url')  # GET ou POST

    threshold_input = request.values.get('threshold', '').replace(',', '.')
    strict_mode = request.values.get('strict_mode') == 'on'

    try:
        threshold = float(threshold_input) if threshold_input else None
    except ValueError:
        threshold = None

    if not url or not is_valid_url(url):
        return jsonify({'error': 'URL invalide.'})

    html_result = process_article(url, threshold)

    if strict_mode and threshold is not None and "Confidence" not in html_result:
        return jsonify({'error': "Aucune catégorie ne dépasse le seuil spécifié."})

    return jsonify({'html': html_result})

# LIFESPAN ROUTES (inchangées)
SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']
API_SERVICE_NAME = 'searchconsole'
API_VERSION = 'v1'

@app.route('/authorize')
def authorize():
    flow = Flow.from_client_secrets_file(
        './json/client_secrets.json',
        scopes=SCOPES,
        redirect_uri=url_for('oauth2callback', _external=True))
    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    session['state'] = state
    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    state = session['state']
    flow = Flow.from_client_secrets_file(
        './json/client_secrets.json',
        scopes=SCOPES,
        state=state,
        redirect_uri=url_for('oauth2callback', _external=True))
    flow.fetch_token(authorization_response=request.url)
    session['credentials'] = credentials_to_dict(flow.credentials)
    return redirect(url_for('input_article'))

@app.route('/lifespan', methods=['GET', 'POST'])
@auth.login_required
def input_article():
    if request.method == 'POST':
        article_url = request.form.get('article_url')
        if 'credentials' not in session:
            return redirect('authorize')

        sites = get_user_sites()
        if not sites:
            return "Site non trouvé. Veuillez autoriser l'accès à Search Console."

        credentials = google_credentials.Credentials(**session['credentials'])
        total_days_with_clicks, dates_with_clicks = calculate_days_with_clicks(sites, article_url, credentials)

        if dates_with_clicks:
            start_date = min(dates_with_clicks)
            end_date = max(dates_with_clicks)
        else:
            start_date = None
            end_date = None

        return render_template('result.html', days_with_clicks=total_days_with_clicks, start_date=start_date, end_date=end_date)

    return render_template('input_article.html')

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

if __name__ == "__main__":
    app.run(debug=True)
