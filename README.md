# 车身断面 DXF × SAE J1100 / J182 × DTS 语义对齐

静态网站（纯 HTML/JS，无依赖）。从 LS-DYNA 整车有限元模型切出车身断面，在浏览器里：

- 按语义图层组显示断面（白车身 / 车门 / 玻璃 / 内饰 / 座椅 …，每个零件一个 DXF 图层）
- **用户自定义参考点**：在 A 截面拖动 SgRP（H 点）和 AHP（踵点），或直接输入坐标
- **自动计算** J1100 布置尺寸：H30、L53、H61（8° 线 +102）、L50-2（前后排 SgRP 间距）、W3、W31、门槛高度、整车长/高
- **手动测量**：DTS 目录里的 manual 项，在截面上点两点（吸附顶点）
- DTS 核对表：实测 vs 目标 → 符合 / 不符合；每项对应约束的断面图层与包络含义
- 导出：带尺寸与 `[DTS]` 语义文字的 DXF（R12）、DTS 核对 CSV、参考点+测量 JSON

所有坐标均为 **SAE J182**：X 向后为正、Y 向左为正、Z 向上为正，单位 mm。

## 数据来源与声明
- 几何：2012 Toyota Camry 详细有限元模型 v5a，由 George Mason University 的 Center for Collision Safety and Analysis (CCSA) 开发，FHWA 资助。https://www.ccsa.gmu.edu/models/2012-toyota-camry 。这是逆向工程的仿真模型，不是丰田官方数据。
- `data/dts_catalog.json` 中的目标值是**示例**，不是任何主机厂 DTS，也不是 SAE 规定值。
- 标注“待核对”的 J1100 定义（H61、W3、W31 的简化做法）需对照 SAE J1100 原文。
- 默认 SgRP（前排）、SgRP2（第二排）由座椅泡沫几何估算：靠背前表面向前 135 mm、坐垫自由表面上方 60 mm；AHP 为踏板后方地板点。都是估算，请在页面上修正。
- 模型不含顶棚、地毯、密封条：H61 需手动输入顶棚厚度扣减；密封压缩量等项无法在本模型上测量。

## 目录
```
index.html               查看器
data/vehicle.json        车型、截面列表、每个 DXF 图层 → 零件/语义组、参考点默认值
data/dts_catalog.json    DTS 目录（键、标准代号、测量方法、目标、约束图层）
data/*.dxf               各截面（R12，每零件一层，图层名 = 语义组__PID_零件名）
tools/gen_sections.py    从 .key 生成上面的 data/
tools/vehicle.json       车型配置：轴向翻转、截面平面、参考点估算
tools/classify.py        零件名 → 语义组的规则（按需修改）
tools/keyparse.py        LS-DYNA *NODE / *ELEMENT_SHELL / *PART / *INCLUDE 读取
tools/section.py         平面切三角形网格、线段拼多段线、射线求交
tools/dxfout.py          无依赖 DXF R12 写出
```

## 换一个 .key 模型
需要 Python 3 + numpy。
1. 复制 `tools/vehicle.json`，按新模型修改：
   - `axis_sign`：把模型坐标换成 J182。模型 X 向前为正就写 `[-1,1,1]`；已是 J182 就写 `[1,1,1]`。
   - `sections`：每个截面的平面（`axis` x/y/z，`value` 为 **J182 坐标下**的值）。
   - `refs`：SgRP / SgRP2 / AHP。可直接给 x、z，或用 `estimate_from` 指定坐垫与靠背零件 PID 自动估算。
2. 看零件名，按需修改 `tools/classify.py` 的正则（不同建模团队命名差异很大）。
3. 生成：`python3 tools/gen_sections.py 你的模型.key 你的配置.json data/`
4. 若 DTS 项用了不同截面 id，同步修改 `data/dts_catalog.json` 的 `section`。
5. 本地预览：`python3 -m http.server`，打开 http://localhost:8000

读取器：壳单元（`*ELEMENT_SHELL`）和实体单元（`*ELEMENT_SOLID`，六面体/楔形/四面体，取外表面）参与切面，座椅泡沫、发动机等实体零件因此能切出闭合轮廓；梁、弹簧、质量单元不参与；支持固定列宽和逗号分隔格式与 `*INCLUDE`，不支持 `*INCLUDE_TRANSFORM`、`*NODE %` 长格式、`*PART` 以外的零件定义（如 `*PART_CONTACT`）。

## 发布
仓库根目录即站点。Settings → Pages → Deploy from a branch → `main` / `(root)`。
