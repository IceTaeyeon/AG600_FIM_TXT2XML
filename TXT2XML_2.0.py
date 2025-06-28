#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
---------------------------------------------------
@File    : TXT2XML.py                              
@Author  : Zhai Jiabao Zhengzhou University           
@Date    : 2025-06-26                              
@Version : 1.01
@Desc    : AG600故障隔离程序编制 - TXT转XML批量转换工具
@Contact : 微信 18939569388
---------------------------------------------------
用于将TXT文档中的故障隔离程序转换为XML格式
每个DMC编码对应独立的XML文件
便于大家录入系统 提高效率
---------------------------------------------------
执行前需安装依赖 pathlib + argparse （使用pip install pathlib argparse）
执行方式：
将该文件放至txt文件目录，在目录中右键“在终端中运行”
输入python TXT2XML.py txt文件名
---------------------------------------------------
"""

import re
import os
from pathlib import Path
import argparse


class FaultIsolationConverter:
    def __init__(self):
        pass

    def read_txt_document(self, file_path):
        """读取TXT文档内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw = f.read()
                clean = re.sub(r'^[-—\s]*隔离程序结束[-—\s]*$', '', raw, flags=re.MULTILINE)
                return clean
        except Exception as e:
            print(f"读取TXT文档时出错: {e}")
            return None

    def parse_fault_procedures(self, content):
        """解析TXT版故障隔离程序"""
        procedures = []

        # 按DMC编码分割内容
        dmc_pattern = r'DMC：(AG600-A-\d{2}-\d+-\d+-\d+A-421A-A)'
        sections = re.split(dmc_pattern, content)

        # 处理分割后的内容
        for i in range(1, len(sections), 2):
            if i + 1 < len(sections):
                dmc_code = sections[i].strip()
                section_content = sections[i + 1].strip()

                # 解析单个故障程序
                procedure = self.parse_single_procedure(dmc_code, section_content)
                if procedure:
                    procedures.append(procedure)

        return procedures

    def parse_single_procedure(self, dmc_code, content):
        """解析单个故障隔离程序"""
        try:
            # 提取 A.故障描述
            fault_desc_match = re.search(r'A\.故障描述\s*\n*(.*?)(?=\n*B\.)', content, re.DOTALL)
            fault_description = fault_desc_match.group(1).strip() if fault_desc_match else "未知故障"

            # 提取 B.初步评估
            initial_eval_match = re.search(r'B\.初步评估\s*\n*(.*?)(?=\n*C\.)', content, re.DOTALL)
            initial_evaluation = initial_eval_match.group(1).strip() if initial_eval_match else ""

            # 提取 C.可能原因
            causes_match = re.search(r'C\.可能的原因\s*\n*(.*?)(?=\n*D\.)', content, re.DOTALL)
            possible_causes = self.parse_causes(causes_match.group(1).strip()) if causes_match else []

            # 提取 D.故障隔离程序
            procedure_match = re.search(r'D\.故障隔离程序\s*\n*(.*?)(?=----------|DMC：|$)', content, re.DOTALL)
            isolation_steps = self.parse_isolation_steps(procedure_match.group(1).strip()) if procedure_match else []

            return {
                'dmc_code': dmc_code,
                'fault_description': fault_description,
                'initial_evaluation': initial_evaluation,
                'possible_causes': possible_causes,
                'isolation_steps': isolation_steps
            }
        except Exception as e:
            print(f"解析DMC {dmc_code} 时出错: {e}")
            return None

    def parse_causes(self, causes_text):
        """解析可能的原因"""
        causes = []
        # 匹配编号的原因 (1), (2), etc.
        cause_pattern = r'\(\d+\)\s*(.*?)(?=\(\d+\)|$)'
        matches = re.findall(cause_pattern, causes_text, re.DOTALL)

        for match in matches:
            cause = match.strip().replace('\n', ' ')
            if cause:
                causes.append(cause)

        return causes

    def parse_isolation_steps(self, steps_text):
        """解析故障隔离步骤"""
        steps = []

        # 主要步骤模式 (1), (2), etc.
        main_step_pattern = r'\((\d+)\)\s*(.*?)(?=\(\d+\)|$)'
        main_matches = re.findall(main_step_pattern, steps_text, re.DOTALL)

        for step_num, step_content in main_matches:
            step_content = step_content.strip()

            # 解析子步骤
            sub_steps = self.parse_sub_steps(step_content)

            # 提取主步骤标题 - 获取第一行或第一个子步骤前的内容
            lines = step_content.split('\n')
            title = lines[0].strip()
            # 如果标题以(a)开头，说明没有单独的标题行
            if re.match(r'\([a-z]\)', title):
                # 从内容中提取主要操作作为标题
                if '更换' in step_content:
                    title = re.search(r'更换([^，。]+)', step_content)
                    title = f"更换{title.group(1)}。" if title else f"步骤{step_num}"
                elif '检查' in step_content:
                    title = re.search(r'检查([^，。]+)', step_content)
                    title = f"检查{title.group(1)}。" if title else f"步骤{step_num}"
                else:
                    title = f"步骤{step_num}"

            steps.append({
                'number': step_num,
                'title': title,
                'sub_steps': sub_steps
            })

        return steps

    def parse_sub_steps(self, step_content):
        """解析子步骤"""
        sub_steps = []

        # 子步骤模式 (a), (b), etc.
        sub_step_pattern = r'\(([a-z])\)\s*(.*?)(?=\([a-z]\)|$)'
        sub_matches = re.findall(sub_step_pattern, step_content, re.DOTALL)

        for sub_letter, sub_content in sub_matches:
            sub_content = sub_content.strip().replace('\n', ' ')

            # 处理参考文档：支持AG600-A-XX-...格式
            reference_pattern = r'AG600-A-\d{2}-\d+-\d+-\d+A-\d+A-A'
            references = re.findall(reference_pattern, sub_content)

            # 处理线路列表 - 按照实际TXT格式处理
            wire_pattern = r'检查以下线路：([^。(]+)'
            wire_match = re.search(wire_pattern, sub_content)
            wires = []
            if wire_match:
                wire_text = wire_match.group(1).strip()
                wires = [w.strip() for w in wire_text.split('、') if w.strip()]

            sub_steps.append({
                'letter': sub_letter,
                'content': sub_content,
                'references': references,
                'wires': wires
            })

        return sub_steps

    def parse_dmc_code(self, dmc_code):
    # def parse_dmc_code(dmc_code: str) -> dict | None:
        """
        将DMC编码解析为XML dmCode。

        支持的编码模式（8 段，用连字符 - 分隔）编写Word时格式一定要规范！:

        Example：
            AG600-A-25-52-00-02A-421A-A
            AG600-A-26-11-02-01A-051A-A
            AG600-A-33-13-02-01A-051A-A
            AG600-A-26-00-00-00A-320A-A
        """
        pattern = (
            r'^AG600-A-'          # 0  前缀
            r'(\d{2})-'           # 1  systemCode      (两位)
            r'(\d{2})-'           # 2  subSystemPair   (两位，后拆分为 subSystem / subSubSystem)
            r'(\d{2})-'           # 3  assyCode        (两位)
            r'(\d{2})A-'          # 4  disassyCode     (两位) + 固定变型 A
            r'(\d{3})A-'          # 5  infoCode        (三位) + 固定变型 A
            r'A$'                 # 6  itemLocationCode 固定 A
        )

        m = re.match(pattern, dmc_code)
        if not m:
            return None

        system_code      = m.group(1)            # 25 / 26 / 33 …
        sub_sys_pair     = m.group(2)            # 52 → “5”“2”
        assy_code        = m.group(3)            # 00 / 02 / …
        disassy_code     = m.group(4)            # 02 / 01 / …
        info_code        = m.group(5)            # 421 / 051 / …

        return {
            "assyCode":            assy_code,
            "disassyCode":         disassy_code,
            "disassyCodeVariant":  "A",
            "infoCode":            info_code,
            "infoCodeVariant":     "A",
            "itemLocationCode":    "A",
            "modelIdentCode":      "AG600",
            "subSubSystemCode":    sub_sys_pair[1],   # 第二位
            "subSystemCode":       sub_sys_pair[0],   # 第一位
            "systemCode":          system_code,
            "systemDiffCode":      "A",
        }

    def generate_xml(self, procedure):
        """生成完整的XML内容"""
        lines = []

        # 补全XML结构
        lines.append('<?xml version="1.0" encoding="UTF-8"?>')
        lines.append('<dmodule>')
        lines.append('<content>')
        lines.append('<procedure>')

        # commonInfo
        fault_desc = procedure['fault_description']

        if fault_desc.startswith("OMS故障代码为") and "故障名称为" in fault_desc:
            # 情况 1：OMS 格式
            match = re.search(r'故障名称为[“"](.+?)[”"]', fault_desc)
            fault_name = match.group(1) if match else fault_desc

        elif fault_desc.startswith("CAS告警信息为"):
            # 情况 2：CAS 格式
            match = re.search(r'CAS告警信息为[“"](.+?)[”"]', fault_desc)
            fault_name = match.group(1) if match else fault_desc

        else:
            # 情况 3：普通格式 （FMEA）
            fault_name = fault_desc

        fault_name = fault_name.rstrip("。")
        description = f"本程序给出了故障名为“{fault_name}”的故障隔离程序。"

        lines.append('<commonInfo>')
        lines.append(f'<para>{description}</para>')
        lines.append('</commonInfo>')
        lines.append('')

        # preliminaryRqmts部分
        lines.append('<preliminaryRqmts>')
        lines.append('<reqCondGroup>')
        lines.append('<noConds/>')
        lines.append('</reqCondGroup>')
        lines.append('')
        lines.append('<reqSupportEquips>')
        lines.append('<noSupportEquips/>')
        lines.append('</reqSupportEquips>')
        lines.append('')
        lines.append('<reqSupplies>')
        lines.append('<noSupplies/>')
        lines.append('</reqSupplies>')
        lines.append('')
        lines.append('<reqSpares>')
        lines.append('<noSpares/>')
        lines.append('</reqSpares>')
        lines.append('')
        lines.append('<reqSafety>')
        lines.append('<noSafety/>')
        lines.append('</reqSafety>')
        lines.append('</preliminaryRqmts>')
        lines.append('')

        # mainProcedure
        lines.append('<mainProcedure>')
        lines.append('')

        # 故障描述
        lines.append('<proceduralStep>')
        lines.append('<para>故障描述</para>')
        lines.append('')
        lines.append('<proceduralStep>')
        lines.append('')
        lines.append(f'<para>{procedure["fault_description"]}</para>')
        lines.append('</proceduralStep>')
        lines.append('</proceduralStep>')
        lines.append('')

        # 初步评估
        if procedure['initial_evaluation']:
            lines.append('<proceduralStep>')
            lines.append('<para>初步评估</para>')
            lines.append('')
            
            initial_content = procedure['initial_evaluation']
            
            # 调整 DMC 编码的正则表达式
            dmc_pattern = r'AG600-A-\d{2}-\d{2}-\d{2}-\d{2}A-\d{3}A-A'

            if re.search(r'\(\d+\)', initial_content):
                eval_steps = self.parse_isolation_steps(initial_content)
                
                for step in eval_steps:
                    lines.append('<proceduralStep>')
                    lines.append(f'<para>{step["title"]}</para>')
                    lines.append('')
                    
                    for sub_step in step['sub_steps']:
                        # 提取 DMC 编码
                        references = re.findall(dmc_pattern, sub_step['content'])
                        processed_content = self.process_para_content(
                            sub_step['content'], 
                            references,  # 解析DMC
                            sub_step['wires']
                        )
                        
                        lines.append('<proceduralStep>')
                        lines.append(f'<para>{processed_content}</para>')
                        lines.append('</proceduralStep>')
                    
                    lines.append('</proceduralStep>')
            else:
                # 确保所有 DMC 编码都被转换为 <dmRef>
                while True:
                    match = re.search(dmc_pattern, initial_content)
                    if not match:
                        break
                    dmc_code = match.group(0)
                    dm_ref_xml = self.create_dm_ref_xml(dmc_code)
                    initial_content = initial_content.replace(dmc_code, dm_ref_xml, 1)

                lines.append('<proceduralStep>')
                lines.append(f'<para>{initial_content}</para>')
                lines.append('</proceduralStep>')
            
            lines.append('</proceduralStep>')
            lines.append('')

        # 可能的原因
        if procedure['possible_causes']:
            lines.append('<proceduralStep>')
            lines.append('<para>可能的原因</para>')
            lines.append('')
            for cause in procedure['possible_causes']:
                lines.append('<proceduralStep>')
                lines.append(f'<para>{cause}</para>')
                lines.append('</proceduralStep>')
                lines.append('')
            lines.append('</proceduralStep>')
            lines.append('')

        # 故障隔离程序
        if procedure['isolation_steps']:
            lines.append('<proceduralStep>')
            lines.append('<para>故障隔离程序</para>')
            lines.append('')

            for step in procedure['isolation_steps']:
                lines.append('<proceduralStep>')
                lines.append(f'<para>{step["title"]}</para>')
                lines.append('')

                for sub_step in step['sub_steps']:
                    # 处理内容，添加dmRef和randomList
                    processed_content = self.process_para_content(
                        sub_step['content'],
                        sub_step['references'],
                        sub_step['wires']
                    )

                    lines.append('<proceduralStep>')
                    lines.append(f'<para>{processed_content}</para>')
                    lines.append('')
                    lines.append('</proceduralStep>')

                lines.append('</proceduralStep>')

            lines.append('</proceduralStep>')

        lines.append('</mainProcedure>')
        lines.append('')

        # closeRqmts
        lines.append('<closeRqmts>')
        lines.append('<reqCondGroup>')
        lines.append('<noConds/>')
        lines.append('</reqCondGroup>')
        lines.append('</closeRqmts>')

        lines.append('</procedure>')
        lines.append('</content>')
        lines.append('</dmodule>')

        return '\n'.join(lines)

    def create_dm_ref_xml(self, dmc_code):
        """创建dmRef XML片段"""
        ref_parts = self.parse_dmc_code(dmc_code)
        if not ref_parts:
            return dmc_code

        return f'''<dmRef>
<dmRefIdent>
<dmCode assyCode="{ref_parts["assyCode"]}" disassyCode="{ref_parts["disassyCode"]}" disassyCodeVariant="{ref_parts["disassyCodeVariant"]}" infoCode="{ref_parts["infoCode"]}" infoCodeVariant="{ref_parts["infoCodeVariant"]}" itemLocationCode="{ref_parts["itemLocationCode"]}" modelIdentCode="{ref_parts["modelIdentCode"]}"
        subSubSystemCode="{ref_parts["subSubSystemCode"]}" subSystemCode="{ref_parts["subSystemCode"]}" systemCode="{ref_parts["systemCode"]}" systemDiffCode="{ref_parts["systemDiffCode"]}"/>
</dmRefIdent>
</dmRef>'''

    def create_random_list_xml(self, wires):
        """创建randomList XML片段"""
        if not wires:
            return ""

        list_items = []
        for wire in wires:
            list_items.append(f'<listItem>\n<para>{wire}</para>\n</listItem>')
            list_items.append('')  #star

        return f'<randomList>\n{chr(10).join(list_items)}\n</randomList>'

    def process_para_content(self, content, references, wires):
        """处理para内容，添加dmRef和randomList"""
        processed_content = content

        # 处理参考文档
        if references:
            for i, ref in enumerate(references):
                dm_ref_xml = self.create_dm_ref_xml(ref)
                # 替换原始的AG600编码为dmRef XML
                processed_content = processed_content.replace(ref, dm_ref_xml)

        # 处理线路列表
        if wires:
            wire_list_xml = self.create_random_list_xml(wires)
            # 查找线路列表的位置并替换
            wire_pattern = r'检查以下线路：[^。]+'
            wire_replacement = f"检查以下线路：{wire_list_xml}"
            processed_content = re.sub(wire_pattern, wire_replacement, processed_content)

        return processed_content

    def convert_txt_to_xml(self, txt_file_path, output_dir):
        """主函数"""
        print(f"开始处理TXT文档: {txt_file_path}")

        # 读取TXT文档
        content = self.read_txt_document(txt_file_path)
        if not content:
            print("无法读取TXT文档内容")
            return False

        # 解析故障程序
        procedures = self.parse_fault_procedures(content)
        if not procedures:
            print("未找到有效的故障隔离程序")
            return False

        print(f"找到 {len(procedures)} 个故障隔离程序")

        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 生成XML文件
        success_count = 0
        for procedure in procedures:
            try:
                xml_content = self.generate_xml(procedure)

                # 保存XML文件
                filename = f"{procedure['dmc_code']}.xml"
                file_path = output_path / filename

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(xml_content)

                print(f"✓ 成功生成: {filename}")
                success_count += 1

            except Exception as e:
                print(f"✗ 生成 {procedure['dmc_code']} 时出错: {e}")

        print(f"\n转换完成！成功生成 {success_count}/{len(procedures)} 个XML文件")
        print(f"输出目录: {output_path.absolute()}")

        return success_count > 0


def main():
    parser = argparse.ArgumentParser(description='TXT故障隔离程序转XML工具')
    parser.add_argument('input_file', help='输入的TXT文档路径')
    parser.add_argument('-o', '--output', default='TXT2XML_OUTPUT', help='输出目录路径 (默认: TXT2XML_OUTPUT)')

    args = parser.parse_args()

    # 检查输入文件
    if not os.path.exists(args.input_file):
        print(f"错误: 输入文件 '{args.input_file}' 不存在")
        return

    # 创建转换器实例
    converter = FaultIsolationConverter()

    # 执行转换
    success = converter.convert_txt_to_xml(args.input_file, args.output)

    if success:
        print("转换成功完成！")
    else:
        print("转换失败，请检查输入文件格式和内容。")


if __name__ == "__main__":
    main()