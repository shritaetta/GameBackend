import uuid
import random
from locust import HttpUser, task, between

class GamePulseUser(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        """
        Executed when a virtual user starts. 
        Registers a new account, logs in, and stores the JWT token for reuse.
        """
        self.username = f"user_{uuid.uuid4().hex[:8]}"
        self.password = "password123"
        self.email = f"{self.username}@example.com"
        
        # 1. Register Account
        self.client.post("/auth/register", json={
            "username": self.username,
            "email": self.email,
            "password": self.password
        })

        # 2. Login
        response = self.client.post("/auth/login", data={
            "username": self.username,
            "password": self.password
        })
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            # Store JWT token for reuse
            self.client.headers.update({"Authorization": f"Bearer {token}"})
            
        # Store created and joined matches
        self.matches = []

    @task(40)
    def view_leaderboard(self):
        self.client.get("/leaderboard")

    @task(30)
    def update_score(self):
        if self.matches:
            match_id = random.choice(self.matches)
            score_increment = random.randint(10, 100)
            self.client.post("/scores", json={
                "match_id": match_id,
                "score": score_increment
            })

    @task(15)
    def join_match(self):
        if self.matches:
            match_id = random.choice(self.matches)
            self.client.post(f"/matches/{match_id}/join")

    @task(10)
    def create_match(self):
        match_name = f"Match_{uuid.uuid4().hex[:6]}"
        response = self.client.post("/matches", json={
            "name": match_name
        })
        if response.status_code == 201:
            match_id = response.json().get("id")
            if match_id:
                self.matches.append(match_id)

    @task(5)
    def register_login(self):
        # Simulate re-authenticating (logging in again) to meet the 5% requirement
        self.client.post("/auth/login", data={
            "username": self.username,
            "password": self.password
        })
