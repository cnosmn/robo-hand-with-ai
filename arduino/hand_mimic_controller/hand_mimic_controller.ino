
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

// Genel servo ayarları
#define SERVOMIN  150
#define SERVOMAX  600  

// Servo tanımlamaları
#define BAS_PARMAK_1 10
#define BAS_PARMAK_2 11
#define ISARET_PARMAK 12
#define ORTA_PARMAK 13
#define YUZUK_PARMAK 14
#define SERCE_PARMAK 15

// Her parmak için hareket limitleri
int servoMin[16] = {150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150};
int servoMax[16] = {600, 600, 600, 600, 600, 600, 600, 600, 600, 600, 600, 600, 600, 600, 600, 600}; 

// Her servo için mevcut pozisyon
int servoPos[16] = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}; // Açı olarak (0-180)

// Programın çalışma durumu
bool isRunning = true;

void setup() {
  Serial.begin(115200);


  pwm.begin();
  pwm.setPWMFreq(60);  // Analog servolar için ~60 Hz güncelleme hızı
  
  // Tüm servoları başlangıç pozisyonuna getir
  for (int i = 10; i <= 15; i++) {
    setServo(i, 0);
    delay(100);
  }
  
}

void loop() {
  if (Serial.available() > 0) {
    String komut = Serial.readStringUntil('\n');
    komut.trim();
    
    // Program kontrolü
    if (komut == "stop") {
      isRunning = false;
      return; // Loop'tan çıkarak diğer komutları işlemez
    }
    else if (komut == "start") {
      isRunning = true;
      return;
    }
    else if (komut == "status") {
      return;
    }
    
    // Eğer program durdurulmuşsa, diğer komutları işleme
    if (!isRunning) {
      return;
    }
    
    // Test komutları
    if (komut.startsWith("test")) {
      if (komut == "testall") {
        testAllServos();
      } else {
        int servoNum = komut.substring(4).toInt();
        testServo(servoNum);
      }
    }
    // Standart servo hareketi
    else if (komut.startsWith("servo:")) {
      int ilkIkiNokta = komut.indexOf(':');
      int ikinciIkiNokta = komut.indexOf(':', ilkIkiNokta + 1);
      
      if (ilkIkiNokta != -1 && ikinciIkiNokta != -1) {
        int servoNum = komut.substring(ilkIkiNokta + 1, ikinciIkiNokta).toInt();
        int aci = komut.substring(ikinciIkiNokta + 1).toInt();
        
        setServo(servoNum, aci);
      }
    }
    // Yavaş hareket - smoothmove:0:90:10 (servo:açı:hız)
    else if (komut.startsWith("smoothmove:")) {
      int ilkIkiNokta = komut.indexOf(':');
      int ikinciIkiNokta = komut.indexOf(':', ilkIkiNokta + 1);
      int ucuncuIkiNokta = komut.indexOf(':', ikinciIkiNokta + 1);
      
      if (ilkIkiNokta != -1 && ikinciIkiNokta != -1 && ucuncuIkiNokta != -1) {
        int servoNum = komut.substring(ilkIkiNokta + 1, ikinciIkiNokta).toInt();
        int aci = komut.substring(ikinciIkiNokta + 1, ucuncuIkiNokta).toInt();
        int hiz = komut.substring(ucuncuIkiNokta + 1).toInt();
        
        moveServoSmooth(servoNum, aci, hiz);
      }
    }
    // Kalibrasyon komutu - calibrate:0:150:600 (servo:min:max)
    else if (komut.startsWith("calibrate:")) {
      int ilkIkiNokta = komut.indexOf(':');
      int ikinciIkiNokta = komut.indexOf(':', ilkIkiNokta + 1);
      int ucuncuIkiNokta = komut.indexOf(':', ikinciIkiNokta + 1);
      
      if (ilkIkiNokta != -1 && ikinciIkiNokta != -1 && ucuncuIkiNokta != -1) {
        int servoNum = komut.substring(ilkIkiNokta + 1, ikinciIkiNokta).toInt();
        int minVal = komut.substring(ikinciIkiNokta + 1, ucuncuIkiNokta).toInt();
        int maxVal = komut.substring(ucuncuIkiNokta + 1).toInt();
        
        calibrateServo(servoNum, minVal, maxVal);
      }
    }
    // Tüm parmakları tek komutla hareket ettirme
    else if (komut.startsWith("movefingers:")) {
      // Format: movefingers:t1:t2:i:m:r:p
      // Örnek: movefingers:90:45:180:180:180:180
      
      int ilkIkiNokta = komut.indexOf(':');
      int ikinciIkiNokta = komut.indexOf(':', ilkIkiNokta + 1);
      int ucuncuIkiNokta = komut.indexOf(':', ikinciIkiNokta + 1);
      int dorduncuIkiNokta = komut.indexOf(':', ucuncuIkiNokta + 1);
      int besinciIkiNokta = komut.indexOf(':', dorduncuIkiNokta + 1);
      int altinciIkiNokta = komut.indexOf(':', besinciIkiNokta + 1);
      
      if (ilkIkiNokta != -1 && ikinciIkiNokta != -1 && ucuncuIkiNokta != -1 && 
          dorduncuIkiNokta != -1 && besinciIkiNokta != -1) {
        
        int thumb1 = komut.substring(ilkIkiNokta + 1, ikinciIkiNokta).toInt();
        int thumb2 = komut.substring(ikinciIkiNokta + 1, ucuncuIkiNokta).toInt();
        int index = komut.substring(ucuncuIkiNokta + 1, dorduncuIkiNokta).toInt();
        int middle = komut.substring(dorduncuIkiNokta + 1, besinciIkiNokta).toInt();
        int ring = komut.substring(besinciIkiNokta + 1, altinciIkiNokta).toInt();
        int pinky = komut.substring(altinciIkiNokta + 1).toInt();
        
        moveFingers(thumb1, thumb2, index, middle, ring, pinky);
      }
    }
    // Hazır hareketler
    else if (komut == "open") {
      openHand();
    }
    else if (komut == "close") {
      closeHand();
    }
    else if (komut == "thumbsup") {
      thumbsUp();
    }
    else if (komut == "point") {
      pointFinger();
    }
    else if (komut == "pinch") {
      pinchGesture();
    }
    else if (komut == "wave") {
      waveHand();
    }
    else if (komut == "init") {
      Serial.println("Sistem başlatıldı");
    }
    else if (komut == "help") {
      showHelp();
    }
    else {

    }
  }
}

