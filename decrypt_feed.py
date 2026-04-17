import struct
import json
import os

def decrypt(v, k):
    n = len(v)
    if n < 2: return v
    delta = 0x9e3779b9
    q = 6 + 52 // n
    sum_val = (q * delta) & 0xffffffff
    y = v[0]
    while sum_val != 0:
        e = (sum_val >> 2) & 3
        for p in range(n - 1, 0, -1):
            z = v[p - 1]
            mx = (((z >> 5 ^ y << 2) + (y >> 3 ^ z << 4)) & 0xffffffff) ^ (((sum_val ^ y) + (k[(p & 3) ^ e] ^ z)) & 0xffffffff)
            v[p] = (v[p] - mx) & 0xffffffff
            y = v[p]
        z = v[n - 1]
        mx = (((z >> 5 ^ y << 2) + (y >> 3 ^ z << 4)) & 0xffffffff) ^ (((sum_val ^ y) + (k[(0 & 3) ^ e] ^ z)) & 0xffffffff)
        v[0] = (v[0] - mx) & 0xffffffff
        y = v[0]
        sum_val = (sum_val - delta) & 0xffffffff
    return v

def decrypt_file(input_path, output_path, key_str="1001"):
    with open(input_path, 'rb') as f:
        data = f.read()
    
    # Pad to 4 bytes
    if len(data) % 4 != 0:
        data += b'\x00' * (4 - (len(data) % 4))
    
    v = list(struct.unpack(f'<{len(data)//4}I', data))
    
    k_bytes = key_str.encode('utf-8')
    k_bytes += b'\x00' * (16 - len(k_bytes))
    k = list(struct.unpack('<4I', k_bytes[:16]))
    
    dec = decrypt(v, k)
    res_bytes = struct.pack(f'<{len(dec)}I', *dec)
    
    # Check if first byte is {
    print(f"First 10 bytes: {res_bytes[:10].hex(' ')}")
    
    res = res_bytes.decode('utf-8', errors='ignore')
    try:
        # Sometimes there's garbage at the end
        pos = res.find('{')
        end = res.rfind('}')
        if pos != -1 and end != -1:
            j = json.loads(res[pos:end+1])
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(j, f, indent=2, ensure_ascii=False)
            print(f"JSON Decrypted: {output_path}")
            return
    except: pass
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(res)
    print(f"Raw Decrypted: {output_path}")

if __name__ == "__main__":
    decrypt_file(r'resources\assets\800x480\InitialFeed.bin', 'InitialFeed_decrypted.json')
