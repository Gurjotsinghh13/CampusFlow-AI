import json
from tests.run_final_real_audit import run_audit

data = run_audit()
print("=" * 80)
print("SESSION RECONCILIATION TABLE:")
print("=" * 80)
print(f"| {'Division':<10} | {'Code':<6} | {'Subject Name':<32} | {'Req Sess':<8} | {'Req Hrs':<7} | {'Sched Sess':<10} | {'Sched Hrs':<9} | {'Diff':<4} |")
print(f"|{'-'*12}|{'-'*8}|{'-'*34}|{'-'*10}|{'-'*9}|{'-'*12}|{'-'*11}|{'-'*6}|")
for r in data["reconciliation"]:
    div_s = "Div-A" if "A" in r["division"] else "Div-B"
    print(f"| {div_s:<10} | {r['code']:<6} | {r['name']:<32} | {r['req_sessions']:<8} | {r['req_hours']:<7} | {r['sched_sessions']:<10} | {r['sched_hours']:<9} | {r['diff_hours']:<4} |")

print("\n" + "=" * 80)
print("FACULTY DETAILED AUDIT:")
print("=" * 80)
for fac_name, fac in data["fac_details"].items():
    days_str = ", ".join(f"{d[:3]}: {h}h" for d, h in fac["day_hours"].items())
    print(f"{fac_name:<25} | Days: {fac['teaching_days']} | Weekly: {fac['weekly_hours']}h | Earliest: {fac['earliest_class']} | Latest: {fac['latest_class']} | Idle Gaps: {fac['idle_gaps']}")
    print(f"   Daily load: {days_str}")

print("\n" + "=" * 80)
print("ROOM DETAILED AUDIT:")
print("=" * 80)
for rm_num, rm in data["room_usage"].items():
    print(f"{rm_num:<12} | Type: {rm['type']:<10} | Capacity: {rm['capacity']} | Hours Used: {rm['hours']} / 35 ({round(rm['hours']/35*100, 1)}%)")
