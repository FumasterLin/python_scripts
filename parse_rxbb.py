# rxbb 导出 xml， xml 转成 html
# 解析html， 生成头文件
# author: Yandong.Lin
# date  : 2021-03

from bs4 import BeautifulSoup
import re


def write_struct(file, name, addr, members, indent=''):
    # 判断是否是地址
    if len(members) == 1:
        for field, bits in members.items():
            if "addr" in field or int(bits) == 32:
                str = '%sRK_U32 %s;\n' % (indent, field)
                file.write(str)
                return
    str = '%sstruct {\n' % (indent)
    file.write(str)
    max_len = 0
    for field in members.keys():
        if len(field) > max_len:
            max_len = len(field)
    for field, bits in members.items():
        str = '%s    RK_U32 %s %4s %d;\n' % (indent, field.ljust(max_len), ':', bits)
        file.write(str)

    str = '%s} %s;\n' % (indent, name.lower())
    file.write(str)


def write_union(file, addr, names, name2members):
    reg_num = int(addr, 16) / 4
    str = 'union {\n'
    file.write(str)
    write_struct(file, names[0], addr, name2members[names[0]], "    ")
    str = '\n'
    file.write(str)
    write_struct(file, names[1], addr, name2members[names[1]], "    ")
    str = '} reg%04d;\n' % (reg_num)
    file.write(str)


def write_comment(file, comment):
    str ='\n/* %s */\n' % (comment)
    file.write(str)


def write_reserved(file, addr_s, addr_e):
    reg_s = int(addr_s, 16) / 4 + 1
    reg_e = int(addr_e, 16) / 4 - 1
    addr_s_int = int(addr_s, 16)
    addr_e_int = int(addr_e, 16)
    if reg_e - reg_s > 0:
        write_comment(file, hex(addr_s_int+4) + ' - ' + hex(addr_e_int-4))
        str = 'RK_U32 reserved%d_%d[%d];\n' % (reg_s, reg_e, reg_e - reg_s + 1)
    else:
        write_comment(file, hex(addr_s_int+4))
        str = 'RK_U32 reserved_%d;\n' % (reg_s)
    file.write(str)


def write_header_file(file_name, addr2name, name2members):
    file = open(file_name, 'w')
    addr_pre = '0x0'
    addr_cur = '0x0'
    for addr, name_list in addr2name.items():
        addr_cur = addr
        reg_diff = (int(addr_cur, 16) / 4) - (int(addr_pre, 16) / 4)
        if reg_diff > 1:
            write_reserved(file, addr_pre, addr_cur)
        write_comment(file, addr + " reg" + str(int(addr_cur, 16) // 4))
        if len(name_list) == 2:
            write_union(file, addr, name_list, name2members)
        else:
            write_struct(file, name_list[0], addr, name2members[name_list[0]])
        addr_pre = addr_cur
    file.close()


def parse_html(file_name):
    print("read htm file start...")
    file = open(file_name, 'rb')
    html = file.read()
    bs = BeautifulSoup(html,"html.parser")
    print("read htm file done...")
    log_en = False

    addr2name = {}
    name2members = {}
    # print(bs.table)
    tables = bs.find_all('table')
    print("parse start...")
    for table in tables:
        # 解析寄存器名字和地址
        reg_names = table.find_all('p', class_="regname")
        reg_addrs = table.find_all('p', class_='regaddrvalue')
        name = ''
        addr = ''
        name_list = []
        for reg_name, reg_addr in zip(reg_names, reg_addrs):
            addr = reg_addr.get_text()
            name = reg_name.get_text()
            if "VEPU_" in name:
                name = name[5:]
            name_list.append(name)
            if log_en:
                print(reg_name.get_text(), reg_addr.get_text())
            if addr in addr2name:
                name_list = addr2name[addr]
                name_list.append(name)
                addr2name[addr] = name_list
            else:
                addr2name[addr] = name_list


            # str ='\n/* %s */\n' % (reg_addr.get_text())
            # file.write(str)
            # str = 'struct %s {\n' % (reg_name.get_text())
            # file.write(str)

        reg_fields = table.find_all('p', class_="regfield")
        reg_fieldposs = table.find_all('p', class_='regfieldpos')

        reg_members = {}
        count = 0
        # 获取寄存器field和bits
        for reg_field, reg_fieldpos in zip(reg_fields[::-1], reg_fieldposs[::-1]):
            #print(reg_fieldpos.get_text(), reg_field.get_text())
            reg_field = reg_field.get_text()
            pos_text = reg_fieldpos.get_text()
            pos = pos_text.split(":")
            if len(pos) == 2:
                bits = int(pos[0]) - int(pos[1]) + 1
                if log_en:
                    print(pos_text, bits, reg_field.get_text())
            else:
                bits = 1
                if log_en:
                    print(pos_text, bits, reg_field.get_text())
            # 判断是否有重复的寄存器名字
            if reg_field in reg_members:
                count = count + 1
                reg_field = ''.join([reg_field, str(count)])
            reg_members[reg_field] = bits

        name2members[name] = reg_members

        #     str = '    RK_U32 %20s %5s %d\n' % (reg_field.get_text().ljust(20), ':', bits)
        #     file.write(str)
        # for reg_name in reg_names:
        #     str = '}%s;\n' % (reg_name.get_text().lower())
        #     file.write(str)
    file.close()
    print("parse done...")
    return [addr2name, name2members]

if __name__ == "__main__":

    regs = parse_html("./VEPU.htm")
    addr2name = regs[0]
    name2members = regs[1]
    print("generate header file start...")
    write_header_file("header.h", addr2name, name2members)
    print("generate header file done...")

