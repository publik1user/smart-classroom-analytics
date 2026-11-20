import sqlite3, os, csv, io
from flask import Flask, request, jsonify, g
from flask_cors import CORS
DB=os.environ.get("DATABASE_URL","classroom.db")
app=Flask(__name__); CORS(app)
def db():
 if "db" not in g: g.db=sqlite3.connect(DB); g.db.row_factory=sqlite3.Row; g.db.execute("PRAGMA foreign_keys=ON")
 return g.db
@app.teardown_appcontext
def close(e):
 d=g.pop("db",None)
 if d: d.close()
def init():
 c=db(); c.executescript("""
 CREATE TABLE IF NOT EXISTS rooms(id INTEGER PRIMARY KEY AUTOINCREMENT,number TEXT UNIQUE NOT NULL,building TEXT NOT NULL,floor INTEGER NOT NULL,capacity INTEGER NOT NULL,type TEXT NOT NULL,active INTEGER DEFAULT 1);
 CREATE TABLE IF NOT EXISTS faculty(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE NOT NULL,department TEXT, email TEXT);
 CREATE TABLE IF NOT EXISTS courses(id INTEGER PRIMARY KEY AUTOINCREMENT,code TEXT UNIQUE NOT NULL,name TEXT NOT NULL,department TEXT);
 CREATE TABLE IF NOT EXISTS sections(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE NOT NULL,students INTEGER NOT NULL);
 CREATE TABLE IF NOT EXISTS sessions(id INTEGER PRIMARY KEY AUTOINCREMENT,room_id INTEGER NOT NULL REFERENCES rooms(id),faculty_id INTEGER REFERENCES faculty(id),course_id INTEGER REFERENCES courses(id),section_id INTEGER REFERENCES sections(id),day TEXT NOT NULL,start TEXT NOT NULL,end TEXT NOT NULL,students INTEGER DEFAULT 0);
 """); c.commit()
 if c.execute("SELECT COUNT(*) FROM rooms").fetchone()[0]==0: seed()
def seed():
 c=db()
 rooms=[("A101","Main Block",1,60,"Lecture"),("A102","Main Block",1,60,"Lecture"),("A103","Main Block",1,40,"Lecture"),("B201","Science Block",2,80,"Lecture"),("B202","Science Block",2,30,"Tutorial"),("B203","Science Block",2,50,"Lecture"),("C301","Engineering Block",3,120,"Seminar Hall"),("C302","Engineering Block",3,35,"Tutorial"),("LAB1","Science Block",1,40,"Lab"),("LAB2","Engineering Block",1,40,"Lab"),("A204","Main Block",2,45,"Lecture"),("B105","Science Block",1,55,"Lecture")]
 c.executemany("INSERT OR IGNORE INTO rooms(number,building,floor,capacity,type) VALUES(?,?,?,?,?)",rooms)
 fac=[("Dr. Sharma","Computer Science","sharma@college.edu"),("Dr. Patel","Mathematics","patel@college.edu"),("Prof. Iyer","Physics","iyer@college.edu"),("Dr. Khan","Chemistry","khan@college.edu"),("Prof. Nair","English","nair@college.edu"),("Dr. Reddy","Computer Science","reddy@college.edu"),("Prof. Gupta","Economics","gupta@college.edu"),("Dr. Mehta","Biology","mehta@college.edu")]
 c.executemany("INSERT OR IGNORE INTO faculty(name,department,email) VALUES(?,?,?)",fac)
 courses=[("CS101","Intro to CS","CS"),("MA101","Calculus","Maths"),("PH101","Physics I","Physics"),("CH101","Chemistry I","Chemistry"),("EN101","English","English"),("CS201","Data Structures","CS"),("EC101","Economics","Economics"),("BI101","Biology","Biology")]
 c.executemany("INSERT OR IGNORE INTO courses(code,name,department) VALUES(?,?,?)",courses)
 c.executemany("INSERT OR IGNORE INTO sections(name,students) VALUES(?,?)",[("CSE-A",55),("CSE-B",48),("ECE-A",38),("ME-A",32)])
 days=["Monday","Tuesday","Wednesday","Thursday","Friday"]; slots=[("09:00","10:00"),("10:00","11:00"),("11:00","12:00"),("14:00","15:00"),("15:00","16:00")]
 import random; random.seed(7); sessions=[]
 for i in range(42):
  sessions.append((random.randint(1,10),random.randint(1,8),random.randint(1,8),random.randint(1,4),random.choice(days),*random.choice(slots),random.randint(25,55)))
 # intentional conflicts for demo
 sessions+=[(1,1,1,1,"Monday","09:00","10:00",50),(1,2,2,2,"Monday","09:00","10:00",30),(2,1,3,3,"Tuesday","10:00","11:00",70)]
 c.executemany("INSERT INTO sessions(room_id,faculty_id,course_id,section_id,day,start,end,students) VALUES(?,?,?,?,?,?,?,?)",sessions); c.commit()
