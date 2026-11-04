# MagineCanvas Fight Director

**AI 打戏导演 Skill · 连贯动作设计 · 镜头编排 · 无限画布生产规划**

> 一句话制作可分镜、可分段、可批量生产的电影级打戏方案。
>
> 当前版本：v0.1.0（独立原创实现）｜语言：中文｜适用：Codex 等支持 `SKILL.md` 的 Agent

`maginecanvas-fight-director` 把打戏需求拆解成四种可执行内容：**战斗调度、镜头时间轴、图片/视频节点提示词、质量检查表**。为 MagineCanvas 这样的无限画布制作环境提供人工可执行的节点布局方案，尤其考虑角色复用、分镜分段和框选批量生成。

本仓库不是原项目的改名镜像，没有复制第三方仓库的代码、说明文字或素材。灵感来源说明见 [NOTICE.md](NOTICE.md)。

## 为什么适合 MagineCanvas

| 能力 | 本 Skill 如何交付 |
|---|---|
| 一句话写打戏 | 生成冲突目标、动作设计、交锋节奏与镜头表 |
| 角色一致性 | 固定角色、衣着、武器和位置的识别卡，逐镜延续状态 |
| 电影分镜 | 秒级时间轴、景别、机位、镜头运动与转场 |
| 可复制提示词 | 每镜图像提示词、视频提示词和需避免的失真清单 |
| 无限画布节点 | 公共参考资产 → 关键帧 → 视频生成 → 质检 → 剪辑 |
| 批量生产 | 用 `batch_group` 组织同类节点，指导手动框选并批量生成 |
| 精准诊断 | 修复越轴、动作跳帧、武器错手、接触点不明等问题 |

**功能边界**：Skill 能输出导演方案、提示词、通用 JSON 节点计划；**不会自动访问 MagineCanvas、调用模型、充值 API 或替你操作画布**。`scripts/build_node_plan.py` 只做确定性的节点结构生成，JSON **不是** MagineCanvas 官方原生导入格式。生成视频仍需在你的画布或视频平台执行。

## 快速安装

### 使用 Codex Skill 安装器

向 Codex 提交：

```text
使用 skill-installer，从我的 GitHub 仓库安装 Skill：
https://github.com/Magine1921/maginecanvas-fight-director
SKILL.md 位于仓库根目录，安装名为 maginecanvas-fight-director。
```

仓库发布前，也可以手动将整个文件夹放在 `~/.codex/skills/maginecanvas-fight-director`；使用支持自定义 Skills 的其他 Agent 时，按其目录要求放置 `SKILL.md`。

### 调用示例

```text
使用 $maginecanvas-fight-director：
拍一段24秒古桥雨夜双人兵器对决，女性双刀师对男性长棍师。
动作要有可见的拦截、受力与反击，最后夺棍而不伤人。
给我导演分镜表 + 每镜生图和生视频提示词 + MagineCanvas 无限画布节点方案。
```

```text
使用 $maginecanvas-fight-director，
把这份打戏拆成 6 个镜头，每镜独立生成视频。
请锁定主角面貌、服装与武器，并列出需要框选批量生成的节点。
```

```text
使用 $maginecanvas-fight-director，诊断下面的动作提示词：
（粘贴提示词）
重点检查人物瞬移、180 度轴线、肢体/武器错位、接触与反应缺失。
只输出问题、修复建议和可替换短句。
```

## 在无限画布上落地

1. 左侧放 **公共资产区**：角色A参考、角色B参考、场景参考、统一画风。
2. 中间按镜头顺序放 **关键帧节点**：`S01-KF`、`S02-KF`……；每镜使用相同公共角色参考。
3. 关键帧后接 **视频节点**：`S01-VIDEO`、`S02-VIDEO`……；相邻镜头分别写明确的入场/离场状态。
4. 右侧放 **质检与剪辑区**：依次检查画面可读性、角色状态和运动连续性；必要时重生成单镜。
5. 用 MagineCanvas 的框选批量生成能力，对同类关键帧节点或同类视频节点分别框选操作。**不要**把素材参考节点、关键帧节点与视频节点混在同一个批次。

更详细的画布布局与制作步骤见 [references/canvas-production.md](references/canvas-production.md)。

## 可运行的本地示例（Python 3.10+，无第三方依赖）

```bash
python scripts/build_node_plan.py examples/brief-rainy-bridge.json \
  --json-out examples/plan-rainy-bridge.json \
  --md-out examples/plan-rainy-bridge.md
python scripts/validate_node_plan.py examples/plan-rainy-bridge.json
python -m unittest discover -s tests -v
```

- 输入 JSON 是结构化拍摄简报，包含角色、场景、镜头动作等。
- 输出 JSON 是**通用节点草案**，用于读取、二次开发或未来自建 MagineCanvas 适配器。
- 输出 Markdown 把每镜图片/视频提示词分开，适合手动复制到画布。
- 脚本不会自动调用 AI；电影级动作创意由 Skill 和 Agent 根据剧情推导。

### 文件结构

```text
maginecanvas-fight-director/
├── SKILL.md                         # Agent 调用的入口与工作规范
├── README.md                        # 开源主页
├── LICENSE                          # 本仓库原创内容 MIT 许可
├── NOTICE.md                        # 原创范围、灵感来源说明
├── agents/openai.yaml               # Agent 展示信息
├── references/
│   ├── action-direction.md          # 动作连续性与摄影原则
│   ├── canvas-production.md         # 画布节点与批量生产
│   ├── delivery-formats.md          # 输出格式与数据结构
│   └── diagnosis.md                 # 质量检查与故障修复
├── scripts/
│   ├── build_node_plan.py           # 简报 → 通用节点 JSON + Markdown
│   └── validate_node_plan.py        # 检验通用节点 JSON
├── examples/
│   ├── brief-rainy-bridge.json      # 原创示例简报
│   ├── plan-rainy-bridge.json        # 已生成节点草案
│   └── plan-rainy-bridge.md          # 已生成提示词
└── tests/test_plan.py               # 自动化基础校验
```

## 版本路线

- **v0.1（本版）**：独立 Skill、结构化分镜、节点规划、批量分组、质量诊断、脚本与测试。
- **后续可做**：根据 MagineCanvas 正式 API / 导入规范开发原生导入器；按照已接入的视频模型的真实能力适配单段时长、参考图数量与分辨率；增加节点运行状态追踪。

## 来源、授权和商标

新写的指令、脚本和示例按 [MIT](LICENSE) 开源。此许可证**不授权**任何未包含在本仓库的第三方内容。有关对独立灵感来源的说明请查看 [NOTICE.md](NOTICE.md)。MagineCanvas 的产品名称在本项目中用于标识目标制作环境，非对第三方视频模型的官方背书。

欢迎提 Issue、提交 PR，一起改进打戏在无限画布中的可复用制作流程。