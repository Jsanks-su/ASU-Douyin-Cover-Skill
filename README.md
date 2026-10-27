# 阿苏 · 抖音海报封面

**一张图片 + 一段文案 → 一张有海报排版依据的抖音封面。**

`douyin-reference-cover` 是一个 Codex Skill：自动从随包的 **170 张书籍海报参考图**中选一张，将用户图片与该参考一起用于图生图，再检查中文文案和抖音主页裁切。当前版本 **0.1.1**。

## 实际示例

输入：一张面条照片，以及「吃面条得用筷子，用AI得靠脑子。」

| 本次海报参考 REF-021 | 成品在主页中的裁切预览 |
| --- | --- |
| <img src="assets/posters/ref-021.jpg" width="420" alt="REF-021 原海报参考" /> | <img src="examples/noodle-ai-profile-preview.jpg" width="315" alt="封面主页预览" /> |

[下载示例上传封面：1080×1920 JPG](examples/noodle-ai-upload.jpg)

## 使用

将整个仓库放到 Codex 的 `skills/douyin-reference-cover` 目录，保留 `SKILL.md`、`assets`、`references`、`scripts` 和 `agents` 的相对位置。Windows 常用位置为 `%USERPROFILE%/.codex/skills/douyin-reference-cover`。已安装旧版本时先备份，更新这个 Skill 的文件。

提供图片并说：

> 使用 $douyin-reference-cover。标题：吃面条得用筷子，用AI得靠脑子。

Skill 自动选参考、完成封面并交付上传母版和同一设计的主页裁切预览。也可以指定「这次用 REF-021」。无需每次先选风格或填写设计问卷。

文案默认原样使用，允许调整断行和关键词层级。参考海报中的品牌、人物和外文不自动带入成品。范围限定为这套参考库驱动的封面制作及修改。

## 上传与主页展示

- 默认上传母版：**1080×1920，9:16，sRGB**。
- 依据本次用户实屏，模拟中央 **1080×1440，3:4** 的主页作品格；上下各240像素只放可裁背景。
- 从真实母版裁切预览，再缩到约320×427，检查全文可读、主体清晰，并避开左下播放量区域。
- 这是本账户截图支持的工作默认值，实际发布入口的裁切预览优先；不能将它宣称为所有抖音入口的统一官方规范。示例尚未实际上传验证。

完整规则见 [platform-framing.md](references/platform-framing.md)。

## 参考图库

所有 **170 张 JPG 与6张总览图都已直接包含在仓库**，没有外部下载链接依赖。参考副本最长边1600像素，来源是用户提供的书籍拍摄照片，经透视、裁切、白平衡与曲面校正后整理。

| 总览 | 范围 |
| --- | --- |
| [第1页](assets/contact-sheets/sheet-01.jpg) | REF-001～030 |
| [第2页](assets/contact-sheets/sheet-02.jpg) | REF-031～060 |
| [第3页](assets/contact-sheets/sheet-03.jpg) | REF-061～090 |
| [第4页](assets/contact-sheets/sheet-04.jpg) | REF-091～120 |
| [第5页](assets/contact-sheets/sheet-05.jpg) | REF-121～150 |
| [第6页](assets/contact-sheets/sheet-06.jpg) | REF-151～170 |

[浏览全部单图](assets/posters) · [索引与标签](references/catalog.json) · [选图说明](references/library-guide.md)

## 工具与依赖

生成需要宿主提供可接收参考图片的图像生成/编辑工具，优先使用 Codex 内置图像工具。仅安装 Skill 不会自动提供生图服务；费用随实际宿主工具计费。

可选检索脚本仅需 Python 标准库；裁切检查脚本另需 Pillow：

```text
python scripts/library.py --id 21
python scripts/library.py --tags photographic typography --limit 8
python scripts/check_framing.py cover.png --out-dir framing-check
```

裁切脚本仅检查尺寸、裁切和可选标题框位置，不负责生成图像，也不能证明文字正确或通过平台审核。

## 素材来源与权利

参考图为用户提供的书籍海报翻拍整理，用于观察构图、字体层级与视觉组织。原海报、字体、品牌等权利归各自权利人；仓库公开展示不意味着对原作品授予再许可。

## 验证记录

- Skill 结构校验通过；170张单图、6张总览图均完成解码与相对路径检查。
- 检索脚本的编号、标签、总览与无效编号处理通过。
- 裁切脚本验证了正常构图、标题出框、左下覆盖和非默认尺寸的识别。
- 已完成本页实际图生图示例，并目视核对文案、1080×1920母版和3:4小图。未执行线上发布。
