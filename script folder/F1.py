# -*- coding: utf-8 -*-
"""
F1 LED Overlay - Sistema di controllo striscia LED WS2812B
basato sul riconoscimento dell'overlay F1 TV (regia internazionale).

F1 LED Overlay - WS2812B LED strip control system
based on F1 TV overlay recognition (international feed).

Risoluzione di riferimento template: 2560 x 1440
Reference template resolution: 2560 x 1440

Usa dxcam per la cattura a bassa latenza se disponibile (Windows),
altrimenti fallback automatico a mss.

Uses dxcam for low-latency capture when available (Windows),
otherwise automatic fallback to mss.
"""

import os
import sys
import time
import traceback
import logging
import cv2
import numpy as np
import serial
import serial.tools.list_ports

# --- BACKEND DI CATTURA / CAPTURE BACKEND -------------------
try:
    import dxcam
    _HAS_DXCAM = True
except ImportError:
    _HAS_DXCAM = False

from mss import mss

# ============================================================
#  LOGGING (solo console) / LOGGING (console only)
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("f1led")

# ============================================================
#  CONFIGURAZIONE / CONFIGURATION
# ============================================================

# Risoluzione dove sono stati presi i template.
# Resolution where templates were captured.
BASE_W = 2560
BASE_H = 1440

# Baudrate seriale verso Arduino / Serial baudrate to Arduino
BAUDRATE = 9600

# Indice del monitor da acquisire (mss: 0=all, 1=primary, 2=secondary...)
# Index of monitor to capture (mss: 0=all, 1=primary, 2=secondary...)
MONITOR_INDEX = 2

# --- PILOTI / DRIVERS ---------------------------------------
# Ogni pilota può avere template per i SETTORI ("settori"),
# per il TEAM RADIO ("tr"), oppure entrambi.
# Each driver can have templates for SECTORS ("settori"),
# for TEAM RADIO ("tr"), or both.
PILOTI = [
    {"code": "LEC", "settori": "blocco_leclerc_1.png", "tr": "Lec_TR.png"},
    {"code": "HAM", "settori": "blocco_hamilton_1.png", "tr": "Ham_TR.png"},
]

# Ordine di priorità quando due piloti matchano contemporaneamente.
# Priority order when two drivers match at the same time.
PRIORITA = [p["code"] for p in PILOTI]

# --- ZONE / ZONES -------------------------------------------
# Coordinate in pixel @ BASE_W x BASE_H.
# Pixel coordinates @ BASE_W x BASE_H.
ZONE_BANDIERE = [
    {'top': 58,   'left': 0,    'width': 551,  'height': 395},
    {'top': 414,  'left': 1286, 'width': 184,  'height': 192},
]
ZONE_RADAR = [
    {'top': 1176, 'left': 453,  'width': 1660, 'height': 221},
    {'top': 950,  'left': 1466, 'width': 760,  'height': 110},
]
ZONE_TR = [
    {'top': 573,  'left': 2103, 'width': 414,  'height': 284},
    {'top': 666,  'left': 2247, 'width': 168,  'height': 123},
]

# --- COSTANTI INTERNE / INTERNAL CONSTANTS ------------------
DISTANZA_Y_FULL     = 161
OFFSETS_FULL        = [-51, 112, 276]
LARGHEZZA_AREA_FULL = 122
ALTEZZA_AREA_FULL   = 4

# --- SOGLIE / THRESHOLDS ------------------------------------
TH_BANDIERA = 0.7
TH_PEC      = 0.8
TH_ANCHOR   = 0.80
TH_TR       = 0.85
TH_SET_PX   = 10

# ============================================================
#  RILEVAMENTO PORTA ARDUINO / ARDUINO PORT DETECTION
# ============================================================

ARDUINO_VID_PID = {
    (0x1A86, 0x7523),  # CH340
    (0x1A86, 0x5523),  # CH341A
    (0x0403, 0x6001),  # FTDI FT232
    (0x2341, 0x0043),  # Arduino UNO
    (0x2341, 0x0042),  # Arduino Mega
    (0x2341, 0x8036),  # Arduino Leonardo
    (0x2A03, 0x0043),  # Arduino.org UNO
    (0x10C4, 0xEA60),  # CP2102
}

def trova_porta_arduino():
    try:
        porte = list(serial.tools.list_ports.comports())
    except Exception as e:
        log.error(f"Errore scansione porte seriali / serial scan error: {e}")
        return None

    if not porte:
        return None

    for p in porte:
        if p.vid is not None and (p.vid, p.pid) in ARDUINO_VID_PID:
            return p.device

    for p in porte:
        testo = f"{p.description} {p.manufacturer} {p.device}".lower()
        if any(k in testo for k in ("arduino", "ch340", "ch341", "ftdi", "usb serial")):
            return p.device

    if len(porte) == 1:
        return porte[0].device

    return None

