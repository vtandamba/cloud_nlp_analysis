from google.cloud import language_v1
from newspaper import Article, ArticleException
from urllib3.exceptions import LocationParseError, SSLError
from requests.exceptions import Timeout, HTTPError, ConnectionError
import csv
from typing import List, Dict, Union

# Analyse des entités avec saillance
def sample_analyze_entities(text_content: str, language_code: str = "fr") -> List[Dict[str, Union[str, float]]]:
    client = language_v1.LanguageServiceClient()
    document = language_v1.Document(
        content=text_content,
        type_=language_v1.Document.Type.PLAIN_TEXT,
        language=language_code
    )
    response = client.analyze_entities(
        request={"document": document, "encoding_type": language_v1.EncodingType.UTF8}
    )

    return [
        {
            "name": entity.name,
            "type": language_v1.Entity.Type(entity.type_).name,
            "salience": float(entity.salience)
        } for entity in response.entities
    ]

# Classification des catégories (en anglais uniquement)
def sample_classify_text(text_content: str, language_code: str = "en") -> List[Dict[str, Union[str, float]]]:
    client = language_v1.LanguageServiceClient()
    document = language_v1.Document(
        content=text_content,
        type_=language_v1.Document.Type.PLAIN_TEXT,
        language=language_code
    )
    response = client.classify_text(request={"document": document})

    return [
        {"name": category.name, "confidence": float(category.confidence)}
        for category in response.categories
    ]

# Traitement de plusieurs articles
def process_articles(urls: List[str], threshold: float = 0.45) -> List[Dict[str, Union[str, List[Dict], None]]]:
    data = []
    for url in urls:
        try:
            article = Article(url)
            article.download()
            article.parse()

            entities = sample_analyze_entities(article.title, "fr")
            categories = [
                c for c in sample_classify_text(article.text, "en")
                if threshold is None or c['confidence'] >= threshold
            ]

            data.append({
                'url': url,
                'title': article.title,
                'entities': entities,
                'categories': categories,
                'error': None
            })
        except (ArticleException, LocationParseError, Timeout, HTTPError, ConnectionError, SSLError, ValueError, IOError, KeyError, AttributeError) as e:
            data.append({
                'url': url,
                'error': str(e)
            })
    return data

# Export CSV
def write_to_csv(data: List[Dict], filename: str = 'articles_analysis.csv') -> None:
    with open(filename, mode='w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['Titre', 'Entités (avec saillance)', 'Catégories'])
        for item in data:
            if item.get('error'):
                continue
            entities_str = ' | '.join([
                f"{entity['name']} (Type: {entity['type']}, Saillance: {entity['salience']:.2f})"
                for entity in item['entities']
            ])
            categories_str = ' | '.join([
                f"{category['name']} (Confidence: {category['confidence']:.2f})"
                for category in item['categories']
            ])
            writer.writerow([item['title'], entities_str, categories_str])

# Traitement d'un seul article
def process_article(url: str, threshold: float = 0.45) -> str:
    try:
        article = Article(url)
        article.download()
        article.parse()

        title_entities_html = sample_analyze_entities(article.title, "fr")
        content_categories_html = [
            c for c in sample_classify_text(article.text, "en")
            if threshold is None or c['confidence'] >= threshold
        ]

        results_html = f"<p class='modal-title'>Titre de l'article : {article.title}</p>"

        results_html += "<div class='modal-section'>"
        results_html += "<h3 class='modal-section-title'>Analyse des entités dans le titre :</h3>"
        results_html += "<ul class='modal-list'>" + "".join(
            f"<li>{entity['name']} (Type: {entity['type']}, Saillance: {entity['salience']:.2f})</li>"
            for entity in title_entities_html
        ) + "</ul></div>"

        results_html += "<div class='modal-section'>"
        results_html += "<h3 class='modal-section-title'>Catégorisation du contenu de l'article :</h3>"
        results_html += "<ul class='modal-list'>" + "".join(
            f"<li>{category['name']} (Confidence: {category['confidence']:.2f})</li>"
            for category in content_categories_html
        ) + "</ul></div>"

        return results_html

    except Exception as e:
        return "<p class='error-message'>Erreur interne lors du traitement de l'article. Une partie attendue de l'article est manquante ou inaccessible.</p>"
