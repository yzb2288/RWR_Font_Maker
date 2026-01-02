import os
import cv2
import copy
import numpy as np
from fnt_reader import FntReader
from ogre_fontdef_reader import OgreFontdefReader

class FntCharAdjust(FntReader):
    def __init__(self, fnt_path_list, fontdef_path, font_type="outline"):
        super().__init__(fnt_path_list)
        self.fontdef_reader = OgreFontdefReader(fontdef_path)
        self.output_fnt_path = "{}_adjusted.fnt".format(os.path.splitext(self.fnt_path_list[0])[0])
        if font_type.lower() == "basic":
            self.fill_value = [255, 255, 255, 0]
            self.alpha_threshold = 0
        elif font_type.lower() == "outline":
            self.fill_value = [0, 0, 0, 0]
            self.alpha_threshold = 1
        else:
            raise Exception("unknown font type!")
        self.char_adjust()
        self.save_fnt(self.output_fnt_path)
    
    def char_adjust(self):
        expended_char_img_info_dict = {}
        for char in self.fontdef_reader.char_glyph_dict.keys():
            unicode = ord(char)
            expended_char_img_info = self.fontdef_reader.get_expended_char_img_info(char, self.alpha_threshold)
            expended_char_img_info_dict[unicode] = expended_char_img_info
        
        new_fnt_page_img_dict = {
            0: np.full(self.fnt_page_img_dict[0].shape, self.fill_value, np.uint8)
        }
        new_fnt_id_sorted_char_dict = copy.deepcopy(self.fnt_id_sorted_char_dict)
        new_page = 0
        spacing_x, spacing_y = (int(spacing) for spacing in self.fnt_root_list[0].find("info").attrib.get("spacing").split(","))
        cursor_x, cursor_y = 0, 0
        for unicode in new_fnt_id_sorted_char_dict.keys():
            x = int(new_fnt_id_sorted_char_dict[unicode].attrib.get("x"))
            y = int(new_fnt_id_sorted_char_dict[unicode].attrib.get("y"))
            width = int(new_fnt_id_sorted_char_dict[unicode].attrib.get("width"))
            height = int(new_fnt_id_sorted_char_dict[unicode].attrib.get("height"))
            char_page = int(new_fnt_id_sorted_char_dict[unicode].attrib.get("page"))
            char_img = self.fnt_page_img_dict[char_page][y:y+height,x:x+width,:]
            if unicode in expended_char_img_info_dict.keys():
                if chr(unicode) == "A":
                    # 加char_img显示
                    cv2.imshow("char_img_before", char_img)
                    cv2.waitKey(0)
                    cv2.destroyWindow("char_img_before")
                
                expended_ratio = expended_char_img_info_dict[unicode]["char"]["width"] / expended_char_img_info_dict[unicode]["glyph"]["width"]
                x_offset_ratio = (expended_char_img_info_dict[unicode]["glyph"]["x"] - expended_char_img_info_dict[unicode]["char"]["x"]) / expended_char_img_info_dict[unicode]["char"]["width"]
                old_width = char_img.shape[1]
                new_char_img_shape = list(char_img.shape)
                new_char_img_shape[1] = int(new_char_img_shape[1] * expended_ratio)
                new_char_img = np.full(new_char_img_shape, self.fill_value, np.uint8)
                x_offset = int(new_char_img_shape[1] * x_offset_ratio)
                new_char_img[:,x_offset:x_offset+char_img.shape[1],:] = char_img[:,:,:]
                char_img = new_char_img
                print("expend char_img unicode {} char {} expended_ratio {:.3f} x_offset_ratio {:.3f} old_width {} new_width {}".format(
                    unicode,
                    chr(unicode),
                    expended_ratio,
                    x_offset_ratio,
                    old_width,
                    new_char_img_shape[1]
                ))
                if chr(unicode) == "A":
                    # 加char_img显示
                    cv2.imshow("char_img_after", char_img)
                    cv2.waitKey(0)
                    cv2.destroyWindow("char_img_after")
            
            else:
                print("keep original char_img unicode {} char {}".format(unicode, chr(unicode)))
                
            try:
                new_fnt_page_img_dict[new_page][cursor_y:cursor_y+char_img.shape[0], cursor_x:cursor_x+char_img.shape[1], :] = char_img[:,:,:]
            except Exception as e:
                cursor_x = 0
                cursor_y += (char_img.shape[0] + spacing_y)
                if cursor_y >= new_fnt_page_img_dict[new_page].shape[0]:
                    cursor_y = 0
                    new_page += 1
                    new_fnt_page_img_dict[new_page] = np.full(self.fnt_page_img_dict[0].shape, self.fill_value, np.uint8)
                    new_fnt_page_img_dict[new_page][cursor_y:cursor_y+char_img.shape[0], cursor_x:cursor_x+char_img.shape[1], :] = char_img[:,:,:]
            
            new_fnt_id_sorted_char_dict[unicode].attrib.update({
                "x": str(cursor_x),
                "y": str(cursor_y),
                "width": str(char_img.shape[1]),
                "height": str(char_img.shape[0]),
                "page": str(new_page),
            })
            cursor_x += (char_img.shape[1] + spacing_x)
            if cursor_x >= new_fnt_page_img_dict[new_page].shape[1]:
                cursor_x = 0
                cursor_y += (char_img.shape[0] + spacing_y)
                if cursor_y >= new_fnt_page_img_dict[new_page].shape[0]:
                    cursor_y = 0
                    new_page += 1
                    new_fnt_page_img_dict[new_page] = np.full(self.fnt_page_img_dict[0].shape, self.fill_value, np.uint8)
        
        # 加new_fnt_page_img_dict[new_page]显示
        cv2.namedWindow("new_fnt_page_img_dict[new_page]", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("new_fnt_page_img_dict[new_page]", 1920, 1080)
        cv2.imshow("new_fnt_page_img_dict[new_page]", new_fnt_page_img_dict[new_page])
        cv2.waitKey(0)
        cv2.destroyWindow("new_fnt_page_img_dict[new_page]")
        
        for i in range(len(self.fnt_root_list)):
            self.fnt_root_list[i].find("chars").clear()
        for unicode in new_fnt_id_sorted_char_dict.keys():
            self.fnt_root_list[0].find("chars").append(new_fnt_id_sorted_char_dict[unicode])
        self.fnt_id_sorted_char_dict = self.get_all_fnt_id_sorted_char_dict()
        self.fnt_page_line_sorted_char_dict = self.get_all_fnt_page_line_sorted_char_dict()
        self.fnt_page_img_dict = new_fnt_page_img_dict
                
if __name__ == "__main__":
    fca = FntCharAdjust(["SarasaMonoSC-Bold+KOMIKA\\bmfc\\basic_komika.fnt"], "origin\\fonts\\latin1_basic_font_100.fontdef", "basic")
    fca = FntCharAdjust(["SarasaMonoSC-Bold+KOMIKA\\bmfc\\outline_komika.fnt"], "origin\\fonts\\latin1_basic_font_outline_100.fontdef", "outline")
    a = 1