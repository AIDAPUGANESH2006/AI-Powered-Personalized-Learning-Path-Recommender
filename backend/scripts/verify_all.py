"""Comprehensive end-to-end verification script for PathWise AI."""
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_pipeline():
    print("=" * 60, flush=True)
    print("PATHWISE AI - COMPREHENSIVE PIPELINE VERIFICATION", flush=True)
    print("=" * 60, flush=True)

    # 1. Health check
    print("Running 1. Health Check...", flush=True)
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print(f"1. Health Check OK: {res.json()}", flush=True)

    # 2. Catalog endpoints
    print("Running 2. Catalog...", flush=True)
    res = client.get("/api/catalog/skills")
    assert res.status_code == 200, f"Skills catalog failed: {res.text}"
    skills = res.json()
    print(f"2. Catalog Skills OK: {len(skills)} skills loaded", flush=True)

    res = client.get("/api/catalog/careers")
    assert res.status_code == 200, f"Careers catalog failed: {res.text}"
    careers = res.json()
    print(f"   Catalog Careers OK: {len(careers)} career roles loaded", flush=True)

    # 3. Authentication - Login with seeded user
    print("Running 3. Auth Login...", flush=True)
    res = client.post(
        "/api/auth/login",
        data={"username": "ganeshaidapu@gmail.com", "password": "password123"},
    )
    assert res.status_code == 200, f"Login failed: {res.text}"
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("3. Auth Login OK: Token generated successfully", flush=True)

    # 4. Profile retrieval
    print("Running 4. Profile retrieval...", flush=True)
    res = client.get("/api/profile", headers=headers)
    assert res.status_code == 200, f"Get profile failed: {res.text}"
    profile = res.json()
    print(f"4. Profile OK: Role={profile['target_career_role_id']}, Skills count={len(profile['skills'])}", flush=True)

    # 5. Skill Gap Calculation
    print("Running 5. Skill Gap...", flush=True)
    res = client.get("/api/recommendations/skill-gap?role_id=ai_ml_engineer", headers=headers)
    assert res.status_code == 200, f"Skill gap failed: {res.text}"
    gap_data = res.json()
    print(f"5. Skill Gap OK: Career Readiness = {gap_data['career_readiness_pct']}%, Total Gaps = {len(gap_data['gaps'])}", flush=True)

    # 6. Recommendations generation with explanations
    print("Running 6. Recommendations...", flush=True)
    res = client.post("/api/recommendations/generate?role_id=ai_ml_engineer&with_explanations=true&top_n=5", headers=headers)
    assert res.status_code == 200, f"Recommendations failed: {res.text}"
    recs = res.json()
    print(f"6. Recommendations OK: Generated {len(recs)} items", flush=True)
    if recs:
        print(f"   Top recommendation: '{recs[0]['title']}' (Score: {recs[0]['total_score']})", flush=True)
        print(f"   Explanation: {recs[0]['explanation'][:100]}...", flush=True)

    # 7. Roadmap generation
    print("Running 7. Roadmap generation...", flush=True)
    res = client.post("/api/roadmap", json={"role_id": "ai_ml_engineer", "pacing_mode": "balanced"}, headers=headers)
    assert res.status_code in [200, 201], f"Roadmap generation failed: {res.text}"
    roadmap = res.json()
    print(f"7. Roadmap OK: Total weeks = {roadmap['total_weeks']}, Items = {len(roadmap['items'])}", flush=True)

    # 8. Pacing adjustment
    print("Running 8. Pacing adjustment...", flush=True)
    res = client.patch("/api/roadmap/pacing", json={"pacing_mode": "fast_track"}, headers=headers)
    assert res.status_code == 200, f"Pacing adjustment failed: {res.text}"
    updated_roadmap = res.json()
    print(f"8. Pacing Adjustment OK: New total weeks = {updated_roadmap['total_weeks']}", flush=True)

    # 9. Free-text Profile Extraction
    print("Running 9. Profile extraction...", flush=True)
    res = client.post(
        "/api/recommendations/profile/analyze",
        json={"text": "I am a 3rd year CSE student, know Python and Java, want to become an AI engineer in 8 months"},
    )
    assert res.status_code == 200, f"Profile extraction failed: {res.text}"
    extracted = res.json()
    print(f"9. Profile Extraction OK: Target={extracted['target_career_role']}, Skills={[s['name'] for s in extracted['skills']]}", flush=True)

    # 10. AI Tutor Chat
    print("Running 10. AI Tutor Chat...", flush=True)
    res = client.post(
        "/api/chat",
        json={"message": "Why do I need statistics for AI?", "history": []},
        headers=headers,
    )
    assert res.status_code == 200, f"Tutor chat failed: {res.text}"
    reply = res.json()["reply"]
    print(f"10. AI Tutor Chat OK: Reply received ({len(reply)} chars)", flush=True)

    print("=" * 60, flush=True)
    print("ALL 10 VERIFICATION TESTS PASSED SUCCESSFULLY!", flush=True)
    print("=" * 60, flush=True)

if __name__ == "__main__":
    test_full_pipeline()
