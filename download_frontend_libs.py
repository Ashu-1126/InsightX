import os
import urllib.request


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


LIBS = [
    ("jspdf.umd.min.js", "https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"),
    ("html2canvas.min.js", "https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"),
]


def main():
    libs_dir = os.path.join(os.path.dirname(__file__), "Frontend", "functions", "libs")
    ensure_dir(libs_dir)
    for filename, url in LIBS:
        dest = os.path.join(libs_dir, filename)
        print(f"Downloading {url} -> {dest}")
        urllib.request.urlretrieve(url, dest)
        print(f"Saved: {dest}")


if __name__ == "__main__":
    main()
