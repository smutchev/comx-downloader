<div align="center">

# 📚 COM-X.LIFE Downloader (Fork)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.7+-blue.svg" alt="Python 3.7+">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License MIT">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey.svg" alt="Platform">
</p>

**Форк оригинального проекта [smutchev/comx-downloader](https://github.com/smutchev/comx-downloader)**

Актуализирована логика скачивания после изменений на сайте com-x.life • Изображения берутся напрямую из `window.__DATA__` • Больше не нужен Selenium для скачивания

[Установка](#-установка) • [Использование](#-использование) • [Возможности](#-возможности) • [FAQ](#-faq)

</div>

## ✅ Решение в этом форке

**Скачивание изображений напрямую из читалки, минуя кнопку «Скачать».**

Страница `/reader/{news_id}/{chapter_id}` содержит в `window.__DATA__` полный список изображений главы:

```json
{
  "images": ["13818/381548/1699567100_0.76154200.jpg", "..."],
  "host": "img.com-x.life",
  "host_ru": "rus.com-x.life",
  "pages": 7,
  "chapter_id": 381548,
  "news_id": 13818
}
```

---

## 📖 Описание

Python-скрипт для автоматического скачивания манги с сайта **com-x.life**. Изображения скачиваются напрямую со страницы читалки и организуются в удобную структуру папок.

**Главное отличие этого форка:** скачивание больше не зависит от кнопки «Скачать» — изображения берутся напрямую из данных страницы читалки (`window.__DATA__`). Это устойчиво к изменениям интерфейса и работает быстрее.

---

## 🔧 Установка

### Требования

- Python 3.7 или выше
- Google Chrome или Mozilla Firefox
- Аккаунт на com-x.life

### Linux

```bash
git clone https://github.com/Forsash3451k/comx-downloader.git
cd comx-downloader
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Windows (можете не использовать venv на ваше усмотрение)

```bash
git clone https://github.com/Forsash3451k/comx-downloader.git
cd comx-downloader
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
```

---

## 🚀 Использование

### Базовый запуск

```bash
python main.py
```

### Первый запуск

1. **Выберите браузер** (Chrome/Firefox)
2. **Авторизуйтесь** на сайте com-x.life в открывшемся окне браузера
3. **Дождитесь автоматического сохранения cookies** — скрипт продолжит работу автоматически

> ⚠️ **Важно!** Авторизация требуется только при первом запуске. Cookies сохраняются в файл `comx_cookies.json`

### Режимы работы

**1. Поиск по названию**
```
📖 Введите URL или Название манги: One Piece
```

**2. Прямая ссылка**
```
📖 Введите URL или Название манги: https://com-x.life/12345-manga-name
```

**3. Скачивание определённых глав**
```
💡 Укажите диапазон (Enter = все): 1-10
💡 Укажите диапазон (Enter = все): 5
💡 Укажите диапазон (Enter = все): 15-
```

---

## 💡 Возможности

### Основные функции

| Функция | Описание |
|---------|----------|
| 🔍 **Поиск** | Быстрый поиск по названию с показом до 30 результатов |
| 📥 **Загрузка** | Скачивание изображений напрямую из данных читалки |
| 📊 **Прогресс** | Показ статуса загрузки каждой главы в реальном времени |
| 🎯 **Диапазоны** | Скачивание отдельных глав или диапазонов (например, 1-50) |
| 💾 **Кэш** | Пропуск уже скачанных глав |
| 🔄 **Возобновление** | Продолжение прерванной загрузки |

### Структура папок

```
Manga/
└── Название Манги/
    ├── Vol. 1 Ch. 1 - Название главы/
    │   ├── 001.jpg
    │   ├── 002.jpg
    │   └── ...
    ├── Vol. 1 Ch. 2 - Название главы/
    │   └── ...
    └── ...
```

---

## 📸 Скриншоты

<div align="center">

### Выбор браузера и поиск
<img width="627" alt="Меню выбора" src="https://github.com/user-attachments/assets/861d495a-50e8-4211-b37d-64c6da367a88" />

### Результаты поиска
<img width="1700" alt="Результаты" src="https://github.com/user-attachments/assets/9f54ec20-5474-4996-a44e-81b9060058ec" />

### Процесс загрузки
<img width="1027" alt="Загрузка" src="https://github.com/user-attachments/assets/bab0c9d3-a878-40c1-806e-dc8290730a70" />

### Завершение работы
<img width="745" alt="Завершение" src="https://github.com/user-attachments/assets/d197f184-4c55-4c30-8274-430e14e0ecad" />

</div>

---

## ❓ FAQ

<details>
<summary><b>Ошибка: "Не удалось авторизоваться"</b></summary>

- Убедитесь, что у вас есть аккаунт на com-x.life
- Проверьте, что браузер установлен корректно
- Удалите файл `comx_cookies.json` и попробуйте снова
</details>

<details>
<summary><b>Ошибка: "Cloudflare или бан"</b></summary>

- Удалите файл `comx_cookies.json`
- Перезапустите скрипт и авторизуйтесь заново
- Подождите несколько минут, если вас временно заблокировали
</details>

<details>
<summary><b>Как скачать только новые главы?</b></summary>

Скрипт автоматически пропускает уже скачанные главы. Просто запустите его снова с той же мангой.
</details>

<details>
<summary><b>Поддерживаются ли другие браузеры?</b></summary>

Сейчас поддерживаются только Chrome и Firefox.
</details>

<details>
<summary><b>Есть ли у скрипта GUI?</b></summary>

Нет, скрипт работает в терминале. GUI используется только на этапе первой авторизации на сайт.
</details>

<details>
<summary><b>Ошибка: "API не вернул ссылку" / "Скачивание доступно через кнопку Скачать"</b></summary>

Это ошибка **оригинального** скрипта. В этом форке она исправлена — скачивание идёт не через API, а через парсинг `window.__DATA__` из страницы читалки. Убедитесь, что используете код именно этого форка.
</details>

<details>
<summary><b>Почему используется зеркало rus.com-x.life?</b></summary>

Это официальное зеркало, которое сам сайт выбирает для пользователей из РФ (поле `host_ru` в `window.__DATA__`). Скрипт использует его как fallback: если `img.com-x.life` не отвечает, автоматически пробуется `rus.com-x.life`.
</details>

---

## 🛠️ Технические детали

### Зависимости

- `requests` — HTTP-запросы
- `selenium` — автоматизация браузера
- `beautifulsoup4` — парсинг HTML
- `inquirer` — интерактивное меню
- `webdriver-manager` — автоматическая установка драйверов
- `img2pdf` + `Pillow` — упаковка в PDF, конвертация WebP
- `cloudscraper` — обход Cloudflare

---

## 📝 Лицензия

Этот проект распространяется под лицензией MIT. См. [LICENSE](LICENSE) для деталей.

---

## 👨‍💻 Автор

Создано [smutchev](https://github.com/smutchev)

Форк с фиксом [Forsash3451k](https://github.com/Forsash3451k)

**Примечание:** Тут содержится вайбкодинг, don't blame me :D

---

## ⭐ Поддержка

Если проект оказался полезным, поставьте звёздочку! Это мотивирует на дальнейшую разработку.

<div align="center">

**[⬆ Наверх](#-com-xlife-downloader-fork)**

</div>