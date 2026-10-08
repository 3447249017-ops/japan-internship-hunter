#!/usr/bin/env python3
"""Japan Internship Hunter V3: public company job-board APIs; no scraping or auto-applications."""
import csv
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'output'
UA = 'JapanInternshipHunter/3.0 (public job-board API educational project)'
FIELDS = ['company','title','location','industry','job_type','language_hints','source','job_url','apply_url','apply_url_status','published_or_updated_at','date_meaning','recency','published_live_at_fetch','match_score','review_status','reason']
LOCATION_KEYS = ('tokyo','東京都','東京','kanagawa','神奈川','横浜','yokohama','川崎','kawasaki')
JAPAN_KEYS = ('japan','日本','tokyo','東京','神奈川','kanagawa','横浜','yokohama')
INTERNSHIP_KEYS = ('internship','intern','インターン','学生向け','学生対象','学生募集','大学生')
EXCLUDE_KEYS = ('meetup','meet up','説明会','セミナー','event','イベント','採用イベント')
INDUSTRIES = {
    'consulting': ('consult','コンサル','strategy','strategic','戦略','research','リサーチ','analyst','アナリスト','advisory','調査'),
    'IT_AI': ('ai','machine learning','ml engineer','software','engineer','エンジニア','robot','ロボット','data','データ','dx','automation','自動化','technology','tech','開発','product'),
    'trading': ('trading','商社','貿易','trade','procurement','調達','supply chain','scm','事業開発','business development'),
}

def download_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=20) as response:
        if response.status != 200:
            raise RuntimeError(f'HTTP {response.status}')
        if int(response.headers.get('Content-Length', '0')) > 8_000_000:
            raise RuntimeError('Response too large')
        return json.load(response)

def clean(value):
    value = re.sub(r'<[^>]*>', ' ', str(value or ''))
    return ' '.join(html.unescape(value).split())

def normalize_job(source, job):
    provider, board, company = source['provider'], source['board'], source['company']
    if provider == 'lever':
        cats = job.get('categories') or {}
        location = cats.get('location') or ', '.join(cats.get('allLocations') or [])
        content = ' '.join([str(job.get('descriptionPlain') or ''), str(job.get('additionalPlain') or ''), str(cats.get('team') or ''), str(cats.get('commitment') or '')])
        return dict(company=company,title=clean(job.get('text')),location=clean(location),description=clean(content),job_url=job.get('hostedUrl') or '',apply_url=job.get('applyUrl') or '',updated='',date_meaning='unknown',source=f'lever:{board}',live=True,commitment=clean(cats.get('commitment')))
    if provider == 'greenhouse':
        return dict(company=company,title=clean(job.get('title')),location=clean((job.get('location') or {}).get('name')),description=clean(job.get('content')),job_url=job.get('absolute_url') or '',apply_url='',updated=job.get('updated_at') or '',date_meaning='last_updated_not_published',source=f'greenhouse:{board}',live=True,commitment='')
    if provider == 'ashby':
        return dict(company=company,title=clean(job.get('title')),location=clean(job.get('location')),description=clean(job.get('descriptionPlain') or job.get('descriptionHtml')),job_url=job.get('jobUrl') or '',apply_url=job.get('applyUrl') or '',updated=job.get('publishedAt') or '',date_meaning='published_at_if_available',source=f'ashby:{board}',live=job.get('isListed',True) is not False,commitment=clean(job.get('employmentType')))
    raise ValueError('Unsupported provider')

def fetch_source(src):
    board = urllib.parse.quote(src['board'],safe='')
    typ=src['provider']
    if typ == 'lever':
        url=f'https://api.lever.co/v0/postings/{board}?mode=json&limit=1000'
    elif typ == 'greenhouse':
        url=f'https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true'
    elif typ == 'ashby':
        url=f'https://api.ashbyhq.com/posting-api/job-board/{board}'
    else:
        raise ValueError('Unknown provider: '+typ)
    raw=download_json(url)
    jobs=raw if typ=='lever' else raw.get('jobs',[])
    if not isinstance(jobs,list):
        raise ValueError('API response has no job list')
    return [normalize_job(src,j) for j in jobs if isinstance(j,dict)]

def parse_date(text):
    if not text: return None
    try:
        dt=datetime.fromisoformat(text.replace('Z','+00:00'))
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
    except (ValueError,TypeError): return None

