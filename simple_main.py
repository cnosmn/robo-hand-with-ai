#!/usr/bin/env python3
"""
Tek dosyada çalışan El Mimic Sistemi
"""
import cv2
import mediapipe as mp
import numpy as np
import serial
import time
import argparse

class SimpleHandMimicSystem:
    def __init__(self, port='/dev/ttyUSB0', baudrate=115200):
        # MediaPipe el tespit modülünü başlat
        print("MediaPipe Hands başlatılıyor...")
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Arduino bağlantısı
        self.ser = None
        try:
            print(f"Arduino'ya {port} portundan bağlanılıyor...")
            self.ser = serial.Serial(port, baudrate, timeout=1)
            print(f"Arduino'ya bağlandı")
            time.sleep(2)  # Arduino'nun resetlenmesini bekle
            self.ser.write(b"start\n")  # Programı başlat
            time.sleep(0.5)
            
            # Arduino'nun yanıtını oku
            response = ""
            while self.ser.in_waiting:
                response += self.ser.readline().decode('utf-8').strip()
            if response:
                print(f"Arduino yanıtı: {response}")
            else:
                print("Arduino'dan yanıt alınamadı")
        except Exception as e:
            print(f"Arduino bağlantı hatası: {e}")
            self.ser = None

        # Son gönderilen parmak açıları
        self.last_angles = {}
        self.update_interval = 2  # Her 2 framede bir güncelle
        self.frame_counter = 0
        self.smooth_factor = 0.7  # Açı yumuşatma faktörü
        self.prev_angles = None
    
    def calculate_finger_angles(self, landmarks):
        """Her parmak eklemi için açı hesaplar"""
        # Ham açıları hesapla
        raw_angles = {
            'thumb_mcp': self._calculate_angle(landmarks[1], landmarks[2], landmarks[3]),
            'thumb_ip': self._calculate_angle(landmarks[2], landmarks[3], landmarks[4]),
            'index': self._calculate_angle(landmarks[5], landmarks[6], landmarks[8]),
            'middle': self._calculate_angle(landmarks[9], landmarks[10], landmarks[12]),
            'ring': self._calculate_angle(landmarks[13], landmarks[14], landmarks[16]),
            'pinky': self._calculate_angle(landmarks[17], landmarks[18], landmarks[20])
        }
        
        # Açıları 0-180 derece aralığına dönüştür (servo motor için)
        servo_angles = {}
        for finger, angle in raw_angles.items():
            # Kalibrasyon değerleri - gerçek uygulamada ayarlayın
            min_angle, max_angle = 120, 170
            servo_angles[finger] = int(np.interp(angle, [min_angle, max_angle], [180, 0]))
            servo_angles[finger] = max(0, min(servo_angles[finger], 180))
        
        # Açıları yumuşat
        if self.prev_angles is not None:
            for key in servo_angles:
                servo_angles[key] = int(self.smooth_factor * self.prev_angles[key] + 
                                     (1 - self.smooth_factor) * servo_angles[key])
        
        self.prev_angles = servo_angles.copy()
        return servo_angles
    
    def _calculate_angle(self, a, b, c):
        """Üç nokta arasındaki açıyı hesaplar"""
        a = np.array([a.x, a.y])
        b = np.array([b.x, b.y])
        c = np.array([c.x, c.y])
        
        # Vektörleri hesapla
        ba = a - b
        bc = c - b
        
        # Açıyı hesapla (radyan)
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
        
        # Radyandan dereceye çevir
        return np.degrees(angle)
    
    def send_finger_angles(self, angles):
        """Parmak açılarını Arduino'ya gönderir"""
        if self.ser is None:
            print("Arduino bağlantısı yok!")
            return False

        # Her güncelleme aralığında veya açılar önemli ölçüde değiştiyse güncelle
        if not self.last_angles or self.frame_counter >= self.update_interval:
            update = True
        else:
            # Açıların önemli ölçüde değişip değişmediğini kontrol et
            threshold = 5
            update = any(abs(angles[k] - self.last_angles.get(k, 0)) > threshold 
                         for k in angles if k in self.last_angles)
        
        if update:
            try:
                # Komut oluştur
                cmd = f"movefingers:{angles['thumb_mcp']}:{angles['thumb_ip']}:" + \
                      f"{angles['index']}:{angles['middle']}:{angles['ring']}:{angles['pinky']}\n"
                
                print(f"Arduino'ya gönderilen: {cmd.strip()}")
                self.ser.write(cmd.encode())
                
                # Yanıt oku (opsiyonel)
                time.sleep(0.1)
                if self.ser.in_waiting:
                    response = self.ser.readline().decode('utf-8').strip()
                    print(f"Arduino yanıtı: {response}")
                
                # Son açıları güncelle
                self.last_angles = angles.copy()
                self.frame_counter = 0
                return True
            except Exception as e:
                print(f"Arduino'ya veri gönderirken hata: {e}")
                return False
        
        self.frame_counter += 1
        return False
    
    def run(self):
        """Kamera akışını başlatır ve işler"""
        print("\n=== GERÇEK ZAMANLI EL TAKİP SİSTEMİ ===")
        print("Çıkış için 'q' tuşuna basın")
        
        # Kamerayı başlat
        print("Kamera açılıyor...")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Kamera açılamadı!")
            return
        print("Kamera başarıyla açıldı")
            
        # Pencere oluştur
        cv2.namedWindow('El Takip Sistemi', cv2.WINDOW_NORMAL)
        
        # FPS hesaplama değişkenleri
        frame_count = 0
        fps_start_time = time.time()
        fps = 0
        
        try:
            while True:
                # Kare al
                ret, frame = cap.read()
                if not ret:
                    print("Kamera karesi okunamadı!")
                    break
                
                # BGR'den RGB'ye dönüştür
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # El tespiti yap
                results = self.hands.process(frame_rgb)
                
                # FPS hesapla
                frame_count += 1
                if (time.time() - fps_start_time) >= 1:
                    fps = frame_count / (time.time() - fps_start_time)
                    frame_count = 0
                    fps_start_time = time.time()
                
                # FPS'i ekranda göster
                cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Eğer el tespit edildiyse
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        # El işaretlerini çiz
                        self.mp_drawing.draw_landmarks(
                            frame, 
                            hand_landmarks, 
                            self.mp_hands.HAND_CONNECTIONS,
                            self.mp_drawing_styles.get_default_hand_landmarks_style(),
                            self.mp_drawing_styles.get_default_hand_connections_style())
                        
                        # Parmak açılarını hesapla
                        finger_angles = self.calculate_finger_angles(hand_landmarks.landmark)
                        
                        # Açıları Arduino'ya gönder
                        self.send_finger_angles(finger_angles)
                        
                        # Açıları ekranda göster
                        y_pos = 60
                        for finger, angle in finger_angles.items():
                            cv2.putText(frame, f"{finger}: {angle}", (10, y_pos), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
                            y_pos += 25
                        
                        # Sadece ilk eli işle
                        break
                else:
                    # El tespit edilemezse uyarı göster
                    cv2.putText(frame, "El tespit edilemedi", (10, 60), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                # Sonucu göster
                cv2.imshow('El Takip Sistemi', frame)
                
                # Çıkış için 'q' tuşuna basma kontrolü
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("Kullanıcı çıkış yaptı")
                    break
        
        except Exception as e:
            print(f"Hata oluştu: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Kaynakları serbest bırak
            cap.release()
            cv2.destroyAllWindows()
            self.close()
    
    def close(self):
        """Kaynakları temizle"""
        print("Sistem kapatılıyor...")
        self.hands.close()
        if self.ser is not None:
            try:
                self.ser.write(b"stop\n")
                time.sleep(0.5)
                self.ser.close()
                print("Arduino bağlantısı kapatıldı")
            except Exception as e:
                print(f"Arduino kapatılırken hata: {e}")

def main():
    # Parametreleri işle
    parser = argparse.ArgumentParser(description="Basit El Takip Sistemi")
    parser.add_argument('--port', type=str, default='/dev/ttyUSB0', help='Arduino seri port adresi')
    parser.add_argument('--baudrate', type=int, default=115200, help='Seri port baudrate (bit/s)')
    args = parser.parse_args()
    
    # Basit sistem nesnesi oluştur
    system = SimpleHandMimicSystem(port=args.port, baudrate=args.baudrate)
    
    try:
        # Sistemi çalıştır
        system.run()
    except KeyboardInterrupt:
        print("\nProgram kullanıcı tarafından durduruldu.")
    except Exception as e:
        print(f"\nHata oluştu: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Program sonlandırıldı.")

if __name__ == "__main__":
    main()