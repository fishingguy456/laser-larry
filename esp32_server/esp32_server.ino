#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>

#define LEDPIN 33

const char* SSID = "NETWORK";
const char* PWD = "PASSWORD";

static double x = 0;
static double y = 0;

WebServer server(80);
StaticJsonDocument<250> jsonDocument;

void handleLED() {
  String body = server.arg("plain");
  deserializeJson(jsonDocument, body);
  int led_status = jsonDocument["ledOn"];
  Serial.println(led_status);
  if (led_status == 1) {
    digitalWrite(LED_BUILTIN, HIGH);
  } else {
    digitalWrite(LED_BUILTIN, LOW);
  }
  server.send(200, "application/json", "{}");
}

void handleXY() {
  String body = server.arg("plain");
  deserializeJson(jsonDocument, body);
  x = jsonDocument["x"];
  y = jsonDocument["y"];
  Serial.printf("x: %3f, y: %3f\n", x, y);
  server.send(200, "application/json", "{}");
}

void setup() {
  Serial.begin(921600);
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(LEDPIN, OUTPUT);
  WiFi.begin(SSID, PWD);
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(500);
  }
  Serial.print("Connected to IP: ");
  Serial.println(WiFi.localIP());
  server.on("/xy", HTTP_POST, handleXY);
  server.on("/led", HTTP_POST, handleLED);
  server.begin();
}

void loop() {
  // put your main code here, to run repeatedly:
  server.handleClient();
}
