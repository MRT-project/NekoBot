import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "bot.json")
DEFAULT_BADWORDS = [
    # Umum Indonesia
    "anjing", "babi", "bangsat", "goblok", "tolol", "idiot", "brengsek", "kampret",
    "bajingan", "sialan", "edun", "keparat", "sinting", "dongo", "gila", "setan", "iblis",
    "tai", "taik", "kafir", "neraka", "sial", "kurang ajar",

    # Seksual Vulgar
    "kontol", "memek", "jembut", "titit", "peler", "pepek", "puki", "ngentot", "coli",
    "coly", "masturbasi", "penis", "vagina", "kelamin", "sperma", "airmani", "ml", "seks",
    "porn", "porno", "bokep", "tusbol", "doggy", "hotsex", "doggystyle", "vulva", "jerkoff",
    "cum", "boobs", "dildo", "bdsm", "anal", "creampie", "fingering", "hentai", "3some",
    "fetish", "69", "orgasme", "mastur", "desahan", "masturbate", "ejakulasi",

    # Plesetan & typo umum
    "kntl", "kntol", "k0nt0l", "k0ntol", "k*ntol", "mmk", "memk", "jbt", "j3mbut", "ngntt",
    "bgsd", "taek", "pntk", "anjg", "anjrit", "anjay", "b@bi", "asw", "t@i", "p3pek",
    "t1tit", "pel3r", "mem3k", "ng3nt0t", "bok3p", "3jakulasi",

    # Bahasa Inggris
    "fuck", "shit", "bitch", "bastard", "slut", "dick", "jerk", "cunt", "fucker",
    "asshole", "motherfucker", "damn", "wtf", "stupid", "nigger", "nigga", "piss",
    "suck", "blowjob", "whore", "cock", "balls", "scrotum", "butt", "tits", "rapist",
    "raping", "sexslave", "cumdump", "pervert", "incest", "pedo", "pedophile",
    "molest", "slutty", "pornhub", "onlyfans", "xvideos", "xhamster", "xnx", "redtube",

    # Hinaan sosial & diskriminasi
    "cacat", "tololmu", "idiotmu", "autis", "downsynd", "dungu", "debil", "retard", "lemah",
    "miskin", "hina", "disabilitas", "gembel", "tuna", "mental", "bodat", "bencong",
    "banci", "waria", "gila", "edan", "sesat", "jahat", "otak udang",

    # Tambahan kata spam/promo
    "pinjol", "duit cepat", "slot gacor", "judi online", "togel", "kasino", "rtp", "deposit",
    "nft gratis", "crypto", "telegram bot porn", "open bo", "ewean", "psk", "lonte", "perek",
    "pelacur", "bokep viral", "vid hot"
]

def _load_db():
    if not os.path.exists(DB_PATH):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        with open(DB_PATH, "w") as f:
            json.dump({
                "groups": {},
                "badwords": {},
                "warnings": {}
            }, f)

    with open(DB_PATH, "r") as f:
        db = json.load(f)

    # Tambahkan default key jika belum ada
    db.setdefault("groups", {})
    db.setdefault("badwords", {})
    db.setdefault("warnings", {})

    return db

def _save_db(data):
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2)

def setup_db():
    _load_db()

def add_group(group_id, group_name="Unknown"):
    if int(group_id) > 0:
        return

    db = _load_db()
    gid = str(group_id)

    if gid not in db["groups"]:
        print(f"🆕 Tambah grup baru ke database: {group_id} - {group_name}")
        db["groups"][gid] = {
            "group_name": group_name,
            "log_channel_id": None,
            "auto_mute_enabled": False,
            "antilink_enabled": False,
            "antibadword_enabled": True,
            "autoclean_enabled": True,
            "welcome_enabled": True,
            "welcome_text": None,
            "rules_text": None,
            "stats": {"warn": 0, "mute": 0, "ban": 0}
        }

    db["groups"][gid].setdefault("banlist", [])
    db["badwords"][gid] = DEFAULT_BADWORDS.copy()

    _save_db(db)

def delete_group(group_id):
    db = _load_db()
    gid = str(group_id)

    if gid in db["groups"]:
        del db["groups"][gid]

    if gid in db["badwords"]:
        del db["badwords"][gid]

    if gid in db["warnings"]:
        del db["warnings"][gid]

    # ✅ tidak perlu del banlist karena sudah masuk ke groups
    _save_db(db)

def set_log_channel(group_id, channel_id):
    db = _load_db()
    db["groups"][str(group_id)]["log_channel_id"] = channel_id
    _save_db(db)

def get_log_channel(group_id):
    db = _load_db()
    return db["groups"].get(str(group_id), {}).get("log_channel_id")

def enable_auto_mute(group_id, enabled):
    db = _load_db()
    db["groups"][str(group_id)]["auto_mute_enabled"] = enabled
    _save_db(db)

