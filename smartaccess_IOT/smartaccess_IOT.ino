// ============================================================
//  SmartAccess — Firmware ESP32 FINAL
//  Hardware : ESP32 + Shield + Lector M308 + LCD I2C 16x2
//  Baudrate M308 : 115200
//  Servo no bloqueante — serial siempre activo
//  Alimentación: DC 6.5–16V por jack barrel
// ============================================================

#include <WiFi.h>
#include <HTTPClient.h>
#include <ESP32Servo.h>
#include <ArduinoJson.h>
#include <LiquidCrystal_I2C.h>

// ------------------------------------------------------------
//  CONFIGURACIÓN
// ------------------------------------------------------------
const char* WIFI_SSID          = "SmartAccess";
const char* WIFI_PASSWORD      = "12345678";
const char* DJANGO_URL         = "http://192.168.137.1:8000/api/acceso/validar/";
const char* NOMBRE_DISPOSITIVO = "ESP32-Puerta1";

// ------------------------------------------------------------
//  PINES
// ------------------------------------------------------------
#define M308_RX_PIN    16
#define M308_TX_PIN    17
#define M308_BAUD    115200
#define M308_BEEP_PIN  18
#define SERVO_PIN      23

// LCD I2C — SDA=21, SCL=22 (pines I2C por defecto del ESP32)
// Dirección I2C más común: 0x27 — si no funciona, prueba 0x3F
LiquidCrystal_I2C lcd(0x27, 16, 2);

// ------------------------------------------------------------
//  SERVO NO BLOQUEANTE
// ------------------------------------------------------------
#define SERVO_ABIERTO   90
#define SERVO_CERRADO    0
#define SERVO_TIEMPO  3000   // ms abierto

bool          servoAbierto = false;
unsigned long servoTiempo  = 0;

// ------------------------------------------------------------
//  VARIABLES
// ------------------------------------------------------------
HardwareSerial m308(2);
Servo servo;
String        bufferQR   = "";
unsigned long ultimaLect = 0;
const unsigned long DEBOUNCE_MS = 2500;

// LCD — tiempo para volver a pantalla idle
unsigned long lcdMensajeTiempo = 0;
const unsigned long LCD_MSG_MS  = 3000;
bool          lcdEnMensaje     = false;

// ------------------------------------------------------------
//  HELPERS LCD
// ------------------------------------------------------------
void lcdClear() {
  lcd.clear();
}

// Escribe dos líneas; cadena vacía = línea en blanco
void lcdPrint(String linea1, String linea2 = "") {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(linea1.substring(0, 16));
  lcd.setCursor(0, 1);
  lcd.print(linea2.substring(0, 16));
}

// Mensaje temporal — vuelve a idle solo después de LCD_MSG_MS
void lcdMensajeTemporal(String linea1, String linea2 = "") {
  lcdPrint(linea1, linea2);
  lcdMensajeTiempo = millis();
  lcdEnMensaje     = true;
}

// Pantalla idle — se muestra cuando no hay actividad
void lcdIdle() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("  SmartAccess   ");
  lcd.setCursor(0, 1);
  lcd.print(" Escanee QR...  ");
}

// ------------------------------------------------------------
//  DECLARACIONES
// ------------------------------------------------------------
void conectarWiFi();
void validarConDjango(String codigo);
void abrirServo();
void beepPermitido();
void beepDenegado();
void beepError();

// ============================================================
//  SETUP
// ============================================================
void setup() {
  Serial.begin(115200);

  // Iniciar LCD
  lcd.init();
  lcd.backlight();
  lcdPrint("  SmartAccess   ", " Iniciando...   ");
  Serial.println("\n=== SmartAccess ESP32 + M308 ===");

  // UART2 para el M308
  m308.begin(M308_BAUD, SERIAL_8N1, M308_RX_PIN, M308_TX_PIN);
  Serial.println("M308 iniciado en UART2 (D16/D17)");
  lcdPrint("Lector M308", "OK");
  delay(800);

  // Beep pin como entrada por defecto
  pinMode(M308_BEEP_PIN, INPUT);

  // Servo
  servo.attach(SERVO_PIN);
  servo.write(SERVO_CERRADO);
  Serial.println("Servo en posición cerrada");
  lcdPrint("Servo", "Posicion cerrada");
  delay(800);

  // WiFi
  conectarWiFi();

  // Listo
  Serial.println("Listo. Esperando lectura M308...\n");
  lcdIdle();
}

