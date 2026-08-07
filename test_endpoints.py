import httpx
import asyncio

async def test():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # signup
        r1 = await client.post("/auth/signup", json={"username": "testuser1234", "email": "test4@test.com", "password": "TestPassword123"})
        print("Signup:", r1.status_code, r1.json())
        
        # signin
        r2 = await client.post("/auth/signin", json={"username": "testuser1234", "password": "TestPassword123"})
        print("Signin:", r2.status_code, r2.json())
        
        if r2.status_code == 200:
            token = r2.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # create ticket
            r3 = await client.post("/tickets", json={"title": "Mouse not working", "description": "My wireless mouse is not connecting", "category": "Hardware", "priority": "Low"}, headers=headers)
            print("Create Ticket:", r3.status_code, r3.json())
            
            if r3.status_code in (200, 201):
                ticket_id = r3.json()["ticket_id"]
                
                # suggest resolutions
                r4 = await client.post(f"/tickets/{ticket_id}/suggest", headers=headers)
                print("Suggest:", r4.status_code, r4.json())

asyncio.run(test())
