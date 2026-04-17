import struct
import os
import json

def get_pack_map(path):
    with open(path, 'rb') as f:
        header = f.read(4)
        total_files, sub_packs = struct.unpack('<HH', header)
        f.read(sub_packs * 2)
        num_offsets = total_files + 1
        offsets = []
        for _ in range(num_offsets):
            offsets.append(struct.unpack('<I', f.read(4))[0])
        pack_map = {}
        for i, start in enumerate(offsets[:-1]):
            f.seek(start)
            f.read(1) # flag
            pack_id = struct.unpack('B', f.read(1))[0]
            pack_map[pack_id] = (start, offsets[i+1])
        return pack_map

def parse_string_pack(path, start, end):
    with open(path, 'rb') as f:
        f.seek(start)
        data = f.read(end-start)
        num = struct.unpack('<I', data[2:6])[0]
        offs = [struct.unpack('<I', data[6+i*4:10+i*4])[0] for i in range(num+1)]
        base = 6 + (num+1)*4 - 4
        res = []
        for i in range(num):
            try:
                s_data = data[base+offs[i]:base+offs[i+1]]
                txt = s_data.decode('utf-8', errors='ignore').split('\x00')[0]
                res.append(txt)
            except:
                res.append("")
        return res

def parse_tabular_data(path, sub_idx):
    with open(path, 'rb') as f:
        total, sub = struct.unpack('<HH', f.read(4))
        f.read(sub * 2)
        offs = [struct.unpack('<I', f.read(4))[0] for _ in range(total+1)]
        f.seek(offs[sub_idx])
        d = f.read(offs[sub_idx+1] - offs[sub_idx])[1:]
        rows, cols = struct.unpack('<II', d[:8])
        ts = d[8:8+cols]; ptr = 8+cols
        table = []
        for r in range(rows):
            row = []
            for c in range(cols):
                t = ts[c]
                if t==1: v=struct.unpack('b', d[ptr:ptr+1])[0]; ptr += 1
                elif t==2: v=struct.unpack('<h', d[ptr:ptr+2])[0]; ptr += 2
                elif t==4: v=struct.unpack('<i', d[ptr:ptr+4])[0]; ptr += 4
                else: v=0
                row.append(v)
            table.append(row)
        return table

asset_13 = r'resources\assets\800x480\13'
asset_en = r'resources\assets\800x480\EN'

print("Initializing string packs...")
pack_map = get_pack_map(asset_en)
all_strings = {}
for pid, (s, e) in pack_map.items():
    pk = parse_string_pack(asset_en, s, e)
    for idx, t in enumerate(pk):
        all_strings[(pid << 10) | idx] = t

print("Extracting quest table...")
quest_table = parse_tabular_data(asset_13, 6)

# Pre-calculate quest names
quest_names_ids = {}
for i, row in enumerate(quest_table):
    if i < 304:
        quest_names_ids[i] = row[3] - 1

library = []
for i, row in enumerate(quest_table):
    if i >= 304: break
    
    q_type = row[12]
    
    # Header Mapping
    name_sid = row[3] - 1
    quest_name = all_strings.get(name_sid, f"Quest_{row[1]}")
    if not quest_name or quest_name.startswith("What's this?"):
        quest_name = all_strings.get(row[11], f"Quest_{row[1]}")

    # The TRUE quantity columns are 18, 24, 30
    if q_type == 15:
        text_box = all_strings.get(row[6], "")
        description = all_strings.get(row[3], "")
        obj_slots = [(row[11], row[18]), (row[16], row[24]), (row[22], row[30])]
    else:
        text_box = all_strings.get(row[3], "")
        description = all_strings.get(row[5], "")
        obj_slots = [(row[6], row[18]), (row[16], row[24]), (row[22], row[30])]

    # Process Objectives
    objectives = []
    next_name_sid = quest_names_ids.get(i+1, -999)
    for oid, count in obj_slots:
        if oid != 0 and oid != -1 and oid != next_name_sid and oid in all_strings:
            s_val = all_strings[oid].strip()
            if s_val and not s_val.startswith("What's this?"):
                # Clean up counts: sometimes game data has large IDs in these slots, 
                # but valid quest counts are usually small 1-99.
                final_count = count if 0 < count < 1000 else 1
                objectives.append({
                    "text": s_val,
                    "count": final_count
                })

    # Prerequisite logic
    prereq_idx = row[13]
    prereq_id = quest_table[prereq_idx][1] if 0 <= prereq_idx < len(quest_table) else None

    library.append({
        "order": i,
        "internal_id": row[1],
        "quest_name": quest_name,
        "text_box": text_box,
        "description": description,
        "prerequisite_order": prereq_idx,
        "prerequisite_id": prereq_id,
        "objectives": objectives,
        "reward_coins": row[8],
        "reward_xp": row[9]
    })

with open('quest_library.json', 'w', encoding='utf-8') as f:
    json.dump(library, f, indent=2, ensure_ascii=False)

print("Quest library generated in quest_library.json")
