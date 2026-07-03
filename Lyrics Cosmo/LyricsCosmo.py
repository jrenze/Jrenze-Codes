import sys
import time
import os
import random
import math
import tkinter as tk
import tkinter.filedialog as fd
import webbrowser
import base64

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame

try:
    import ctypes
    IS_WINDOWS = (os.name == 'nt')
except ImportError:
    IS_WINDOWS = False

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SONG_FILE = os.path.join(BASE_DIR, "song.mp3")
SYNCED_LYRICS_TXT = os.path.join(BASE_DIR, "synced_lyrics.txt")

TRANSPARENT_KEY = (255, 0, 128)
BOX_COLOR = (0, 0, 0)
BORDER_COLOR = (50, 50, 60)
BOX_SIZE = 300

SETTINGS = {
    'float_duration': 17.0,
    'theme': 'Galaxy'
}

THEMES = {
    'Galaxy': [(255, 255, 255), (200, 220, 255), (255, 220, 200), (180, 255, 255)],
    'Vaporwave': [(255, 100, 200), (200, 50, 255), (100, 255, 255), (255, 0, 150)],
    'Aurora': [(50, 255, 100), (0, 255, 200), (100, 255, 150), (200, 255, 255)],
    'Supernova': [(255, 50, 50), (255, 150, 0), (255, 200, 100), (255, 255, 50)],
    'Cyberpunk': [(255, 255, 0), (0, 255, 255), (255, 0, 255), (255, 255, 255)],
    'Matrix': [(0, 255, 0), (50, 200, 50), (0, 150, 0), (100, 255, 100)],
    'Blood Moon': [(255, 0, 0), (200, 0, 0), (150, 0, 0), (255, 100, 0)],
    'Ocean': [(0, 0, 255), (0, 150, 255), (0, 255, 255), (0, 100, 255)],
    'Sunset': [(255, 100, 0), (255, 50, 150), (200, 0, 200), (255, 150, 0)]
}

def _d(s):
    return base64.b64decode(s).decode('utf-8')

def ask_for_audio_file():
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    filepath = fd.askopenfilename(
        title="Select Audio File",
        filetypes=[("Audio Files", "*.mp3 *.wav *.ogg"), ("All Files", "*.*")]
    )
    root.destroy()
    return filepath

def make_window_transparent_overlay():
    if not IS_WINDOWS:
        return
    hwnd = pygame.display.get_wm_info()["window"]
    user32 = ctypes.windll.user32
    exstyle = user32.GetWindowLongW(hwnd, -20)
    user32.SetWindowLongW(hwnd, -20, exstyle | 0x00080000)
    r, g, b = TRANSPARENT_KEY
    user32.SetLayeredWindowAttributes(hwnd, (b << 16) | (g << 8) | r, 255, 0x00000001 | 0x00000002)
    user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 1 | 2)

def set_window_opacity(opacity):
    if not IS_WINDOWS:
        return
    hwnd = pygame.display.get_wm_info()["window"]
    user32 = ctypes.windll.user32
    r, g, b = TRANSPARENT_KEY
    user32.SetLayeredWindowAttributes(hwnd, (b << 16) | (g << 8) | r, opacity, 0x00000001 | 0x00000002)

def ask_for_lyrics_gui():
    root = tk.Tk()
    root.title("Paste Your Lyrics")
    root.geometry("500x600")
    root.attributes('-topmost', True)
    root.configure(bg='#121212')
    
    label = tk.Label(root, text="Paste your lyrics below (one line per lyric):", font=("Segoe UI", 12), bg='#121212', fg='white')
    label.pack(pady=10)
    
    text_area = tk.Text(root, wrap=tk.WORD, font=("Segoe UI", 11), bg='#1e1e1e', fg='white', insertbackground='white', relief=tk.FLAT)
    text_area.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
    
    result_lyrics = []
    
    def on_save():
        content = text_area.get("1.0", tk.END)
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        result_lyrics.extend(lines)
        root.destroy()
        
    btn = tk.Button(root, text="Start Syncing!", command=on_save, bg="#008CBA", fg="white", font=("Segoe UI", 12, "bold"), relief=tk.FLAT)
    btn.pack(pady=15)
    
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.deiconify()
    root.lift()
    root.focus_force()
    root.mainloop()
    return result_lyrics

