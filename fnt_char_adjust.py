import os
import cv2
import copy
import numpy as np
from fnt_reader import FntReader
from ogre_fontdef_reader import OgreFontdefReader

class FntCharAdjust(FntReader):
    def __init__(self, fnt_path_list, font_type="outline"):
        super().__init__(fnt_path_list)
        self.output_fnt_path = "{}_adjusted.fnt".format(os.path.splitext(self.fnt_path_list[0])[0])
        self.font_type = font_type
        if font_type.lower() == "basic":
            self.fill_value = [255, 255, 255, 0]
            self.alpha_threshold = 0
        elif font_type.lower() == "outline":
            self.fill_value = [0, 0, 0, 0]
            self.alpha_threshold = 1
        else:
            raise Exception("unknown font type!")
    
    def char_adjust(self, char_unicode_list:list, padding_adjust=[-1, 0, -1, 0], keep_not_zreo=False):
        new_fnt_page_img_dict = {
            0: np.full(self.fnt_page_img_dict[0].shape, self.fill_value, np.uint8)
        }
        new_fnt_id_sorted_char_dict = copy.deepcopy(self.fnt_id_sorted_char_dict)
        new_page = 0
        spacing_x, spacing_y = (int(spacing) for spacing in self.fnt_root_list[0].find("info").attrib.get("spacing").split(","))
        cursor_x, cursor_y = 0, 0
        line_height = 0
        padding_adjust_origin = copy.deepcopy(padding_adjust)
        for unicode in new_fnt_id_sorted_char_dict.keys():
            x = int(new_fnt_id_sorted_char_dict[unicode].attrib.get("x"))
            y = int(new_fnt_id_sorted_char_dict[unicode].attrib.get("y"))
            width = int(new_fnt_id_sorted_char_dict[unicode].attrib.get("width"))
            height = int(new_fnt_id_sorted_char_dict[unicode].attrib.get("height"))
            char_page = int(new_fnt_id_sorted_char_dict[unicode].attrib.get("page"))
            char_img = self.fnt_page_img_dict[char_page][y:y+height,x:x+width,:]
            if unicode in char_unicode_list:
                char_unicode_list.remove(unicode)
                if chr(unicode) == "I":
                    # 加char_img显示
                    cv2.namedWindow("char_img_before", cv2.WINDOW_NORMAL)
                    #cv2.resizeWindow("char_img_before", 100, 200)
                    cv2.imshow("char_img_before", char_img)
                    cv2.waitKey(0)
                    cv2.destroyWindow("char_img_before")
                padding_adjust = copy.deepcopy(padding_adjust_origin)
                print(f"调整字符: {chr(unicode)}, u{unicode}, width: {width}, height: {height}")
                if keep_not_zreo:
                    none_empty_x_min = none_empty_x_max = none_empty_y_min = none_empty_y_max = 0
                    for i in range(width):
                        if np.sum(char_img[:,i,3]) > 0:
                            none_empty_x_min = i
                            break
                    for i in range(width):
                        if np.sum(char_img[:,width-1-i,3]) > 0:
                            none_empty_x_max = width-i
                            break
                    for i in range(height):
                        if np.sum(char_img[i,:,3]) > 0:
                            none_empty_y_min = i
                            break
                    for i in range(height):
                        if np.sum(char_img[height-1-i,:,3]) > 0:
                            none_empty_y_max = height-i
                            break
                    if padding_adjust[0] < -none_empty_x_min:
                        print(f"左侧宽度缩减超出非空边界, 设置为: {-none_empty_x_min}")
                        padding_adjust[0] = -none_empty_x_min
                    if padding_adjust[1] < -none_empty_y_min:
                        print(f"上侧高度缩减超出非空边界, 设置为: {-none_empty_y_min}")
                        padding_adjust[1] = -none_empty_y_min
                    if padding_adjust[2] < none_empty_x_max - width:
                        print(f"右侧宽度缩减超出非空边界, 设置为: {none_empty_x_max - width}")
                        padding_adjust[2] = none_empty_x_max - width
                    if padding_adjust[3] < none_empty_y_max - height:
                        print(f"下侧高度缩减超出非空边界, 设置为: {none_empty_y_max - height}")
                        padding_adjust[3] = none_empty_y_max - height
                
                new_char_img_shape = list(char_img.shape)
                if padding_adjust[0] <= -new_char_img_shape[1] or padding_adjust[2] <= -new_char_img_shape[1] or (padding_adjust[0] + padding_adjust[2]) <= -new_char_img_shape[1]:
                    raise Exception("宽度调整参数错误")
                if padding_adjust[1] <= -new_char_img_shape[0] or padding_adjust[3] <= -new_char_img_shape[0] or (padding_adjust[1] + padding_adjust[3]) <= -new_char_img_shape[0]:
                    raise Exception("高度调整参数错误")
                new_char_img_shape[0] = new_char_img_shape[0] + padding_adjust[1] + padding_adjust[3]
                new_char_img_shape[1] = new_char_img_shape[1] + padding_adjust[0] + padding_adjust[2]
                new_char_img = np.full(new_char_img_shape, self.fill_value, np.uint8)
                src_rect_x_min = dst_rect_x_min = 0
                src_rect_y_min = dst_rect_y_min = 0
                src_rect_x_max = dst_rect_x_max = width
                src_rect_y_max = dst_rect_y_max = height
                
                if padding_adjust[0] < 0:
                    src_rect_x_min -= padding_adjust[0]
                    if (np.sum(char_img[:,0:src_rect_x_min,3]) > 0):
                        print(f"警告: {chr(unicode)}左侧宽度缩减存在非0像素")
                else:
                    dst_rect_x_min += padding_adjust[0]
                if padding_adjust[2] < 0:
                    src_rect_x_max += padding_adjust[2]
                    if (np.sum(char_img[:,src_rect_x_max:width,3]) > 0):
                        print(f"警告: {chr(unicode)}右侧宽度缩减存在非0像素")
                dst_rect_x_max = dst_rect_x_min + src_rect_x_max - src_rect_x_min
                if padding_adjust[1] < 0:
                    src_rect_y_min -= padding_adjust[1]
                    if (np.sum(char_img[0:src_rect_y_min,:,3]) > 0):
                        print(f"警告: {chr(unicode)}上侧高度缩减存在非0像素")
                else:
                    dst_rect_y_min += padding_adjust[1]
                if padding_adjust[3] < 0:
                    src_rect_y_max += padding_adjust[3]
                    if (np.sum(char_img[src_rect_y_max:height,:,3]) > 0):
                        print(f"警告: {chr(unicode)}下侧高度缩减存在非0像素")
                dst_rect_y_max = dst_rect_y_min + src_rect_y_max - src_rect_y_min
                
                new_char_img[dst_rect_y_min:dst_rect_y_max, dst_rect_x_min:dst_rect_x_max, :] = char_img[src_rect_y_min:src_rect_y_max, src_rect_x_min:src_rect_x_max, :]
                char_img = new_char_img
                
                if chr(unicode) == "I":
                    # 加char_img显示
                    cv2.namedWindow("char_img_after", cv2.WINDOW_NORMAL)
                    #cv2.resizeWindow("char_img_after", 100, 200)
                    cv2.imshow("char_img_after", char_img)
                    cv2.waitKey(0)
                    cv2.destroyWindow("char_img_after")
                
            if char_img.shape[0] > line_height:
                line_height = char_img.shape[0]
            
            try:
                new_fnt_page_img_dict[new_page][cursor_y:cursor_y+char_img.shape[0], cursor_x:cursor_x+char_img.shape[1], :] = char_img[:,:,:]
            except Exception as e:
                cursor_x = 0
                cursor_y += (line_height + spacing_y)
                try:
                    new_fnt_page_img_dict[new_page][cursor_y:cursor_y+char_img.shape[0], cursor_x:cursor_x+char_img.shape[1], :] = char_img[:,:,:]
                except Exception as e:
                    print("write in new page {}".format(new_page + 1))
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
                cursor_y += (line_height + spacing_y)
                if cursor_y >= new_fnt_page_img_dict[new_page].shape[0]:
                    cursor_y = 0
                    new_page += 1
                    new_fnt_page_img_dict[new_page] = np.full(self.fnt_page_img_dict[0].shape, self.fill_value, np.uint8)
        
        if len(char_unicode_list) != 0:
            print("注意: 以下字符不在字体中: {}".format(" ".join([chr(unicode) for unicode in char_unicode_list])))
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
    
    def char_adjust_to_expended_fontdef(self, fontdef_path):
        fontdef_reader = OgreFontdefReader(fontdef_path)
        expended_char_img_info_dict = {}
        for char in fontdef_reader.char_glyph_dict.keys():
            unicode = ord(char)
            expended_char_img_info = fontdef_reader.get_expended_char_img_info(char, self.alpha_threshold)
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
                try:
                    new_fnt_page_img_dict[new_page][cursor_y:cursor_y+char_img.shape[0], cursor_x:cursor_x+char_img.shape[1], :] = char_img[:,:,:]
                except Exception as e:
                    print("write in new page {}".format(new_page + 1))
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
    
    def save(self):
        self.save_fnt(self.output_fnt_path)
                
