# Design

> Samantha 前端视觉设计系统。遵循 Google Stitch DESIGN.md 格式。
> 最后更新: 2026-06-07 — 琥珀色 · 思源黑体 · 暖渐变

## Color Palette

琥珀为主色，米白为基底，营造"深夜书房台灯"般的温暖安静感。

| Token | 用途 | 色值 |
|-------|------|------|
| `--bg-primary` | 主背景（顶部微暖渐变） | `#faf9f7` → `#faf7f2` |
| `--bg-surface` | 卡片/面板背景 | `#f3f0eb` (stone) |
| `--bg-bubble-user` | 用户气泡 | `#e8e4dc` (fog) |
| `--bg-bubble-sam` | Samantha 气泡 | `#ffffff` |
| `--ink-primary` | 正文文字 | `#2c2c2a` (soft ink) |
| `--ink-secondary` | 辅助文字 | `#7a7874` (muted stone) |
| `--accent` | 强调色 | `#c4956a` (amber) |
| `--accent-soft` | 强调弱化 | `#dcc4a8` (pale amber) |
| `--border` | 分割线 | `rgba(196, 149, 106, 0.18)` (amber tint) |
| `--shadow-sam` | Sam 气泡阴影 | `0 1px 3px rgba(0,0,0,0.04), 0 2px 8px rgba(0,0,0,0.03)` |
| `--safety-warn` | 安全警告 | `#d4a574` (amber clay) |
| `--safety-block` | 安全拦截 | `#c48b7a` (dusty rose) |

### 情绪色彩映射

| 情绪 | 色值 |
|------|------|
| happy | `#a8c97e` (warm green) |
| sad | `#8fa4c4` (dusty blue) |
| angry | `#c48b7a` (dusty rose) |
| anxious | `#d4a574` (amber clay) |
| tired | `#b8b0a8` (stone grey) |
| neutral | `#dcc4a8` (pale amber) |

## Typography

全局统一思源黑体（Source Han Sans CN），无衬线，清晰利落。

| Token | Font Stack | Size / Weight |
|-------|-----------|---------------|
| `--font-ui` | `"Source Han Sans CN", "Noto Sans SC", "Inter", sans-serif` | 14px / 500 |
| `--font-mono` | `"JetBrains Mono", monospace` | 13px / 400 |

### 字号层级

| Level | Size | Weight | Line Height | 用途 |
|-------|------|--------|-------------|------|
| h1 | 16px | 600 | 1.3 | 页面标题（Header） |
| body | 16px | 400 | 1.6 | 对话正文 |
| caption | 14px | 400 | 1.5 | 面板正文 |
| label | 12px | 500 | 1.4 | 面板标签、badge |

## Spacing

基于 4px 的缩放系统。

| Token | Value | 用途 |
|-------|-------|------|
| `--space-xs` | 4px | 内部紧凑间距 |
| `--space-sm` | 8px | 元素内间距 |
| `--space-md` | 16px | 气泡内边距 |
| `--space-lg` | 24px | 区块间距 |
| `--space-xl` | 32px | 面板间距 |
| `--space-2xl` | 48px | 页面边距 |

## Layout

```
┌──────────────────────────────────────────────┐
│  Header (48px) — amber 半透明底线             │
│  Samantha · 情感陪伴               [状态]     │
├──────────────────────┬───────────────────────┤
│                      │  Emotion              │
│   Chat Area (65ch)   │  ┌─────────────────┐  │
│   背景: 琥珀微渐变     │  │ 微光圆环 (默认可见)│  │
│   ┌──────────────┐   │  │ valence ○────   │  │
│   │ user bubble   │──▶│  │ arousal ○───   │  │
│   └──────────────┘   │  │ label: 平静      │  │
│   ◀─┌──────────────┐ │  └─────────────────┘  │
│     │ sam bubble    │ │                       │
│     │ 双层阴影       │ │  Memory              │
│     └──────────────┘ │  ┌─────────────────┐  │
│                      │  │ · 可展开卡片     │  │
│   Input              │  └─────────────────┘  │
│   ┌──────────────┐   │                       │
│   │ 输入框  [发送] │   │                       │
│   └──────────────┘   │                       │
├──────────────────────┴───────────────────────┤
│  空状态: "晚上好 — 我是 Samantha"              │
└──────────────────────────────────────────────┘
```

- 聊天区最大宽度: 65ch
- 右侧面板宽度: 240px
- 移动端 (<1024px): 面板隐藏，聊天区全宽
- 分割线使用 amber 半透明色（`rgba(196,149,106,0.12~0.18)`）

## Components

### ChatBubble

用户气泡：右对齐，最大宽度 70%，背景 `--bg-bubble-user`，不对称圆角（左上/左下 16px，右上/右下 4px）。

Samantha 气泡：左对齐，最大宽度 70%，背景白色，不对称圆角（右上/右下 16px，左上/左下 4px），双层阴影（`0 1px 3px + 0 2px 8px`）。

### ChatBox

空状态：居中展示 emoji "晚上好" + "我是 Samantha，今天过得怎么样？"，字体 15px，暖灰色。
有新消息时自动滚动到底部（smooth behavior）。

### EmotionPanel

- 背景 `--bg-surface`，面板圆角 16px
- 默认显示"平静"状态的半透明圆环（opacity 0.5），不隐藏
- 有真实情绪数据时圆环和文字恢复 100% 不透明度
- 情绪标签大字 18px，带颜色指示
- Valence/Arousal 双轴水平条

### MemoryPanel

- 背景 `--bg-surface`，面板圆角 16px
- 记忆条目为白色卡片（圆角 12px），hover 时淡琥珀背景
- 可点击展开/收起原文，箭头图标 `▸` / `▾`
- 空状态显示"暂无相关记忆"

### ChatInput

- 全宽输入框，背景 `--bg-surface`，圆角 16px
- Focus 时显示 2px 琥珀色 ring
- 发送按钮：琥珀色背景，hover 时加深至 `#b8875e`
- 支持 Enter 发送，Shift+Enter 换行

## Motion

节制的微动，尊重 `prefers-reduced-motion`。

| 场景 | 动画 | Duration | Easing |
|------|------|----------|--------|
| 气泡出现 | `opacity` + `translateY(4px)` → 0 | 200ms | ease-out |
| 情绪指针移动 | `width` 过渡 | 400ms | ease-out |
| 发送按钮 hover | `background` 暗化 | 150ms | ease |
| `prefers-reduced-motion` | 所有动画 → instant | 0ms | — |

## Border Radius

大圆角策略，柔和包容：

| 元素 | 圆角 |
|------|------|
| 气泡（主要圆角） | 16px |
| 气泡（次要圆角） | 4px |
| 面板 | 16px |
| 输入框 | 16px |
| 按钮 | 12px |
| 记忆卡片 | 12px |
| 工具标签/badge | 8px |

## References

- **Notion** — 安静感：内容优先，暖灰白基底，界面向后退
- **Craft** — 排版：精致的字体层级，适度的留白呼吸感
- **Apple Messages** — 气泡：不对称圆角的方向感，大圆角的柔和触感

## 改动记录

- 2026-06-06: 初始版本，鼠尾草绿 + Noto Serif SC 正文
- 2026-06-07: 主色切换为琥珀 `#c4956a`；字体统一思源黑体；新增暖渐变背景、琥珀半透明分割线、气泡双层阴影、空状态问候语、情绪面板默认可见
