import pdfplumber
import re


def pdf_dan_malumot_ajrat(pdf_path):
    """
    PDF fayldan umumiy ma'lumotlar va har bir talabaning
    batafsil ma'lumotlarini ajratib oladi.

    Qaytaradi:
        {
            'fan_nomi': str,
            'fan_oqituvchi': str,
            'guruh': str,
            'jami_talabalar': int,
            'baho_5': int,
            'baho_4': int,
            'baho_3': int,
            'kelmadi': int,
            'talabalar': [
                {
                    'fio': str,               # F.I.Sh
                    'reyting_raqam': str,     # Reyting daftarcha raqami
                    'joriy': int,             # J (joriy nazorat)
                    'oraliq': int,            # O (oraliq nazorat)
                    'joriy_oraliq': int,      # J+O
                    'yakuniy': int,           # YN (yakuniy nazorat)
                    'ozlashtirish': int,      # O'zlashtirish ko'rsatkichi
                    'baho': int,              # Baho (3/4/5)
                },
                ...
            ],
            'xato': None | str
        }
    """
    natija = {
        'fan_nomi': '',
        'fan_oqituvchi': '',
        'guruh': '',
        'jami_talabalar': 0,
        'baho_5': 0,
        'baho_4': 0,
        'baho_3': 0,
        'kelmadi': 0,
        'talabalar': [],
        'xato': None
    }

    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ''
            all_tables = []

            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + '\n'
                # Jadval ma'lumotlarini ham ajrat
                tables = page.extract_tables()
                if tables:
                    all_tables.extend(tables)

            if not full_text.strip():
                natija['xato'] = "PDF dan matn ajratib bo'lmadi"
                return natija

            lines = [line.strip() for line in full_text.split('\n') if line.strip()]

            # O'qituvchi pattern — barcha apostrof variantlari
            oqituvchi_pattern = re.compile(
                r"fan\s*o['\u2018\u2019\u02bc`]?qituvchi(?:lar)?(?:i)?\s*:",
                re.IGNORECASE
            )

            for i, line in enumerate(lines):

                # GURUH — faqat raqam formatini olish: 304-25
                guruh_match = re.search(r'[Gg]uruh\s*:\s*(\d{3}-\d{2,3})', line)
                if guruh_match:
                    natija['guruh'] = guruh_match.group(1)

                # FAN NOMI — "Fan:" bilan boshlanadigan qator
                fan_match = re.match(r'^[Ff]an\s*:\s*(.+)', line)
                if fan_match:
                    natija['fan_nomi'] = fan_match.group(1).strip()

                # FAN O'QITUVCHILARI
                if oqituvchi_pattern.search(line):
                    if ':' in line:
                        qism = line.split(':', 1)[1]
                    elif i + 1 < len(lines):
                        qism = lines[i + 1]
                    else:
                        qism = ''

                    qism = qism.strip().strip(',').strip()
                    qismlar = [
                        q.strip().strip(',').strip()
                        for q in qism.split(',')
                        if q.strip().strip(',').strip()
                        and not re.search(
                            r'nazorat|mas.ul|dekan|mudiri|yakuniy',
                            q, re.IGNORECASE
                        )
                    ]
                    if qismlar:
                        natija['fan_oqituvchi'] = ', '.join(qismlar)

                # JAMI TALABALAR VA BAHOLAR
                if re.search(r'jami talabalar', line, re.IGNORECASE):
                    m = re.search(
                        r'jami talabalar\s+soni\s*:\s*(\d+)',
                        line, re.IGNORECASE
                    )
                    if m:
                        natija['jami_talabalar'] = int(m.group(1))

                    m = re.search(
                        r'["\u201c\u201d\u0022]5["\u201c\u201d\u0022]\s*:\s*(\d+)',
                        line
                    )
                    if m:
                        natija['baho_5'] = int(m.group(1))

                    m = re.search(
                        r'["\u201c\u201d\u0022]4["\u201c\u201d\u0022]\s*:\s*(\d+)',
                        line
                    )
                    if m:
                        natija['baho_4'] = int(m.group(1))

                    m = re.search(
                        r'["\u201c\u201d\u0022]3["\u201c\u201d\u0022]\s*:\s*(\d+)',
                        line
                    )
                    if m:
                        natija['baho_3'] = int(m.group(1))

                    m = re.search(
                        r'["\u201c\u201d\u0022][Kk]elmadi["\u201c\u201d\u0022]\s*:\s*(\d+)',
                        line
                    )
                    if m:
                        natija['kelmadi'] = int(m.group(1))

            # ── TALABALAR JADVALI ──────────────────────────────────────────
            # Usul 1: pdfplumber jadvalini ishlatish
            talabalar = _jadvaldan_talabalar_ajrat(all_tables)

            # Usul 2: agar jadval bo'sh bo'lsa, matndan regex bilan ajrat
            if not talabalar:
                talabalar = _matndan_talabalar_ajrat(lines)

            natija['talabalar'] = talabalar

        # Asosiy maydonlar bo'sh bo'lsa xato
        if not natija['fan_nomi'] and not natija['jami_talabalar']:
            natija['xato'] = "Asosiy ma'lumotlar topilmadi"

    except Exception as e:
        natija['xato'] = str(e)

    return natija


