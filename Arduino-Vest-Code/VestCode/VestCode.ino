//VestCode project by fisk1234ost (https://github.com/fisk1234ost)
//based on CaiVR's Custom Haptic Vest V1  (Raspi Vest Script) 
//(https://github.com/CaiVR/CaiVR-Custom-Haptic-Vest-V1/tree/main/Raspi%20Vest%20Script)

// Please include ArduinoOSCWiFi.h to use ArduinoOSC on the platform
// which can use both WiFi and Ethernet
#include <ArduinoOSCWiFi.h>
// this is also valid for other platforms which can use only WiFi
// #include <ArduinoOSC.h>

#include "PCA9685.h"


// WiFi stuff
const char* ssid = "your-ssid";
const char* pwd = "your-password";
// for ArduinoOSC
const int recv_port = 1025;

PCA9685 pwmController;

//Motor Index Mapping (index used to send motor data to correct motor)
int motorMap [] = {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31};


void setup() {

  Serial.begin(115200);

  Wire.begin();
  pwmController.init();

  delay(2000);

  Serial.println("Program: VestCode");

  // WiFi stuff (no timeout setting for WiFi)
#if defined(ESP_PLATFORM) || defined(ARDUINO_ARCH_RP2040)
#ifdef ESP_PLATFORM
  WiFi.disconnect(true, true);  // disable wifi, erase ap info
#else
  WiFi.disconnect(true);  // disable wifi
#endif
  delay(1000);
  WiFi.mode(WIFI_STA);
#endif
  WiFi.begin(ssid, pwd);

  while (WiFi.status() != WL_CONNECTED) {
      Serial.print(".");
      delay(500);
#ifdef ARDUINO_UNOR4_WIFI
      static int count = 0;
      if (count++ > 20) {
          Serial.println("WiFi connection timeout, retry");
          WiFi.begin(ssid, pwd);
          count = 0;
      }
#endif
  }
  Serial.print("WiFi connected, IP = ");
  Serial.println(WiFi.localIP());
  // subscribe osc messages
  OscWiFi.subscribe(recv_port, "/h", onOscReceived);
  Serial.print('starting server');

//ignore this, its literally just the startup chime
  for (int i = 0; i < 16; i++) {
    pwmController.setChannelOn(i);
    pwmController.setChannelOn(i+16);
  }
  delay(500);
  for (int i = 0; i < 16; i++) {
    pwmController.setChannelOff(i);
    pwmController.setChannelOff(i+16);
  }
  delay(50);
  for (int i = 0; i < 16; i++) {
  pwmController.setChannelPWM(i, floatToDuty(0.6));
  pwmController.setChannelPWM(i+16, floatToDuty(0.6));
  }
  delay(150);
  for (int i = 0; i < 16; i++) {
    pwmController.setChannelOff(i);
    pwmController.setChannelOff(i+16);
  }
  delay(100);
  for (int i = 0; i < 16; i++) {
    pwmController.setChannelOn(i);
    pwmController.setChannelOn(i+16);
  }
  delay(500);
  for (int i = 0; i < 16; i++) {
    pwmController.setChannelOff(i);
    pwmController.setChannelOff(i+16);
  }
}

uint16_t floatToDuty(float e){
  return static_cast<uint16_t>(e*4096);
}

void onOscReceived(const OscMessage& m) {
  Serial.print(m.remoteIP());
  Serial.print(" ");
  Serial.print(m.remotePort());
  Serial.print(" ");
  Serial.print(m.size());
  Serial.print(" ");
  Serial.print(m.address());
  Serial.print(" ");
  Serial.println(m.arg<String>(0));
  handle_values(m.arg<String>(0));
}


void handle_values(String args){
  uint16_t valArray [32];
  
  String temp = "";
  int index = 0;
  for (int i = 0; i < args.length(); i++)
  {
    if (args[i] != ',')
    {
      temp += args[i];
    }
    else{
    valArray[index] = floatToDuty(temp.toFloat());
      index++;
      temp = "";
    }
  }
  valArray[index] = floatToDuty(temp.toFloat());



  Serial.print(valArray[0]);
  for (int i = 0; i < 32; i++) {
    pwmController.setChannelPWM(i, valArray[i]);
  }
   Serial.println();
}

void loop() {
    OscWiFi.parse(); // to receive osc
}
