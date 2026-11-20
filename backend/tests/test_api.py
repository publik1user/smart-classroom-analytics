import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__),".."))
os.environ["DATABASE_URL"]="test.db"
import app as m
import pytest
@pytest.fixture()
def client():
 if os.path.exists("test.db"): os.remove("test.db")
 with m.app.app_context(): m.init()
 yield m.app.test_client()
 if os.path.exists("test.db"): os.remove("test.db")
def test_health(client): assert client.get("/api/health").json["status"]=="ok"
def test_rooms_seed(client): assert len(client.get("/api/rooms").json)>=10
def test_create_room(client):
 r=client.post("/api/rooms",json={"number":"Z999","building":"Test","floor":1,"capacity":25,"type":"Lecture"}); assert r.status_code==201
 assert client.post("/api/rooms",json={"number":"Z999","building":"Test","floor":1,"capacity":25}).status_code==409
 assert client.post("/api/rooms",json={"number":"Z998","building":"T","capacity":-1}).status_code==400
def test_dashboard(client):
 d=client.get("/api/dashboard").json; assert d["total_classrooms"]>=10 and "utilization_percent" in d
def test_conflicts(client): assert len(client.get("/api/conflicts").json)>=1
def test_recommendations(client):
 r=client.get("/api/recommendations?students=30&type=Lecture").json; assert r and "suitability_score" in r[0]
def test_availability(client):
 d=client.get("/api/availability?day=Monday&start=09:00&end=10:00").json; assert "available" in d and "occupied" in d
def test_analytics(client):
 d=client.get("/api/analytics").json; assert d["by_room"] and d["heatmap"]
def test_session_validation(client): assert client.post("/api/sessions",json={"room_id":1,"day":"Monday","start":"10:00","end":"09:00"}).status_code==400
def test_csv_import_validation(client):
 r=client.post("/api/import/rooms?dry_run=true",json={"csv":"number,building,floor,capacity,type\nX1,Main,1,0,Lecture\n"}); assert r.json["errors"]
