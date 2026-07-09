import sqlite3

import allure
import pytest
import requests
from faker import Faker

from app.sandbox import Character
from api.api_client import APIClient


# Классы для проверки контракта
class ExtensionCharacter(Character):
    id: int
    
# Фикстура в которой находится базовый url-адрес.
@pytest.fixture
def base_url():
    return "http://127.0.0.1:8080/mythology"

# Фикстура осуществляющая подключение/отключение от БД.
@pytest.fixture
def connection_db():
    connection = sqlite3.connect('mythology.db')
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    yield cursor
    connection.close()

# Фикстура для реализации библиотеки Faker() в тестах.
@pytest.fixture
def fake():
    return Faker()

# Фикстура автоматически подставляющая заголовок Authorization, со свежим токеном.
@pytest.fixture
def auth_session(base_url):
    session = requests.Session()
    response = requests.post(f'{base_url}/login', json={'username': 'admin', 'password': 'password123'})
    assert response.status_code == 200, 'Не удалось авторизоваться для тестов'

    token = response.json().get('access_token')
    session.headers.update({'Authorization': f'Bearer {token}'})
    yield session
    session.close()

# Фикстура для быстрого создания персонажа.
@pytest.fixture
def create_test_character(fake, api_client):
    with allure.step('Фикстура: Создание тестового персонажа'):
        generate_name = fake.first_name()
        generate_role = fake.word()
        payload = {'name': generate_name, 'role': generate_role, 'age': 18}
        response = api_client.create_character(payload=payload)
        data_id = response.json().get('id')
    yield response
    with allure.step('Фикстура: Авто-удаление тестового персонажа'):
        if data_id:
            api_client.delete_character(character_id=data_id)

# Фикстура инициализирующая и возвращающая клиент для отправки запросов.
@pytest.fixture
def api_client(base_url, auth_session):
    return APIClient(base_url=base_url, auth_session=auth_session)
