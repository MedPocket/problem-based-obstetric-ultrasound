import os
import re
import unicodedata

def slugify(text):
    text = text.lower()
    replacements = {
        'à':'a','á':'a','ả':'a','ã':'a','ạ':'a','ă':'a','ằ':'a','ắ':'a','ẳ':'a','ẵ':'a','ặ':'a','â':'a','ầ':'a','ấ':'a','ẩ':'a','ẫ':'a','ậ':'a',
        'đ':'d',
        'è':'e','é':'e','ẻ':'e','ẽ':'e','ẹ':'e','ê':'e','ề':'e','ế':'e','ể':'e','ễ':'e','ệ':'e',
        'ì':'i','í':'i','ỉ':'i','ĩ':'i','ị':'i',
        'ò':'o','ó':'o','ỏ':'o','õ':'o','ọ':'o','ô':'o','ồ':'o','ố':'o','ổ':'o','ỗ':'o','ộ':'o','ơ':'o','ờ':'o','ớ':'o','ở':'o','ỡ':'o','ợ':'o',
        'ù':'u','ú':'u','ủ':'u','ũ':'u','ụ':'u','ư':'u','ừ':'u','ứ':'u','ử':'u','ữ':'u','ự':'u',
        'ỳ':'y','ý':'y','ỷ':'y','ỹ':'y','ỵ':'y'
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text).strip('-')
    return text

def is_ignored_line(line):
    # Match DR.THANH OBGY or similar
    if re.match(r"^\s*DR\.?\s*THANH\s*OBGY\s*$", line, re.IGNORECASE):
        return True
    # Match empty or form feed only
    if not line.strip() or line.strip() == '\x0c':
        return True
    # Match page numbers (only digits, possibly with form feed)
    if re.match(r"^\s*[\x0c\f]?\s*\d+\s*$", line.strip()):
        return True
    return False

def clean_and_normalize_line(line):
    # Remove form feed characters
    line = line.replace('\x0c', '').replace('\f', '')
    # Normalize bullet points (, •, o) at the beginning of the line
    line = re.sub(r'^\s*[•]\s*', '- ', line)
    # Replace < and > with HTML entities to avoid JSX parsing issues in MDX
    line = line.replace('<', '&lt;').replace('>', '&gt;')
    return line

def extract_description(lines):
    desc_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Skip headers, lists, and tables
        if stripped.startswith('#') or stripped.startswith('-') or stripped.startswith('*') or stripped.startswith('|'):
            continue
        # Clean markdown symbols, HTML tags, and quotes for description
        cleaned = re.sub(r'[*_`#"\\]', '', stripped)
        desc_lines.append(cleaned)
        if len(' '.join(desc_lines)) > 150:
            break
    desc = ' '.join(desc_lines)
    if len(desc) > 155:
        desc = desc[:152] + '...'
    return desc or "Tài liệu chi tiết về siêu âm sản phụ khoa lâm sàng."

chapters_config = [
    {
        "dir": "03-he-than-kinh-dau-so",
        "title": "Hệ thần kinh & Đầu sọ",
        "icon": "brain",
        "lessons": [1, 2, 3, 4]
    },
    {
        "dir": "04-vung-mat",
        "title": "Vùng mặt",
        "icon": "smile",
        "lessons": [5, 6, 7, 8]
    },
    {
        "dir": "05-long-nguc-tim-mach",
        "title": "Lồng ngực & Tim mạch",
        "icon": "heart",
        "lessons": [9, 10, 11, 12, 13, 14, 15]
    },
    {
        "dir": "06-tieu-hoa-thanh-bung",
        "title": "Hệ tiêu hóa & Thành bụng",
        "icon": "utensils",
        "lessons": [16, 17, 18]
    },
    {
        "dir": "07-tiet-nieu",
        "title": "Hệ tiết niệu",
        "icon": "droplet",
        "lessons": [19, 20, 21, 22, 23]
    },
    {
        "dir": "08-co-xuong-khop",
        "title": "Hệ cơ xương khớp",
        "icon": "accessibility",
        "lessons": [24, 25, 26, 27, 28]
    },
    {
        "dir": "09-dau-co-gay",
        "title": "Cổ & Gáy",
        "icon": "user",
        "lessons": [29, 30]
    },
    {
        "dir": "10-banh-nhau-day-ron-nuoc-oi",
        "title": "Bánh nhau, Dây rốn & Nước ối",
        "icon": "droplets",
        "lessons": [31, 32, 33, 34, 35, 36]
    },
    {
        "dir": "11-benh-ly-thai-nhi-da-thai",
        "title": "Bệnh lý thai nhi & Đa thai",
        "icon": "users",
        "lessons": [37, 38, 39]
    }
]

