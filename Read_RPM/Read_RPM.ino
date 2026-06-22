// Pin declaration
const int EN_PIN = 26; 
const int PH_PIN = 25;
const int C1 = 33; // Encoder Phase A
const int C2 = 34; // Encoder Phase B


// Motor Constants
double reduction_ratio = 10.0;
// Encoder Constants (can be found in the datasheet, e.g: ROB-28633)
int ppr_num = 7;
double shaft_ppr = reduction_ratio * ppr_num; 
// Total pulses per full revolution of the output shaft


// Variables for speed calculation
volatile long pulse_count = 0;
unsigned long prev_time = 0;
double rpm = 0;
double target_rpm = 120.0;
double speed = 65536*25/100;


// Interrupt Service Routine (ISR) - called every time C1 goes HIGH
void IRAM_ATTR countPulse() {
  pulse_count++;
}


void setup() {
  Serial.begin(115200);
  pinMode(EN_PIN, OUTPUT);
  pinMode (PH_PIN, OUTPUT);
  analogWriteResolution(EN_PIN, 16);
  analogWrite(EN_PIN, speed);
  digitalWrite (PH_PIN, HIGH);
  pinMode(C1, INPUT_PULLUP);
  pinMode(C2, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(C1), countPulse, RISING);
  delay (1000);
}


int curindex = 0;
int size = 100;
double sum = 0;
double Kp = 0.4;

void loop() {
  unsigned long current_time = millis();
  
  // Calculate speed every 100ms
  if (current_time - prev_time >= 100) {
    noInterrupts();
    long current_pulses = pulse_count;
    pulse_count = 0;                      // RESET the counter to zero
    interrupts();
    double rotations = (double)current_pulses / shaft_ppr;
    rpm = (rotations / 0.5) * 60.0;
    Serial.print("Pulses: ");
    Serial.print(current_pulses);
    Serial.print(" | Speed: ");
    Serial.print(rpm);
    Serial.println(" RPM");

    prev_time = current_time;

  if (curindex < size){
    sum += rpm;
    curindex+=1;
  }

  else {
    Serial.println(sum/size);
    analogWrite (EN_PIN, 0);
    }
  }

}