class MCIAudioPlayer:
    def __init__(self, filepath):
        self.filepath = os.path.abspath(filepath)
        self.using_mci = False
        if IS_WINDOWS:
            open_command = f'open "{self.filepath}" type mpegvideo alias song'
            res = ctypes.windll.winmm.mciSendStringW(open_command, None, 0, 0)
            if res == 0:
                self.using_mci = True
        if not self.using_mci:
            pygame.mixer.init()
            pygame.mixer.music.load(self.filepath)

    def play(self):
        if self.using_mci:
            ctypes.windll.winmm.mciSendStringW('play song', None, 0, 0)
        else:
            pygame.mixer.music.play()

    def get_pos(self):
        if self.using_mci:
            buf = ctypes.create_unicode_buffer(128)
            ctypes.windll.winmm.mciSendStringW('status song position', buf, 128, 0)
            try:
                return int(buf.value.strip()) / 1000.0
            except ValueError:
                return 0.0
        else:
            return pygame.mixer.music.get_pos() / 1000.0

    def get_length(self):
        if self.using_mci:
            buf = ctypes.create_unicode_buffer(128)
            ctypes.windll.winmm.mciSendStringW('status song length', buf, 128, 0)
            try:
                return int(buf.value.strip()) / 1000.0
            except ValueError:
                return 0.0
        else:
            return 0.0

    def is_busy(self):
        if self.using_mci:
            buf = ctypes.create_unicode_buffer(128)
            ctypes.windll.winmm.mciSendStringW('status song mode', buf, 128, 0)
            return buf.value.strip().lower() == 'playing'
        else:
            return pygame.mixer.music.get_busy()

    def close(self):
        if self.using_mci:
            ctypes.windll.winmm.mciSendStringW('close song', None, 0, 0)
        else:
            if pygame.mixer.get_init():
                pygame.mixer.quit()

def lerp(a, b, t):
    return a + (b - a) * min(max(t, 0.0), 1.0)

def blend_color(c1, c2, ratio):
    r = int(c1[0] + (c2[0] - c1[0]) * ratio)
    g = int(c1[1] + (c2[1] - c1[1]) * ratio)
    b = int(c1[2] + (c2[2] - c1[2]) * ratio)
    return (r, g, b)

def get_fade_in_color(age, max_fade_duration, bg_color):
    if age < 0:
        return None
    if max_fade_duration <= 0.0:
        max_fade_duration = 0.1
    progress = min(age / max_fade_duration, 1.0)
    r = int(lerp(bg_color[0], 255, progress))
    g = int(lerp(bg_color[1], 255, progress))
    b = int(lerp(bg_color[2], 255, progress))
    return (r, g, b)

def generate_galaxy_stars(num_stars=40, width=BOX_SIZE, height=BOX_SIZE):
    stars = []
    palette = THEMES[SETTINGS['theme']]
    for _ in range(num_stars):
        stars.append({
            'x': random.randint(5, width - 5),
            'y': random.randint(5, height - 5),
            'size': random.randint(1, 3),
            'speed': random.uniform(1.0, 4.0),
            'offset': random.uniform(0, 10.0),
            'color': random.choice(palette)
        })
    return stars

def draw_stars(surface, stars, current_time):
    for star in stars:
        pulse = math.sin(current_time * star['speed'] + star['offset'])
        normalized_pulse = (pulse + 1.0) / 2.0 
        star_r = int(star['color'][0] * normalized_pulse)
        star_g = int(star['color'][1] * normalized_pulse)
        star_b = int(star['color'][2] * normalized_pulse)
        pygame.draw.circle(surface, (star_r, star_g, star_b), (int(star['x']), int(star['y'])), star['size'])

def draw_neon_text(surface, text, font, color, x, y):
    glow_color = (max(0, int(color[0]*0.4)), max(0, int(color[1]*0.4)), max(0, int(color[2]*0.4)))
    offsets = [(-2,0), (2,0), (0,-2), (0,2), (-1,-1), (1,1), (-1,1), (1,-1)]
    for dx, dy in offsets:
        glow_surf = font.render(text, True, glow_color)
        surface.blit(glow_surf, (x + dx, y + dy))
    main_surf = font.render(text, True, color)
    surface.blit(main_surf, (x, y))

