import requests
from datetime import datetime
import pytz
import os
import json
import re

CF_HANDLE = "qmwneb946"
API_URL = f"https://codeforces.com/api/user.status?handle={CF_HANDLE}" 
BEIJING_TZ = pytz.timezone('Asia/Shanghai') 


def get_submissions():
    response = requests.get(API_URL) 
    if response.status_code!=  200:
        raise Exception("Failed to fetch data from Codeforces API")
    data = response.json() 
    if data["status"]!= "OK":
        raise Exception("API returned non-OK status")
    return data["result"]


def process_submissions(submissions):
    current_date = datetime.now(BEIJING_TZ).date() 
    current_date_str = current_date.strftime("%Y-%m-%d") 
    daily_submissions = []

    for sub in submissions:
        creation_time = datetime.fromtimestamp(sub["creationTimeSeconds"],  tz=pytz.utc) 
        creation_time = creation_time.astimezone(BEIJING_TZ) 
        if creation_time.date()  == current_date:
            daily_submissions.append({ 
                "id": sub["id"],
                "time": creation_time.strftime("%Y-%m-%d  %H:%M:%S"),
                "problem": sub["problem"]["name"],
                "contest": sub["problem"]["contestId"],
                "index": sub["problem"]["index"],
                "rating": sub["problem"].get("rating", "N/A"),
                "tags": ", ".join(sub["problem"]["tags"]),
                "language": sub["programmingLanguage"],
                "verdict": sub["verdict"],
                "passed": sub["passedTestCount"],
                "consumed": f"{sub['timeConsumedMillis']}ms / {sub['memoryConsumedBytes']}bytes"
            })

    return current_date_str, sorted(daily_submissions, key=lambda x: x["id"], reverse=True)


def update_daily_file(date_str, submissions):
    filename = f"{date_str}.md"
    content = [f"# {date_str} Submissions\n"]

    if submissions:
        content.append(" | ID | Time | Problem | Contest | Rating | Tags | Language | Verdict | Tests | Resources |")
        content.append(" |----|------|---------|---------|--------|------|----------|---------|-------|-----------|")
        for sub in submissions:
            problem_link = f"[{sub['problem']}](https://codeforces.com/problemset/problem/{sub['contest']}/{sub['index']})" 
            row = [
                sub["id"],
                sub["time"],
                problem_link,
                sub["contest"],
                sub["rating"],
                sub["tags"],
                sub["language"],
                sub["verdict"],
                sub["passed"],
                sub["consumed"]
            ]
            content.append(" | " + " | ".join(map(str, row)) + " |")
    else:
        content.append("No  submissions today.")

    with open(filename, "w") as f:
        f.write("\n".join(content)) 


def update_readme(submissions):
    if not os.path.exists("README.md"): 
        return

    with open("README.md",  "r") as f:
        readme = f.read() 

    new_content = ["## Latest Submissions\n"]
    if submissions:
        new_content.append(" | Problem | Contest | Rating | Verdict | Time |")
        new_content.append(" |---------|---------|--------|---------|------|")
        for sub in submissions[:5]:  # Show last 5 submissions
            problem_link = f"[{sub['problem']}](https://codeforces.com/problemset/problem/{sub['contest']}/{sub['index']})" 
            row = [
                problem_link,
                sub["contest"],
                sub["rating"],
                sub["verdict"],
                sub["time"]
            ]
            new_content.append(" | " + " | ".join(map(str, row)) + " |")
    else:
        new_content.append("No  recent submissions.")

    # Update between markers
    updated_readme = re.sub( 
        r"<!-- START_SUBMISSIONS -->.*<!-- END_SUBMISSIONS -->",
        f"<!-- START_SUBMISSIONS -->\n" + "\n".join(new_content) + "\n<!-- END_SUBMISSIONS -->",
        readme,
        flags=re.DOTALL
    )

    with open("README.md",  "w") as f:
        f.write(updated_readme) 


if __name__ == "__main__":
    submissions = get_submissions()
    date_str, processed = process_submissions(submissions)
    update_daily_file(date_str, processed)
    update_readme(processed)
