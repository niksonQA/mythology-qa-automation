import allure
import pytest
import requests

from app.sandbox import CharacterUpdate, CharacterRating
from conftest import ExtensionCharacter
from api.api_client import APIClient


# ======================================================================
# ТЕСТ №1: Отправка запроса на создание нескольких сущностей.
# ======================================================================
@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.parametrize('payload_type', [
    'boundary',
    'high boundary'
],
ids=[
    'create valid_1 character',
    'create valid_2 character'
])

@allure.title('Отправка POST-запроса на создание нескольких сущностей (позитив)')
def test_create_valid_character(connection_db, payload_type, fake, api_client):
    with allure.step('Подготовка данных для осуществления теста и отправки запроса'):
        if payload_type == 'boundary':
            payload = {'name': fake.first_name(), 'role': fake.word(), 'age': 18}
        else:
            payload = {'name': fake.first_name(), 'role': fake.word(), 'age': 19}
 
    with allure.step('Подготовка: Отправка запроса, проверка статус-кода, получение id'):
        response = api_client.create_character(payload=payload)
        assert response.status_code == 201
        data_id = response.json().get('id')

    with allure.step('Отправка SQL-запроса на нахождение персонажа в БД'):
        connection_db.execute('SELECT characters.name, characters.role FROM characters WHERE characters.id = ?', (data_id,))
        db_row = connection_db.fetchone()

    with allure.step('Проверка нахождения созданного персонажа в БД'):
        assert db_row['name'] == payload['name']
        assert db_row['role'] == payload['role']

    with allure.step('Проверка соответствия условиям контракта JSON-схемы'):
        ExtensionCharacter.model_validate(response.json())
    
    with allure.step('Удаление созданного персонажа из базы данных'):
        api_client.delete_character(character_id=data_id)

@pytest.mark.negative
@pytest.mark.parametrize('payload_type, expected_status', [
    ('low boundary', 400),
    ('empty', 422)
],
ids=[
    'create inalid character',
    'create empty character'
])

@allure.title('Отправка POST-запроса на создание нескольких сущностей с некорректным возрастом (негатив)')
def test_create_invalid_character(payload_type, fake, api_client, expected_status):
    with allure.step('Подготовка данных для осуществления теста'):
        if payload_type == 'low boundary':
            payload = {'name': fake.first_name(), 'role': fake.word(), 'age': 17}
        else:
            payload = {'name': '', 'role': '', 'age': ''}
 
    with allure.step('Отправка запроса'):
        response = api_client.create_character(payload=payload)
    
    with allure.step('Проверка обработки 422 и 400 статус-кода'):
        assert response.status_code == expected_status

@pytest.mark.negative
@allure.title("Отправка запроса без обязательного поля 'role'. ")
def test_create_character_without_role(fake, api_client):
    with allure.step('Отправка POST-запроса'):
        payload = {'name': fake.first_name()}
        response = api_client.create_character(payload=payload)

    with allure.step('Проверка обработки 422 статус-кода'):
        assert response.status_code == 422

@pytest.mark.negative
@allure.title("Отправка запроса на создание персонажа с лишним ключом 'desc' ")
def test_create_character_invalid_extra_keys(fake, api_client):
    with allure.step('Отправка POST-запроса, проверка статус-кода'):
        payload = {'name': fake.first_name(), 'role': fake.word(), 'desc': fake.sentence()}
        response = api_client.create_character(payload=payload)
    
    with allure.step('Проверка обработки 422 статус-кода'):
        assert response.status_code == 422

# ======================================================================
# ТЕСТ №2: Отправка запроса на просмотр содержимого в базе данных.
# ======================================================================
@pytest.mark.smoke
@pytest.mark.regression
@allure.title('Создание персонажа и проверка нахождения в БД')
def test_found_character(connection_db, create_test_character, api_client):
    with allure.step('Фикстура: Создание персонажа'):
        test_character = create_test_character.json()
        character_id = test_character.get('id')
        expected_name = test_character.get('name')
        expected_role = test_character.get('role')
        
    with allure.step('Подготовка: Отправка запроса, проверка статус-кода'):
        response2 = api_client.get_character(character_id=character_id)
        assert response2.status_code == 200

    with allure.step('Осуществление выборки необходимых данных из БД'):
        connection_db.execute('SELECT name, role FROM characters WHERE id = ?', (character_id,))
        db_row = connection_db.fetchone()

    with allure.step('Проверка нахождения персонажа в БД'):
        assert db_row is not None, f'Персонаж с ID {character_id} - не найден в базе данных!'
        assert db_row['name'] == expected_name
        assert db_row['role'] == expected_role

@pytest.mark.negative
@allure.title('Проверка обработки 404 ошибки при просмотре списка персонажей (негатив)')
def test_found_nonexistent_character(api_client):
    with allure.step('Отправка запроса на просмотр несуществующего персонажа'):
        response = api_client.get_character(character_id=9999999)

    with allure.step('Проверка обработки 404 статус-кода'):
        assert response.status_code == 404

