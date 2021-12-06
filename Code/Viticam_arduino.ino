#include "LowPower.h"
#include <Servo.h>
#include <Wire.h> //https://www.arduino.cc/en/reference/wire

//Variables
unsigned long timeprevious = millis();
int transistor = 2 ;






void setup() {
  //Serial.begin(9600);
  pinMode(transistor, OUTPUT);
}

void loop() {
  digitalWrite(transistor, LOW);   
  delay(500);
  blk(1);
  digitalWrite(transistor, HIGH);   

  //********* Wait 1min20 *********
  for (int k = 1; k <= 15; k++) { 
  LowPower.powerDown(SLEEP_8S, ADC_OFF, BOD_OFF);
  }
  delay(50);

  //********* sleepMode *********
  digitalWrite(transistor, LOW);   
  delay(50);
  blk(1);
  for (int i = 1; i <3150 ; i++){ //3600 pour 8h, 3150 avec le recalage
      LowPower.powerDown(SLEEP_8S, ADC_OFF, BOD_OFF);
  }
}

void blk(int j) {
  for (int i = 1; i <= j; i++) { 
    digitalWrite(13,HIGH);
    delay(25);
    digitalWrite(13,LOW);
    delay(100);
  }
}
