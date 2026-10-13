#!/usr/bin/env python3
"""
SkillRadar VN — do nguon tuyen dung
Chay truoc khi viet crawler. Script nay KHONG thu thap du lieu,
chi tai 1 trang moi nguon de xem co lay duoc khong.

Cai dat:  pip install httpx
Chay:     python probe_sources.py > probe_report.txt
Gui lai file probe_report.txt.
"""

import json
import re
import sys
import time
import urllib.robotparser as robotparser
from urllib.parse import urlparse

try:
    import httpx
except ImportError:
    sys.exit("Thieu thu vien. Chay: pip install httpx")

# User-agent khai bao ro rang, dung cam ket trong de xuat.
# Email lay tu config/sources.yaml (contact_email), dung chung voi crawler.
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
from src.config import load_sources, user_agent  # noqa: E402

UA = user_agent(load_sources().get("contact_email"))

DELAY = 2.0          # giay giua 2 request, de thap
TIMEOUT = 25.0

# Sua danh sach nay neu ban muon them/bot nguon.
# 'list' la 1 trang danh sach viec lam bat ky cua trang do.
SITES = {
    "itviec":        ["https://itviec.com/it-jobs"],
    "vietnamworks":  ["https://www.vietnamworks.com/viec-lam"],
    "careerviet":    ["https://careerviet.vn/viec-lam/tat-ca-viec-lam-vi.html"],
    "careerlink":    ["https://www.careerlink.vn/viec-lam/tat-ca-viec-lam"],
    "jobsgo":        ["https://jobsgo.vn/viec-lam.html"],
    "vieclam24h":    ["https://vieclam24h.vn/tim-kiem-viec-lam-nhanh"],
    "topcv":         ["https://www.topcv.vn/viec-lam"],
    "job3s":         ["https://job3s.vn/tim-viec-lam"],
}

BOT_WALL = re.compile(
    r"(cf-browser-verification|cf_chl|Just a moment|Checking your browser|"
    r"Attention Required|Access denied|captcha|DataDome|PerimeterX)", re.I)

JOB_HINT = re.compile(
    r"(tuy\w*n d\w*ng|vi\w*c l\w*m|m\w*c l\w*ng|kinh nghi\w*m|ung tuy\w*n|"
    r"job|salary|apply|experience)", re.I)


def robots_for(url, client):
    """Tai robots.txt va tra ve (cho_phep, trich_doan)."""
    p = urlparse(url)
    rurl = f"{p.scheme}://{p.netloc}/robots.txt"
    try:
        r = client.get(rurl)
        if r.status_code != 200:
            return None, f"robots.txt tra ve HTTP {r.status_code}"
        txt = r.text
        rp = robotparser.RobotFileParser()
        rp.parse(txt.splitlines())
        allowed = rp.can_fetch(UA, url)
        # trich phan Disallow dang chu y
        lines = [l.strip() for l in txt.splitlines()
                 if l.strip().lower().startswith(("user-agent", "disallow", "crawl-delay"))]
        head = " | ".join(lines[:14])[:420]
        delay = rp.crawl_delay(UA)
        return allowed, f"crawl-delay={delay} :: {head}"
    except Exception as e:
        return None, f"loi tai robots.txt: {type(e).__name__}"


def sitemaps_for(url, client):
    """Tim sitemap va RSS — day la duong duoc cac trang chu dong mo."""
    p = urlparse(url)
    root = f"{p.scheme}://{p.netloc}"
    found = []
    # 1. khai bao trong robots.txt
    try:
        r = client.get(f"{root}/robots.txt")
        if r.status_code == 200:
            found += re.findall(r"(?im)^\s*sitemap:\s*(\S+)", r.text)
    except Exception:
        pass
    # 2. duong dan mac dinh
    for guess in ("/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml"):
        if any(guess in f for f in found):
            continue
        try:
            r = client.get(root + guess)
            if r.status_code == 200 and "<" in r.text[:200]:
                found.append(root + guess)
        except Exception:
            pass
        time.sleep(0.6)
    out = []
    for sm in dict.fromkeys(found):
        try:
            r = client.get(sm)
            body = r.text if r.status_code == 200 else ""
            n_loc = body.count("<loc>")
            kind = "chi muc sitemap" if "<sitemapindex" in body else "danh sach URL"
            jobish = len(re.findall(r"<loc>[^<]*(viec-lam|job|tuyen-dung)[^<]*</loc>", body, re.I))
            out.append(f"{sm} -> HTTP {r.status_code}, {kind}, {n_loc} loc, {jobish} co ve la tin tuyen dung")
        except Exception as e:
            out.append(f"{sm} -> loi {type(e).__name__}")
        time.sleep(0.6)
    return out


