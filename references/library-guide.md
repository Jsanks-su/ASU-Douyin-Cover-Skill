# 图库入口

本包包含170张书籍翻拍海报的校正参考副本，最长边1600像素。全部参考、总览与索引均随包提供，选图和生成不需要访问原始照片、历史交付目录或聊天记录。

所有图片与索引均为相对路径，安装或移动这个Skill后仍能使用，不依赖安装前的工作目录。

- 文件索引：[catalog.json](catalog.json)。编号、来源、图像路径、粗分类与联系表位置；旧 `recommended_start` 仅为手动浏览起点。
- 视觉档案：[matching-index.json](matching-index.json)。170项均有构图家族、主体图像类型、观察到的角色/配色及推断的插图方式、长宽比、标题容量、信息密度、改编提示与图片哈希。观察和推断分开，证据级别写在 `review`。
- 创意档案：[creative-index.json](creative-index.json)。逐张打开全图后提取的独特优点、核心创意、必要关系、适配条件、失败方式、生图锚点与验收项；区分可见观察、解读和用户反馈依据，不冒充作者意图。
- [创意对照表](creative-atlas.md)：按编号比较170项；[创意阅读规则](creative-reading.md)说明如何让这些关系参与选择、提示词和实图验收。
- 联系表：`../assets/contact-sheets/sheet-01.jpg` 至 `sheet-06.jpg`，按编号每页30张。
- 选定参考图：`../assets/posters/ref-001.jpg` 至 `ref-170.jpg`。

制作新封面先按[原图匹配](matching.md)建档并检索；只按编号看图、浏览图库时可用原有入口：

```text
python -X utf8 scripts/library.py --profile /absolute/path/source-profile.json --limit 12
python -X utf8 scripts/library.py --profile /absolute/path/source-profile.json --reference 151
python scripts/library.py --tags typography minimal --limit 12
python scripts/library.py --id 151
python -X utf8 scripts/creative.py --id 112
python -X utf8 scripts/creative.py --mechanism cross_plane
python -X utf8 scripts/creative.py --mechanisms
python scripts/library.py --sheets
```

`--profile` 扫描全库结构条件，不依赖粗标签。脚本给出候选、兼容性分项、适配理由、风险和实际图片路径，最终选择仍须打开原图与候选实图复排；不使用分数直接决定生成。`--tags` 只是手动浏览过滤器，不是自动匹配流程。

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

`single_design` 是单个设计；`collection_page` 是多设计资料页，必须选择具体子图；`specimen_page` 是字体/技术/内页标本，须明确借用的版式与信息支撑。资料页不是可以直接生成的整页模板。无需一次加载170张完整图片，先检索，再对候选看全图。

维护图库时，变更图片后要重新看图更新档案及 `image_sha256`，并重跑检索检查。联系表观察不足以确认细字、位置与子框；新增条目不能仅从旧标签猜出详细版式。

创意档案同样绑定实际图片哈希，改图后须同步复看。`--id` 返回完整创意记录；候选列表只返回比较用简卡，不能用简卡替代生成前的完整阅读。原结构索引的联系表证据级别与新版逐张创意阅读的全图证据级别分别保留，不倒改旧验证历史。

应保留用户这一张图片的内容依据。使用拼贴类参考时，可以组织这张图的不同有效局部；不能为填满拼版而生成额外案例、人物或界面。
