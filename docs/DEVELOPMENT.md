# 开发环境说明

## 推荐方式：Docker

需要安装 Git 和带 Compose v2 的 Docker Desktop。

```bash
git clone <repository-url>
cd ServiceUniverse
python scripts/select_role.py A
docker compose up --build
```

打开 <http://localhost:8000>。第一次构建需要下载 Python 依赖，时间会较长。

常用命令：

```bash
docker compose ps
docker compose logs -f gateway
docker compose restart water-billing
docker compose down
```

除非明确需要删除开发数据卷，否则不要执行 `docker compose down -v`。

## 本地 Python 方式

统一使用 Python 3.11：

```bash
python -m venv .venv
```

PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Bash：

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

运行单个服务：

```bash
python -m uvicorn services.water_billing.app.main:app --reload --port 8101
```

运行前端：

```bash
python -m uvicorn frontend.app.main:app --reload --port 8000
```

运行 Gateway：

```bash
python -m uvicorn gateway.app.main:app --reload --port 8080
```

本地运行完整系统时，每个下游服务需要单独终端，因此完整集成优先使用 Compose。

## 质量检查

```bash
python -m ruff check .
python -m pytest
docker compose config
python scripts/smoke_test.py
```

## 端口表

| Component | Port |
|---|---:|
| Frontend | 8000 |
| Gateway | 8080 |
| Water Billing | 8101 |
| Gas Fault | 8102 |
| Attraction Reservation | 8201 |
| Library Account | 8202 |
| Parking Availability | 8301 |
| Parking Billing | 8302 |

不要为了绕过本地冲突而静默修改共享端口。

## 常见问题

### Gateway 显示所有服务不可用

Docker 容器内必须使用 `http://water-billing:8101` 之类的 Compose 服务名，
不能使用 `localhost`。已提交的 Compose 文件会自动设置。

### 浏览器显示 Gateway 不可用

先确认 <http://localhost:8080/health> 可访问，并检查 `FRONTEND_ORIGINS` 是否包含
<http://localhost:8000>。

### 端口被占用

停止之前启动的进程或容器。不要直接修改团队端口表。
