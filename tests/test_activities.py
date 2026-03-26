import pytest


class TestGetActivities:
    """Tests for the GET /activities endpoint"""
    
    def test_get_activities_returns_200(self, client):
        """Test that GET /activities returns status code 200"""
        response = client.get("/activities")
        assert response.status_code == 200
    
    def test_get_activities_returns_dict(self, client):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)
    
    def test_get_activities_contains_expected_activities(self, client):
        """Test that response contains expected activities"""
        response = client.get("/activities")
        activities = response.json()
        
        expected = ["Chess Club", "Programming Class", "Gym Class", "Basketball Team", 
                   "Volleyball Club", "Art Studio", "Music Ensemble", "Debate Team", "Science Club"]
        for activity in expected:
            assert activity in activities
    
    def test_get_activities_structure(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignup:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_returns_200(self, client):
        """Test that signup returns status code 200 on success"""
        response = client.post("/activities/Chess Club/signup?email=test@mergington.edu")
        assert response.status_code == 200
    
    def test_signup_adds_participant(self, client):
        """Test that signup adds participant to activity"""
        email = "newstudent@mergington.edu"
        client.post(f"/activities/Chess Club/signup?email={email}")
        
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Chess Club"]["participants"]
    
    def test_signup_returns_success_message(self, client):
        """Test that signup returns success message"""
        email = "newstudent@mergington.edu"
        response = client.post(f"/activities/Chess Club/signup?email={email}")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Chess Club" in data["message"]
    
    def test_signup_activity_not_found(self, client):
        """Test that signup returns 404 for non-existent activity"""
        response = client.post("/activities/NonExistent/signup?email=test@mergington.edu")
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_signup_duplicate_registration(self, client):
        """Test that duplicate signup returns 400"""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.post(f"/activities/Chess Club/signup?email={email}")
        
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_multiple_activities(self, client):
        """Test that student can signup for multiple activities"""
        email = "versatile@mergington.edu"
        
        response1 = client.post(f"/activities/Chess Club/signup?email={email}")
        response2 = client.post(f"/activities/Basketball Team/signup?email={email}")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        activities = client.get("/activities").json()
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Basketball Team"]["participants"]


class TestUnregister:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_returns_200(self, client):
        """Test that unregister returns status code 200 on success"""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.delete(f"/activities/Chess Club/unregister?email={email}")
        assert response.status_code == 200
    
    def test_unregister_removes_participant(self, client):
        """Test that unregister removes participant from activity"""
        email = "michael@mergington.edu"  # Already in Chess Club
        client.delete(f"/activities/Chess Club/unregister?email={email}")
        
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities["Chess Club"]["participants"]
    
    def test_unregister_returns_success_message(self, client):
        """Test that unregister returns success message"""
        email = "michael@mergington.edu"
        response = client.delete(f"/activities/Chess Club/unregister?email={email}")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Chess Club" in data["message"]
    
    def test_unregister_activity_not_found(self, client):
        """Test that unregister returns 404 for non-existent activity"""
        response = client.delete("/activities/NonExistent/unregister?email=test@mergington.edu")
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_unregister_not_registered(self, client):
        """Test that unregister returns 400 for non-registered student"""
        email = "notregistered@mergington.edu"
        response = client.delete(f"/activities/Chess Club/unregister?email={email}")
        
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]
    
    def test_unregister_then_signup_again(self, client):
        """Test that student can signup after unregistering"""
        email = "flexible@mergington.edu"
        activity = "Chess Club"
        
        # Sign up
        response1 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response1.status_code == 200
        
        # Unregister
        response2 = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response2.status_code == 200
        
        # Sign up again
        response3 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response3.status_code == 200


class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_signup_unregister_cycle(self, client):
        """Test complete signup and unregister cycle"""
        email = "cycle@mergington.edu"
        activity = "Programming Class"
        
        # Get initial participant count
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity]["participants"])
        
        # Sign up
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Verify added
        mid_response = client.get("/activities")
        mid_count = len(mid_response.json()[activity]["participants"])
        assert mid_count == initial_count + 1
        
        # Unregister
        unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert unregister_response.status_code == 200
        
        # Verify removed
        final_response = client.get("/activities")
        final_count = len(final_response.json()[activity]["participants"])
        assert final_count == initial_count
    
    def test_capacity_tracking(self, client):
        """Test that participant count is accurate"""
        activity = "Basketball Team"
        
        # Get initial state
        response = client.get("/activities")
        activity_data = response.json()[activity]
        initial_count = len(activity_data["participants"])
        max_capacity = activity_data["max_participants"]
        
        # Verify participants don't exceed capacity
        assert initial_count <= max_capacity
        
        # Signup and verify count increases
        email = "ballplayer@mergington.edu"
        client.post(f"/activities/{activity}/signup?email={email}")
        
        response = client.get("/activities")
        new_count = len(response.json()[activity]["participants"])
        assert new_count == initial_count + 1
