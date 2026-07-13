const int EN_PIN    = 10;                  
const int PH_PIN    = 9;                  
const int SLEEP     = 8;                 
const int A         = 3;
const int B         = 2; 
const int MPU_SDA   = 4;
const int MPU_SCL   = 5;


void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  Serial.print ("hello");
  pinMode(EN_PIN, OUTPUT);
  pinMode(PH_PIN, OUTPUT);
  pinMode(SLEEP, OUTPUT);

  digitalWrite(SLEEP, 1);
  analogWriteResolution(EN_PIN, 14);

  digitalWrite (PH_PIN, HIGH);
  analogWrite (EN_PIN, 4000);
  delay(1000);

  analogWrite(EN_PIN, 0);
  delay(1000);

  digitalWrite (PH_PIN, LOW);
  analogWrite (EN_PIN, 4000);
  delay(1000);

  analogWrite(EN_PIN, 0);
  delay(1000);
}

void loop() {
  // put your main code here, to run repeatedly:

}
