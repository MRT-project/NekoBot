import re

def flexible_pattern(word: str) -> str:
    """
    Buat pola fleksibel dari kata badword.
    Cocok juga untuk variasi seperti: k*0n.t0l, m3m3k, dll.
    """
    translation = {
        "a": "a@4", "b": "b8", "c": "c(", "e": "e3", "g": "g9", "h": "h",
        "i": "i1!|", "k": "k", "l": "l1|!", "m": "m", "n": "n", "o": "o0",
        "p": "p", "s": "s5$", "t": "t7+", "u": "u", "v": "v", "w": "w",
        "x": "x", "y": "y", "z": "z2"
    }

    parts = []
    for char in word.lower():
        if char in translation:
            safe_chars = re.escape(translation[char])
            parts.append(f"[{safe_chars}]")
        else:
            parts.append(re.escape(char))

    # Gabungkan dengan fleksibel antar karakter (boleh ada simbol di antara huruf)
    return r"[\W_]*".join(parts)


def build_badword_regex(badwords: list[str]) -> re.Pattern:
    """
    Gabungkan semua pola menjadi satu regex besar.
    Lewati kata kosong dan hindari error dari regex kompleks.
    """
    patterns = []
    for word in badwords:
        word = word.strip()
        if word:
            try:
                pattern = flexible_pattern(word)
                re.compile(pattern)  # test compile
                patterns.append(pattern)
            except re.error as e:
                print(f"⚠️ Badword '{word}' skipped: invalid pattern ({e})")

    if not patterns:
        return re.compile(r"(?!x)x")  # always false

    return re.compile(r"(?:{})".format("|".join(patterns)), re.IGNORECASE)
