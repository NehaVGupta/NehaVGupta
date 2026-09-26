class DetectionService:
    def __init__(self, registry, images, cache):
        self.reg, self.images, self.cache = registry, images, cache

    def analyze(self, image_id):
        key = f"det:{self.reg.get('object_detection').name}:{image_id}"
        hit = self.cache.get(key)
        if hit is not None:
            return hit
        out = {"objects": self.reg.run("object_detection", self.images.load_bgr(image_id))}
        self.cache.set(key, out)
        return out
