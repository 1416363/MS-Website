# -*- coding: utf-8 -*-
"""Снимок таблицы карточек.
Вписывает в страницу нынешнее содержимое таблицы, чтобы при открытии
сразу показывался верный текст, а не прежний. Запускается по расписанию."""
import urllib.request, urllib.parse, csv, io, html, re, pathlib

ТАБЛИЦА = "1QQBUnCOFtdYd6_3szeFolWkJfjN1x6i2aJqDSlzH6fg"
ЛИСТ = "Лист1"
ЦВЕТА = [("#1a73e8","#e4eefc","#f4f8fe"), ("#188038","#e3f0e7","#f3f9f5"),
         ("#a50e0e","#f4e2e2","#faf3f3"), ("#b26a00","#f6ebda","#fbf6ef"),
         ("#00695c","#dfeeeb","#f1f8f7"), ("#7b1fa2","#efe4f4","#f8f4fa")]

url = (f"https://docs.google.com/spreadsheets/d/{ТАБЛИЦА}"
       f"/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(ЛИСТ)}")
строки = list(csv.reader(io.StringIO(
    urllib.request.urlopen(url, timeout=25).read().decode("utf-8"))))

разделы, поимени = [], {}
for с in строки[1:]:
    if len(с) < 4 or not с[0].strip() or not с[2].strip():
        continue
    имя = с[0].strip()
    if имя not in поимени:
        поимени[имя] = {"имя": имя, "карточки": []}
        разделы.append(поимени[имя])
    поимени[имя]["карточки"].append({
        "номер": с[1].strip(),
        "заголовок": с[2].strip(),
        "строки": [re.sub(r"^\s*[-–—•]\s*", "", л).strip()
                   for л in с[3].split("\n") if л.strip()]})

def щ(t): return html.escape(t, quote=False)


def жирным(t):
    """Слова между звёздочками — жирным. Звёздочки убираются."""
    return re.sub(r'\*([^*\n]+)\*', r'<b>\1</b>', щ(t))

вкладки, блоки = [], []
for и, р in enumerate(разделы):
    c, soft, pale = ЦВЕТА[и % len(ЦВЕТА)]
    стиль = f"--c:{c}; --soft:{soft}; --pale:{pale}"
    вкладки.append(f'    <a class="tab" href="#s{и+1}" style="{стиль}">{щ(р["имя"])}</a>')
    пункты = []
    for к in р["карточки"]:
        сп = "".join(f"\n            <li>{жирным(л)}</li>" for л in к["строки"])
        пункты.append(
            f'        <li class="card">\n'
            f'          <h3>{жирным(к["заголовок"])}</h3>\n'
            f'          <ul class="card-list">{сп}\n          </ul>\n'
            f'          <span class="card-num">{щ(к["номер"])}</span>\n'
            f'        </li>')
    блоки.append(
        f'  <section class="block" id="s{и+1}" style="{стиль}">\n'
        f'      <div class="block-head">\n'
        f'        <h2><span class="num">{и+1}</span>{щ(р["имя"])}</h2>\n'
        f'      </div>\n'
        f'      <ol class="items">\n' + "\n".join(пункты) + "\n      </ol>\n"
        f'  </section>')

п = pathlib.Path("ms-value4.html")
т = п.read_text(encoding="utf-8")

# таблички выгоды сохраняем: они живут в странице, а не в таблице
таблички = dict(re.findall(
    r'<h2><span class="num">\d+</span>([^<]+)</h2>\s*(<div class="gain">.*?</div>)', т, re.S))

новые_блоки = []
for б in блоки:
    имя = re.search(r'</span>([^<]+)</h2>', б).group(1)
    if имя in таблички:
        б = б.replace("</h2>\n      </div>", "</h2>\n        " + таблички[имя] + "\n      </div>")
    новые_блоки.append(б)

т = re.sub(r'(<div class="tabs">\n).*?(\n  </div>)',
           lambda м: м.group(1) + "\n".join(вкладки) + м.group(2), т, count=1, flags=re.S)
начало = т.index('<section class="block"')
начало = т.rindex("\n", 0, начало) + 1
конец = т.index('  <section class="final">')
т = т[:начало] + "\n\n".join(новые_блоки) + "\n\n" + т[конец:]

п.write_text(т, encoding="utf-8")
print(f"вписано: разделов {len(разделы)}, карточек {sum(len(р['карточки']) for р in разделы)}")
print("табличек выгоды сохранено:", sum(1 for б in новые_блоки if 'class="gain"' in б))
