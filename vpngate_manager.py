import requests
import base64
import subprocess
import os
import time
import random

class VpngateManager:
    def __init__(self, tmp_file="tmp.ovpn", connect_timeout=3, verbose=False):
        """
            tmp_file: VPNプロファイルの一時的な保存先
            connect_timeout: VPNに接続した際のタイムアウト時間
            verbose: ログの表示設定
        """
        self.OVPN_TMP_FILE = tmp_file
        self.CONNECT_TIMEOUT = connect_timeout
        self.ovpn_list = self.fetch_ovpn_list()
        self.verbose = verbose
        if not self.ovpn_list:
            raise RuntimeError("OVPNリストが取得できませんでした")
        self.selected_ovpn = random.choice(self.ovpn_list)
        self.proc = None

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
            ovpn_b64 = cols[14]
            if ovpn_b64:
                try:
                    ovpn_data = base64.b64decode(ovpn_b64).decode("utf-8")
                    ovpn_list.append(ovpn_data)
                except Exception:
                    continue
        return ovpn_list

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
                if self.verbose: print(f"VPN 接続完了, 接続時間: {time.time() - start_time}")
                time.sleep(0.5)
                return True
            if time.time() - start_time > self.CONNECT_TIMEOUT:
                if self.verbose: print("接続タイムアウト")
                self.disconnect()
                return False

    def disconnect(self):
        if self.proc:
            self.proc.terminate()
            subprocess.run(["sudo", "pkill", "-f", self.OVPN_TMP_FILE])
            time.sleep(0.5)
            self.proc = None
        if os.path.exists(self.OVPN_TMP_FILE):
            os.remove(self.OVPN_TMP_FILE)
        if self.verbose: print("VPN 切断完了")
