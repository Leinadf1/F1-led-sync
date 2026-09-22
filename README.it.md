<div align="center">

# 🏎️ F1-led-sync

**Trasforma la F1 in uno spettacolo di luci in tempo reale.**

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-red.svg)](https://opencv.org/)
[![Telegram](https://img.shields.io/badge/Telegram-@delfino_cchione-2CA5E0?logo=telegram&logoColor=white)](https://t.me/delfino_cchione)

[🇬🇧 English](README.md) &nbsp;|&nbsp; 🇮🇹 **Italiano**

</div>

---

### 📖 Cos'è

**F1-led-sync** analizza in tempo reale lo schermo su cui stai guardando la F1 e trasforma quello che succede in pista in **effetti luminosi su una striscia LED WS2812B**.

Tutto automatico, tutto in tempo reale, senza toccare nulla.

### 🔍 Come funziona

**Riconoscimento automatico dell'overlay F1** tramite computer vision (OpenCV). Lo script legge continuamente lo schermo, rileva bandiere, settori dei piloti e team radio, e invia i comandi corrispondenti ad Arduino che pilota la striscia LED.

---

### 🏁 Bandiere

| 🎨 Evento a schermo | 💡 Effetto sulla striscia LED |
|:---|:---|
| 🟡 **Bandiera gialla** | La striscia **lampeggia di giallo** |
| 🟡 **VSC o SC in fase di chiusura** | La striscia **lampeggia di giallo** |
| 🟡 **VSC o SC attiva** | Il giallo **rimane fisso** |
| 🔴 **Bandiera rossa** | Il rosso **rimane fisso** |
| 🚦 **Pit Exit Closed** | **Gli ultimi 10 LED si accendono di rosso** |

---

### 🏎️ Piloti

| 🎨 Evento a schermo | 💡 Effetto sulla striscia LED |
|:---|:---|
| 📻 **Team radio** di Leclerc o Hamilton | **Gli ultimi 10 LED si accendono di rosso** (sui 60 totali della striscia) |
| 🟣🟢🟡 **Settori** di Leclerc o Hamilton nella parte bassa dello schermo | **3 gruppi di 10 LED** seguono i colori dei 3 settori (viola / verde / giallo) |

I piloti sono **personalizzabili**: puoi impostare quelli che vuoi creando template su misura (vedi sotto).

---

### ✨ Caratteristiche

- 📺 **Riconoscimento automatico dell'overlay F1** tramite computer vision (OpenCV)
- 🔧 **Scalatura automatica** a qualsiasi risoluzione (1080p, 1440p, 4K)
- 🔌 **Rilevamento automatico della porta seriale** — niente COM5 / ttyUSB0 da configurare
- 🏁 **Gestione completa delle bandiere**: verde, gialla, rossa, VSC, Safety Car, Pit Exit Closed
- 🟣 **Settori pilota**: viola (miglior tempo), verde (miglior in sessione), giallo (più lento)
- 📻 **Indicatore team radio** per i piloti configurati
- 🛡️ **Nessun crash improvviso**: se manca un template o l'Arduino, lo script continua e segnala l'errore

### 🎬 Vuoi vedere il sistema in azione?

Nel repository non ci sono video o GIF demo. **Se vuoi vedere video del sistema in funzione, foto, o qualsiasi altro contenuto, scrivimi tranquillamente su [Telegram](https://t.me/delfino_cchione)** — ti mando tutto quello che ti serve per capire come funziona dal vivo.

### 🧰 Cosa ti serve

#### Hardware

| Componente | Note |
|---|---|
| **Striscia LED WS2812B** | 60 LED nell'esempio, ma funziona con qualsiasi lunghezza |
| **Arduino** (UNO, Nano, Mega...) | Qualsiasi modello con porta USB |
| **Alimentatore 5V** per la striscia | Dimensionato in base al numero di LED (60 mA per LED a piena potenza) |
| **Breadboard + cavi jumper** | Solo per i collegamenti |
| **PC** con Windows / Linux / macOS | Deve avere una porta USB libera e la F1 visibile a schermo |

#### Software

- **Python 3.8+**
- Librerie elencate in `requirements.txt` (`opencv-python`, `numpy`, `mss`, `pyserial`)

### 🚀 Installazione

**1. Clona il repository**

```bash
git clone https://github.com/Leinadf1/F1-led-sync.git
cd F1-led-sync
```

**2. Installa le dipendenze Python**

```bash
pip install -r requirements.txt
```

**3. Carica lo sketch su Arduino**

Apri `Codicestriscia.ino` nell'IDE di Arduino e caricalo. Non serve modificarlo.

**4. Collega la striscia LED**

- **DIN** della striscia → **pin 6** di Arduino
- **+5V** della striscia → **alimentatore esterno 5V** (NON da Arduino se hai più di 20 LED)
- **GND** della striscia → **GND dell'alimentatore** E **GND di Arduino** (massa comune obbligatoria)

**5. Avvia lo script**

```bash
python F1.py
```

### ⚙️ Configurazione

Il file `F1.py` è pronto all'uso. Le uniche cose che potresti voler modificare sono in cima al file:

```python
MONITOR_INDEX = 2  # 0=tutti, 1=primario, 2=secondario...

PILOTI = [
    {"code": "LEC", "settori": "blocco_leclerc_1.png", "tr": "Lec_TR.png"},
    {"code": "HAM", "settori": "blocco_hamilton_1.png", "tr": "Ham_TR.png"},
]
```

Il sistema **scala automaticamente** tutti i template e le zone alla risoluzione dello schermo. Che tu sia a 1080p, 1440p o 4K, non devi cambiare nulla.

### 🏎️ Aggiungere o cambiare piloti

Di default il sistema segue **Charles Leclerc** e **Lewis Hamilton**.

Aggiungere altri piloti richiede la creazione di **template personalizzati** (ritagli di screenshot dell'overlay F1) che devono essere precisi al pixel.

Per questo non è documentato passo-passo: **se hai difficoltà nel farlo e vuoi seguire altri piloti, scrivimi su [Telegram](https://t.me/delfino_cchione)**.

### 📁 Struttura del progetto

```
F1-led-sync/
├── F1.py                  # Script principale
├── Codicestriscia.ino     # Sketch Arduino
├── requirements.txt       # Dipendenze Python
├── README.md              # Readme inglese
├── README.it.md           # Readme italiano (questo file)
├── LICENSE
│
│   # Template
├── blocco_leclerc_1.png
├── blocco_hamilton_1.png
├── Lec_TR.png
├── Ham_TR.png
├── pit_closed.png
├── gialla.png
├── rossa.png
├── verde.png
├── vsc.png
├── sc.png
├── vsc end.png
└── sc end.png
```

> ⚠️ **Importante**: tutti i file devono rimanere nella **stessa cartella**.

### 🛠️ Risoluzione problemi

**"Nessun Arduino rilevato"**
- Controlla il cavo USB
- Su Windows, verifica in *Gestione dispositivi* che compaia la porta COM
- Su Linux: `sudo usermod -a -G dialout $USER`, poi logout/login

**"Template mancante: nomefile.png"**
- Il file non è nella cartella dello script
- Il nome non corrisponde esattamente (attenzione a maiuscole/minuscole)

**Le bandiere non vengono rilevate**
- Verifica che `MONITOR_INDEX` punti al monitor giusto
- Lo schermo deve essere in **fullscreen**

### 📄 Licenza

MIT — vedi [LICENSE](LICENSE).

### ⚠️ Disclaimer

Progetto personale e non ufficiale. Non affiliato con Formula 1, FOM, FIA, Sky o i team.

---

<div align="center">

### 💬 Hai domande? Hai bisogno di aiuto?

[![Telegram](https://img.shields.io/badge/Scrivimi_su_Telegram-@delfino_cchione-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/delfino_cchione)

**Fatto con ❤️ per la community F1**

</div>