# ======================================================================
# ТЕСТ №3: Отправка запроса на удаление данных.
# ======================================================================
@pytest.mark.smoke
@pytest.mark.regression
@allure.title('Проверка корректности удаления персонажа')
def test_delete_character(connection_db, fake, api_client):
    with allure.step('Подготовка данных'):
        fake_name = fake.first_name()
        fake_role = fake.word()

    with allure.step('Отправка запроса на создание персонажа'):
        payload = {'name': fake_name, 'role': fake_role, 'age': 18}
        response1 = api_client.create_character(payload=payload)
        assert response1.status_code == 201
        character_id = response1.json().get('id')

    with allure.step('Отправка запроса на удаление персонажа'):
        api_client.delete_character(character_id=character_id)

    with allure.step('SQL-запрос на выборку данных'):
        connection_db.execute('SELECT name, role FROM characters WHERE id = ?', (character_id,))
        db_row = connection_db.fetchone()

    with allure.step('Проверка отсутствия созданного персонажа в БД'):
        assert db_row is None

@pytest.mark.negative
@allure.title('Проверка обработки 404 ошибки при удалении несуществующего персонажа (негатив)')
def test_delete_nonexistent_character(api_client):
    with allure.step('Отправка запроса на удаление несуществующего'):
        response = api_client.delete_character(character_id=9999)

    with allure.step('Проверка обработки 404 статус-кода'):
        assert response.status_code == 404

# ======================================================================
# ТЕСТЫ №4: Отправка запроса для рекрутинга персонажа.
# ======================================================================
@pytest.mark.smoke
@pytest.mark.regression
@allure.title('Проверка рекрутинга персонажа (позитив)')
def test_recruit_character_valid(connection_db, create_test_character, api_client):
    with allure.step('Фикстура: создание и подготовка тестовых данных'):
        test_character = create_test_character.json()
        character_id = test_character.get('id')

    with allure.step('Выполнение операции рекрутинга персонажа'):
        response2 = api_client.recruit_character(character_id=character_id)
        assert response2.status_code == 200
        data = response2.json()

    with allure.step('Отправка SQL-запроса на выборку'):
        connection_db.execute('SELECT name, role FROM characters WHERE id = ?', (character_id,))
        db_row = connection_db.fetchone()

    with allure.step('Проверка нахождения персонажа в БД и присвоение статуса'):
        assert db_row['name'] == test_character.get('name')
        assert db_row['role'] == test_character.get('role')
        assert data['status'] == 'recruited'
    
@pytest.mark.negative
@allure.title('Проверка рекрутинга несуществующего персонажа (негатив)')
def test_recruit_character_invalid(api_client):
    with allure.step('Отправка запроса на рекрутинг с несуществующим ID'):
        response = api_client.recruit_character(character_id=99999)

    with allure.step('Проверка возврата 404 статус-кода'):
        assert response.status_code == 404

@pytest.mark.negative
@allure.title('Проверка передачи некорректного типа данных (негатив)')
def test_recruit_character_invalid_type(api_client):
    with allure.step('Отправка запроса на рекрутинг со строкой вместо ID'):
        response = api_client.recruit_character(character_id='mike_angel')

    with allure.step('Проверка возврата 422 статус-кода'):
        assert response.status_code == 422

# ======================================================================
# ТЕСТЫ №5: Отправка запроса для изменения данных о персонаже.
# ======================================================================
@pytest.mark.smoke
@pytest.mark.regression
@allure.title('Проверка изменения данных у существующего персонажа (позитив)')
def test_update_character_valid(connection_db, create_test_character, api_client):
    with allure.step('Фикстура: создание тестовых данных'):
        test_character = create_test_character.json()
        data_id = test_character.get('id')

    with allure.step('Отправка SQL-запроса для проверки нахождения в базе'):
        connection_db.execute('SELECT name, role FROM characters WHERE id = ?', (data_id,))
        db_row_1 = connection_db.fetchone()

    with allure.step('Проверка нахождения персонажа в БД, а также соответствие JSON-схемы'):
        assert db_row_1['name'] == test_character.get('name')
        assert db_row_1['role'] == test_character.get('role')
        ExtensionCharacter.model_validate(test_character)

    with allure.step('Подготовка: отправка запроса на изменение данных у существующего персонажа'):
        new_role = 'Head of QA'
        payload = {'role': new_role}
        response2 = api_client.update_character(character_id=data_id, payload=payload)
        assert response2.status_code == 200

    with allure.step('Отправка SQL-запроса для убеждения в изменении роли'):
        connection_db.execute('SELECT name, role FROM characters WHERE id = ?', (data_id,))
        db_row_2 = connection_db.fetchone()

    with allure.step('Проверка изменения роли, а также соответствия JSON-схемы'):
        assert db_row_2['role'] == new_role
        CharacterUpdate.model_validate(response2.json())