# ============================================================
#  SCALATURA / SCALING
# ============================================================

def scale_zone(z, sx, sy):
    return {
        'top':    int(round(z['top']    * sy)),
        'left':   int(round(z['left']   * sx)),
        'width':  int(round(z['width']  * sx)),
        'height': int(round(z['height'] * sy)),
    }

def scale_int(v, s):
    return max(1, int(round(v * s)))

def scale_template(t, sx, sy):
    if t is None:
        return None
    h, w = t.shape[:2]
    new_w = max(1, int(round(w * sx)))
    new_h = max(1, int(round(h * sy)))
    if (new_w, new_h) == (w, h):
        return t
    interp = cv2.INTER_AREA if sx < 1.0 else cv2.INTER_CUBIC
    return cv2.resize(t, (new_w, new_h), interpolation=interp)

# ============================================================
#  CARICAMENTO TEMPLATE / TEMPLATE LOADING
# ============================================================

def carica(path):
    if not path:
        return None
    full = os.path.join(BASE_DIR, path)
    img = cv2.imread(full, 0)
    if img is None:
        log.warning(f"⚠️  Template mancante / missing: {path}")
    return img

FLAG_FILES = {
    'pit_closed': 'pit_closed.png',
    'gialla':     'gialla.png',
    'rossa':      'rossa.png',
    'verde':      'verde.png',
    'vsc':        'vsc.png',
    'sc':         'sc.png',
    'vsc_end':    'vsc end.png',
    'sc_end':     'sc end.png',
}

# ============================================================
#  FUNZIONI DI MATCH / MATCH FUNCTIONS
# ============================================================

def check_template(img_gray, template, thresh=0.7):
    if template is None:
        return False
    if template.shape[0] > img_gray.shape[0] or template.shape[1] > img_gray.shape[1]:
        return False
    res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
    _, mv, _, _ = cv2.minMaxLoc(res)
    return mv > thresh

def match_fixed(img_gray, template):
    if template is None:
        return -1, None
    if template.shape[0] > img_gray.shape[0] or template.shape[1] > img_gray.shape[1]:
        return -1, None
    res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
    _, mv, _, ml = cv2.minMaxLoc(res)
    return mv, ml

def read_settori_bgra(roi_bgra, ax, ay, offsets, dist_y, larg, alt):
    lett = []
    for off_x in offsets:
        x1 = ax + off_x
        y1 = ay + dist_y
        x2 = x1 + larg
        y2 = y1 + alt
        zb = roi_bgra[max(0, y1):min(y2, roi_bgra.shape[0]),
                      max(0, x1):min(x2, roi_bgra.shape[1])]
        if zb.size == 0:
            lett.append("X"); continue
        zh = cv2.cvtColor(cv2.cvtColor(zb, cv2.COLOR_BGRA2BGR), cv2.COLOR_BGR2HSV)
        if np.sum(cv2.inRange(zh, np.array([135, 100, 100]), np.array([170, 255, 255])) > 0) > TH_SET_PX:
            lett.append("P")
        elif np.sum(cv2.inRange(zh, np.array([35, 70, 70]), np.array([85, 255, 255])) > 0) > TH_SET_PX:
            lett.append("V")
        elif np.sum(cv2.inRange(zh, np.array([15, 100, 100]), np.array([35, 255, 255])) > 0) > TH_SET_PX:
            lett.append("Y")
        else:
            lett.append("X")
    return "".join(lett)

def check_bandiere(gray_roi, flags):
    if check_template(gray_roi, flags.get('pit_closed'), TH_PEC):
        return "PEC"
    if check_template(gray_roi, flags.get('vsc_end')) or check_template(gray_roi, flags.get('sc_end')):
        return "B"
    if check_template(gray_roi, flags.get('gialla'), TH_BANDIERA):
        return "B"
    if check_template(gray_roi, flags.get('rossa'), TH_PEC):
        return "R"
    if check_template(gray_roi, flags.get('vsc')) or check_template(gray_roi, flags.get('sc')):
        return "Y"
    if 'verde' in flags and check_template(gray_roi, flags['verde'], TH_PEC):
        return "G"
    return ""

# ============================================================
#  SETUP (template + Arduino)
# ============================================================

