#include "BluetoothSerial.h"

BluetoothSerial SerialBT;
const String BTname = "Tensegrity-BT3";

// Pins
const int EN_PIN = 26; 
const int PH_PIN = 25;
const int C1 = 33; 
const int C2 = 34; 

// Constants
const float reduction_ratio = 10.0;
const int ppr_num = 7;
const float shaft_ppr = reduction_ratio * ppr_num; 

// Pulse timer
volatile unsigned long last_pulse_time = 0;
volatile long delta_micros = 0;
volatile int direction = 1;

// Average calculation
#define FILTER_SIZE 10
float rpm_buffer[FILTER_SIZE] = {0};
int filter_idx = 0;
float raw_rpm = 0;
float avg_rpm = 0;

// PID and Timing
unsigned long prev_loop_time = 0;
const float period_ms = 50; 
float target_rpm = 120.0;
float speed = 9500;
float error = 0;
float last_error = 0;

// PID Constants (Adjusted for 16-bit PWM)
const float kP = 1.2;
const float kD = 0.5;

void IRAM_ATTR countPulse();

void setup() {
  SerialBT.begin(BTname);
  Serial.begin(115200);
  pinMode(EN_PIN, OUTPUT);
  pinMode(PH_PIN, OUTPUT);
  pinMode(C1, INPUT_PULLUP);
  pinMode(C2, INPUT_PULLUP);
  analogWriteResolution(EN_PIN, 16);
  attachInterrupt(digitalPinToInterrupt(C1), countPulse, RISING);
}

void loop() {
  if (SerialBT.available()) {
    target_rpm = SerialBT.readStringUntil('\n').toFloat();
  }

  unsigned long current_time = millis();
  if (current_time - prev_loop_time >= period_ms) {
    prev_loop_time = current_time;

    // 1. Get Encoder data
    noInterrupts();
    long d_micros = delta_micros;
    int d_dir = direction;
    unsigned long last_p = last_pulse_time;
    interrupts();

    // 2. Calculate Raw RPM
    if (micros() - last_p > 250000) { // 0.25s timeout for stop
      raw_rpm = 0;
    } else if (d_micros > 0) {
      raw_rpm = (1000000.0 / d_micros / shaft_ppr) * 60.0 * d_dir;
    }

    // 3. Averaging out
    rpm_buffer[filter_idx] = raw_rpm;
    filter_idx = (filter_idx + 1) % FILTER_SIZE;
    float sum = 0;
    for(int i=0; i<FILTER_SIZE; i++) {
      sum += rpm_buffer[i];
    }
    avg_rpm = sum / FILTER_SIZE;

    // 4. Speed calculation
    error = abs(target_rpm) - abs(avg_rpm);
    speed += kP * error + kD * (error - last_error) / (period_ms / 1000.0);
    speed = constrain(speed, 0, 65535); 
    last_error = error;

    // 5. Speed and Direction change
    if (target_rpm == 0) {
      analogWrite(EN_PIN, 0);
      speed = 0;
    } 
    else if (target_rpm > 0) {
      digitalWrite(PH_PIN, HIGH);
      analogWrite(EN_PIN, (int)speed);
    } 
    else {
      digitalWrite(PH_PIN, LOW);
      analogWrite(EN_PIN, (int)speed);
    }

    // 6. Output for Plotter/Python
    SerialBT.println(BTname);
    SerialBT.print("Target:"); SerialBT.print(target_rpm); 
    SerialBT.print(",");
    SerialBT.print(" Avg:"); SerialBT.println(avg_rpm);
    
    Serial.print("Target:"); Serial.print(target_rpm);
    Serial.print(" Avg:"); Serial.println(avg_rpm);
  }
}

void IRAM_ATTR countPulse() {
  unsigned long now = micros();
  delta_micros = now - last_pulse_time;
  last_pulse_time = now;
  direction = (digitalRead(C2) == LOW) ? -1 : 1;
}