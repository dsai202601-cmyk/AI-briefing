# AI Briefing — Opsætningsguide

Denne guide fører dig igennem opsætningen af din personlige AI Briefing webapp.
Når du er færdig, har du en side der automatisk opdateres kl. 06:00 hver morgen
og kan tilgås fra enhver enhed via et fast link.

**Estimeret tid:** 20-30 minutter (du skal kun gøre dette én gang)

---

## Oversigt: Hvad skal sættes op

Du skal oprette tre gratis konti og forbinde dem:

1. **GitHub** — opbevarer koden og kører det daglige opdateringsscript
2. **Netlify** — hoster webappen online (dit faste link)
3. **Anthropic** — AI-tjenesten der kuraterer nyhederne (koster ca. $5-10/måned)

---

## Trin 1: Opret en GitHub-konto

1. Gå til **https://github.com/signup**
2. Opret en konto med din email
3. Vælg den gratis plan ("Free")

### Opret et nyt repository

1. Klik på **"+"** øverst til højre → **"New repository"**
2. Navn: `ai-briefing`
3. Vælg **Public** (nødvendigt for gratis GitHub Actions)
4. Klik **"Create repository"**

### Upload koden

På den nye repository-side ser du instruktioner. Åbn en terminal (eller Git Bash) og kør:

```bash
cd sti/til/ai-briefing-mappen
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/DIT-BRUGERNAVN/ai-briefing.git
git push -u origin main
```

**Alternativ (uden terminal):** Du kan også uploade filerne direkte via GitHub's webinterface:
1. Gå til dit nye repository
2. Klik **"uploading an existing file"**
3. Træk alle filerne fra ai-briefing mappen ind
4. Klik **"Commit changes"**

---

## Trin 2: Opret en Anthropic API-nøgle

1. Gå til **https://console.anthropic.com**
2. Opret en konto og tilføj et betalingsmiddel
3. Gå til **API Keys** i venstre menu
4. Klik **"Create Key"** og kopiér nøglen (den ser ud som: `sk-ant-...`)
5. **Gem nøglen et sikkert sted** — du får brug for den i næste trin

**Pris:** Scriptet bruger Claude Sonnet med web search. En daglig opdatering koster ca. $0.15-0.30, dvs. ca. $5-10 per måned.

---

## Trin 3: Tilføj API-nøglen som GitHub Secret

1. Gå til dit repository på GitHub
2. Klik **Settings** → **Secrets and variables** → **Actions**
3. Klik **"New repository secret"**
4. Navn: `ANTHROPIC_API_KEY`
5. Værdi: Indsæt din Anthropic API-nøgle
6. Klik **"Add secret"**

---

## Trin 4: Test at GitHub Actions virker

1. Gå til dit repository → **Actions**-fanen
2. Du bør se workflowet "Daily AI Briefing Update"
3. Klik på det → klik **"Run workflow"** → **"Run workflow"**
4. Vent 2-3 minutter. Når den er grøn ✅, er din `index.html` opdateret med rigtige nyheder!

---

## Trin 5: Opret en Netlify-konto og deploy

1. Gå til **https://app.netlify.com/signup**
2. Klik **"Sign up with GitHub"** (nemmeste metode)
3. Godkend adgangen

### Forbind dit repository

1. Klik **"Add new site"** → **"Import an existing project"**
2. Vælg **GitHub**
3. Find og vælg dit `ai-briefing` repository
4. Indstillinger:
   - Branch to deploy: `main`
   - Build command: *(lad stå tomt)*
   - Publish directory: `.`
5. Klik **"Deploy site"**

Netlify giver dig et link som `https://random-name-12345.netlify.app`. Du kan ændre navnet under **Site configuration** → **Change site name** til f.eks. `ai-briefing-ds.netlify.app`.

---

## Trin 6: Opsæt refresh-knappen

For at refresh-knappen virker, skal Netlify kunne trigge GitHub Actions.

### Opret en GitHub Personal Access Token

1. Gå til **https://github.com/settings/tokens**
2. Klik **"Generate new token (classic)"**
3. Navn: `AI Briefing Refresh`
4. Vælg scope: **repo** (fuld adgang til repositories)
5. Klik **"Generate token"** og kopiér tokenet

### Tilføj til Netlify

1. Gå til dit site på Netlify
2. Klik **Site configuration** → **Environment variables**
3. Tilføj to variabler:
   - `GITHUB_TOKEN` = dit personal access token fra ovenfor
   - `GITHUB_REPO` = `DIT-BRUGERNAVN/ai-briefing` (f.eks. `johndoe/ai-briefing`)

---

## Færdig!

Din AI Briefing er nu live. Her er hvad der sker automatisk:

- **Kl. 06:00 CET** hver morgen kører GitHub Actions scriptet
- Scriptet søger efter dagens AI-nyheder via Claude
- Den opdaterede side deployes automatisk til Netlify
- Du åbner dit link og har en frisk briefing klar

**Refresh-knappen** lader dig manuelt trigge en opdatering når som helst.
Det tager 2-3 minutter at generere nyt indhold.

### Tips

- **Bogmærk linket** på din telefons homescreen for hurtig adgang
- På iPhone: Åbn linket i Safari → tryk Del-knappen → "Føj til hjemmeskærm"
- På Android: Åbn i Chrome → tryk ⋮ → "Føj til startskærm"

---

## Fejlfinding

**GitHub Actions fejler:**
- Tjek at `ANTHROPIC_API_KEY` er korrekt sat under Settings → Secrets
- Tjek at din Anthropic-konto har kredit

**Refresh-knappen virker ikke:**
- Tjek at `GITHUB_TOKEN` og `GITHUB_REPO` er sat i Netlify Environment variables
- Tokenet skal have `repo`-scope

**Siden opdateres ikke:**
- Gå til GitHub → Actions → se om workflowet kører/fejler
- Netlify deployer automatisk når der pushes til main

---

## Omkostninger

| Tjeneste | Pris |
|----------|------|
| GitHub (Free) | Gratis |
| Netlify (Free tier) | Gratis |
| Anthropic API | ca. $5-10/måned |
| **I alt** | **ca. $5-10/måned** |
