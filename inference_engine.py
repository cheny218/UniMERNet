import os
import sys
import torch
from PIL import Image

# 探测上层目录路径
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from unimernet.common.config import Config
import unimernet.tasks as tasks
from unimernet.processors import load_processor


class UniMERNetEngine:
    def __init__(self, cfg_path: str = None, model_path: str = None, device: str = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        
        # 默认寻找 configs/demo.yaml
        if cfg_path is None:
            cfg_path = os.path.join(base_dir, "configs", "demo.yaml")
        
        self.cfg_path = cfg_path
        self.model_path = model_path
        self.model = None
        self.vis_processor = None
        self._load_model()

    def _load_model(self):
        if not os.path.exists(self.cfg_path):
            raise FileNotFoundError(f"未找到配置文件：{self.cfg_path}")

        cfg = Config.from_file(self.cfg_path)
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