from locust import HttpUser, between, task
from faker import Faker

fake = Faker()

class MythologyUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.created_ids = []
        for _ in range(2):
            payload = {
                'name': fake.first_name(),
                'role': fake.word()
            }
            
        response = self.client.post('/', json=payload)

        if response.status_code == 201:
            char_id = response.json().get('id')
            if char_id:
                self.created_ids.append(char_id)
        else:
            print(f'Ошибка создания! Статус: {response.status_code}')

    @task(3)
    def get_character(self):
        target_id = self.created_ids[0]
        self.client.get(f'/{target_id}')
    
    @task(1)
    def create_character(self):
        payload = {
            'name': fake.first_name(),
            'role': fake.word()
        }
        with self.client.post(f'/', json=payload, catch_response=True) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f'Ошибка создания! Статус: {response.status_code}')

