import pdfplumber
import re


def pdf_dan_malumot_ajrat(pdf_path):
    natija = {
        'fan_nomi': '',
        'fan_oqituvchi': '',
        'guruh': '',
        'jami_talabalar': 0,
        'baho_5': 0,
        'baho_4': 0,
        'baho_3': 0,
        'kelmadi': 0,
        'xato': None
    }

    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ''
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + '\n'

            if not full_text.strip():
                natija['xato'] = "PDF dan matn ajratib bo'lmadi"
                return natija

            # DEBUG — o'qituvchi qatorini toping
            for line in full_text.split('\n'):
                if 'qituvchi' in line.lower():
                    print(f"TOPILDI: '{repr(line)}'")

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

                    # Tozalash
                    qism = qism.strip().strip(',').strip()

                    # Vergul bilan ajratilgan bo'lsa, har birini tozala
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
                # "Jami talabalar soni: 26, shundan, "5": 2, "4": 12, "3": 12, "2": 0, "Kelmadi": 0"
                if re.search(r'jami talabalar', line, re.IGNORECASE):

                    # Jami soni
                    m = re.search(
                        r'jami talabalar\s+soni\s*:\s*(\d+)',
                        line, re.IGNORECASE
                    )
                    if m:
                        natija['jami_talabalar'] = int(m.group(1))

                    # "5" — har xil qo'shtirnoq variantlari
                    m = re.search(
                        r'["\u201c\u201d\u0022]5["\u201c\u201d\u0022]\s*:\s*(\d+)',
                        line
                    )
                    if m:
                        natija['baho_5'] = int(m.group(1))

                    # "4"
                    m = re.search(
                        r'["\u201c\u201d\u0022]4["\u201c\u201d\u0022]\s*:\s*(\d+)',
                        line
                    )
                    if m:
                        natija['baho_4'] = int(m.group(1))

                    # "3"
                    m = re.search(
                        r'["\u201c\u201d\u0022]3["\u201c\u201d\u0022]\s*:\s*(\d+)',
                        line
                    )
                    if m:
                        natija['baho_3'] = int(m.group(1))

                    # Kelmadi
                    m = re.search(
                        r'["\u201c\u201d\u0022][Kk]elmadi["\u201c\u201d\u0022]\s*:\s*(\d+)',
                        line
                    )
                    if m:
                        natija['kelmadi'] = int(m.group(1))

        # Asosiy maydonlar bo'sh bo'lsa xato
        if not natija['fan_nomi'] and not natija['jami_talabalar']:
            natija['xato'] = "Asosiy ma'lumotlar topilmadi"

    except Exception as e:
        natija['xato'] = str(e)

    return natija