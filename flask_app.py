# ========================================
# FILE 1: flask_app.py (Main Application)
# ========================================

from flask import Flask, render_template_string, request, jsonify, session
import secrets
from datetime import datetime, timezone

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Kiswahili word list
KISWAHILI_WORDS = [
    "baba", "mama", "kaka", "dada", "paka", "mbwa", "taka", "hapa", "pale",
    "kule", "lala", "nana", "tano", "sita", "saba", "nane", "tisa", "kumi",
    "maji", "nazi", "pesa", "basi", "hali", "rais", "sisi", "wiki", "vita",
    "kazi", "wazi", "hizi", "huko", "yako", "yangu", "jina", "kina", "moja",
    "mbili", "tatu", "nchi", "mchi", "chai", "aina", "asali", "baada", "nyama",
    "shika", "amani", "barua", "bibi", "kitabu", "rafiki", "familia", "chakula",
    "nyumbani", "shule", "habari", "safari", "bahari", "samaki", "ndege",
    "tembo", "twiga", "simba", "cheza", "penda", "soma", "andika", "sema",
    "sikia", "tazama", "kimya", "furaha", "uzuri", "jambo", "karibu", "kwaheri",
    "mwalimu", "mwanafunzi", "marafiki", "watoto", "wazazi", "nyumba",
    "shangazi", "mjomba", "kijana", "mzazi", "wasiwasi",
    "kaka", "mama", "baba", "kama", "kaba", "kaaba", "chama", "haba", "hama", "hema", "abee", "acha",
    "achama", "ache", "adaa", "amaa", "amka", "mamba", "babe", "bacha", "baka", "bamba", "bakaa", "makaa",
    "bambam", "beba", "bebi", "beka", "bembe", "bemba", "chaa", "chacha", "chaka", "cheche",
    "chemba", "chembe", "kabaka", "kacha", "kamba", "kame", "kema", "kemba", "keba",
]

PUZZLES = [
    {"center": "A", "outer": ["M", "C", "E", "K", "B", "H"]},
    {"center": "I", "outer": ["K", "T", "A", "B", "S", "Z"]},
]

def get_daily_puzzle():
    """Get the puzzle for today based on date"""
    # Use UTC date to ensure everyone gets the same puzzle
    today = datetime.now(timezone.utc).date()
    # Use days since epoch to get a consistent index
    days_since_epoch = (today - datetime(2025, 1, 1).date()).days
    puzzle_index = days_since_epoch % len(PUZZLES)
    return PUZZLES[puzzle_index]

def get_today_key():
    """Get a unique key for today's date"""
    return datetime.now(timezone.utc).strftime('%Y-%m-%d')

def get_valid_words(center, outer_letters):
    all_letters = set([center.lower()] + [l.lower() for l in outer_letters])
    valid = []
    for word in KISWAHILI_WORDS:
        if len(word) < 4:
            continue
        if center.lower() not in word:
            continue
        if all(char in all_letters for char in word):
            valid.append(word)
    return valid

def get_rank(score, total_possible):
    if total_possible == 0:
        return "Beginner"
    percentage = (score / (total_possible * 5)) * 100
    if percentage >= 100:
        return "Bingwa Mkuu"
    elif percentage >= 70:
        return "Bingwa"
    elif percentage >= 50:
        return "Hodari"
    elif percentage >= 40:
        return "Mzuri"
    elif percentage >= 25:
        return "Vizuri"
    elif percentage >= 15:
        return "Mbaya si"
    elif percentage >= 8:
        return "Mwanzo Mzuri"
    else:
        return "Mwanzo"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="sw">
