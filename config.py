#----------
#  CONFIG
#----------
# I valori si leggono dalle variabili d'ambiente (vedi .env.example).
# Non scrivere token o ID qui: questo file è pubblico.
import os
import sys


def _required(name):
    value = os.environ.get(name, "").strip()
    if not value:
        sys.exit(f"Variabile d'ambiente {name} mancante: impostala nel file .env")
    return value


#Token del bot Telegram che si vuole utilizzare
BOT_TOKEN = _required("BOT_TOKEN")

#ID del canale Telegram che si vuole utilizzare
CHANNEL_ID = _required("CHANNEL_ID")

#Il nome del comune che si vuole usare
COMUNE = os.environ.get("COMUNE", "Merate")

#L'URL della pagina del comune che si vuole
# apri questo url: https://www.merateonline.it/p/cerca-comune/598
# tasto destro sul nome del comune, copi il link e lo incolli qua
URL = os.environ.get("NEWS_URL", "https://www.merateonline.it/articoli/l/56/merate")

#Modalità per restare in attesa di nuove notizie.
#Impostare a false per inviare le notizie solo una volta.
SERVER_MODE = os.environ.get("SERVER_MODE", "true").strip().lower() in ("1", "true", "yes")

#Imposta ogni quanti minuti effettuare una nuova ricerca
COOLDOWN = int(os.environ.get("COOLDOWN", "10"))
