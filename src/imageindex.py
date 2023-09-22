from server import Server

INDEX_FILE_NAME_INDEX_CHARS = 1
INDEX_IGNORE_CASE = True

def _getIndexCollection(db, index: str):
    if INDEX_IGNORE_CASE:
        index = index.lower()
    return db.collection(index)

def _getIndexDocById(db, image_id: str):
    return _getIndexCollection(db, image_id[:INDEX_FILE_NAME_INDEX_CHARS]).document(image_id)

def findImageUrl(db, image_id: str) -> str | None:
    doc = _getIndexDocById(db, image_id).get()
    if doc.exists:
        return doc.to_dict().get("url")
    else:
        return None

def setImageUrl(db, image_id: str, image_url: str):
    doc = _getIndexDocById(db, image_id)
    doc.set({"url": image_url})

async def rebuildIndex(db, server: Server):
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

    print("Writing image index to database...")

    batch = db.batch()

    for index in image_index:
        images: dict[str, str] = image_index[index]
        for image in images:
            doc = _getIndexDocById(db, image)
            batch.set(doc, {"url": images[image]})

    batch.commit()

    print("Done")

def clearIndex(db):
    batch = db.batch()
    
    for collection in db.collections():
        for doc in collection.list_documents():
            batch.delete(doc)

    batch.commit()