def load_synced_lyrics():
    if not os.path.exists(SYNCED_LYRICS_TXT):
        return None, None
    synced = []
    song_path = None
    with open(SYNCED_LYRICS_TXT, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('[SONG_PATH]'):
                song_path = line.replace('[SONG_PATH]', '', 1)
                continue
            word_entries = line.split('|')
            line_data = []
            for entry in word_entries:
                parts = entry.split(',', 2)
                if len(parts) == 3:
                    try:
                        line_data.append((float(parts[0]), float(parts[1]), parts[2]))
                    except ValueError:
                        continue
            if line_data:
                synced.append(line_data)
    return song_path, (synced if synced else None)

def wrap_line_data(line_data, font, max_width):
    lines = []
    current_line = []
    current_w = 0
    space_w = font.size(" ")[0]
    for data in line_data:
        word_w = font.size(data[2])[0]
        if current_line and current_w + space_w + word_w > max_width:
            lines.append(current_line)
            current_line = [data]
            current_w = word_w
        else:
            current_line.append(data)
            if current_w > 0: current_w += space_w
            current_w += word_w
    if current_line:
        lines.append(current_line)
    return lines

def get_spawn_x(active_boxes, screen_w, box_size, current_time):
    for _ in range(50):
        test_x = random.randint(20, screen_w - box_size - 20)
        overlap = False
        for box in active_boxes:
            if current_time - box['spawn_time'] < (SETTINGS['float_duration'] * 0.3):
                if abs(box['x'] - test_x) < box_size + 20:
                    overlap = True
                    break
        if not overlap:
            return test_x
    return random.randint(20, screen_w - box_size - 20)

def draw_centered_ui_block(screen, w, h, stars, current_time):
    sw, sh = screen.get_size()
    rect = pygame.Rect((sw - w) // 2, (sh - h) // 2, w, h)
    pygame.draw.rect(screen, BOX_COLOR, rect, border_radius=0)
    
    star_surf = pygame.Surface((w, h))
    star_surf.fill(BOX_COLOR)
    draw_stars(star_surf, stars, current_time)
    screen.blit(star_surf, (rect.x, rect.y))
    
    pygame.draw.rect(screen, BORDER_COLOR, rect, width=2, border_radius=0)
    return rect

def draw_button(screen, font, text, cx, cy, mouse_pos):
    surf = font.render(text, True, (255, 255, 255))
    rect = pygame.Rect(0, 0, 300, 45)
    rect.center = (cx, cy)
    
    is_hover = rect.collidepoint(mouse_pos)
    bg_color = (30, 30, 40) if is_hover else (15, 15, 20)
    
    pygame.draw.rect(screen, bg_color, rect, border_radius=5)
    pygame.draw.rect(screen, (70, 70, 80), rect, width=1, border_radius=5)
    screen.blit(surf, (rect.x + (rect.width - surf.get_width()) // 2, rect.y + (rect.height - surf.get_height()) // 2))
    
    return rect, is_hover

def run_countdown(screen, font):
    for i in range(3, 0, -1):
        screen.fill(TRANSPARENT_KEY)
        sw, sh = screen.get_size()
        text_surf = font.render(str(i), True, (255, 255, 255))
        screen.blit(text_surf, (sw - text_surf.get_width() - 40, sh - text_surf.get_height() - 40))
        pygame.display.flip()
        
        start_ticks = pygame.time.get_ticks()
        while pygame.time.get_ticks() - start_ticks < 1000:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return False
            pygame.time.Clock().tick(60)
    return True

def run_sync_mode(screen, font, stars):
    audio_file = ask_for_audio_file()
    if not audio_file:
        return
        
    plain_lyrics = ask_for_lyrics_gui()
    if not plain_lyrics:
        return
        
    font_small = pygame.font.SysFont("segoeui", 24)
    if not run_countdown(screen, font_small):
        return
        
    words_list = [line.split() for line in plain_lyrics]
    player = MCIAudioPlayer(audio_file)
    player.play()
    
    synced_lines = []
    current_line_syncs = []
    current_line_idx = 0
    current_word_idx = 0
    running = True
    clock = pygame.time.Clock()
    last_tap_time = 0.0
    
    while running and player.is_busy():
        current_time = player.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    if current_line_idx < len(words_list) and (current_time - last_tap_time > 0.1):
                        word = words_list[current_line_idx][current_word_idx]
                        current_line_syncs.append((current_time, 0.0, word))
                        current_word_idx += 1
                        if current_word_idx >= len(words_list[current_line_idx]):
                            synced_lines.append(current_line_syncs)
                            current_line_syncs = []
                            current_line_idx += 1
                            current_word_idx = 0
                        last_tap_time = current_time
                        
        screen.fill(TRANSPARENT_KEY)
        rect = draw_centered_ui_block(screen, 1200, 250, stars, current_time)
        
        title_surf = font.render("TAP [SPACE] WHEN YOU HEAR EACH WORD START", True, (255, 255, 255))
        screen.blit(title_surf, (rect.x + (rect.width - title_surf.get_width()) // 2, rect.y + 20))
        
        if current_line_idx < len(words_list):
            line_words = words_list[current_line_idx]
            total_width = sum(font.size(w + " ")[0] for w in line_words)
            start_x = rect.x + (rect.width - total_width) // 2
            current_x = start_x
            y = rect.y + 100
            
            for i, word in enumerate(line_words):
                if i < current_word_idx:
                    color = (255, 255, 255)
                    screen.blit(font.render(word + " ", True, color), (current_x, y))
                elif i == current_word_idx:
                    color = (0, 255, 255)
                    draw_neon_text(screen, word + " ", font, color, current_x, y)
                else:
                    color = (150, 150, 150)
                    screen.blit(font.render(word + " ", True, color), (current_x, y))
                
                current_x += font.size(word + " ")[0]
            
            if current_line_idx + 1 < len(words_list):
                next_text = " ".join(words_list[current_line_idx + 1])
                next_surf = font.render(f'Next: "{next_text}"', True, (200, 200, 200))
                screen.blit(next_surf, (rect.x + (rect.width - next_surf.get_width()) // 2, rect.y + 180))
        else:
            done_surf = font.render("ALL WORDS SYNCED! Waiting for song to end (or press ESC)...", True, (0, 255, 0))
            screen.blit(done_surf, (rect.x + (rect.width - done_surf.get_width()) // 2, rect.y + 100))
            
        wm_surf = font_small.render(_d('QHJpbi5yZW56ZQ=='), True, (255, 255, 255))
        sw, sh = screen.get_size()
        screen.blit(wm_surf, (sw - wm_surf.get_width() - 40, sh - wm_surf.get_height() - 40))
            
        pygame.display.flip()
        clock.tick(60)
        
    player.close()
    
    if current_line_syncs:
        synced_lines.append(current_line_syncs)
    
    if synced_lines:
        flat_taps = [tap for line in synced_lines for tap in line]
        total_len = player.get_length()
        if total_len <= 0.0 and flat_taps:
            total_len = flat_taps[-1][0] + 5.0
            
        for i in range(len(flat_taps)):
            start_time, _, word = flat_taps[i]
            if i < len(flat_taps) - 1:
                dur = flat_taps[i+1][0] - start_time
            else:
                dur = total_len - start_time
                if dur <= 0: dur = 4.0
            flat_taps[i] = (start_time, max(0.1, dur), word)
            
        synced_data = []
        flat_idx = 0
        for line in synced_lines:
            line_str_parts = []
            for _ in line:
                start, dur, word = flat_taps[flat_idx]
                line_str_parts.append(f"{start:.3f},{dur:.3f},{word}")
                flat_idx += 1
            synced_data.append("|".join(line_str_parts))
            
        try:
            with open(SYNCED_LYRICS_TXT, 'w', encoding='utf-8') as f:
                f.write(f"[SONG_PATH]{os.path.abspath(audio_file)}\n")
                f.write("\n".join(synced_data))
        except Exception as e:
            pass
            
    pygame.event.clear()

def run_play_mode(screen, font, menu_stars):
    song_path, synced_lines = load_synced_lyrics()
    
    if not synced_lines or not song_path or not os.path.exists(song_path):
        screen.fill(TRANSPARENT_KEY)
        rect = draw_centered_ui_block(screen, 800, 250, menu_stars, pygame.time.get_ticks() / 1000.0)
        
        err_surf1 = font.render("You don't have any lyrics saved", True, (255, 100, 100))
        err_surf2 = font.render("Please click '1. Sync Lyrics' to sync a song first.", True, (255, 255, 255))
        err_surf3 = font.render("Press any key to return to menu.", True, (255, 255, 255))
        
        screen.blit(err_surf1, (rect.x + (rect.width - err_surf1.get_width()) // 2, rect.y + 40))
        screen.blit(err_surf2, (rect.x + (rect.width - err_surf2.get_width()) // 2, rect.y + 110))
        screen.blit(err_surf3, (rect.x + (rect.width - err_surf3.get_width()) // 2, rect.y + 170))
        pygame.display.flip()
        
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type in (pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    waiting = False
        return
        
    font_small = pygame.font.SysFont("segoeui", 24)
    if not run_countdown(screen, font_small):
        return

    spawn_times = []
    for i in range(len(synced_lines)):
        if i == 0:
            first_word_time = synced_lines[0][0][0]
            ideal = first_word_time - (SETTINGS['float_duration'] * 0.5)
            spawn_times.append(min(0.0, ideal))
        else:
            spawn_times.append(synced_lines[i-1][-1][0])

    player = MCIAudioPlayer(song_path)
    player.play()
    
    current_line_idx = 0
    clock = pygame.time.Clock()
    running = True
    screen_w, screen_h = screen.get_size()
    space_w = font.size(" ")[0]
    active_boxes = []
    trail_particles = []
    wrapped_lines = [wrap_line_data(line, font, BOX_SIZE - 40) for line in synced_lines]
    
    song_len = player.get_length()
    set_window_opacity(255)
    
    song_ended_time = None
    current_time = 0.0
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    
        if player.is_busy():
            current_time = player.get_pos()
        else:
            if song_ended_time is None:
                song_ended_time = time.time()
            elif time.time() - song_ended_time >= 5.0:
                break
                
        screen.fill(TRANSPARENT_KEY)
        
        is_phase1 = False
        is_phase2 = False
        phase1_ratio = 0.0
        phase2_ratio = 0.0
        
        time_left = song_len - current_time
        if 3.0 < time_left <= 6.0:
            is_phase1 = True
            phase1_ratio = (6.0 - time_left) / 3.0
        elif 0.0 < time_left <= 3.0:
            is_phase2 = True
            phase2_ratio = (3.0 - time_left) / 3.0
        elif time_left <= 0.0:
            is_phase2 = True
            phase2_ratio = 1.0
            
        if is_phase2:
            opacity = int((max(0.0, time_left) / 3.0) * 255)
            set_window_opacity(max(0, min(255, opacity)))
            
        if current_line_idx < len(synced_lines):
            if current_time >= spawn_times[current_line_idx]:
                active_boxes.append({
                    'spawn_time': current_time,
                    'x': get_spawn_x(active_boxes, screen_w, BOX_SIZE, current_time),
                    'wrapped': wrapped_lines[current_line_idx],
                    'stars': generate_galaxy_stars(),
                    'shooting_stars': []
                })
                current_line_idx += 1
                
        for p in trail_particles[:]:
            p['y'] += p['vy']
            p['life'] -= 0.01
            if p['life'] <= 0:
                trail_particles.remove(p)
            else:
                c_p = p['color']
                if is_phase1 or is_phase2:
                    c_p = blend_color(c_p, (255, 255, 255), phase1_ratio if is_phase1 else 1.0)
                
                draw_size = int(p['size'] * p['life'])
                if draw_size > 0:
                    pygame.draw.circle(screen, c_p, (int(p['x']), int(p['y'])), draw_size)
                
        for box in list(active_boxes):
            progress = (current_time - box['spawn_time']) / SETTINGS['float_duration']
            if progress > 1.0:
                active_boxes.remove(box)
                continue
                
            y = screen_h - (progress * (screen_h + BOX_SIZE))
            x = box['x']
            
            if random.random() < 0.15:
                p_col = random.choice(box['stars'])['color'] if box['stars'] else (255, 255, 255)
                trail_particles.append({
                    'x': x + random.randint(0, BOX_SIZE),
                    'y': y + BOX_SIZE,
                    'life': 1.0,
                    'vy': random.uniform(0.5, 2.5),
                    'size': random.uniform(1.5, 4.0),
                    'color': p_col
                })
                
            if random.random() < 0.005:
                box['shooting_stars'].append({
                    'x': random.randint(0, BOX_SIZE),
                    'y': 0,
                    'len': random.randint(20, 60),
                    'vx': random.uniform(3.0, 6.0) * random.choice([1, -1]),
                    'vy': random.uniform(4.0, 8.0)
                })
            
            curr_border = BORDER_COLOR
            if is_phase1:
                curr_border = blend_color(BORDER_COLOR, (255, 255, 255), phase1_ratio)
            elif is_phase2:
                curr_border = (255, 255, 255)
            
            box_rect = pygame.Rect(x, y, BOX_SIZE, BOX_SIZE)
            pygame.draw.rect(screen, BOX_COLOR, box_rect, border_radius=0)
            
            for star in box['stars']:
                pulse = math.sin(current_time * star['speed'] + star['offset'])
                np = (pulse + 1.0) / 2.0 
                star_r = int(star['color'][0] * np)
                star_g = int(star['color'][1] * np)
                star_b = int(star['color'][2] * np)
                c_star = (star_r, star_g, star_b)
                
                if is_phase1 or is_phase2:
                    c_star = blend_color(c_star, (255, 255, 255), phase1_ratio if is_phase1 else 1.0)
                    
                pygame.draw.circle(screen, c_star, (int(x + star['x']), int(y + star['y'])), star['size'])
                
            for ss in box['shooting_stars'][:]:
                ss['x'] += ss['vx']
                ss['y'] += ss['vy']
                if ss['y'] > BOX_SIZE + ss['len'] or ss['x'] < -ss['len'] or ss['x'] > BOX_SIZE + ss['len']:
                    box['shooting_stars'].remove(ss)
                else:
                    c_ss = (255, 255, 255)
                    if is_phase1 or is_phase2:
                        c_ss = blend_color(c_ss, (255, 255, 255), phase1_ratio if is_phase1 else 1.0)
                    start_pos = (int(x + ss['x']), int(y + ss['y']))
                    end_pos = (int(x + ss['x'] - ss['vx'] * 3), int(y + ss['y'] - ss['vy'] * 3))
                    pygame.draw.line(screen, c_ss, start_pos, end_pos, 2)
                
            pygame.draw.rect(screen, curr_border, box_rect, width=2, border_radius=0)
            
            wrapped = box['wrapped']
            start_y = y + (BOX_SIZE - len(wrapped) * font.get_height()) // 2
            
            for l_idx, wrap_line in enumerate(wrapped):
                line_w = sum(font.size(w)[0] + space_w for _, _, w in wrap_line) - space_w
                curr_x = x + (BOX_SIZE - line_w) // 2
                curr_y = start_y + l_idx * font.get_height()
                
                for word_start, word_dur, word in wrap_line:
                    if current_time >= word_start:
                        color = get_fade_in_color(current_time - word_start, word_dur * 0.5, BOX_COLOR)
                        if color:
                            if is_phase1 or is_phase2:
                                color = blend_color(color, (255, 255, 255), phase1_ratio if is_phase1 else 1.0)
                            
                            is_active = (current_time < word_start + word_dur)
                            if is_active and not (is_phase1 or is_phase2):
                                draw_neon_text(screen, word, font, color, curr_x, curr_y)
                            else:
                                screen.blit(font.render(word, True, color), (curr_x, curr_y))
                    curr_x += font.size(word)[0] + space_w

        wm_surf = font_small.render(_d('QHJpbi5yZW56ZQ=='), True, (255, 255, 255))
        screen.blit(wm_surf, (screen_w - wm_surf.get_width() - 40, screen_h - wm_surf.get_height() - 40))

        pygame.display.flip()
        clock.tick(60)
        
    player.close()
    set_window_opacity(255)
    pygame.event.clear()

def main():
    pygame.init()
    info = pygame.display.Info()
    screen_w, screen_h = info.current_w, info.current_h
    screen = pygame.display.set_mode((screen_w, screen_h), pygame.NOFRAME)
    pygame.display.set_caption("Lyrics Cosmo")
    
    make_window_transparent_overlay()
    
    font_title = pygame.font.SysFont("segoeui", 52, bold=True)
    font_btn = pygame.font.SysFont("segoeui", 26, bold=True)
    font_small = pygame.font.SysFont("segoeui", 16, bold=True)
    font_sync = pygame.font.SysFont("segoeui", 34, bold=True)
    font_play = pygame.font.SysFont("segoeui", 34, bold=True)
    font_guide = pygame.font.SysFont("segoeui", 22)
    
    menu_stars = generate_galaxy_stars(120, 800, 550)
    sync_stars = generate_galaxy_stars(150, 1200, 250)
    guide_stars = generate_galaxy_stars(150, 900, 550)
    settings_stars = generate_galaxy_stars(150, 800, 480)
    
    current_state = 'menu'
    running = True
    clock = pygame.time.Clock()
    
    while running:
        current_time = pygame.time.get_ticks() / 1000.0
        mouse_pos = pygame.mouse.get_pos()
        events = pygame.event.get()
        
        any_hover = False
        
        for event in events:
            if event.type == pygame.QUIT:
                running = False
        
        if current_state == 'menu':
            screen.fill(TRANSPARENT_KEY)
            rect = draw_centered_ui_block(screen, 800, 550, menu_stars, current_time)
            
            title_surf = font_title.render("Lyrics Cosmo", True, (255, 255, 255))
            screen.blit(title_surf, (rect.x + (rect.width - title_surf.get_width()) // 2, rect.y + 30))
            
            btn_sync, h1 = draw_button(screen, font_btn, "1. Sync Lyrics", rect.centerx, rect.y + 130, mouse_pos)
            btn_play, h2 = draw_button(screen, font_btn, "2. Play Lyrics", rect.centerx, rect.y + 190, mouse_pos)
            btn_guide, h3 = draw_button(screen, font_btn, "3. Instructions", rect.centerx, rect.y + 250, mouse_pos)
            btn_settings, h4 = draw_button(screen, font_btn, "4. Settings", rect.centerx, rect.y + 310, mouse_pos)
            btn_exit, h5 = draw_button(screen, font_btn, "5. Exit", rect.centerx, rect.y + 370, mouse_pos)
            
            cx = rect.x + 30
            cy = rect.y + 450
            
            t1 = font_small.render(_d('bWFkZSBieSByZW56ZQ=='), True, (255, 255, 255))
            screen.blit(t1, (cx, cy))
            cy += 25
            
            t2_pre = font_small.render("tiktok: ", True, (255, 255, 255))
            screen.blit(t2_pre, (cx, cy))
            t2 = font_small.render(_d('QHJpbi5yZW56ZQ=='), True, (0, 255, 255))
            r2 = screen.blit(t2, (cx + t2_pre.get_width(), cy))
            cy += 25
            
            t3_pre = font_small.render("Github: ", True, (255, 255, 255))
            screen.blit(t3_pre, (cx, cy))
            t3 = font_small.render(_d('anJlbnpl'), True, (0, 255, 255))
            r3 = screen.blit(t3, (cx + t3_pre.get_width(), cy))
            
            h_t2 = r2.collidepoint(mouse_pos)
            h_t3 = r3.collidepoint(mouse_pos)
            
            any_hover = h1 or h2 or h3 or h4 or h5 or h_t2 or h_t3
            
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if h1: current_state = 'sync'
                    elif h2: current_state = 'play'
                    elif h3: current_state = 'guide'
                    elif h4: current_state = 'settings'
                    elif h5: running = False
                    elif h_t2: webbrowser.open(_d('aHR0cHM6Ly93d3cudGlrdG9rLmNvbS9AcmluLnJlbnplP19yPTEmX3Q9WlMtOTdqTlBsbGg1UXo='))
                    elif h_t3: webbrowser.open(_d('aHR0cHM6Ly9naXRodWIuY29tL2pyZW56ZS9KcmVuemUtQ29kZXM='))
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
            
            pygame.display.flip()
            
        elif current_state == 'settings':
            screen.fill(TRANSPARENT_KEY)
            rect = draw_centered_ui_block(screen, 800, 480, settings_stars, current_time)
            
            title_surf = font_title.render("Settings", True, (255, 255, 255))
            screen.blit(title_surf, (rect.x + (rect.width - title_surf.get_width()) // 2, rect.y + 40))
            
            btn_speed, h1 = draw_button(screen, font_btn, f"Float Speed: {int(SETTINGS['float_duration'])}s", rect.centerx, rect.y + 180, mouse_pos)
            btn_theme, h2 = draw_button(screen, font_btn, f"Theme: {SETTINGS['theme']}", rect.centerx, rect.y + 250, mouse_pos)
            btn_back, h3 = draw_button(screen, font_btn, "Back to Menu", rect.centerx, rect.y + 350, mouse_pos)
            
            any_hover = h1 or h2 or h3
            
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if h1:
                        speeds = [10.0, 15.0, 17.0, 20.0, 25.0]
                        idx = speeds.index(SETTINGS['float_duration'])
                        SETTINGS['float_duration'] = speeds[(idx + 1) % len(speeds)]
                    elif h2:
                        theme_names = list(THEMES.keys())
                        idx = theme_names.index(SETTINGS['theme'])
                        SETTINGS['theme'] = theme_names[(idx + 1) % len(theme_names)]
                        
                        menu_stars = generate_galaxy_stars(120, 800, 550)
                        sync_stars = generate_galaxy_stars(150, 1200, 250)
                        guide_stars = generate_galaxy_stars(150, 900, 550)
                        settings_stars = generate_galaxy_stars(150, 800, 480)
                    elif h3:
                        current_state = 'menu'
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    current_state = 'menu'
            
            pygame.display.flip()
            
        elif current_state == 'guide':
            screen.fill(TRANSPARENT_KEY)
            rect = draw_centered_ui_block(screen, 900, 550, guide_stars, current_time)
            
            title_surf = font_title.render("Instructions", True, (255, 255, 255))
            screen.blit(title_surf, (rect.x + (rect.width - title_surf.get_width()) // 2, rect.y + 20))
            
            lines = [
                "SETUP:",
                "1. Click '1. Sync Lyrics' from the menu.",
                "2. A window will ask you to select your audio file (.mp3, .wav).",
                "3. Paste your lyrics. (Each lyric sentence MUST be on a new line).",
                "",
                "SYNCING:",
                "1. The song will play. TAP the spacebar exactly when each word starts.",
                "2. Your taps map out exactly when words should fade in.",
                "",
                "PLAYING:",
                "1. Just click '2. Play Lyrics'!",
                "2. The window vanishes, and lyrics float majestically over your desktop!"
            ]
            
            cy = rect.y + 80
            for line in lines:
                lsurf = font_guide.render(line, True, (200, 200, 200))
                screen.blit(lsurf, (rect.x + 40, cy))
                cy += 28
                
            cy += 15
            msg1 = font_guide.render("Please follow Renz on TikTok. It helps me create more projects like this!", True, (255, 255, 255))
            screen.blit(msg1, (rect.x + 40, cy))
            cy += 30
            msg2 = font_guide.render("Sincerely, ", True, (255, 255, 255))
            screen.blit(msg2, (rect.x + 40, cy))
            
            tk_link = font_guide.render(_d('QHJpbi5yZW56ZQ=='), True, (0, 255, 255))
            r_tk = screen.blit(tk_link, (rect.x + 40 + msg2.get_width(), cy))
                
            btn_back, h_back = draw_button(screen, font_btn, "Back to Menu", rect.centerx, rect.y + 490, mouse_pos)
            h_tk = r_tk.collidepoint(mouse_pos)
            
            any_hover = h_back or h_tk
            
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if h_back: current_state = 'menu'
                    elif h_tk: webbrowser.open(_d('aHR0cHM6Ly93d3cudGlrdG9rLmNvbS9AcmluLnJlbnplP19yPTEmX3Q9WlMtOTdqTlBsbGg1UXo='))
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    current_state = 'menu'
                    
            pygame.display.flip()
            
        elif current_state == 'sync':
            run_sync_mode(screen, font_sync, sync_stars)
            current_state = 'menu'
            
        elif current_state == 'play':
            run_play_mode(screen, font_play, menu_stars)
            current_state = 'menu'

        if any_hover:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
            
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
