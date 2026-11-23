"""圖片修補 Provider。

介面：repair(rgb: HxWx3 uint8, unknown: HxW bool) -> HxWx3 uint8，把 unknown 區域用已知像素填滿。
要接其他修補工具（例如合法取得的 inpainting 服務）時，在 REPAIR_PROVIDERS 多註冊一個函式即可。
"""
import cv2
import numpy as np


def opencv_repair(rgb, unknown):
    # ponytail: Telea 邊緣延伸，只適合小面積、單純色塊；大面積遮擋由 image_processor 轉成人工修補任務。
    return cv2.inpaint(np.ascontiguousarray(rgb), unknown.astype(np.uint8) * 255, 3, cv2.INPAINT_TELEA)


REPAIR_PROVIDERS = {"opencv": opencv_repair}
