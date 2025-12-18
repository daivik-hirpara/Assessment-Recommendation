/**
 * SHL Assessment Recommender - Frontend Application
 */

// Always use localhost:8000 for local development
// When deploying, change this to your deployed API URL
const API_BASE_URL = 'http://localhost:8000';

const elements = {
    queryInput: document.getElementById('queryInput'),
    searchBtn: document.getElementById('searchBtn'),
    clearBtn: document.getElementById('clearBtn'),
    charCount: document.getElementById('charCount'),
    resultsSection: document.getElementById('resultsSection'),
    resultsBody: document.getElementById('resultsBody'),
    resultCount: document.getElementById('resultCount'),
    loadingState: document.getElementById('loadingState'),
    errorState: document.getElementById('errorState'),
    errorMessage: document.getElementById('errorMessage'),
    resultsTable: document.getElementById('resultsTable'),
    sampleBtns: document.querySelectorAll('.sample-btn')
};

function updateCharCount() {
    const count = elements.queryInput.value.length;
    elements.charCount.textContent = count;
}

function setLoading(isLoading) {
    elements.searchBtn.disabled = isLoading;
    elements.loadingState.classList.toggle('hidden', !isLoading);
    elements.errorState.classList.add('hidden');
    
    if (isLoading) {
        elements.resultsTable.style.display = 'none';
    }
}

function showError(message) {
    elements.errorState.classList.remove('hidden');
    elements.errorMessage.textContent = message;
    elements.resultsTable.style.display = 'none';
}

function formatTestTypes(types) {
    if (!types || types.length === 0) return '-';
    
    const typeLabels = {
        'K': { label: 'Knowledge', class: 'type-k' },
        'P': { label: 'Personality', class: 'type-p' },
        'S': { label: 'Simulation', class: 'type-s' }
    };
    
    return types
        .filter(t => t && typeLabels[t])
        .map(t => `<span class="type-badge ${typeLabels[t].class}">${t}</span>`)
        .join('');
}

function formatStatus(value) {
    if (value === 'Yes') {
        return '<span class="status-yes">✓ Yes</span>';
    }
    return '<span class="status-no">No</span>';
}

function renderResults(data) {
    const { recommendations, count } = data;
    
    elements.resultsSection.classList.remove('hidden');
    elements.resultsTable.style.display = 'block';
    elements.resultCount.textContent = `${count} result${count !== 1 ? 's' : ''}`;
    
    elements.resultsBody.innerHTML = recommendations.map((rec, index) => `
        <tr>
            <td>${index + 1}</td>
            <td>
                <a href="${rec.url}" target="_blank" rel="noopener" class="assessment-link">
                    ${rec.name}
                </a>
            </td>
            <td>${formatTestTypes(rec.test_types)}</td>
            <td>${rec.duration || '-'}</td>
            <td>${formatStatus(rec.remote_support)}</td>
            <td>${formatStatus(rec.adaptive_support)}</td>
        </tr>
    `).join('');
}

async function performSearch() {
    const query = elements.queryInput.value.trim();
    
    if (!query) {
        showError('Please enter a query or job description.');
        elements.resultsSection.classList.remove('hidden');
        return;
    }
    
    setLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/recommend`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                max_results: 10
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP error ${response.status}`);
        }
        
        const data = await response.json();
        renderResults(data);
        
    } catch (error) {
        console.error('Search error:', error);
        showError(error.message || 'Failed to get recommendations. Please try again.');
        elements.resultsSection.classList.remove('hidden');
    } finally {
        setLoading(false);
    }
}

function clearInput() {
    elements.queryInput.value = '';
    updateCharCount();
    elements.queryInput.focus();
}

function useSampleQuery(event) {
    const query = event.target.dataset.query;
    if (query) {
        elements.queryInput.value = query;
        updateCharCount();
        performSearch();
    }
}

elements.queryInput.addEventListener('input', updateCharCount);
elements.searchBtn.addEventListener('click', performSearch);
elements.clearBtn.addEventListener('click', clearInput);

elements.queryInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && event.ctrlKey) {
        performSearch();
    }
});

elements.sampleBtns.forEach(btn => {
    btn.addEventListener('click', useSampleQuery);
});

updateCharCount();

async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        console.log('API Health:', data);
    } catch (error) {
        console.warn('API not available:', error.message);
    }
}

checkHealth();
