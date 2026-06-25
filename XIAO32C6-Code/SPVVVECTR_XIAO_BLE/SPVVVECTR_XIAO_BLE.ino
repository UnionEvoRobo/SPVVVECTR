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
String name = "SPVVVECTR1";
#define SERVICE_UUID        "afcdeba4-f8a9-4ca1-baa5-021afe634998"
#define CHARACTERISTIC_UUID "83147421-2684-43ec-af39-58533d866c8e"

String name = "SPVVVECTR2";
#define SERVICE_UUID        "8aaba9c2-7f68-49d6-97cb-b9783ea29fd6"
#define CHARACTERISTIC_UUID "2a612f78-13b2-4b3a-bab8-50b00d2f003f"

String name = "SPVVVECTR3";
#define SERVICE_UUID        "e132a2ee-a68a-4b4b-98fa-29ef8bbc0be2"
#define CHARACTERISTIC_UUID "ccba8d13-8743-45f7-9fd9-69a20a9acddc"

String name = "test_board";
#define SERVICE_UUID        "900ec402-1a33-4c94-a3d7-076951f68065"
#define CHARACTERISTIC_UUID "cf9ecefe-a9f3-4087-af6a-cf7a6f917750"
*/


/*      BLE variables: Change name and UUID here      */
String name = "test_board";
#define SERVICE_UUID        "900ec402-1a33-4c94-a3d7-076951f68065"
#define CHARACTERISTIC_UUID "cf9ecefe-a9f3-4087-af6a-cf7a6f917750"

BLECharacteristic *pGlobalCharacteristic; 
bool sprint = true;


/*            Declare the GPIO pins here              */
const int EN_PIN    = 25;                  //Note: Old board uses 26
const int PH_PIN    = 26;                  //Note: Old board uses 25
const int SLEEP     = 27;                  //Note: Not on old board
const int A         = 33;
const int B         = 34; 
const int MPU_SDA   = 8;
const int MPU_SCL   = 9;
const int INT       = 9;


/*                Declare MPU6050 here                */
MPU6050 mpu;
#define OUTPUT_READABLE_ACCELGYRO
//#define OUTPUT_BINARY_ACCELGYRO
int16_t ax, ay, az; 
int16_t gx, gy, gz; 
int     calibrate_size = 200;
bool    blinkState;
volatile bool is_calibrating = false;

/*         Declare Encoder specifications here        */
const float reduction_ratio = 10.0;         //Since the motor is 1:10 reduction
const int   ppr_num = 7;                    //Inside encoder datasheet
const float hall_resolution = reduction_ratio * ppr_num; 

//Encoder Pulse timer variables
volatile unsigned long last_pulse_time = 0;
volatile long delta_micros = 0;
volatile int  direction = 1;                //1 is CCW

//Stall Detection variables
volatile unsigned long stall_timer = 0;
const unsigned long STALL_THRESHOLD_MS = 1000;  //time before killing power
const float MIN_SAFE_RPM = 20.0;                //minimum RPM to be considered "moving"
const int MAX_SPEED = 65535 * 20/100;           //pwm driver is 16-bit

// Average calculation variables
#define FILTER_SIZE 10
float rpm_buffer[FILTER_SIZE] = {0};
int filter_idx = 0;
float raw_rpm = 0;
float avg_rpm = 0;

// Misc
unsigned long prev_loop_time = 0;
unsigned long prev_noti_time = 0;
const float period_ms = 50; 
float target_rpm = 0.0;                         //Set initial RPM here
float speed = 0;                                //Set initial speed here
const int MAX_RPM = 1000;                       //Set Maximum RPM here

// PID  Controller Variables (Adjusted for 16-bit PWM)
const float kP = 3;
const float kD = 0.5;
float error = 0;
float last_error = 0;


/*========================================================*/
/*                          Function                      */
void IRAM_ATTR countPulse();
void pin_setup();
void mpu_setup();
void mpu_read();
void ble_setup();
void mpu_calibration();


