document.addEventListener('DOMContentLoaded', () => {
    document.querySelector('textarea[name="urls"]').addEventListener('paste', function (e) {
        e.preventDefault();
        let pastedData = (e.clipboardData || window.clipboardData).getData('Text');
        let processedText = pastedData.replace(/(https?:\/\/[^\s]+)/g, "$1\n");
        document.execCommand('insertText', false, processedText);
    });

    changeInputType();
});

function changeInputType() {
    const inputType = document.getElementById("inputType").value;
    document.getElementById("multipleArticlesForm").style.display = inputType === "textarea" ? "flex" : "none";
    document.getElementById("singleArticleForm").style.display = inputType === "input" ? "flex" : "none";
}

function closeModal() {
    document.getElementById('resultModal').style.display = 'none';
}

// ----------- SINGLE ARTICLE (modale) -----------
document.getElementById('singleArticleForm').addEventListener('submit', function(event) {
    event.preventDefault();

    const btn = document.querySelector('#singleArticleForm .btn-analyze');
    btn.disabled = true;
    btn.textContent = 'Analyse en cours...';
    btn.classList.add('loading');

    const url = document.getElementById('singleUrl').value;
    
    const thresholdInputs = document.querySelectorAll('#threshold');
    const salienceInputs = document.querySelectorAll('#salience');

    const threshold = thresholdInputs[1]?.value || "";
    const salience = salienceInputs[1]?.value || "";
    
    //  -------------------
    const params = new URLSearchParams({
        url: url,
        threshold: threshold,
        salience: salience
    });

    fetch(`/submit_url?${params.toString()}`)
        .then(res => res.json())
        .then(data => {
            btn.disabled = false;
            btn.textContent = 'Analyser';
            btn.classList.remove('loading');

            if (data.error) {
                openModal('<p>' + data.error + '</p>');
            } else {
                document.getElementById('resultContainer').innerHTML = data.html;
                document.getElementById('resultModal').style.display = 'block';
            }
        })
        .catch(() => {
            btn.disabled = false;
            btn.textContent = 'Analyser';
            btn.classList.remove('loading');
            openModal('<p>Erreur réseau.</p>');
        });
});


// ----------- MULTIPLE ARTICLES (analyse uniquement, boutons après) -----------
document.getElementById('multipleArticlesForm').addEventListener('submit', function (event) {
    event.preventDefault();

    const urls = document.getElementById('multipleUrls').value.trim();
    if (!urls) return openModal('<p>Aucune URL fournie.</p>');

    const threshold = document.getElementById('threshold')?.value || "";
    const salience = document.getElementById('salience')?.value || "";

    const formData = new FormData();
    formData.append('urls', urls);
    formData.append('threshold', threshold);
    formData.append('salience', salience);


const btn = document.querySelector('#multipleArticlesForm .btn-analyze');
btn.disabled = true;
btn.textContent = 'Analyse en cours...';
btn.classList.add('loading');

fetch('/submit_urls', { method: 'POST', body: formData })
   .then(res => {
    return res.json().then(data => {
        // Réinitialiser le bouton
        btn.disabled = false;
        btn.textContent = 'Analyser';
        btn.classList.remove('loading');

        document.getElementById('exportButtons').style.display = 'flex';

        if (data.warning) {
            openModal(`<p><strong>${data.warning}</strong></p>`);
        }
    });
})
.catch(err => {
    btn.disabled = false;
    btn.textContent = 'Analyser';
    btn.classList.remove('loading');

    const message = err.message.toLowerCase();
    const customMsg = message.includes("aucun article valide")
        ? `<p><strong>Analyse terminée, mais aucun article ne correspond aux critères spécifiés.</strong><br>
            Essayez d’abaisser le <em>seuil de confiance</em> ou de <em>saillance</em>.</p>`
        : `<p>${err.message}</p>`;
    openModal(customMsg);
});



});

// ----------- EXPORT CSV -----------
function exportCSV() {
    const form = document.getElementById('multipleArticlesForm');
    const formData = new FormData(form);

    fetch('/submit_urls_csv', {
        method: 'POST',
        body: formData
    })
        .then(res => {
            if (res.ok) return res.blob();
            return res.json().then(data => { throw new Error(data.error || "Erreur inconnue"); });
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'articles_analysis.csv';
            document.body.appendChild(a);
            a.click();
            a.remove();
        })
        .catch(err => {
            openModal('<p>' + err.message + '</p>');
        });
}

// ----------- EXPORT EXCEL -----------
function exportExcel() {
    const form = document.getElementById('multipleArticlesForm');
    const formData = new FormData(form);

    fetch('/submit_urls_excel', { method: 'POST', body: formData })
        .then(res => {
            if (!res.ok) return res.json().then(data => { throw new Error(data.error); });
            return res.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = "articles_analysis.xlsx";
            document.body.appendChild(a);
            a.click();
            a.remove();
        })
        .catch(err => openModal('<p>' + err.message + '</p>'));
}

// ----------- MODALE UTILITÉ -----------
function openModal(content) {
    document.getElementById('resultContainer').innerHTML = content;
    document.getElementById('resultModal').style.display = 'block';
}
