import os
from PIL import Image

def resize_and_rename_images(directory, size=(512, 512)):
    count = 1
    for filename in sorted(os.listdir(directory)):
        if filename.endswith(".jpg"):
            filepath = os.path.join(directory, filename)
            with Image.open(filepath) as img:
                resized_img = img.resize(size, Image.Resampling.LANCZOS)

                # Determine the new filename
                if count == 1:
                    new_filename = "profile.png"
                else:
                    new_filename = f"profile{count}.png"

                new_filepath = os.path.join(directory, new_filename)
                resized_img.save(new_filepath)

                count += 1

if __name__ == "__main__":
    current_directory = os.getcwd()
    resize_and_rename_images(current_directory)
