# Public Library Membership and Account

- 负责人：成员 D
- 端口：`8202`
- 类型：业务服务
- Gateway：`gateway/app/routers/library_account.py`
- 前端：`frontend/templates/services/library-account.html`

最小流程：

1. 创建图书馆会员；
2. 查询会员与账户信息；
3. 提供代表性的借阅或账户状态信息；
4. 返回明确的校验和资源不存在错误。

```bash
python -m uvicorn services.library_account.app.main:app --reload --port 8202
```

验证：<http://localhost:8202/health>
