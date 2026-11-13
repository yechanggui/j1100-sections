# 断面 DXF × SAE J1100 / J182 × DTS 语义对齐

静态网站（无后端、无外部依赖）：在浏览器里查看截面 DXF，并把每个尺寸与 **标准代号 / 驱动的断面图层 / DTS 键** 对齐。

- `index.html` 查看器（画布缩放平移、图层开关、点表格行高亮并缩放到对应尺寸、导出语义 CSV、可拖入自己的 DXF）
- `data/*.dxf` 示意断面（A 纵向中心截面、B 顶盖-侧围-车门横截面、C 门槛-密封条截面）
- `data/semantics.json` 语义对齐表（尺寸代号、定义、锚点、驱动图层、DTS 键、状态）
- `tools/gen_demo.py` 生成上述 DXF 和 JSON（仅标准库 + numpy）
- `tools/pipeline/` 从 LS-DYNA `.key` 切截面并按零件分层输出 DXF 的流水线（见 `build.py`）

## 重要说明
1. 演示几何和数值是**示意数据**，不是任何真实车型。
2. J1100 为付费标准，条目定义写作“待核对”的需对照标准原文；`L34*` 是简化。
3. `dts_target` 留空，请填入贵司 DTS 目标/公差；`dts_key` 是对齐接口，可按贵司命名改写。
4. 尺寸在 DXF 中以线/箭头/文字绘制（非 DIMENSION 实体），语义信息以 `[DTS] key` 文字（图层 `ANNOT-DTS`）+ `semantics.json` 携带。

## 图层命名
`BIW-*` 白车身 · `DOOR-*` 车门 · `GLASS-*` 玻璃 · `TRIM-*` 内饰 · `SEAL-*` 密封条 · `SEAT-*` 座椅 · `REF-POINTS` 参考点 · `DIM-J1100` / `DIM-OEM` 尺寸 · `ANNOT-DTS` DTS 语义

## 本地运行
`python3 -m http.server` 然后打开 http://localhost:8000