def setup():
    flag_full = {}
    for k, f in FLAG_FILES.items():
        t = carica(f)
        if t is not None:
            flag_full[k] = t

    piloti_tpl = []
    for p in PILOTI:
        code = p["code"]
        sett = carica(p.get("settori")) if p.get("settori") else None
        tr   = carica(p.get("tr"))      if p.get("tr")      else None
        if sett is None and tr is None:
            log.warning(f"⚠️  Pilota senza template / Driver with no template: {code}")
            continue
        piloti_tpl.append({"code": code, "settori": sett, "tr": tr})

    if not piloti_tpl:
        log.warning("⚠️  Nessun pilota valido / No valid drivers")

    porta = os.environ.get("F1LED_PORT") or trova_porta_arduino()
    arduino = None

    if porta is None:
        log.warning("⚠️  Nessun Arduino rilevato. Lo script gira comunque (solo debug).")
        log.warning("⚠️  No Arduino detected. Script keeps running (debug only).")
    else:
        try:
            arduino = serial.Serial(porta, BAUDRATE, timeout=1)
            time.sleep(2)
            log.info(f"✅ Arduino connesso / connected: {porta}")
        except Exception as e:
            log.error(f"⚠️  Errore apertura / error opening {porta}: {e}")
            arduino = None

    return flag_full, piloti_tpl, arduino

# ============================================================
#  SETUP CATTURA SCHERMO / SCREEN CAPTURE SETUP
# ============================================================

def setup_capture():
    """
    Prova a usare dxcam (bassa latenza, Windows only).
    Se il monitor richiesto non esiste, usa il primario con dxcam.
    Fallback a mss solo se dxcam non è disponibile o fallisce del tutto.
    """
    use_dxcam = _HAS_DXCAM
    camera = None
    sct = None
    mon = None
    real_w = real_h = 0

    if use_dxcam:
        try:
            output_idx = max(0, MONITOR_INDEX - 1)

            try:
                camera = dxcam.create(output_idx=output_idx, output_color="BGRA")
            except IndexError:
                if output_idx != 0:
                    log.warning("⚠️  dxcam: indice non valido, provo col primario.")
                    log.warning("⚠️  dxcam: invalid index, trying primary.")
                    camera = dxcam.create(output_idx=0, output_color="BGRA")
                else:
                    raise

            if camera is None:
                use_dxcam = False
            else:
                # Warm-up: il primo grab può restituire None.
                # Warm-up: first grab may return None.
                frame = None
                for _ in range(20):
                    frame = camera.grab()
                    if frame is not None:
                        break
                    time.sleep(0.05)
                if frame is None:
                    try:
                        camera.release()
                    except Exception:
                        pass
                    use_dxcam = False
                    camera = None
                else:
                    real_h, real_w = frame.shape[:2]
                    log.info("⚡ Backend cattura / capture backend: dxcam (low latency)")
        except Exception as e:
            log.warning(f"⚠️  dxcam non disponibile, uso mss / dxcam not available, using mss: {e}")
            use_dxcam = False
            camera = None

    if not use_dxcam:
        sct = mss()
        if MONITOR_INDEX >= len(sct.monitors):
            log.warning(f"⚠️  Monitor {MONITOR_INDEX} non disponibile, uso il primario.")
            log.warning(f"⚠️  Monitor {MONITOR_INDEX} not available, using primary.")
            mon = sct.monitors[1]
        else:
            mon = sct.monitors[MONITOR_INDEX]
        real_w = mon['width']
        real_h = mon['height']
        log.info("🖥️  Backend cattura / capture backend: mss")

    return use_dxcam, camera, sct, mon, real_w, real_h

# ============================================================
#  MAIN LOOP
# ============================================================

