import sys
import os
import fitz  # PyMuPDF
import regex as re

def convert_pdf(pdf_path, margin=72):
    doc = fitz.open(pdf_path)
    pages = []
    
    for page in doc:
        r = page.rect
        #clip_rect = fitz.Rect(margin, margin, r.width - margin, r.height - margin)
        page_text = page.get_text("text")
        pages.append(page_text)
    
    doc.close()
    # output text into a file with ---- in between pages 
    #with open("output.txt", "w", encoding="utf-8") as f:
        #for i, page in enumerate(pages):
            #f.write(f"--- Page {i+1} ---\n")
            #f.write(page) 
    
    return pages

def find_citation_segments(text):
    text = re.sub(r'\s*\n\s*', ' ', text)
    patterns = [
        re.compile(r'^(?P<source>[^,]+?)\s*,\s*(?P<year>(?:18|19|20)\d{2}(?:[a-f])?)$', re.IGNORECASE),
        re.compile(r'^(?P<source>[^,]+?)\s*,\s*(?P<year>n\.d\.(?:-[a-z])?)$', re.IGNORECASE),
        re.compile(r'^(?P<source>[^,]+?)\s*,\s*et\s*al\.?\s*,\s*(?P<year>(?:18|19|20)\d{2}(?:[a-f])?|n\.d\.(?:-[a-z])?)$', re.IGNORECASE),
        re.compile(r'^(?P<source>(?:[^,]+,\s*)+(?:&|and)\s*[^,]+)\s*,\s*(?P<year>(?:18|19|20)\d{2}(?:[a-f])?)$', re.IGNORECASE),
        re.compile(r'^(?P<source>[^,]+?)\s+(?P<year>(?:18|19|20)\d{2}(?:[a-f])?)$', re.IGNORECASE),
        re.compile(r'^(?P<source>[^,]+?)\s+(?P<year>n\.d\.(?:-[a-z])?)$', re.IGNORECASE),
        re.compile(r'^(?P<source>[^,]+?\s*(?:et|e)\s*al\.?)\s+(?P<year>(?:18|19|20)\d{2}(?:[a-f])?|n\.d\.(?:-[a-z])?)$', re.IGNORECASE),
        re.compile(r'^(?P<source>(?:[^,]+\s*)+(?:&|and)\s*[^,]+)\s+(?P<year>(?:18|19|20)\d{2}(?:[a-f])?)$', re.IGNORECASE)
    ]
    segments = []
    paren_pat = re.compile(r'\((.*?)\)', re.DOTALL)
    groups = paren_pat.findall(text)
    for group in groups:
        # Decide delimiter:
        if ';' in group:
            parts = group.split(';')
        else:
            dates = re.findall(r'(?:18|19|20)\d{2}', group)
            if len(dates) >= 2:
                parts = group.split(',')
            else:
                parts = [group]
        for seg in parts:
            candidate = seg.strip()
            if not candidate:
                continue
            for pat in patterns:
                if pat.match(candidate):
                    segments.append(candidate)
                    break
    return segments

def process_citations(segments):
    patterns = [
        re.compile(r'^(?P<source>[^,]+?)\s*,\s*(?P<year>(?:18|19|20)\d{2}(?:[a-f])?)$', re.IGNORECASE),
        re.compile(r'^(?P<source>[^,]+?)\s*,\s*(?P<year>n\.d\.(?:-[a-z])?)$', re.IGNORECASE),
        re.compile(r'^(?P<source>[^,]+?)\s*,\s*et\s*al\.?\s*,\s*(?P<year>(?:18|19|20)\d{2}(?:[a-f])?|n\.d\.(?:-[a-z])?)$', re.IGNORECASE),
        re.compile(r'^(?P<source>(?:[^,]+,\s*)+(?:&|and)\s*[^,]+)\s*,\s*(?P<year>(?:18|19|20)\d{2}(?:[a-f])?)$', re.IGNORECASE),
        re.compile(r'^(?P<source>[^,]+?)\s+(?P<year>(?:18|19|20)\d{2}(?:[a-f])?)$', re.IGNORECASE),
        re.compile(r'^(?P<source>[^,]+?)\s+(?P<year>n\.d\.(?:-[a-z])?)$', re.IGNORECASE),
        re.compile(r'^(?P<source>[^,]+?\s*(?:et|e)\s*al\.?)\s+(?P<year>(?:18|19|20)\d{2}(?:[a-f])?|n\.d\.(?:-[a-z])?)$', re.IGNORECASE),
        re.compile(r'^(?P<source>(?:[^,]+\s*)+(?:&|and)\s*[^,]+)\s+(?P<year>(?:18|19|20)\d{2}(?:[a-f])?)$', re.IGNORECASE)
    ]
    unique_sources = set()
    for cand in segments:
        matched = False
        for pat in patterns:
            m = pat.match(cand)
            if m:
                src = m.group('source')
                src = src.replace(',', '')
                src = re.sub(r'\bet\s*al\.?', '', src, flags=re.IGNORECASE).strip()
                if src:
                    unique_sources.add(src)
                matched = True
                break
        if not matched:
            default = cand.split(',')[0].replace(',', '')
            default = re.sub(r'\bet\s*al\.?', '', default, flags=re.IGNORECASE).strip()
            if default:
                unique_sources.add(default)
    return unique_sources

