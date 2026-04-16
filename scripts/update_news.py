#!/usr/bin/env python3
"""
AI Briefing Daily News Curator
Generates a daily executive briefing with curated AI news for Danske Spil CEO
"""

import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from anthropic import Anthropic

# ============================================================================
# CONSTANTS
# ============================================================================

MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 8000
CET = timezone(timedelta(hours=2))
UGEDAGE = ["Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag", "Lørdag", "Søndag"]
MAANEDER = [
    "januar", "februar", "marts", "april", "maj", "juni",
    "juli", "august", "september", "oktober", "november", "december"
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_danish_date():
    """Get current date in Danish format with CET timezone."""
    now = datetime.now(CET)
    weekday = UGEDAGE[now.weekday()]
    day = now.day
    month = MAANEDER[now.month - 1]
    year = now.year
    time_str = now.strftime("%H:%M")

    full = f"{weekday} d. {day}. {month} {year}"

    return {
        "weekday": weekday,
        "day": day,
        "month": month,
        "year": year,
        "full": full,
        "time": time_str
    }

def escape_html(text):
    """Escape HTML special characters."""
    if not text:
        return ""
    text = str(text)
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    return text

def generate_top_story_html(story):
    """Generate HTML for a top story card."""
    priority = story.get("priority", "green").lower()
    priority_colors = {
        "red": "#ef4444",
        "amber": "#f59e0b",
        "green": "#10b981"
    }
    color = priority_colors.get(priority, "#10b981")

    priority_text = {"red": "KRITISK", "amber": "VIGTIG", "green": "VÆRD AT KENDE"}.get(priority, "VÆRD AT KENDE")

    gambling_badge = '<span style="display: inline-block; background: linear-gradient(135deg, #c2185b, #880e4f); color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; margin-left: 8px;">🎰 GAMBLING</span>' if story.get("is_gambling") else ""

    html = f"""
    <div style="border-left: 4px solid {color}; padding: 16px; background: white; border-radius: 8px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.08);">
        <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background: {color}; margin-right: 8px;"></span>
            <span style="font-size: 11px; font-weight: 700; color: {color}; text-transform: uppercase; letter-spacing: 0.5px;">{priority_text}</span>
            {gambling_badge}
        </div>
        <h3 style="margin: 8px 0; font-size: 16px; color: #1a1a2e; font-weight: 600;">{escape_html(story.get('title', ''))}</h3>
        <p style="margin: 8px 0; font-size: 14px; color: #64748b; line-height: 1.5;">{escape_html(story.get('description', ''))}</p>
        <p style="margin: 8px 0; font-size: 13px; color: #4f46e5; font-style: italic;"><strong>Vigtig for CEO:</strong> {escape_html(story.get('relevance_tag', ''))}</p>
        <a href="{escape_html(story.get('url', '#'))}" target="_blank" style="display: inline-block; margin-top: 8px; font-size: 13px; color: #4f46e5; text-decoration: none; font-weight: 500;">Læs mere →</a>
    </div>
    """
    return html

def generate_item_html(item, icon, source_key, duration_key):
    """Generate HTML for a content item (video, podcast, or article)."""
    gambling_badge = '<span style="display: inline-block; background: linear-gradient(135deg, #c2185b, #880e4f); color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; margin-top: 8px;">🎰 GAMBLING</span>' if item.get("is_gambling") else ""

    source = escape_html(item.get(source_key, ""))
    duration = escape_html(item.get(duration_key, ""))

    html = f"""
    <div class="content-card" style="background: white; border-radius: 8px; padding: 16px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); transition: transform 0.3s ease, box-shadow 0.3s ease; display: flex; flex-direction: column;">
        <div style="font-size: 24px; margin-bottom: 8px;">{icon}</div>
        <h4 style="margin: 8px 0; font-size: 14px; color: #1a1a2e; font-weight: 600; line-height: 1.4;">{escape_html(item.get('title', ''))}</h4>
        <p style="margin: 8px 0; font-size: 12px; color: #64748b; line-height: 1.5; flex-grow: 1;">{escape_html(item.get('summary', ''))}</p>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px; padding-top: 10px; border-top: 1px solid #e2e8f0;">
            <span style="font-size: 11px; color: #64748b; font-weight: 500;">{source}</span>
            <span style="font-size: 11px; color: #64748b;">⏱️ {duration}</span>
        </div>
        {gambling_badge}
        <a href="{escape_html(item.get('url', '#'))}" target="_blank" style="display: inline-block; margin-top: 10px; font-size: 12px; color: #4f46e5; text-decoration: none; font-weight: 500;">Åbn →</a>
    </div>
    """
    return html

def generate_html(data, date_info):
    """Generate complete responsive HTML page."""
    top_stories_html = "".join(generate_top_story_html(story) for story in data.get("top_stories", []))

    youtube_items = "".join(
        generate_item_html(item, "📹", "channel", "duration")
        for item in data.get("youtube", [])
    )

    podcast_items = "".join(
        generate_item_html(item, "🎙️", "show", "duration")
        for item in data.get("podcasts", [])
    )

    article_items = "".join(
        generate_item_html(item, "📰", "source", "read_time")
        for item in data.get("articles", [])
    )

    html = f"""<!DOCTYPE html>
<html lang="da">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Briefing - Dagligt Executive Briefing</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #f0f2f5;
            --accent: #4f46e5;
            --text-primary: #1a1a2e;
            --text-secondary: #64748b;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg);
            color: var(--text-primary);
            line-height: 1.6;
        }}

        header {{
            background: linear-gradient(135deg, #1e1b4b 0%, #312e81 40%, #4338ca 100%);
            color: white;
            padding: 32px 24px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }}

        .header-container {{
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .header-title {{
            display: flex;
            flex-direction: column;
        }}

        .logo {{
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 4px;
            letter-spacing: -0.5px;
        }}

        .date-display {{
            font-size: 13px;
            opacity: 0.9;
        }}

        .header-actions {{
            display: flex;
            gap: 16px;
            align-items: center;
        }}

        .refresh-btn {{
            background: rgba(255, 255, 255, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.3);
            color: white;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.3s ease;
        }}

        .refresh-btn:hover {{
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
        }}

        .refresh-btn.loading {{
            opacity: 0.6;
            pointer-events: none;
        }}

        .last-updated {{
            font-size: 12px;
            opacity: 0.8;
        }}

        main {{
            max-width: 1200px;
            margin: 32px auto;
            padding: 0 24px;
        }}

        .briefing-section {{
            background: white;
            border-radius: 12px;
            padding: 32px;
            margin-bottom: 32px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            animation: fadeIn 0.6s ease;
        }}

        .briefing-section h2 {{
            font-size: 24px;
            margin-bottom: 16px;
            color: #1e1b4b;
            border-bottom: 3px solid var(--accent);
            padding-bottom: 12px;
        }}

        .briefing-text {{
            font-size: 15px;
            line-height: 1.8;
            color: var(--text-secondary);
            margin-bottom: 16px;
        }}

        .expand-btn {{
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            background: var(--accent-light, #e0e7ff);
            color: var(--accent, #4f46e5);
            border: none;
            padding: 0.45rem 1rem;
            border-radius: 8px;
            font-size: 0.82rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            font-family: inherit;
            margin-bottom: 1.5rem;
        }}
        .expand-btn:hover {{
            background: var(--accent, #4f46e5);
            color: white;
        }}
        .expand-btn .arrow {{
            transition: transform 0.3s;
            font-size: 0.7rem;
        }}
        .expand-btn.open .arrow {{
            transform: rotate(180deg);
        }}
        .extended-briefing {{
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.5s ease, opacity 0.4s ease;
            opacity: 0;
            margin-bottom: 0;
        }}
        .extended-briefing.open {{
            max-height: 2000px;
            opacity: 1;
            margin-bottom: 1.5rem;
        }}
        .extended-briefing-inner {{
            background: linear-gradient(135deg, #fafaf9 0%, #f5f3ff 100%);
            border: 1px solid rgba(79, 70, 229, 0.1);
            border-radius: 10px;
            padding: 1.5rem;
            color: var(--text-secondary, #64748b);
            font-size: 0.9rem;
            line-height: 1.9;
        }}
        .extended-briefing-inner h3 {{
            color: var(--text-primary, #1a1a2e);
            font-size: 0.95rem;
            font-weight: 700;
            margin: 1.25rem 0 0.5rem;
        }}
        .extended-briefing-inner h3:first-child {{
            margin-top: 0;
        }}

        .top-stories {{
            margin-top: 24px;
        }}

        .top-stories h3 {{
            font-size: 16px;
            color: #1a1a2e;
            margin-bottom: 16px;
            font-weight: 600;
        }}

        .content-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 24px;
            margin-top: 32px;
        }}

        .content-column {{
            display: flex;
            flex-direction: column;
        }}

        .column-header {{
            font-size: 18px;
            font-weight: 700;
            color: white;
            padding: 16px;
            border-radius: 8px 8px 0 0;
            margin-bottom: 0;
        }}

        .video-header {{
            background: linear-gradient(135deg, #dc2626, #991b1b);
        }}

        .podcast-header {{
            background: linear-gradient(135deg, #7c3aed, #5b21b6);
        }}

        .article-header {{
            background: linear-gradient(135deg, #2563eb, #1e40af);
        }}

        .content-column-items {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}

        .content-card {{
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}

        .content-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.12) !important;
        }}

        footer {{
            background: #1a1a2e;
            color: #64748b;
            text-align: center;
            padding: 24px;
            margin-top: 48px;
            font-size: 12px;
        }}

        .toast {{
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: #10b981;
            color: white;
            padding: 16px 24px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            z-index: 1000;
            opacity: 0;
            transition: opacity 0.3s ease;
            max-width: 300px;
        }}

        .toast.show {{
            opacity: 1;
        }}

        .toast.error {{
            background: #ef4444;
        }}

        @media (max-width: 900px) {{
            .content-grid {{
                grid-template-columns: 1fr;
            }}

            .header-container {{
                flex-direction: column;
                text-align: center;
                gap: 16px;
            }}

            .header-actions {{
                justify-content: center;
            }}

            .briefing-section {{
                padding: 24px;
            }}
        }}

        @keyframes fadeIn {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="header-container">
            <div class="header-title">
                <div class="logo">🤖 AI Briefing</div>
                <div class="date-display">{escape_html(date_info['full'])} · {escape_html(date_info['time'])}</div>
            </div>
            <div class="header-actions">
                <button class="refresh-btn" onclick="refreshNews()">⟳ Opdater nu</button>
                <div class="last-updated" id="lastUpdated">Sidst opdateret: {escape_html(date_info['time'])}</div>
            </div>
        </div>
    </header>

    <main>
        <section class="briefing-section">
            <h2>Executive Briefing</h2>
            <p class="briefing-text">{escape_html(data.get('executive_briefing', ''))}</p>

            <button class="expand-btn" onclick="toggleExtended()">
                <span class="arrow">▼</span> Længere resumé
            </button>

            <div class="extended-briefing" id="extendedBriefing">
                <div class="extended-briefing-inner">
                    {data.get('extended_briefing', '')}
                </div>
            </div>

            <div class="top-stories">
                <h3>Top 3 Nyheder</h3>
                {top_stories_html}
            </div>
        </section>

        <div class="content-grid">
            <div class="content-column">
                <div class="column-header video-header">📹 Video</div>
                <div class="content-column-items">
                    {youtube_items}
                </div>
            </div>

            <div class="content-column">
                <div class="column-header podcast-header">🎙️ Podcasts</div>
                <div class="content-column-items">
                    {podcast_items}
                </div>
            </div>

            <div class="content-column">
                <div class="column-header article-header">📰 Artikler</div>
                <div class="content-column-items">
                    {article_items}
                </div>
            </div>
        </div>
    </main>

    <footer>
        <p>AI Briefing • Dagligt executive briefing kurateret for Danske Spil</p>
        <p style="margin-top: 8px; opacity: 0.7;">Opdateret {escape_html(date_info['full'])} · Kilde: Anthropic Claude AI med web search</p>
    </footer>

    <div class="toast" id="toast"></div>

    <script>
        function refreshNews() {{
            const btn = document.querySelector('.refresh-btn');
            btn.classList.add('loading');
            btn.textContent = '⟳ Opdaterer...';

            fetch('/.netlify/functions/refresh', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
            }})
            .then(response => {{
                if (response.ok) {{
                    showToast('Briefing opdateret!', 'success');
                    setTimeout(() => window.location.reload(), 1500);
                }} else {{
                    showToast('Fejl ved opdatering', 'error');
                    btn.classList.remove('loading');
                    btn.textContent = '⟳ Opdater nu';
                }}
            }})
            .catch(error => {{
                console.error('Error:', error);
                showToast('Kunne ikke opdatere briefing', 'error');
                btn.classList.remove('loading');
                btn.textContent = '⟳ Opdater nu';
            }});
        }}

        function toggleExtended() {{
            const panel = document.getElementById('extendedBriefing');
            const btn = document.querySelector('.expand-btn');
            panel.classList.toggle('open');
            btn.classList.toggle('open');
            btn.querySelector('.arrow').textContent = panel.classList.contains('open') ? '▲' : '▼';
        }}

        function showToast(message, type = 'success') {{
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.className = 'toast show';
            if (type === 'error') {{
                toast.classList.add('error');
            }}
            setTimeout(() => {{
                toast.classList.remove('show');
            }}, 4000);
        }}

        // Scroll animation for cards
        const observer = new IntersectionObserver((entries) => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    entry.target.style.animation = 'fadeIn 0.6s ease';
                }}
            }});
        }});

        document.querySelectorAll('.content-card, .briefing-section').forEach(el => {{
            observer.observe(el);
        }});
    </script>
</body>
</html>
"""
    return html

# ============================================================================
# MAIN FUNCTIONS
# ============================================================================

def curate_news(client, date_info):
    """Call Claude API with web search to curate daily AI news."""

    prompt = f"""Du er en senior AI-nyhedsredaktør der kuraterer et dagligt executive briefing for
CEO'en i Danske Spil. Dagens dato er {date_info['full']}.

═══════════════════════════════════════════
REDAKTIONEL PROFIL — UDVÆLGELSESKRITERIER
═══════════════════════════════════════════

MÅLGRUPPE: C-level topleder i spilbranchen. Ikke tekniker, men forstår tekniske
begreber hvis de forklares kort. Træffer strategiske beslutninger om AI-investering,
partnerskaber og organisationsforandring.

KILDEPRIORITERING (i rækkefølge):
1. TIER 1 — Washington Post, New York Times, Bloomberg, Financial Times, Wall Street Journal.
   Disse SKAL prioriteres når de dækker AI.
2. TIER 2 — Anerkendte tech-medier: TechCrunch, The Verge, Wired, Ars Technica, MIT Tech Review.
3. TIER 3 — Branchemedier for gambling/iGaming: iGaming Business, Gaming Intelligence, EGR, SBC News.
4. TIER 4 — Analysehuse og konsulentrapporter: McKinsey, BCG, Gartner, a16z, Sequoia.
Undgå anonyme blogs, clickbait-sites og ukendende kilder.

UNDGÅ DISSE KILDER (brugeren følger dem allerede):
- Podcasts: Channels, Pivot, Sam Harris/Making Sense, Lex Fridman, The Daily (NYT)
- Danske aviser generelt
Hvis en af disse har en exceptionelt vigtig AI-nyhed, må du nævne den, men find primært ANDRE kilder.

EMNE-PRIORITERING (vigtigst først):
1. FORRETNINGSSTRATEGI: Konkurrenters AI-tiltag, M&A, nye AI-produktlanceringer, markedstrends,
   partnerships, investeringer. Hvad gør tech-giganterne og AI-selskaberne strategisk?
2. TEKNOLOGISKE GENNEMBRUD: Nye modeller, capabilities, benchmarks. Fokusér på hvad det
   BETYDER for forretning, ikke de tekniske detaljer.
3. LEDELSE & ORGANISATION: AI-adoption i topledelse, organisatorisk transformation,
   change management, nye roller, workforce impact.
Regulering/compliance er SEKUNDÆRT — medtag kun hvis det er breaking eller har direkte
forretningskonsekvenser.

GAMBLING/SPIL-FOKUS (20% af indholdet):
Prioritér i denne rækkefølge:
1. Hvad konkurrenter gør med AI: Flutter, Entain, Kindred, Betsson, bet365, DraftKings, FanDuel
2. AI-teknologi i branchen: fraud detection, personalisering, odds-optimering, kundeservice-AI
Regulering og responsible gambling er sekundært her.

TIDSVINDUE: Seneste 7 dage. Kvalitet og relevans over aktualitet — en vigtig analyse fra
i mandags slår en uvigtig nyhed fra i dag.

GEOGRAFISK SCOPE: Globalt. Ingen nordisk/europæisk bias.

SPROG OG TONE:
- Alle resuméer og briefing på DANSK
- Let teknisk: begreber som LLM, fine-tuning, RAG, multimodal må bruges, men forklar
  kort i parentes første gang (f.eks. "RAG (en metode til at koble AI til virksomhedsdata)")
- Direkte, forretningsorienteret sprog. Ingen buzzwords, ingen hype.
- Fokusér altid på "hvad betyder dette strategisk" frem for "hvad skete der teknisk"
- Originale titler kan beholdes på engelsk

═══════════════════════════════════════════
INDHOLDSSTRUKTUR
═══════════════════════════════════════════

1. EXECUTIVE BRIEFING (150-200 ord):
   Et sammenhængende referat af ugens/dagens vigtigste AI-udvikling.
   Skrives som en fortælling, ikke punktform. Afslut med 1-2 sætninger om
   hvad der er værd at holde øje med de kommende dage.

1b. EXTENDED BRIEFING (400-600 ord, HTML-formateret):
   En uddybet analyse af de vigtigste nyheder. Opdelt i 3-4 afsnit med h3-overskrifter
   i HTML-format. Hvert afsnit uddyber en vigtig nyhed med strategisk kontekst.
   Afslut med et "Hvad du bør holde øje med"-afsnit.
   Brug HTML-tags: <h3>Overskrift</h3> efterfulgt af brødtekst.
   Skriv i et format der er let at skimme men giver reel dybde.

2. TOP 3 NYHEDER:
   - Overskrift
   - Kort beskrivelse (1-2 sætninger, fokus på strategisk betydning)
   - Prioritet: "red" (breaking/game-changing), "amber" (vigtig trend), "green" (værd at kende)
   - Relevans-tag: én sætning om HVORFOR dette er vigtigt for en CEO
   - URL til den bedste kilde
   - is_gambling: true/false

3. VIDEO/YOUTUBE (5 stk):
   Find 5 AI-videoer publiceret inden for de seneste 7 dage.
   Prioritér: konference-talks, executive interviews, produkt-demoer, strategianalyser.
   Mindst 1 skal handle om gambling/spilbranchen + AI.
   Angiv: titel, kanal, resumé (dansk), URL, varighed.

4. PODCASTS (5 stk):
   Find 5 AI-podcast-episoder fra de seneste 7 dage.
   UNDGÅ: Channels, Pivot, Making Sense, Lex Fridman, The Daily.
   Prioritér: a16z, Hard Fork, All-In, Stratechery, AI-specifikke podcasts.
   Mindst 1 skal handle om gambling/spilbranchen + AI.
   Angiv: titel, podcast-navn, resumé (dansk), URL, varighed.

5. ARTIKLER (5 stk):
   Find 5 AI-artikler fra de seneste 7 dage.
   PRIORITÉR Tier 1-kilder (WP, NYT, Bloomberg, FT, WSJ) når de har relevant dækning.
   Mindst 1 skal handle om gambling/spilbranchen + AI.
   Angiv: titel, kilde, resumé (dansk), URL, estimeret læsetid.

FORDELING: 80% generelle AI-nyheder, 20% gambling/spilbranchen.

Svar med rent JSON, ingen anden tekst:

{{
  "executive_briefing": "...",
  "extended_briefing": "<h3>Overskrift 1</h3>Uddybende tekst...<h3>Overskrift 2</h3>Mere tekst...",
  "top_stories": [
    {{
      "title": "...",
      "description": "...",
      "priority": "red|amber|green",
      "relevance_tag": "...",
      "url": "...",
      "is_gambling": false
    }}
  ],
  "youtube": [
    {{
      "title": "...",
      "channel": "...",
      "summary": "...",
      "url": "...",
      "duration": "...",
      "is_gambling": false
    }}
  ],
  "podcasts": [
    {{
      "title": "...",
      "show": "...",
      "summary": "...",
      "url": "...",
      "duration": "...",
      "is_gambling": false
    }}
  ],
  "articles": [
    {{
      "title": "...",
      "source": "...",
      "summary": "...",
      "url": "...",
      "read_time": "...",
      "is_gambling": false
    }}
  ]
}}
"""

    print("Søger efter AI-nyheder med Claude...")
    messages = [{"role": "user", "content": prompt}]

    # Loop up to 10 times to handle tool use
    for attempt in range(10):
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            tools=[{"type": "web_search_20250305"}],
            messages=messages,
        )

        # Check stop reason
        if response.stop_reason == "end_turn":
            break

        if response.stop_reason == "tool_use":
            # Append assistant response
            messages.append({"role": "assistant", "content": response.content})

            # Process tool uses and create tool results
            tool_results = []
            for content_block in response.content:
                if content_block.type == "tool_use":
                    # For web_search_20250305, we just continue - Claude handles it
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": "Search completed"
                    })

            # Append tool results
            if tool_results:
                messages.append({"role": "user", "content": tool_results})
        else:
            break

    # Extract JSON from response
    text_content = ""
    for content_block in response.content:
        if hasattr(content_block, "text"):
            text_content += content_block.text

    # Find JSON in response
    json_match = re.search(r"\{[\s\S]*\}", text_content)
    if json_match:
        try:
            data = json.loads(json_match.group())
            return data
        except json.JSONDecodeError:
            raise ValueError("Could not parse JSON from Claude response")

    raise ValueError("No JSON found in Claude response")

def main():
    """Main entry point."""
    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    # Create client
    client = Anthropic(api_key=api_key)

    # Get date info
    date_info = get_danish_date()

    # Curate news
    print(f"Curating news for {date_info['full']}...", file=sys.stderr)
    data = curate_news(client, date_info)

    # Generate HTML
    print("Generating HTML...", file=sys.stderr)
    html = generate_html(data, date_info)

    # Save to index.html in repo root
    repo_root = Path(__file__).parent.parent
    output_file = repo_root / "index.html"

    output_file.write_text(html, encoding="utf-8")
    print(f"Successfully saved to {output_file}", file=sys.stderr)

if __name__ == "__main__":
    main()
