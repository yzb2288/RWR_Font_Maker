import os
import copy
import numpy as np
from fnt_reader import FntReader

class FntSpaceCompresser(FntReader):
    def __init__(self, fnt_path_list, font_type="outline"):
        super().__init__(fnt_path_list)
        self.output_fnt_path = "{}_compressed.fnt".format(os.path.splitext(self.fnt_path_list[0])[0])
        if font_type.lower() == "basic":
            self.fill_value = [255, 255, 255, 0]
        elif font_type.lower() == "outline":
            self.fill_value = [0, 0, 0, 0]
        self.compress_page()
        self.save_fnt(self.output_fnt_path)
    
    def compress_page(self):
        last_line_y = 0
        move_up_sum = 0
        last_line_min_space_bottom = 0
        for page in self.fnt_page_line_sorted_char_dict.keys():
            #if page == 0:
            #    self.fnt_image = cv2.imdecode(np.fromfile(file=self.fnt_page_path_dict[page], dtype=np.uint8), cv2.IMREAD_UNCHANGED)
            #else:
            #    extend_fnt_image = cv2.imdecode(np.fromfile(file=self.fnt_page_path_dict[page], dtype=np.uint8), cv2.IMREAD_UNCHANGED)
            
            for line in self.fnt_page_line_sorted_char_dict[page]:
                min_space_top = int(line[0].attrib.get("height")) # 上方空像素行数
                min_space_bottom = min_space_top # 下方空像素行数
                for line_char in line:
                    x = int(line_char.attrib.get("x"))
                    y = int(line_char.attrib.get("y"))
                    width = int(line_char.attrib.get("width"))
                    height = int(line_char.attrib.get("height"))
                    
                    pix_sum_top = 0
                    for i in range(height):
                        pix_sum_top += np.sum(self.fnt_page_img_dict[page][y+i,x:(x+width),:])
                        if pix_sum_top != 0:
                            if i < min_space_top:
                                min_space_top = i
                            break
                    
                    pix_sum_bottom = 0
                    for i in range(height):
                        pix_sum_bottom += np.sum(self.fnt_page_img_dict[page][y+height-1-i,x:(x+width),:])
                        if pix_sum_bottom != 0:
                            if i < min_space_bottom:
                                min_space_bottom = i
                            break
                    
                #self.fnt_page_img_dict[page][y+min_space_top,:,:] = [0, 0, 255,255]
                #self.fnt_page_img_dict[page][y+height-1-min_space_bottom,:,:] = [0, 255, 0,255]
                #self.fnt_page_img_dict[page][y,:,:] = [255, 255, 0,255]
                #self.fnt_page_img_dict[page][y+height-1,:,:] = [0, 255, 255,255]
                
                #cv2.imshow("test", self.fnt_page_img_dict[page])
                #cv2.waitKey(0)
                if page == 0:
                    line_mat_copy = self.fnt_page_img_dict[page][y:(y+height),:,:].copy()
                    line_move_up = min(last_line_min_space_bottom, min_space_top)
                    move_up_sum += line_move_up
                    self.fnt_page_img_dict[0][y:(y+height),:,:] = self.fill_value
                    draw_new_line_y = y - move_up_sum
                    print("page: {}, line_y: {}, last_line_min_space_bottom: {}, last_line_y: {}, draw_new_line_y: {}".format(
                        page,
                        y,
                        last_line_min_space_bottom,
                        last_line_y,
                        draw_new_line_y
                    ))
                    self.fnt_page_img_dict[0][draw_new_line_y:(draw_new_line_y+height),:,:] = line_mat_copy
                    last_line_min_space_bottom = min_space_bottom
                    last_line_y = draw_new_line_y
                    
                    for line_char in line:
                        line_char.attrib.update({"y": str(draw_new_line_y)})
                else:
                    line_mat_copy = self.fnt_page_img_dict[page][y:(y+height),:,:].copy()
                    draw_new_line_y = last_line_y + height - min(last_line_min_space_bottom, min_space_top)
                    print("page: {}, line_y: {}, last_line_min_space_bottom: {}, last_line_y: {}, draw_new_line_y: {}".format(
                        page,
                        y,
                        last_line_min_space_bottom,
                        last_line_y,
                        draw_new_line_y
                    ))
                    self.fnt_page_img_dict[0][draw_new_line_y:(draw_new_line_y+height),:,:] = line_mat_copy
                    last_line_min_space_bottom = min_space_bottom
                    last_line_y = draw_new_line_y
                    
                    for line_char in line:
                        line_char.attrib.update({"y": str(draw_new_line_y), "page": "0"})
        
        self.fnt_page_line_sorted_char_dict = copy.deepcopy(self.fnt_page_line_sorted_char_dict)
        all_char_list = []
        for page in self.fnt_page_line_sorted_char_dict.keys():
            for line in self.fnt_page_line_sorted_char_dict[page]:
                all_char_list.extend(line)
        all_char_list.sort(key=lambda t:int(t.attrib.get("id")))
        for i in range(len(self.fnt_root_list)):
            self.fnt_root_list[i].find("chars").clear()
        self.fnt_root_list[0].find("chars").extend(all_char_list)
        self.fnt_id_sorted_char_dict = self.get_all_fnt_id_sorted_char_dict()
        self.fnt_page_line_sorted_char_dict = self.get_all_fnt_page_line_sorted_char_dict()
        self.fnt_page_img_dict = [self.fnt_page_img_dict[0]]

if __name__ == "__main__":
    fsc = FntSpaceCompresser(["SarasaMonoSC-Bold+KOMIKA\\bmfc\\basic_sarasa.fnt", "SarasaMonoSC-Bold+KOMIKA\\bmfc\\basic_komika_adjusted.fnt"], "basic")
    fsc = FntSpaceCompresser(["SarasaMonoSC-Bold+KOMIKA\\bmfc\\outline_sarasa.fnt", "SarasaMonoSC-Bold+KOMIKA\\bmfc\\outline_komika_adjusted.fnt"], "outline")
    fsc = FntSpaceCompresser(["SarasaMonoSC-Bold\\bmfc\\basic.fnt"], "basic")
    fsc = FntSpaceCompresser(["SarasaMonoSC-Bold\\bmfc\\outline.fnt"], "outline")
    fsc = FntSpaceCompresser(["SourceMedium+KOMIKA\\bmfc\\basic_source.fnt", "SourceMedium+KOMIKA\\bmfc\\basic_komika_adjusted.fnt"], "basic")
    fsc = FntSpaceCompresser(["SourceMedium+KOMIKA\\bmfc\\outline_source.fnt", "SourceMedium+KOMIKA\\bmfc\\outline_komika_adjusted.fnt"], "outline")
    fsc = FntSpaceCompresser(["SourceMedium_mod\\bmfc\\basic.fnt"], "basic")
    fsc = FntSpaceCompresser(["SourceMedium_mod\\bmfc\\outline.fnt"], "outline")
    a = 1