def search_for_keywords(text):
    import regex as re
    keywords = ["bibliography", "references", "literature cited", "citations", "citations list", "literatures cited"]
    forbidden = ["table of contents", "contents", "list of contents"]
    results = []
    lines = text.splitlines()
    for line in lines[:3]:
        clean_top = re.sub(r'[^\w\s]', '', line).strip().lower()
        for forbidden_word in forbidden:
            if forbidden_word in clean_top:
                return []
    for idx, line in enumerate(lines):
        variants = []
        clean_line = re.sub(r'[^\w\s]', '', line)
        for kw in keywords:
            cap_kw = kw.capitalize()
            up_kw = kw.upper()
            if cap_kw in line:
                if not re.search(rf'\b{re.escape(cap_kw)}\b\s*\d', clean_line):
                    variants.append(cap_kw)
            if up_kw in line and up_kw not in variants:
                if not re.search(rf'\b{re.escape(up_kw)}\b\s*\d', clean_line):
                    variants.append(up_kw)
        if variants:
        #    print("="*50)
        #    print(text)
        #    print("="*50)
           results.append((idx, line.strip()))
    return results

"""
def find_bibliography_pages(page_texts):
    bibliography_pages = {}
    for i, text in enumerate(page_texts):
        results = search_for_keywords(text)
        #print(results)
        if results:
            bibliography_pages[i + 1] = results  # Page numbering starts at 1.
    return bibliography_pages

def _is_header(line: str) -> bool:

    return True

def collect_bibliography_section(page_texts):
    
    For each page where a bibliography keyword appears,
    collect all the lines from that point forward (across pages)
    until you hit another section header or the next biblio‐start page.
    
    Returns: { start_page_number: bibliography_text }
    
    biblio_pages = find_bibliography_pages(page_texts)
    sections = {}
    sorted_starts = sorted(biblio_pages.keys())
    num_pages = len(page_texts)

    for idx, start in enumerate(sorted_starts):
        # determine where to stop: right before the next biblio page, or the end
        stop_page = sorted_starts[idx+1] if idx+1 < len(sorted_starts) else num_pages + 1
        buf = []

        page = start
        # on the first page, start just after the keyword line
        line_idx = biblio_pages[start][0][0] + 1

        while page < stop_page:
            lines = page_texts[page - 1].splitlines()

            # if we're on a subsequent page, check for a new header in the top few lines
            if page != start:
                if any(_is_header(l) for l in lines[:5]):
                    break
                line_idx = 0  # collect from the top if no header

            # collect until we hit another header
            for l in lines[line_idx:]:
                if _is_header(l):
                    page = stop_page  # break outer loop too
                    break
                buf.append(l)
            else:
                page += 1
                continue
            break  # we saw a header, so stop collecting

        sections[start] = "\n".join(buf).strip()

    return sections
"""

def main():
    
    # folder = "test"
    # for every file in os.listdir(folder):
    #     if file.endswith(".pdf"):
    #         pdf_path = os.path.join(folder, file)
    #         print(f"Processing {pdf_path}...")
    #         
    
    pdf_path = "test/CMR-Y3_M46_3-00188271.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file '{pdf_path}' not found.")
        sys.exit(1)
    
    pages_text = convert_pdf(pdf_path)
    
    """
    if bibliography_pages:
        print("Bibliography keywords found on the following pages:")
        for page_num, occurrences in bibliography_pages.items():
            print(f"\nPage {page_num}:")
            for line_number, line_text, variants in occurrences:
                # Display the original line number (adding 1 for human-friendly output).
                print(f"  Line {line_number + 1}: '{line_text}' -> Found keywords: {', '.join(variants)}")
    else:
        print("No bibliography keywords found in the document.")
    
    
    full_text = " ".join(pages_text).replace("\n", " ")
    
    citation_segments = find_citation_segments(full_text)
    inline_sources = process_citations(citation_segments)
    
    #print("Inline sources:", inline_sources)
    
    # remove if less than 2 characters or if its a number
    first_words = set()
    for s in inline_sources:
        parts = s.strip().split()
        if len(parts[0]) < 2 or parts[0].isdigit():
            continue
        if parts:
            first_words.add(parts[0].lower())
        
            
    #for word in first_words:
    #    print(word)    
        
    
    biblio_sections = collect_bibliography_section(pages_text)
    for pg, text in biblio_sections.items():
        print(f"\n--- Bibliography on page {pg} ---")
        print(text)

    
    for i, text in enumerate(pages_text):
        print(f"--- Page {i+1} ---")
         print(text)
        print("=" * 50)
    """
    #output isolated bibliography section
    
    
 
if __name__ == '__main__':
    main()