@pytest.mark.negative
@allure.title('Проверка обновления данных у несуществующего персонажа (негатив)')
def test_update_character_invalid(fake, api_client):
    with allure.step('Генерация фейкового имени'):
        generate_name = fake.first_name()
        payload = {'name': generate_name}

    with allure.step('Отправка запроса на обновление данных'):
        response = api_client.update_character(character_id=9999, payload=payload)

    with allure.step('Проверка возврата 404 статус-кода'):
        assert response.status_code == 404

@pytest.mark.negative
@allure.title('Проверка обновления данных при передачи некорректного типа данных (негатив)')
def test_update_character_invalid_type(fake, api_client):
    with allure.step('Генерация фейковой роли'):
        generate_role = fake.word()
        payload = {'role': generate_role}

    with allure.step('Отправка запроса на обновление данных'):
        response = api_client.update_character(character_id=None, payload=payload)

    with allure.step('Проверка возврата 422 статус-кода'):
        assert response.status_code == 422

@pytest.mark.negative
@allure.title('Проверка обновления данных при нарушении контракта (негатив)')
def test_update_character_invalid_schema(create_test_character, api_client):
    with allure.step('Создание невалидных тестовых данных'):
        invalid_payload = {
            'name': {'first_name': 'Ivan', 'last_name': 'Ivanov'}
        }

    with allure.step('Создание тестового персонажа и отправка запроса на обновление данных'):
        character_id = create_test_character.json().get('id')

    with allure.step('Отправка запроса на частичное обновление данных'):
        response = api_client.update_character(character_id=character_id, payload=invalid_payload)
        assert response.status_code == 422

    with allure.step('Проверка соответствия контракта'):
        assert 'msg' in response.json()['detail'][0]

# ======================================================================
# ТЕСТЫ №6: Отправка запроса для просмотра рейтинга.
# ======================================================================
@pytest.mark.smoke
@pytest.mark.regression
@allure.title('Проверка получения рейтинга персонажа (позитив)')
def test_character_rating(create_test_character, mocker, api_client):
    with allure.step('Подготовка данных'):
        mock_response = mocker.Mock()
        test_character = create_test_character.json()
        test_id = test_character.get('id')
        payload = {
            "character_id": 42,
            "global_rating": 95.8,
            "rank": "S-Tier",
            "status": "Calculated by Mock Service"
        }

    with allure.step('Создание мока'):
        mock_response.status_code = 200
        mock_response.json.return_value=payload
        mocker.patch('requests.Session.get', return_value=mock_response)

    with allure.step('Отправка запроса и проверка возвращения 200 статус-кода'):
        result = api_client.get_character_rating(character_id=test_id)
        assert result.status_code == 200
        result_json = result.json()

    with allure.step('Проверка соответвия тела JSON-схеме'):
        validated_data = CharacterRating.model_validate(result_json)

        assert validated_data.character_id == 42
        assert validated_data.global_rating == 95.8
        assert validated_data.rank == 'S-Tier'
        assert validated_data.status == "Calculated by Mock Service"

@pytest.mark.negative
@allure.title('Проверка получения рейтинга несуществующего персонажа (негатив)')
def test_character_rating_not_found(mocker, api_client):
    with allure.step('Подготовка данных'):
        mock_response = mocker.Mock()
        invalid_id = 9999
        payload = {
            "detail": "Character not found"
        }   

    with allure.step('Создание мока'):
        mock_response.status_code = 404
        mock_response.json.return_value=payload
        mocker.patch('requests.Session.get', return_value=mock_response)

    with allure.step('Отправка запроса и проверка возвращения 404 статус-кода'):
        result = api_client.get_character_rating(character_id=invalid_id)
        assert result.status_code == 404
        result_json = result.json()

    with allure.step('Проверка текста ошибки'):
        assert 'Character not found' in result_json['detail']

@pytest.mark.negative
@allure.title('Проверка получения рейтинга персонажа при internal error (негатив)')
def test_character_rating_server_error(mocker, api_client):
    with allure.step('Подготовка данных'):
        mock_response = mocker.Mock()
        invalid_id = 9999
        payload = {
            "detail": "Не удалось получить ответ от внешнего сервиса рейтингов."
        }  

    with allure.step('Создание мока'):
        mock_response.status_code = 500
        mock_response.json.return_value=payload
        mocker.patch('requests.Session.get', return_value=mock_response)

    with allure.step('Отправка запроса и проверка возвращения 500 статус-кода'):
        result = api_client.get_character_rating(character_id=invalid_id)
        assert result.status_code == 500
        result_json = result.json()

    with allure.step('Проверка текста ошибки'):
        assert "Не удалось получить ответ от внешнего сервиса рейтингов." in result_json['detail']
