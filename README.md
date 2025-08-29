# VpngateManager

Python クラス VpngateManager を使って，VPN Gate の公開 VPN サーバーに自動で接続・切断を簡単に行えます．

## 概要
- VpngateManager は VPN Gate の .ovpn プロファイルを自動で取得し，インスタンス化時にランダムで VPN を選択します．
- ランダムに VPN を選択する際に， VPN 接続先の最低速度と最高 Ping を設定できます．
- 条件を満たす VPN がない場合は速度が高速な VPN の上位からランダムに接続先を選択します．
- インスタンス化と共に VPN に接続します．
- インスタンス化時に VPN に接続したくない場合は init_to_connect = False を指定します．
- init_to_connect = False の場合 connect() することで VPN に接続します．
- 接続後は disconnect() することで VPN から切断します．
- 切断後は元の IP アドレスに戻ります．
- タイムアウト機能付きで，VPN 接続に失敗した場合は自動で切断します．
- ログの表示は verbose=True でオンにできます．
- run_with_timeoutを用いることで特定の関数の実行時間がタイムアウトに収まるか確認できます．


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

vpn_manager = VpngateManager(verbose=True)
print("自分のIP:", get_my_ip())

vpn_manager.disconnect()
print("自分のIP:", get_my_ip())
"""
自分のIP: 114.*.*.20
接続先: IP=219.100.37.92, Speed=408.01 Mbps, Ping=11.0 ms
VPN 接続完了, 接続時間: 4.44 秒
自分のIP: 219.100.37.238
VPN 切断完了
自分のIP: 114.*.*.20
"""
```

## 注意事項
- 本スクリプトは Linux / WSL 環境での使用を想定しています．Windows では動作保証がありません．
- 公開 VPN のため，接続先の安定性や速度は保証されません．
