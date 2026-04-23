import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import shutil
import zipfile
import re
import base64
import json
import tempfile
import urllib.request
from pathlib import Path
import webbrowser


# ------------------ Загрузка библиотек ------------------
def download_libs_if_needed(libs_dir):
    libs_dir.mkdir(exist_ok=True)
    files = {
        "reveal.js": "https://cdn.jsdelivr.net/npm/reveal.js@4.3.1/dist/reveal.js",
        "reveal.css": "https://cdn.jsdelivr.net/npm/reveal.js@4.3.1/dist/reveal.css",
        "theme-black.css": "https://cdn.jsdelivr.net/npm/reveal.js@4.3.1/dist/theme/black.css",
        "pannellum.js": "https://cdn.jsdelivr.net/npm/pannellum@2.5.6/build/pannellum.js",
        "pannellum.css": "https://cdn.jsdelivr.net/npm/pannellum@2.5.6/build/pannellum.css",
    }
    for name, url in files.items():
        dest = libs_dir / name
        if not dest.exists():
            try:
                urllib.request.urlretrieve(url, dest)
            except Exception:
                return False
    return True


# ------------------ Нормализация имён ------------------
def normalize_filename(filename):
    trans = {'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e', 'ж': 'zh', 'з': 'z', 'и': 'i',
             'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
             'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '', 'ы': 'y', 'ь': '',
             'э': 'e', 'ю': 'yu', 'я': 'ya',
             'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'E', 'Ж': 'ZH', 'З': 'Z', 'И': 'I',
             'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T',
             'У': 'U', 'Ф': 'F', 'Х': 'H', 'Ц': 'TS', 'Ч': 'CH', 'Ш': 'SH', 'Щ': 'SCH', 'Ъ': '', 'Ы': 'Y', 'Ь': '',
             'Э': 'E', 'Ю': 'YU', 'Я': 'YA'}
    name, ext = os.path.splitext(filename)
    name = ''.join(trans.get(c, c) for c in name)
    name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
    return name + ext.lower()


