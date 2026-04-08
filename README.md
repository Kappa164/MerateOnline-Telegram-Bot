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
├── news_bot.db
├── .gitignore
└── README.md
```

### File principali

- `script.py` → script principale del bot
- `config.py` → file di configurazione
- `news_bot.db` → database generato autoamaticamente

---

## 🔧 Configurazione e utilizzo

Inserisci i valori in `config.py` come segue:

#### `BOT_TOKEN`
Token del bot Telegram. Usa **@BotFather** per creare un bot e ottenere il suo token.

Esempio:

```python
BOT_TOKEN = "1234567890:ABCDEF..."
```

#### `CHANNEL_ID`
Canale o chat dove inviare le notizie.

Esempio:

```python
CHANNEL_ID = "@nome_canale"
```

se non funziona, usa l'ID del canale o della chat ottenibile usando **@MyIDBot**

```python
CHANNEL_ID = "-1001234567890"
```


> Il bot deve essere amministratore del canale, altrimenti non potrà inviare messaggi.

#### `COMUNE`
Nome del comune di cui si vogliono ottenere le notizie. 

Questa stringa serve a rimuovere il nome del paese dal titolo (spesso viene messo come prefisso) e dalla categoria.

Esempio:

```python
COMUNE = "Merate"
```

#### `URL`
URL del sito da cui fare scraping.

#### COME OTTENGO L'URL DEL MIO COMUNE?

1) apri https://www.merateonline.it/p/cerca-comune/598
2) seleziona il comune che ti interessa
3) copia il link e assegnalo a `URL`

Esempio per Merate:

```python
URL = "https://www.merateonline.it/articoli/l/56/merate"
```

#### `SERVER_MODE`
È possibile eseguire lo script una sola volta oppure avviare la modalità server in modo da scansionare automaticamente MerateOnline cercando nuovi articoli.

Per disabilitare la server mode impostare la variabile a **False**:

```python
SERVER_MODE = False
```

#### `COOLDOWN`
Numero di minuti di attesa tra una ricerca e l'altra (in minuti).

Esempio:

```python
COOLDOWN = 10    #ogni 10 minuti
```

Più è basso, più spesso il bot controllerà nuove notizie.

---
### Installa le dipendenze

```bash
pip install requests beautifulsoup4
```

### Avvia lo script

```bash
python script.py
```

---



## 🔨 Possibili miglioramenti futuri

- supporto a più comuni contemporaneamente
- invio immagini insieme agli articoli
- riassunto della notizia in descrizione

### Versione 1.0