#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h> 
#include "esp_wifi.h"
#include "esp_wpa2.h"
#include "wifipass.h"

// #include "wifipass.h"

#define LEDPIN 33

static float x = 0;
static float y = 0;

// const char* SSID = "UofT";
// const char* PWD = "PWD";

float phi;
float theta;

float phi_live;
float theta_live;

int d = 50;
int h = 100;
int a = 100;
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

  phi = (atan(x/d))*180/pi;
  theta = (atan(y/d))*180/pi;
  Serial.println(phi);
  Serial.println(theta);
}

void setup() {
  Serial.begin(921600);
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(LEDPIN, OUTPUT);
  azimuth.attach(12);
  zenith.attach(13);
  azimuth.write(map(90, 0, 180, 0, 180));
  zenith.write(map(45, 0, 180, 0, 180));

  WiFi.disconnect(true);
  WiFi.mode(WIFI_STA);
  esp_wifi_sta_wpa2_ent_set_username((uint8_t *)EAP_USERNAME, strlen(EAP_USERNAME));
  esp_wifi_sta_wpa2_ent_set_password((uint8_t *)EAP_PASSWORD, strlen(EAP_PASSWORD));
  esp_wifi_sta_wpa2_ent_enable(); //set config settings to enable function
  WiFi.begin(SSID);
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
  delay(1);
  phi_live = phi_live + (phi - phi_live)/40;
  theta_live = theta_live + (theta - theta_live)/40;

  azimuth.write(map(phi_live, 0, 180, 0, 180));
  zenith.write(map(theta_live, 0, 180, 0, 180));

  server.handleClient();
}