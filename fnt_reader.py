import os
import cv2
import copy
import numpy as np
import xml.etree.ElementTree as ET

class FntReader:
    def __init__(self, fnt_path_list:list):
        self.fnt_path_list = fnt_path_list
        self.fnt_tree_list = [ET.parse(fnt_path) for fnt_path in self.fnt_path_list]
        self.fnt_root_list = [tree.getroot() for tree in self.fnt_tree_list]
        self.fnt_page_img_path_dict = self.get_all_fnt_page_img_file_dict()
        self.fnt_id_sorted_char_dict = self.get_all_fnt_id_sorted_char_dict()
        self.fnt_page_line_sorted_char_dict = self.get_all_fnt_page_line_sorted_char_dict()
        self.fnt_page_img_dict = self.get_all_fnt_page_img_dict()
        
    def get_all_fnt_page_img_file_dict(self):
        fnt_page_img_path_dict = {}
        for i in range(len(self.fnt_root_list)):
            folder_path = os.path.split(self.fnt_path_list[i])[0]
            if i == 0:
                for fnt_page in self.fnt_root_list[i].find("pages").findall("page"):
                    fnt_page_img_path_dict[int(fnt_page.attrib.get("id"))] = os.path.join(folder_path, fnt_page.attrib.get("file"))
            else:
                for fnt_page in self.fnt_root_list[i].find("pages").findall("page"):
                    new_page_id = max(fnt_page_img_path_dict.keys()) + 1
                    fnt_page_img_path_dict[new_page_id] = os.path.join(folder_path, fnt_page.attrib.get("file"))
        return fnt_page_img_path_dict
    
    def get_all_fnt_id_sorted_char_dict(self):
        all_char_list = []
        page_num = 0
        for i in range(len(self.fnt_root_list)):
            chars = self.fnt_root_list[i].find("chars").findall("char")
            if i != 0:
                for char in chars:
                    char.attrib.update({"page": str(page_num + int(char.attrib.get("page")))})
            page_num += len(self.fnt_root_list[i].find("pages").findall("page"))
            all_char_list.extend(chars)
        return self.get_id_sorted_char(all_char_list)
    
    def get_all_fnt_page_line_sorted_char_dict(self):
        fnt_page_line_sorted_char_dict = {}
        for i in range(len(self.fnt_root_list)):
            if i == 0:
                sorted_page_char = self.get_page_line_sorted_char(self.fnt_root_list[i].find("chars").findall("char"))
                fnt_page_line_sorted_char_dict.update(sorted_page_char)
            else:
                sorted_page_char = self.get_page_line_sorted_char(self.fnt_root_list[i].find("chars").findall("char"))
                for page in sorted_page_char.keys():
                    new_page_id = max(fnt_page_line_sorted_char_dict.keys()) + 1
                    fnt_page_line_sorted_char_dict[new_page_id] = sorted_page_char[page]
        return fnt_page_line_sorted_char_dict
    
    def get_all_fnt_page_img_dict(self):
        fnt_page_img_dict = {}
        for page in self.fnt_page_img_path_dict.keys():
            fnt_page_img_dict[page] = cv2.imdecode(np.fromfile(file=self.fnt_page_img_path_dict[page], dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        return fnt_page_img_dict
    
    def get_id_sorted_char(self, chars):
        char_dict = {}
        for ch in chars:
            try:
                id = int(ch.attrib.get("id", 0))
            except (ValueError, TypeError):
                continue
            if id not in char_dict.keys():
                char_dict[id] = ch
            else:
                raise Exception("duplicate id!")
        sorted_dict = {id: char_dict[id] for id in sorted(char_dict.keys())}
        return sorted_dict

    def get_page_line_sorted_char(self, chars):
        pages = {}
        for ch in chars:
            try:
                page = int(ch.attrib.get("page", 0))
                x = int(ch.attrib.get("x", 0))
                y = int(ch.attrib.get("y", 0))
            except (ValueError, TypeError):
                continue
            pages.setdefault(page, {}).setdefault(y, []).append((x, ch))

        #sorted_pages = []
        sorted_pages = {}
        for page_key in sorted(pages.keys()):
            #sorted_pages.append([])
            sorted_pages[page_key] = []
            for y_key in sorted(pages[page_key].keys()):
                lst = pages[page_key][y_key]
                lst.sort(key=lambda t: t[0])  # 按 x 排序
                #sorted_pages[-1].append([elem for _, elem in lst])
                sorted_pages[page_key].append([elem for _, elem in lst])
        return sorted_pages
    
    def save_fnt(self, output_fnt_path):
        head, tail = os.path.split(output_fnt_path)
        root, ext = os.path.splitext(tail)
        if ext != ".fnt":
            raise Exception("not a .fnt ext file path!")
        if not os.path.exists(head):
            os.makedirs(head)
        
        save_fnt_root = copy.deepcopy(self.fnt_root_list[0])
        save_fnt_tree = ET.ElementTree(save_fnt_root)
        fnt_id_sorted_char_dict_copy = copy.deepcopy(self.fnt_id_sorted_char_dict)
        chars = save_fnt_root.find("chars")
        chars.clear()
        chars.attrib.update({"count": str(len(fnt_id_sorted_char_dict_copy.keys()))})
        page = None
        save_page_list = []
        for id in fnt_id_sorted_char_dict_copy.keys():
            chars.append(fnt_id_sorted_char_dict_copy[id])
            char_page = int(fnt_id_sorted_char_dict_copy[id].attrib.get("page"))
            if page != char_page:
                page = char_page
                save_page_list.append(page)
        
        pages = save_fnt_root.find("pages")
        pages.clear()
        for page in save_page_list:
            pages.append(ET.Element("page", {"id": str(page), "file": "{}_{}.png".format(root, page)}))
        
        save_fnt_tree.write(output_fnt_path, encoding="utf-8", xml_declaration=True)
        for page in save_page_list:
            print("saving " + "{}_{}.png".format(root, page))
            cv2.imencode(ext=".png", img=self.fnt_page_img_dict[page], params=[cv2.IMWRITE_PNG_COMPRESSION, 1])[1].tofile(os.path.join(head, "{}_{}.png".format(root, page)))