if __name__ == "__main__":
    fca = FntCharAdjust(["SarasaUiSC-Bold_mod\\bmfc\\basic_offset0.fnt"], "basic")
    fca.char_adjust(
        char_unicode_list=[
            73, 105, 106, 108, 204, 205, 206, 207,
            236, 237, 238, 239, 296, 297, 298, 299,
            305, 322, 463, 464, 921, 953,
            1030, 1031, 1110, 1111, 1112],
        padding_adjust=[0, 0, -1, 0],
        keep_not_zreo=True
    )
    fca.save()
    fca = FntCharAdjust(["SarasaUiSC-Bold_mod\\bmfc\\outline_offset0.fnt"], "outline")
    fca.char_adjust(
        char_unicode_list=[
            73, 105, 106, 108, 204, 205, 206, 207,
            236, 237, 238, 239, 296, 297, 298, 299,
            305, 322, 463, 464, 921, 953,
            1030, 1031, 1110, 1111, 1112],
        padding_adjust=[0, 0, -1, 0],
        keep_not_zreo=True
    )
    fca.save()
    fca = FntCharAdjust(["SarasaUiSC-Bold+KOMIKA\\bmfc\\outline_offset0.fnt"], "outline")
    fca.char_adjust_to_expended_fontdef("origin\\fonts\\latin1_basic_font_outline_100.fontdef")
    fca.save()
    fca = FntCharAdjust(["SarasaUiSC-Bold+KOMIKA\\bmfc\\basic_offset0.fnt"], "basic")
    fca.char_adjust_to_expended_fontdef("origin\\fonts\\latin1_basic_font_100.fontdef")
    fca.save()
    a = 1