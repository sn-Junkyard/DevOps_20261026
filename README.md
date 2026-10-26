# B02 · DRAFT E5–E7

沈诺 · 学号 241880401 · B02。复用课程 B-draft 参考实现，回放已保存的 DeepSeek 候选，不调用模型 API。仅覆盖 E5–E7 教学样例。

## 运行

宿主机需 Python 3、Git、Docker Engine、Buildx、Compose，当前账号可访问 `/var/run/docker.sock`。在仓库根目录执行，每次重跑更换 `--out`：

```bash
python3 scripts/lab_cloud.py doctor
python3 scripts/lab_cloud.py build --out work/build-01 --build-timeout 1200
python3 scripts/lab_cloud.py e5 --out work/e5-01 --build-timeout 600
docker build --progress=plain -f fixtures/ci-candidates/DeepSeek-E5.Dockerfile -t course1020-draft-e5:local work/e5-01/project
image_id=$(docker image inspect course1020-draft-e5:local --format '{{.Id}}')
docker run --rm --network none "$image_id"
python3 scripts/lab_cloud.py e6 --replay --out work/e6-01 --build-timeout 600
python3 scripts/verify_e6_b_evidence.py --run-dir work/e6-01/evidence
python3 scripts/lab_cloud.py gate --replay --out work/e7-01 --build-timeout 600
```

预期：E5 初始 Docker 构建退出 1，日志 `make: not found`（镜像内命令退出 127），采集脚本退出 0。修复构建和按镜像 ID 运行均退出 0，输出 `hello E3`。E6 成功，E7 六项检查通过。

新增测试检查含符号链接的项目在执行 Docker 前被拒绝，基础 24 项测试增至 25 项。CLI、核心流程和报告格式沿用课程实现。候选来源见 `fixtures/ci-candidates/replay-provenance.json`。

## 交付与 CI

完整本机证据及报告在 `../results/`，不加入 Git。仓库保留[实验报告](docs/实验报告.md)及[GitHub 验收步骤](docs/GitHub验收.md)。workflow 支持手动触发和 main 的 PR 检查，普通 push 不触发。首次云端正常、失败与恢复验收已自动完成，真实运行和 PR 链接见实验报告；后续仍可手动运行。无需模型密钥。
