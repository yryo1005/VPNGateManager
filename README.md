# VpngateManager

Python クラス VpngateManager を使って，VPN Gate の公開 VPN サーバーに自動で接続・切断を簡単に行えます．

## 概要
- VpngateManager は VPN Gate の .ovpn プロファイルを自動で取得し，インスタンス化時にランダムで VPN を選択します．
- インスタンス化した後は connect() で VPN に接続します．
- 接続後は disconnect() することで VPN から切断します．
- 切断後は元の IP アドレスに戻ります．
- タイムアウト機能付きで，VPN 接続に失敗した場合は自動で切断します．
- ログの表示は verbose=True でオンにできます．

## インストール
初回のみ OpenVPN をインストールする必要があります（Linux / WSL 環境向け）:

```
sudo apt install openvpn -y
```

Python 側の依存パッケージは requests のみです:

```
pip install requests
```

## 使用例

```python
import requests
from VPNGateManager.vpngate_manager import VpngateManager

def get_my_ip():
    try:
        res = requests.get("https://api.ipify.org")
        return res.text
    except Exception as e:
        return f"IP確認エラー: {e}"

print("自分のIP:", get_my_ip())

vpn_manager = VpngateManager(tmp_file="tmp.ovpn", connect_timeout=3, verbose=True)
vpn_manager.connect()
print("自分のIP:", get_my_ip())
vpn_manager.disconnect()

print("自分のIP:", get_my_ip())
"""
自分のIP: 114.150.235.20
VPN 接続完了
自分のIP: 221.71.231.160
VPN 切断完了
自分のIP: 114.150.235.20
"""
```

## サンプルデータ
- VPNGateManager_sample.ipynb にサンプルコードと実行例を用意しています．

## 注意事項
- 本スクリプトは Linux / WSL 環境での使用を想定しています．Windows では動作保証がありません．
- 公開 VPN のため，接続先の安定性や速度は保証されません．
