import os
import chardet
import traceback

class RWRCharScaner(object):
    def __init__(self, rwr_game_path:str, extra_scan_folder_list:list[str]=[], output_char_file_path:str=None, language:str="cn"):
        self.rwr_game_path = os.path.abspath(rwr_game_path)
        self.extra_scan_folder_list = []
        for extra_scan_folder_path in extra_scan_folder_list:
            if os.path.exists(extra_scan_folder_path):
                self.extra_scan_folder_list.append(extra_scan_folder_path)
            else:
                raise Exception("不存在该额外扫描文件夹: {}".format(extra_scan_folder_path))
        if output_char_file_path == None:
            self.output_char_file_path = "./rwr_used_char.txt"
        else:
            self.output_char_file_path = output_char_file_path
        self.language = language
        self.rwr_packages_folder_path = os.path.join(self.rwr_game_path, "media\\packages")
        if not os.path.exists(self.rwr_packages_folder_path):
            raise Exception("不存在该游戏路径: {}".format(self.rwr_game_path))
        self.scan_file_list = []
        self.rwr_package_folder_list = []
        self.rwr_names_folder_list = []
        self.rwr_language_folder_list = []
        self.all_language_list = ["cn", "de", "en", "es", "fr", "it", "kr", "pl", "pt", "ru"]
        self.scan_char_str = ""
        
        self.get_rwr_package_folder_list()
        self.get_rwr_names_folder()
        self.get_rwr_language_folder_list()
        self.get_scan_file_list()
        self.scan_char()
        self.write_output_char_file()
    
    def get_rwr_package_folder_list(self):
        files = os.listdir(self.rwr_packages_folder_path)
        for file in files:
            file_path = os.path.join(self.rwr_packages_folder_path, file)
            if os.path.isdir(file_path):
                self.rwr_package_folder_list.append(file_path)

    def get_rwr_names_folder(self):
        for packages_folder in self.rwr_package_folder_list:
            files = os.listdir(packages_folder)
            for file in files:
                if file == "names":
                    file_path = os.path.join(packages_folder, file)
                    self.rwr_names_folder_list.append(file_path)
    
    def get_rwr_language_folder_list(self):
        for packages_folder in self.rwr_package_folder_list:
            files = os.listdir(packages_folder)
            for file in files:
                if file == "languages":
                    file_path = os.path.join(packages_folder, file)
                    if self.language == "all":
                        self.rwr_language_folder_list.extend([os.path.join(file_path, language) for language in self.all_language_list])
                    else:
                        language_folder_path = os.path.join(file_path, self.language)
                        if os.path.exists(language_folder_path):
                            self.rwr_language_folder_list.append(language_folder_path)
                        else:
                            raise Exception("不存在该翻译文件夹, 请检查language参数: {}".format(language_folder_path))
    
    def get_scan_file_list(self):
        for names_folder_path in self.rwr_names_folder_list:
            self.folder_walker(names_folder_path)
        for language_folder_path in self.rwr_language_folder_list:
            self.folder_walker(language_folder_path)
        for extra_scan_folder_path in self.extra_scan_folder_list:
            self.folder_walker(extra_scan_folder_path)
    
    def scan_char(self):
        for scan_file_path in self.scan_file_list:
            with open(scan_file_path, mode="rb") as fp:
                scan_file_bytes = fp.read()
                charset_detcet_result = chardet.detect(scan_file_bytes)
                if charset_detcet_result["encoding"] == None:
                    continue
                if charset_detcet_result["confidence"] < 1.0:
                    scan_file_str = self.check_file_encoding(scan_file_bytes, scan_file_path, charset_detcet_result, charset_detcet_result["encoding"])
                else:
                    scan_file_str = scan_file_bytes.decode(charset_detcet_result["encoding"])
                for line in scan_file_str.splitlines():
                    for char in line:
                        if char in self.scan_char_str:
                            continue
                        else:
                            self.scan_char_str += char
        self.scan_char_str = self.remove_upprintable_chars(self.scan_char_str)
    
    def check_file_encoding(self, file_bytes:bytes, file_path:str, charset_detcet_result:dict, encoding:str):
        scan_file_str = file_bytes.decode(encoding)
        os.system("cls")
        print(scan_file_str)
        print("当前文件: {}".format(file_path))
        print("请检查以上文件解码内容是否包含乱码, 当前编码识别结果: {}".format(charset_detcet_result))
        if "�" in scan_file_str:
            print("\033[33m当前文件可能存在乱码字符�, 请手动检查\033[0m")
        print("输入回车确认使用当前编码, 输入新编码名称(python中允许使用的)重新打开: ")
        while True:
            try:
                new_encoding = input().strip().lower()
                if new_encoding != "":
                    return self.check_file_encoding(file_bytes, file_path, {'encoding': new_encoding, 'confidence': '手动输入的编码'}, new_encoding)
                else:
                    os.system("cls")
                    return scan_file_str
            except Exception as e:
                print(traceback.format_exc())
                print("解码失败! 输入回车确认继续使用之前的编码, 输入新编码名称(python中允许使用的)重新打开: ")
                
    
    def write_output_char_file(self):
        with open(self.output_char_file_path, "w", encoding="utf-8-sig") as fp:
            fp.write(self.scan_char_str)
    
    def remove_upprintable_chars(self, s:str):
        """移除所有不可见字符"""
        return ''.join(x for x in s if x.isprintable())
    
    def folder_walker(self, root_path):
        files = os.listdir(root_path)
        for file in files:
            file_path = os.path.join(root_path, file)
            if not os.path.isdir(file_path):
                self.scan_file_list.append(file_path)
            else:
                self.folder_walker(file_path)

if __name__ == "__main__":
    print("###############################")
    print("欢迎使用RWR游戏内字符扫描器")
    print("###############################\n")
    print("请输入RWR游戏根目录: ")
    rwr_game_path = input().strip()
    print("请输入RWR游戏语言代号(language文件夹的子文件夹名称, 回车默认cn): ")
    language = input().strip()
    if language == "":
        language = "cn"
    extra_scan_folder_list = []
    while True:
        print("请输入一个需要额外扫描字符的目录列表(建议导入7000常用字文件夹, 回车跳过): ")
        extra_scan_folder_path = input().strip()
        if extra_scan_folder_path == "":
            break
        else:
            extra_scan_folder_list.append(extra_scan_folder_path)
    print("请输入最终输出的字符合集文件名(默认为当前目录的rwr_used_char.txt): ")
    output_char_file_path = input().strip()
    if output_char_file_path == "":
        output_char_file_path = None
    
    rcs = RWRCharScaner(
        rwr_game_path=rwr_game_path,
        extra_scan_folder_list=extra_scan_folder_list,
        output_char_file_path=output_char_file_path,
        language=language
    )
