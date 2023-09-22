from bs4 import BeautifulSoup
import re
import sys
import logging

if __name__ == "__main__":
    arg = sys.argv
    logging.getLogger().setLevel(logging.DEBUG)
    file = open(arg[1], 'r', encoding='utf-8')
    html = file.read()
    bs = BeautifulSoup(html,"html.parser") # 缩进格式
    file.close()

    file = open(arg[2],'w', encoding='utf-8')
    fp_tmp = open(arg[3], 'w', encoding='utf-8')
    log_en = False
    # print(bs.table)
    trs = bs.find_all('tr')
    # print(trs[0])
    """
    {"swreg0", [{bit_name, bits}, {bit_name, av1_flag}]}
    """
    reg_dic = {}
    member_list = []
    name_to_bits = {}
    name_av1_flag = {}

    find_swreg = False
    find_av1 = False
    reserve_cnt = 0
    for idx, tr in enumerate(bs.find_all('tr')):
        tds = tr.find_all('td')
        if len(tds) > 0:
            if not find_swreg and "swreg" in tds[0].get_text():
                find_swreg = True
                reg_name = tds[0].get_text()
                name_to_bits = {}
                name_av1_flag = {}
                reserve_cnt = 0
                continue
            if not find_av1 and len(tds) > 14 and "AV1" in tds[14].get_text():
                find_av1 = True
                continue
            # if not find_av1 and find_swreg and "Bit" in tds[0].get_text():
            #     find_av1 = True
            #     continue
            if find_swreg and find_av1:
                bits_str = tds[0].get_text()
                if len(bits_str) == 0 or "" == bits_str:
                    find_swreg = False
                    find_av1 = False
                    name_to_bits = {}
                    name_av1_flag = {}
                    reserve_cnt = 0
                    logging.debug("fount one end")
                    # file.write("fount one end \n")
                    continue
                else:
                    bits = bits_str #.split(":")
                bit_name = tds[1].get_text()
                if bit_name == "" or bit_name == "-" or "-" in bit_name:
                    bit_name = "reserved" + reserve_cnt.__str__()
                    reserve_cnt += 1
                """获取是否是av1 支持的"""
                if len(tds) > 14:
                    av1_flag = "x" in tds[14].get_text()
                else:
                    logging.error("warning can not find av1 flag, name %s bit_name %s" % (reg_name, bit_name))
                    break
                # av1_flag = True
                if av1_flag:
                    bit_name = bit_name + ":1"
                else:
                    bit_name = bit_name + ":0"
                    continue

                if bit_name in name_to_bits:
                    logging.error("err bit name already in list %s" % (bit_name))
                    break
                name_to_bits[bit_name] = bits
                name_av1_flag[bit_name] = av1_flag
                reg_dic[reg_name] = [name_to_bits, name_av1_flag]

    reg_num_pre = -1
    for reg_name, member_list in reg_dic.items():
        name_to_bits = member_list[0]
        name_av1_flag = member_list[1]

        reg_num = int(reg_name[5:], 10)
        if reg_num_pre + 1 != reg_num:
            logging.warning("reserve reg %d -> %d" % (reg_num_pre, reg_num))
            if reg_num - reg_num_pre == 2:
                str = "RK_U32 reserved_%d;\n" %(reg_num_pre + 1)
            else:
                str = "RK_U32 reserved_%d_%d[%d];\n" % (reg_num_pre + 1, reg_num - 1, reg_num- reg_num_pre - 1)
            file.write(str)
        reg_num_pre = reg_num

        str = "struct {\n"
        file.write(str)
        str = "----- %s -----\n" % (reg_name)
        fp_tmp.write(str)


        bit_name_list = []
        bit_list = []
        adjust_len = 0
        for bit_name, bits in name_to_bits.items():
            bit_name_list.append(bit_name)
            bit_list.append(bits)
            if len(bit_name) > adjust_len:
                adjust_len = len(bit_name)

        reserve_cnt = 0
        bit_s_pre = 0
        bit_e_pre = 0
        bit_e = 0
        bit_s = 0
        total_bits = 0
        for bit_name, bits_str in zip(bit_name_list[::-1], bit_list[::-1]):
            name, valid = bit_name.split(":")[0], bit_name.split(":")[1]
            if "reserved" in name or int(valid, 10) == 0:
                name = "reserved" + reserve_cnt.__str__()
                reserve_cnt += 1
            bits = bits_str.split(":")
            name = name.lower()

            if len(bits) == 2:
                bit_s = int(bits[1], 10)
                bit_e = int(bits[0], 10)
                # str = "%s : %d \n" % (name.ljust(20), bit_e - bit_s + 1)
                bits_int = bit_e - bit_s + 1
            else:
                bit_s = bit_e = int(bits[0], 10)
                bits_int = 1
                # str = "%s : %d \n" % (name.ljust(20), 1)
            if bit_e_pre == 0 and bit_s_pre == 0:
                if bit_e_pre != bit_s:
                    name_reserve = "reserved" + reserve_cnt.__str__()
                    str = "    RK_U32 %s : %d;\n" % (name_reserve.ljust(adjust_len), bit_s - bit_e_pre)
                    file.write(str)
                    reserve_cnt += 1
                    total_bits += bit_s - bit_e_pre
            elif bit_e_pre + 1 != bit_s:
                # bits_int = bit_s - bit_e_pre
                name_reserve = "reserved" + reserve_cnt.__str__()
                str = "    RK_U32 %s : %d;\n" % (name_reserve.ljust(adjust_len), bit_s - bit_e_pre - 1)
                file.write(str)
                reserve_cnt += 1
                total_bits += bit_s - bit_e_pre - 1
                # str = "%s : %d \n" % (name.ljust(20), 1)
            str = "    RK_U32 %s : %d;\n" % (name.ljust(adjust_len), bits_int)
            file.write(str)
            str1 = "%s : %s;\n" % (name.ljust(adjust_len), bits_str)
            fp_tmp.write(str1)
            total_bits += bits_int

            bit_s_pre = bit_s
            bit_e_pre = bit_e
            if bit_s == bit_e == 0:
                bit_s_pre = 1
        if total_bits != 32:
            if total_bits < 32:
                name_reserve = "reserved" + reserve_cnt.__str__()
                str = "    RK_U32 %s : %d;\n" % (name_reserve.ljust(adjust_len), 32 - total_bits)
                file.write(str)
            else:
                logging.warning("bits over 32 %s %d" % (reg_name, total_bits))
        str = "} %s;\n\n" %(reg_name)
        file.write(str)

        # if len(tds) > 20 or len(tds) >= 9:
        #     if len(tds) > 20:
        #         str = 'idex %d len %d str: %s str1: %s av1: %s\n' % (idx, len(tds), tds[0].get_text(), tds[1].get_text(), tds[14].get_text())
        #     else:
        #         # if "swreg" in tds[0].get_text():
        #         str = 'idx %d len %d str: %s str1: %s\n' % (idx, len(tds), tds[0].get_text(), tds[1].get_text())
        #     if tds[0].get_text():
        #         file.write(str)
    # for tr in trs:
    #     # data = tr.find('td', class_="xl98")
    #     # reg_addrs = tr.find_all('p', class_='regaddrvalue')
    #     data = tr.find_all('td')
    #     if data:
    #         print(data.contents[0])
    # for table in tables:
    #     reg_names = table.find_all('p', class_="regname")
    #     reg_addrs = table.find_all('p', class_='regaddrvalue')
    #
    #     for reg_name, reg_addr in zip(reg_names, reg_addrs):
    #         if log_en:
    #             print(reg_name.get_text(), reg_addr.get_text())
    #         # str ='%10s %10s %10s \n' % ('ID','Name','Record')
    #         str ='\n/* %s */\n' % (reg_addr.get_text())
    #         file.write(str)
    #         str = 'struct %s {\n' % (reg_name.get_text())
    #         file.write(str)
    #
    #     reg_fields = table.find_all('p', class_="regfield")
    #     reg_fieldposs = table.find_all('p', class_='regfieldpos')
    #
    #     for reg_field, reg_fieldpos in zip(reg_fields[::-1], reg_fieldposs[::-1]):
    #         #print(reg_fieldpos.get_text(), reg_field.get_text())
    #         pos_text = reg_fieldpos.get_text()
    #         pos = pos_text.split(":")
    #         if len(pos) == 2:
    #             bits = int(pos[0]) - int(pos[1]) + 1
    #             if log_en:
    #                 print(pos_text, bits, reg_field.get_text())
    #         else:
    #             bits = 1
    #             if log_en:
    #                 print(pos_text, bits, reg_field.get_text())
    #         str = '    RK_U32 %20s %5s %d\n' % (reg_field.get_text().ljust(20), ':', bits)
    #         file.write(str)
    #     for reg_name in reg_names:
    #         str = '}%s;\n' % (reg_name.get_text().lower())
    #         file.write(str)

    file.close()
    fp_tmp.close()
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
