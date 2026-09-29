"""Create realistic sample data for a Nigerian university (all names and numbers are fake).

    python demo/seed_data.py
"""

import csv
import json
import random
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = HERE / "sandbox" / "university_data"
MARKER = ".uniguard-demo-sandbox"

FIRST = ["Adebayo", "Chinedu", "Aisha", "Musa", "Ngozi", "Emeka", "Fatima", "Tunde", "Ibrahim", "Blessing",
         "Oluwaseun", "Zainab", "Chiamaka", "Yusuf", "Funmilayo", "Obinna", "Hauwa", "Segun", "Amaka", "Sadiq",
         "Temitope", "Kelechi", "Halima", "Uche", "Bukola", "Abdullahi", "Nneka", "Femi", "Maryam", "Ifeanyi"]
LAST = ["Okafor", "Adeyemi", "Bello", "Nwosu", "Abubakar", "Olawale", "Eze", "Mohammed", "Ogunleye", "Okeke",
        "Suleiman", "Adekunle", "Obi", "Danjuma", "Ajayi", "Chukwu", "Garba", "Afolabi", "Umar", "Nnamdi"]
STATES = ["Lagos", "Kano", "Enugu", "Oyo", "Kaduna", "Anambra", "Ogun", "Borno", "Rivers", "Kwara", "Benue", "Imo"]
COURSES = {"CMP468": "Computer Security", "CMP462": "Compiler Construction", "CMP466": "Software Engineering II",
           "CMP472": "Artificial Intelligence", "GST412": "Entrepreneurship"}


def grade(score: int) -> tuple[str, int]:
    for cut, g, p in [(70, "A", 5), (60, "B", 4), (50, "C", 3), (45, "D", 2), (40, "E", 1)]:
        if score >= cut:
            return g, p
    return "F", 0


def main() -> None:
    random.seed(468)
    if TARGET.exists() and any(TARGET.iterdir()):
        print(f"{TARGET} already has data; delete demo/sandbox to start over.")
        return
    TARGET.mkdir(parents=True, exist_ok=True)
    (TARGET / MARKER).write_text("UniGuard demo data. Safe to destroy in simulations.\n")

    students = []
    for i in range(1, 121):
        students.append({
            "matric_no": f"CMP/{random.choice([2021, 2022])}/{i:03d}",
            "surname": random.choice(LAST), "other_names": random.choice(FIRST),
            "state_of_origin": random.choice(STATES), "level": 400,
            "jamb_reg": f"{random.randint(10**9, 10**10 - 1)}{random.choice('ABCDEFGH')}{random.choice('ABCDEFGH')}",
            "phone": f"080{random.randint(10**7, 10**8 - 1)}",
        })

    reg = TARGET / "registry"
    (reg / "results").mkdir(parents=True)
    (reg / "student_records").mkdir(parents=True)
    with open(reg / "student_records" / "400L_students.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=students[0].keys())
        w.writeheader()
        w.writerows(students)

    for code, title in COURSES.items():
        with open(reg / "results" / f"{code}_2025_2026_second_semester.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["matric_no", "course", "ca_30", "exam_70", "total", "grade", "grade_point"])
            for s in students:
                ca, ex = random.randint(10, 30), random.randint(20, 70)
                g, p = grade(ca + ex)
                w.writerow([s["matric_no"], code, ca, ex, ca + ex, g, p])
        (reg / "results" / f"{code}_senate_approval.txt").write_text(
            f"{code} {title}: results approved at Senate meeting. Signed: Registrar.\n")

    bursary = TARGET / "bursary"
    bursary.mkdir()
    with open(bursary / "school_fees_payments_2025_2026.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["matric_no", "rrr", "amount_ngn", "channel", "status"])
        for s in students:
            w.writerow([s["matric_no"], f"{random.randint(10**11, 10**12 - 1)}", random.choice([45000, 62500, 90000]),
                        random.choice(["Remita card", "Bank branch", "USSD"]), "PAID"])

    admissions = TARGET / "admissions"
    admissions.mkdir()
    (admissions / "caps_admission_list_2026.json").write_text(json.dumps(
        [{"jamb_reg": s["jamb_reg"], "course": "Computer Science", "status": "ADMITTED"} for s in students[:40]],
        indent=1))

    lectures = TARGET / "departments" / "computer_science" / "lecture_notes"
    lectures.mkdir(parents=True)
    for n, topic in enumerate(["Overview of security in computing", "Characteristics of computer intrusion",
                               "Types of security breaches", "Classes of attacks", "Methods of defense",
                               "Encryption and decryption", "Database security", "Network security",
                               "Security policies and standards"], 1):
        (lectures / f"CMP468_week{n:02d}.md").write_text(
            f"# CMP 468 Week {n}: {topic}\n\n" + ("Lecture notes paragraph. " * 200) + "\n")

    hr = TARGET / "hr"
    hr.mkdir()
    db = sqlite3.connect(hr / "staff_payroll.sqlite")
    db.execute("CREATE TABLE staff (staff_id TEXT, name TEXT, rank TEXT, ippis_no TEXT, grade_level TEXT)")
    for i in range(60):
        db.execute("INSERT INTO staff VALUES (?,?,?,?,?)",
                   (f"SP{1000 + i}", f"{random.choice(FIRST)} {random.choice(LAST)}",
                    random.choice(["Lecturer II", "Lecturer I", "Senior Lecturer", "Reader", "Professor"]),
                    f"IPPIS{random.randint(100000, 999999)}", f"CONUASS {random.randint(2, 7)}"))
    db.commit()
    db.close()

    (HERE / "sandbox" / "ups_status.txt").write_text("MAINS 100\n")
    files = [p for p in TARGET.rglob("*") if p.is_file()]
    print(f"Created {len(files)} files ({sum(p.stat().st_size for p in files) / 1024:.0f} KiB) in {TARGET}")


if __name__ == "__main__":
    sys.exit(main())
