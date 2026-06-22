/**
  * This is the code for Tensegrity microcontroller.
  * Upload this code to the microcontroller
  * before running the Python BLE communication code.
*/

/*    Components list     */
/*    Motor driver: https://www.pololu.com/product/2990   */
/*    Motor + Encoder: https://www.amazon.com/Waveshare-All-Metal-Precision-Reduction-Connector/dp/B0CW1TCCTL */
/*    MPU 6050: https://www.dfrobot.com/product-880.html  */
/*    Note: I used Electronic Cats library for the MPU6050*/

/*    Libraries list     */
/*    BLE: From ESP-32 Board Manager Built-in Libs  */
/*    MPU6050: https://github.com/electroniccats/mpu6050    */
/*    Queue: https://github.com/EinarArnason/ArduinoQueue   */

#include <BLEDevice.h> 
#include <BLEUtils.h> 
#include <BLEServer.h>
#include <BLE2902.h>
#include <I2Cdev.h>
#include <MPU6050.h>

/*========================================================*/
/*                Variables declaration                   */

/*
String name = "Tensegrity-BT1";
#define SERVICE_UUID        "afcdeba4-f8a9-4ca1-baa5-021afe634998"
#define CHARACTERISTIC_UUID "83147421-2684-43ec-af39-58533d866c8e"

String name = "Tensegrity-BT2";
#define SERVICE_UUID        "8aaba9c2-7f68-49d6-97cb-b9783ea29fd6"
#define CHARACTERISTIC_UUID "2a612f78-13b2-4b3a-bab8-50b00d2f003f"

String name = "Tensegrity-BT3";
#define SERVICE_UUID        "e132a2ee-a68a-4b4b-98fa-29ef8bbc0be2"
#define CHARACTERISTIC_UUID "ccba8d13-8743-45f7-9fd9-69a20a9acddc"
*/


/*      BLE variables: Change name and UUID here      */
String name = "Tensegrity-BT2";
// Change it for each of the active PCB
#define SERVICE_UUID        "8aaba9c2-7f68-49d6-97cb-b9783ea29fd6"
#define CHARACTERISTIC_UUID "2a612f78-13b2-4b3a-bab8-50b00d2f003f"
BLECharacteristic *pGlobalCharacteristic; 
bool sprint = true;


/*            Declare the GPIO pins here              */
const int EN_PIN    = 25;                  //Note: Old board uses 26
const int PH_PIN    = 26;                  //Note: Old board uses 25
const int SLEEP     = 27;                  //Note: Not on old board
const int A         = 33;
const int B         = 34; 
const int MPU_SDA   = 21;
const int MPU_SCL   = 22;
const int INT       = 9;


/*                Declare MPU6050 here                */
MPU6050 mpu;
#define OUTPUT_READABLE_ACCELGYRO
//#define OUTPUT_BINARY_ACCELGYRO
int16_t ax, ay, az; 
int16_t gx, gy, gz; 
int     calibrate_size = 200;
bool    blinkState;


/*         Declare Encoder specifications here        */
const float reduction_ratio = 10.0;         //Since the motor is 1:10 reduction
const int   ppr_num = 7;                    //Inside encoder datasheet
const float hall_resolution = reduction_ratio * ppr_num; 


/*         Create a new queue for the message        */
QueueHandle_t bleMessageQueue;
const int QUEUE_SIZE = 10;

//Encoder Pulse timer variables
volatile unsigned long last_pulse_time = 0;
volatile long delta_micros = 0;
volatile int  direction = 1;                //1 is CCW

//Stall Detection variables
volatile unsigned long stall_timer = 0;
const unsigned long STALL_THRESHOLD_MS = 1000;  //time before killing power
const float MIN_SAFE_RPM = 20.0;                //minimum RPM to be considered "moving"
const int MAX_SPEED = 66535 * 20/100;           //pwm driver is 16-bit

// Average calculation variables
#define FILTER_SIZE 10
float rpm_buffer[FILTER_SIZE] = {0};
int filter_idx = 0;
float raw_rpm = 0;
float avg_rpm = 0;

