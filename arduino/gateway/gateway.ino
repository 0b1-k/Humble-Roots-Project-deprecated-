#include <PString.h>
#include <LowPower.h>
#include <RFM69.h>
#include <SPI.h>

#define SERIAL_BAUD     115200
#define NETWORK_ID      100
#define THIS_NODE_ID    1
#define FREQUENCY       RF69_433MHZ
#define ENCRYPTKEY      "1234567890123456"
#define LED             9
#define SERIAL_TIMEOUT  1

RFM69 radio;
char RadioIn[100];
char CmdInput[100];
PString RadioInData(RadioIn, sizeof(RadioIn));
PString Cmd(CmdInput, sizeof(CmdInput));

void setup() {
  Serial.begin(SERIAL_BAUD);
  Serial.setTimeout(SERIAL_TIMEOUT);
  delay(10);
  radio.initialize(FREQUENCY, THIS_NODE_ID, NETWORK_ID);
  radio.encrypt(ENCRYPTKEY);
  pinMode(LED, OUTPUT);
  Serial.println("Listening");
  Serial.flush();
}

void loop() {
  int byteCount = Serial.available();
  while (byteCount--){
    char data = Serial.read();
    if (Cmd.length() < Cmd.capacity()){
      if (data == '\r'){
        continue;
      } else if (data == '\n'){
        SendCommandToNode(CmdInput);
        Cmd.begin();
      } else {
        Cmd += data;
      }
    }
    else {
      Cmd.begin();
    }
  }
  
  if (radio.receiveDone() && radio.DATALEN > 0 && radio.TARGETID == THIS_NODE_ID) {
    if (radio.ACKRequested()){
      radio.sendACK();
    }
    RadioInData.begin();
    RadioInData += "node=";
    RadioInData += radio.SENDERID;
    RadioInData += "&rssi=";
    RadioInData += radio.RSSI;
    RadioInData += "&";
    int start = RadioInData.length();
    for(int i=0; i<radio.DATALEN; i++, start++){
      RadioIn[start] = radio.DATA[i];
    }
    RadioIn[start] = 0;
    Serial.println(RadioIn);
    Serial.flush();
  }
}

void SendCommandToNode(char* data){
  char* scratch = strstr(data, "node=");
  char* cmd = strstr(data, "&");
  if(scratch!=NULL){
    char* token = strtok(scratch, "&");
    if(token!=NULL){
      char* nodeData = strstr(token, "=");
      if(nodeData!=NULL){
        nodeData++;
        int nodeID = atoi(nodeData);
        Serial.print("node=");
        Serial.print(nodeID);
        Serial.print("&");
        Serial.print(++cmd);
        Serial.print("&tx=");
        if(radio.sendWithRetry(nodeID, cmd, strlen(cmd))){
          Serial.println("ack");
        } else {
          Serial.println("nack");
        }
      }
    }
  } else {
    Serial.print("Bad cmd: ");
    Serial.println(data);
  }
  Serial.flush();
}

