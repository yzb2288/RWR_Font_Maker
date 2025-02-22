import os

def make_bmfc_imported_icon_images_from_dir(dir_path):
    imported_icon_images_lines = []
    for name in os.listdir(dir_path):
        if os.path.isfile(os.path.join(dir_path, name)):
            name_split = os.path.splitext(name)
            if name_split[1] == ".png":
                try:
                    char_id = int(name_split[0])
                    imported_icon_images_lines.append("icon=\"{}.png\",{},0,0,0\n".format(char_id, char_id))
                except:
                    print("{} is not a char png".format(name))
                    continue
    with open(os.path.join(dir_path, "bmfc_imported_icon_images.txt"), "w") as f:
        f.write("# imported icon images\n")
        f.writelines(imported_icon_images_lines)

if __name__ == "__main__":
    make_bmfc_imported_icon_images_from_dir("./Komika_45_basic")