// PID and Timing variables
unsigned long prev_loop_time = 0;
unsigned long prev_noti_time = 0;
float target_rpm = 0.0;                         //Set initial RPM here
float speed = 0;                                //Set initial speed here


// Callback class to handle incoming BLE writes
class MyCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
      String value = pCharacteristic->getValue().c_str();
      if (value.length() > 0) {
        target_rpm = value.toFloat();
        target_rpm = constrain(target_rpm, -500, 500);
        Serial.print("New Target RPM via BLE: ");
        Serial.println(target_rpm);
      }
    }
};

//Class to make the BLE discoverable again after disconnecting.
class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
      Serial.println(">>> Device Connected");
    };

    void onDisconnect(BLEServer* pServer) {
      xTaskCreate(
            [](void* param) {
                vTaskDelay(pdMS_TO_TICKS(500)); // Wait 500ms for radio to clear
                BLEDevice::startAdvertising();   // Restart advertising
                Serial.println(">>> Advertising Restarted via Background Task");
                vTaskDelete(NULL);               // Delete this task (clean up)
            }, 
            "restart_ble", 2048, NULL, 1, NULL
        );
    }
};



/*========================================================*/
/*            Function  and Task Prototype                */
void IRAM_ATTR countPulse();
void pin_setup();
void mpu_setup();
void ble_setup();


/*========================================================*/
/*                  Main setup function                   */
void setup() {

  Serial.begin (115200);
  pin_setup();
  ble_setup();

  target_rpm = 120;
  xTaskCreate (encoderTask, "Encoder Task", 2048, NULL, 1, NULL);
  xTaskCreate (motorTask, "Motor Task", 2048, NULL, 2, NULL);
}


/*========================================================*/
/*                  Main loop function                   */
void loop() {
}


/*========================================================*/
/*                          Tasks                         */
void encoderTask (void *parameter) {
  float running_sum = 0;
  while (1) {
    // 1. Get Encoder data (pulse period)
    noInterrupts();
    long d_micros = delta_micros;
    int d_dir = direction;
    unsigned long last_p = last_pulse_time;
    interrupts();


    // 2. Calculate Raw RPM
    if (micros() - last_p > 100000) { // 0.1s timeout for stop
      raw_rpm = 0;
    } 
    else if (d_micros > 0) {
      raw_rpm = (1000000.0 / d_micros / hall_resolution) * 60.0 * d_dir;
    }


    // 3. Averaging out (the RPM)
    running_sum -= rpm_buffer[filter_idx];
    rpm_buffer[filter_idx] = raw_rpm;
    filter_idx = (filter_idx + 1) % FILTER_SIZE;
    running_sum += raw_rpm;
    avg_rpm = running_sum / FILTER_SIZE;

    //4. Delay
    vTaskDelay (pdMS_TO_TICKS(5));
  }
}


void motorTask (void *parameter) {
  // PID  Controller Variables (Adjusted for 16-bit PWM)
  const float kP = 2;
  const float kI = 0.5;
  float error = 0;
  double errorIntegral = 0;

  TickType_t xLastWakeTime = xTaskGetTickCount();
  const TickType_t xPeriod = pdMS_TO_TICKS(75);
  const float dt = 0.075;

  while (1){

    vTaskDelayUntil(&xLastWakeTime, xPeriod);

    float reading = avg_rpm; 
    float setpoint = target_rpm;

    //PID Output calculation
    error = abs(setpoint) - abs(reading);
    errorIntegral += error * dt;

    // Anti-windup clamping to prevent memory overflow
    double max_integral_clamp = 65535.0 / (kI > 0 ? kI : 1.0);
    if (errorIntegral > max_integral_clamp)   errorIntegral = max_integral_clamp;
    if (errorIntegral < 0)                    errorIntegral = 0;

    double pTerm = kP * error;
    double iTerm = kI * errorIntegral;
    double speed = pTerm + iTerm;
    speed = constrain(speed, 0, 65535);


    //Stall Detection Logic
    if (abs(target_rpm) > 0 && speed > MAX_SPEED && abs(avg_rpm) < MIN_SAFE_RPM) {
      if (stall_timer == 0)   {stall_timer = millis();} 
      else if (millis() - stall_timer > STALL_THRESHOLD_MS) { // STALL TRIGGERED
        target_rpm = 0; speed = 0; errorIntegral=0; stall_timer = 0; // Reset timer
      }
    } 
    else { stall_timer = 0; }


    // 6. Speed and Direction change
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

    Serial.println(reading);
  }
}