def main():
    with open("public/Problem-based-obstetric-ultrasound_tieng-Viet.md", "r") as f:
        lines = f.readlines()

    # Step 1: Find actual start index of each lesson
    lessons = []
    for idx, line in enumerate(lines):
        m = re.match(r"^BÀI\s+(\d+)\s*:\s*(.*)", line.strip())
        if m:
            num = int(m.group(1))
            title = m.group(2).strip()
            if "...." not in title:
                lessons.append((num, title, idx))

    print(f"Detected {len(lessons)} actual lessons.")

    # Create directories and store lesson pages per chapter for meta.ts
    chapter_pages = {cfg["dir"]: [] for cfg in chapters_config}

    for i in range(len(lessons)):
        num, title, idx = lessons[i]
        start = idx
        end = lessons[i+1][2] if i+1 < len(lessons) else len(lines)

        # Extract lesson content lines
        lesson_lines = lines[start:end]
        cleaned_lines = []
        for line in lesson_lines:
            if is_ignored_line(line):
                continue
            cleaned_lines.append(clean_and_normalize_line(line))

        # Re-verify the title in first line and clean it
        if cleaned_lines and cleaned_lines[0].strip().startswith("BÀI"):
            # We can strip it because we will add it via frontmatter or title header
            title_line = cleaned_lines.pop(0)

        # Strip remaining empty lines at top and bottom
        while cleaned_lines and not cleaned_lines[0].strip():
            cleaned_lines.pop(0)
        while cleaned_lines and not cleaned_lines[-1].strip():
            cleaned_lines.pop()

        # Find which chapter config this lesson belongs to
        target_cfg = None
        for cfg in chapters_config:
            if num in cfg["lessons"]:
                target_cfg = cfg
                break

        if not target_cfg:
            print(f"Warning: Lesson {num} ({title}) not mapped to any chapter.")
            continue

        # Slugify
        slug = f"bai-{num:02d}-{slugify(title)}"
        chapter_pages[target_cfg["dir"]].append(slug)

        # Generate description
        desc = extract_description(cleaned_lines)

        # Format lesson content
        content_str = "\n".join(cleaned_lines)

        # Create frontmatter
        mdx_content = f"""---
title: "Bài {num:d}: {title}"
description: "{desc}"
---

{content_str}
"""

        # Write lesson file
        target_dir = os.path.join("docs", target_cfg["dir"])
        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, f"{slug}.mdx")
        with open(file_path, "w") as f_out:
            f_out.write(mdx_content)
        print(f"Wrote {file_path}")

    # Step 2: Write meta.ts for each chapter
    for cfg in chapters_config:
        target_dir = os.path.join("docs", cfg["dir"])
        os.makedirs(target_dir, exist_ok=True)
        pages_list = chapter_pages[cfg["dir"]]

        pages_str = ",\n    ".join(f'"{p}"' for p in pages_list)
        meta_content = f"""import {{ defineMeta }} from "blume";

export default defineMeta({{
  title: "{cfg['title']}",
  icon: "{cfg['icon']}",
  order: {chapters_config.index(cfg) + 3},
  collapsed: true,
  pages: [
    {pages_str}
  ],
}});
"""
        meta_path = os.path.join(target_dir, "meta.ts")
        with open(meta_path, "w") as f_meta:
            f_meta.write(meta_content)
        print(f"Wrote {meta_path}")

if __name__ == "__main__":
    main()
