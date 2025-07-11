from google.cloud import language_v1
from newspaper import Article, ArticleException
from urllib3.exceptions import LocationParseError, SSLError
from requests.exceptions import Timeout, HTTPError, ConnectionError
import csv
from typing import List, Dict, Union


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
def process_article(url: str, threshold: float = None) -> str:
    try:
        article = Article(url)
        article.download()
        article.parse()

        title_entities = sample_analyze_entities(article.title, "fr")
        content_categories = sample_classify_text(article.text, "en")

        if threshold is not None:
            content_categories = [c for c in content_categories if c['confidence'] >= threshold]

        results_html = f"<p class='modal-title'>Titre de l'article : {article.title}</p>"

        results_html += "<div class='modal-section'>"
        results_html += "<h3 class='modal-section-title'>Analyse des entités dans le titre :</h3>"
        results_html += "<ul class='modal-list'>" + "".join(
            f"<li>{entity['name']} (Type: {entity['type']}, Saillance: {entity['salience']:.2f})</li>"
            for entity in title_entities
        ) + "</ul>"
        results_html += "</div>"

        results_html += "<div class='modal-section'>"
        results_html += "<h3 class='modal-section-title'>Catégorisation du contenu de l'article :</h3>"

        if content_categories:
            results_html += "<ul class='modal-list'>" + "".join(
                f"<li>{cat['name']} (Confidence: {cat['confidence']:.2f})</li>"
                for cat in content_categories
            ) + "</ul>"
        else:
            results_html += "<p>Aucune catégorie ne dépasse le seuil de confiance spécifié.</p>"

        results_html += "</div>"

        return results_html
    except Exception as e:
        return "<p class='error-message'>Erreur interne lors du traitement de l'article.</p>"


def process_articles(urls: List[str], threshold: float = None, strict: bool = False) -> List[Dict]:
    results = []
    for url in urls:
        try:
            article = Article(url)
            article.download()
            article.parse()

            entities = sample_analyze_entities(article.title, "fr")
            categories = sample_classify_text(article.text, "en")

            if threshold is not None:
                categories = [c for c in categories if c['confidence'] >= threshold]

            if strict and threshold is not None and not categories:
                raise ValueError("Aucune catégorie ne dépasse le seuil.")

            results.append({
                "url": url,
                "title": article.title,
                "entities": entities,
                "categories": categories,
                "error": None
            })

        except (ArticleException, LocationParseError, Timeout, HTTPError, ConnectionError, SSLError, ValueError) as e:
            results.append({
                "url": url,
                "title": "",
                "entities": [],
                "categories": [],
                "error": str(e)
            })
    return results


def write_to_csv(data: List[Dict], filename: str = 'articles_analysis.csv') -> None:
    with open(filename, mode='w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['URL', 'Titre', 'Entités (avec saillance)', 'Catégories (avec confidence)'])

        for item in data:
            if item.get('error'):
                writer.writerow([item['url'], 'ERREUR', item['error'], ''])
                continue

            entities_str = ' | '.join([
                f"{entity['name']} (Type: {entity['type']}, Saillance: {entity['salience']:.2f})"
                for entity in item['entities']
            ])

            categories_str = ' | '.join([
                f"{cat['name']} (Confidence: {cat['confidence']:.2f})"
                for cat in item['categories']
            ])

            writer.writerow([item['url'], item['title'], entities_str, categories_str])