def is_auto_mute_enabled(group_id):
    db = _load_db()
    return db["groups"].get(str(group_id), {}).get("auto_mute_enabled", True)

def set_auto_mute(group_id, enabled: bool):
    db = _load_db()
    db["groups"][str(group_id)]["auto_mute_enabled"] = enabled
    _save_db(db)

def add_badword(group_id, word):
    db = _load_db()
    db["badwords"].setdefault(str(group_id), [])
    if word.lower() not in db["badwords"][str(group_id)]:
        db["badwords"][str(group_id)].append(word.lower())
    _save_db(db)

def get_badwords(group_id):
    db = _load_db()
    return db["badwords"].get(str(group_id), [])

def add_warning(group_id, user_id):
    db = _load_db()
    key = f"{group_id}:{user_id}"
    db["warnings"][key] = db["warnings"].get(key, 0) + 1
    _save_db(db)
    return db["warnings"][key]

def reset_warning(group_id, user_id):
    db = _load_db()
    key = f"{group_id}:{user_id}"
    if key in db["warnings"]:
        del db["warnings"][key]
    _save_db(db)

def set_welcome(group_id, text):
    db = _load_db()
    db["groups"][str(group_id)]["welcome_text"] = text
    _save_db(db)

def get_welcome(group_id):
    db = _load_db()
    return db["groups"].get(str(group_id), {}).get("welcome_text")

def set_rules(group_id, text):
    db = _load_db()
    db["groups"][str(group_id)]["rules_text"] = text
    _save_db(db)

def get_rules(group_id):
    db = _load_db()
    return db["groups"].get(str(group_id), {}).get("rules_text", "Belum ada rules.")

def get_all_group_ids():
    db = _load_db()
    return [int(gid) for gid in db["groups"].keys()]

def set_antilink(group_id, enabled: bool):
    db = _load_db()
    db["groups"][str(group_id)]["antilink_enabled"] = enabled
    _save_db(db)

def is_antilink_enabled(group_id):
    db = _load_db()
    return db["groups"].get(str(group_id), {}).get("antilink_enabled", False)

def set_welcome_enabled(group_id, enabled: bool):
    db = _load_db()
    db["groups"][str(group_id)]["welcome_enabled"] = enabled
    _save_db(db)

def is_welcome_enabled(group_id):
    db = _load_db()
    return db["groups"].get(str(group_id), {}).get("welcome_enabled", True)

def del_badword(group_id, word):
    db = _load_db()
    key = str(group_id)
    word = word.lower()

    if word in db["badwords"].get(key, []):
        db["badwords"][key].remove(word)
        _save_db(db)
        return True
    return False

def set_antibadword(group_id, enabled: bool):
    db = _load_db()
    db["groups"][str(group_id)]["antibadword_enabled"] = enabled
    _save_db(db)

def is_antibadword_enabled(group_id):
    db = _load_db()
    return db["groups"].get(str(group_id), {}).get("antibadword_enabled", True)

def is_autoclean_enabled(group_id):
    db = _load_db()
    return db["groups"].get(str(group_id), {}).get("autoclean_enabled", True)

def set_autoclean(group_id, enabled: bool):
    db = _load_db()
    db["groups"][str(group_id)]["autoclean_enabled"] = enabled
    _save_db(db)

def add_stat(group_id, action: str):
    db = _load_db()
    group = db["groups"].setdefault(str(group_id), {})
    stats = group.setdefault("stats", {"warn": 0, "mute": 0, "ban": 0})
    if action in stats:
        stats[action] += 1
    _save_db(db)

def get_stats(group_id):
    db = _load_db()
    return db["groups"].get(str(group_id), {}).get("stats", {"warn": 0, "mute": 0, "ban": 0})

def get_banlist(group_id):
    db = _load_db()
    return db["groups"].get(str(group_id), {}).get("banlist", [])

def add_to_banlist(group_id, user_id):
    db = _load_db()
    group = db["groups"].setdefault(str(group_id), {})
    banlist = group.setdefault("banlist", [])
    if user_id not in banlist:
        banlist.append(user_id)
    _save_db(db)

def remove_from_banlist(group_id, user_id):
    db = _load_db()
    group = db["groups"].setdefault(str(group_id), {})
    banlist = group.setdefault("banlist", [])
    if user_id in banlist:
        banlist.remove(user_id)
    _save_db(db)

def ensure_group(group_id, title="Unknown"):
    if int(group_id) > 0:
        return

    db = _load_db()
    gid = str(group_id)
    if gid not in db["groups"]:
        add_group(group_id, title)

log_channels = {}

def set_log_channel(gid: int, cid: int):
    log_channels[gid] = cid

def get_log_channel(gid: int):
    return log_channels.get(gid)

def clear_log_channel(gid: int):
    log_channels.pop(gid, None)
    