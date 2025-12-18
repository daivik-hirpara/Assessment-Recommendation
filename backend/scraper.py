"""
SHL Product Catalog Scraper - FULL VERSION
Scrapes Individual Test Solutions with descriptions for ALL assessments.
"""

import asyncio
import json
import re
from pathlib import Path
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup


DATA_DIR = Path(__file__).parent.parent / "data"
CATALOG_URL = "https://www.shl.com/products/product-catalog/"

TIMEOUT = 30000
MAX_RETRIES = 2


async def safe_goto(page: Page, url: str, retries: int = MAX_RETRIES) -> bool:
    """Navigate to URL with retries."""
    for attempt in range(retries):
        try:
            await page.goto(url, timeout=TIMEOUT, wait_until="domcontentloaded")
            await asyncio.sleep(1)
            return True
        except PlaywrightTimeout:
            print(f"  Timeout {attempt + 1}/{retries}")
            if attempt < retries - 1:
                await asyncio.sleep(2)
        except Exception as e:
            print(f"  Error: {e}")
    return False


async def scrape_catalog_page(page: Page, start: int) -> list[dict]:
    """Scrape a single page of the catalog."""
    url = f"{CATALOG_URL}?start={start}&type=1"
    
    success = await safe_goto(page, url)
    if not success:
        return []
    
    content = await page.content()
    soup = BeautifulSoup(content, "lxml")
    
    assessments = []
    
    tables = soup.find_all("table")
    for table in tables:
        rows = table.find_all("tr")
        for row in rows[1:]:
            cells = row.find_all("td")
            if len(cells) >= 4:
                name_cell = cells[0]
                link = name_cell.find("a")
                if link:
                    name = link.get_text(strip=True)
                    href = link.get("href", "")
                    if href and not href.startswith("http"):
                        href = f"https://www.shl.com{href}"
                    
                    remote_yes = cells[1].find("span", class_=lambda x: x and "catalogue__circle--yes" in str(x)) if len(cells) > 1 else None
                    adaptive_yes = cells[2].find("span", class_=lambda x: x and "catalogue__circle--yes" in str(x)) if len(cells) > 2 else None
                    
                    remote_support = "Yes" if remote_yes else "No"
                    adaptive_support = "Yes" if adaptive_yes else "No"
                    
                    test_types = []
                    if len(cells) > 3:
                        type_spans = cells[3].find_all("span", class_="product-catalogue__key")
                        for span in type_spans:
                            txt = span.get_text(strip=True)
                            if txt in ["K", "P", "S"]:
                                test_types.append(txt)
                    
                    duration = ""
                    if len(cells) > 4:
                        duration = cells[4].get_text(strip=True)
                    
                    assessments.append({
                        "name": name,
                        "url": href,
                        "remote_support": remote_support,
                        "adaptive_support": adaptive_support,
                        "test_types": test_types,
                        "duration": duration,
                        "description": ""
                    })
    
    return assessments


async def scrape_assessment_description(page: Page, assessment: dict) -> str:
    """Scrape description from an assessment's page."""
    try:
        success = await safe_goto(page, assessment["url"], retries=1)
        if not success:
            return ""
        
        content = await page.content()
        soup = BeautifulSoup(content, "lxml")
        
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            return meta_desc.get("content", "")[:500]
        
        main_content = soup.find("main") or soup.find("article")
        if main_content:
            paragraphs = main_content.find_all("p")
            if paragraphs:
                return " ".join(p.get_text(strip=True) for p in paragraphs[:3])[:500]
        
    except Exception as e:
        pass
    
    return ""


async def main():
    """Main scraping function."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_file = DATA_DIR / "assessments.json"
    
    all_assessments = []
    
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        print("Scraping catalog pages...")
        for page_num in range(33):
            start = page_num * 12
            assessments = await scrape_catalog_page(page, start)
            all_assessments.extend(assessments)
            print(f"  Page {page_num + 1}/33: {len(assessments)} items (Total: {len(all_assessments)})")
            await asyncio.sleep(0.5)
        
        seen_urls = set()
        unique = []
        for a in all_assessments:
            if a["url"] not in seen_urls:
                seen_urls.add(a["url"])
                unique.append(a)
        all_assessments = unique
        print(f"\nUnique assessments: {len(all_assessments)}")
        
        print(f"\nScraping descriptions for ALL {len(all_assessments)} assessments...")
        for i, assessment in enumerate(all_assessments):
            desc = await scrape_assessment_description(page, assessment)
            assessment["description"] = desc
            
            if (i + 1) % 25 == 0:
                pct = (i + 1) / len(all_assessments) * 100
                has_desc = sum(1 for a in all_assessments[:i+1] if a.get("description"))
                print(f"  Progress: {i + 1}/{len(all_assessments)} ({pct:.0f}%) - {has_desc} with descriptions")
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(all_assessments, f, indent=2, ensure_ascii=False)
            
            await asyncio.sleep(0.3)
        
        await browser.close()
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_assessments, f, indent=2, ensure_ascii=False)
    
    has_desc = sum(1 for a in all_assessments if a.get("description"))
    print(f"\n✅ Scraped {len(all_assessments)} assessments")
    print(f"📝 With descriptions: {has_desc} ({has_desc/len(all_assessments)*100:.1f}%)")
    print(f"📁 Saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