// ============================================================
//  LOOP — no bloqueante
// ============================================================
void loop() {

  // --- Cerrar servo cuando expire el tiempo ---
  if (servoAbierto && (millis() - servoTiempo >= SERVO_TIEMPO)) {
    servo.write(SERVO_CERRADO);
    servoAbierto = false;
    Serial.println("Servo cerrado");
    lcdMensajeTemporal("Puerta cerrada", "");
  }

  // --- Volver a pantalla idle tras mensaje temporal ---
  if (lcdEnMensaje && (millis() - lcdMensajeTiempo >= LCD_MSG_MS)) {
    lcdEnMensaje = false;
    lcdIdle();
  }

  // --- Reconectar WiFi si se cae ---
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi caído, reconectando...");
    lcdMensajeTemporal("WiFi caido", "Reconectando...");
    conectarWiFi();
  }

  // --- Leer M308 ---
  while (m308.available()) {
    char c = (char)m308.read();

    if (c == '\r' || c == '\n') {
      bufferQR.trim();
      if (bufferQR.length() > 0) {
        unsigned long ahora = millis();
        if (ahora - ultimaLect > DEBOUNCE_MS) {
          ultimaLect = ahora;
          Serial.println("QR leído: " + bufferQR);

          // Mostrar código truncado en LCD (máx 16 chars)
          String codigoCorto = bufferQR.substring(0, 16);
          lcdPrint("QR detectado:", codigoCorto);
          delay(400);
          lcdPrint("Validando...", "Por favor espere");

          validarConDjango(bufferQR);
        } else {
          Serial.println("(duplicado ignorado)");
          lcdMensajeTemporal("Escaneo repetido", "Espere un momento");
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
//  ACTUADORES
// ============================================================
void abrirServo() {
  servo.write(SERVO_ABIERTO);
  servoAbierto = true;
  servoTiempo  = millis();
  Serial.println("Servo abierto — cerrará en " + String(SERVO_TIEMPO / 1000) + "s");
}

void beepPermitido() {
  Serial.println("✅ ACCESO PERMITIDO");
  lcdMensajeTemporal(" ACCESO PERMIT. ", "  Bienvenido!   ");
  abrirServo();
  pinMode(M308_BEEP_PIN, OUTPUT);
  digitalWrite(M308_BEEP_PIN, HIGH); delay(100);
  digitalWrite(M308_BEEP_PIN, LOW);
  pinMode(M308_BEEP_PIN, INPUT);
}

void beepDenegado() {
  Serial.println("❌ ACCESO DENEGADO");
  lcdMensajeTemporal(" ACCESO DENEGADO", "  No autorizado ");
  pinMode(M308_BEEP_PIN, OUTPUT);
  for (int i = 0; i < 3; i++) {
    digitalWrite(M308_BEEP_PIN, HIGH); delay(80);
    digitalWrite(M308_BEEP_PIN, LOW);  delay(80);
  }
  pinMode(M308_BEEP_PIN, INPUT);
}

void beepError() {
  Serial.println("⚠️  Error de conexión");
  lcdMensajeTemporal(" ERROR DE RED   ", "Revise conexion ");
  pinMode(M308_BEEP_PIN, OUTPUT);
  digitalWrite(M308_BEEP_PIN, HIGH); delay(200);
  digitalWrite(M308_BEEP_PIN, LOW);
  pinMode(M308_BEEP_PIN, INPUT);
}

// ============================================================
//  WIFI
// ============================================================
void conectarWiFi() {
  WiFi.disconnect(true);
  WiFi.mode(WIFI_OFF);
  delay(1000);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Conectando a WiFi");
  lcdPrint("Conectando WiFi", WIFI_SSID);

  int intentos = 0;
  while (WiFi.status() != WL_CONNECTED && intentos < 25) {
    delay(500);
    Serial.print(".");
    intentos++;

    // Animación de puntos en LCD
    String puntos = "";
    for (int p = 0; p < (intentos % 4); p++) puntos += ".";
    lcd.setCursor(0, 1);
    lcd.print(String(WIFI_SSID).substring(0, 12) + "   " );
    lcd.setCursor(12, 1);
    lcd.print(puntos + "   ");
  }

  if (WiFi.status() == WL_CONNECTED) {
    String ip = WiFi.localIP().toString();
    Serial.println("\nIP: " + ip);  
    lcdPrint("WiFi conectado!", ip);
    delay(1500);
    lcdIdle();
  } else {
    Serial.println("\n[ERROR] Sin WiFi.");
    lcdMensajeTemporal("ERROR: Sin WiFi", "Reintentando...");
  }
}