<head>

  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-7910716152647155"
     crossorigin="anonymous"></script>

    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Spelling Bee - Kiswahili</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f7f7f7;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 1fr 400px;
            gap: 30px;
        }
        @media (max-width: 968px) {
            .container { 
                grid-template-columns: 1fr;
                grid-template-rows: auto auto auto auto;
            }
            .header { 
                grid-column: 1;
                grid-row: 1;
            }
            .game-area {
                grid-column: 1;
                grid-row: 3;
            }
            .sidebar {
                grid-column: 1;
                grid-row: 2;
                margin-bottom: 0;
            }
        }
        .header {
            grid-column: 1 / -1;
            text-align: center;
            margin-bottom: 20px;
        }
        h1 { font-size: 2.5em; margin-bottom: 10px; }
        .subtitle { color: #666; font-size: 1.1em; }
        .daily-badge {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 8px 20px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
            margin-top: 10px;
        }
        .game-area {
            background: white;
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .rank {
            text-align: center;
            margin-bottom: 30px;
            padding: 15px;
            background: #fef3c7;
            border-radius: 10px;
        }
        .rank-title { font-size: 0.9em; color: #92400e; margin-bottom: 5px; }
        .rank-name { font-size: 1.5em; font-weight: bold; color: #f59e0b; }
        .progress { display: flex; gap: 3px; margin-top: 10px; }
        .progress-dot {
            flex: 1;
            height: 8px;
            background: #fde68a;
            border-radius: 4px;
        }
        .progress-dot.filled { background: #f59e0b; }
        .hexagon-container {
            display: flex;
            justify-content: center;
            margin: 40px 0;
            position: relative;
        }
        .hex-grid { position: relative; width: 280px; height: 250px; }
        .hexagon {
            position: absolute;
            width: 80px;
            height: 80px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.8em;
            font-weight: bold;
            cursor: pointer;
            user-select: none;
            transition: all 0.2s;
        }
       .hex-shape {
       width: 100%;
       height: 100%;
       background: #e8e8e8;
       clip-path: polygon(
        25% 0%,    /* Top left (pushed out) */
        75% 0%,    /* Top right (pushed out) */
        100% 50%,  /* Mid right */
        75% 100%,  /* Bottom right */
        25% 100%,  /* Bottom left */
        0% 50%     /* Mid left */
       );
       display: flex;
       align-items: center;
       justify-content: center;
       transition: all 0.2s ease;
       position: relative;
       }

        .hexagon:hover .hex-shape { background: #d4d4d4; transform: scale(1.05);
         border-color: #b0b0b0; }
        .hexagon.center .hex-shape { background: #fbbf24;  border-color: #f59e0b;}
        .hexagon.center:hover .hex-shape { background: #f59e0b;
         border-color: #d97706; }
        .hex-center { top: 100px; left: 100px; }
        .hex-top { top: 15px; left: 100px; }
        .hex-top-right { top: 60px; left: 168px; }
        .hex-bottom-right { top: 145px; left: 168px; }
        .hex-bottom { top: 185px; left: 100px; }
        .hex-bottom-left { top: 145px; left: 32px; }
        .hex-top-left { top: 55px; left: 32px; }
        .input-area { text-align: center; margin-bottom: 5px; }
        @media (max-width: 968px) {
            .input-area { margin-bottom: 16px; }
        }
        .word-display {
            font-size: 2em;
            height: 17px;
            display: flex;
            align-items: center;
            justify-content: center;
            letter-spacing: 3px;
            font-weight: 500;
            margin-bottom: 1px;
        }
        .controls { display: flex; gap: 10px; justify-content: center; }
        button {
            padding: 12px 24px;
            font-size: 1em;
            border: 2px solid #ddd;
            background: white;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.2s;
            font-weight: 600;
        }
        button:hover { background: #f5f5f5; border-color: #999; }
        .btn-enter { background: #000; color: white; border-color: #000; }
        .btn-enter:hover { background: #333; }
        .message {
            text-align: center;
            padding: 10px;
            margin: 10px 0;
            border-radius: 8px;
            font-weight: 600;
            height: 5px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .success { background: #d1fae5; color: #065f46; }
        .error { background: #fee2e2; color: #991b1b; }
        .info { background: #dbeafe; color: #1e40af; }
        .sidebar {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            max-height: 600px;
            overflow-y: auto;
        }
        .score-section { margin-bottom: 30px; }
        .score-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            padding: 10px;
            background: #f9fafb;
            border-radius: 8px;
        }
        .score-label { color: #666; }
        .score-value { font-weight: bold; color: #000; }
        .found-words-section h3 { margin-bottom: 15px; color: #333; }
        .word-item {
            padding: 10px;
            margin-bottom: 1px;
            background: #f9fafb;
            border-radius: 8px;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .word-text { font-weight: 600; text-transform: uppercase; }
        .next-puzzle {
            background: #eff6ff;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            margin-top: 20px;
        }
        .next-puzzle-text {
            font-size: 0.9em;
            color: #1e40af;
            font-weight: 600;
        }

        /* ACCORDION STYLES - HIDDEN BY DEFAULT (DESKTOP) */
        .accordion-header,
        .accordion-content,
        .words-grid,
        .accordion-chevron,
        .accordion-words-preview,
        .accordion-summary {
            display: none;
        }

        /* MOBILE ACCORDION STYLES (≤968px) */
        @media (max-width: 968px) {
            .sidebar {
                padding: 0;
                background: transparent;
                box-shadow: none;
                max-height: none;
                overflow-y: visible;
                margin-bottom: 16px;
            }

            .score-section {
                background: white;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 16px;
                border: 1px solid #e5e7eb;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }

            .found-words-section {
                display: none;
            }

            .next-puzzle {
                background: #eff6ff;
                padding: 15px;
                border-radius: 10px;
                text-align: center;
                margin-top: 16px;
                border: 1px solid #dbeafe;
            }

            /* ACCORDION HEADER */
            .accordion-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 14px 16px;
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
                cursor: pointer;
                user-select: none;
                transition: background-color 0.2s, border-radius 0.3s;
                margin-bottom: 16px;
                min-height: 48px;
            }

            .accordion-header:hover {
                background: #fafafa;
            }

            .accordion-header.expanded {
                border-bottom-left-radius: 0;
                border-bottom-right-radius: 0;
                margin-bottom: 0;
            }

            .accordion-words-preview {
                display: flex;
                gap: 12px;
                overflow-x: auto;
                overflow-y: hidden;
                flex: 1;
                scroll-behavior: smooth;
                scrollbar-width: none;
                -ms-overflow-style: none;
            }

            .accordion-words-preview::-webkit-scrollbar {
                display: none;
            }

            .accordion-preview-word {
                flex-shrink: 0;
                white-space: nowrap;
                font-size: 15px;
                font-weight: 500;
                color: #333;
            }

            .accordion-preview-word.bold {
                font-weight: 700;
            }

            .accordion-chevron {
                display: flex;
                flex-shrink: 0;
                margin-left: 12px;
                font-size: 20px;
                color: #666;
                transition: transform 0.3s ease;
                align-items: center;
                justify-content: center;
            }

            .accordion-chevron.expanded {
                transform: rotate(180deg);
            }

            /* ACCORDION CONTENT */
            .accordion-content {
                display: none;
                max-height: 0;
                overflow: hidden;
                background: white;
                border: 1px solid #e5e7eb;
                border-top: none;
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
                transition: max-height 0.3s ease;
                margin-bottom: 16px;
            }

            .accordion-content.expanded {
                display: block;
                max-height: 400px;
                overflow-y: auto;
            }

            .accordion-summary {
                display: none;
                font-size: 16px;
                font-weight: 600;
                color: #333;
                padding: 14px 16px;
            }

            .accordion-summary.expanded {
                display: block;
            }

            /* WORDS GRID */
            .words-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                padding: 0;
            }

            .word-cell {
                padding: 12px;
                font-size: 15px;
                font-weight: 500;
                color: #1f2937;
                text-transform: uppercase;
                text-align: left;
                line-height: 1.4;
                border-bottom: 1px solid #e5e7eb;
            }

            .word-cell:nth-child(odd) {
                border-right: 1px solid #e5e7eb;
            }

            .word-cell:nth-child(even) {
                border-right: none;
            }

            .word-cell.bold-word {
                font-weight: 700;
            }

            .word-cell:nth-last-child(2),
            .word-cell:nth-last-child(1) {
                border-bottom: none;
            }
        }

    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🐝 Spelling Bee - Kiswahili</h1>
            <p class="subtitle">Tengeneza maneno mengi iwezekanavyo!</p>
            <div class="daily-badge">📅 Changamoto ya Leo: {{ today_date }}</div>
        </div>

        <div class="game-area">
            <div class="rank">
                <div class="rank-title">Cheo Chako</div>
                <div class="rank-name" id="rank">{{ rank }}</div>
                <div class="progress" id="progress"></div>
            </div>
            
            <div class="input-area">
                <div class="word-display" id="currentWord"></div>
                <div id="message" class="message"></div>
            </div>

            <div class="hexagon-container">
                <div class="hex-grid">
                    <div class="hexagon center hex-center" data-letter="{{ center }}" onclick="addLetter('{{ center }}')">
                        <div class="hex-shape">{{ center }}</div>
                    </div>
                    {% for letter in outer %}
                    <div class="hexagon hex-{{ ['top', 'top-right', 'bottom-right', 'bottom', 'bottom-left', 'top-left'][loop.index0] }}"
                         data-letter="{{ letter }}" onclick="addLetter('{{ letter }}')">
                        <div class="hex-shape">{{ letter }}</div>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <div class="controls">
                <button onclick="deleteLetter()">Futa</button>
                <button onclick="shuffle()">🔄 Changanya</button>
                <button class="btn-enter" onclick="submitWord()">Wasilisha</button>
            </div>
        </div>

        <div class="sidebar">
            <div class="score-section">
                <div class="score-item">
                    <span class="score-label">Maneno</span>
                    <span class="score-value" id="wordCount">{{ found_count }}</span>
                </div>
                <div class="score-item">
                    <span class="score-label">Alama</span>
                    <span class="score-value" id="score">{{ score }}</span>
                </div>
                <div class="score-item">
                    <span class="score-label">Zinazowezekana</span>
                    <span class="score-value">{{ total_possible }}</span>
                </div>
            </div>

            <!-- ACCORDION COMPONENT FOR MOBILE -->
            <div class="accordion-header" role="button" aria-expanded="false" aria-label="Toggle found words" tabindex="0" onclick="toggleAccordion()" onkeypress="toggleAccordionKeyboard(event)">
                <div class="accordion-words-preview" id="wordsPreview">
                    {% for word in found_words %}
                    <span class="accordion-preview-word{% if word|length >= 6 %} bold{% endif %}">{{ word }}</span>
                    {% endfor %}
                </div>
                <div class="accordion-chevron" id="accordionChevron">▼</div>
            </div>

            <div class="accordion-content" id="accordionContent">
                <div class="accordion-summary" id="accordionSummary">
                    You have found <span id="wordCountSummary">{{ found_count }}</span> words
                </div>
                <div class="words-grid" id="wordsGrid">
                    {% for word in found_words %}
                    <div class="word-cell{% if word|length >= 6 %} bold-word{% endif %}">{{ word }}</div>
                    {% endfor %}
                </div>
            </div>

            <div class="found-words-section">
                <h3>Maneno Yaliyopatikana ({{ found_count }})</h3>
                <div id="foundWords">
                    {% for word in found_words %}
                    <div class="word-item">
                        <span class="word-text">{{ word }}</span>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <div class="next-puzzle">
                <div class="next-puzzle-text">⏰ Puzzle mpya kesho!</div>
            </div>
        </div>
    </div>

    <script>
        let currentWord = '';
        const centerLetter = '{{ center }}'.toLowerCase();

        function addLetter(letter) {
            currentWord += letter.toLowerCase();
            updateDisplay();
        }

        function deleteLetter() {
            currentWord = currentWord.slice(0, -1);
            updateDisplay();
        }

        function updateDisplay() {
            document.getElementById('currentWord').textContent = currentWord.toUpperCase();
        }

        function shuffle() {
            const hexagons = document.querySelectorAll('.hexagon:not(.center)');
            const positions = ['top', 'top-right', 'bottom-right', 'bottom', 'bottom-left', 'top-left'];
            const letters = Array.from(hexagons).map(h => h.dataset.letter);

            for (let i = letters.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [letters[i], letters[j]] = [letters[j], letters[i]];
            }

            hexagons.forEach((hex, i) => {
                hex.dataset.letter = letters[i];
                hex.querySelector('.hex-shape').textContent = letters[i];
                hex.className = 'hexagon hex-' + positions[i];
                hex.onclick = () => addLetter(letters[i]);
            });
        }

        function showMessage(text, type) {
            const msgDiv = document.getElementById('message');
            msgDiv.textContent = text;
            msgDiv.className = 'message ' + type;
            if (type !== 'info') {
                setTimeout(() => {
                    msgDiv.textContent = '';
                    msgDiv.className = 'message';
                }, 3000);
            }
        }

        function submitWord() {
            if (currentWord.length < 4) {
                showMessage('Neno liwe na herufi 4 au zaidi!', 'error');
                return;
            }

            if (!currentWord.includes(centerLetter)) {
                showMessage(`Lazima utumie herufi "${centerLetter.toUpperCase()}"!`, 'error');
                return;
            }

            fetch('/submit', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({word: currentWord})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    showMessage(data.message, 'success');
                    document.getElementById('wordCount').textContent = data.found_count;
                    document.getElementById('score').textContent = data.score;
                    document.getElementById('rank').textContent = data.rank;

                    const wordList = document.getElementById('foundWords');
                    const wordItem = document.createElement('div');
                    wordItem.className = 'word-item';
                    wordItem.innerHTML = `<span class="word-text">${currentWord.toUpperCase()}</span>`;
                    wordList.insertBefore(wordItem, wordList.firstChild);

                    // Update accordion
                    const words = [];
                    document.querySelectorAll('.word-cell').forEach(cell => {
                        words.push(cell.textContent.toLowerCase());
                    });
                    words.unshift(currentWord.toLowerCase());
                    updateAccordion(words);

                    updateProgress(data.progress);
                } else {
                    showMessage(data.message, 'error');
                }
                currentWord = '';
                updateDisplay();
            });
        }

        function updateProgress(progress) {
            const progressDiv = document.getElementById('progress');
            progressDiv.innerHTML = '';
            for (let i = 0; i < 10; i++) {
                const dot = document.createElement('div');
                dot.className = 'progress-dot' + (i < progress ? ' filled' : '');
                progressDiv.appendChild(dot);
            }
        }

        document.addEventListener('keydown', (e) => {
            const key = e.key.toLowerCase();
            const allLetters = [centerLetter, ...{{ outer | tojson }}].map(l => l.toLowerCase());

            if (allLetters.includes(key)) {
                addLetter(key);
            } else if (e.key === 'Backspace') {
                deleteLetter();
            } else if (e.key === 'Enter') {
                submitWord();
            }
        });

        // ACCORDION FUNCTIONS
        function toggleAccordion() {
            const header = document.querySelector('.accordion-header');
            const content = document.getElementById('accordionContent');
            const chevron = document.getElementById('accordionChevron');
            const preview = document.querySelector('.accordion-words-preview');
            const summary = document.getElementById('accordionSummary');
            
            const isExpanded = content.classList.contains('expanded');
            
            if (isExpanded) {
                content.classList.remove('expanded');
                header.classList.remove('expanded');
                chevron.classList.remove('expanded');
                preview.style.display = 'flex';
                summary.classList.remove('expanded');
                header.setAttribute('aria-expanded', 'false');
            } else {
                content.classList.add('expanded');
                header.classList.add('expanded');
                chevron.classList.add('expanded');
                preview.style.display = 'none';
                summary.classList.add('expanded');
                header.setAttribute('aria-expanded', 'true');
            }
        }

        function toggleAccordionKeyboard(event) {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                toggleAccordion();
            }
        }

        function updateAccordion(words) {
            const preview = document.querySelector('.accordion-words-preview');
            const grid = document.getElementById('wordsGrid');
            const countSpan = document.getElementById('wordCountSummary');
            
            if (!preview || !grid) return;
            
            // Clear and update preview
            preview.innerHTML = '';
            words.forEach(word => {
                const span = document.createElement('span');
                span.className = 'accordion-preview-word';
                if (word.length >= 6) {
                    span.classList.add('bold');
                }
                span.textContent = word.toUpperCase();
                preview.appendChild(span);
            });
            
            // Update count
            if (countSpan) {
                countSpan.textContent = words.length;
            }
            
            // Update grid
            grid.innerHTML = '';
            words.forEach(word => {
                const cell = document.createElement('div');
                cell.className = 'word-cell';
                if (word.length >= 6) {
                    cell.classList.add('bold-word');
                }
                cell.textContent = word.toUpperCase();
                grid.appendChild(cell);
            });
        }

        updateProgress({{ progress }});

    </script>
</body>
</html>
"""

@app.route('/')
def index():
    today_key = get_today_key()

    # Reset session if it's a new day
    if session.get('date') != today_key:
        session.clear()
        session['date'] = today_key
        session['found_words'] = []
        session['score'] = 0

    puzzle = get_daily_puzzle()
    valid_words = get_valid_words(puzzle['center'], puzzle['outer'])
    rank = get_rank(session['score'], len(valid_words))
    progress = min(10, int((len(session['found_words']) / max(1, len(valid_words))) * 10))

    return render_template_string(
        HTML_TEMPLATE,
        center=puzzle['center'],
        outer=puzzle['outer'],
        found_words=session['found_words'],
        found_count=len(session['found_words']),
        score=session['score'],
        total_possible=len(valid_words),
        rank=rank,
        progress=progress,
        today_date=datetime.now(timezone.utc).strftime('%d %B %Y')
    )

@app.route('/submit', methods=['POST'])
def submit_word():
    today_key = get_today_key()

    # Ensure we're still on the same day
    if session.get('date') != today_key:
        session.clear()
        session['date'] = today_key
        session['found_words'] = []
        session['score'] = 0

    data = request.json
    word = data.get('word', '').lower()
    puzzle = get_daily_puzzle()

    if word in session.get('found_words', []):
        return jsonify({'success': False, 'message': '✗ Tayari umeandika neno hili!'})

    if len(word) < 4:
        return jsonify({'success': False, 'message': '✗ Neno liwe na herufi 4 au zaidi!'})

    if puzzle['center'].lower() not in word:
        return jsonify({'success': False, 'message': f'✗ Lazima utumie herufi "{puzzle["center"]}"!'})

    all_letters = set([puzzle['center'].lower()] + [l.lower() for l in puzzle['outer']])
    if not all(char in all_letters for char in word):
        return jsonify({'success': False, 'message': '✗ Tumia herufi zilizopo tu!'})

    if word not in KISWAHILI_WORDS:
        return jsonify({'success': False, 'message': '✗ Neno si sahihi!'})

    if 'found_words' not in session:
        session['found_words'] = []
    session['found_words'].append(word)
    session['score'] = session.get('score', 0) + len(word)
    session.modified = True

    valid_words = get_valid_words(puzzle['center'], puzzle['outer'])
    rank = get_rank(session['score'], len(valid_words))
    progress = min(10, int((len(session['found_words']) / max(1, len(valid_words))) * 10))

    return jsonify({
        'success': True,
        'message': f'✓ Vizuri! +{len(word)} alama',
        'found_count': len(session['found_words']),
        'score': session['score'],
        'rank': rank,
        'progress': progress
    })

if __name__ == "__main__":
    app.run(debug=True)