/*========================================================*/
/*                       BLE CallBacks                    */
// Callback class to handle incoming BLE writes
class MyCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
      String value = pCharacteristic->getValue().c_str();
      value.trim();
      if (value.length() > 0) {
        if (value.equalsIgnoreCase("calibrate") && !is_calibrating) {
          //Run IMU Calibration task
          xTaskCreate(
            [](void* param) {
              mpu_calibration();
              vTaskDelete(NULL); // Self-terminate when finished
            },
            "mpu_cal_task", 4096, NULL, 1, NULL
          );
        }
        else {
          target_rpm = value.toFloat();
          //BLE Set Target Speed
          target_rpm = constrain(target_rpm, -1-MAX_RPM, 1+MAX_RPM);
          Serial.print("New Target RPM via BLE: ");
          Serial.println(target_rpm);
        }
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
/*                  Main setup function                   */
void setup() {

  Serial.begin (115200);
  //pin_setup();
  ble_setup();
  mpu_setup();
  mpu_read();
  mpu_calibration();
}


/*========================================================*/
/*                  Main loop function                   */
void loop() {
  
  //Update timer
  unsigned long current_time = millis();
  
  //MOTOR CONTROL LOGIC
  if (current_time - prev_loop_time >= period_ms) {
    prev_loop_time = current_time;

    // 1. Get Encoder data (pulse period)
    /*noInterrupts();
    long d_micros = delta_micros;
    int d_dir = direction;
    unsigned long last_p = last_pulse_time;
    interrupts();

    // 2. Calculate Raw RPM
    if (micros() - last_p > 250000) { // 0.25s timeout for stop
      raw_rpm = 0;
    } else if (d_micros > 0) {
      raw_rpm = (1000000.0 / d_micros / hall_resolution) * 60.0 * d_dir;
    }

    // 3. Averaging out (the RPM)
    rpm_buffer[filter_idx] = raw_rpm;
    filter_idx = (filter_idx + 1) % FILTER_SIZE;
    float sum = 0;
    for(int i=0; i<FILTER_SIZE; i++) {
      sum += rpm_buffer[i];
    }
    avg_rpm = sum / FILTER_SIZE;

    // 4. PID Speed calculation
    error = abs(target_rpm) - abs(avg_rpm);
    speed += kP * error + kD * (error - last_error) / (period_ms / 1000.0);
    speed = constrain(speed, 0, 65535*80/100); 
    last_error = error;

    //4.5 Stall Detection Logic
    if (abs(target_rpm) > 0 && speed > MAX_SPEED && abs(avg_rpm) < MIN_SAFE_RPM) {
      if (stall_timer == 0) {
        //Start stall timer
        stall_timer = current_time;
      } 
      else if (current_time - stall_timer > STALL_THRESHOLD_MS) {
        // STALL TRIGGERED
        target_rpm = 0; 
        speed = 0;
        stall_timer = 0; // Reset timer
        Serial.println(">>> Stall Detected! Turning off motor.");
      }
    } 
    else {
      stall_timer = 0; // Reset timer again if not stall
    }

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
    Serial.print(current_time);
    Serial.print(" ");
    Serial.println (avg_rpm);*/

    // 6. MPU-6050 data
    if (!is_calibrating) {
      mpu_read();
      Serial.print("a:\t");
      Serial.print(ax); Serial.print("\t");
      Serial.print(ay); Serial.print("\t");
      Serial.println(az);
      Serial.print("g:\t");
      Serial.print(gx); Serial.print("\t");
      Serial.print(gy); Serial.print("\t");
      Serial.println(gz);
    }
  }

  // 7. BLE message
  if (current_time - prev_noti_time >= 800) {
    prev_noti_time = current_time;
    // 6. Update BLE Notify and Serial
    String output = String(target_rpm) + "," + 
                    String(avg_rpm) + "," + 
                    String(ax) + "," + 
                    String(ay) + "," + 
                    String(az) + "," + 
                    String(gx) + "," + 
                    String(gy) + "," + 
                    String(gz);
    pGlobalCharacteristic->setValue(output.c_str());
    pGlobalCharacteristic->notify();
  }

  vTaskDelay(pdMS_TO_TICKS(1)); //Decoupling Time
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
  //BLE initialization, MTU packet size, create a server and a service
  BLEDevice::init(name);
  BLEDevice::setMTU(512);
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
  
  pAdvertising->setScanResponse(true); 
  pAdvertising->setMinPreferred(0x00);  // Clear preferred settings
  pAdvertising->setMinPreferred(0x06);  // Then set them again
  
  pAdvertising->start();
  Serial.println("BLE initialized!");
}


/*========================================================*/
/*                      IMU Code                          */
void mpu_read() {
  /* Read raw accel/gyro data from the module. Other methods commented*/
  mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
  //mpu.getAcceleration(&ax, &ay, &az);
  //mpu.getRotation(&gx, &gy, &gz);

  /*Print the obtained data on the defined format*/
  #ifdef OUTPUT_READABLE_ACCELGYRO
    /*Serial.print("g:\t");
    Serial.print(gx); Serial.print("\t");
    Serial.print(gy); Serial.print("\t");
    Serial.println(gz);*/
  #endif
}


void mpu_calibration() {
  is_calibrating = true;

  long ax_sum =0, ay_sum = 0, az_sum = 0;
  long gx_sum =0, gy_sum = 0, gz_sum = 0;
  const int samples = 500;
  const int usDelay = 3150;

  /*  Stop the motor briefly and calibrate the MPU6050*/
  //1. Stop the motor momentarily and reset the offset
  float backup_target = target_rpm;
  target_rpm = 0;
  digitalWrite(SLEEP, 0);
  mpu.setXAccelOffset(0); mpu.setYAccelOffset(0); mpu.setZAccelOffset(0);
  mpu.setXGyroOffset(0);  mpu.setYGyroOffset(0);  mpu.setZGyroOffset(0);
  vTaskDelay(pdMS_TO_TICKS(500));

  //2. Collect raw mpu data samples
  for (int i=0; i< samples; i++) {
    int16_t rax, ray, raz, rgx, rgy, rgz;
    mpu.getMotion6(&rax, &ray, &raz, &rgx, &rgy, &rgz);
    ax_sum += rax; ay_sum += ray; az_sum += raz;
    gx_sum += rgx; gy_sum += rgy; gz_sum += rgz;
    delayMicroseconds(usDelay);

    //Time-break for other BLE task
    if (i % 20 == 0) {
      vTaskDelay(pdMS_TO_TICKS(1));
    }
  }

  //3. Calculate Offset
  int ax_offset = -(ax_sum / samples) / 8;
  int ay_offset = -(ay_sum / samples) / 8;
  int az_offset = (16384 - (az_sum / samples)) / 8; 
  //Factoring gravity constant in az.
  int gx_offset = -(gx_sum / samples) / 4;
  int gy_offset = -(gy_sum / samples) / 4;
  int gz_offset = -(gz_sum / samples) / 4;

  //4. Apply calibrated offsets
  mpu.setXAccelOffset(ax_offset); mpu.setYAccelOffset(ay_offset); mpu.setZAccelOffset(az_offset);
  mpu.setXGyroOffset(gx_offset);  mpu.setYGyroOffset(gy_offset);  mpu.setZGyroOffset(gz_offset);

  //5. Return to original RPM
  target_rpm = backup_target;
  digitalWrite(SLEEP, 1);

  is_calibrating = false;
}