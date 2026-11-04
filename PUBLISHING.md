# 把此项目发布到你的 GitHub 仓库

项目名称：`maginecanvas-fight-director`。该压缩包是独立原创实现，不包含上游仓库文件。

## 通过 GitHub CLI（macOS / Linux）

1. 登录 GitHub，确保已安装 `git` 和 `gh`（GitHub CLI）。
2. 解压 ZIP，进入 `maginecanvas-fight-director` 目录。
3. 在终端执行：

```bash
git init -b main
git add .
git commit -m "feat: initial MagineCanvas Fight Director skill"
gh auth login
gh repo create maginecanvas-fight-director --public --source=. --remote=origin --push
```

> 如果 `gh auth login` 已完成，可以略过。仓库名称占用或已有同名仓库时，不要覆盖旧内容；先确认远端仓库地址及历史。

## 通过 GitHub 网页创建

1. 在 GitHub 点击 **New repository**，填写 `maginecanvas-fight-director`，可设为 Public。
2. **不要**勾选初始化 README、LICENSE、.gitignore，因为压缩包里已提供这些文件。
3. 按创建后的 GitHub 页面提示，将解压目录中的文件提交并推送至新仓库。

## 发布前检查

```bash
python -m unittest discover -s tests -v
python scripts/validate_node_plan.py examples/plan-rainy-bridge.json
```

- 仓库公开说明中可写：`Open-source AI fight choreography skill for MagineCanvas-style infinite canvas workflows; storyboard, character consistency, image/video prompts and batch planning.`
- 建议 Topics：`agent-skills`, `ai-video`, `fight-choreography`, `storyboard`, `maginecanvas`, `workflow`, `aigc`。
- 确认没有上传任何真实密钥、客户素材或个人数据。
- 当前 `NOTICE.md` 载明灵感来源；不得把没有授权的第三方文件引入后重新标记成 MIT。

## Codex 手动安装

发布后（或在本地测试）可以使用：

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
git clone "https://github.com/Magine1921/maginecanvas-fight-director.git" \
  "${CODEX_HOME:-$HOME/.codex}/skills/maginecanvas-fight-director"
```

重新打开 Codex 会话或按其 Skill 发现规则刷新；调用 `$maginecanvas-fight-director`。