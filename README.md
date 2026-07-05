# 🚀 Mythology QA Automation Project

Проект по автоматизации тестирования API с настроенным CI/CD пайплайном. 

## 🛠 Стек технологий
* **Язык программирования:** Python 3.10+
* **Тестовый фреймворк:** Pytest
* **Тестирование API:** Requests
* **Отчетность:** Allure Reports
* **Инфраструктура:** GitHub Actions & Telegram Bot Notifications

---

## 🏃 Запуск проекта локально

1. Клонировать репозиторий:
   ```bash
   git clone [https://github.com/твоё-имя-аккаунта/mythology-qa-automation.git](https://github.com/твоё-имя-аккаунта/mythology-qa-automation.git)
   cd mythology-qa-automation
*(Не забудь в ссылке поменять `твоё-имя-аккаунта` на свой реальный логин на GitHub).*

---

2. Установить зависимости:
pip install -r requirements.txt

3. Запустить тесты:
pytest

🤖 CI/CD Пайплайн
В проекте настроен автоматический рабочий процесс через GitHub Actions:

При каждом git push в ветку main автоматически поднимается бэкенд приложения.

Запускаются тесты с подсчетом покрытия (Coverage).

Результаты сборки отправляются в Telegram-бот в виде мгновенного отчета со ссылкой на прогон.