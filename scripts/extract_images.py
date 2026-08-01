import fitz
import os

def extract_images():
    pdf_path = "public/Problem-based-obstetric-ultrasound_tieng-Viet.pdf"
    output_dir = "public/assets"
    os.makedirs(output_dir, exist_ok=True)

    doc = fitz.open(pdf_path)
    print(f"Opened PDF with {len(doc)} pages.")

    extracted_count = 0
    for page_num in range(1, len(doc) + 1):
        page = doc[page_num - 1]
        image_list = page.get_images(full=True)
        img_idx = 1
        for img_info in image_list:
            xref = img_info[0]
            width = img_info[2]
            height = img_info[3]

            # Skip very small images (e.g. icons, headers, footers)
            if width < 50 or height < 50:
                continue

            try:
                pix = fitz.Pixmap(doc, xref)
                # Skip if it has no colorspace (likely a mask)
                if pix.colorspace is None:
                    continue

                filename = f"img-{page_num}-{img_idx}.png"
                filepath = os.path.join(output_dir, filename)

                # Save as PNG
                pix.save(filepath)
                print(f"Extracted Page {page_num} Image {img_idx}: {filepath} ({width}x{height})")
                img_idx += 1
                extracted_count += 1
            except Exception as e:
                print(f"Error extracting image on Page {page_num}, xref {xref}: {e}")

    print(f"Total extracted: {extracted_count}")

if __name__ == "__main__":
    extract_images()
