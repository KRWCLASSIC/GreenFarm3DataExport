import csv
import struct
import os

def parse_tabular_data(path, sub_idx):
    if not os.path.exists(path): return None
    with open(path, 'rb') as f:
        header = f.read(4)
        if len(header) < 4: return None
        total, subs = struct.unpack('<HH', header)
        if sub_idx >= total: return None
        f.read(subs * 2)
        offs = [struct.unpack('<I', f.read(4))[0] for _ in range(total+1)]
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

def export_spreadsheet():
    # Load Set 15 (Rewards/Probabilities)
    table_15 = parse_tabular_data('resources/assets/800x480/13', 15)
    
    # Action Explanations based on de-obfuscated SID associations and game context
    action_info = {
        100: {
            "name": "Neighbor Help: Animals",
            "explanation": "Triggered when feeding, brushing, or helping a neighbor's animal. This action pulls rewards from the 'Animal Collection' pool (ID 6xxx), which includes Super Animal baby items."
        },
        97: {
            "name": "Neighbor Help: Crops & Trees",
            "explanation": "Triggered when watering or harvesting a neighbor's crops or trees. This action pulls from the 'Crop Collection' pool, where items like Pumpkins and rare harvest collectibles are found."
        },
        99: {
            "name": "Special Interactions",
            "explanation": "Triggered during limited-time neighbor events or high-value social interactions. Offers the highest base drop rate for elite collectibles."
        },
        101: {
            "name": "Own Farm: Animal Care",
            "explanation": "Standard interactions on your own farm. While it has a defined drop rate, neighbor help is much more likely to yield rare collection items."
        },
        155: {
            "name": "Task Achievement (Tiers)",
            "explanation": "Cumulative milestone rewards for completing a set number of tasks. The multiple entries represent different 'Tier' thresholds (e.g. Bronze, Silver, Gold milestones)."
        },
        153: {
            "name": "Progress Milestone",
            "explanation": "One-time rewards for hitting specific game progression markers (e.g. restoring a manor room or reaching a build limit)."
        },
        81: {
            "name": "Daily Login Bonus",
            "explanation": "Base probability for receiving a bonus item upon first login of the day."
        },
        156: {
            "name": "Level Up Reward",
            "explanation": "Probability weight for receiving a bonus collectible upon character level advancement."
        },
        9: {
            "name": "Global Sales",
            "explanation": "Small probability of a 'tip' or rare item when selling goods through the shop or order board."
        },
        139: {
            "name": "Social Currency Gathering",
            "explanation": "Bonus chance for a collection item when collecting hearts or coins left behind by visitors."
        }
    }

    # Process and Deduplicate
    unique_actions = {}
    for row in table_15:
        action_id = row[1]
        chance_bp = row[7]
        coin_reward = row[6]
        
        # We group by Action ID. If multiple rows exist, we note it.
        if action_id not in unique_actions:
            unique_actions[action_id] = {
                "coin": coin_reward,
                "chance": chance_bp,
                "count": 1,
                "all_chances": [chance_bp]
            }
        else:
            unique_actions[action_id]["count"] += 1
            unique_actions[action_id]["all_chances"].append(chance_bp)
            # Update coin if higher
            unique_actions[action_id]["coin"] = max(unique_actions[action_id]["coin"], coin_reward)
            unique_actions[action_id]["chance"] = max(unique_actions[action_id]["chance"], chance_bp)

    with open('drop_rates.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Action Type', 'Action ID', 'Explanation', 'Base Success Chance (%)', 'Max Coin Reward', 'Complexity Note'])
        
        # Sort by chance descending
        sorted_ids = sorted(unique_actions.keys(), key=lambda x: unique_actions[x]['chance'], reverse=True)
        
        for aid in sorted_ids:
            data = unique_actions[aid]
            info = action_info.get(aid, {"name": f"Other (ID {aid})", "explanation": "General game action or system trigger."})
            
            percentage = f"{data['chance'] / 100:.2f}%"
            note = ""
            if data['count'] > 1:
                note = f"Multiple Tiers: {', '.join([f'{c/100:.2f}%' for c in sorted(list(set(data['all_chances'])))])}"
            
            writer.writerow([
                info['name'],
                aid,
                info['explanation'],
                percentage,
                data['coin'],
                note
            ])

    print("Successfully exported drop_rates.csv")

if __name__ == "__main__":
    export_spreadsheet()
