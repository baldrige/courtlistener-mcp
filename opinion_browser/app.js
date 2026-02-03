// Key terms to highlight in opinions (at paragraph level)
const HIGHLIGHT_PATTERNS = {
    injury: [
        /\b(uninjured|injured)\s+(class\s+)?members?\b/i,
        /\binjury[- ]in[- ]fact\b/i,
        /\bArticle\s+III\s+standing\b/i,
        /\b(lack(s|ed|ing)?|establish(ed|ing)?)\s+standing\b/i,
        /\bconcrete\s+(and\s+particularized\s+)?injur(y|ies)\b/i,
        /\bconstitutional\s+standing\b/i,
        /\b(no|without)\s+injury\b/i,
        /\bstanding\s+requirement\b/i,
    ],
    rule23: [
        /\bRule\s+23(\([a-z]\)(\([0-9]\))?)?/i,
        /\bclass\s+certification\b/i,
        /\bFed(eral|\.)?\s*R(ule|\.)?\s*(of\s+)?Civ(il|\.)?\s*P(rocedure|\.)?\s*23/i,
        /\bcertif(y|ied|ication)\s+(a\s+|the\s+)?class\b/i,
        /\bclass[- ]action\s+(suit|litigation|lawsuit)?\b/i,
        /\bdeny(ing)?\s+class\s+certification\b/i,
        /\bgranting\s+class\s+certification\b/i,
    ],
    predominance: [
        /\bpredomina(nce|te|tes|tion)\b/i,
        /\bcommon\s+(questions?|issues?)\b/i,
        /\bcommonality\b/i,
        /\btypicality\b/i,
        /\bnumerosity\b/i,
        /\badequa(cy|te)\s+(of\s+)?representation\b/i,
        /\bsuperior(ity)?\b/i,
        /\bindividualized\s+(inquiry|questions?|issues?|proof)\b/i,
    ]
};

let opinions = [];
let currentOpinion = null;

// Load opinions data
async function loadOpinions() {
    try {
        const response = await fetch('opinions.json');
        opinions = await response.json();
        renderCaseList(opinions);
        updateStats();
    } catch (error) {
        console.error('Failed to load opinions:', error);
        document.getElementById('caseListContainer').innerHTML =
            '<li class="case-item">Error loading cases. Make sure opinions.json exists.</li>';
    }
}

// Render the case list sidebar
function renderCaseList(cases) {
    const container = document.getElementById('caseListContainer');
    container.innerHTML = '';

    cases.forEach((opinion, index) => {
        const li = document.createElement('li');
        li.className = 'case-item';
        li.dataset.index = index;

        const name = opinion.case_name || opinion.search_metadata?.name || 'Unknown Case';
        const date = opinion.date_filed || opinion.search_metadata?.date || '';
        const court = opinion.court || opinion.search_metadata?.court || '';
        const wordCount = opinion.word_count || 0;

        const hasPdf = opinion.pdf_url ? '<span class="pdf-badge">PDF</span>' : '';

        li.innerHTML = `
            <div class="case-name">${escapeHtml(name)} ${hasPdf}</div>
            <div class="case-info">
                <span class="case-date">${formatDate(date)}</span>
                ${court ? `<span class="case-court"> | ${escapeHtml(court)}</span>` : ''}
                ${wordCount ? `<span class="case-words"> | ${wordCount.toLocaleString()} words</span>` : ''}
            </div>
        `;

        li.addEventListener('click', () => selectCase(index));
        container.appendChild(li);
    });
}

