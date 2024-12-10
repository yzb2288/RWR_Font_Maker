import os
import chardet

class FontCharChecker(object):
    def __init__(self, char_collection_file_path:str, fontdef_file_path:str, output_exclude_char_file_path:str=None):
        if not os.path.exists(char_collection_file_path):
            raise Exception("字符合集文件不存在, 请检查路径!")
        else:
            self.char_collection_file_path = os.path.abspath(char_collection_file_path)
        if not os.path.exists(fontdef_file_path):
            raise Exception(".fontdef文件不存在, 请检查路径!")
        else:
            self.fontdef_file_path = os.path.abspath(fontdef_file_path)
        if output_exclude_char_file_path == None:
            self.output_exclude_char_file_path = "./exclude_char.txt"
        else:
            self.output_exclude_char_file_path = output_exclude_char_file_path
        self.char_collection_str = ""
        self.fontdef_unicode_str = ""
        self.exclude_char_str = ""
        self.read_char_collection_file()
        self.read_fontdef_unicode()
        self.check_char()
    
    def read_char_collection_file(self):
        with open(self.char_collection_file_path, "rb") as fp:
            char_collection_str_bytes = fp.read()
            charset_detcet_result = chardet.detect(char_collection_str_bytes)
            if charset_detcet_result["encoding"] == None:
                raise Exception("未能识别字符合集文件的编码!")
            else:
                if charset_detcet_result["confidence"] < 1.0:
                    print("Warining: 字符合集文件编码置信度{}, 当前编码: {}".format(charset_detcet_result["confidence"], charset_detcet_result["encoding"]))
                self.char_collection_str = char_collection_str_bytes.decode(charset_detcet_result["encoding"])
    
    def read_fontdef_unicode(self):
        with open(self.fontdef_file_path, "rb") as fp:
            fontdef_str_bytes = fp.read()
            charset_detcet_result = chardet.detect(fontdef_str_bytes)
            if charset_detcet_result["encoding"] == None:
                raise Exception("未能识别字符合集文件的编码!")
            else:
                if charset_detcet_result["confidence"] < 1.0:
                    print("Warining: 字符合集文件编码置信度{}, 当前编码: {}".format(charset_detcet_result["confidence"], charset_detcet_result["encoding"]))
                self.fontdef_str = fontdef_str_bytes.decode(charset_detcet_result["encoding"])
            for line in self.fontdef_str.splitlines():
                if "glyph" in line:
                    self.fontdef_unicode_str += chr(int(line.strip().split()[1].replace("u", "")))
    
    def check_char(self):
        for char in self.char_collection_str:
            if char in self.fontdef_unicode_str:
                continue
            else:
                self.exclude_char_str += char
        self.exclude_char_str = self.remove_upprintable_chars(self.exclude_char_str)
        if self.exclude_char_str != "":
            print("当前不包含在字体中的字符: ")
            print(self.exclude_char_str)
            print("当前不包含在字体中的字符Unicode: ")
            exclude_char_unicode_str = ""
            for char in self.exclude_char_str:
                exclude_char_unicode_str += "\\u{} ".format(ord(char))
            print(exclude_char_unicode_str)
            self.save_exclude_char()
        else:
            print("当前字体已包含所有字符合集中的字符")
    
    def remove_upprintable_chars(self, s:str):
        """移除所有不可见字符"""
        return ''.join(x for x in s if x.isprintable())
    
    def save_exclude_char(self):
        with open(self.output_exclude_char_file_path, "w", encoding="utf-8-sig") as fp:
            fp.write(self.exclude_char_str)

if __name__ == "__main__":
    print("#################################")
    print("欢迎使用fontdef字体字符检查器")
    print("#################################\n")
    print("请输入字符合集文件路径: ")
    char_collection_file_path = input().strip()
    print("请输入字体fontdef文件路径: ")
    fontdef_file_path = input().strip()
    print("请输入最终输出的未包含字符文件路径(回车默认为当前目录的exclude_char.txt): ")
    output_exclude_char_file_path = input().strip()
    if output_exclude_char_file_path == "":
        output_exclude_char_file_path = None
    
    fcc = FontCharChecker(
        char_collection_file_path=char_collection_file_path,
        fontdef_file_path=fontdef_file_path,
        output_exclude_char_file_path=output_exclude_char_file_path
    )