# ─────────────────────────────────────────────────────────────────────────────
#  YORDAMCHI FUNKSIYALAR
# ─────────────────────────────────────────────────────────────────────────────

def _int_yoki_nol(qiymat):
    """Xavfsiz int konvertatsiya"""
    try:
        if qiymat is None:
            return 0
        s = str(qiymat).strip()
        if not s or s == 'None':
            return 0
        return int(float(s))
    except (ValueError, TypeError):
        return 0


def _reyting_raqammi(s):
    """
    Reyting daftarcha raqamini tekshiradi.
    Misol: 401251101250, 428251100153
    Odatda 12 xonali raqam.
    """
    s = str(s).strip()
    return bool(re.match(r'^\d{9,15}$', s))


def _fio_mi(s):
    """
    Familiya Ism Sharif ekanligini taxminiy tekshiradi.
    Katta harf bilan boshlanadi va bo'sh joy bor.
    """
    s = str(s).strip()
    # Kamida 2 so'z, katta harf bilan boshlanadi
    return bool(re.match(r'^[A-Z\u0410-\u042F\u04B0\u04B2\u049A\u04AE\u0492\u04E8\u040E\u04BA\u04D8\u04DC][A-Za-z\u0400-\u04FF\u02BC\'-]+(\s+[A-Za-z\u0400-\u04FF\u02BC\'-]+){1,4}$', s))


