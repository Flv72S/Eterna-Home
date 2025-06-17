from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("\n--- ROUTES REGISTRATE ---")
for route in app.routes:
    print(f"{route.path} -> {route.name}")

print("\n--- TEST /api/v1/auth/register ---")
response = client.post("/api/v1/auth/register", json={"email": "test@example.com", "password": "Test123!@#", "full_name": "Test User"})
print(f"Status code: {response.status_code}")
print(f"Response: {response.text}") 