void bleTask (void *parameter) {
  unsigned long now = millis();
  while (1) {
    if (now - prev_noti_time >= 800) {
    prev_noti_time = now;
    // 6. Update BLE Notify and Serial
    String output = "Tar:" + String(target_rpm) + "|Avg:" + String(avg_rpm);
    pGlobalCharacteristic->setValue(output.c_str());
    pGlobalCharacteristic->notify();
    }
  }
}


/*========================================================*/
/*            Interrupt Service Routine                   */
void IRAM_ATTR countPulse() {
  unsigned long now = micros();
  delta_micros = now - last_pulse_time;
  last_pulse_time = now;
  direction = (digitalRead(B) == LOW) ? -1 : 1;
}


/*========================================================*/
/*                  Set up functions                      */
void pin_setup(){
  /*Set up PIN direction and initial level*/
  pinMode(EN_PIN, OUTPUT);
  pinMode(PH_PIN, OUTPUT);
  pinMode(SLEEP, OUTPUT);

  pinMode(INT, INPUT_PULLUP);
  pinMode(A, INPUT_PULLUP);
  pinMode(B, INPUT_PULLUP);

  analogWriteResolution(EN_PIN, 16);
  digitalWrite  (PH_PIN, 0);
  analogWrite   (EN_PIN, 0);
  digitalWrite  (SLEEP, 1);

 /*Add an attach interrupt here to INT pin*/
  attachInterrupt(digitalPinToInterrupt(A), countPulse, RISING);
}


void mpu_setup(){
  /*--Start I2C interface--*/
  #if I2CDEV_IMPLEMENTATION == I2CDEV_ARDUINO_WIRE
    Wire.begin(); 
  #elif I2CDEV_IMPLEMENTATION == I2CDEV_BUILTIN_FASTWIRE
    Fastwire::setup(400, true);
  #endif

  while (!Serial) {}

  /*Initialize device and check connection*/ 
  Serial.println("Initializing MPU...");
  mpu.initialize();
  Serial.println("Testing MPU6050 connection...");
  if(mpu.testConnection() ==  false){
    Serial.println("MPU6050 connection failed");
    while(true);
  }
  else{
    Serial.println("MPU6050 connection successful");
  }
}


void ble_setup() {
  //BLE initialization, create a server and a service
  BLEDevice::init(name);
  BLEServer *pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());
  BLEService *pService = pServer->createService(SERVICE_UUID);

  //Set characteristics: read, write, and notify
  pGlobalCharacteristic = pService->createCharacteristic(
                             CHARACTERISTIC_UUID,
                             BLECharacteristic::PROPERTY_WRITE | 
                             BLECharacteristic::PROPERTY_WRITE_NR |
                             BLECharacteristic::PROPERTY_READ  |
                             BLECharacteristic::PROPERTY_NOTIFY // Add Notify for updates
                           );
  

  //Added Descriptors to fix error for Win 10/11
  pGlobalCharacteristic->addDescriptor(new BLE2902());


  //Start service and advertising
  pGlobalCharacteristic->setCallbacks(new MyCallbacks());
  pService->start();

  BLEAdvertising *pAdvertising = pServer->getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  
  pAdvertising->setScanResponse(false); 
  pAdvertising->setMinPreferred(0x00);  // Clear preferred settings
  pAdvertising->setMinPreferred(0x06);  // Then set them again
  
  pAdvertising->start();
  Serial.println("BLE initialized!");
}


