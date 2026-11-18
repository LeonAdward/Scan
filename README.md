# 商品扫描 GitHub Actions 云端构建（根目录版）

上传本压缩包**内部文件**到 GitHub 仓库根目录，不要上传外层文件夹。

根目录：`base.apk`、`scanner.js`、`patch.py`、`server-config.js`、`server-client.js`、`README.md`。

**唯一必须保留的子目录**是 `.github/workflows/build.yml`：GitHub Actions 只识别该固定路径，不能将 build.yml 直接放根目录。

在 Actions 页面运行 `Build 商品扫描 camera-permission patch`，下载 Artifact。此工作流尚未在 GitHub 运行验证；失败时检查日志。

## 日后连接服务器

默认完全离线，不会自动访问服务器。`server-config.js` 中 `enabled:false`，后续设置为 true 并填写 HTTPS `baseUrl` 后，JS 可以通过 `ShopScannerServer.request('/v1/products')` 访问 API（需要后端实现接口、处理身份验证、CORS 和同步冲突）。

当前只提供**服务器连接预留接口**，尚未实现远端库存同步、账号登录、OCR 或 AI 模型。不要把密钥直接写进前端文件。服务器请求必须使用 HTTPS。

未签名 APK 不可直接安装，需后续签名。原工作流对原始 Activity 的 Smali 修改依赖类结构，尚未经过云端构建验证。
