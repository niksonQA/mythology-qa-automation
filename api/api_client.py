import logging

class APIClient:
    def __init__(self, base_url, auth_session):
        self.base_url = base_url
        self.auth_session = auth_session
    
    def log_response(self, response):
        if 'Mock' in str(type(response)):
            logging.info(f'Request/Response: Использовался Mock-объект в тесте')
            return
        
        logging.info(f'Request: {response.request.method} {response.request.url}')
        logging.info(f'Response: {response.status_code} {response.text}')

    def create_character(self, payload):
        response = self.auth_session.post(f'{self.base_url}', json=payload)
        self.log_response(response)
        return response
    
    def get_character(self, character_id):
        response = self.auth_session.get(f'{self.base_url}/{character_id}')
        self.log_response(response)
        return response
    
    def delete_character(self, character_id):
        response = self.auth_session.delete(f'{self.base_url}/{character_id}')
        self.log_response(response)
        return response
    
    def recruit_character(self, character_id):
        response = self.auth_session.post(f'{self.base_url}/{character_id}/recruit')
        self.log_response(response)
        return response
    
    def update_character(self, character_id, payload):
        response = self.auth_session.patch(f'{self.base_url}/{character_id}', json=payload)
        self.log_response(response)
        return response
    
    def get_character_rating(self, character_id):
        response = self.auth_session.get(f'{self.base_url}/{character_id}')
        self.log_response(response)
        return response

