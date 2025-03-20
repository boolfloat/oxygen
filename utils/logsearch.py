import asyncio
from dataclasses import dataclass
import os
from typing import Iterable, Literal

@dataclass
class Cookie:
    url: str
    include_subdomains: bool
    path: str
    secure: bool
    expires: int
    name: str
    value: str

    def playwright(self):
        return {
            # "url": self.path,
            "name": self.name,
            "value": self.value,
            "domain": self.url,
            "path": self.path,
            "expires": self.expires,
            # "httpOnly": False,
            "secure": self.secure,
            # "sameSite": "Lax",
        }
    
    def netscape(self):
        return f"{self.url}\t{'TRUE' if self.include_subdomains else 'FALSE'}\t{self.path}\t{'TRUE' if self.secure else 'FALSE'}\t{self.expires}\t{self.name}\t{self.value}"
    
    def json(self):
        return {
            self.name: self.value
        }
    
@dataclass
class Log:
    """
        Log format

        :param path: path to log
        :param acc_type: type of account (can be "premium_*" or "free")
        :param cookies: netscape cookies
    """
    path: str
    # acc_type: Literal["premium", "free", "duo_premium", "family_premium_v2"] # remnants of spotify relinker
    cookies: list[Cookie]

def extract_cookies(lines: list[str]) -> list[Cookie]:
    res = []
    # print(lines)
    for line in lines:
        if line == "": continue
        if not "TRUE" in line or not "FALSE" in line: continue
        if line.split("\t")[1] in ("TRUE", "FALSE") and line.split("\t")[2] == "/":
            l = line.split("\t")
            if len(l) == 6: continue
            res.append(Cookie(l[0], l[1] == "TRUE", l[2], l[3] == "TRUE", int(l[4]), l[5], l[6]))
    return res

def parse_log(lines: list[str]) -> Log:
    return Log(path=lines[0], acc_type=lines[1].split(" ")[2], cookies=extract_cookies(lines[3:]))

def split_log_lines(logs: list[str]) -> list[Log]:
    res = []
    tmp = []
    start = False
    stop = False
    skip = False
    # l_n = 1
    for i in range(len(logs)):
        line = logs[i]
        if skip:
            skip = False
            continue
        if line == "---------------------------":
            if start:
                stop = True
            else:
                start = True
        else:
            tmp.append(line)

        if stop:
            stop = False
            start = False
            res.append(parse_log(tmp))
            tmp = []
            skip = True
    return res

def find_cookies(path: str):
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.startswith("Cookies"):
                yield os.path.join(root, file)

def parse_logs(path: str):
    all_cookies_files = [file for file in find_cookies(path)]
    print("Cookie files: "+ str(len(all_cookies_files)) +"\n")
    # print(all_cookies_files)
    parsed_cookies = []
    for cookies_file in all_cookies_files:
        try:
            with open(cookies_file, "r", encoding="utf-8", errors="replace") as f:
                netscape = [line.strip() for line in f.readlines()]
                try:
                    l = extract_cookies(netscape)
                except Exception as e:
                    print("Failed to parse", cookies_file, e)
                    continue
                res = []
                for cookie in l:
                    # if ".spotify" in cookie.url:
                    res.append(cookie)
                parsed_cookies.append(res)
        except Exception as ex:
             print("Failed to parse", cookies_file, ex)
    return ("Found cookies: "+ str(len(parsed_cookies))+"\n", parsed_cookies)

    # with open("result.txt", "w") as f:
    #     for cookies in parsed_cookies:
    #         await asyncio.sleep(1)
    #         try:
    #             plan = await getAccountInfo(cookies)
    #         except Exception as e:
    #             print("Error getting account info", e)
    #             continue
    #         if plan.get("currentPlan") == "free": continue
    #         canRelink = await relinkable(Log("<3", None, cookies))
    #         if not canRelink: continue
    #         yield "Relinkable Found!\n"
    #         f.write(f"{cookie.path}\nAccount type: {plan.get('currentPlan')}\n---------------------------\n{'\n'.join([cookie.netscape() for cookie in cookies])}\n---------------------------\n\n")