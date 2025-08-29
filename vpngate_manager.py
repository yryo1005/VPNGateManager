import os
import time
import random
import select
import base64
import requests
import subprocess
import multiprocessing

class VpngateManager:
    def __init__(self, tmp_file="tmp.ovpn", connect_timeout=3, verbose=False, min_speed = 10048695, max_ping = 3, init_to_connect = True):
        self.OVPN_TMP_FILE = tmp_file
        self.CONNECT_TIMEOUT = connect_timeout
        self.verbose = verbose
        self.MIN_SPEED = min_speed
        self.MAX_PING = max_ping

        if os.path.exists(self.OVPN_TMP_FILE):
            subprocess.Popen(
                ["sudo", "openvpn", "--config", self.OVPN_TMP_FILE],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            os.remove(self.OVPN_TMP_FILE)
            time.sleep(1)

        if init_to_connect: self.connect()

    def fetch_ovpn_list(self):
        url = "https://www.vpngate.net/api/iphone/"
        try:
            res = requests.get(url, timeout=3)
            lines = res.text.splitlines()
            ovpn_list = []
            for line in lines:
                if line.startswith("*") or line.startswith("#"):
                    continue
                cols = line.split(",")
                if len(cols) < 15:
                    continue

                try:
                    ip = cols[1]
                    try:
                        ping = float(cols[3])
                    except (ValueError, TypeError):
                        ping = 999999
                    try:
                        speed = float(cols[4])
                    except (ValueError, TypeError):
                        speed = 0.0
                    ovpn_b64 = cols[14]
                    if ovpn_b64:
                        ovpn_data = base64.b64decode(ovpn_b64).decode("utf-8")
                        ovpn_list.append({
                            "ip": ip,
                            "ping": ping,
                            "speed": speed,
                            "ovpn": ovpn_data
                        })
                except Exception:
                    continue
        except:
            ovpn_list = self.fetch_ovpn_list()
        return ovpn_list

    def select_vpn(self):
        tmp_list = [L for L in self.ovpn_list if L["speed"] > self.MIN_SPEED and L["ping"] < self.MAX_PING]
        if not tmp_list:
            tmp_list = sorted(self.ovpn_list, key=lambda x: (-x["speed"], x["ping"]))[:20]
        selected_vpn = random.choice(tmp_list)
        if self.verbose:
            print(f"接続先: IP={selected_vpn['ip']}, Speed={selected_vpn['speed']/1e6:.2f} Mbps, Ping={selected_vpn['ping']} ms")
        return selected_vpn["ovpn"]

    def connect(self):
        self.proc = None
        self.ovpn_list = self.fetch_ovpn_list()
        self.selected_ovpn = self.select_vpn()
        self.connect_command()

    def connect_command(self):
        with open(self.OVPN_TMP_FILE, "w") as f:
            f.write(self.selected_ovpn)

        self.proc = subprocess.Popen(
            ["sudo", "openvpn", "--config", self.OVPN_TMP_FILE],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        start_time = time.time()
        while True:
            if time.time() - start_time > self.CONNECT_TIMEOUT:
                if self.verbose: print("接続タイムアウト")
                self.disconnect()
                return self.connect()

            rlist, _, _ = select.select([self.proc.stdout], [], [], 0.5)
            if rlist:
                line = self.proc.stdout.readline()
                if "Initialization Sequence Completed" in line:
                    if self.verbose: print(f"VPN 接続完了, 接続時間: {time.time() - start_time:.2f} 秒")
                    time.sleep(1)
                    return True

    def disconnect(self):
        if self.proc:
            subprocess.run(["sudo", "pkill", "-f", self.OVPN_TMP_FILE])
            self.proc = None
        if os.path.exists(self.OVPN_TMP_FILE):
            os.remove(self.OVPN_TMP_FILE)
        if self.verbose: print("VPN 切断完了")
        time.sleep(1)

def get_my_ip():
    try:
        res = requests.get("https://api.ipify.org")
        return res.text
    except Exception as e:
        return f"IP確認エラー: {e}"

def run_with_timeout(func, timeout=3, *args, **kwargs):
    def wrapper(q, *args, **kwargs):
        try:
            q.put(func(*args, **kwargs))
        except Exception:
            q.put(False)

    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=wrapper, args=(q, *args), kwargs=kwargs)
    p.start()
    p.join(timeout)
    if p.is_alive():
        p.terminate()
        p.join()
        return False
    return q.get()