def classify(job, now=None):
    now=now or datetime.now(timezone.utc)
    title=job['title'].lower(); loc=job['location'].lower()
    desc=job['description'].lower(); commitment=job.get('commitment','').lower()
    # Require the job location to identify the target region explicitly.
    region_ok=any(k in loc for k in LOCATION_KEYS)
    internship=any(k in title or k in commitment for k in INTERNSHIP_KEYS)
    event=any(k in title for k in EXCLUDE_KEYS)
    nonintern=any(k in title for k in ('senior manager','director','シニアマネージャー','部長')) and not internship
    industry_tags=[k for k,words in INDUSTRIES.items() if any(w in (title+' '+desc) for w in words)]
    # Match tokens like 'AI' only on word boundaries to avoid matching e.g. 'training'.
    if 'IT_AI' in industry_tags and not any(w in title+' '+desc for w in INDUSTRIES['IT_AI'] if len(w)>2) and not re.search(r'\bai\b',title+' '+desc):
        industry_tags.remove('IT_AI')
    lang=[]
    for name,keys in [('Japanese',('japanese','日本語')),('English',('english','英語')),('Chinese',('chinese','中国語'))]:
        if any(k in title+' '+desc+' '+commitment for k in keys):lang.append(name)
    updated=parse_date(job.get('updated'))
    if updated is None: recency='unknown'
    elif updated > now+timedelta(days=1): recency='invalid_future'
    elif updated>=now-timedelta(days=30): recency='updated_within_30_days'
    else: recency='updated_more_than_30_days_ago'
    if event: status='not_a_job'; reason='活动/说明会，不是实习岗位'
    elif not internship:status='other_jobs';reason='标题/岗位类别没有明确实习标记'
    elif not region_ok:status='outside_target_or_unknown_location';reason='工作地点未明确匹配东京/神奈川'
    elif nonintern:status='other_jobs';reason='可能属于非学生职位'
    elif industry_tags:status='priority_manual_review';reason='企业当前公开列表中的目标地区、行业实习线索；必须核验要求和申请状态'
    else:status='internship_industry_unknown';reason='实习和地区匹配，但行业尚未确认'
    apply=job.get('apply_url','')
    # A Greenhouse hosted job URL is a job detail page, not necessarily the direct form.
    apply_status='direct_apply_url_from_provider' if apply else ('job_detail_only_verify_apply_button' if job.get('job_url') else 'missing')
    score=(40 if internship else 0)+(25 if region_ok else 0)+(20 if industry_tags else 0)+(10 if recency=='updated_within_30_days' else 0)+(5 if apply else 0)
    return { 'company':job['company'],'title':job['title'],'location':job['location'],'industry':'|'.join(industry_tags) or 'unknown','job_type':'internship' if internship else 'other_or_unknown','language_hints':'|'.join(lang) or 'not_specified','source':job['source'],'job_url':job['job_url'],'apply_url':apply,'apply_url_status':apply_status,'published_or_updated_at':job.get('updated',''),'date_meaning':job.get('date_meaning','unknown'),'recency':recency,'published_live_at_fetch':str(job.get('live',False)).lower(),'match_score':score,'review_status':status,'reason':reason}

def write_csv(path, rows):
    with open(path,'w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS); writer.writeheader(); writer.writerows(rows)

def main():
    OUT.mkdir(exist_ok=True)
    with open(ROOT/'sources.json',encoding='utf-8') as f:sources=json.load(f)
    active=[s for s in sources if s.get('enabled',True)]
    if not active:
        print('No enabled sources in sources.json',file=sys.stderr)
        return 2
    all_jobs=[];errors=[];source_counts={}
    for src in active:
        key=src['company']+' ('+src['provider']+')'
        try:
            jobs=fetch_source(src);all_jobs.extend(jobs);source_counts[key]=len(jobs)
            print(f'{key}: {len(jobs)} published posts returned')
        except (ValueError,KeyError,urllib.error.URLError,TimeoutError,OSError) as exc:
            errors.append({'source':key,'error':str(exc)[:250]});print(f'FAILED {key}: {exc}',file=sys.stderr)
    if not source_counts:
        print('All sources failed; refusing to create misleading success data.',file=sys.stderr)
        return 1
    seen=set();rows=[]
    for job in all_jobs:
        key=job['job_url'] or job['source']+'|'+job['title']+'|'+job['location']
        if key in seen:continue
        seen.add(key)
        row=classify(job)
        if row['published_live_at_fetch']=='true':rows.append(row)
    rows.sort(key=lambda r:(r['review_status']!='priority_manual_review',-r['match_score'],r['company'],r['title']))
    priority=[r for r in rows if r['review_status']=='priority_manual_review']
    other=[r for r in rows if r['review_status']!='priority_manual_review']
    write_csv(OUT/'all_company_jobs.csv',rows)
    write_csv(OUT/'priority_manual_review.csv',priority)
    write_csv(OUT/'other_jobs.csv',other)
    summary={'generated_utc':datetime.now(timezone.utc).isoformat(),'sources_requested':len(active),'sources_succeeded':len(source_counts),'source_counts':source_counts,'source_errors':errors,'published_jobs_fetched_unique':len(rows),'priority_manual_review':len(priority),'other_jobs':len(other),'validated_applications':0,'note':'Provider lists published jobs, not confirmed eligibility, open forms, or dates; updated_at is not publication date. Search limited to sources.json.'}
    (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    return 0

if __name__=='__main__':sys.exit(main())