def rows(q,a=()): return [dict(r) for r in db().execute(q,a).fetchall()]
def one(q,a=()):
 r=db().execute(q,a).fetchone(); return dict(r) if r else None
def overlap(s1,e1,s2,e2): return s1<e2 and s2<e1
def find_conflicts():
 sess=rows("SELECT s.*,r.number room_number,r.capacity FROM sessions s JOIN rooms r ON r.id=s.room_id")
 out=[]
 for i,a in enumerate(sess):
  if a["students"]>a["capacity"]: out.append({"type":"Invalid Assignment - Capacity Exceeded","session_id":a["id"],"detail":f'{a["room_number"]} capacity {a["capacity"]} < {a["students"]} students', "day":a["day"]})
  for b in sess[i+1:]:
   if a["day"]!=b["day"] or not overlap(a["start"],a["end"],b["start"],b["end"]): continue
   if a["room_id"]==b["room_id"]: out.append({"type":"Double-Booked Classroom","session_ids":[a["id"],b["id"]],"detail":f'Room {a["room_number"]} booked twice', "day":a["day"]})
   if a["faculty_id"] and a["faculty_id"]==b["faculty_id"]: out.append({"type":"Faculty Conflict","session_ids":[a["id"],b["id"]],"detail":f'Faculty {a["faculty_id"]} in two classes', "day":a["day"]})
   if a["section_id"] and a["section_id"]==b["section_id"]: out.append({"type":"Section Conflict","session_ids":[a["id"],b["id"]],"detail":f'Section {a["section_id"]} in two classes', "day":a["day"]})
 return out
@app.route("/api/health")
def health(): return jsonify({"status":"ok"})
@app.route("/api/rooms",methods=["GET","POST"])
def rooms():
 if request.method=="POST":
  d=request.json or {}
  if not d.get("number") or not d.get("building") or not d.get("capacity"): return jsonify({"error":"number, building, capacity required"}),400
  if int(d["capacity"])<=0: return jsonify({"error":"capacity must be positive"}),400
  try:
   cur=db().execute("INSERT INTO rooms(number,building,floor,capacity,type,active) VALUES(?,?,?,?,?,?)",(d["number"],d["building"],int(d.get("floor",1)),int(d["capacity"]),d.get("type","Lecture"),1 if d.get("active",True) else 0)); db().commit()
  except sqlite3.IntegrityError: return jsonify({"error":"room number already exists"}),409
  return jsonify(one("SELECT * FROM rooms WHERE id=?",(cur.lastrowid,))),201
 return jsonify(rows("SELECT * FROM rooms ORDER BY building,number"))
@app.route("/api/rooms/<int:i>",methods=["GET","PUT","DELETE"])
def room(i):
 if not one("SELECT * FROM rooms WHERE id=?",(i,)): return jsonify({"error":"not found"}),404
 if request.method=="DELETE": db().execute("DELETE FROM rooms WHERE id=?",(i,)); db().commit(); return jsonify({"deleted":True})
 if request.method=="PUT":
  d=request.json or {}; db().execute("UPDATE rooms SET number=?,building=?,floor=?,capacity=?,type=?,active=? WHERE id=?",(d.get("number"),d.get("building"),int(d.get("floor",1)),int(d.get("capacity",1)),d.get("type","Lecture"),1 if d.get("active",True) else 0,i)); db().commit()
 return jsonify(one("SELECT * FROM rooms WHERE id=?",(i,)))
@app.route("/api/rooms/<int:i>/schedule")
def room_sched(i): return jsonify(rows("SELECT * FROM sessions WHERE room_id=? ORDER BY day,start",(i,)))
def crud(table,unique):
 def f():
  if request.method=="POST":
   d=request.json or {}
   cols=list(d.keys())
   try:
    cur=db().execute(f"INSERT INTO {table}({','.join(cols)}) VALUES({','.join('?'*len(cols))})",tuple(d.values())); db().commit()
   except Exception as e: return jsonify({"error":str(e)}),400
   return jsonify(one(f"SELECT * FROM {table} WHERE id=?",(cur.lastrowid,))),201
  return jsonify(rows(f"SELECT * FROM {table}"))
 return f
