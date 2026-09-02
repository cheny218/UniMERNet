import os
import sys
import argparse
import torch
from PIL import Image

# 确保路径解析正确
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from unimernet.common.config import Config
import unimernet.tasks as tasks
from unimernet.processors import load_processor


class UniMERNetEngine:
    def __init__(self, cfg_path: str = None, model_path: str = None, device: str = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        
        # 自动定位 demo.yaml 配置文件
        possible_cfg_paths = [
            cfg_path,
            os.path.join(base_dir, "configs", "demo.yaml"),
            os.path.join(base_dir, "_internal", "configs", "demo.yaml"),
            os.path.join(base_dir, "..", "configs", "demo.yaml"),
        ]
        self.cfg_path = next((p for p in possible_cfg_paths if p and os.path.exists(p)), "configs/demo.yaml")
        self.model_path = model_path
        self.model = None
        self.vis_processor = None
        self._load_model()

    def _load_model(self):
        # 采用 UniMERNet 官方标准的配置加载方式
        args = argparse.Namespace(cfg_path=self.cfg_path, options=None)
        cfg = Config(args)

        if self.model_path and os.path.exists(self.model_path):
            cfg.config.model.pretrained = self.model_path

        task = tasks.setup_task(cfg)
        self.model = task.build_model(cfg).to(self.device).eval()
        self.vis_processor = load_processor(
            'formula_image_eval', 
            cfg.config.datasets.formula_rec_eval.vis_processor.eval
        )

    def predict(self, image: Image.Image) -> str:
        if image.mode != "RGB":
            image = image.convert("RGB")
        processed_img = self.vis_processor(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            output = self.model.generate({"image": processed_img})
        
        latex_code = output.get("pred_str", [""])[0]
        return latex_code.strip()
