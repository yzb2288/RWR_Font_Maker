import os
import cv2
import numpy as np

class OgreFontdefReader(object):
    def __init__(self, fontdef_file_path):
        self.fontdef_file_path = os.path.abspath(fontdef_file_path)
        self.char_glyph_dict = {}
        with open(self.fontdef_file_path, "r", encoding="utf-8") as self.fontdef_file:
            self.read_fontdef_file()
        self.read_source_png_file()
    
    def read_fontdef_file(self):
        while True:
            fontdef_line_str = self.fontdef_file.readline()
            if fontdef_line_str:
                fontdef_line_str_split = fontdef_line_str.strip().split()
                if len(fontdef_line_str_split) > 0:
                    if fontdef_line_str_split[0] == "source":
                        self.source_png_file_name = fontdef_line_str_split[1]
                        self.source_png_file_path = os.path.join(os.path.dirname(self.fontdef_file_path), self.source_png_file_name)
                    elif fontdef_line_str_split[0] == "glyph":
                        char_unicode = int(fontdef_line_str_split[1].replace("u", ""))
                        char = chr(char_unicode)
                        u1 = float(fontdef_line_str_split[2])
                        v1 = float(fontdef_line_str_split[3])
                        u2 = float(fontdef_line_str_split[4])
                        v2 = float(fontdef_line_str_split[5])
                        self.char_glyph_dict[char] = {
                            "u1": u1,
                            "v1": v1,
                            "u2": u2,
                            "v2": v2
                        }
            else:
                break
    
    def read_source_png_file(self):
        self.source_img = cv2.imdecode(np.fromfile(self.source_png_file_path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        self.source_img_height, self.source_img_width, channel_number = self.source_img.shape
    
    def get_char_img(self, char:str, addon_padding=[0,0,0,0], resize_to_height=0):
        try:
            char_img = self.source_img[
                int(self.char_glyph_dict[char]["v1"]*self.source_img_height - addon_padding[1]):int(self.char_glyph_dict[char]["v2"]*self.source_img_height + addon_padding[3]),
                int(self.char_glyph_dict[char]["u1"]*self.source_img_width - addon_padding[0]):int(self.char_glyph_dict[char]["u2"]*self.source_img_width + addon_padding[2])
            ]
            if resize_to_height:
                #char_img_shape = list(char_img.shape)
                #char_img_shape[0] = resize_to_height
                scale = resize_to_height / char_img.shape[0]
                #char_img_shape[1] = int(scale * char_img.shape[1])
                if scale < 1:
                    char_img_resized = cv2.resize(src=char_img, dsize=None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
                    print("resize char {} from {}x{} to {}x{} (after addon_padding) using cv2.INTER_AREA".format(char, char_img.shape[1], char_img.shape[0], char_img_resized.shape[1], char_img_resized.shape[0]))
                elif scale > 1:
                    char_img_resized = cv2.resize(src=char_img, dsize=None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
                    print("resize char {} from {}x{} to {}x{} (after addon_padding) using cv2.INTER_CUBIC".format(char, char_img.shape[1], char_img.shape[0], char_img_resized.shape[1], char_img_resized.shape[0]))
                return char_img_resized
            else:
                return char_img
        except Exception as e:
            raise
    
    def get_expended_char_img_info(self, char:str, alpha_threshold=0):
        char_top = int(self.char_glyph_dict[char]["v1"]*self.source_img_height)
        char_bottom = int(self.char_glyph_dict[char]["v2"]*self.source_img_height)
        char_left = int(self.char_glyph_dict[char]["u1"]*self.source_img_width)
        char_right = int(self.char_glyph_dict[char]["u2"]*self.source_img_width)
        #print(char_right - char_left)
        glyph_left = -1
        glyph_right = -1
        alpha_sum_threshold = (char_bottom - char_top) * alpha_threshold
        while True:
            left_alpha_sum = np.sum(self.source_img[char_top:char_bottom, char_left, 3])
            right_alpha_sum = np.sum(self.source_img[char_top:char_bottom, char_right-1, 3])
            
            if left_alpha_sum <= alpha_sum_threshold and glyph_left < 0:
                glyph_left = char_left + 1
            if right_alpha_sum <= alpha_sum_threshold and glyph_right < 0:
                glyph_right = char_right - 1
            
            if left_alpha_sum <= alpha_sum_threshold and right_alpha_sum <= alpha_sum_threshold:
                char_left += 1
                char_right -= 1
                break
            elif char_left == 0 and right_alpha_sum <= alpha_sum_threshold:
                glyph_left = 0
                char_right -= 1
                break
            elif left_alpha_sum <= alpha_sum_threshold and char_right == self.source_img_width:
                glyph_right = self.source_img_width
                char_left += 1
                break
            elif char_left == 0 and char_right == self.source_img_width:
                glyph_left = 0
                glyph_right = self.source_img_width
                break
            else:
                if char_left > 0:
                    char_left -= 1
                if char_right < self.source_img_width:
                    char_right += 1
        if glyph_left < 0 or glyph_right < 0:
            raise Exception("get glyph edge failed!")
        
        expended_char_img_info = {
            "char": {
                "x": char_left,
                "y": char_top,
                "width": char_right - char_left,
                "height": char_bottom - char_top
            },
            "glyph": {
                "x": glyph_left,
                "y": char_top,
                "width": glyph_right - glyph_left,
                "height": char_bottom - char_top
            }
        }
        
        """expended_char_img = self.source_img[
            char_top:char_bottom,
            char_left:char_right
        ]
        cv2.imshow("expended_char_img", expended_char_img)
        cv2.waitKey(0)
        glyph_img = self.source_img[
            char_top:char_bottom,
            glyph_left:glyph_right
        ]
        cv2.destroyWindow("expended_char_img")
        cv2.imshow("glyph_img", glyph_img)
        cv2.waitKey(0)
        cv2.destroyWindow("glyph_img")"""
        
        return expended_char_img_info

    def save_all_char_img(self, save_dir, addon_padding=[0,0,0,0], resize_to_height=0):
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        imported_icon_images_lines = []
        for char in self.char_glyph_dict.keys():
            try:
                char_img = self.get_char_img(char, addon_padding, resize_to_height)
                print("saving " + "{}.png".format(ord(char)))
                cv2.imencode(ext=".png", img=char_img, params=[cv2.IMWRITE_PNG_COMPRESSION, 1])[1].tofile(os.path.join(save_dir, "{}.png".format(ord(char))))
            except Exception as e:
                print("Error saving char {} ({}) png: {}".format(char, ord(char), e.args[0]))
            else:
                imported_icon_images_lines.append("icon=\"{}.png\",{},0,0,0\n".format(ord(char), ord(char)))
            
        with open(os.path.join(save_dir, "bmfc_imported_icon_images.txt"), "w") as f:
            f.write("# imported icon images\n")
            f.writelines(imported_icon_images_lines)
            
        

if __name__ == "__main__":
    
    ofr = OgreFontdefReader(fontdef_file_path="origin\\fonts\\latin1_basic_font_100.fontdef")
    while True:
        print("输入单个字符:")
        char = input().strip()
        if len(char) == 0 or len(char) > 1:
            print("输入错误")
            continue
        expc = ofr.get_expended_char_img_info(char, 0)
        print(expc)
    
    '''
    ### korean
    ofr = OgreFontdefReader(fontdef_file_path="chinese_input_font_outline_100.fontdef")
    char_img = ofr.get_char_img("游")
    cv2.imencode(ext=".png", img=char_img, params=[cv2.IMWRITE_PNG_COMPRESSION, 1])[1].tofile(os.path.join("./", "{}.png".format(ord("游"))))
    with open("rwr_chinese_font_char.txt", "w", encoding="utf-8-sig") as f:
        for char in ofr.char_glyph_list.keys():
            f.write(char)
    ofr.save_all_char_img(save_dir="./korean_basic_font_100", addon_padding=[0, 0, 0, 0], resize_to_height=45)
    # rwr_width_offset = 0
    
    ofr = OgreFontdefReader(fontdef_file_path="origin\\fonts\\korean_basic_font_outline_100.fontdef")
    ofr.save_all_char_img(save_dir="./korean_basic_font_outline_100", addon_padding=[0, 0, 0, 0], resize_to_height=47)
    # rwr_width_offset = 0

    ### russian
    ofr = OgreFontdefReader(fontdef_file_path="origin\\fonts\\russian_basic_font_100.fontdef")
    ofr.save_all_char_img(save_dir="./russian_basic_font_100", addon_padding=[0, 0, 0, 0], resize_to_height=45)
    # rwr_width_offset = 0
    
    ofr = OgreFontdefReader(fontdef_file_path="origin\\fonts\\russian_basic_font_outline_100.fontdef")
    ofr.save_all_char_img(save_dir="./russian_basic_font_outline_100", addon_padding=[0, 0, 0, 0], resize_to_height=47)
    # rwr_width_offset = 0
    
    ### latin1
    ofr = OgreFontdefReader(fontdef_file_path="origin\\fonts\\latin1_basic_font_100.fontdef")
    ofr.save_all_char_img(save_dir="./latin1_basic_font_100", addon_padding=[7, 0, 7, 0], resize_to_height=45)
    # resize char ü from 39x64 to 27x45 (after addon_padding) using cv2.INTER_AREA
    # rwr_width_offset = int(7 * 45 / 64)
    
    ofr = OgreFontdefReader(fontdef_file_path="origin\\fonts\\latin1_basic_font_outline_100.fontdef")
    ofr.save_all_char_img(save_dir="./latin1_basic_font_outline_100", addon_padding=[10, 0, 10, 0], resize_to_height=47)
    # resize char ü from 41x64 to 30x47 (after addon_padding) using cv2.INTER_AREA
    # rwr_width_offset = int(10 * 47 / 64)
    
    cv2.namedWindow('char_img', cv2.WINDOW_KEEPRATIO)
    for char in ofr.char_glyph_list.keys():
        char_img = ofr.get_char_img(char, addon_padding=[10, 0, 10, 0])
        try:
            cv2.imshow("char_img", char_img)
            cv2.waitKey(0)
        except:
            pass
    cv2.destroyAllWindows()'''