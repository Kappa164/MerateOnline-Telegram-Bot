import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
import re
import sqlite3
import os
import logging
import schedule
from config import BOT_TOKEN, CHANNEL_ID, SERVER_MODE, COMUNE, URL, COOLDOWN

# --LOGGING--
class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.INFO: "\033[94m",
        logging.WARNING: "\033[93m",
        logging.ERROR: "\033[91m"
    }
    RESET = "\033[0m"

    def format(self, r):
        colore = self.COLORS.get(r.levelno, "")
        messaggio = super().format(r)
        return f"{colore}{messaggio}{self.RESET}"


gestore = logging.StreamHandler()
formatter = ColorFormatter('%(asctime)s - %(levelname)s - %(message)s')
gestore.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    logger.addHandler(gestore)

logger.propagate = False
#---------------------


# --RIEPILOGO GIORNALIERO--
# I controlli di routine non vanno nel log: si contano e a mezzanotte esce un
# solo riepilogo della giornata. Gli errori vengono comunque segnalati subito.
class Statistiche:
    def __init__(self):
        self.azzera()

    def azzera(self):
        self.controlli = 0
        self.trovate = 0
        self.inviate = 0
        self.errori = []
        self.altri = 0

    def errore(self, testo):
        if len(self.errori) < 10:
            self.errori.append(f"{datetime.now():%H:%M}: {testo}")
        else:
            self.altri += 1


stats = Statistiche()


