from server import Server
import os
import shutil

INDEX_DIR = "index"
INDEX_FILE_NAME_INDEX_CHARS = 1
INDEX_FILE_EXTENSION = ""
INDEX_INFO_SPLIT_CHAR = ","
INDEX_IGNORE_CASE = True

def _indexLineToImage(line: str) -> (str, str):
    split_index = line.find(INDEX_INFO_SPLIT_CHAR)
    return (line[:split_index], line[split_index + 1:].strip())

def _imageToIndexLine(image_id: str, image_url: str):
    return image_id + INDEX_INFO_SPLIT_CHAR + image_url

def _getIndexFile(index: str) -> str:
    if INDEX_IGNORE_CASE:
        index = index.lower()
    return os.path.join(INDEX_DIR, index + INDEX_FILE_EXTENSION)

def _getIndexFileById(image_id: str) -> str:
    return _getIndexFile(image_id[:INDEX_FILE_NAME_INDEX_CHARS])

def _getImageFromFile(file_path: str, image_id: str) -> str | None:
    f = open(file_path, "r")
    lines = f.readlines()
    f.close()

    for line in lines:
        (id, url) = _indexLineToImage(line)
        if id == image_id:
            return url
    
    return None

def findImageUrl(image_id: str) -> str | None:
    file_path = _getIndexFileById(image_id)
    
    if not os.path.isfile(file_path):
        return None
    
    return _getImageFromFile(file_path, image_id)

def setImageUrl(image_id: str, image_url: str):
    file_path = _getIndexFileById(image_id)
    index_line = _imageToIndexLine(image_id, image_url) + "\n"

    lines = []
    if os.path.isfile(file_path):
        with open(file_path, "r") as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            (id, url) = _indexLineToImage(line)
            if id == image_id:
                lines[i] = index_line
                break
        else:
            lines.append(index_line)

    else:
        lines = [index_line]

    with open(file_path, "w") as f:
        f.writelines(lines)

async def rebuildIndex(server: Server, only_if_missing: bool = False):
    if only_if_missing:
        if os.path.isdir(INDEX_DIR):
            return
        print("Index not found, building from scratch...")
    else:
        print("Rebuilding index from scratch...")

    image_index: dict[str, dict[str, str]] = {}

    channels = server.fetchIndexChannels()
    print(f"Fetched {len(channels)} channels...")

    for i, channel in enumerate(channels):
        channel_images = await server.fetchChannelImages(channels[channel], channel)
        print(f"Fetched {len(channel_images)} images from channel {channels[channel].name} ({i + 1} of {len(channels)})...")

        for image_id in channel_images:
            index = image_id[:INDEX_FILE_NAME_INDEX_CHARS]
            if INDEX_IGNORE_CASE:
                index = index.lower()
            
            if not index in image_index:
                image_index[index] = {}
            image_index[index][image_id] = channel_images[image_id]

    print("Writing image index to disk...")

    if os.path.exists(INDEX_DIR):
        shutil.rmtree(INDEX_DIR, ignore_errors = True)
    os.makedirs(INDEX_DIR)

    for index in image_index:
        images: dict[str, str] = image_index[index]
        with open(_getIndexFile(index), "w") as f:
            for image in images:
                line = _imageToIndexLine(image, images[image])
                f.write(line + "\n")

    print("Done")
