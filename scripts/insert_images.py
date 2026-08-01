import os
import re
import glob

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
    if re.match(r"^\s*DR\.?\s*THANH\s*OBGY\s*$", line, re.IGNORECASE):
        return True
    if not line.strip() or line.strip() == '\x0c':
        return True
    if re.match(r"^\s*[\x0c\f]?\s*\d+\s*$", line.strip()):
        return True
    return False

def clean_and_normalize_line(line):
    line = line.replace('\x0c', '').replace('\f', '')
    line = re.sub(r'^\s*[•]\s*', '- ', line)
    line = line.replace('<', '&lt;').replace('>', '&gt;')
    return line.strip()

def get_lessons_map():
    with open('/tmp/pdf_text.txt', 'r') as f:
        text = f.read()
    pages = text.split('\x0c')
    lessons = []
    for idx, page in enumerate(pages):
        for line in page.split('\n'):
            m = re.match(r'^\s*BÀI\s+(\d+)\s*:\s*(.*)', line.strip(), re.IGNORECASE)
            if m:
                num = int(m.group(1))
                title = m.group(2).strip()
                if '....' not in title:
                    lessons.append((num, title, idx + 1))
                    break
    lessons = sorted(lessons)

    lesson_pages = {}
    for i in range(len(lessons)):
        num, title, start_page = lessons[i]
        end_page = lessons[i+1][2] - 1 if i+1 < len(lessons) else len(pages)
        lesson_pages[num] = (start_page, end_page)
    return lesson_pages, pages

def main():
    lesson_pages, pdf_pages = get_lessons_map()
    assets_dir = "/tmp/assets"  # Currently images are in /tmp/assets
    img_files = os.listdir(assets_dir)

    # Let's map MDX files
    mdx_files = glob.glob('docs/**/*.mdx', recursive=True)

    for mdx_path in mdx_files:
        filename = os.path.basename(mdx_path)
        if filename == "index.mdx":
            continue

        m = re.search(r'bai-(\d+)', filename)
        if not m:
            continue
        lesson_num = int(m.group(1))

        if lesson_num not in lesson_pages:
            print(f"Warning: Lesson {lesson_num} ({filename}) not found in PDF lessons map.")
            continue

        start_page, end_page = lesson_pages[lesson_num]
        print(f"Processing {mdx_path} (Lesson {lesson_num}, pages {start_page} to {end_page})")

        with open(mdx_path, 'r') as f:
            mdx_content = f.read()

        mdx_lines = mdx_content.split('\n')

        # We want to identify the alignment of PDF lines to MDX lines
        # For each page p in [start_page, end_page]:
        # we find all MDX line indices that match any non-empty clean line of page p.
        page_mdx_indices = {}
        for p in range(start_page, end_page + 1):
            page_text = pdf_pages[p-1]
            page_lines = [clean_and_normalize_line(l) for l in page_text.split('\n') if not is_ignored_line(l)]

            matched_indices = []
            for mdx_idx, mdx_line in enumerate(mdx_lines):
                cleaned_mdx = mdx_line.strip()
                if not cleaned_mdx:
                    continue
                # Simple substring or exact match
                for pl in page_lines:
                    if pl and (pl in cleaned_mdx or cleaned_mdx in pl):
                        matched_indices.append(mdx_idx)
                        break
            page_mdx_indices[p] = sorted(list(set(matched_indices)))

        # For each page p, let's find the images
        # Images are named img-p-i.png
        insertions = {} # map mdx_idx -> list of image tags to insert after

        last_valid_idx = len(mdx_lines) - 1 # fallback if no match

        for p in range(start_page, end_page + 1):
            # Find images for page p
            p_imgs = sorted([f for f in img_files if f.startswith(f"img-{p}-")])
            if not p_imgs:
                continue

            # If we have images, find where to insert them
            # Let's look at page matching MDX lines
            p_indices = page_mdx_indices.get(p, [])

            # Find any label lines among the matched MDX lines
            label_indices = []
            for idx in p_indices:
                line_text = mdx_lines[idx]
                if any(w in line_text for w in ["Hình", "Lược đồ", "Bảng", "Sơ đồ", "Biểu đồ", "Figure", "Table", "Chart"]):
                    label_indices.append(idx)

            if label_indices:
                # We have labels! Let's match images to labels
                # If we have multiple images and multiple labels, match them in order
                if len(p_imgs) == len(label_indices):
                    for img, idx in zip(p_imgs, label_indices):
                        insertions.setdefault(idx, []).append(img)
                        last_valid_idx = idx
                else:
                    # Otherwise, put all images of this page after the first label
                    idx = label_indices[0]
                    for img in p_imgs:
                        insertions.setdefault(idx, []).append(img)
                    last_valid_idx = idx
            elif p_indices:
                # No labels found, but we have text on this page. Put images at the end of this page's text
                idx = p_indices[-1]
                for img in p_imgs:
                    insertions.setdefault(idx, []).append(img)
                last_valid_idx = idx
            else:
                # No matching lines for this page at all (e.g. page of only diagrams)
                # Put after the last valid insertion point
                for img in p_imgs:
                    insertions.setdefault(last_valid_idx, []).append(img)

        # Now rebuild MDX file with insertions
        new_mdx_lines = []
        for idx, line in enumerate(mdx_lines):
            new_mdx_lines.append(line)
            if idx in insertions:
                for img in insertions[idx]:
                    img_tag = f"\n![{img}](/problem-based-obstetric-ultrasound/assets/{img})\n"
                    new_mdx_lines.append(img_tag)

        with open(mdx_path, 'w') as f_out:
            f_out.write('\n'.join(new_mdx_lines))
        print(f"Updated {mdx_path} with {sum(len(v) for v in insertions.values())} images.")

if __name__ == "__main__":
    main()
