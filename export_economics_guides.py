import struct
import os
import csv

def get_pack_map(path):
    if not os.path.exists(path): return {}
    with open(path, 'rb') as f:
        header = f.read(4)
        if len(header) < 4: return {}
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
    if not os.path.exists(path): return None
    with open(path, 'rb') as f:
        header = f.read(4)
        if len(header) < 4: return None
        total, subs = struct.unpack('<HH', header)
        if sub_idx >= total: return None
        f.seek(4 + subs * 2)
        offs = [struct.unpack('<I', f.read(4))[0] for _ in range(total+1)]
        if sub_idx >= len(offs) - 1: return None
        f.seek(offs[sub_idx])
        d = f.read(offs[sub_idx+1] - offs[sub_idx])
        if not d or d[0] != 2: return None
        r, c = struct.unpack('<II', d[1:9])
        ts = d[9:9+c]
        ptr = 9+c
        table = []
        for _ in range(r):
            row = []
            for t in ts:
                if t == 1: v = struct.unpack('b', d[ptr:ptr+1])[0]; ptr += 1
                elif t == 2: v = struct.unpack('<h', d[ptr:ptr+2])[0]; ptr += 2
                elif t == 4: v = struct.unpack('<i', d[ptr:ptr+4])[0]; ptr += 4
                else: v = 0
                row.append(v)
            table.append(row)
        return table

def load_all_strings(path):
    pack_map = get_pack_map(path)
    all_strings = {}
    for pid, (s, e) in pack_map.items():
        pk = parse_string_pack(path, s, e)
        for idx, t in enumerate(pk):
            all_strings[(pid << 10) | idx] = t
    return all_strings

def export_all():
    asset_13 = r'resources\assets\800x480\13'
    asset_en = r'resources\assets\800x480\EN'
    
    print("Loading strings...")
    strings = load_all_strings(asset_en)
    
    # --- TROPHIES (Table 25) ---
    print("Exporting Trophies...")
    trophies = parse_tabular_data(asset_13, 25)
    if trophies:
        with open('trophy_mining_guide.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Trophy ID', 'Name', 'Description', 'Bronze Req', 'Silver Req', 'Gold Req', 'Coin Reward', 'XP Reward', 'CASH REWARD'])
            for row in trophies:
                name = strings.get(row[3], f"Trophy_{row[0]}")
                desc = strings.get(row[6], "")
                # Mapping based on C0660cg.java logic
                # Col 8: Bronze, Col 9: Silver, Col 10: Gold
                # Col 12: Coins (m3446gY encoded), Col 11: XP (m3446gY encoded)? 
                # Wait, code said: afl[i] = q(row[11]), afm[i] = gX(row[12]), afn[i] = gX(row[13])
                # AFL = long (XP), AFM = int (Coin), AFN = int (Cash)
                xp = row[11]
                coins = row[12]
                cash = row[13]
                writer.writerow([row[0], name, desc, row[8], row[9], row[10], coins, xp, cash])
                
    # --- COLLECTIONS (Table 16) ---
    print("Exporting Collections...")
    collections = parse_tabular_data(asset_13, 16)
    if collections:
        with open('collection_mining_guide.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Collection ID', 'Name', 'Item 1 ID', 'Item 2 ID', 'Item 3 ID', 'Item 4 ID', 'Coin Reward', 'XP Reward', 'Cash Reward'])
            # Table 17 has the item IDs (60 rows, 4 per collection)
            items_table = parse_tabular_data(asset_13, 17)
            for i, row in enumerate(collections):
                name_sid = i + 115056 # Derived from C0660cg logic
                name = strings.get(name_sid, f"Collection_{i}")
                
                # Get items from Table 17
                c_items = []
                if items_table:
                    for j in range(4):
                        idx = i * 4 + j
                        if idx < len(items_table):
                            c_items.append(items_table[idx][1])
                
                # Table 16: Col 5 = Coins, Col 6 = XP
                coins = row[5]
                xp = row[6]
                writer.writerow([i, name, *c_items, coins, xp, 0])

    # --- LEVEL UP REWARDS (Table 27) ---
    print("Exporting Level Rewards...")
    levels = parse_tabular_data(asset_13, 27)
    if levels:
        with open('level_up_mining_guide.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Level', 'XP Required', 'Coin Reward', 'Energy Reward', 'CASH REWARD'])
            for row in levels:
                # Table 27: Col 1 = Level, Col 3 = Energy? Col 4 = XP? Col 5 = Cash?
                # Based on m3434gM(int i) logic:
                # i4 = agO[level-1], s = agP[level-1]
                # agO = Table 27 Col 4, agP = Table 27 Col 5
                level = row[1]
                energy = row[3]
                coins = row[4] # agO
                cash = row[5]  # agP
                writer.writerow([level, row[2], coins, energy, cash])

    print("All extraction scripts completed. Check root for .csv files.")

if __name__ == "__main__":
    export_all()