// Arduino kodunuzdaki setServo fonksiyonunu değiştirin
void setServo(uint8_t servoNum, int angle) {
  if (servoNum < 10 || servoNum > 15) {
    return;
  }
  
  // Açı sınırlaması yap
  if (angle < 0) angle = 0;
  if (angle > 180) angle = 180;
  
  // Eğer mevcut açı ile yeni açı arasında büyük fark yoksa, hareketi atla
  // Bu servo motorların gereksiz titreşimini önler
  if (abs(servoPos[servoNum] - angle) < 3) {
    return;
  }
  
  uint16_t pulse = map(angle, 0, 180, servoMin[servoNum], servoMax[servoNum]);
  pwm.setPWM(servoNum, 0, pulse);
  
  // Mevcut pozisyonu güncelle
  servoPos[servoNum] = angle;
  
  // Yoğun seri port trafiğini önlemek için açı bilgisini sadece debug modu açıksa yazdır

}

void showHelp() {}


void testServo(int servoNum) {
  if (servoNum < 10 || servoNum > 15) {
    return;
  }
  
  Serial.println(servoNum);
  
  // Yavaşça 0 dereceye getir
  moveServoSmooth(servoNum, 0, 10);
  delay(1000);
  
  // Yavaşça 90 dereceye getir
  moveServoSmooth(servoNum, 90, 10);
  delay(1000);
  
  // Yavaşça 180 dereceye getir
  moveServoSmooth(servoNum, 180, 10);
  delay(1000);
  
  // Yavaşça sıfırla
  moveServoSmooth(servoNum, 0, 10);
  delay(1000);
  
}