def image_to_base64(image_path):
    with open(image_path, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode('utf-8')
    ext = os.path.splitext(image_path)[1].lower()
    mime = 'image/jpeg' if ext in ('.jpg',
                                   '.jpeg') else 'image/png' if ext == '.png' else 'image/gif' if ext == '.gif' else 'application/octet-stream'
    return f'data:{mime};base64,{b64}'


# ------------------ Форматирование текста ------------------
def format_text(text):
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    return text


# ------------------ Генерация HTML ------------------
def generate_html(slides, offline_libs=True):
    base_path = "./libs/" if offline_libs else ""
    reveal_js = f"{base_path}reveal.js" if offline_libs else "https://cdn.jsdelivr.net/npm/reveal.js@4.3.1/dist/reveal.js"
    reveal_css = f"{base_path}reveal.css" if offline_libs else "https://cdn.jsdelivr.net/npm/reveal.js@4.3.1/dist/reveal.css"
    theme_css = f"{base_path}theme-black.css" if offline_libs else "https://cdn.jsdelivr.net/npm/reveal.js@4.3.1/dist/theme/black.css"
    pannellum_js = f"{base_path}pannellum.js" if offline_libs else "https://cdn.jsdelivr.net/npm/pannellum@2.5.6/build/pannellum.js"
    pannellum_css = f"{base_path}pannellum.css" if offline_libs else "https://cdn.jsdelivr.net/npm/pannellum@2.5.6/build/pannellum.css"

    slides_html = []
    audio_config = {}
    for idx, slide in enumerate(slides):
        slide_audio = slide.get("audio", "")
        messages = slide.get("messages", [])
        audio_config[idx] = {"slide": f"./assets/{slide_audio}" if slide_audio else "", "messages": []}
        for msg in messages:
            audio_config[idx]["messages"].append(f"./assets/{msg['audio']}" if msg.get("audio") else "")

        slide_type = slide["type"]
        background_attr = ""
        background_div = ""
        if slide_type == "image":
            background_attr = f'data-background-image="./assets/{slide.get("filename", "")}" data-background-size="cover" data-background-position="center"'
        elif slide_type == "panorama":
            b64_data = slide.get("base64", "")
            pano_id = f"pano_{idx}"
            background_div = f'''
            <div id="{pano_id}" style="width:100%; height:100%; position:absolute; top:0; left:0; z-index:0;"></div>
            <script>
                (function() {{
                    var css = document.createElement('link');
                    css.rel = 'stylesheet';
                    css.href = '{pannellum_css}';
                    document.head.appendChild(css);
                    var script = document.createElement('script');
                    script.src = '{pannellum_js}';
                    script.onload = function() {{
                        pannellum.viewer('{pano_id}', {{
                            "type": "equirectangular",
                            "panorama": "{b64_data}",
                            "autoLoad": true,
                            "showControls": false,
                            "mouseZoom": false,
                            "draggable": true
                        }});
                    }};
                    document.head.appendChild(script);
                }})();
            </script>
            '''

        audio_panel = f'''
        <div class="audio-panel" id="audio-panel-{idx}">
            <div class="audio-icon" onclick="toggleAudioPanel({idx})">&#128266;</div>
            <div class="audio-controls" id="audio-controls-{idx}" style="display:none;">
                <input type="range" class="volume-slider" id="volume-{idx}" min="0" max="1" step="0.1" value="1" oninput="setVolume({idx}, this.value)">
                <button onclick="playPauseAudio({idx})" id="playpause-{idx}">▶</button>
                <button onclick="stopAudio({idx})">■</button>
            </div>
        </div>
        '''

        textbox_html = ""
        if messages:
            msgs_js = []
            for msg in messages:
                title = format_text(msg.get("title", ""))
                text = format_text(msg.get("text", ""))
                msgs_js.append({"title": title, "text": text})
            messages_json = json.dumps(msgs_js, ensure_ascii=False)
            textbox_html = f'''
            <div class="textbox-container" id="textbox-container-{idx}">
                <div class="textbox-nav">
                    <button class="nav-arrow" id="prev-msg-{idx}" onclick="prevMessage({idx})">&larr;</button>
                    <button class="nav-arrow" id="next-msg-{idx}" onclick="nextMessage({idx})">&rarr;</button>
                </div>
                <div class="textbox">
                    <div class="textbox-title" id="textbox-title-{idx}"></div>
                    <div class="textbox-text" id="textbox-text-{idx}"></div>
                </div>
            </div>
            <script>
                (function() {{
                    var messages = {messages_json};
                    var currentMsg = 0;
                    var titleEl = document.getElementById('textbox-title-{idx}');
                    var textEl = document.getElementById('textbox-text-{idx}');
                    var container = document.getElementById('textbox-container-{idx}');
                    var prevBtn = document.getElementById('prev-msg-{idx}');
                    var nextBtn = document.getElementById('next-msg-{idx}');

                    function showMessage(index) {{
                        if (index >= 0 && index < messages.length) {{
                            var msg = messages[index];
                            titleEl.innerHTML = msg.title;
                            textEl.innerHTML = msg.text;
                            currentMsg = index;
                            updateNavButtons();
                            // Аудио сообщения
                            var audioSrc = getMessageAudio({idx}, index);
                            if (audioSrc) {{
                                setTimeout(function() {{
                                    playMessageAudio(audioSrc);
                                }}, 1000);
                            }}
                        }}
                    }}

                    function updateNavButtons() {{
                        if (prevBtn) {{
                            prevBtn.disabled = (currentMsg === 0);
                        }}
                        if (nextBtn) {{
                            nextBtn.disabled = (currentMsg === messages.length - 1);
                        }}
                    }}

                    window.prevMessage = function(idx) {{
                        if (currentMsg > 0) showMessage(currentMsg - 1);
                    }};

                    window.nextMessage = function(idx) {{
                        if (currentMsg < messages.length - 1) showMessage(currentMsg + 1);
                    }};

                    showMessage(currentMsg);

                    container.addEventListener('click', function(e) {{
                        if (!e.target.closest('.nav-arrow')) {{
                            if (currentMsg < messages.length - 1) showMessage(currentMsg + 1);
                        }}
                    }});

                    // Переключение по пробелу
                    document.addEventListener('keydown', function(e) {{
                        if (e.code === 'Space' && Reveal.getIndices().h === {idx}) {{
                            e.preventDefault();
                            if (currentMsg < messages.length - 1) {{
                                showMessage(currentMsg + 1);
                            }}
                        }}
                    }});
                }})();
            </script>
            '''

        if slide_type in ("image", "panorama"):
            section_open = f'<section {background_attr}>' if slide_type == "image" else '<section>'
            slide_content = f'''
            {section_open}
                {background_div}
                {textbox_html}
                {audio_panel}
            </section>
            '''
        elif slide_type == "quiz":
            q = slide["question"]
            options = slide["options"]
            correct = slide["correct"]
            options_html = ""
            for i, opt in enumerate(options):
                img_html = ""
                if opt.get("image"):
                    img_html = f'<img src="./assets/{opt["image"]}" alt="Вариант {i + 1}">'
                options_html += f'''
                <div class="quiz-option" data-opt="{i}">
                    {img_html}
                    <div class="quiz-option-text">{opt["text"]}</div>
                </div>
                '''
            slide_content = f'''
            <section>
                <div class="quiz-container">
                    <h2>{q}</h2>
                    <div class="quiz-options" id="quiz-options-{idx}">
                        {options_html}
                    </div>
                    <p id="quiz-result-{idx}" style="margin-top: 20px; font-size: 1.5rem;"></p>
                </div>
                <div id="quiz-overlay-{idx}" class="quiz-overlay"></div>
                {audio_panel}
                <script>
                    (function() {{
                        var correct = {correct};
                        var options = document.querySelectorAll('#quiz-options-{idx} .quiz-option');
                        var resultEl = document.getElementById('quiz-result-{idx}');
                        var overlay = document.getElementById('quiz-overlay-{idx}');
                        var answered = false;

                        function showFlash() {{
                            overlay.style.opacity = '0.5';
                            setTimeout(function() {{ overlay.style.opacity = '0'; }}, 200);
                        }}

                        options.forEach(function(opt) {{
                            opt.addEventListener('click', function() {{
                                if (answered) return;
                                var selected = parseInt(this.getAttribute('data-opt'));
                                if (selected === correct) {{
                                    resultEl.innerHTML = 'Правильно!';
                                    resultEl.style.color = '#4CAF50';
                                    answered = true;
                                }} else {{
                                    resultEl.innerHTML = 'Неправильно';
                                    resultEl.style.color = '#f44336';
                                    showFlash();
                                }}
                            }});
                        }});
                    }})();
                </script>
            </section>
            '''
        else:
            slide_content = "<section><h2>Неизвестный тип слайда</h2></section>"

        slides_html.append(slide_content)

    slides_combined = "\n".join(slides_html)
    audio_config_json = json.dumps(audio_config, ensure_ascii=False)

    return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Маршрут</title>
    <base href="./">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="{reveal_css}">
    <link rel="stylesheet" href="{theme_css}">
    <style>
        * {{ font-family: 'Inter', sans-serif; }}
        .reveal .slides section {{
            padding: 0 !important;
            height: 100% !important;
            position: relative !important;
        }}
        body, html {{ margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; }}
        .reveal {{ width: 100vw; height: 100vh; }}
        #progress-counter {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(0,0,0,0.6);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 16px;
            z-index: 100;
            pointer-events: none;
            backdrop-filter: blur(4px);
        }}
        .audio-panel {{
            position: absolute;
            bottom: 20px;
            left: 20px;
            z-index: 200;
        }}
        .audio-icon {{
            background: rgba(0,0,0,0.3);
            color: white;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            cursor: pointer;
            backdrop-filter: blur(4px);
            transition: 0.2s;
        }}
        .audio-icon:hover {{ background: rgba(0,0,0,0.6); }}
        .audio-controls {{
            position: absolute;
            bottom: 50px;
            left: 0;
            background: rgba(0,0,0,0.5);
            backdrop-filter: blur(4px);
            padding: 10px;
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            min-width: 120px;
        }}
        .audio-controls input[type=range] {{ width: 100%; }}
        .audio-controls button {{
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            padding: 6px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }}
        .audio-controls button:hover {{ background: rgba(255,255,255,0.4); }}
        .textbox-container {{
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 25vh;
            background: linear-gradient(to top, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0) 100%);
            z-index: 10;
            display: flex;
            align-items: flex-end;
            padding: 0 40px 20px 40px;
            cursor: pointer;
            color: white;
            box-sizing: border-box;
        }}
        .textbox-nav {{
            position: absolute;
            top: -30px;
            right: 20px;
            display: flex;
            gap: 10px;
            z-index: 15;
        }}
        .nav-arrow {{
            background: rgba(0,0,0,0.5);
            color: white;
            border: none;
            border-radius: 50%;
            width: 36px;
            height: 36px;
            font-size: 20px;
            cursor: pointer;
            backdrop-filter: blur(4px);
            display: flex;
            align-items: center;
            justify-content: center;
            transition: 0.2s;
        }}
        .nav-arrow:hover {{ background: rgba(0,0,0,0.8); }}
        .nav-arrow:disabled {{ opacity: 0.3; cursor: default; }}
        .textbox {{ width: 100%; }}
        .textbox-title {{
            font-weight: 700;
            font-size: 2.2rem;
            margin-bottom: 8px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }}
        .textbox-text {{
            font-size: 1.3rem;
            line-height: 1.4;
            text-shadow: 1px 1px 3px rgba(0,0,0,0.5);
        }}
        .quiz-container {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 100vh;
            padding: 20px;
            color: white;
            z-index: 5;
            position: relative;
        }}
        .quiz-options {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            max-width: 800px;
            margin-top: 30px;
        }}
        .quiz-option {{
            background: rgba(30,30,30,0.8);
            border: 2px solid #555;
            border-radius: 16px;
            padding: 10px;
            cursor: pointer;
            transition: 0.2s;
            backdrop-filter: blur(4px);
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .quiz-option:hover {{ background: rgba(60,60,60,0.8); border-color: #aaa; }}
        .quiz-option img {{
            width: 100%;
            max-height: 150px;
            object-fit: cover;
            border-radius: 12px;
            margin-bottom: 8px;
        }}
        .quiz-option-text {{
            font-size: 1.3rem;
            font-weight: 600;
            text-align: center;
            padding: 8px;
        }}
        .quiz-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: red;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.1s;
            z-index: 999;
        }}
        .reveal section > *:not(.textbox-container):not(.audio-panel):not(#progress-counter) {{
            z-index: 5;
            position: relative;
        }}
    </style>
</head>
<body>
    <div class="reveal">
        <div class="slides">
            {slides_combined}
        </div>
    </div>
    <div id="progress-counter">Пройдено: <span id="completed-value">0</span> / {len(slides)}</div>
    <script>
        var audioConfig = {audio_config_json};
        var currentAudio = null;
        var currentVolume = 1.0;
        var slideAudioElements = {{}};

        function getSlideAudioSrc(slideIdx) {{
            return audioConfig[slideIdx] ? audioConfig[slideIdx].slide : '';
        }}

        function getMessageAudio(slideIdx, msgIdx) {{
            if (audioConfig[slideIdx] && audioConfig[slideIdx].messages[msgIdx]) {{
                return audioConfig[slideIdx].messages[msgIdx];
            }}
            return '';
        }}

        function setVolume(slideIdx, val) {{
            currentVolume = parseFloat(val);
            if (slideAudioElements[slideIdx]) {{
                slideAudioElements[slideIdx].volume = currentVolume;
            }}
        }}

        function toggleAudioPanel(slideIdx) {{
            var controls = document.getElementById('audio-controls-' + slideIdx);
            if (controls) {{
                controls.style.display = controls.style.display === 'none' ? 'flex' : 'none';
            }}
        }}

        function playPauseAudio(slideIdx) {{
            var audio = slideAudioElements[slideIdx];
            if (!audio) {{
                var src = getSlideAudioSrc(slideIdx);
                if (!src) return;
                audio = new Audio(src);
                audio.volume = currentVolume;
                slideAudioElements[slideIdx] = audio;
            }}
            if (audio.paused) {{
                audio.play();
                document.getElementById('playpause-' + slideIdx).textContent = '⏸';
            }} else {{
                audio.pause();
                document.getElementById('playpause-' + slideIdx).textContent = '▶';
            }}
        }}

        function stopAudio(slideIdx) {{
            var audio = slideAudioElements[slideIdx];
            if (audio) {{
                audio.pause();
                audio.currentTime = 0;
                document.getElementById('playpause-' + slideIdx).textContent = '▶';
            }}
        }}

        function playMessageAudio(src) {{
            if (!src) return;
            if (currentAudio) {{
                currentAudio.pause();
                currentAudio = null;
            }}
            var audio = new Audio(src);
            audio.volume = currentVolume;
            currentAudio = audio;
            audio.play();
        }}

        function onSlideChange(event) {{
            var idx = event.indexh;
            if (currentAudio) {{
                currentAudio.pause();
                currentAudio = null;
            }}
            for (var key in slideAudioElements) {{
                if (slideAudioElements[key]) {{
                    slideAudioElements[key].pause();
                }}
            }}
            window.COMPLETED = idx + 1;
            document.getElementById('completed-value').textContent = window.COMPLETED;

            var slideSrc = getSlideAudioSrc(idx);
            if (slideSrc) {{
                setTimeout(function() {{
                    var audio = new Audio(slideSrc);
                    audio.volume = currentVolume;
                    slideAudioElements[idx] = audio;
                    audio.play();
                    var btn = document.getElementById('playpause-' + idx);
                    if (btn) btn.textContent = '⏸';
                }}, 2000);
            }}
        }}

        window.COMPLETED = 0;
    </script>
    <script src="{reveal_js}"></script>
    <script>
        Reveal.initialize({{
            hash: true,
            transition: 'slide',
            backgroundTransition: 'zoom',
            width: '100%',
            height: '100%',
            margin: 0,
            minScale: 1,
            maxScale: 1,
            keyboard: {{
                32: null  // отключаем пробел для навигации Reveal
            }}
        }});
        Reveal.on('slidechanged', onSlideChange);
        Reveal.on('ready', function(event) {{
            onSlideChange(event);
        }});
    </script>
</body>
</html>'''


# ------------------ GUI (без изменений) ------------------
class PresentationBuilder:
    def __init__(self, root):
        self.root = root
        self.root.title("Конструктор маршрутов .irf")
        self.root.geometry("900x700")
        self.slides = []
        self.temp_dir = None
        self.metadata = {"Name": "", "Desc": "", "Time": "", "Pic": ""}
        self.create_widgets()

    def create_widgets(self):
        toolbar = tk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        tk.Button(toolbar, text="Открыть .irf", command=self.open_irf).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Добавить", command=self.add_slide).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Изменить", command=self.edit_slide).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Удалить", command=self.delete_slide).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Вверх", command=self.move_up).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Вниз", command=self.move_down).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Экспорт .irf", command=self.export).pack(side=tk.RIGHT, padx=5)

        meta_frame = tk.LabelFrame(self.root, text="Метаданные маршрута", padx=5, pady=5)
        meta_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(meta_frame, text="Название:").grid(row=0, column=0, sticky=tk.W)
        self.name_entry = tk.Entry(meta_frame, width=50)
        self.name_entry.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)
        tk.Label(meta_frame, text="Описание:").grid(row=1, column=0, sticky=tk.W)
        self.desc_entry = tk.Entry(meta_frame, width=50)
        self.desc_entry.grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)
        tk.Label(meta_frame, text="Время:").grid(row=2, column=0, sticky=tk.W)
        self.time_entry = tk.Entry(meta_frame, width=20)
        self.time_entry.grid(row=2, column=1, padx=5, pady=2, sticky=tk.W)
        tk.Label(meta_frame, text="Картинка-превью:").grid(row=3, column=0, sticky=tk.W)
        self.pic_var = tk.StringVar()
        pic_frame = tk.Frame(meta_frame)
        pic_frame.grid(row=3, column=1, sticky=tk.W)
        tk.Entry(pic_frame, textvariable=self.pic_var, width=40).pack(side=tk.LEFT)
        tk.Button(pic_frame, text="Обзор...", command=self.browse_pic).pack(side=tk.LEFT, padx=5)

        list_frame = tk.Frame(self.root)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                  font=("TkDefaultFont", 11),
                                  selectmode=tk.SINGLE, activestyle="none")
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)
        self.refresh_listbox()

    def browse_pic(self):
        filetypes = [("Изображения", "*.jpg *.jpeg *.png *.gif *.bmp"), ("Все файлы", "*.*")]
        filename = filedialog.askopenfilename(title="Выберите превью-картинку", filetypes=filetypes)
        if filename:
            self.pic_var.set(filename)

    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for i, slide in enumerate(self.slides):
            stype = slide["type"]
            if stype == "image":
                text = f"{i + 1}. Изображение"
            elif stype == "panorama":
                text = f"{i + 1}. Панорама"
            elif stype == "quiz":
                text = f"{i + 1}. Викторина: {slide.get('question', '')[:30]}"
            else:
                text = f"{i + 1}. Неизвестный тип"
            if slide.get("messages"): text += f" ({len(slide['messages'])} текстов)"
            if slide.get("audio"): text += " [A]"
            self.listbox.insert(tk.END, text)

    def add_slide(self):
        dialog = SlideDialog(self.root, title="Добавить слайд")
        if dialog.result:
            self.slides.append(dialog.result)
            self.refresh_listbox()

    def edit_slide(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Не выбрано", "Выберите слайд")
            return
        idx = sel[0]
        slide = self.slides[idx]
        dialog = SlideDialog(self.root, title="Изменить слайд", slide_data=slide)
        if dialog.result:
            self.slides[idx] = dialog.result
            self.refresh_listbox()

    def delete_slide(self):
        sel = self.listbox.curselection()
        if not sel: return
        idx = sel[0]
        del self.slides[idx]
        self.refresh_listbox()

    def move_up(self):
        sel = self.listbox.curselection()
        if not sel or sel[0] == 0: return
        idx = sel[0]
        self.slides[idx], self.slides[idx - 1] = self.slides[idx - 1], self.slides[idx]
        self.refresh_listbox()
        self.listbox.selection_set(idx - 1)

    def move_down(self):
        sel = self.listbox.curselection()
        if not sel or sel[0] >= len(self.slides) - 1: return
        idx = sel[0]
        self.slides[idx], self.slides[idx + 1] = self.slides[idx + 1], self.slides[idx]
        self.refresh_listbox()
        self.listbox.selection_set(idx + 1)

    def open_irf(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Interactive Route File", "*.irf"), ("Все файлы", "*.*")],
            title="Открыть маршрут .irf"
        )
        if not file_path: return
        try:
            if self.temp_dir: shutil.rmtree(self.temp_dir, ignore_errors=True)
            self.temp_dir = tempfile.mkdtemp(prefix="irf_editor_")
            with zipfile.ZipFile(file_path, 'r') as zf:
                zf.extractall(self.temp_dir)
            meta_path = os.path.join(self.temp_dir, "metadata.json")
            if os.path.exists(meta_path):
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                self.name_entry.delete(0, tk.END);
                self.name_entry.insert(0, meta.get("Name", ""))
                self.desc_entry.delete(0, tk.END);
                self.desc_entry.insert(0, meta.get("Desc", ""))
                self.time_entry.delete(0, tk.END);
                self.time_entry.insert(0, meta.get("Time", ""))
                pic_name = meta.get("Pic", "")
                if pic_name:
                    pic_path = os.path.join(self.temp_dir, pic_name)
                    if os.path.exists(pic_path):
                        self.pic_var.set(pic_path)
                    else:
                        self.pic_var.set("")
                self.metadata = meta.copy()
            else:
                messagebox.showwarning("Внимание", "metadata.json не найден, метаданные не загружены.")
            json_path = os.path.join(self.temp_dir, "presentation.json")
            if not os.path.exists(json_path):
                messagebox.showerror("Ошибка", "Файл presentation.json не найден в архиве.")
                return
            with open(json_path, 'r', encoding='utf-8') as f:
                slides_data = json.load(f)
            assets_src = os.path.join(self.temp_dir, "assets")
            assets_dst = os.path.join(self.temp_dir, "edit_assets")
            os.makedirs(assets_dst, exist_ok=True)
            new_slides = []
            for s in slides_data:
                slide = s.copy()
                if slide["type"] in ("image", "panorama"):
                    fname = slide.get("filename", "")
                    if fname:
                        src = os.path.join(assets_src, fname)
                        dst = os.path.join(assets_dst, fname)
                        if os.path.exists(src):
                            shutil.copy2(src, dst)
                            slide["src"] = dst
                        else:
                            slide["src"] = ""
                if slide.get("audio"):
                    src = os.path.join(assets_src, slide["audio"])
                    dst = os.path.join(assets_dst, slide["audio"])
                    if os.path.exists(src):
                        shutil.copy2(src, dst)
                        slide["audio"] = dst
                    else:
                        slide["audio"] = ""
                if slide.get("messages"):
                    for msg in slide["messages"]:
                        if msg.get("audio"):
                            src = os.path.join(assets_src, msg["audio"])
                            dst = os.path.join(assets_dst, msg["audio"])
                            if os.path.exists(src):
                                shutil.copy2(src, dst)
                                msg["audio"] = dst
                            else:
                                msg["audio"] = ""
                if slide["type"] == "quiz":
                    for opt in slide["options"]:
                        if opt.get("image"):
                            src = os.path.join(assets_src, opt["image"])
                            dst = os.path.join(assets_dst, opt["image"])
                            if os.path.exists(src):
                                shutil.copy2(src, dst)
                                opt["image"] = dst
                            else:
                                opt["image"] = ""
                new_slides.append(slide)
            self.slides = new_slides
            self.refresh_listbox()
            messagebox.showinfo("Готово", "Маршрут загружен.")
        except Exception as e:
            messagebox.showerror("Ошибка открытия", str(e))

    def export(self):
        if not self.slides:
            messagebox.showwarning("Нет слайдов", "Добавьте хотя бы один слайд.")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".irf",
            filetypes=[("Interactive Route File", "*.irf")],
            title="Сохранить маршрут как..."
        )
        if not file_path: return
        temp_dir = Path("temp_build")
        temp_dir.mkdir(exist_ok=True)
        assets_dir = temp_dir / "assets"
        assets_dir.mkdir(exist_ok=True)
        libs_dir = temp_dir / "libs"
        libs_dir.mkdir(exist_ok=True)
        try:
            offline_ok = download_libs_if_needed(libs_dir)
            meta = {
                "Name": self.name_entry.get().strip(),
                "Desc": self.desc_entry.get().strip(),
                "Time": self.time_entry.get().strip(),
                "Pic": ""
            }
            pic_src = self.pic_var.get().strip()
            if pic_src and os.path.exists(pic_src):
                pic_name = normalize_filename(os.path.basename(pic_src))
                pic_dst = temp_dir / pic_name
                shutil.copy2(pic_src, pic_dst)
                meta["Pic"] = pic_name
            else:
                meta["Pic"] = ""
            meta_path = temp_dir / "metadata.json"
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
            slides_for_json = []
            for slide in self.slides:
                slide_copy = slide.copy()
                if slide["type"] in ("image", "panorama"):
                    src_path = Path(slide["src"])
                    if not src_path.exists():
                        messagebox.showerror("Ошибка", f"Файл не найден: {src_path}")
                        return
                    safe_name = normalize_filename(src_path.name)
                    dest_path = assets_dir / safe_name
                    shutil.copy2(src_path, dest_path)
                    slide["filename"] = safe_name
                    slide_copy["filename"] = safe_name
                    if slide["type"] == "panorama":
                        b64 = image_to_base64(src_path)
                        slide["base64"] = b64
                elif slide["type"] == "quiz":
                    for opt in slide_copy["options"]:
                        if opt.get("image"):
                            img_path = Path(opt["image"])
                            if not img_path.exists():
                                messagebox.showerror("Ошибка", f"Файл не найден: {img_path}")
                                return
                            safe_img = normalize_filename(img_path.name)
                            shutil.copy2(img_path, assets_dir / safe_img)
                            opt["image"] = safe_img
                if slide.get("audio"):
                    audio_path = Path(slide["audio"])
                    if audio_path.exists():
                        safe_audio = normalize_filename(audio_path.name)
                        shutil.copy2(audio_path, assets_dir / safe_audio)
                        slide["audio"] = safe_audio
                        slide_copy["audio"] = safe_audio
                if slide.get("messages"):
                    for msg in slide_copy["messages"]:
                        if msg.get("audio"):
                            audio_path = Path(msg["audio"])
                            if audio_path.exists():
                                safe_audio = normalize_filename(audio_path.name)
                                shutil.copy2(audio_path, assets_dir / safe_audio)
                                msg["audio"] = safe_audio
                slides_for_json.append(slide_copy)
            pres_json = temp_dir / "presentation.json"
            with open(pres_json, 'w', encoding='utf-8') as f:
                json.dump(slides_for_json, f, ensure_ascii=False, indent=2)
            html_content = generate_html(self.slides, offline_libs=offline_ok)
            index_html = temp_dir / "index.html"
            index_html.write_text(html_content, encoding="utf-8")
            with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.write(index_html, arcname="index.html")
                zf.write(pres_json, arcname="presentation.json")
                zf.write(meta_path, arcname="metadata.json")
                if meta["Pic"]:
                    zf.write(temp_dir / meta["Pic"], arcname=meta["Pic"])
                for asset in assets_dir.iterdir():
                    zf.write(asset, arcname=f"assets/{asset.name}")
                if offline_ok:
                    for lib in libs_dir.iterdir():
                        zf.write(lib, arcname=f"libs/{lib.name}")
            messagebox.showinfo("Готово", f"Маршрут сохранён:\n{file_path}")
            if messagebox.askyesno("Открыть папку", "Открыть папку с файлом?"):
                webbrowser.open(os.path.dirname(file_path))
        except Exception as e:
            messagebox.showerror("Ошибка экспорта", str(e))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def __del__(self):
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)


# ------------------ Диалог слайда (без эмодзи) ------------------
class SlideDialog(tk.Toplevel):
    def __init__(self, parent, title="Слайд", slide_data=None):
        super().__init__(parent)
        self.title(title)
        self.result = None
        self.slide_data = slide_data
        self.type_var = tk.StringVar(value="image")
        self.src_var = tk.StringVar()
        self.audio_var = tk.StringVar()
        self.messages = []
        self.question_var = tk.StringVar()
        self.options = []
        self.correct_var = tk.IntVar(value=0)
        self.num_options = tk.IntVar(value=4)
        if slide_data:
            self.type_var.set(slide_data["type"])
            if slide_data["type"] in ("image", "panorama"):
                self.src_var.set(slide_data.get("src", ""))
                self.audio_var.set(slide_data.get("audio", ""))
                self.messages = slide_data.get("messages", [])
            elif slide_data["type"] == "quiz":
                self.question_var.set(slide_data.get("question", ""))
                self.options = slide_data.get("options", [])
                self.correct_var.set(slide_data.get("correct", 0))
                self.num_options.set(len(self.options))
                self.audio_var.set(slide_data.get("audio", ""))
        self.create_widgets()
        self.update_fields()
        self.transient(parent)
        self.grab_set()
        self.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        self.wait_window()

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(main_frame, text="Тип слайда:").grid(row=0, column=0, sticky=tk.W, pady=5)
        type_frame = ttk.Frame(main_frame)
        type_frame.grid(row=0, column=1, sticky=tk.W, pady=5)
        ttk.Radiobutton(type_frame, text="Изображение", variable=self.type_var, value="image",
                        command=self.update_fields).pack(side=tk.LEFT)
        ttk.Radiobutton(type_frame, text="Панорама 360", variable=self.type_var, value="panorama",
                        command=self.update_fields).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(type_frame, text="Викторина", variable=self.type_var, value="quiz",
                        command=self.update_fields).pack(side=tk.LEFT)
        self.fields_frame = ttk.Frame(main_frame)
        self.fields_frame.grid(row=1, column=0, columnspan=2, pady=10, sticky="nsew")
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="OK", command=self.on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=self.destroy).pack(side=tk.LEFT, padx=5)

    def update_fields(self):
        for widget in self.fields_frame.winfo_children():
            widget.destroy()
        t = self.type_var.get()
        row = 0
        if t in ("image", "panorama"):
            ttk.Label(self.fields_frame, text="Файл изображения:").grid(row=row, column=0, sticky=tk.W, pady=2)
            entry = ttk.Entry(self.fields_frame, textvariable=self.src_var, width=50)
            entry.grid(row=row, column=1, padx=5)
            ttk.Button(self.fields_frame, text="Обзор...", command=self.browse_image).grid(row=row, column=2)
            row += 1
            ttk.Label(self.fields_frame, text="Озвучка слайда (опционально):").grid(row=row, column=0, sticky=tk.W,
                                                                                    pady=2)
            entry_audio = ttk.Entry(self.fields_frame, textvariable=self.audio_var, width=50)
            entry_audio.grid(row=row, column=1, padx=5)
            ttk.Button(self.fields_frame, text="Обзор...", command=lambda: self.browse_audio(self.audio_var)).grid(
                row=row, column=2)
            row += 1
            ttk.Label(self.fields_frame, text="Текстовые сообщения:").grid(row=row, column=0, sticky=tk.W, pady=5)
            row += 1
            msg_frame = ttk.Frame(self.fields_frame)
            msg_frame.grid(row=row, column=0, columnspan=3, sticky="nsew")
            self.msg_listbox = tk.Listbox(msg_frame, height=4)
            self.msg_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scroll = ttk.Scrollbar(msg_frame, orient=tk.VERTICAL, command=self.msg_listbox.yview)
            scroll.pack(side=tk.RIGHT, fill=tk.Y)
            self.msg_listbox.config(yscrollcommand=scroll.set)
            btn_msg_frame = ttk.Frame(msg_frame)
            btn_msg_frame.pack(side=tk.BOTTOM, pady=5)
            ttk.Button(btn_msg_frame, text="Добавить", command=self.add_message).pack(side=tk.LEFT, padx=2)
            ttk.Button(btn_msg_frame, text="Изменить", command=self.edit_message).pack(side=tk.LEFT, padx=2)
            ttk.Button(btn_msg_frame, text="Удалить", command=self.delete_message).pack(side=tk.LEFT, padx=2)
            self.refresh_message_listbox()
            row += 1
        elif t == "quiz":
            ttk.Label(self.fields_frame, text="Вопрос:").grid(row=row, column=0, sticky=tk.W, pady=2)
            ttk.Entry(self.fields_frame, textvariable=self.question_var, width=60).grid(row=row, column=1, columnspan=2,
                                                                                        pady=2, sticky=tk.W)
            row += 1
            ttk.Label(self.fields_frame, text="Количество вариантов (до 6):").grid(row=row, column=0, sticky=tk.W,
                                                                                   pady=2)
            spin = ttk.Spinbox(self.fields_frame, from_=2, to=6, textvariable=self.num_options, width=5,
                               command=self.update_options_count)
            spin.grid(row=row, column=1, sticky=tk.W)
            row += 1
            self.options_frame = ttk.Frame(self.fields_frame)
            self.options_frame.grid(row=row, column=0, columnspan=3, sticky="nsew", pady=5)
            self.render_options()
            row += 1
            ttk.Label(self.fields_frame, text="Правильный ответ (номер):").grid(row=row, column=0, sticky=tk.W, pady=5)
            correct_frame = ttk.Frame(self.fields_frame)
            correct_frame.grid(row=row, column=1, columnspan=2, sticky=tk.W)
            self.correct_spin = ttk.Spinbox(correct_frame, from_=1, to=self.num_options.get(),
                                            textvariable=self.correct_var, width=5)
            self.correct_spin.pack(side=tk.LEFT)
            self.correct_var.set(min(self.correct_var.get(), self.num_options.get()))
            row += 1
            ttk.Label(self.fields_frame, text="Озвучка слайда (опционально):").grid(row=row, column=0, sticky=tk.W,
                                                                                    pady=2)
            entry_audio = ttk.Entry(self.fields_frame, textvariable=self.audio_var, width=50)
            entry_audio.grid(row=row, column=1, padx=5)
            ttk.Button(self.fields_frame, text="Обзор...", command=lambda: self.browse_audio(self.audio_var)).grid(
                row=row, column=2)
            row += 1

    def browse_image(self):
        filetypes = [("Изображения", "*.jpg *.jpeg *.png *.gif *.bmp"), ("Все файлы", "*.*")]
        filename = filedialog.askopenfilename(title="Выберите изображение", filetypes=filetypes)
        if filename: self.src_var.set(filename)

    def browse_audio(self, var):
        filetypes = [("Аудио", "*.mp3 *.wav *.ogg *.m4a"), ("Все файлы", "*.*")]
        filename = filedialog.askopenfilename(title="Выберите аудиофайл", filetypes=filetypes)
        if filename: var.set(filename)

    def refresh_message_listbox(self):
        self.msg_listbox.delete(0, tk.END)
        for msg in self.messages:
            title = msg.get("title", "Без заголовка")
            self.msg_listbox.insert(tk.END, title)

    def add_message(self):
        dialog = MessageDialog(self, title="Добавить сообщение")
        if dialog.result:
            self.messages.append(dialog.result)
            self.refresh_message_listbox()

    def edit_message(self):
        sel = self.msg_listbox.curselection()
        if not sel: return
        idx = sel[0]
        msg = self.messages[idx]
        dialog = MessageDialog(self, title="Изменить сообщение", msg_data=msg)
        if dialog.result:
            self.messages[idx] = dialog.result
            self.refresh_message_listbox()

    def delete_message(self):
        sel = self.msg_listbox.curselection()
        if not sel: return
        idx = sel[0]
        del self.messages[idx]
        self.refresh_message_listbox()

    def update_options_count(self):
        n = self.num_options.get()
        if len(self.options) < n:
            for _ in range(n - len(self.options)):
                self.options.append({"text": "", "image": ""})
        else:
            self.options = self.options[:n]
        self.render_options()
        self.correct_spin.config(to=n)
        if self.correct_var.get() > n: self.correct_var.set(n)

    def render_options(self):
        for w in self.options_frame.winfo_children(): w.destroy()
        for i in range(self.num_options.get()):
            if i >= len(self.options): self.options.append({"text": "", "image": ""})
            opt = self.options[i]
            f = ttk.Frame(self.options_frame)
            f.pack(fill=tk.X, pady=2)
            ttk.Label(f, text=f"Вариант {i + 1}:").pack(side=tk.LEFT)
            text_var = tk.StringVar(value=opt.get("text", ""))
            text_entry = ttk.Entry(f, textvariable=text_var, width=30)
            text_entry.pack(side=tk.LEFT, padx=5)
            img_var = tk.StringVar(value=opt.get("image", ""))
            img_entry = ttk.Entry(f, textvariable=img_var, width=30)
            img_entry.pack(side=tk.LEFT, padx=5)
            ttk.Button(f, text="Обзор...", command=lambda v=img_var: self.browse_image_for_option(v)).pack(side=tk.LEFT)
            opt["_text_var"] = text_var
            opt["_img_var"] = img_var

    def browse_image_for_option(self, var):
        filetypes = [("Изображения", "*.jpg *.jpeg *.png *.gif *.bmp"), ("Все файлы", "*.*")]
        filename = filedialog.askopenfilename(title="Выберите изображение", filetypes=filetypes)
        if filename: var.set(filename)

    def on_ok(self):
        t = self.type_var.get()
        if t in ("image", "panorama"):
            src = self.src_var.get().strip()
            if not src: messagebox.showerror("Ошибка", "Укажите путь к файлу изображения."); return
            if not os.path.exists(src): messagebox.showerror("Ошибка", "Файл не существует."); return
            audio = self.audio_var.get().strip()
            result = {"type": t, "src": src, "messages": self.messages, "audio": audio if audio else ""}
        elif t == "quiz":
            q = self.question_var.get().strip()
            if not q: messagebox.showerror("Ошибка", "Введите вопрос."); return
            opts = []
            for i in range(self.num_options.get()):
                opt_data = self.options[i]
                text = opt_data["_text_var"].get().strip()
                if not text: messagebox.showerror("Ошибка", f"Текст варианта {i + 1} не может быть пустым."); return
                img = opt_data["_img_var"].get().strip()
                opts.append({"text": text, "image": img})
            correct = self.correct_var.get() - 1
            audio = self.audio_var.get().strip()
            result = {"type": "quiz", "question": q, "options": opts, "correct": correct,
                      "audio": audio if audio else ""}
        else:
            result = None
        self.result = result
        self.destroy()


# ------------------ Диалог сообщения (без эмодзи) ------------------
class MessageDialog(tk.Toplevel):
    def __init__(self, parent, title="Сообщение", msg_data=None):
        super().__init__(parent)
        self.title(title)
        self.result = None
        self.msg_data = msg_data
        self.title_var = tk.StringVar()
        self.text_var = tk.StringVar()
        self.audio_var = tk.StringVar()
        if msg_data:
            self.title_var.set(msg_data.get("title", ""))
            self.text_var.set(msg_data.get("text", ""))
            self.audio_var.set(msg_data.get("audio", ""))
        self.create_widgets()
        self.transient(parent)
        self.grab_set()
        self.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        self.wait_window()

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(main_frame, text="Заголовок:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(main_frame, textvariable=self.title_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Label(main_frame, text="Текст (можно **жирный** и *курсив*):").grid(row=1, column=0, sticky=tk.W, pady=2)
        text_frame = ttk.Frame(main_frame)
        text_frame.grid(row=1, column=1, padx=5)
        self.text_widget = tk.Text(text_frame, width=50, height=5)
        self.text_widget.pack(side=tk.LEFT)
        scroll = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.text_widget.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_widget.config(yscrollcommand=scroll.set)
        if self.msg_data: self.text_widget.insert("1.0", self.msg_data.get("text", ""))
        ttk.Label(main_frame, text="Озвучка (опционально):").grid(row=2, column=0, sticky=tk.W, pady=2)
        audio_frame = ttk.Frame(main_frame)
        audio_frame.grid(row=2, column=1, padx=5)
        ttk.Entry(audio_frame, textvariable=self.audio_var, width=40).pack(side=tk.LEFT)
        ttk.Button(audio_frame, text="Обзор...", command=self.browse_audio).pack(side=tk.LEFT, padx=5)
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="OK", command=self.on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=self.destroy).pack(side=tk.LEFT, padx=5)

    def browse_audio(self):
        filetypes = [("Аудио", "*.mp3 *.wav *.ogg *.m4a"), ("Все файлы", "*.*")]
        filename = filedialog.askopenfilename(title="Выберите аудиофайл", filetypes=filetypes)
        if filename: self.audio_var.set(filename)

    def on_ok(self):
        title = self.title_var.get().strip()
        text = self.text_widget.get("1.0", tk.END).strip()
        audio = self.audio_var.get().strip()
        if not title and not text:
            messagebox.showerror("Ошибка", "Заголовок или текст должны быть заполнены.")
            return
        self.result = {"title": title, "text": text, "audio": audio}
        self.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = PresentationBuilder(root)
    root.mainloop()