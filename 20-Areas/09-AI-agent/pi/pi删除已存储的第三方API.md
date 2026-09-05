> 注:config-pi 已于 2026-09-03 更名 config-ai(GitHub 旧链接自动重定向)

# pi 删除已存储的第三方 API(密钥)

> 适用:需要清除 pi 中已存储的第三方(provider)API Key,例如套餐到期、账号弃用、
> 或某 provider 不再使用。相关笔记:[pi-config模块拆解](<./pi-config模块拆解.md>)、
> [pi会话机制与电脑重启后恢复](<./pi会话机制与电脑重启后恢复.md>)。

## 一、密钥存哪里

pi 的 provider 密钥全部是**明文 JSON 文件**,不存在数据库/凭据管理器(model-hub 扩展及其 `model-hub.json` 已弃用移除,2026-09-03):

| 文件 | 作用 | 结构 |
|---|---|---|
| `~/.pi/agent/auth.json` | 各 provider 的 API Key(主存储) | 顶层键 = provider 名,每个值是 `{ "type": ..., "key": ... }` |

两个文件**永不入库**(config-pi 只存 `*.template` 占位);`setup.sh` 部署时发现它们已存在会**保留不覆盖**。

**注意**:`pi auth` 命令只有 `print-api-key` / `print-bearer-token` / `check`,**没有删除/登出子命令**——清除必须手动编辑文件。

## 二、删除单个 provider(如删除 ark-coding)

### 1. 从 auth.json 移除

```bash
# 预览将删的键(确认拼写)
node -e "const a=require(process.env.HOME+'/.pi/agent/auth.json'); console.log(Object.keys(a).join('\n'))"

# 备份后删除(以 ark-coding 为例)
cp ~/.pi/agent/auth.json ~/.pi/agent/auth.json.bak
node -e "const fs=require('fs'),h=process.env.HOME,p=h+'/.pi/agent/auth.json'; const a=JSON.parse(fs.readFileSync(p,'utf8')); delete a['ark-coding']; fs.writeFileSync(p, JSON.stringify(a,null,2))"
```

### 2. 检查引用并修正

- **defaultProvider**:若被删的是默认 provider,先改 `~/.pi/agent/settings.json` 的 `defaultProvider` 指向现存 provider,否则 pi 启动报无默认 provider:
  ```bash
  grep -o '"defaultProvider": "[^"]*"' ~/.pi/agent/settings.json
  ```
- 环境变量注入的 key(如 `ARK_CODING_API_KEY`)若已设,文件删除不影响——**环境变量优先级存在时,删除文件可能无效**,需同时 unset:
  ```bash
  env | grep -i "ARK_CODING\|ark-coding"
  ```

## 三、彻底清理全部第三方 API(重置状态)

```bash
# 1) 备份(可随时回滚)
cp ~/.pi/agent/auth.json ~/.pi/agent/auth.json.bak.$(date +%Y%m%d)

# 2) 把 auth.json 重置为仅含空占位(而非删除文件——删除后 setup.sh 会用模板重建,行为一致)
echo '{}' > ~/.pi/agent/auth.json

# 3) settings.json 的 defaultProvider 改回可用项或 'google'(pi 内置)
```

## 四、副作用与注意事项

| 事项 | 说明 |
|---|---|
| setup.sh 是否恢复 | 不会。部署时若 auth.json 已存在则保留原样;若**被删除**,则从 template 重建为占位(`<YOUR_TOKEN>`),需重填才能用 |
| 已加载会话 | 运行中的 pi 在内存里仍持有旧 key 直到重启;/reload 或重启后生效 |
| 受影响功能 | 该 provider 的模型在 /model 消失、provider 调用报缺凭据错误 |
| 环境变量注入 | `ARK_CODING_API_KEY` 等 env key 不走文件;要彻底清除需在启动环境里 unset |
| 网页/账号侧 | 这只是本地凭据;若目的是停用账号,还需到 provider 官网删除/停用 API Key |

## 五、验证删除生效

```bash
pi auth check --provider ark-coding            # 应报无凭据/不可用
pi auth check --json                           # 全量凭据状态,确认无残留
ls ~/.pi/agent/auth.json.bak*                  # 确认备份存在(可回滚)
```

验证无误后删除备份:`rm ~/.pi/agent/auth.json.bak*`