def _jadvaldan_talabalar_ajrat(all_tables):
    """
    pdfplumber extract_tables() natijasidan talabalar ma'lumotini ajratadi.

    PDF jadval tuzilishi (2 qatorli sarlavha, merged cells):
    Qator 0: ['№', 'Talabaning familiyasi...', 'Reyting...', 'Semestrda toplagan ballar', None, None, 'YN', 'Ozlashtirish', 'Baho', ...]
    Qator 1: [None, None, None, 'ΣJN', 'ΣON', 'ΣJN+ΣON', None, None, None, ...]
    Qator 2+: ma'lumot qatorlari

    Ustun tartibi (indeks):
      0:№  1:FIO  2:Reyting  3:ΣJN  4:ΣON  5:ΣJN+ΣON  6:YN  7:Ozlashtirish  8:Baho  9:imzo
    """
    talabalar = []

    for table in all_tables:
        if not table or len(table) < 3:
            continue

        # Jadval sarlavhasini aniqlash:
        # birinchi qatorda "familiya" yoki "reyting" so'zi bor
        header_row0_idx = None
        for idx, row in enumerate(table):
            if not row:
                continue
            row_text = ' '.join(str(c or '') for c in row).lower()
            if 'familiya' in row_text or 'reyting' in row_text:
                header_row0_idx = idx
                break

        # Sarlavha topilmadimi? — keyingi sahifa jadvali (sarlavhasiz davom)
        if header_row0_idx is None:
            first_cell = str(table[0][0] or '').strip() if table and table[0] else ''
            if re.match(r'^\d{1,3}$', first_cell):
                # Sarlavhasiz davom jadvali — standart ustun pozitsiyalari
                col_idx_std = {'fio':1,'reyting':2,'joriy':3,'oraliq':4,'jo':5,'yn':6,'ozl':7,'baho':8}
                for row in table:
                    if not row or all(c is None or str(c).strip()=='' for c in row): continue
                    fc = str(row[0] or '').strip()
                    if not re.match(r"^\d{1,3}$", fc): continue
                    def sg(key):
                        i = col_idx_std.get(key)
                        return row[i] if i is not None and i < len(row) else None
                    fio = re.sub(r"\s*\n\s*", ' ', str(sg("fio") or '')).strip()
                    if not fio: continue
                    j = _int_yoki_nol(sg("joriy")); o = _int_yoki_nol(sg("oraliq"))
                    jo = _int_yoki_nol(sg("jo")); yn = _int_yoki_nol(sg("yn"))
                    if jo==0 and (j>0 or o>0): jo = j+o
                    talabalar.append({"fio":fio,"reyting_raqam":str(sg("reyting") or '').strip(),
                        "joriy":j,"oraliq":o,"joriy_oraliq":jo,"yakuniy":yn,
                        "ozlashtirish":_int_yoki_nol(sg("ozl")),"baho":_int_yoki_nol(sg("baho"))})
                continue
            else:
                continue

        # Ikkinchi sarlavha qatori (ΣJN, ΣON, ΣJN+ΣON) — ixtiyoriy
        # Ma'lumot qatorlari header_row0_idx + 1 yoki + 2 dan boshlanadi
        # Agar keyingi qatorda raqam bo'lmasa u ham sarlavha
        data_start = header_row0_idx + 1
        if data_start < len(table):
            next_row = table[data_start]
            if next_row:
                first_cell = str(next_row[0] or '').strip()
                if not re.match(r'^\d{1,3}$', first_cell):
                    # ΣJN qatori, o'tkazib yubor
                    data_start += 1

        # Ustun indekslarini sarlavhadan aniqlash
        # Birinchi sarlavha qatori va ikkinchi (ΣJN satri) ni birlashtirish
        h0 = table[header_row0_idx]
        h1 = table[header_row0_idx + 1] if (header_row0_idx + 1 < data_start) else [None] * len(h0)

        # Barcha ustun nomlarini birlashtirish (2-qatordan ΣJN, ΣON, ΣJN+ΣON olish)
        merged_header = []
        for ci in range(len(h0)):
            top = str(h0[ci] or '').strip()
            bot = str(h1[ci] if ci < len(h1) else '').strip()
            # Ikkinchi qatorda aniq nom bo'lsa uni afzal ko'rish
            if bot and bot not in ('None', ''):
                merged_header.append(bot)
            else:
                merged_header.append(top)

        # Ustun indekslarini aniqlash
        col_idx = {
            'fio': None,
            'reyting': None,
            'joriy': None,
            'oraliq': None,
            'jo': None,
            'yn': None,
            'ozl': None,
            'baho': None,
        }

        for ci, ct in enumerate(merged_header):
            ct_low = ct.lower()
            if re.search(r'familiya|ism|sharif|talaba', ct_low):
                col_idx['fio'] = ci
            elif re.search(r'reyting|daftar', ct_low):
                col_idx['reyting'] = ci
            elif re.search(r'σjn\s*\+|∑jn\s*\+|jn\+|j\+o', ct_low):
                col_idx['jo'] = ci
            elif re.search(r'σjn|∑jn', ct_low):
                col_idx['joriy'] = ci
            elif re.search(r'σon|∑on', ct_low):
                col_idx['oraliq'] = ci
            elif re.search(r'yakuniy|^yn$', ct_low):
                col_idx['yn'] = ci
            elif re.search(r"o.zlashtirish|ozlashtirish|ko.rsatk", ct_low):
                col_idx['ozl'] = ci
            elif re.search(r'^baho$', ct_low):
                col_idx['baho'] = ci

        # Agar ustunlar topilmagan bo'lsa, pozitsiya bo'yicha taxminiy belgilash
        # (standart PDF jadval: 0:№ 1:FIO 2:Reyting 3:JN 4:ON 5:JN+ON 6:YN 7:Ozl 8:Baho)
        if col_idx['fio'] is None:
            col_idx['fio'] = 1
        if col_idx['reyting'] is None:
            col_idx['reyting'] = 2
        if col_idx['joriy'] is None:
            col_idx['joriy'] = 3
        if col_idx['oraliq'] is None:
            col_idx['oraliq'] = 4
        if col_idx['jo'] is None:
            col_idx['jo'] = 5
        if col_idx['yn'] is None:
            col_idx['yn'] = 6
        if col_idx['ozl'] is None:
            col_idx['ozl'] = 7
        if col_idx['baho'] is None:
            col_idx['baho'] = 8

        # Ma'lumot qatorlarini o'qish
        for row in table[data_start:]:
            if not row or all(c is None or str(c).strip() == '' for c in row):
                continue

            # Birinchi ustun raqam bo'lishi kerak (1, 2, 3...)
            first_cell = str(row[0] or '').strip()
            if not re.match(r'^\d{1,3}$', first_cell):
                continue

            def safe_get(key):
                idx = col_idx.get(key)
                if idx is not None and idx < len(row):
                    return row[idx]
                return None

            # FIO — yangi qatorlarni bo'shliq bilan almashtirish
            fio_raw = str(safe_get('fio') or '').strip()
            fio = re.sub(r'\s*\n\s*', ' ', fio_raw).strip()

            if not fio:
                continue

            reyting = str(safe_get('reyting') or '').strip()

            joriy = _int_yoki_nol(safe_get('joriy'))
            oraliq = _int_yoki_nol(safe_get('oraliq'))
            jo = _int_yoki_nol(safe_get('jo'))
            yn = _int_yoki_nol(safe_get('yn'))
            ozl = _int_yoki_nol(safe_get('ozl'))
            baho = _int_yoki_nol(safe_get('baho'))

            # J+O ni hisoblash agar yo'q bo'lsa
            if jo == 0 and (joriy > 0 or oraliq > 0):
                jo = joriy + oraliq

            talabalar.append({
                'fio': fio,
                'reyting_raqam': reyting,
                'joriy': joriy,
                'oraliq': oraliq,
                'joriy_oraliq': jo,
                'yakuniy': yn,
                'ozlashtirish': ozl,
                'baho': baho,
            })

    return talabalar


