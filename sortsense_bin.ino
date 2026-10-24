/*
 SortSense smart-bin station firmware (ESP32-CAM, Arduino core)
 Flow: IR sensor detects item -> capture JPEG -> POST to gateway (/classify)
       -> gateway returns {"cat":"rec","conf":0.91}
       -> conf >= 0.80 : green LED + open that lid via servo
          conf <  0.80 : amber LED + buzzer, wait for user button press (4 buttons = 4 bins)
 Also reports HC-SR04 fill level every 10 min (MQTT/HTTP) for collection alerts.
*/
#include <WiFi.h>
#include <HTTPClient.h>
#include "esp_camera.h"
#include <ESP32Servo.h>

const char* SSID = "CAMPUS_WIFI"; const char* PASS = "********";
const char* GATEWAY = "http://192.168.1.50:8000/classify";
const float THRESH = 0.80;
#define IR_PIN 13
#define SERVO_PIN 14
#define LED_G 2
#define LED_A 4
#define BUZZ 15
#define TRIG 12
#define ECHO 16
Servo chute;                         // rotating chute: 0/60/120/180 deg = bio/rec/non/haz
int angleFor(String c){ return c=="bio"?0 : c=="rec"?60 : c=="non"?120 : 180; }

void setupCamera(){ camera_config_t c = {}; /* standard AI-Thinker pin map omitted for brevity */
  c.pixel_format = PIXFORMAT_JPEG; c.frame_size = FRAMESIZE_QVGA; c.jpeg_quality = 12; c.fb_count = 1;
  esp_camera_init(&c); }

void routeTo(String cat){ chute.write(angleFor(cat)); delay(1200); chute.write(90); }

void setup(){ Serial.begin(115200); pinMode(IR_PIN,INPUT); pinMode(LED_G,OUTPUT); pinMode(LED_A,OUTPUT);
  pinMode(BUZZ,OUTPUT); pinMode(TRIG,OUTPUT); pinMode(ECHO,INPUT); chute.attach(SERVO_PIN); chute.write(90);
  WiFi.begin(SSID,PASS); while(WiFi.status()!=WL_CONNECTED) delay(300); setupCamera(); }

float fillPercent(float depthCm=60){ digitalWrite(TRIG,LOW); delayMicroseconds(2); digitalWrite(TRIG,HIGH);
  delayMicroseconds(10); digitalWrite(TRIG,LOW); float d = pulseIn(ECHO,HIGH)*0.0343/2;
  return constrain(100*(1-d/depthCm),0,100); }

void loop(){
  if(digitalRead(IR_PIN)==LOW){                     // item placed on tray
    camera_fb_t* fb = esp_camera_fb_get(); if(!fb) return;
    HTTPClient h; h.begin(GATEWAY); h.addHeader("Content-Type","image/jpeg");
    int code = h.POST(fb->buf, fb->len); String body = h.getString(); h.end(); esp_camera_fb_return(fb);
    if(code==200){
      String cat = body.substring(body.indexOf("\"cat\":\"")+7, body.indexOf("\"cat\":\"")+10);
      float conf = body.substring(body.indexOf("\"conf\":")+7).toFloat();
      if(conf >= THRESH){ digitalWrite(LED_G,HIGH); routeTo(cat); digitalWrite(LED_G,LOW); }
      else { digitalWrite(LED_A,HIGH); tone(BUZZ,1000,200);  /* user presses one of 4 buttons -> routeTo + label upload */ }
    }
    delay(1500);
  }
  static unsigned long t=0; if(millis()-t>600000){ t=millis(); Serial.printf("fill=%.0f%%\n",fillPercent()); }
}
