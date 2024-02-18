#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h> 

#define LEDPIN 33

const char* SSID = "NETWORK";
const char* PWD = "PASSWORD";

static float x = 0;
static float y = 0;

float phi;
float theta;

int d = 4;
int h = 1;
int a = 1;
float pi = 3.14159265358979;

Servo azimuth;
Servo zenith;

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

  phi = (atan(x/d) + pi/2)*180/pi;
  theta = (atan((y-h)/d) + pi/4)*180/pi;
  Serial.println(phi);
  Serial.println(theta);
  azimuth.write(map(phi, 0, 180, 0, 180));
  zenith.write(map(theta, 0, 180, 0, 180));
}

void setup() {
  Serial.begin(921600);
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(LEDPIN, OUTPUT);
  azimuth.attach(12);
  zenith.attach(13);
  azimuth.write(map(90, 0, 180, 0, 180));
  zenith.write(map(45, 0, 180, 0, 180));
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
  server.handleClient();
}