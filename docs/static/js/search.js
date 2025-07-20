document.addEventListener('DOMContentLoaded', function () {
    let idx = null;
    const searchInput = document.getElementById('search-input');
    const searchResults = document.getElementById('search-results');
    let documents = [];

    // Fetch the search data
    fetch('/search-index.json')
        .then(response => response.json())
        .then(data => {
            documents = data.docs;
            // Dynamically build the lunr index
            idx = lunr(function () {
                this.ref('id');
                this.field('title');
                this.field('content');

                documents.forEach(function (doc) {
                    this.add(doc);
                }, this);
            });
        })
        .catch(error => console.error('Error loading search data:', error));

    searchInput.addEventListener('keyup', function () {
        const query = this.value.trim();

        if (query.length < 2) {
            searchResults.style.display = 'none';
            return;
        }

        if (!idx) {
            return;
        }

        const results = idx.search(query);
        displayResults(results);
    });

    function displayResults(results) {
        if (results.length > 0) {
            searchResults.innerHTML = '';
            results.forEach(result => {
                // Use the documents array to find the title and path
                const doc = documents.find(d => d.id === result.ref);
                if (doc) {
                    const li = document.createElement('li');
                    const a = document.createElement('a');
                    a.href = doc.id; // The 'id' is the path
                    a.textContent = doc.title;
                    li.appendChild(a);
                    searchResults.appendChild(li);
                }
            });
            searchResults.style.display = 'block';
        } else {
            searchResults.style.display = 'none';
        }
    }

    // Hide results when clicking outside
    document.addEventListener('click', function(event) {
        if (!searchResults.contains(event.target) && event.target !== searchInput) {
            searchResults.style.display = 'none';
        }
    });
});