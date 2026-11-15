# MerateOnline Telegram Bot

**Bot Python per fare scraping automatico delle notizie da `MerateOnline` e pubblicarle su un canale Telegram.**
**Perfetto per restare aggiornati sulle news del proprio comune senza dover controllare manualmente il sito.**

---

## ⚙️ Funzionalità

- Estrae automaticamente le notizie usando `beautifulsoup`
- Ordina correttamente per data e ora le notizie
- Tiene traccia delle notizie già notificate evitando duplicati
- Il bot Telegram invia messaggi in formato Markdown
- Logging in console di tutte le scansioni ed eventuali errori

---

## 📦 Requisiti

- **Python 3.8+**
- `requests`
- `beautifulsoup4`

---

## 📂 Struttura del progetto

```text
.
├── script.py
├── config.py
├── .env.example
├── .env            (da creare, escluso da git)
├── news_bot.db     (generato automaticamente)
├── Dockerfile
├── compose.yaml
└── README.md
```

### File principali

- `script.py` → script principale del bot
- `config.py` → legge la configurazione dalle variabili d'ambiente
- `.env` → i tuoi valori (token, canale, comune…): **non va mai committato**
- `news_bot.db` → database generato automaticamente

---

## 🔧 Configurazione

Copia il file di esempio e inserisci i tuoi valori:

```bash
cp .env.example .env
```

| Variabile | Obbligatoria | Descrizione |
| --- | --- | --- |
| `BOT_TOKEN` | sì | Token del bot Telegram, da **@BotFather** |
| `CHANNEL_ID` | sì | Canale o chat dove inviare le notizie: `@nome_canale` oppure l'ID numerico (es. `-1001234567890`, ottenibile con **@MyIDBot**) |
| `COMUNE` | no (`Merate`) | Nome del comune: viene tolto dal titolo e dalla categoria delle notizie |
| `NEWS_URL` | no (Merate) | Pagina di MerateOnline da cui fare scraping |
| `SERVER_MODE` | no (`true`) | `true` resta in ascolto, `false` invia le notizie una volta sola |
| `COOLDOWN` | no (`10`) | Minuti tra una ricerca e l'altra |

> Il bot deve essere amministratore del canale, altrimenti non potrà inviare messaggi.

#### Come ottengo l'URL del mio comune?

1) apri https://www.merateonline.it/p/cerca-comune/598
2) seleziona il comune che ti interessa
3) copia il link e assegnalo a `NEWS_URL`

---

## ▶️ Avvio

### Con Docker

```bash
docker compose up -d --build
```

`compose.yaml` carica automaticamente il file `.env`.

### Senza Docker

```bash
pip install -r requirements.txt
set -a; . ./.env; set +a
python script.py
```

---

## 🔨 Possibili miglioramenti futuri

- supporto a più comuni contemporaneamente
- invio immagini insieme agli articoli
- riassunto della notizia in descrizione

### Versione 1.0