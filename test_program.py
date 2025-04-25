#!/usr/bin/env python3
"""
Test programı - Her bir bileşeni ayrı ayrı test eder
"""
import cv2
import time
import sys
import argparse

print("=== EL HAREKETİ TEMEL TEST PROGRAMI ===")

# Argümanları işle
parser = argparse.ArgumentParser(description="Test programı")
parser.add_argument('--test', type=str, choices=['kamera', 'arduino', 'tam'], 
                   default='tam', help='Çalıştırılacak test')
args = parser.parse_args()

print(f"Seçilen test: {args.test}")

def test_kamera():
    """Kamera test fonksiyonu"""
    print("\n=== KAMERA TESTİ ===")
    print("Kamera başlatılıyor...")
    
    # OpenCV videocapture nesnesini oluştur
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("HATA: Kamera açılamadı!")
        return False
    
    print("Kamera başarıyla açıldı")
    print("3 saniyelik görüntü testi yapılacak...")
    print("Görüntü penceresi açılacak (görmüyorsanız, minimuma indirilmiş olabilir).")
    
    # Bir pencere oluştur
    cv2.namedWindow('Kamera Testi', cv2.WINDOW_NORMAL)
    
    # Birkaç kare al
    frame_count = 0
    start_time = time.time()
    
    while (time.time() - start_time) < 3:  # 3 saniye çalıştır
        ret, frame = cap.read()
        if not ret:
            print("HATA: Kamera karesi okunamadı!")
            break
        
        # Kare sayısını göster
        frame_count += 1
        cv2.putText(frame, f"Kare: {frame_count}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Çıkış için tuş
        cv2.putText(frame, "Cikmak icin 'q' tusuna basin", (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Görüntüyü göster
        cv2.imshow('Kamera Testi', frame)
        
        # 1ms bekle ve tuşa basılıp basılmadığını kontrol et
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Kullanıcı çıkış yaptı")
            break
    
    # Kaynakları serbest bırak
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"Kamera testi tamamlandı. {frame_count} kare işlendi.")
    return True

def test_arduino():
    """Arduino test fonksiyonu"""
    print("\n=== ARDUINO TESTİ ===")
    
    try:
        import serial
        print("PySerial modülü başarıyla import edildi")
    except ImportError:
        print("HATA: PySerial modülü bulunamadı! pip install pyserial ile yükleyin.")
        return False
    
    port_path = input("Arduino port yolunu girin (örn. /dev/ttyUSB0): ")
    
    try:
        print(f"Arduino'ya {port_path} portundan bağlanılıyor...")
        ser = serial.Serial(port_path, 115200, timeout=1)
        print(f"Arduino'ya başarıyla bağlandı")
        
        # Test komutu gönder
        print("Test komutu gönderiliyor: 'start\\n'")
        ser.write(b"start\n")
        time.sleep(0.5)
        
        # Yanıtı oku
        response = ""
        while ser.in_waiting:
            response += ser.readline().decode('utf-8').strip()
        
        if response:
            print(f"Arduino yanıtı: {response}")
        else:
            print("Arduino'dan yanıt alınamadı")
        
        # Bağlantıyı kapat
        ser.close()
        print("Arduino bağlantısı kapatıldı")
        return True
    
    except Exception as e:
        print(f"HATA: Arduino bağlantısında sorun: {e}")
        return False

def test_tam():
    """Tam sistem testi"""
    print("\n=== TAM SİSTEM TESTİ ===")
    
    # Önce kamerayı test et
    kamera_ok = test_kamera()
    if not kamera_ok:
        print("Kamera testi başarısız, tam test durduruluyor.")
        return False
    
    # Ardından Arduino'yu test et
    arduino_ok = test_arduino()
    if not arduino_ok:
        print("Arduino testi başarısız, tam test durduruluyor.")
        return False
    
    print("\nTüm testler başarıyla tamamlandı!")
    return True

# Seçilen testi çalıştır
if args.test == 'kamera':
    test_kamera()
elif args.test == 'arduino':
    test_arduino()
else:
    test_tam()

print("\nTest programı tamamlandı.")