app.add_url_rule("/api/faculty",view_func=crud("faculty","name"),methods=["GET","POST"],endpoint="faculty")
app.add_url_rule("/api/courses",view_func=crud("courses","code"),methods=["GET","POST"],endpoint="courses")
app.add_url_rule("/api/sections",view_func=crud("sections","name"),methods=["GET","POST"],endpoint="sections")
@app.route("/api/sessions",methods=["GET","POST"])
def sessions():
 if request.method=="POST":
  d=request.json or {}
  for k in ("room_id","day","start","end"):
   if not d.get(k): return jsonify({"error":f"{k} required"}),400
  if d["end"]<=d["start"]: return jsonify({"error":"end must be after start"}),400
  room=one("SELECT * FROM rooms WHERE id=?",(d["room_id"],))
  if not room: return jsonify({"error":"room not found"}),404
  cur=db().execute("INSERT INTO sessions(room_id,faculty_id,course_id,section_id,day,start,end,students) VALUES(?,?,?,?,?,?,?,?)",(d["room_id"],d.get("faculty_id"),d.get("course_id"),d.get("section_id"),d["day"],d["start"],d["end"],int(d.get("students",0)))); db().commit()
  return jsonify(one("SELECT * FROM sessions WHERE id=?",(cur.lastrowid,))),201
 q="SELECT s.*,r.number room_number,f.name faculty_name,co.code course_code,se.name section_name FROM sessions s LEFT JOIN rooms r ON r.id=s.room_id LEFT JOIN faculty f ON f.id=s.faculty_id LEFT JOIN courses co ON co.id=s.course_id LEFT JOIN sections se ON se.id=s.section_id WHERE 1=1"; a=[]
 for k,col in [("day","s.day"),("faculty_id","s.faculty_id"),("section_id","s.section_id"),("room_id","s.room_id")]:
  if request.args.get(k): q+=f" AND {col}=?"; a.append(request.args[k])
 return jsonify(rows(q+" ORDER BY s.day,s.start",a))
@app.route("/api/sessions/<int:i>",methods=["PUT","DELETE"])
def session(i):
 if request.method=="DELETE": db().execute("DELETE FROM sessions WHERE id=?",(i,)); db().commit(); return jsonify({"deleted":True})
 d=request.json or {}; db().execute("UPDATE sessions SET room_id=?,faculty_id=?,course_id=?,section_id=?,day=?,start=?,end=?,students=? WHERE id=?",(d.get("room_id"),d.get("faculty_id"),d.get("course_id"),d.get("section_id"),d.get("day"),d.get("start"),d.get("end"),int(d.get("students",0)),i)); db().commit(); return jsonify(one("SELECT * FROM sessions WHERE id=?",(i,)))
@app.route("/api/dashboard")
def dashboard():
 day=request.args.get("day","Monday"); t=request.args.get("time","10:00")
 total=db().execute("SELECT COUNT(*) FROM rooms").fetchone()[0]; active=db().execute("SELECT COUNT(*) FROM rooms WHERE active=1").fetchone()[0]
 occ=rows("SELECT room_id FROM sessions WHERE day=? AND start<=? AND end>?",(day,t,t)); occ_ids={r["room_id"] for r in occ}
 sess=db().execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
 util=round(sess/(total*35)*100,2) if total else 0
 return jsonify({"total_classrooms":total,"active_classrooms":active,"occupied":len(occ_ids),"available":active-len(occ_ids),"utilization_percent":util,"total_sessions":sess,"conflicts":len(find_conflicts()),"day":day,"time":t})
@app.route("/api/availability")
def avail():
 day=request.args.get("day","Monday"); s=request.args.get("start","09:00"); e=request.args.get("end","10:00")
 busy={r["room_id"] for r in rows("SELECT room_id FROM sessions WHERE day=?",(day,)) if overlap(s,e,rows("SELECT start FROM sessions WHERE id=?",())[0]["start"] if False else s,s)} # placeholder replaced below
 # correct busy calc
 busy=set()
 for r in rows("SELECT room_id,start,end FROM sessions WHERE day=?",(day,)):
  if overlap(s,e,r["start"],r["end"]): busy.add(r["room_id"])
 allr=rows("SELECT * FROM rooms WHERE active=1")
 return jsonify({"occupied":[r for r in allr if r["id"] in busy],"available":[r for r in allr if r["id"] not in busy]})
