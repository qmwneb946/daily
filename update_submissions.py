import requests 
from datetime import datetime 
import pytz 
import os 
import re 
 
CF_HANDLE = "qmwneb946"
API_URL = f"https://codeforces.com/api/user.status?handle={CF_HANDLE}" 
BEIJING_TZ = pytz.timezone('Asia/Shanghai') 
 
def get_submissions():
    try:
        response = requests.get(API_URL,  timeout=10)
        response.raise_for_status() 
        data = response.json() 
        if data["status"] != "OK":
            raise Exception("API status not OK")
        return data["result"]
    except Exception as e:
        print(f"获取数据失败: {str(e)}")
        return []
 
def process_submissions(submissions):
    current_date = datetime.now(BEIJING_TZ).date() 
    processed = []
    
    for sub in submissions:
        # 转换时区 [1]()
        utc_time = datetime.fromtimestamp(sub["creationTimeSeconds"],  pytz.utc) 
        beijing_time = utc_time.astimezone(BEIJING_TZ) 
        
        if beijing_time.date()  != current_date:
            continue 
            
        processed.append({ 
            "id": sub["id"],
            "time": beijing_time.strftime("%Y-%m-%d  %H:%M:%S"),
            "problem": sub["problem"]["name"],
            "contest": sub["problem"]["contestId"],
            "index": sub["problem"]["index"],
            "rating": sub["problem"].get("rating", "N/A"),
            "tags": ", ".join(sub["problem"]["tags"]),
            "verdict": sub["verdict"],
            "tests": sub["passedTestCount"],
            "runtime": f"{sub['timeConsumedMillis']}ms",
            "memory": f"{sub['memoryConsumedBytes'] // 1024}KB"
        })
    
    return sorted(processed, key=lambda x: x["id"], reverse=True)
 
def update_daily_log(submissions):
    date_str = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d") 
    filename = f"logs/{date_str}.md"
    
    content = [f"# {date_str} 提交记录\n"]
    if submissions:
        content.append(" | ID | 时间 | 题目 | 比赛 | 难度 | 标签 | 结果 | 测试用例 | 运行时间 | 内存消耗 |")
        content.append(" |----|------|-----|-----|------|-----|------|---------|--------|----------|")
        for sub in submissions:
            problem_link = f"[{sub['problem']}](https://codeforces.com/problemset/problem/{sub['contest']}/{sub['index']})" 
            row = [
                sub["id"],
                sub["time"],
                problem_link,
                sub["contest"],
                sub["rating"],
                sub["tags"],
                sub["verdict"],
                sub["tests"],
                sub["runtime"],
                sub["memory"]
            ]
            content.append(" | " + " | ".join(map(str, row)) + " |")
    else:
        content.append(" 今日无提交记录")
    
    os.makedirs("logs",  exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(content)) 
    filename = "READMD.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(content)) 
 
if __name__ == "__main__":
    submissions = get_submissions()
    processed = process_submissions(submissions)
    update_daily_log(processed)
