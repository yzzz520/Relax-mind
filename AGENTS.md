# AGENTS.md

> Codex 每次开工前先读这个文件。

---

## 1. 网络访问（重要，先看这条）

**本机的命令行 TLS 通道被沙箱切断**，表现是：

| 方式 | 结果 |
|---|---|
| `curl` | `schannel: AcquireCredentialsHandle failed: SEC_E_NO_CREDENTIALS` |
| `Invoke-WebRequest` / `Invoke-RestMethod` | `基础连接已经关闭: 接收时发生错误` |
| `npm install` | 偶发失败（同一个原因） |

**唯一稳定的方式是 Python 的 `urllib`** —— 它走 OpenSSL，不经过 Windows schannel。

### 下载任意文件（模板）

```powershell
$py = "C:\Users\Y\Documents\deepseek-harness\default-workspace\tools\python312\python.exe"
& $py -c @"
import urllib.request
req = urllib.request.Request('HTTPS_URL', headers={'User-Agent': 'Mozilla/5.0'})
open(r'OUTPUT_PATH', 'wb').write(urllib.request.urlopen(req, timeout=30).read())
"@
```

### 已验证可以访问的域名

- `raw.githubusercontent.com`（GitHub 原始文件）
- `archive.apache.org`、`mirrors.huaweicloud.com`、`registry.npmmirror.com`
- `pypi.tuna.tsinghua.edu.cn`
- `bootstrap.pypa.io`

### 已验证**无法**直接访问

- `archive.org`、`api.openverse.org`（超时）
- `cdn.pixabay.com` 根路径（403，但具体文件可能可下）

### 用 Python 装包

```powershell
$env:PIP_CONFIG_FILE = "C:\Users\Y\Documents\deepseek-harness\default-workspace\tools\config\pip.ini"
& $py -m pip install <包名>
```

> 注意：pip 的 `TEMP` 必须指向工作区内目录，否则解包会因 ACL 失败。
> 若 pip 报 `PermissionError [Errno 13]`，先设：
> `$env:TEMP = "C:\Users\Y\Documents\deepseek-harness\default-workspace\tools\temp"`

### 已经下载好的参考源码（**不要去网上找，直接读**）

```
docs/vendor/reactbits/Lightfall.tsx     27.6 KB
docs/vendor/reactbits/Particles.tsx     33.4 KB
docs/vendor/reactbits/Radar.tsx         35.3 KB
```

来源：`github.com/DavidHDev/react-bits`（MIT）。**GLSL 字符串必须原样保留。**

---

## 2. 项目约定

- 技术栈锁定：Vue 3 + Vite + JavaScript（不用 TS）+ Pinia + Vue Router + ECharts
- 禁止引入：React、framer-motion、three.js
- 所有网络请求走 `src/api/`，组件内不直接 fetch
- 每批任务结束**停下报告**，不要连续推进下一批
- 报告必须给**实测数据**，不要写"正常""已完成"

---

## 3. 已知环境事实

- Java 21（`JAVA_HOME` 已配）
- Maven 3.9.9（`C:\Users\Y\Documents\deepseek-harness\default-workspace\tools\maven`）
- Python 3.12（上文的 `$py`）
- Node 24 / npm 11
- 项目开发服务器：`npm run dev` → `http://localhost:5173`
- 截图用 headless Edge，**截之前先等 1500ms**（避免拍到动画中间帧）
