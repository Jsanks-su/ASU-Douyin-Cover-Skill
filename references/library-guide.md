# 图库入口

本包包含用户提供的170张书籍翻拍参考图，采用本会话完成的v2校正结果制作便携副本。编号与用户原参考图一致。参考副本最长边1600像素，原尺寸校正图与原始照片仍在用户原交付目录。

所有图片与索引均为相对路径，安装或移动这个Skill后仍能使用，不依赖本次聊天的工作目录。

- 完整索引：[catalog.json](catalog.json)。包含编号、来源文件、图像路径、粗分类、适配优先级和联系表位置。
- 联系表：`../assets/contact-sheets/sheet-01.jpg` 至 `sheet-06.jpg`，按编号每页30张。
- 选定参考图：`../assets/posters/ref-001.jpg` 至 `ref-170.jpg`。

可先用辅助脚本列出参考，或直接读取索引并查看联系表：

```text
python scripts/library.py --tags typography minimal --limit 12
python scripts/library.py --id 151
python scripts/library.py --sheets
```

标签只是缩小视觉查找范围，不是必须遵守的版式模板。最终选图必须查看实际图像。

| 标签 | 用途 |
| --- | --- |
| typography | 以大字、字形、强文字层级组织画面 |
| geometric | 几何图形、色块、抽象构成 |
| photographic | 人物或其他摄影主体与排字结合 |
| illustration | 插画、绘画、图形人物与装饰语言 |
| collage | 拼贴、多块内容、网格组合 |
| editorial | 刊物封面、文字版面、资料页 |
| minimal | 少量元素、单一主体或强留白 |
| pattern | 重复、网格、纹理或图案构成 |

`recommended_start` 标出容易迁移到图片加中文文案的起步参考，不限制用户选择其他编号。通常先查看少量候选，再打开一张选定参考，不需要一次加载170张图片。

应保留用户这一张图片的内容依据。使用拼贴类参考时，可以组织这张图的不同有效局部；不能为填满拼版而生成额外案例、人物或界面。