def analyse(html):
    """Xem noi dung nam san trong HTML hay phai chay JavaScript."""
    out = {}
    out["bytes"] = len(html)
    out["bot_wall"] = bool(BOT_WALL.search(html[:6000]))
    out["ld_json"] = len(re.findall(r'application/ld\+json', html, re.I))
    out["next_data"] = "__NEXT_DATA__" in html
    out["nuxt"] = "__NUXT__" in html
    out["job_posting_schema"] = bool(re.search(r'"@type"\s*:\s*"JobPosting"', html, re.I))
    # dem the <a> tro toi trang chi tiet viec lam
    hrefs = re.findall(r'href="([^"]+)"', html)
    jobish = [h for h in hrefs if re.search(r"(viec-lam|job|tuyen-dung|jobs)/", h)]
    out["job_links"] = len(jobish)
    out["rss"] = re.findall(r'type="application/(?:rss|atom)\+xml"[^>]*href="([^"]+)"', html)[:3]
    out["sample_links"] = jobish[:3]
    # dem tin hieu tieng Viet tuyen dung trong phan text
    text = re.sub(r"<script.*?</script>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    out["text_chars"] = len(re.sub(r"\s+", " ", text).strip())
    out["job_words"] = len(JOB_HINT.findall(text))
    return out


def verdict(a, allowed):
    if allowed is False:
        return "BO QUA — robots.txt khong cho phep"
    if a["bot_wall"]:
        return "CHAN — co tuong chong bot, khong dung duoc"
    if a["job_posting_schema"]:
        return "TOT NHAT — co schema JobPosting, bok du lieu rat sach"
    if a["next_data"] or a["nuxt"]:
        return "TOT — du lieu nam trong JSON nhung trong trang"
    if a["job_links"] >= 10 and a["text_chars"] > 4000:
        return "DUNG DUOC — HTML dung san, parse bang CSS selector"
    if a["text_chars"] < 2000:
        return "CAN JAVASCRIPT — trang rong, phai dung trinh duyet"
    return "KHONG CHAC — can xem tay"


def main():
    print("SkillRadar VN — bao cao do nguon")
    print("User-Agent:", UA)
    print("=" * 72)
    with httpx.Client(headers={"User-Agent": UA,
                               "Accept-Language": "vi,en;q=0.8"},
                      follow_redirects=True, timeout=TIMEOUT) as c:
        for name, urls in SITES.items():
            print(f"\n### {name}")
            for url in urls:
                allowed, note = robots_for(url, c)
                print(f"  robots: cho_phep={allowed} :: {note}")
                time.sleep(DELAY)
                if allowed is False:
                    print("  -> BO QUA, khong tai trang.")
                    continue
                try:
                    r = c.get(url)
                    a = analyse(r.text)
                    print(f"  HTTP {r.status_code} | {a['bytes']:,} bytes | text {a['text_chars']:,} ky tu")
                    print(f"  JobPosting_schema={a['job_posting_schema']} ld+json={a['ld_json']} "
                          f"NEXT_DATA={a['next_data']} NUXT={a['nuxt']}")
                    print(f"  link_viec_lam={a['job_links']} tu_khoa={a['job_words']} bot_wall={a['bot_wall']}")
                    for s in a["sample_links"]:
                        print(f"    vi du: {s[:110]}")
                    if a["rss"]:
                        print(f"  RSS: {a['rss']}")
                    print(f"  >> {verdict(a, allowed)}")
                    for line in sitemaps_for(url, c):
                        print(f"  sitemap: {line[:160]}")
                except Exception as e:
                    print(f"  LOI: {type(e).__name__}: {e}")
                time.sleep(DELAY)
    print("\n" + "=" * 72)
    print("Xong. Gui lai toan bo ket qua nay.")


if __name__ == "__main__":
    main()
