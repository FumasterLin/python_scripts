from bs4 import BeautifulSoup
import re

if __name__ == "__main__":
    file = open('./VEPU.htm', 'rb')
    html = file.read()
    bs = BeautifulSoup(html,"html.parser") # 缩进格式
    file = open("header.h",'w')
    log_en = False
    # print(bs.table)
    tables = bs.find_all('table')
    for table in tables:
        reg_names = table.find_all('p', class_="regname")
        reg_addrs = table.find_all('p', class_='regaddrvalue')

        for reg_name, reg_addr in zip(reg_names, reg_addrs):
            if log_en:
                print(reg_name.get_text(), reg_addr.get_text())
            # str ='%10s %10s %10s \n' % ('ID','Name','Record')
            str ='\n/* %s */\n' % (reg_addr.get_text())
            file.write(str)
            str = 'struct %s {\n' % (reg_name.get_text())
            file.write(str)

        reg_fields = table.find_all('p', class_="regfield")
        reg_fieldposs = table.find_all('p', class_='regfieldpos')

        for reg_field, reg_fieldpos in zip(reg_fields[::-1], reg_fieldposs[::-1]):
            #print(reg_fieldpos.get_text(), reg_field.get_text())
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
            str = '    RK_U32 %20s %5s %d\n' % (reg_field.get_text().ljust(20), ':', bits)
            file.write(str)
        for reg_name in reg_names:
            str = '}%s;\n' % (reg_name.get_text().lower())
            file.write(str)

    file.close()

# print(bs.find_all("a")) # 获取所有的a标签
# print(bs.find(id="u1")) # 获取id="u1"
# p = bs.table
# for item in p.find_next(class_="regname"):
#     print(item.get_text()) # 获取所有的a标签，并遍历打印a标签中的href的值

# p_node = bs.find('p', class_='regname')
# print(p_node.name,p_node['class'],p_node.get_text())

# reg_names = bs.find_all('p', class_='regname')
# for reg_name in reg_names:
#     print(reg_name.get_text())
#
# reg_addrs = bs.find_all('p', class_='regaddrvalue')
# for reg_addr in reg_addrs:
#     print(reg_addr.get_text())
#
# reg_fields = bs.find_all('p', class_='regfield')
# for reg_field in reg_fields:
#     print(reg_field.get_text())
#
# reg_fieldposs = bs.find_all('p', class_='regfieldpos')
# for reg_fieldpos in reg_fieldposs:
#     print(reg_fieldpos.get_text())