@app.route("/api/conflicts")
def conflicts(): return jsonify(find_conflicts())
@app.route("/api/recommendations")
def rec():
 students=int(request.args.get("students",40)); typ=request.args.get("type","Lecture"); day=request.args.get("day","Monday"); s=request.args.get("start","09:00"); e=request.args.get("end","10:00")
 av=avail().get_json()["available"]; out=[]
 counts={r["room_id"]:r["c"] for r in rows("SELECT room_id,COUNT(*) c FROM sessions GROUP BY room_id")}
 for r in av:
  if r["capacity"]<students: continue
  score=100-abs(r["capacity"]-students)  # capacity fit
  if r["type"]==typ: score+=20
  score-=counts.get(r["id"],0)*2  # prefer less utilized
  out.append({**r,"suitability_score":round(max(0,score),1),"reason":f'Capacity fit, {"type match, " if r["type"]==typ else ""}available {day} {s}-{e}'})
 return jsonify(sorted(out,key=lambda x:-x["suitability_score"]))
@app.route("/api/analytics")
def analytics():
 by_room=rows("SELECT r.number,r.building,COUNT(s.id) sessions,ROUND(COUNT(s.id)*100.0/35,2) utilization_percent FROM rooms r LEFT JOIN sessions s ON s.room_id=r.id GROUP BY r.id ORDER BY utilization_percent DESC")
 heat=rows("SELECT day,start,COUNT(*) count FROM sessions GROUP BY day,start ORDER BY day,start")
 by_build=rows("SELECT r.building,COUNT(DISTINCT r.id) rooms,COUNT(s.id) sessions FROM rooms r LEFT JOIN sessions s ON s.room_id=r.id GROUP BY r.building")
 by_day=rows("SELECT day,COUNT(*) sessions FROM sessions GROUP BY day")
 return jsonify({"by_room":by_room,"heatmap":heat,"underutilized":[r for r in by_room if r["utilization_percent"]<20],"by_building":by_build,"by_day":by_day})
def parse_csv():
 if "file" in request.files: text=request.files["file"].read().decode()
 elif request.json and "csv" in request.json: text=request.json["csv"]
 else: text=request.get_data(as_text=True)
 return list(csv.DictReader(io.StringIO(text)))
@app.route("/api/import/rooms",methods=["POST"])
def imp_rooms():
 dry=request.args.get("dry_run")=="true" or (request.json and request.json.get("dry_run")); data=parse_csv(); errors=[]; valid=[]
 for n,r in enumerate(data,2):
  try:
   if not r.get("number") or int(r.get("capacity",0))<=0: raise ValueError("number and positive capacity required")
   valid.append(r)
  except Exception as ex: errors.append({"row":n,"error":str(ex)})
 if not dry and not errors:
  for r in valid: 
   try: db().execute("INSERT INTO rooms(number,building,floor,capacity,type) VALUES(?,?,?,?,?)",(r["number"],r.get("building","Main Block"),int(r.get("floor",1)),int(r["capacity"]),r.get("type","Lecture")))
   except: pass
  db().commit()
 return jsonify({"valid":len(valid),"errors":errors,"saved":0 if dry or errors else len(valid)})
@app.route("/api/import/timetable",methods=["POST"])
def imp_tt():
 dry=request.args.get("dry_run")=="true"; data=parse_csv(); errors=[]
 for n,r in enumerate(data,2):
  if not r.get("room_id") or not r.get("day") or not r.get("start") or not r.get("end"): errors.append({"row":n,"error":"room_id, day, start, end required"})
 if not dry and not errors:
  for r in data: db().execute("INSERT INTO sessions(room_id,faculty_id,course_id,section_id,day,start,end,students) VALUES(?,?,?,?,?,?,?,?)",(r["room_id"],r.get("faculty_id") or None,r.get("course_id") or None,r.get("section_id") or None,r["day"],r["start"],r["end"],int(r.get("students",0))))
  db().commit()
 return jsonify({"valid":len(data)-len(errors),"errors":errors,"saved":0 if dry or errors else len(data)})
@app.route("/api/seed",methods=["POST"])
def reseed():
 for t in ("sessions","rooms","faculty","courses","sections"): db().execute(f"DELETE FROM {t}")
 db().commit(); seed(); return jsonify({"seeded":True})
with app.app_context(): init()
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)),debug=True)
