// ============================================================
//  SmartAccess — Firmware ESP32 FINAL
//  Hardware : ESP32 + Lector M308
//  Baudrate M308 : 115200
// ============================================================

#include <WiFi.h>
#include <HTTPClient.h>
#include <ESP32Servo.h>  
#include <ArduinoJson.h>

// ------------------------------------------------------------
//  CONFIGURACIÓN
// ------------------------------------------------------------
const char* WIFI_SSID          = "SmartAccess";
const char* WIFI_PASSWORD      = "12345678";
const char* DJANGO_URL = "http://192.168.137.1:8000/api/acceso/validar/";
const char* NOMBRE_DISPOSITIVO = "ESP32-Puerta1";

// ------------------------------------------------------------
//  PINES
// ------------------------------------------------------------
#define M308_RX_PIN    16      // GPIO16 RX2 ← TTLTXD del M308 (PIN4)
#define M308_TX_PIN    17      // GPIO17 TX2 → TTLRXD del M308 (PIN3)
#define M308_BAUD    115200    // ← baudrate confirmado
#define M308_BEEP_PIN  18      // GPIO18 → PIN7 BEEP del M308
#define SERVO_PIN  23
Servo servo;
// ------------------------------------------------------------
//  VARIABLES
// ------------------------------------------------------------
HardwareSerial m308(2);
String        bufferQR   = "";
unsigned long ultimaLect = 0;
const unsigned long DEBOUNCE_MS = 2500;

// ------------------------------------------------------------
//  DECLARACIONES
// ------------------------------------------------------------
void conectarWiFi();
void validarConDjango(String codigo);
void beepPermitido();
void beepDenegado();
void beepError();

// ============================================================
//  SETUP
// ============================================================
void setup() {
  Serial.begin(115200);
  Serial.println("\n=== SmartAccess ESP32 + M308 ===");

  m308.begin(M308_BAUD, SERIAL_8N1, M308_RX_PIN, M308_TX_PIN);
  pinMode(M308_BEEP_PIN, INPUT);
  servo.attach(SERVO_PIN);
  servo.write(0);   // posición cerrada al inicio
  delay(500);

  conectarWiFi();
  Serial.println("Listo. Esperando lectura M308...\n");
}

// ============================================================
//  LOOP
// ============================================================
void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi caído, reconectando...");
    conectarWiFi();
  }

  while (m308.available()) {
    char c = (char)m308.read();

    if (c == '\r' || c == '\n') {
      bufferQR.trim();
      if (bufferQR.length() > 0) {
        unsigned long ahora = millis();
        if (ahora - ultimaLect > DEBOUNCE_MS) {
          ultimaLect = ahora;
          Serial.println("QR leído: " + bufferQR);
          validarConDjango(bufferQR);
        } else {
          Serial.println("(duplicado ignorado)");
        }
        bufferQR = "";
      }
    } else {
      bufferQR += c;
    }
  }
}

// ============================================================
//  DJANGO
// ============================================================
void validarConDjango(String codigo) {
  Serial.println("Enviando a Django...");
  HTTPClient http;
  http.begin(DJANGO_URL);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(5000);

  StaticJsonDocument<256> body;
  body["codigo"]      = codigo;
  body["dispositivo"] = NOMBRE_DISPOSITIVO;

  String jsonStr;
  serializeJson(body, jsonStr);

  int httpCode = http.POST(jsonStr);
  Serial.println("HTTP: " + String(httpCode));

  if (httpCode == 200) {
    String respuesta = http.getString();
    Serial.println("Respuesta: " + respuesta);
    StaticJsonDocument<128> resp;
    if (!deserializeJson(resp, respuesta)) {
      String resultado = resp["acceso"].as<String>();
      if (resultado == "permitido") beepPermitido();
      else beepDenegado();
    }
  } else if (httpCode == 404) {
    Serial.println("Credencial no existe.");
    beepDenegado();
  } else {
    Serial.println("Error HTTP: " + String(httpCode));
    beepError();
  }

  http.end();
}

// ============================================================
//  BUZZER M308
// ============================================================
void beepPermitido() {
  Serial.println("✅ ACCESO PERMITIDO");

  servo.write(90);   // gira 90° — ajusta este valor según tu instalación
  delay(3000);       // mantiene abierto 3 segundos
  servo.write(0);    // vuelve a cerrar
  pinMode(M308_BEEP_PIN, OUTPUT);
  digitalWrite(M308_BEEP_PIN, HIGH); delay(600);
  digitalWrite(M308_BEEP_PIN, LOW);
  pinMode(M308_BEEP_PIN, INPUT);
}

void beepDenegado() {
  Serial.println("❌ ACCESO DENEGADO");
  pinMode(M308_BEEP_PIN, OUTPUT);
  for (int i = 0; i < 3; i++) {
    digitalWrite(M308_BEEP_PIN, HIGH); delay(150);
    digitalWrite(M308_BEEP_PIN, LOW);  delay(150);
  }
  pinMode(M308_BEEP_PIN, INPUT);
}

void beepError() {
  Serial.println("⚠️  Error de conexión");
  pinMode(M308_BEEP_PIN, OUTPUT);
  digitalWrite(M308_BEEP_PIN, HIGH); delay(1000);
  digitalWrite(M308_BEEP_PIN, LOW);
  pinMode(M308_BEEP_PIN, INPUT);
}

// ============================================================
//  WIFI
// ============================================================
void conectarWiFi() {

  WiFi.disconnect(true);   // ← agregar
  WiFi.mode(WIFI_OFF);     // ← agregar
  delay(1000);             // ← agregar

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Conectando a WiFi");

  int intentos = 0;
  while (WiFi.status() != WL_CONNECTED && intentos < 25) {
    delay(500);
    Serial.print(".");
    intentos++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nIP: " + WiFi.localIP().toString());
  } else {
    Serial.println("\n[ERROR] Sin WiFi.");
  }
}
