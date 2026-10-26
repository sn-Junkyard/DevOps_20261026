# GitHub Actions 与合并门禁验收

仓库：https://github.com/sn-Junkyard/DevOps_20261026 。本仓库已在用户后续授权后自动完成正常、失败及修复恢复运行，并配置 main 分支保护。真实运行和 PR 链接见文末记录。以下命令供复查或重演；重演请使用新的分支名。

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

## 本仓库自动验收记录（2026-10-26）

用户随后授权自动执行云端验收，使用现有 Git 认证完成，无需新增 token。以下均为本仓库真实运行：

|阶段|Actions 运行|结果|服务测试|
|---|---|---|---|
|正常|[40308819409](https://github.com/sn-Junkyard/DevOps_20261026/actions/runs/40308819409)|通过|25 passed|
|故意失败|[40309128245](https://github.com/sn-Junkyard/DevOps_20261026/actions/runs/40309128245)|失败（符合预期）|1 failed / 25 passed|
|修复恢复|[40309341962](https://github.com/sn-Junkyard/DevOps_20261026/actions/runs/40309341962)|通过|26 passed|

同一 PR：[B02 E7 #1](https://github.com/sn-Junkyard/DevOps_20261026/pull/1)。失败提交 416cbacd4bbc4720e25c1d242303221bec0bbca9；修复提交 86c2c285bdfbba5c674e03d4ce5623fa97496013。

已核验 main 必需检查 e7-b-quality-gate / App 15368，strict=true、enforce_admins=true、审批人数 0。失败 PR 为 OPEN/BLOCKED，普通 `gh pr merge --merge` 退出 1，原文为 base branch policy prohibits the merge；主分支保持原 SHA。修复运行的五场景均通过，PR 恢复 CLEAN。报告更新也须通过同一保护检查后才普通合并。

全部运行日志、artifact、保护配置、拒绝日志及最终合并记录归档到本地 results/E7/CI-normal、CI-rejection、CI-recovery 等目录。PR 的 artifact/commit.txt 是实际检出的合并测试提交，run.json/headSha 是对应分支提交，两者分别保留。

当前会话的浏览器/桌面清单均为空，无法采集真实网页截图；原始 API、运行日志和 artifact 均完整保存。若要求图片形式，需在上述真实页面补拍截图。未生成图片代替截图。
