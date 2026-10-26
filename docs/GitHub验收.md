# GitHub Actions 与合并门禁验收

仓库：https://github.com/sn-Junkyard/DevOps_20261026 。本次不启动云端 CI、不创建 PR、不修改分支保护。以下由仓库所有者操作并保存真实证据。

## 正常手动运行

Settings → Actions → General 启用 Actions，允许使用 checkout 和 upload-artifact。workflow 仅需 `contents: read`，无需模型密钥或额外写权限。

Actions → **E7 B quality gate** → **Run workflow**，选择 main，保持 `fail_demo=false`。默认分支必须已有 workflow。CLI 等效操作：

```bash
cd /home/sn/workspace/DevOps_20261020_Course/code
gh auth login
gh workflow run e7-quality-gate.yml --ref main -f fail_demo=false
gh run list --workflow e7-quality-gate.yml --limit 5
```

填写真实正常运行 ID，再保存运行链接、SHA 和 artifact：

```bash
run_id=替换为正常运行ID
gh run watch "$run_id" --exit-status
gh run view "$run_id" --json url,headSha,conclusion > ../results/E7/CI-normal.json
gh run download "$run_id" --dir "../results/E7/CI-normal-$run_id"
```

预期 `e7-b-quality-gate` 成功，25 项服务测试通过，五个工作流场景通过，`gate-result.json` 的 `passed=true`。artifact 保留 14 天，需下载备份。失败时同样归档已有日志。手动设 `fail_demo=true` 能演示 oracle 失败，但不能代替实际 PR 拒绝合并证据。

## main 分支保护

首次成功后核对实际检查名、App ID：

```bash
repo=sn-Junkyard/DevOps_20261026
sha=$(git rev-parse HEAD)
gh api "repos/$repo/commits/$sha/check-runs" --jq '.check_runs[] | {name, conclusion, app_id: .app.id}'
```

核对 `ci/B-main-protection.json` 的 App ID（默认 15368），若不同则更新。main 设置必需检查 `e7-b-quality-gate`、strict=true、enforce_admins=true、PR 合并、审批人数 0，禁止强制推送和删除。可使用 Settings → Branches 或：

```bash
gh api --method PUT "repos/$repo/branches/main/protection" --input ci/B-main-protection.json
gh api "repos/$repo/branches/main/protection" > ../results/E7/main-protection.json
```

需仓库管理员权限。若权限或账号计划不支持，保留真实错误并检查设置，不将失败记作完成，不自行更改仓库可见性。

## 同一 PR 的失败、拒绝与恢复

从最新 main 建立演示分支，加入课程故意错误测试。创建和更新 PR 会自动运行检查：

```bash
git switch main
git pull --ff-only
git switch -c e7-gate-reject-demo
cp ci/rejection-demo/B/test_ci_reject_demo.py services/draft/tests/
git add services/draft/tests/test_ci_reject_demo.py
git commit -m "Demonstrate E7 rejection with wrong version oracle"
git push -u origin e7-gate-reject-demo
gh pr create --base main --head e7-gate-reject-demo --title "Demonstrate E7 merge rejection" --body "故意错误的返回码预期用于验证 CI 与合并拦截，保存证据后修复。"
```

填写真实 PR 编号，等待失败检查。预期 1 failed、25 passed，PR 为 OPEN/BLOCKED。确认 main 保护已生效且必需检查失败后，尝试普通合并：

```bash
pr_num=替换为PR编号
gh pr checks "$pr_num" --watch
mkdir -p ../results/E7/CI-rejection
gh pr view "$pr_num" --json state,mergeStateStatus,headRefOid,url > ../results/E7/CI-rejection/PR.json
gh pr merge "$pr_num" --merge > ../results/E7/CI-rejection/merge-rejection.log 2>&1
merge_code=$?
printf 'MERGE_EXIT_CODE=%s\n' "$merge_code" | tee ../results/E7/CI-rejection/merge-exit-code.txt
```

预期合并退出非零，明确因分支策略被拒绝。不要使用管理员绕过或自动合并。保存本次 PR 失败运行链接、head SHA、失败日志、artifact 及实际保护配置。

在同一 PR 修正预期：

```bash
cp ci/rejection-demo/B/fixed/test_ci_reject_demo.py services/draft/tests/
git add services/draft/tests/test_ci_reject_demo.py
git commit -m "Restore version success oracle"
git push
gh pr checks "$pr_num" --watch
gh pr view "$pr_num" --json state,mergeStateStatus,headRefOid,url
```

确认全部检查属于最新 head SHA，预期 26 passed、五场景通过。下载恢复 artifact 后再合并：

```bash
mkdir -p ../results/E7/CI-recovery
gh pr merge "$pr_num" --merge
gh pr view "$pr_num" --json state,mergedAt,mergeCommit,url > ../results/E7/CI-recovery/PR-merged.json
git switch main
git pull --ff-only
```

失败和恢复运行分别使用 `gh run view RUN_ID --json url,headSha,conclusion` 保存元数据、`gh run view RUN_ID --log` 保存日志、`gh run download RUN_ID --dir 证据目录` 下载 artifact。补拍 Actions、保护配置、失败 PR、拒绝和恢复合并的真实截图，并更新本地 `results/验收记录.csv`。恢复修改的是教学测试预期，不是算法。
