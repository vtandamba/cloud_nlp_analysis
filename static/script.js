//Retour à la ligne auto dans le textarea

document.addEventListener('DOMContentLoaded', (event) => {
    document.querySelector('textarea[name="urls"]').addEventListener('paste', function(e) {
        e.preventDefault();
        let clipboardData = e.clipboardData || window.clipboardData;
        let pastedData = clipboardData.getData('Text');
        // let processedText = pastedData.replace(/(https?:\/\/)(?!www\.)([^\s]+)/g, "$1www.$2"); 
        let processedText = pastedData.replace(/(https?:\/\/[^\s]+)/g, "$1\n");

        if (document.queryCommandSupported('insertText')) {
            document.execCommand('insertText', false, processedText);
        } else {
            this.value += processedText;
        }
    });
});



// Popup modal
function analyze(event) {
    event.preventDefault(); 

    var text = document.getElementById("text").value;
    var modal = document.getElementById("resultModal");
    modal.style.display = "block";
}


function openModal(html) {
    document.getElementById('resultContainer').innerHTML = html; 
    document.getElementById('resultModal').style.display = 'block';
}

function closeModal() {
    var modal = document.getElementById("resultModal");
    modal.style.display = "none";
}

function closeModal() {
    document.getElementById('resultModal').style.display = 'none';
}


// Popup modal en cas d'erreur sur un seul article
document.getElementById('singleArticleForm').addEventListener('submit', function(event) {
    event.preventDefault(); 
    var url = document.getElementById('singleUrl').value;
    fetch(`/submit_url?url=${encodeURIComponent(url)}`)
        .then(response => response.json())
        .then(data => {
            if(data.error) {
                console.error('Error:', data.error);
            } else {
                openModal(data.html); 
            }
        })
        .catch(error => console.error('Error fetching data:', error));
});

// Popup modal en cas d'erreur pour les urls multiples
document.getElementById('multipleArticlesForm').addEventListener('submit', function(event) {
    event.preventDefault();
    var urlsElement = document.getElementById('multipleUrls');
    if (!urlsElement || !urlsElement.value) {
        openModal('<p>Erreur : Aucune URL fournie.</p>');
        return;
    }
    var urls = urlsElement.value.split('\n');
    var formData = new FormData();
    formData.append('urls', urls.join('\n'));

    fetch('/submit_urls', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if(response.ok) {
            var contentDisposition = response.headers.get('Content-Disposition');
            var filename = contentDisposition.split('filename=')[1];
            response.blob().then(blob => {
                var url = window.URL.createObjectURL(blob);
                var a = document.createElement('a');
                a.href = url;
                a.download = filename || 'download';
                a.click();
            });
        } else {
            return response.json();
        }
    })
    .then(data => {
        if(data && data.error) {
            openModal(`<p>${data.error}</p>`);
        }
    })
    .catch(error => {
        console.error('Error fetching data:', error);
        openModal('<p>Erreur interne lors du traitement de l\'article. Une partie attendue de l\'article est manquante ou inaccessible.</p>');
    });
});


// Changer le type d'input
function changeInputType() {
    var inputType = document.getElementById("inputType").value;
    var multipleArticlesForm = document.getElementById("multipleArticlesForm");
    var singleArticleForm = document.getElementById("singleArticleForm");

    if (inputType === "textarea") {
        multipleArticlesForm.style.display = "flex";
        singleArticleForm.style.display = "none";
    } else if (inputType === "input") {
        multipleArticlesForm.style.display = "none";
        singleArticleForm.style.display = "flex";
    }
}

changeInputType();

// Ouvrir la modale automatiquement si résultats présents dans HTML
window.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('resultsPresent')) {
        document.getElementById('resultModal').style.display = 'block';
    }
});