// Select and display a case
function selectCase(index) {
    const opinion = opinions[index];
    if (!opinion) return;

    currentOpinion = opinion;

    // Update active state in list
    document.querySelectorAll('.case-item').forEach((item, i) => {
        item.classList.toggle('active', i === index);
    });

    // Update header
    const name = opinion.case_name || opinion.search_metadata?.name || 'Unknown Case';
    document.getElementById('caseName').textContent = name;

    const meta = document.getElementById('caseMeta');
    const parts = [];
    if (opinion.citation) parts.push(`<span><strong>Citation:</strong> ${escapeHtml(opinion.citation)}</span>`);
    if (opinion.date_filed) parts.push(`<span><strong>Date:</strong> ${formatDate(opinion.date_filed)}</span>`);
    if (opinion.court) parts.push(`<span><strong>Court:</strong> ${escapeHtml(opinion.court)}</span>`);
    if (opinion.judges) parts.push(`<span><strong>Judges:</strong> ${escapeHtml(opinion.judges)}</span>`);

    // External links
    if (opinion.pdf_url) {
        const pageInfo = opinion.pdf_page_count ? ` (${opinion.pdf_page_count} pages)` : '';
        parts.push(`<span><a href="${opinion.pdf_url}" target="_blank" class="pdf-link">PDF${pageInfo}</a></span>`);
    }
    if (opinion.url) {
        parts.push(`<span><a href="${opinion.url}" target="_blank">CourtListener</a></span>`);
    }
    if (opinion.google_scholar_url) {
        parts.push(`<span><a href="${opinion.google_scholar_url}" target="_blank">Google Scholar</a></span>`);
    }
    meta.innerHTML = parts.join('');

    // Render opinion text with highlights
    const content = document.getElementById('opinionContent');

    if (opinion.error) {
        content.innerHTML = `<p class="placeholder">Error loading this opinion: ${escapeHtml(opinion.error)}</p>`;
        return;
    }

    let html = '';

    // Add syllabus if present
    if (opinion.syllabus && opinion.syllabus.trim()) {
        html += `<div class="syllabus">
            <span class="syllabus-label">Syllabus</span>
            ${formatAndHighlightText(opinion.syllabus)}
        </div>`;
    }

    // Add main text
    if (opinion.text && opinion.text.trim()) {
        html += `<div class="opinion-text">${formatAndHighlightText(opinion.text)}</div>`;
    } else {
        html += `<p class="placeholder">No text available for this opinion.</p>`;
    }

    content.innerHTML = html;
    content.scrollTop = 0;
}

// Format text and apply paragraph-level highlighting
function formatAndHighlightText(text) {
    if (!text) return '';

    // Split into paragraphs on double newlines (preserve original structure)
    const paragraphs = text.split(/\n\n+/);

    return paragraphs.map(para => {
        if (!para.trim()) return '';

        // Check which highlight categories match this paragraph
        const matches = new Set();
        for (const [category, patterns] of Object.entries(HIGHLIGHT_PATTERNS)) {
            for (const pattern of patterns) {
                if (pattern.test(para)) {
                    matches.add(category);
                    break;
                }
            }
        }

        // Build CSS classes for highlighting
        let classes = 'paragraph';
        if (matches.size > 0) {
            classes += ' highlighted';
            matches.forEach(cat => classes += ` highlight-${cat}`);
        }

        // Preserve internal newlines with <br>, escape HTML
        const htmlContent = escapeHtml(para).replace(/\n/g, '<br>');
        return `<div class="${classes}">${htmlContent}</div>`;
    }).filter(p => p).join('\n');
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Format date for display
function formatDate(dateStr) {
    if (!dateStr) return '';
    try {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    } catch {
        return dateStr;
    }
}

// Update stats display
function updateStats() {
    const statsDiv = document.createElement('div');
    statsDiv.className = 'stats';

    const totalWords = opinions.reduce((sum, op) => sum + (op.word_count || 0), 0);
    const courts = [...new Set(opinions.map(op => op.court || op.search_metadata?.court).filter(Boolean))];

    statsDiv.innerHTML = `
        <strong>${opinions.length}</strong> cases |
        <strong>${totalWords.toLocaleString()}</strong> total words |
        <strong>${courts.length}</strong> courts
    `;

    const container = document.querySelector('.case-list');
    container.insertBefore(statsDiv, document.getElementById('caseListContainer'));
}

// Filter cases by search
function setupSearch() {
    const searchInput = document.getElementById('caseSearch');
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();

        if (!query) {
            renderCaseList(opinions);
            return;
        }

        const filtered = opinions.filter((op, index) => {
            const name = (op.case_name || op.search_metadata?.name || '').toLowerCase();
            const court = (op.court || op.search_metadata?.court || '').toLowerCase();
            const text = (op.text || '').toLowerCase();
            const syllabus = (op.syllabus || '').toLowerCase();

            return name.includes(query) ||
                   court.includes(query) ||
                   text.includes(query) ||
                   syllabus.includes(query);
        });

        renderCaseList(filtered);
    });
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadOpinions();
    setupSearch();
});
