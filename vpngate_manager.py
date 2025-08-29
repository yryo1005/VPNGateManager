import requests
import base64
import subprocess
import os
import time
import random

class VpngateManager:
    def __init__(self, tmp_file="tmp.ovpn", connect_timeout=3, verbose=False, min_speed = 10048695, max_ping = 30, init_to_connect = True):
        """
            tmp_file: VPNプロファイルの一時的な保存先
            connect_timeout: VPNに接続した際のタイムアウト時間
            verbose: ログの表示するか否か
            min_speed: VPN接続先の最低速度
            max_ping: VPN接続先の最高Ping
            init_to_connect: インスタンス化と共にVPNに接続するか否か
        """
        self.OVPN_TMP_FILE = tmp_file
        self.CONNECT_TIMEOUT = connect_timeout
        self.verbose = verbose
        self.MIN_SPEED = min_speed
        self.MAX_PING = max_ping

        self.ovpn_list = self.fetch_ovpn_list()
        if not self.ovpn_list:
            raise RuntimeError("OVPNリストが取得できませんでした")
        # ランダムではなく速度順にソートされたリストの先頭を選ぶ
        self.selected_ovpn = self.select_vpn()
        self.proc = None
        if init_to_connect: self.connect()

    def fetch_ovpn_list(self):
        url = "https://www.vpngate.net/api/iphone/"
        res = requests.get(url)
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
                # Speedも同様に安全に変換
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
        return ovpn_list

    def select_vpn(self):
        # 速度とPingが条件を満たしたVPNのみ抽出
        tmp_list = [L for L in self.ovpn_list if L["speed"] > self.MIN_SPEED and L["ping"] < self.MAX_PING]
        if not tmp_list:
            # 速度降順, Ping昇順でソート，上位20件のみ抽出
            tmp_list = sorted(self.ovpn_list, key=lambda x: (-x["speed"], x["ping"]))[:20]

        selected_vpn = random.choice(tmp_list)
        if self.verbose:
            print(f"接続先: IP={selected_vpn['ip']}, Speed={selected_vpn['speed']/1e6:.2f} Mbps, Ping={selected_vpn['ping']} ms")
        return selected_vpn["ovpn"]

    def connect(self):
        with open(self.OVPN_TMP_FILE, "w") as f:
            f.write(self.selected_ovpn)

        self.proc = subprocess.Popen(
            ["sudo", "openvpn", "--config", self.OVPN_TMP_FILE],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        start_time = time.time()
        for line in self.proc.stdout:
            if "Initialization Sequence Completed" in line:
                if self.verbose: print(f"VPN 接続完了, 接続時間: {time.time() - start_time:.2f} 秒")
                time.sleep(0.5)
                return True
            if time.time() - start_time > self.CONNECT_TIMEOUT:
                if self.verbose: print("接続タイムアウト")
                self.disconnect()

                # 異なる接続先を選択する
                self.ovpn_list = self.fetch_ovpn_list()
                if not self.ovpn_list:
                    raise RuntimeError("OVPNリストが取得できませんでした")
                self.selected_ovpn = self.select_vpn()
                self.proc = None
                return self.connect()

    def disconnect(self):
        if self.proc:
            self.proc.terminate()
            subprocess.run(["sudo", "pkill", "-f", self.OVPN_TMP_FILE])
            time.sleep(0.5)
            self.proc = None
        if os.path.exists(self.OVPN_TMP_FILE):
            os.remove(self.OVPN_TMP_FILE)
        if self.verbose: print("VPN 切断完了")
