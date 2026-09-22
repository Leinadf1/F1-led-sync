<div align="center">

# 🏎️ F1-led-sync

**Turn your F1 TV broadcast into a real-time LED light show.**

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-red.svg)](https://opencv.org/)

🇬🇧 **English** &nbsp;|&nbsp; [🇮🇹 Italiano](README.it.md)

</div>

---

### 📖 What is it

**F1-led-sync** analyzes your screen in real time while you're watching F1 and translates what happens on track into **light effects on a WS2812B LED strip**.

Yellow flag comes out? Your room glows yellow. Safety car? Flashing. Leclerc or Hamilton set a fast sector? The strip shows the right color. Incoming team radio? A small indicator lights up.

Fully automatic, fully real-time, nothing to touch.

### ✨ Features

- 📺 **Automatic F1 TV overlay recognition** via computer vision (OpenCV)
- 🔧 **Automatic scaling** to any screen resolution (1080p, 1440p, 4K)
- 🔌 **Automatic serial port detection** — no manual COM5 / ttyUSB0 configuration
- 🏁 **Full flag handling**: green, yellow, red, VSC, Safety Car, Pit Exit Closed
- 🟣 **Driver sectors**: purple (fastest), green (personal best), yellow (slower)
- 📻 **Team radio indicator** for configured drivers
- 🛡️ **No random crashes**: if a template or Arduino is missing, the script keeps running and reports the issue

### 🎥 Demo

> *[Add a GIF or short video showing the system in action here]*

### 🧰 What you need

#### Hardware

| Component | Notes |
|---|---|
| **WS2812B LED strip** | 60 LEDs in the example, but works with any length |
| **Arduino** (UNO, Nano, Mega...) | Any model with a USB port |
| **5V power supply** for the strip | Sized based on LED count (60 mA per LED at full brightness) |
| **Breadboard + jumper wires** | Just for wiring |
| **PC** with Windows / Linux / macOS | Must have a free USB port and F1 TV visible on screen |

#### Software

- **Python 3.8+**
- Libraries listed in `requirements.txt` (`opencv-python`, `numpy`, `mss`, `pyserial`)

### 🚀 Installation

**1. Clone the repository**

```bash
git clone https://github.com/Leinadf1/F1-led-sync.git
cd F1-led-sync
```

**2. Install Python dependencies**

```bash
pip install -r requirements.txt
```

**3. Upload the sketch to Arduino**

Open `Codicestriscia.ino` in the Arduino IDE and upload it. No modifications needed.

**4. Wire the LED strip**

- Strip **DIN** → Arduino **pin 6**
- Strip **+5V** → **external 5V power supply** (NOT from Arduino if you have more than 20 LEDs)
- Strip **GND** → **power supply GND** AND **Arduino GND** (common ground is mandatory)

**5. Run the script**

```bash
python F1.py
```

### ⚙️ Configuration

The `F1.py` file is ready to use out of the box. The only things you might want to change are at the top of the file:

```python
MONITOR_INDEX = 2  # 0=all, 1=primary, 2=secondary...

PILOTI = [
    {"code": "LEC", "settori": "blocco_leclerc_1.png", "tr": "Lec_TR.png"},
    {"code": "HAM", "settori": "blocco_hamilton_1.png", "tr": "Ham_TR.png"},
]
```

The system **automatically scales** all templates and zones to your screen resolution. Whether you run at 1080p, 1440p or 4K, you don't need to change anything.

### 🏎️ Adding or changing drivers

By default the system follows **Charles Leclerc** and **Lewis Hamilton**.

Adding other drivers requires creating **custom templates** (cropped screenshots of the F1 TV overlay) that must be pixel-perfect. A couple of pixels off and the recognition fails silently.

That's why it's not documented step-by-step: if you want to follow other drivers, **message me on Telegram** ([@delfino_cchione](https://t.me/delfino_cchione)) with:

- The driver(s) you want to follow
- Your screen resolution
- Your operating system

I'll prepare the correct templates and send them ready to use.

### 📁 Project structure

```
F1-led-sync/
├── F1.py                  # Main script
├── Codicestriscia.ino     # Arduino sketch
├── requirements.txt       # Python dependencies
├── README.md              # English readme (this file)
├── README.it.md           # Italian readme
├── LICENSE
│
│   # Templates (grayscale images)
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

> ⚠️ **Important**: all files must stay in the **same folder**.

### 🎮 Supported commands

| Command | Meaning | Effect |
|---|---|---|
| `G` | Green flag | Whole strip green |
| `Y` | Yellow flag / VSC / SC | Whole strip orange |
| `R` | Red flag | Whole strip red |
| `B` | Flashing yellow flag | Orange blink 250ms |
| `PEC` | Pit Exit Closed | First 10 LEDs red |
| `TR` | Incoming team radio | Last 5 LEDs red |
| `XXX` | No event | Strip off |
| `PYX`, `PVX`... | 3-sector status | 3 groups of 10 colored LEDs |

### 🛠️ Troubleshooting

**"No Arduino detected"**
- Check the USB cable
- On Windows, verify in *Device Manager* that a COM port appears
- On Linux: `sudo usermod -a -G dialout $USER`, then logout/login

**"Missing template: filename.png"**
- The file is not in the script folder
- The name doesn't match exactly (watch uppercase/lowercase)

**Flags not detected**
- Verify `MONITOR_INDEX` is the correct monitor
- F1 TV must be in **fullscreen**

### 📄 License

MIT — see [LICENSE](LICENSE).

### ⚠️ Disclaimer

Personal, unofficial project. Not affiliated with Formula 1, FOM, FIA, Sky or any team.

---

<div align="center">

**Made with ❤️ for the F1 community**

</div>
