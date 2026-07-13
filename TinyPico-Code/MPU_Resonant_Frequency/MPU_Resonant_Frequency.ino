#include <I2Cdev.h>
#include <MPU6050.h>


/*                  Declare GPIO here                 */
const int MPU_SDA   = 21;
const int MPU_SCL   = 22;

/*                Declare MPU6050 here                */
MPU6050 mpu;
#define OUTPUT_READABLE_ACCELGYRO
//#define OUTPUT_BINARY_ACCELGYRO
int16_t ax, ay, az; 
int16_t gx, gy, gz; 
int     calibrate_size = 200;
bool    blinkState;
volatile bool is_calibrating = false;

/*                        Functions                    */
void mpu_setup();
void mpu_read();
void ble_setup();
void mpu_calibration();

void setup() {
  Serial.begin(115200);
  mpu_setup();
  vTaskDelay(pdMS_TO_TICKS(1000));

  Serial.println("MPU calibration. Press Enter to start.");
  while(Serial.available() == 0) {}
  mpu_calibration();
  Serial.println("MPU calibration completed.");

  while (Serial.available() > 0) {
    Serial.read(); 
    delay(2);
  }

  Serial.println("Resonant Frequency Test? Press Enter to start.");
  while(Serial.available() == 0) {}
  long long int start_time = millis();
  long long int current_time = start_time;
  int delta_time = 0;
  while (delta_time < 5000) {
    current_time = millis();
    delta_time = current_time - start_time;
    mpu_read();
    Serial.print (delta_time);
    Serial.print ("\t");
    Serial.println (az);
    vTaskDelay(pdMS_TO_TICKS(10));
  } 
  Serial.println ("Test completed!");
}

void loop() {
}

/*                      IMU Code                          */
void mpu_setup(){
  /*--Start I2C interface--*/
  #if I2CDEV_IMPLEMENTATION == I2CDEV_ARDUINO_WIRE
    Wire.begin(); 
  #elif I2CDEV_IMPLEMENTATION == I2CDEV_BUILTIN_FASTWIRE
    Fastwire::setup(400, true);
  #endif

  //while (!Serial) {}

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
  is_calibrating = false;
}