class MerateNewsBot:
    def __init__(self, token: str, channel_id: str):
        self.bot_token = token
        self.channel_id = channel_id
        self.url_base = f"https://api.telegram.org/bot{token}"
        
        #apro una sessione HTTP per più richieste, invece di aprirne una singola ogni volta 
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
        })
        
        #database per le notizie
        self.nome_db = "news_bot.db"
        self.init_database()

    # --INIZIALLIZZAZIONE DATABASE--
    def init_database(self):
        conn = sqlite3.connect(self.nome_db)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notizie (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url_notizia TEXT UNIQUE,
                titolo TEXT,
                data_invio TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("The database is ready")

    # --CONTROLLA SE UNA NOTIZIA È STATA GIÀ INVIATA--
    def notizia_inviata(self, url_notizia: str) -> bool:
        conn = sqlite3.connect(self.nome_db)
        cursor = conn.cursor()
        # Controllo per URL
        cursor.execute("SELECT 1 FROM notizie WHERE url_notizia = ?", (url_notizia,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    # --MARKA UNA NOTIZIA COME INVIATA--
    def mark_notizia_inviata(self, url_notizia: str, titolo: str):
        conn = sqlite3.connect(self.nome_db)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO notizie (url_notizia, titolo) VALUES (?, ?)",
            (url_notizia, titolo)
        )
        conn.commit()
        conn.close()

    # --PULISCE IL NOME DEL COMUNE DAL TITOLO DELLA NOTIZIA--
    def pulisci_titolo(self, titolo: str) -> str:
        prefissi = [
            f'{COMUNE}:',
            f'{COMUNE}：',  # due punti unicode
        ]
        for p in prefissi:
            if titolo.lower().startswith(p.lower()):
                return titolo[len(p):].strip()
        return titolo.strip()

    # --RIMUOVE LA CATEGORIA "COMUNE"
    def pulisci_categoria(self, categorie: list) -> list:
        return [cat for cat in categorie if cat.lower() != COMUNE.lower()]

    # --ESCAPE TESTO PER TELEGRAM MARKDOWN--
    def markdown(self, text: str) -> str:
        escape = r'_[]()~`>#+-=|{}.!*'
        return ''.join(f'\\{c}' if c in escape else c for c in text)

    # --TRONCA TESTO SENZA SPEZZARE LE PAROLE--
    def tronca_descrizione(self, testo: str, max: int = 250) -> str:
        testo = testo.strip()
        if len(testo) <= max:
            return testo

        soglia = max - 3
        troncato = testo[:soglia]

        matches = list(re.finditer(r'[\s.,;:!?]', troncato))
        if matches:
            troncato = troncato[:matches[-1].start()]

        troncato = troncato.rstrip(' .,;:!?')

        if not troncato:
            troncato = testo[:soglia].rstrip()

        return troncato + '...'

    # --PARSING DATA ITALIANA IN DATETIME
    def parse_data(self, data: str) -> datetime:
        try:
            mesi = {
                'gennaio': '01', 'febbraio': '02', 'marzo': '03',
                'aprile': '04', 'maggio': '05', 'giugno': '06',
                'luglio': '07', 'agosto': '08', 'settembre': '09',
                'ottobre': '10', 'novembre': '11', 'dicembre': '12'
            }

            testo = data.strip().lower()

            match_data = re.search(r'(\d{1,2})\s+([a-zà]+)\s+(\d{4})', testo)
            if not match_data:
                return datetime.now()

            giorno, mese_testo, anno = match_data.groups()
            mese = mesi.get(mese_testo, '01')

            ore = '00'
            minuti = '00'

            match_ora = re.search(r'(\d{1,2}):(\d{2})', testo)
            if match_ora:
                ore, minuti = match_ora.groups()

            return datetime.strptime(
                f"{giorno.zfill(2)}/{mese}/{anno} {ore.zfill(2)}:{minuti}",
                "%d/%m/%Y %H:%M"
            )
        except Exception:
            return datetime.now()

    # --WEBSCRAPING--
    def scrape_notizie(self) -> list:
        url = URL
        logger.debug("Scraping notizie da merateonline.it...")
        
        try:
            risposta = self.session.get(url, timeout=15)
            risposta.raise_for_status()
            
            soup = BeautifulSoup(risposta.content, 'html.parser')
            
            articoli = soup.find_all('article', class_='section_margin') #prende tutti gli articoli
            logger.debug(f"Trovati {len(articoli)} articoli")
            
            notizie = []
            
            for a in articoli:
                try:
                    notizia = self.parse_article(a)
                    if notizia and not self.notizia_inviata(notizia['url']):
                        notizie.append(notizia)
                except Exception as e:
                    logger.warning(f"An article could not be parsed: {e}")
                    stats.errore(f"an article could not be parsed ({e})")
                    continue
            
            #ordina dalla meno recente alla più recente (prima mando le notizie vecchie)
            notizie.sort(key=lambda x: x['datetime'])
            
            logger.debug(f"{len(notizie)} nuove notizie da inviare")
            return notizie
            
        except Exception as e:
            logger.error(f"The news page could not be read: {e}")
            stats.errore(f"the news page could not be read ({e})")
            return []

    #--PARSING SINGOLO ARTICOLO--
    def parse_article(self, articolo) -> dict:
        #data
        data_elem = articolo.find('span', class_='meta_date')
        data_str = data_elem.text.strip() if data_elem else "Data non disponibile"
        data_pulita = self.parse_data(data_str)
        
        #titolo
        titolo_elem = articolo.find('div', class_='alith_post_title').find('a')
        titolo_raw = titolo_elem.text.strip() if titolo_elem else "Titolo non disponibile"
        titolo_pulito = self.pulisci_titolo(titolo_raw)
        
        #url
        url = titolo_elem.get('href') if titolo_elem else ""
        if url and not url.startswith('http'):
            url = f"https://www.merateonline.it{url}"
        
        #categorie
        categorie = []
        categorie_elem = articolo.find_all('div', class_='meta_categories')
        for cat_elem in categorie_elem:
            cat_link = cat_elem.find('a')
            if cat_link:
                categorie.append(cat_link.text.strip())
        
        categorie_pulite = self.pulisci_categoria(categorie)
        
        #descrizione
        descrizione_elem = articolo.find('p', class_='alith_post_except')
        desc = descrizione_elem.text.strip() if descrizione_elem else ""
        
        #limita la descrizione senza spezzare le parole
        desc = self.tronca_descrizione(desc, 250)
        
        return {
            'date': data_str,
            'datetime': data_pulita,
            'titolo': titolo_pulito,
            'url': url,
            'categories': categorie_pulite,
            'description': desc
        }

    #--FORMATTAZIONE MESSAGGIO TELEGRAM--
    def formatta_messaggio_telegram(self, news: dict) -> str:
        titolo = self.markdown(news['titolo'])
        data = self.markdown(news['date'])
        descrizione = self.markdown(news['description']) if news['description'] else ""
        categorie = ", ".join(self.markdown(cat) for cat in news['categories']) if news['categories'] else "Notizia"
        url = news['url']

        messaggio = f"📰 *{titolo}*\n\n"
        messaggio += f"🗓️ {data}\n"

        if news['categories']:
            messaggio += f"🏷️ {categorie}\n\n"
        else:
            messaggio += "\n"

        if news['description']:
            messaggio += f"_{descrizione}_\n\n"

        messaggio += f"🔗 [Leggi articolo completo]({url})"

        return messaggio
    #--INVIA MESSAGGIO VIA BOT
    def send_telegram_message(self, testo: str) -> bool:
        try:
            #crea il payload
            payload = {
                'chat_id': self.channel_id,
                'text': testo,
                'parse_mode': 'MarkdownV2',
                'disable_web_page_preview': False
            }
            
            risposta = self.session.post(
                f"{self.url_base}/sendMessage",
                json=payload,
                timeout=10
            )
            risposta.raise_for_status()
            
            return True
            
        except Exception as e:
            logger.error(f"A news item could not be sent to Telegram: {e}")
            stats.errore(f"a news item could not be sent to Telegram ({e})")
            return False

    #--CONTROLLA E INVIA NUOVE NOTIZIE--
    def check_invia_notizie(self):
        logger.debug("Controllo nuove notizie...")
        stats.controlli += 1
        
        # Scraping notizie
        nuove_notizie = self.scrape_notizie()
        
        if not nuove_notizie:
            logger.debug("Nessuna nuova notizia")
            return
        
        stats.trovate += len(nuove_notizie)
        logger.debug(f"Invio {len(nuove_notizie)} nuove notizie...")
        
        # Invio notizie (dalla meno recente alla più recente)
        cont = 0
        for i, news in enumerate(nuove_notizie, 1):
            logger.debug(f"Invio {i}/{len(nuove_notizie)}: {news['titolo'][:50]}...")
            
            message = self.formatta_messaggio_telegram(news)
            if self.send_telegram_message(message):
                self.mark_notizia_inviata(news['url'], news['titolo'])
                cont +=1
                stats.inviate += 1
                logger.debug("Notizia inviata")
            
            # Wait tra un messaggio e l'altro
            if i < len(nuove_notizie):
                time.sleep(3)  # 3 secondi tra un messaggio e l'altro
        
        logger.debug(f"COMPLETATO: {cont}/{len(nuove_notizie)} notizie inviate")

    #--RIEPILOGO DELLA GIORNATA APPENA FINITA--
    def riepilogo(self):
        giorno = datetime.now() - timedelta(minutes=5)
        problemi = len(stats.errori) + stats.altri
        logger.info(
            f"Daily recap for {giorno:%d/%m/%Y}: {stats.controlli} checks run, "
            f"{stats.trovate} news found and {stats.inviate} sent, "
            + (f"{problemi} problem{'s' if problemi != 1 else ''}" if problemi else "no problems")
        )
        # un problema per riga, con il livello INFO: sono già stati segnalati
        for e in stats.errori:
            logger.info(f"Problem at {e}")
        if stats.altri:
            logger.info(f"...and {stats.altri} more problems")
        stats.azzera()

    #--ESEGUI UNA VOLTA LA RICERCA--
    def esegui_singolo(self):
        logger.info(f"The news bot for {COMUNE} is running a single check")
        self.check_invia_notizie()

    #--AVVIA IN MODALITÀ SERVER--
    def avvia_server(self):
        logger.info(f"The news bot for {COMUNE} has started: it checks every {COOLDOWN} minutes and sends a recap at midnight")
        
        # Esegui immediatamente un controllo
        self.check_invia_notizie()
        
        # Schedula la ricerca di notizie
        schedule.every(COOLDOWN).minutes.do(self.check_invia_notizie)
        schedule.every().day.at("00:00").do(self.riepilogo)
        
        #loop infinito
        while True:
            try:
                schedule.run_pending()
                time.sleep(20)  #controlla tre volte al minuto
            except Exception as e:
                logger.error(f"The main loop failed: {e}")
                stats.errore(f"the main loop failed ({e})")
                time.sleep(60)  #aspetta 1 minuto e riprova

#--MAIN--
def main():
    #creazione bot
    bot = MerateNewsBot(BOT_TOKEN, CHANNEL_ID)
    
    if SERVER_MODE:
        bot.avvia_server()
    else:
        bot.esegui_singolo()

if __name__ == "__main__":
    main()