# 两台电脑开发与私有数据同步

目标：公开 GitHub 只同步代码、文档、配置模板；真实数据库、种子数据、上传文件通过私有目录同步。

## 推荐目录

在仓库外维护私有目录，例如：

```bash
/Users/zhangdifei03/Desktop/旅途重构/lv_private_data/
  db/
    latest.dump
  seed_data/
    destinations.json
    photo_spots.json
    outfits.json
  uploads/
  backups/
```

## 公开仓库不要提交

不要提交以下内容：

- `.env`、`.env.production`
- API Key、Token、服务器密码、私钥
- 数据库文件：`*.db`、`*.sqlite3`、`*.dump`、`*.sql`、`*.sql.gz`
- 真实种子数据 JSON
- 用户上传文件、私有缓存、向量库

## 导入私有种子数据

```bash
cd backend
LV_SEED_DATA_DIR="/path/to/lv_private_data/seed_data" python -m scripts.seed_knowledge --reset
```

也可以显式传参：

```bash
cd backend
python -m scripts.seed_knowledge --reset --data-dir "/path/to/lv_private_data/seed_data"
```

## 同步到另一台电脑

1. 用 GitHub 同步代码：

```bash
git pull origin main
```

2. 用私有通道同步 `lv_private_data/`：

可选方式：AirDrop、移动硬盘、Syncthing、加密网盘、private GitHub repo。

如果使用 GitHub，同步数据的仓库必须是 **private repo**，不要放到公开仓库。
