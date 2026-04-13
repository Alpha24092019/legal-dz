#!/usr/bin/env python3
"""
سكريبت لتحميل الجرائد الرسمية الجزائرية من الموقع الرسمي
"""

import requests
from bs4 import BeautifulSoup
import os
import re
from datetime import datetime
import json
import time

class JOScraper:
    def __init__(self):
        self.base_url = "http://www.joradp.dz"
        self.output_dir = "content/library/جرائد-رسمية"
        self.pdfs_dir = "static/pdfs/jo"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # إنشاء المجلدات
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.pdfs_dir, exist_ok=True)
    
    def get_jo_list(self, year=None):
        """جلب قائمة الجرائد الرسمية لسنة معينة"""
        if year is None:
            year = datetime.now().year
            
        url = f"{self.base_url}/JOIndexe/Recueil-{year}.htm"
        
        try:
            response = self.session.get(url, timeout=30)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            journals = []
            
            # البحث عن روابط الجرائد
            for link in soup.find_all('a', href=re.compile(r'\.pdf', re.I)):
                href = link.get('href')
                if href and 'JO' in href:
                    full_url = href if href.startswith('http') else f"{self.base_url}{href}"
                    
                    # استخراج رقم العدد والتاريخ
                    text = link.get_text(strip=True)
                    match = re.search(r'(\d+)[^\d]+(\d{2})[/-](\d{2})[/-](\d{4})', text)
                    
                    if match:
                        numero, day, month, year = match.groups()
                        journals.append({
                            'numero': numero,
                            'date': f"{year}-{month}-{day}",
                            'url': full_url,
                            'title': f"الجريدة الرسمية رقم {numero} - {day}/{month}/{year}"
                        })
            
            return journals
            
        except Exception as e:
            print(f"خطأ في جلب القائمة: {e}")
            return []
    
    def download_pdf(self, url, filename):
        """تحميل ملف PDF"""
        filepath = os.path.join(self.pdfs_dir, filename)
        
        if os.path.exists(filepath):
            print(f"الملف موجود مسبقاً: {filename}")
            return filepath
        
        try:
            print(f"جاري تحميل: {filename}")
            response = self.session.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            # التحقق من حجم الملف
            total_size = int(response.headers.get('content-length', 0))
            
            with open(filepath, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\rالتقدم: {percent:.1f}%", end='')
            
            print(f"\nتم التحميل: {filename}")
            return filepath
            
        except Exception as e:
            print(f"\nخطأ في تحميل {filename}: {e}")
            if os.path.exists(filepath):
                os.remove(filepath)
            return None
    
    def create_markdown(self, journal_info, pdf_path):
        """إنشاء ملف Markdown للجريدة"""
        filename = f"jo-{journal_info['numero']}-{journal_info['date']}.md"
        filepath = os.path.join(self.output_dir, filename)
        
        if os.path.exists(filepath):
            print(f"ملف Markdown موجود: {filename}")
            return
        
        # حساب حجم الملف
        size_mb = os.path.getsize(pdf_path) / (1024 * 1024) if pdf_path else 0
        
        content = f"""---
title: "{journal_info['title']}"
date: {journal_info['date']}T00:00:00+01:00
year: {journal_info['date'][:4]}
numero: {journal_info['numero']}
pages: 0
downloads: 0
file_size: "{size_mb:.1f} MB"
pdf_url: "/pdfs/jo/{os.path.basename(pdf_path) if pdf_path else ''}"
categories: ["جرائد رسمية"]
description: "الجريدة الرسمية للجمهورية الجزائرية الديمقراطية الشعبية - العدد {journal_info['numero']} بتاريخ {journal_info['date']}"
draft: false
---

## نبذة

هذه الجريدة الرسمية تحتوي على النصوص القانونية والتنظيمية والقرارات المنشورة بتاريخ {journal_info['date']}.

## المحتويات الرئيسية

- القوانين
- المراسيم التنفيذية
- القرارات الوزارية
- الإعلانات القانونية

## التحميل

يمكنك تحميل الجريدة الرسمية كاملة بصيغة PDF من الزر أدناه.
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"تم إنشاء: {filename}")
    
    def run(self, year=None, limit=None):
        """تشغيل السكريبت"""
        print(f"بدء تحميل الجرائد الرسمية لسنة {year or datetime.now().year}...")
        
        journals = self.get_jo_list(year)
        print(f"تم العثور على {len(journals)} جريدة رسمية")
        
        if limit:
            journals = journals[:limit]
        
        for i, journal in enumerate(journals, 1):
            print(f"\n[{i}/{len(journals)}] معالجة: {journal['title']}")
            
            # تحميل PDF
            pdf_filename = f"jo-{journal['numero']}-{journal['date']}.pdf"
            pdf_path = self.download_pdf(journal['url'], pdf_filename)
            
            # إنشاء Markdown
            if pdf_path:
                self.create_markdown(journal, pdf_path)
            
            # تأخير بين الطلبات
            time.sleep(2)
        
        print("\nاكتمل التحميل!")

def update_library_index():
    """تحديث فهرس المكتبة"""
    library_dir = "content/library"
    index_file = "data/library_index.json"
    
    os.makedirs("data", exist_ok=True)
    
    index = {
        "categories": {},
        "total_laws": 0,
        "last_update": datetime.now().isoformat()
    }
    
    for category in os.listdir(library_dir):
        cat_path = os.path.join(library_dir, category)
        if os.path.isdir(cat_path):
            files = [f for f in os.listdir(cat_path) if f.endswith('.md')]
            index["categories"][category] = len(files)
            index["total_laws"] += len(files)
    
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    
    print(f"تم تحديث الفهرس: {index['total_laws']} قانون")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='تحميل الجرائد الرسمية الجزائرية')
    parser.add_argument('--year', type=int, help='السنة المستهدفة')
    parser.add_argument('--limit', type=int, help='عدد الجرائد للتحميل')
    parser.add_argument('--update-index', action='store_true', help='تحديث الفهرس فقط')
    
    args = parser.parse_args()
    
    if args.update_index:
        update_library_index()
    else:
        scraper = JOScraper()
        scraper.run(year=args.year, limit=args.limit)