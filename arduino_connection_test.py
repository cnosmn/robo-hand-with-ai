import serial
import time

def check_arduino_connection(port, baudrate=115200):
    print(f"Arduino bağlantısı test ediliyor... Port: {port}, Baudrate: {baudrate}")
    
    try:
        # Arduino'ya bağlanmayı dene
        ser = serial.Serial(port, baudrate, timeout=2)
        print(f"Bağlantı başarılı! Port {port} açıldı.")
        
        # Arduino'nun sıfırlanması için bekle
        time.sleep(2)
        
        # Arduino'ya test komutu gönder
        test_command = "status\n"
        print(f"Test komutu gönderiliyor: {test_command.strip()}")
        ser.write(test_command.encode())
        
        # Yanıt bekleniyor
        time.sleep(1)
        
        # Yanıtı oku
        response = ""
        while ser.in_waiting:
            response += ser.readline().decode('utf-8').strip()
        
        if response:
            print(f"Arduino'dan yanıt alındı: {response}")
        else:
            print("Arduino'dan yanıt alınamadı, ancak bağlantı açık görünüyor.")
        
        # Bağlantıyı kapat
        ser.close()
        print("Bağlantı kapatıldı.")
        return True
        
    except serial.SerialException as e:
        print(f"Hata: {e}")
        print("Arduino bağlantısı kurulamadı.")
        return False
        
if __name__ == "__main__":
    import sys
    
    # Komut satırı argümanlarını işle
    if len(sys.argv) > 1:
        port = sys.argv[1]
    else:
        # Port listesini göster
        import glob
        ports = glob.glob('/dev/tty*')
        print("Mevcut portlar:")
        for i, p in enumerate(ports):
            print(f"{i}: {p}")
        
        # Kullanıcıdan port seçmesini iste
        port_index = input("Test etmek istediğiniz portun numarasını girin (0, 1, 2, ...): ")
        try:
            port = ports[int(port_index)]
        except (ValueError, IndexError):
            print("Geçersiz port seçimi.")
            print("Varsayılan port: /dev/ttyACM0 kullanılacak.")
            port = "/dev/ttyACM0"
    
    # Baudrate kontrolü
    if len(sys.argv) > 2:
        try:
            baudrate = int(sys.argv[2])
        except ValueError:
            print("Geçersiz baudrate. Varsayılan değer: 115200 kullanılacak.")
            baudrate = 115200
    else:
        baudrate = 115200
    
    # Bağlantıyı test et
    check_arduino_connection(port, baudrate)