//Bluetooth
#include "BluetoothSerial.h"

// Check if Bluetooth is available
#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth is not enabled! Please run `make menuconfig` to and enable it
#endif

BluetoothSerial SerialBT;


// Pin declaration
const int EN_PIN = 26; 
const int PH_PIN = 25;
const int C1 = 33; // Encoder Phase A
const int C2 = 34; // Encoder Phase B


// Motor Constants
const float reduction_ratio = 10.0;
// Encoder Constants (can be found in the datasheet, e.g: ROB-28633)
const int ppr_num = 7;
const float shaft_ppr = reduction_ratio * ppr_num; 
// Total pulses per full revolution of the output shaft


// Variables for speed calculation
volatile int pulse_count = 0;
unsigned long prev_time = 0;
float inst_rpm = 0;
float avg_rpm = 0;
float target_rpm = 120.0; 
float speed = 9500;
int curindex = 0;
#define size 10
float speeds[size] = {0};
bool full = false;
const float period_ms = 100; 

// PID constants
const float kP = 1.1;
const float kD = 0.2;
float error = 0;
float last_error = 0;                      


//Functions
void IRAM_ATTR countPulse();
float avgspeed();


void setup() {
  SerialBT.begin("Tensegrity-1");         //BT Name
  Serial.begin(115200);

  pinMode(EN_PIN, OUTPUT);
  pinMode(PH_PIN, OUTPUT);
  pinMode(C1, INPUT_PULLUP);
  pinMode(C2, INPUT_PULLUP);
  analogWriteResolution(EN_PIN, 16);
  attachInterrupt(digitalPinToInterrupt(C1), countPulse, RISING);

  delay (1000);
}


void loop() {
  //Receive data from Bluetooth
  if (SerialBT.available()) {
    String incoming = SerialBT.readStringUntil('\n');
    float new_target = incoming.toFloat();
    target_rpm = new_target;
    SerialBT.print("Target updated to: ");
    SerialBT.println(target_rpm);
  }

  //Keep track of current time
  unsigned long current_time = millis();
  
  if (current_time - prev_time >= period_ms) {
    prev_time = current_time;
    
    noInterrupts();
    long current_pulses = pulse_count;
    pulse_count = 0;
    interrupts();
    
    float rotations = (float)current_pulses / shaft_ppr;
    inst_rpm = (rotations * 1000 / period_ms) * 60.0;
    
    speeds[curindex] = inst_rpm;
    avg_rpm = avgspeed();
    curindex++;
    curindex %= size;

    // PID Calculation
    error = abs(target_rpm) - abs(avg_rpm);
    speed += kP * error + kD * (error - last_error) / (period_ms/1000);
    speed = constrain(speed, 0, 65535); 
    last_error = error;

    //Speed change
    if (target_rpm == 0) {analogWrite (EN_PIN, 0);}
    else if (target_rpm > 0) {
      digitalWrite (PH_PIN, HIGH);
      analogWrite (EN_PIN, speed);
    }
    else{
      digitalWrite (PH_PIN, LOW);
      analogWrite (EN_PIN, speed);
    }

    // Output to Serial Plotter (Wireless)
    // Formatting as "Value1,Value2" allows the Plotter to draw multiple lines
    SerialBT.print("Target RPM: ");
    SerialBT.print(target_rpm);
    SerialBT.print(", Average RPM: ");
    SerialBT.println(avg_rpm);
    
    // Also mirror to USB Serial for wired debugging
    Serial.print("Target:"); Serial.print(target_rpm);
    Serial.print(","); Serial.print("Avg:"); Serial.println(avg_rpm);
  }
}


void IRAM_ATTR countPulse() {
  // Check Phase B (C2) when Phase A (C1) rises
  if (digitalRead(C2) == LOW) {
    pulse_count--; // Clockwise
  } else {
    pulse_count++; // Counter-clockwise
  }
}


float avgspeed() {
  float sum = 0;
  for (int i=0; i< size; i++) {
    sum += speeds[i];
  }
  if (!full) {
    if (curindex == size-1) {full=true;}
    return float(sum/(curindex+1));
  }
  else {return float(sum/size);}
}