def _matndan_talabalar_ajrat(lines):
    """
    Jadval ajratilmagan holda matn qatorlaridan talabalar ma'lumotini regex bilan ajratadi.

    Qator formati (matndan):
    1 BOLBEKOVA ZAHRO BOBOMUROD QIZI 401251101250 42 0 42 38 80 4
    """
    talabalar = []

    # Pattern: raqam + FIO (bir nechta so'z, katta harflar) + reyting (9-15 xona) + raqamlar + baho
    # Misol: "1 BOLBEKOVA ZAHRO BOBOMUROD QIZI 401251101250 42 0 42 38 80 4"
    talaba_pattern = re.compile(
        r'^(\d{1,3})\s+'                          # T/R
        r'([A-Z\u0410-\u042F][A-Z\u0410-\u042F\u04B0\u04B2\u02BC\'-]+'  # Familiya
        r'(?:\s+[A-Z\u0410-\u042F][A-Z\u0410-\u042F\u04B0\u04B2\u02BC\'-]+){1,4})'  # Ism Sharif
        r'\s+(\d{9,15})'                          # Reyting raqam
        r'\s+(\d+)'                               # ΣJN (joriy)
        r'\s+(\d+)'                               # ΣON (oraliq)
        r'\s+(\d+)'                               # ΣJN+ΣON
        r'\s+(\d+)'                               # YN
        r'\s+(\d+)'                               # O'zlashtirish
        r'\s+([2-5])'                             # Baho
        r'\s*$'
    )

    for line in lines:
        m = talaba_pattern.match(line)
        if m:
            joriy = _int_yoki_nol(m.group(4))
            oraliq = _int_yoki_nol(m.group(5))
            jo = _int_yoki_nol(m.group(6))
            yn = _int_yoki_nol(m.group(7))
            ozl = _int_yoki_nol(m.group(8))
            baho = _int_yoki_nol(m.group(9))

            if jo == 0 and (joriy > 0 or oraliq > 0):
                jo = joriy + oraliq

            talabalar.append({
                'fio': m.group(2).strip(),
                'reyting_raqam': m.group(3).strip(),
                'joriy': joriy,
                'oraliq': oraliq,
                'joriy_oraliq': jo,
                'yakuniy': yn,
                'ozlashtirish': ozl,
                'baho': baho,
            })

    return talabalar