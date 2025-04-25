import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import time
import random
import os

class MemoryGameWithCV:
    def __init__(self, root):
        self.root = root
        self.root.title("Hafıza Oyunu")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f0f0")
        
        # Oyun ayarları
        self.card_pairs = 8  # 8 çift = 16 kart
        self.card_positions = []  # Kartların koordinatları [x1, y1, x2, y2]
        self.detected_cards = []  # Tespit edilen açık kartlar
        self.matched_pairs = []  # Eşleşen çiftler
        self.card_labels = {}  # Kart etiketleri (çiftleri belirlemek için)
        
        # Oyuncu bilgileri
        self.current_player = "player"  # "player" veya "ai"
        self.player_score = 0
        self.ai_score = 0
        self.last_flipped_card = None
        self.ai_memory = {}  # Yapay zekanın hafızası {label: [positions]}
        
        # Kamera ayarları
        self.camera = None
        self.is_running = False
        self.frame = None
        
        # Kartların yerleşimi için grid oluşturma
        self.grid_rows = 4
        self.grid_cols = 4
        self.grid_cells = []  # [[x1,y1,x2,y2], ...] - Her hücre için koordinatlar
        
        # Arayüz oluşturma
        self.create_ui()
        
        # Kalibrasyon durumu
        self.is_calibrating = False
        self.calibration_points = []
    
    def create_ui(self):
        # Ana frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Sol panel - Kamera görüntüsü
        self.camera_frame = ttk.LabelFrame(main_frame, text="Kamera Görüntüsü")
        self.camera_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.camera_view = ttk.Label(self.camera_frame)
        self.camera_view.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Sağ panel - Kontroller ve skorlar
        control_frame = ttk.LabelFrame(main_frame, text="Kontroller", width=300)
        control_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5, expand=False)
        
        # Skorlar
        score_frame = ttk.Frame(control_frame)
        score_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(score_frame, text="Oyuncu:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.player_score_label = ttk.Label(score_frame, text="0")
        self.player_score_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(score_frame, text="Yapay Zeka:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.ai_score_label = ttk.Label(score_frame, text="0")
        self.ai_score_label.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Durum mesajı
        self.status_label = ttk.Label(control_frame, text="Oyuna başlamak için 'Başlat' butonuna tıklayın.")
        self.status_label.pack(fill=tk.X, padx=5, pady=10)
        
        # Butonlar
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.start_button = ttk.Button(btn_frame, text="Başlat", command=self.start_game)
        self.start_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.calibrate_button = ttk.Button(btn_frame, text="Kartları Kalibre Et", command=self.start_calibration)
        self.calibrate_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.new_game_button = ttk.Button(btn_frame, text="Yeni Oyun", command=self.reset_game, state=tk.DISABLED)
        self.new_game_button.grid(row=1, column=0, padx=5, pady=5, sticky="ew", columnspan=2)
        
        # Kart tipleri için referans görüntüler (sadece gösterim amaçlı)
        card_types_frame = ttk.LabelFrame(control_frame, text="Kart Tipleri")
        card_types_frame.pack(fill=tk.X, padx=5, pady=5, expand=False)
        
        self.card_types_view = ttk.Label(card_types_frame, text="Kartlar kalibrasyon sırasında etiketlenecek")
        self.card_types_view.pack(fill=tk.X, padx=5, pady=5)
    
    def start_game(self):
        """Oyunu ve kamerayı başlatır"""
        if self.is_running:
            return
        
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            messagebox.showerror("Hata", "Kamera açılamadı!")
            return
        
        self.is_running = True
        self.start_button.config(text="Durdur", command=self.stop_game)
        self.update_camera()
        
        self.status_label.config(text="Kartları masaya yerleştirin ve kalibrasyon yapın.")
    
    def stop_game(self):
        """Oyunu ve kamerayı durdurur"""
        self.is_running = False
        if self.camera:
            self.camera.release()
        self.start_button.config(text="Başlat", command=self.start_game)
        self.status_label.config(text="Oyun durduruldu.")
    
    def update_camera(self):
        """Kamera görüntüsünü günceller ve kart tespiti yapar"""
        if not self.is_running:
            return
        
        ret, frame = self.camera.read()
        if ret:
            self.frame = frame.copy()
            
            # Eğer kalibrasyon yapılıyorsa
            if self.is_calibrating:
                # Kalibrasyon noktalarını göster
                for i, point in enumerate(self.calibration_points):
                    cv2.circle(frame, (point[0], point[1]), 5, (0, 255, 0), -1)
                    cv2.putText(frame, str(i+1), (point[0] + 10, point[1]), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                # Eğer tüm ızgara noktaları kalibre edildiyse, ızgarayı çiz
                if len(self.calibration_points) == 4:
                    pts1 = np.float32(self.calibration_points)
                    width, height = 400, 400
                    pts2 = np.float32([[0, 0], [width, 0], [0, height], [width, height]])
                    matrix = cv2.getPerspectiveTransform(pts1, pts2)
                    warped = cv2.warpPerspective(frame, matrix, (width, height))
                    
                    # Izgara çizgileri
                    cell_height = height // self.grid_rows
                    cell_width = width // self.grid_cols
                    
                    for i in range(self.grid_rows + 1):
                        y = i * cell_height
                        cv2.line(warped, (0, y), (width, y), (0, 255, 0), 2)
                    
                    for i in range(self.grid_cols + 1):
                        x = i * cell_width
                        cv2.line(warped, (x, 0), (x, height), (0, 255, 0), 2)
                    
                    # Warped görüntüyü ana kare içine yerleştir
                    h, w = frame.shape[:2]
                    offset_x, offset_y = 50, 50
                    frame[offset_y:offset_y+height, offset_x:offset_x+width] = warped
            
            # Eğer oyun aktifse, kart tespiti yap
            elif self.grid_cells and self.current_player == "player":
                self.detect_cards(frame)
            
            # Görüntüyü dönüştür ve UI'a yerleştir
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            self.camera_view.imgtk = imgtk
            self.camera_view.configure(image=imgtk)
        
        self.root.after(30, self.update_camera)
    
    def start_calibration(self):
        """Kalibrasyon modunu başlatır"""
        if not self.is_running:
            messagebox.showinfo("Bilgi", "Önce kamerayı başlatın!")
            return
        
        self.is_calibrating = True
        self.calibration_points = []
        self.status_label.config(text="Kalibrasyon başlatıldı. Kart alanının 4 köşesini tıklatın (Sol üst, Sağ üst, Sol alt, Sağ alt)")
        self.camera_view.bind("<Button-1>", self.add_calibration_point)
    
    def add_calibration_point(self, event):
        """Kalibrasyon noktası ekler"""
        if len(self.calibration_points) < 4:
            # Tıklanan koordinatları al
            x, y = event.x, event.y
            
            # Frame boyutuna göre ölçekle
            frame_height, frame_width = self.frame.shape[:2]
            display_width = self.camera_view.winfo_width()
            display_height = self.camera_view.winfo_height()
            
            # Ölçekleme faktörleri
            scale_x = frame_width / display_width
            scale_y = frame_height / display_height
            
            # Gerçek koordinatları hesapla
            real_x = int(x * scale_x)
            real_y = int(y * scale_y)
            
            self.calibration_points.append([real_x, real_y])
            
            if len(self.calibration_points) == 4:
                self.finish_calibration()
    
    def finish_calibration(self):
        """Kalibrasyonu tamamlar ve kart ızgarasını oluşturur"""
        self.is_calibrating = False
        self.camera_view.unbind("<Button-1>")
        
        # Perspektif dönüşümü
        pts1 = np.float32(self.calibration_points)
        width, height = 400, 400
        pts2 = np.float32([[0, 0], [width, 0], [0, height], [width, height]])
        self.transform_matrix = cv2.getPerspectiveTransform(pts1, pts2)
        
        # Grid hücrelerini oluştur
        self.grid_cells = []
        cell_height = height // self.grid_rows
        cell_width = width // self.grid_cols
        
        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                x1 = col * cell_width
                y1 = row * cell_height
                x2 = x1 + cell_width
                y2 = y1 + cell_height
                self.grid_cells.append([x1, y1, x2, y2])
        
        # Kart etiketlerini oluştur (rastgele)
        labels = []
        for i in range(self.card_pairs):
            labels.extend([i, i])  # Her etiketin iki örneği
        random.shuffle(labels)
        
        # Etiketleri grid hücrelerine ata
        self.card_labels = {}
        for i, cell in enumerate(self.grid_cells):
            card_id = f"card_{i}"
            label = labels[i]
            self.card_labels[card_id] = label
        
        self.status_label.config(text="Kalibrasyon tamamlandı. Oyun başladı! Sıra: Oyuncu")
        self.new_game_button.config(state=tk.NORMAL)
        self.current_player = "player"
    
    def detect_cards(self, frame):
        """Açık kartları tespit eder"""
        if not self.grid_cells or not hasattr(self, 'transform_matrix'):
            return
        
        # Perspektif dönüşümü
        warped = cv2.warpPerspective(frame, self.transform_matrix, (400, 400))
        
        # Renk dönüşümleri ve eşik işlemleri
        gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 150, 255, cv2.THRESH_BINARY_INV)
        
        # Her hücreyi kontrol et
        for i, (x1, y1, x2, y2) in enumerate(self.grid_cells):
            cell_id = f"card_{i}"
            
            # Bu kart zaten eşleştirildi mi?
            if any(cell_id in pair for pair in self.matched_pairs):
                continue
            
            # Hücre bölgesini al
            cell_region = thresh[y1:y2, x1:x2]
            
            # Hücredeki beyaz piksel oranı
            white_ratio = np.sum(cell_region > 0) / cell_region.size
            
            # Eğer belirli bir eşik değerinden fazla beyaz piksel varsa, kart açık demektir
            # (Değerler gerçek ortama göre ayarlanmalıdır)
            if white_ratio > 0.1:  # Eşik değerini ayarlayın
                # Kart açık olarak işaretlendi
                if cell_id not in self.detected_cards:
                    self.handle_flipped_card(cell_id, i, frame)
                
                # Kart bölgesini çiz
                cv2.rectangle(warped, (x1, y1), (x2, y2), (0, 255, 0), 2)
                # Kart etiketini göster
                cv2.putText(warped, f"Card {i} (Type: {self.card_labels[cell_id]})", 
                            (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Dönüştürülmüş görüntüyü ana kare içine yerleştir
        h, w = frame.shape[:2]
        offset_x, offset_y = 50, 50
        frame[offset_y:offset_y+400, offset_x:offset_x+400] = warped
    
    def handle_flipped_card(self, card_id, cell_index, frame):
        """Açılan kartı işler"""
        if self.current_player != "player" or card_id in self.detected_cards:
            return
        
        # Kartı açık olarak işaretle
        self.detected_cards.append(card_id)
        
        # Yapay zeka hafızasına ekle
        card_label = self.card_labels[card_id]
        if card_label not in self.ai_memory:
            self.ai_memory[card_label] = []
        if card_id not in self.ai_memory[card_label]:
            self.ai_memory[card_label].append(card_id)
        
        # İlk kart mı kontrol et
        if not self.last_flipped_card:
            self.last_flipped_card = card_id
            self.status_label.config(text=f"Kart açıldı: {card_id}. İkinci kartı açın.")
        else:
            # İkinci kart açıldığında eşleşme kontrolü
            first_card_label = self.card_labels[self.last_flipped_card]
            second_card_label = self.card_labels[card_id]
            
            if first_card_label == second_card_label:
                # Eşleşme bulundu
                self.matched_pairs.append((self.last_flipped_card, card_id))
                self.player_score += 1
                self.player_score_label.config(text=str(self.player_score))
                self.status_label.config(text="Eşleşme buldunuz! Tekrar sıra sizde.")
                
                # Eşleşen kartları tespit listesinden çıkar
                self.detected_cards.remove(self.last_flipped_card)
                self.detected_cards.remove(card_id)
                self.last_flipped_card = None
                
                # Oyun bitti mi kontrol et
                if len(self.matched_pairs) == self.card_pairs:
                    self.end_game()
            else:
                # Eşleşme yok, sıra yapay zekaya geçiyor
                self.status_label.config(text="Eşleşme bulunamadı. Sıra yapay zekada.")
                self.current_player = "ai"
                
                # Kartları 2 saniye sonra kapatılmış olarak işaretle
                self.root.after(2000, lambda: self.reset_flipped_cards())
                
                # Yapay zekanın hamlesi için 3 saniye bekle
                self.root.after(3000, self.ai_move)
    
    def reset_flipped_cards(self):
        """Eşleşmeyen kartları kapatır"""
        if self.last_flipped_card and self.last_flipped_card in self.detected_cards:
            self.detected_cards.remove(self.last_flipped_card)
        
        # Eşleşen kartlar dışındakileri temizle
        matched_card_ids = [card for pair in self.matched_pairs for card in pair]
        self.detected_cards = [card for card in self.detected_cards if card in matched_card_ids]
        
        self.last_flipped_card = None
    
    def ai_move(self):
        """Yapay zekanın hamlesini gerçekleştirir"""
        if self.current_player != "ai" or len(self.matched_pairs) == self.card_pairs:
            return
        
        self.status_label.config(text="Yapay zeka hamle yapıyor...")
        
        # Bilinen eşleşmeler var mı kontrol et
        known_pairs = []
        for label, cards in self.ai_memory.items():
            unique_cards = [card for card in cards if not any(card in pair for pair in self.matched_pairs)]
            if len(unique_cards) >= 2:
                known_pairs.append(unique_cards[:2])
        
        if known_pairs:
            # Bilinen bir çift seç
            selected_pair = random.choice(known_pairs)
            first_card, second_card = selected_pair
        else:
            # Rastgele iki kart seç
            available_cards = [f"card_{i}" for i in range(len(self.grid_cells)) 
                              if f"card_{i}" not in [card for pair in self.matched_pairs for card in pair]]
            
            if len(available_cards) < 2:
                self.end_game()
                return
            
            first_card, second_card = random.sample(available_cards, 2)
        
        # İlk kartı aç
        first_card_label = self.card_labels[first_card]
        self.status_label.config(text=f"Yapay zeka ilk kartı açtı: {first_card}")
        
        # İkinci kartı 1 saniye sonra aç
        self.root.after(1000, lambda: self.complete_ai_move(first_card, second_card))
    
    def complete_ai_move(self, first_card, second_card):
        """Yapay zekanın hamlesini tamamlar"""
        # İkinci kartı aç
        second_card_label = self.card_labels[second_card]
        
        # Kartlar eşleşiyor mu kontrol et
        if self.card_labels[first_card] == self.card_labels[second_card]:
            # Eşleşme bulundu
            self.matched_pairs.append((first_card, second_card))
            self.ai_score += 1
            self.ai_score_label.config(text=str(self.ai_score))
            self.status_label.config(text="Yapay zeka eşleşme buldu! Tekrar sıra onda.")
            
            # Oyun bitti mi kontrol et
            if len(self.matched_pairs) == self.card_pairs:
                self.end_game()
            else:
                # Sıra hala yapay zekada
                self.root.after(2000, self.ai_move)
        else:
            # Eşleşme yok, sıra oyuncuya geçiyor
            self.status_label.config(text="Yapay zeka eşleşme bulamadı. Sıra sizde.")
            self.current_player = "player"
    
    def end_game(self):
        """Oyunu bitirir ve sonucu gösterir"""
        if self.player_score > self.ai_score:
            result = f"Tebrikler! Kazandınız! Skor: {self.player_score}-{self.ai_score}"
        elif self.ai_score > self.player_score:
            result = f"Yapay zeka kazandı. Skor: {self.player_score}-{self.ai_score}"
        else:
            result = f"Berabere bitti! Skor: {self.player_score}-{self.ai_score}"
        
        self.status_label.config(text=f"Oyun bitti. {result}")
        messagebox.showinfo("Oyun Bitti", result)
    
    def reset_game(self):
        """Oyunu sıfırlar"""
        # Oyun değişkenlerini sıfırla
        self.detected_cards = []
        self.matched_pairs = []
        self.last_flipped_card = None
        self.player_score = 0
        self.ai_score = 0
        self.ai_memory = {}
        self.current_player = "player"
        
        # Skorları güncelle
        self.player_score_label.config(text="0")
        self.ai_score_label.config(text="0")
        
        # Yeni kart etiketleri oluştur
        if self.grid_cells:
            labels = []
            for i in range(self.card_pairs):
                labels.extend([i, i])
            random.shuffle(labels)
            
            self.card_labels = {}
            for i in range(len(self.grid_cells)):
                self.card_labels[f"card_{i}"] = labels[i]
        
        self.status_label.config(text="Yeni oyun başladı! Sıra: Oyuncu")

# Programı başlat
if __name__ == "__main__":
    root = tk.Tk()
    app = MemoryGameWithCV(root)
    root.mainloop()