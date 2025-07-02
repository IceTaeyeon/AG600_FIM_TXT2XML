# 故障隔离程序编制 TXT转XML文件批量转换工具

## 📌 项目介绍
  本工具用于将故障隔离程序TXT文件批量解析为符合Editor系统格式的XML文件，便于后续录入。

## ✨ 主要功能
- 按 DMC 编码 自动切分多个故障隔离程序
- 解析 故障描述、初步评估、可能的原因、隔离步骤
- 支持 参考DMRL编号转 <dmRef> 引用
- 支持 线路转 <randomList> 清单

## 📄 使用注意事项（Word 编辑要求）
- 为确保工具正常解析，请将Word文档另存为为UTF-8编码的TXT文件
- 为了使 TXT 格式能被正确解析，请确保 Word 编写时遵守以下要求
  - 每句话后一定要有句号！
  - 每个故障隔离程序开头需声明DMC编码，如
    <pre><code>DMC：AG600-A-26-11-00-02A-421A-A
    故障代码：26110151
    A.故障描述
      OMS故障代码为“26110151”，故障名称为“1发回路2-火警传感器故障”。
    ......</code></pre>
  - 每个步骤必须编号：如 (1), (2)，子步骤为 (a), (b)……
  - 完整步骤应写在一行，不要在句中使用Enter换行
  - 线路格式应标准统一，示例：
    <pre><code>参考AG600-A-26-11-02-01A-051A-A，检查以下线路：
      W2971-26108-22、W2971-26109-22</code></pre>
  - 删除文中所有空格（使用记事本替换功能）
  - 删除参考DMC编号的括号：如（AG600-A-26-11-02-01A-051A-A）要改为AG600-A-26-11-02-01A-051A-A
  - LRU 后不要保留件号：如 防火控制器（HKH17A） → 防火控制器

## 🚀 使用方法
- 确保你已安装 Python 环境，并安装依赖
  <pre><code>pip install pathlib argparse</code></pre>
  - 或将repository中的requirements.txt下载到本地，使用其安装依赖
   <pre><code>pip install -r requirements.txt</code></pre>
- 将py文件与TXT文件放在同一文件夹下
- 执行文件转换命令
  - 在文件夹目录中启用终端，执行以下命令（默认输出为同目录 TXT2XML_OUTPUT 文件夹）
  <pre><code>python TXT2XML.py 26-Example.txt</code></pre>
  - 或者指定输出目录
  <pre><code>python TXT2XML.py 26-Example.txt -o output_dir</code></pre>
- 结果输出
  - 转换完成后，会在指定目录下生成多个XML文件，每个对应一个DMC编号。

## 🔍 XML文件编辑操作
- 使用Editor软件打开故障隔离程序后，单击左上角“视图” → “XML源码”
- 在源码中找到 <content> 部分 （基本上都在58-59行）
![image](https://github.com/user-attachments/assets/fd8107b0-667d-438c-89d5-effdd6f206e2)
- 打开上一步生成的XML文件（推荐使用Visual Studio Code，使用Edge或Chrome浏览器进行预览与复制会无法保留xml的换行格式）
- 选中从第3行 <content> 开始后的所有内容，复制并粘贴到Editor的源码部分（替换掉原本的 <content> ）
![image](https://github.com/user-attachments/assets/3c328d6c-9981-4396-a9a7-1df1155e3591)
- 复制完毕后，单击左上角“视图” → “XML源码”，在弹出的窗口选择“是”，即可回到UI界面，查看故障隔离程序编辑结果
![image](https://github.com/user-attachments/assets/eeeab2a3-f79f-46ae-bc57-e7cc0d28555c)

## ⚠️ 已知问题
- （250702已修复）无法识别“初步评估”部分中 DMC 编号前后带括号的格式。

