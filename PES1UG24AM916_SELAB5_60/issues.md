# Lab 5: Static Code Analysis - Issues Table

File: `hostel_allocation.py`. 

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| Flask debug=True (Bandit B201, High) | Security | 80 | Werkzeug debugger lets anyone who can reach the portal run arbitrary code. | Removed debug=True; app runs on 127.0.0.1 only. |
| Reflected XSS in /room | Security | 77 | The id from the URL is concatenated into HTML, so ?id=`<script>` runs in the browser. A missing id also crashes with TypeError. No tool flags this. | Escape with markupsafe.escape; return HTTP 400 if id is missing. |
| Unsafe yaml.load (Bandit B506, Medium) | Security | 21 | yaml.Loader can build arbitrary Python objects from a malicious config. | Use yaml.safe_load. |
| Insecure logging.config.listen (Bandit B612, Medium) | Security | 72 | Opens a socket that accepts logging configs from the network. The function was never used. | Deleted startRemoteLogConfig and its import. |
| Room overfilled (off-by-one) | Bug | 33 | len(occupants) > capacity lets a room take capacity+1 people (3 students in 2-bed room A1). | Changed the check to < capacity. |
| Gender ignored (Pylint W0613 unused argument) | Bug | 29, 33 | Female student was placed in the boys' block. Pylint only reports the unused argument. | A room must match the student's gender. |
| No duplicate-allocation check | Bug | 29-38 | Allocating S1 twice gave a second bed and overwrote the first allocation. | Return the existing room if the student is already allocated. |
| vacateRoom leaves student in room | Bug | 41-45 | Only allocations was cleared; occupants still listed the student, so the bed was never freed. | pop the allocation and remove the id from the room's occupants. |
| vacantBeds miscounts | Bug | 58-63 | Counted only fully empty rooms, ignoring free beds in partly filled rooms. | Sum capacity minus occupants over all rooms. |
| priorityOrder sorts the wrong way | Bug | 52-53 | Ascending sort puts juniors first, but seniors should come first. | Added reverse=True. |
| monthlyFee rounds down | Bug | 47-50 | 45 // 30 = 1, so 15 days were free. Unallocated students caused a KeyError. | Use math.ceil(days / 30); raise a clear KeyError for unknown ids. |
| Mutable default argument (Pylint W0102) | Bug | 29 | preferred=[] is shared across calls. Unknown room numbers in preferred caused KeyError. | Default to None; keep only rooms that exist. |
| Silent failure on invalid year | Bug | 30-31 | Returns None, same as waitlisted, so callers cannot tell them apart. | isinstance check (excluding bool); None documented as no room. |
| Waitlist duplicates | Bug | 38 | The same student was appended on every retry. | Append only if not already waitlisted. |
| Hardcoded password (Bandit B106, Low) | Security | 66 | Password stored in source code and version control. | Read from environment variable WARDEN_DB_PASSWORD. |
| random for lottery (Bandit B311, Low) | Security | 56 | Predictable pseudo-random generator for a lottery. | Use secrets.SystemRandom().sample. |
| main() runs on import (Flake8 E305) | Design | 101 | Importing the module runs the demo. | Added if __name__ == "__main__" guard. |
| Unused imports os, sys (Flake8 F401, Pylint W0611) | Style | 1-2 | Dead imports. | Removed sys; os is now used for the password. |
| type() comparison (Flake8 E721, Pylint C0123) | Style | 30 | Non-idiomatic type check. | Use isinstance. |
| Naming, docstrings, dict iteration (Pylint C0103, C0114, C0116, C0206) | Style | 20-82, 60 | camelCase function names, no docstrings, loop over keys then index. | Renamed to snake_case, added docstrings, iterate with values()/items(). |
| Formatting (Flake8 E302, E305, E501) | Style | many | One blank line between functions; lines over 79 characters. | Two blank lines; wrapped long lines. |
