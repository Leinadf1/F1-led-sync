#include <Adafruit_NeoPixel.h>

#define PIN_STRISCIA 6
#define NUM_LEDS     60 

Adafruit_NeoPixel strip = Adafruit_NeoPixel(NUM_LEDS, PIN_STRISCIA, NEO_GRB + NEO_KHZ800);

unsigned long previousMillis = 0;
const long intervallo = 250; 
bool statoGiallo = false;
String comando = "XXX"; 

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
  strip.begin();
  strip.setBrightness(255);
  strip.clear();
  strip.show(); // Parte spento
  
  Serial.begin(9600);
}

uint32_t getColore(char c) {
  switch (c) {
    case 'V': return strip.Color(0, 255, 0);   
    case 'Y': return strip.Color(255, 140, 0); 
    case 'P': return strip.Color(144, 0, 255); 
    case 'R': return strip.Color(255, 0, 0);   
    default:  return strip.Color(0, 0, 0);     
  }
}

void loop() {
  if (Serial.available() > 0) {
    comando = Serial.readStringUntil('\n');
    comando.trim();
    comando.toUpperCase();
  }

  // --- 1. BANDIERE E MESSAGGI ---
  if (comando == "B") {  
    if (millis() - previousMillis >= intervallo) {
      previousMillis = millis();
      statoGiallo = !statoGiallo;
      uint32_t col = statoGiallo ? strip.Color(255, 140, 0) : 0;
      for(int i=0; i<NUM_LEDS; i++) strip.setPixelColor(i, col);
      strip.show(); 
    }
  } 
  else if (comando == "PEC") { // Pit Exit Closed -> Primi 10 LED rossi
    strip.clear();
    for(int i = 0; i <= 9; i++) {
      strip.setPixelColor(i, strip.Color(255, 0, 0));
    }
    strip.show();
  }
  else if (comando == "R") {  
    for(int i=0; i<NUM_LEDS; i++) strip.setPixelColor(i, strip.Color(255, 0, 0));
    strip.show();
  }
  else if (comando == "G") {  
    for(int i=0; i<NUM_LEDS; i++) strip.setPixelColor(i, strip.Color(0, 255, 0));
    strip.show();
  }
  else if (comando == "Y") {  
    for(int i=0; i<NUM_LEDS; i++) strip.setPixelColor(i, strip.Color(255, 140, 0));
    strip.show();
  }
  
  // --- 2. TEAM RADIO ---
  else if (comando == "TR") {
    strip.clear();
    for(int i = 50; i <= 59; i++) {
      strip.setPixelColor(i, strip.Color(255, 0, 0));
    }
    strip.show();
  }

  // --- 3. SETTORI ---
  else if (comando.length() == 3 && comando != "XXX") {
    strip.clear(); 
    for(int i = 0; i < NUM_LEDS; i++) {
      if (i >= 0 && i <= 9) strip.setPixelColor(i, getColore(comando[0]));
      else if (i >= 25 && i <= 34) strip.setPixelColor(i, getColore(comando[1]));
      else if (i >= 50 && i <= 59) strip.setPixelColor(i, getColore(comando[2]));
    }
    strip.show();
  }

  // --- 4. RESET ---
  else if (comando == "X" || comando == "XXX") {
    strip.clear();
    strip.show();
  }
}