void testAllServos() {
  
  for (int servo = 10; servo <= 15; servo++) {
    Serial.println(servo);
    
    // 90 dereceye getir
    moveServoSmooth(servo, 90, 10);
    delay(500);
    
    // Sıfırla
    moveServoSmooth(servo, 0, 10);
    delay(500);
  }
  
}

void moveServoSmooth(uint8_t servoNum, int targetAngle, int speedDelay) {
  if (servoNum < 10 || servoNum > 15) {
    return;
  }
  
  // Açı sınırlaması yap
  if (targetAngle < 0) targetAngle = 0;
  if (targetAngle > 180) targetAngle = 180;
  
  int currentAngle = servoPos[servoNum];
  
  Serial.print(servoNum);
  Serial.print(currentAngle);
  Serial.print(targetAngle);

  
  // Yumuşak geçiş için kademeli hareket
  if (currentAngle < targetAngle) {
    for (int pos = currentAngle; pos <= targetAngle; pos++) {
      setServo(servoNum, pos);
      delay(speedDelay);
    }
  } 
  else {
    for (int pos = currentAngle; pos >= targetAngle; pos--) {
      setServo(servoNum, pos);
      delay(speedDelay);
    }
  }
  
}

void calibrateServo(uint8_t servoNum, int minVal, int maxVal) {
  if (servoNum < 10 || servoNum > 15) {
    return;
  }
  
  servoMin[servoNum] = minVal;
  servoMax[servoNum] = maxVal;

}

void moveFingers(int thumb1, int thumb2, int index, int middle, int ring, int pinky) {
  setServo(BAS_PARMAK_1, thumb1);
  setServo(BAS_PARMAK_2, thumb2);
  setServo(ISARET_PARMAK, index);
  setServo(ORTA_PARMAK, middle);
  setServo(YUZUK_PARMAK, ring);
  setServo(SERCE_PARMAK, pinky);
  
}

// Hazır hareketler
void openHand() {
  
  for (int i = 10; i <= 15; i++) {
    moveServoSmooth(i, 0, 5);
    delay(100);
  }
  
}

void closeHand() {
  
  for (int i = 10; i <= 15; i++) {
    moveServoSmooth(i, 180, 5);
    delay(100);
  }
  
}

void thumbsUp() {
  
  // Önce eli kapat
  closeHand();
  delay(500);
  
  // Başparmak birinci eklemi yukarı kaldır
  moveServoSmooth(BAS_PARMAK_1, 0, 5);
  // Başparmak ikinci eklemi yukarı kaldır
  moveServoSmooth(BAS_PARMAK_2, 180, 5);
  
}

void pointFinger() {
  
  // Önce eli kapat
  closeHand();
  delay(500);
  
  // İşaret parmağını aç
  moveServoSmooth(ISARET_PARMAK, 0, 5);
  
}

void pinchGesture() {
  
  // Önce eli aç
  openHand();
  delay(500);
  
  // İşaret parmağı ve başparmağı birleştir
  moveServoSmooth(BAS_PARMAK_1, 90, 5);
  moveServoSmooth(BAS_PARMAK_2, 90, 5);
  moveServoSmooth(ISARET_PARMAK, 90, 5);
  
  // Diğer parmakları kapat
  moveServoSmooth(ORTA_PARMAK, 180, 5);
  moveServoSmooth(YUZUK_PARMAK, 180, 5);
  moveServoSmooth(SERCE_PARMAK, 180, 5);
  
}

void waveHand() {
  
  // Önce eli aç
  openHand();
  delay(500);
  
  // Parmakları ardışık hareket ettir
  for (int i = 0; i < 3; i++) {
    for (int servo = SERCE_PARMAK; servo >= ISARET_PARMAK; servo--) {
      moveServoSmooth(servo, 90, 5);
      delay(100);
    }
    
    for (int servo = SERCE_PARMAK; servo >= ISARET_PARMAK; servo--) {
      moveServoSmooth(servo, 0, 5);
      delay(100);
    }
  }
  
}