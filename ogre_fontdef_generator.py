import os
import cv2
import shutil
import xml.etree.ElementTree as ET

class OgreFontdefGenerator(object):
    def __init__(self, fnt_file_path:str, output_font_name, output_font_file_name, font_png_file_name, font_image_scale:float=1):
        self.fnt_file_path = fnt_file_path
        self.output_font_name = output_font_name
        self.output_font_file_name, self.output_font_file_name_suffix = os.path.splitext(os.path.basename(output_font_file_name))
        self.font_png_file_name, self.font_png_file_name_suffix = os.path.splitext(os.path.basename(font_png_file_name))
        self.font_image_scale = font_image_scale
        self.fnt_tree = ET.parse(fnt_file_path)
        self.fnt_root = self.fnt_tree.getroot()

        self.fnt_info = self.fnt_root.find("info")
        self.fnt_common = self.fnt_root.find("common")
        self.fnt_pages = self.fnt_root.find("pages")
        self.fnt_chars = self.fnt_root.find("chars")
        
        self.fnt_page_list = self.fnt_pages.findall("page")
        if len(self.fnt_page_list) != 1:
            raise Exception("字体位图必须为单个文件, 暂不支持多个图片文件, 请自行调整生成位图时的尺寸!") # 当前100分辨率字体最大尺寸介于8000-9000的正方形, 50和25的在1900-2000
        self.fnt_image_file_name = self.fnt_page_list[0].attrib.get("file")
        self.fnt_image_file_path = os.path.join(os.path.dirname(os.path.abspath(self.fnt_file_path)), self.fnt_image_file_name)
        
        self.fnt_image = None
        #self.fnt_image = cv2.imread(filename=self.fnt_image_file_path, flags=cv2.IMREAD_UNCHANGED)
        #self.fnt_image_width = self.fnt_image.shape[1]
        #self.fnt_image_height = self.fnt_image.shape[0]
        
        self.fnt_image_width = int(self.fnt_common.attrib.get("scaleW"))
        self.fnt_image_height = int(self.fnt_common.attrib.get("scaleH"))
        #if self.fnt_image_width != self.fnt_image_height:
            #raise Exception("字体位图必须长宽必须相同!")
        self.creat_ogre_fontdef_file()
        self.parse_char()
        self.copy_png_image()
        
    
    def creat_ogre_fontdef_file(self):
        self.ogre_fontdef_file = open(file="{}.fontdef".format(self.output_font_file_name), mode="w", encoding="utf-8")
        self.ogre_fontdef_file.writelines(["{}\n".format(self.output_font_name), "{\n", "\ttype image\n", "\tsource {}.png\n".format(self.font_png_file_name)])
    
    def parse_char(self):
        rwr_width_offset = int(0.00655 * self.fnt_image_width) # rwr逆天算法, 字符渲染宽度会随着材质尺寸发生变化, 此为逆向消除偏移量, 仅字符材质间隔为1px的时候适用
        for char in self.fnt_chars:
            id = int(char.attrib.get("id"))
            x = int(char.attrib.get("x"))
            y = int(char.attrib.get("y"))
            width = int(char.attrib.get("width"))
            height = int(char.attrib.get("height"))
            xoffset = int(char.attrib.get("xoffset"))
            yoffset = int(char.attrib.get("yoffset"))
            xadvance = int(char.attrib.get("xadvance"))
            u1 = (x + rwr_width_offset) / self.fnt_image_width
            v1 = y / self.fnt_image_height
            u2 = (x + width - rwr_width_offset) / self.fnt_image_width
            v2 = (y + height) / self.fnt_image_height
            self.ogre_fontdef_file.write("\tglyph u{} {} {} {} {}\n".format(id, u1, v1, u2, v2))
            #if id == 82:
                #if self.fnt_image == None:
                    #self.fnt_image = cv2.imread(filename=self.fnt_image_file_path, flags=cv2.IMREAD_UNCHANGED)
                #char_image = self.fnt_image[y:(y+height), x:(x+width)]
                #cv2.imwrite(filename="./{}_t.png".format(id), img=char_image)
        self.ogre_fontdef_file.write("}")
        self.ogre_fontdef_file.close()
    
    def copy_png_image(self):
        if self.font_image_scale == 1:
            shutil.copyfile(src=self.fnt_image_file_path, dst="{}.png".format(self.font_png_file_name))
        else:
            if self.fnt_image == None:
                self.fnt_image = cv2.imread(filename=self.fnt_image_file_path, flags=cv2.IMREAD_UNCHANGED)
            self.fnt_image_scaled = cv2.resize(src=self.fnt_image, dsize=(int(self.fnt_image_width * self.font_image_scale), int(self.fnt_image_height * self.font_image_scale)), interpolation=cv2.INTER_CUBIC)
            cv2.imwrite(filename="{}.png".format(self.font_png_file_name), img=self.fnt_image_scaled)
        
if __name__ == "__main__":
    # 位图生成器
    # https://angelcode.com/products/bmfont/
    rfg = OgreFontdefGenerator("42.fnt", "ChineseBasicFont100", "chinese_basic_font_100", "chinese_basic_font_100")
    rfg = OgreFontdefGenerator("42.fnt", "ChineseBasicFont050", "chinese_basic_font_050", "chinese_basic_font_050", 1900/3072) # 2048/3072
    rfg = OgreFontdefGenerator("42.fnt", "ChineseBasicFont025", "chinese_basic_font_025", "chinese_basic_font_025", 1536/3072) # 1536/3072
    
    rfg = OgreFontdefGenerator("36_55.fnt", "ChineseBasicFontOutline100", "chinese_basic_font_outline_100", "chinese_basic_font_outline_100")
    rfg = OgreFontdefGenerator("36_55.fnt", "ChineseBasicFontOutline050", "chinese_basic_font_outline_050", "chinese_basic_font_outline_050", 1900/3200) # 2048/3200
    rfg = OgreFontdefGenerator("36_55.fnt", "ChineseBasicFontOutline025", "chinese_basic_font_outline_025", "chinese_basic_font_outline_025", 1536/3200) # 1536/3200
    
    rfg = OgreFontdefGenerator("36_55.fnt", "ChineseInputFontOutline100", "chinese_input_font_outline_100", "chinese_basic_font_outline_100")
    rfg = OgreFontdefGenerator("36_55.fnt", "ChineseInputFontOutline050", "chinese_input_font_outline_050", "chinese_basic_font_outline_050", 1900/3200) # 2048/3200
    rfg = OgreFontdefGenerator("36_55.fnt", "ChineseInputFontOutline025", "chinese_input_font_outline_025", "chinese_basic_font_outline_025", 1536/3200) # 1536/3200