def main():
    flag_full, piloti_tpl, arduino = setup()

    # Variabili scalate (inizializzate dalle costanti base).
    # Scaled variables (initialized from base constants).
    zone_bandiere = [dict(z) for z in ZONE_BANDIERE]
    zone_radar    = [dict(z) for z in ZONE_RADAR]
    zone_tr       = [dict(z) for z in ZONE_TR]
    distanza_y    = DISTANZA_Y_FULL
    offsets       = list(OFFSETS_FULL)
    larghezza     = LARGHEZZA_AREA_FULL
    altezza       = ALTEZZA_AREA_FULL

    use_dxcam, camera, sct, mon, real_w, real_h = setup_capture()

    try:
        sx = real_w / BASE_W
        sy = real_h / BASE_H
        s_avg = (sx + sy) / 2.0

        log.info(f"📺 Risoluzione rilevata / Detected resolution: {real_w}x{real_h}")

        # Scala zone / Scale zones
        zone_bandiere = [scale_zone(z, sx, sy) for z in zone_bandiere]
        zone_radar    = [scale_zone(z, sx, sy) for z in zone_radar]
        zone_tr       = [scale_zone(z, sx, sy) for z in zone_tr]

        # Scala costanti interne / Scale internal constants
        distanza_y = scale_int(distanza_y, s_avg)
        offsets    = [int(round(o * s_avg)) for o in offsets]
        larghezza  = scale_int(larghezza, s_avg)
        altezza    = scale_int(altezza, s_avg)

        # Scala template / Scale templates
        for k, v in list(flag_full.items()):
            if v is not None:
                flag_full[k] = scale_template(v, sx, sy)
        for p in piloti_tpl:
            if p["settori"] is not None:
                p["settori"] = scale_template(p["settori"], sx, sy)
            if p["tr"] is not None:
                p["tr"] = scale_template(p["tr"], sx, sy)

        log.info("🏎️  SISTEMA F1 ONLINE ATTIVO / F1 SYSTEM ONLINE")

        ultimo_inviato = ""
        locked = None
        n_piloti_settori = len([p for p in piloti_tpl if p["settori"] is not None])

        while True:
            # --- Cattura frame / Frame capture ---
            try:
                if use_dxcam:
                    img_bgra = camera.grab()
                    if img_bgra is None:
                        time.sleep(0.001)
                        continue
                else:
                    img_bgra = np.array(sct.grab(mon))
            except Exception as e:
                log.error(f"❌ Errore cattura schermo / screen grab error: {e}")
                time.sleep(1)
                continue

            # --- 1. BANDIERE / FLAGS ---
            cmd_bandiere = ""
            for z in zone_bandiere:
                x0, y0 = z['left'], z['top']
                x1, y1 = x0 + z['width'], y0 + z['height']
                roi = img_bgra[y0:y1, x0:x1]
                if roi.size == 0:
                    continue
                g = cv2.cvtColor(roi, cv2.COLOR_BGRA2GRAY)
                res = check_bandiere(g, flag_full)
                if res != "":
                    cmd_bandiere = res
                    break

            # --- 2. ANCORE + SETTORI / ANCHORS + SECTORS ---
            detections = {}
            for z in zone_radar:
                x0, y0 = z['left'], z['top']
                x1, y1 = x0 + z['width'], y0 + z['height']
                roi = img_bgra[y0:y1, x0:x1]
                if roi.size == 0:
                    continue
                g = cv2.cvtColor(roi, cv2.COLOR_BGRA2GRAY)

                for p in piloti_tpl:
                    if p["settori"] is None:
                        continue
                    v, loc = match_fixed(g, p["settori"])
                    if v > TH_ANCHOR and loc is not None:
                        sett = read_settori_bgra(roi, loc[0], loc[1],
                                                 offsets, distanza_y,
                                                 larghezza, altezza)
                        if p["code"] not in detections or v > detections[p["code"]][0]:
                            detections[p["code"]] = (v, sett)

                if len(detections) >= n_piloti_settori:
                    break

            # --- 3. LOCK ISTANTANEO / INSTANT LOCK ---
            cmd_settori = "XXX"
            if locked is not None and locked not in detections:
                locked = None

            if locked is None:
                for code in PRIORITA:
                    if code in detections:
                        v, sett = detections[code]
                        if sett != "XXX":
                            locked = code
                            cmd_settori = sett
                            break
            else:
                cmd_settori = detections[locked][1]

            # --- 4. TEAM RADIO ---
            cmd_tr = ""
            if locked is None and not detections:
                for z in zone_tr:
                    x0, y0 = z['left'], z['top']
                    x1, y1 = x0 + z['width'], y0 + z['height']
                    roi = img_bgra[y0:y1, x0:x1]
                    if roi.size == 0:
                        continue
                    g = cv2.cvtColor(roi, cv2.COLOR_BGRA2GRAY)
                    for p in piloti_tpl:
                        if p["tr"] is not None and check_template(g, p["tr"], TH_TR):
                            cmd_tr = "TR"
                            break
                    if cmd_tr:
                        break

            # --- 5. PRIORITÀ FINALE / FINAL PRIORITY ---
            if cmd_bandiere != "":
                cmd_finale = cmd_bandiere
            elif cmd_settori != "XXX":
                cmd_finale = cmd_settori
            elif cmd_tr != "":
                cmd_finale = cmd_tr
            else:
                cmd_finale = "XXX"

            if cmd_finale != ultimo_inviato:
                if arduino:
                    try:
                        arduino.write((cmd_finale + "\n").encode())
                    except Exception as e:
                        log.error(f"❌ Errore invio seriale / serial send error: {e}")
                ultimo_inviato = cmd_finale

            time.sleep(0.01)

    finally:
        # Rilascia dxcam / Release dxcam
        if camera is not None:
            try:
                camera.release()
            except Exception:
                pass
        # Chiudi mss / Close mss
        if sct is not None:
            try:
                sct.close()
            except Exception:
                pass
        # Chiudi seriale / Close serial
        if arduino:
            try:
                arduino.close()
            except Exception:
                pass

# ============================================================
#  ENTRY POINT
# ============================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("\n👋 Chiusura in corso... / Shutting down...")
    except Exception as e:
        log.error("❌ ERRORE / ERROR:")
        log.error(traceback.format_exc())
    finally:
        try:
            input("\nPremi INVIO per chiudere... / Press ENTER to close...")
        except Exception:
            pass
