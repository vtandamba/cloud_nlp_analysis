import os
from flask import *
from article_processor import process_articles, process_article, write_to_csv, write_to_excel
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

# ---------- Analyse simple (un seul article)
@app.route('/submit_url', methods=['GET', 'POST'])
@auth.login_required
def submit_url():
    url = request.values.get('url')
    threshold_input = request.values.get('threshold', '').replace(',', '.')
    strict_mode = request.values.get('strict_mode') == 'on'

    try:
        threshold = float(threshold_input) if threshold_input else None
    except ValueError:
        threshold = None

    if not url or not is_valid_url(url):
        return jsonify({'error': 'URL invalide.'})

    html_result = process_article(url, threshold)
    results = process_articles([url], threshold, strict_mode)
    write_to_csv(results, 'articles_analysis.csv')

    if strict_mode and threshold is not None and "Aucune catégorie" in html_result:
        return jsonify({'error': "Aucune catégorie ne dépasse le seuil spécifié."})

    return jsonify({'html': html_result})

# ---------- Analyse multiple (sans retour de fichier direct)
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
    if not urls:
        return jsonify({'error': "Aucune URL fournie."}), 400

    results = process_articles(urls, threshold, strict_mode)

    if not any(r for r in results if not r.get('error')):
        return jsonify({'error': "Aucun article valide. Vérifiez les URLs ou diminuez le seuil."}), 400

    write_to_csv(results, 'articles_analysis.csv')
    write_to_excel(results, 'articles_analysis.xlsx')

    # ✅ Ne retourne rien à télécharger ici. Analyse uniquement.
    return jsonify({'success': True})

# ---------- Export CSV (manuel)
@app.route('/submit_urls_csv', methods=['POST'])
@auth.login_required
def submit_urls_csv():
    try:
        return send_file('articles_analysis.csv', as_attachment=True, download_name='articles_analysis.csv')
    except Exception:
        return jsonify({'error': 'Fichier CSV introuvable.'}), 500

# ---------- Export Excel (manuel)
@app.route('/submit_urls_excel', methods=['POST'])
@auth.login_required
def submit_urls_excel():
    try:
        return send_file('articles_analysis.xlsx', as_attachment=True, download_name='articles_analysis.xlsx')
    except Exception:
        return jsonify({'error': 'Fichier Excel introuvable.'}), 500

# ---------- Google Search Console ----------
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

        start_date = min(dates_with_clicks) if dates_with_clicks else None
        end_date = max(dates_with_clicks) if dates_with_clicks else None

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
