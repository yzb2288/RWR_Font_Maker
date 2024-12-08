import os
import cv2
import shutil
import numpy as np
import xml.etree.ElementTree as ET

class OgreFontdefGenerator(object):
    def __init__(self, fnt_file_path:str, output_font_name, output_font_file_name, font_png_file_name, font_image_scale:float=1):
        self.fnt_file_path = fnt_file_path
        self.output_font_name = output_font_name
        self.output_font_file_name, self.output_font_file_suffix = os.path.splitext(os.path.basename(output_font_file_name))
        self.font_png_file_name, self.font_png_file_suffix = os.path.splitext(os.path.basename(font_png_file_name))
        self.font_image_scale = font_image_scale
        self.fnt_tree = ET.parse(fnt_file_path)
        self.fnt_root = self.fnt_tree.getroot()

        self.fnt_info = self.fnt_root.find("info")
        self.fnt_common = self.fnt_root.find("common")
        self.fnt_pages = self.fnt_root.find("pages")
        self.fnt_chars = self.fnt_root.find("chars")
        
        self.fnt_page_list = self.fnt_pages.findall("page")
        if len(self.fnt_page_list) != 1:
            raise Exception("字体位图必须为单个文件, 暂不支持多个图片文件, 请自行调整生成位图时的尺寸!") # 当前100分辨率字体最大尺寸介于8000-9000的正方形, 50和25的更低一些
        self.fnt_image_file_name = self.fnt_page_list[0].attrib.get("file")
        self.fnt_image_file_path = os.path.join(os.path.dirname(os.path.abspath(self.fnt_file_path)), self.fnt_image_file_name)
        self.fnt_image_file_suffix = os.path.splitext(self.fnt_image_file_path)[1]
        if self.fnt_image_file_suffix != ".png":
            raise Exception("图片材质必须为png格式, 其余格式兼容性不佳!")
        
        self.fnt_image = None
        #self.fnt_image = cv2.imdecode(np.fromfile(file=self.fnt_image_file_path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
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
        self.ogre_fontdef_file.writelines(["{}\n".format(self.output_font_name), "{\n", "\ttype image\n", "\tsource {}{}\n".format(self.font_png_file_name, self.fnt_image_file_suffix)])
    
    def parse_char(self):
        #rwr_width_offset = int(0.00655 * self.fnt_image_width) # rwr逆天算法, 字符渲染宽度会随着材质尺寸发生变化, 此为逆向消除偏移量, 仅字符材质间隔为1px的时候适用
        rwr_width_offset = 0
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
                #cv2.imencode(ext=self.fnt_image_file_suffix, img=char_image)[1].tofile("./{}_t.png".format(id))
        self.ogre_fontdef_file.write("}")
        self.ogre_fontdef_file.close()
    
    def copy_png_image(self):
        if self.font_image_scale == 1:
            shutil.copyfile(src=self.fnt_image_file_path, dst="{}{}".format(self.font_png_file_name, self.fnt_image_file_suffix))
        else:
            if self.fnt_image == None:
                self.fnt_image = cv2.imdecode(np.fromfile(file=self.fnt_image_file_path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
            self.fnt_image_scaled = cv2.resize(src=self.fnt_image, dsize=(int(self.fnt_image_width * self.font_image_scale), int(self.fnt_image_height * self.font_image_scale)), interpolation=cv2.INTER_CUBIC)
            cv2.imencode(ext=self.fnt_image_file_suffix, img=self.fnt_image_scaled)[1].tofile("{}{}".format(self.font_png_file_name, self.fnt_image_file_suffix))
        
if __name__ == "__main__":
    # 字体位图生成器
    # https://angelcode.com/products/bmfont/
    basic = "微软雅黑_7000常用汉字_RWR已有翻译字体_补充部分外文_34px_0outline_36xspace_0offset_5000x5000.fnt"
    basic_outline = "微软雅黑_7000常用汉字_RWR已有翻译字体_补充部分外文_34px_3outline_36xspace_0offset_5000x5000.fnt"
    input_outline = "微软雅黑_7000常用汉字_RWR已有翻译字体_补充部分外文_34px_3outline_36xspace_0offset_5000x5000.fnt"
    
    rfg = OgreFontdefGenerator(
        fnt_file_path=basic,
        output_font_name="ChineseBasicFont100",
        output_font_file_name="chinese_basic_font_100",
        font_png_file_name="chinese_basic_font_100"
    )
    rfg = OgreFontdefGenerator(
        fnt_file_path=basic,
        output_font_name="ChineseBasicFont050",
        output_font_file_name="chinese_basic_font_050",
        font_png_file_name="chinese_basic_font_050",
        font_image_scale=2048/3200
    ) # font_image_scale缩放参数参考了原有字库文件的尺寸比例, 可以自行调整到合适的清晰度和大小, 过大可能导致游戏无法启动(050和025的字体允许大材质大小要比100低得多)
    rfg = OgreFontdefGenerator(
        fnt_file_path=basic,
        output_font_name="ChineseBasicFont025",
        output_font_file_name="chinese_basic_font_025",
        font_png_file_name="chinese_basic_font_025",
        font_image_scale=1536/3200
    )
    
    rfg = OgreFontdefGenerator(
        fnt_file_path=basic_outline,
        output_font_name="ChineseBasicFontOutline100",
        output_font_file_name="chinese_basic_font_outline_100",
        font_png_file_name="chinese_basic_font_outline_100"
    )
    rfg = OgreFontdefGenerator(
        fnt_file_path=basic_outline,
        output_font_name="ChineseBasicFontOutline050",
        output_font_file_name="chinese_basic_font_outline_050",
        font_png_file_name="chinese_basic_font_outline_050",
        font_image_scale=2048/3200
    )
    rfg = OgreFontdefGenerator(
        fnt_file_path=basic_outline,
        output_font_name="ChineseBasicFontOutline025",
        output_font_file_name="chinese_basic_font_outline_025",
        font_png_file_name="chinese_basic_font_outline_025",
        font_image_scale=1536/3200
    )

    rfg = OgreFontdefGenerator(
        fnt_file_path=input_outline,
        output_font_name="ChineseInputFontOutline100",
        output_font_file_name="chinese_input_font_outline_100",
        font_png_file_name="chinese_basic_font_outline_100"
    )
    rfg = OgreFontdefGenerator(
        fnt_file_path=input_outline,
        output_font_name="ChineseInputFontOutline050",
        output_font_file_name="chinese_input_font_outline_050",
        font_png_file_name="chinese_basic_font_outline_050",
        font_image_scale=2048/3200
    )
    rfg = OgreFontdefGenerator(
        fnt_file_path=input_outline,
        output_font_name="ChineseInputFontOutline025",
        output_font_file_name="chinese_input_font_outline_025",
        font_png_file_name="chinese_basic_font_outline_025",
        font_image_scale=1536/3200
    )