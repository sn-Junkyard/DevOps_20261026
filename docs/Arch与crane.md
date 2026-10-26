# Arch 本机与 crane 镜像导入

课程执行在 Arch Linux 宿主机，服务和样例均在 Linux 容器中运行，未使用 Ubuntu 虚拟机。CI 使用 Ubuntu 24.04 Runner。

本机安装 `docker docker-buildx docker-compose github-cli crane`，启动 Docker 后确保当前用户可访问 socket。新增 docker 组权限需重新登录后生效。本次为现有会话授予了当前用户 socket ACL，未将 socket 改为全员可写。

Docker 服务直接访问 Docker Hub 超时。通过本机现有代理下载 OCI 布局，然后导入 Docker；保留整个多平台索引以维持课程固定摘要，不改为其他镜像：

```bash
export HTTP_PROXY=http://127.0.0.1:7897
export HTTPS_PROXY=http://127.0.0.1:7897
mkdir -p work/images
crane pull --format oci --annotate-ref python:3.13-slim@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f work/images/python-baseline
tar -C work/images/python-baseline -cf - . | docker load
docker tag python@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f python:3.13-slim
```

必须等待 `crane pull` 成功退出后再打包导入。同样下载并导入服务基础镜像 `python:3.13-slim@sha256:f82c96458eedc847b233e582eb31336f4954b39cae020b6dcf5b3ed0e5cbcd74` 和 CLI 镜像 `docker:28.5.1-cli@sha256:9190b0613792e658a7783cf14b2d5ace5941bb68ede7276922ea36ee457d76ad`。

Docker 29 的本次导入环境需给镜像建立对应标签，BuildKit 才直接复用：构建服务前，将服务基础镜像标为 `python:3.13-slim`，CLI 镜像标为 `docker:28.5.1-cli`；服务构建完成后，将上面基线镜像重新标为 `python:3.13-slim`，再执行 E5/E6/E7。两个原始摘要保持可用。服务 Dockerfile 使用内置构建前端，避免单独解析外部 frontend。

apt/pip 下载使用独立 `work/docker-client/config.json` 的 `proxies.default` 配置，通过 `DOCKER_CONFIG` 仅对本次命令生效。容器内代理使用宿主桥接网关 `172.17.0.1:7897`，因为容器内 `127.0.0.1` 指向容器自身。具体网关应以 `docker network inspect bridge` 为准。本机代理需要监听容器可达地址。

自动构建器将已有代理环境变量按名称传给 Docker 的预定义 build args，报告只记录变量名称。未设置代理的 Ubuntu Runner 直接构建，不需要本机代理配置。最终程序仍禁网运行。下载缓存留在临时目录，交付物仅保存真实下载、导入及镜像检查日志。
