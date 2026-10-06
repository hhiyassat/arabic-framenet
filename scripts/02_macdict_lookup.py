import csv, ctypes, pathlib, re
CF = ctypes.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
CS = ctypes.CDLL('/System/Library/Frameworks/CoreServices.framework/CoreServices')
class CFRange(ctypes.Structure): _fields_ = [('loc', ctypes.c_long), ('len', ctypes.c_long)]
UTF8 = 0x08000100
CF.CFStringCreateWithCString.restype = ctypes.c_void_p
CF.CFStringCreateWithCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint32]
CF.CFStringGetCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_long, ctypes.c_uint32]
CF.CFSetGetCount.argtypes = [ctypes.c_void_p]; CF.CFSetGetCount.restype = ctypes.c_long
CF.CFSetGetValues.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
CF.CFRelease.argtypes = [ctypes.c_void_p]
CS.DCSCopyAvailableDictionaries.restype = ctypes.c_void_p
CS.DCSDictionaryGetName.restype = ctypes.c_void_p; CS.DCSDictionaryGetName.argtypes = [ctypes.c_void_p]
CS.DCSCopyTextDefinition.restype = ctypes.c_void_p
CS.DCSCopyTextDefinition.argtypes = [ctypes.c_void_p, ctypes.c_void_p, CFRange]

def cfstr(s): return CF.CFStringCreateWithCString(None, s.encode('utf-8'), UTF8)
def pystr(ref):
    if not ref: return ''
    buf = ctypes.create_string_buffer(65536)
    return buf.value.decode('utf-8', 'replace') if CF.CFStringGetCString(ref, buf, 65536, UTF8) else ''

dset = CS.DCSCopyAvailableDictionaries()
n = CF.CFSetGetCount(dset); arr = (ctypes.c_void_p * n)(); CF.CFSetGetValues(dset, arr)
names = {pystr(CS.DCSDictionaryGetName(d)): d for d in arr}
print('available_dictionaries =', sorted(names))
AR = [d for nm, d in names.items() if 'Arabic' in nm]
assert len(AR) == 1, 'Arabic dictionary not found by name'
AR = AR[0]

def lookup(term):
    s = cfstr(term); r = CS.DCSCopyTextDefinition(AR, s, CFRange(0, len(term)))
    out = pystr(r); CF.CFRelease(s)
    if r: CF.CFRelease(r)
    return out.replace('\n', ' ')[:300]

GL = pathlib.Path(__file__).resolve().parents[1] / '01_glossary' / 'fe_glossary.tsv'
rows = list(csv.DictReader(open(GL, encoding='utf-8'), delimiter='\t'))
hit = ar_hit = 0
for r in rows:
    q = r['fe_name'].replace('_', ' ').lower()
    d = lookup(q)
    if not d and ' ' in q:
        d = lookup(q.split()[-1]); d = d and 'PARTIAL(last word): ' + d
    r['mac_dict_candidate'] = d
    if d: hit += 1
    if re.search(r'[\u0600-\u06FF]', d): ar_hit += 1
with open(GL, 'w', encoding='utf-8', newline='') as w:
    wr = csv.DictWriter(w, fieldnames=rows[0].keys(), delimiter='\t'); wr.writeheader(); wr.writerows(rows)
print(f'names={len(rows)} hits={hit} hits_arabic={ar_hit} hit_rate_arabic={ar_hit/len(rows):.3f}  # MEASURED')
