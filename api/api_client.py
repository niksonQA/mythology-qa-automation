class APIClient:
    def __init__(self, base_url, auth_session):
        self.base_url = base_url
        self.auth_session = auth_session

    def create_character(self, payload):
        return self.auth_session.post(f'{self.base_url}', json=payload)
    
    def get_character(self, character_id):
        return self.auth_session.get(f'{self.base_url}/{character_id}')
    
    def delete_character(self, character_id):
        return self.auth_session.delete(f'{self.base_url}/{character_id}')
    
    def recruit_character(self, character_id):
        return self.auth_session.post(f'{self.base_url}/{character_id}/recruit')
    
    def update_character(self, character_id, payload):
        return self.auth_session.patch(f'{self.base_url}/{character_id}', json=payload)
    
    def get_character_rating(self, character_id):
        return self.auth_session.get(f'{self.base_url}/{character_id}')

