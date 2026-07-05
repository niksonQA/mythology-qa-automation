import sqlite3

import allure
import pytest
import requests
from faker import Faker

from app.sandbox import Character


# Классы для проверки контракта
class ExtensionCharacter(Character):
    id: int
    
# Фикстура в которой находится базовый url-адрес.
@pytest.fixture
def base_url():
    return 'http://127.0.0.1:8080/mythology'

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

@pytest.fixture
def auth_session(base_url):
    session = requests.Session()
    response = requests.post(f'{base_url}/login', json={'username': 'admin', 'password': 'password123'})
    assert response.status_code == 200, 'Не удалось авторизоваться для тестов'

    token = response.json().get('access_token')
    session.headers.update({'Authorization': f'Bearer {token}'})
    yield session
    session.close()
    
@pytest.fixture
def create_test_character(base_url, fake, auth_session):
    with allure.step('Фикстура: Создание тестового персонажа'):
        generate_name = fake.first_name()
        generate_role = fake.word()
        response = auth_session.post(f'{base_url}', json={'name': generate_name, 'role': generate_role})
        data_id = response.json().get('id')
    yield response
    with allure.step('Фикстура: Авто-удаление тестового персонажа'):
        if data_id:
            auth_session.delete(f'{base_url}/{data_id}')
